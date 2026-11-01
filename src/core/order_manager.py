"""
[M2] Owner: Thân Văn Thế Lâm
File: src/core/order_manager.py

Nhiệm vụ:
- Quản lý vòng đời đơn hàng, đóng gói trạng thái private.
- Trạng thái Shipper suy diễn từ đơn hàng (BUSY / IDLE).
- Kiểm tra hợp lệ điểm giao hàng qua bản đồ Graph và routing_service.
- Gom chuyến giao hàng nguyên tử (start_delivery) và hoàn thành đơn hàng (complete_delivery).
- Kiểm tra hàng đợi ưu tiên của bếp (PriorityEngine) khi chuyển CONFIRMED -> PREPARING.
- Chặn chuyển trực tiếp vào DELIVERING qua update_order_status.
- Nạp đơn hàng an toàn với per-record exception handling (load_errors).
- Hoàn tác / Làm lại (Undo/Redo) toàn bộ chuyến và đơn lẻ bằng CustomStack.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from src.core.priority_engine import PriorityEngine
from src.core.routing_service import is_valid_delivery_node, load_map_graph
from src.core.storage import load_json, save_json
from src.core.structures import CustomStack, SortedIndex
from src.models.graph_node import Graph
from src.models.order import Order, OrderStatus


class OrderManager:
    """Lớp quản lý đơn hàng với đóng gói an toàn và quy tắc nghiệp vụ chặt chẽ."""

    def __init__(
        self,
        storage_path: str | Path = "data/orders.json",
        graph: Graph | None = None,
    ) -> None:
        """Khởi tạo OrderManager, nạp bản đồ và nạp dữ liệu từ file JSON."""
        self.storage_path: Path | str = storage_path
        self._orders: dict[str, Order] = {}
        self._last_error: str = ""
        self._map_error: str = ""
        self._load_errors: list[str] = []

        # Đóng gói các chỉ mục và ngăn xếp phục vụ tìm kiếm và Undo/Redo
        self._name_index: SortedIndex = SortedIndex()
        self._email_index: SortedIndex = SortedIndex()
        self._undo_stack: CustomStack = CustomStack()
        self._redo_stack: CustomStack = CustomStack()

        # Nạp bản đồ nếu chưa được cung cấp
        if graph is not None:
            self._graph: Graph | None = graph
            self._map_error = ""
        else:
            try:
                self._graph = load_map_graph()
                self._map_error = ""
            except Exception as err:
                self._graph = None
                self._map_error = str(err)

        self.load_orders()

    @property
    def orders(self) -> dict[str, Order]:
        """Trả về bản sao nông của từ điển đơn hàng để bảo vệ dữ liệu nội bộ."""
        return self._orders.copy()

    @property
    def graph(self) -> Graph | None:
        """Đồ thị bản đồ giao hàng hiện tại."""
        return self._graph

    @graph.setter
    def graph(self, g: Graph | None) -> None:
        self._graph = g
        if g is not None:
            self._map_error = ""

    @property
    def map_error(self) -> str:
        """Thông báo lỗi nạp bản đồ (nếu có)."""
        return self._map_error

    @map_error.setter
    def map_error(self, val: str) -> None:
        self._map_error = str(val)

    @property
    def last_error(self) -> str:
        """Thông báo lỗi thao tác gần nhất."""
        return self._last_error

    @last_error.setter
    def last_error(self, val: str) -> None:
        self._last_error = str(val)

    @property
    def load_errors(self) -> list[str]:
        """Danh sách các lỗi phát sinh khi nạp đơn hàng."""
        return self._load_errors

    def _create_snapshot(self) -> dict[str, str]:
        """Tạo bản sao trạng thái hiện tại của toàn bộ đơn hàng.

        # Độ phức tạp: O(n).
        """
        return {order_id: order.status for order_id, order in self._orders.items()}

    def _restore_snapshot(self, snapshot: dict[str, str]) -> None:
        """Khôi phục trạng thái đơn hàng từ bản snapshot bằng order.restore_status.

        # Độ phức tạp: O(n) khôi phục và ghi file.
        """
        for order_id, status in snapshot.items():
            if order_id in self._orders:
                self._orders[order_id].restore_status(status)
        self.save_orders()

    def load_orders(self) -> None:
        """Đọc danh sách đơn hàng từ file JSON an toàn qua storage.load_json.

        Bắt (ValueError, KeyError, TypeError) cho từng bản ghi hỏng và ghi vào load_errors.
        # Độ phức tạp: O(n log n) với n đơn hàng nạp vào và chèn vào 2 SortedIndex.
        """
        self._orders.clear()
        self._name_index.clear()
        self._email_index.clear()
        self._load_errors.clear()

        try:
            data = load_json(self.storage_path, default={})
        except Exception as err:
            self._load_errors.append(f"Không thể đọc file đơn hàng: {err}")
            return

        if not isinstance(data, (dict, list)):
            self._load_errors.append(
                "Dữ liệu đơn hàng không hợp lệ (phải là từ điển hoặc danh sách)."
            )
            return

        records = data.values() if isinstance(data, dict) else data
        for item in records:
            if not isinstance(item, dict):
                self._load_errors.append(f"Bản ghi đơn hàng không phải từ điển: {item}")
                continue
            try:
                order = Order.from_dict(item)
                self._orders[order.id] = order
                self._name_index.insert(order.customer_name, order.id)
                self._email_index.insert(order.customer_email, order.id)
            except (ValueError, KeyError, TypeError) as err:
                self._load_errors.append(f"Lỗi bản ghi đơn hàng: {err}")

    def save_orders(self) -> None:
        """Ghi dữ liệu đơn hàng hiện tại vào file JSON qua storage.save_json.

        # Độ phức tạp: O(n) theo kích thước dữ liệu đơn hàng cần ghi.
        """
        data = {k: v.to_dict() for k, v in self._orders.items()}
        save_json(self.storage_path, data)

    def next_id(self) -> str:
        """Tự động sinh mã đơn hàng mới không trùng lặp (ví dụ O001, O002, ...).

        # Độ phức tạp: O(n) duyệt qua danh sách mã đơn hiện có.
        """
        max_num = 0
        for order_id in self._orders:
            if order_id.startswith("O") and order_id[1:].isdigit():
                num = int(order_id[1:])
                if num > max_num:
                    max_num = num

        candidate_num = max_num + 1
        new_id = f"O{candidate_num:03d}"
        while new_id in self._orders:
            candidate_num += 1
            new_id = f"O{candidate_num:03d}"
        return new_id

    def get_order(self, order_id: str) -> Order | None:
        """Lấy đơn hàng theo mã ID O(1)."""
        if not isinstance(order_id, str):
            return None
        return self._orders.get(order_id.strip())

    def get_all_orders(self) -> list[Order]:
        """Lấy toàn bộ danh sách đối tượng đơn hàng hiện có."""
        return list(self._orders.values())

    def get_orders_by_status(self, status: str) -> list[Order]:
        """Lấy danh sách các đơn hàng theo trạng thái chỉ định.

        # Độ phức tạp: O(n) duyệt qua danh sách đơn hàng.
        """
        return [order for order in self._orders.values() if order.status == status]

    def get_shipper_status(self) -> str:
        """Trạng thái Shipper suy diễn từ đơn hàng: BUSY nếu có đơn DELIVERING, else IDLE."""
        for order in self._orders.values():
            if order.status == OrderStatus.DELIVERING:
                return "BUSY"
        return "IDLE"

    def get_current_trip(self) -> list[Order]:
        """Danh sách các đơn hàng đang trong chuyến giao hiện tại (trạng thái DELIVERING)."""
        return [
            order for order in self._orders.values()
            if order.status == OrderStatus.DELIVERING
        ]

    def can_undo(self) -> bool:
        """Kiểm tra có thể thực hiện Hoàn tác (Undo) hay không."""
        return not self._undo_stack.is_empty()

    def can_redo(self) -> bool:
        """Kiểm tra có thể thực hiện Làm lại (Redo) hay không."""
        return not self._redo_stack.is_empty()

    def create_order(
        self,
        order_id: str,
        customer_name: str,
        customer_email: str,
        items: list[Any],
        created_at: float,
        is_vip: bool = False,
        delivery_node_id: str | None = None,
    ) -> bool:
        """Tạo đơn hàng mới với kiểm tra ràng buộc bản đồ, shipper và dữ liệu.

        # Độ phức tạp: O(log n) chèn vào 2 SortedIndex + O(n) lưu file JSON.
        """
        if self._graph is None or self._map_error:
            self.last_error = self._map_error or "Bản đồ chưa sẵn sàng."
            return False

        if self.get_shipper_status() == "BUSY":
            self.last_error = "Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"
            return False

        clean_node = str(delivery_node_id).strip() if delivery_node_id is not None else ""
        if not clean_node or not is_valid_delivery_node(self._graph, clean_node):
            self.last_error = "Điểm giao không hợp lệ"
            return False

        clean_id = str(order_id).strip()
        if not clean_id:
            self.last_error = "Mã đơn hàng không được để trống."
            return False

        if clean_id in self._orders:
            self.last_error = f"Mã đơn hàng '{clean_id}' đã tồn tại."
            return False

        if not str(customer_name).strip():
            self.last_error = "Tên khách hàng không được để trống."
            return False

        if not str(customer_email).strip():
            self.last_error = "Email khách hàng không được để trống."
            return False

        if not items:
            self.last_error = "Danh sách món ăn không được để trống."
            return False

        try:
            new_order = Order(
                order_id=clean_id,
                customer_name=customer_name,
                customer_email=customer_email,
                items=items,
                created_at=created_at,
                is_vip=is_vip,
                delivery_node_id=clean_node,
            )
        except Exception as err:
            self.last_error = str(err)
            return False

        self._orders[new_order.id] = new_order
        self._name_index.insert(new_order.customer_name, new_order.id)
        self._email_index.insert(new_order.customer_email, new_order.id)
        self.save_orders()
        self.last_error = ""
        return True

    def start_delivery(self, order_ids: list[str]) -> bool:
        """Bắt đầu giao hàng gom chuyến nguyên tử cho danh sách mã đơn READY chỉ định.

        Chụp một snapshot duy nhất trước khi chuyển tất cả đơn sang DELIVERING.
        # Độ phức tạp: O(k) kiểm tra + O(n) lưu snapshot và ghi file JSON.
        """
        if self.get_shipper_status() == "BUSY":
            self.last_error = "Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"
            return False

        if not order_ids:
            self.last_error = "Danh sách đơn hàng rỗng."
            return False

        if len(order_ids) != len(set(order_ids)):
            self.last_error = "Danh sách đơn hàng có mã trùng lặp."
            return False

        if self._graph is None or self._map_error:
            self.last_error = self._map_error or "Bản đồ chưa sẵn sàng."
            return False

        for oid in order_ids:
            if oid not in self._orders:
                self.last_error = f"Không tìm thấy đơn hàng '{oid}'."
                return False
            order = self._orders[oid]
            if order.status != OrderStatus.READY:
                self.last_error = (
                    f"Đơn hàng '{oid}' đang ở trạng thái {order.status}, "
                    "chỉ đơn READY mới có thể giao hàng."
                )
                return False
            if (
                not order.delivery_node_id
                or not is_valid_delivery_node(self._graph, order.delivery_node_id)
            ):
                self.last_error = f"Đơn hàng '{oid}' có điểm giao không hợp lệ."
                return False

        snapshot = self._create_snapshot()
        self._undo_stack.push(snapshot)
        self._redo_stack.clear()

        for oid in order_ids:
            self._orders[oid].change_status(OrderStatus.DELIVERING)

        self.save_orders()
        self.last_error = ""
        return True

    def complete_delivery(self, order_id: str) -> bool:
        """Hoàn thành giao một đơn hàng đang ở trạng thái DELIVERING sang PAID.

        Chụp một snapshot và lưu file một lần.
        # Độ phức tạp: O(1) tra cứu và đổi trạng thái + O(n) lưu snapshot và ghi file.
        """
        clean_id = str(order_id).strip()
        if clean_id not in self._orders:
            self.last_error = f"Không tìm thấy đơn hàng '{clean_id}'."
            return False

        order = self._orders[clean_id]
        if order.status != OrderStatus.DELIVERING:
            self.last_error = (
                f"Đơn hàng '{clean_id}' không ở trạng thái DELIVERING "
                f"(hiện tại: {order.status})."
            )
            return False

        snapshot = self._create_snapshot()
        if order.change_status(OrderStatus.PAID):
            self._undo_stack.push(snapshot)
            self._redo_stack.clear()
            self.save_orders()
            self.last_error = ""
            return True

        self.last_error = f"Không thể chuyển trạng thái từ {order.status} sang PAID."
        return False

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Cập nhật trạng thái đơn hàng có bảo vệ thứ tự ưu tiên và chặn DELIVERING.

        # Độ phức tạp: O(1) tra cứu + O(n log n) xếp hạng ưu tiên (nếu CONFIRMED->PREPARING)
        # + O(n) lưu snapshot và ghi file.
        """
        clean_id = str(order_id).strip()
        if clean_id not in self._orders:
            self.last_error = f"Không tìm thấy đơn hàng '{clean_id}'."
            return False

        order = self._orders[clean_id]

        # Chặn chuyển trực tiếp vào DELIVERING
        if new_status in {OrderStatus.DELIVERING, "DELIVERING"}:
            self.last_error = "Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"
            return False

        # Chặn CONFIRMED -> PREPARING nếu không phải đơn đứng đầu hàng đợi ưu tiên
        if (
            order.status in {OrderStatus.CONFIRMED, "CONFIRMED"}
            and new_status in {OrderStatus.PREPARING, "PREPARING"}
        ):
            confirmed = self.get_orders_by_status(OrderStatus.CONFIRMED)
            top = PriorityEngine().next_order(confirmed, now=time.time())
            if top and clean_id != top.id:
                self.last_error = (
                    f"Đơn hàng '{top.id}' ({top.customer_name}) có độ ưu tiên cao hơn, "
                    "phải chế biến trước."
                )
                return False

        # Chặn hủy đơn khi đã PAID hoặc đang DELIVERING
        if new_status == OrderStatus.CANCELLED and order.status in {
            OrderStatus.PAID,
            OrderStatus.DELIVERING,
        }:
            self.last_error = f"Không thể hủy đơn hàng đang ở trạng thái {order.status}."
            return False

        snapshot = self._create_snapshot()
        if order.change_status(new_status):
            self._undo_stack.push(snapshot)
            self._redo_stack.clear()
            self.save_orders()
            self.last_error = ""
            return True

        self.last_error = (
            f"Không thể chuyển trạng thái từ {order.status} sang {new_status}."
        )
        return False

    def undo(self) -> bool:
        """Hoàn tác hành động gần nhất."""
        if self._undo_stack.is_empty():
            return False

        current_snapshot = self._create_snapshot()
        self._redo_stack.push(current_snapshot)

        previous_snapshot = self._undo_stack.pop()
        self._restore_snapshot(previous_snapshot)
        return True

    def redo(self) -> bool:
        """Làm lại hành động vừa hoàn tác."""
        if self._redo_stack.is_empty():
            return False

        current_snapshot = self._create_snapshot()
        self._undo_stack.push(current_snapshot)

        next_snapshot = self._redo_stack.pop()
        self._restore_snapshot(next_snapshot)
        return True

    def find_by_name(self, name: str) -> list[Order]:
        """Tìm đơn theo Tên khách hàng dùng Binary Search trên SortedIndex.

        # Độ phức tạp: O(log n) tìm kiếm Binary Search + O(k) với k kết quả khớp.
        """
        matched_ids = self._name_index.find_all(name)
        return [self._orders[oid] for oid in matched_ids if oid in self._orders]

    def find_by_email(self, email: str) -> list[Order]:
        """Tìm đơn theo Email khách hàng dùng Binary Search trên SortedIndex.

        # Độ phức tạp: O(log n) tìm kiếm Binary Search + O(k) với k kết quả khớp.
        """
        matched_ids = self._email_index.find_all(email)
        return [self._orders[oid] for oid in matched_ids if oid in self._orders]
