"""
[M5] Owner: Thân Văn Thế Lâm
File: src/core/order_manager.py

Nhiệm vụ:
- Quản lý vòng đời đơn hàng, kiểm tra trường hợp biên (không hủy đơn PAID/DELIVERING;
  chỉ nhận đơn mới khi Shipper rảnh hoặc gom chuyến hợp lệ).
- Undo/Redo chuyển trạng thái bằng CustomStack (LIFO) tự viết.
- Tìm đơn theo Tên khách hàng và Email O(log n) bằng SortedIndex + Binary Search.
- Đọc/ghi file JSON an toàn qua storage.load_json / storage.save_json.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.storage import load_json, save_json
from src.core.structures import CustomStack, SortedIndex
from src.models.order import Order, OrderStatus


class OrderManager:
    """Lớp quản lý đơn hàng với chỉ mục tìm kiếm O(log n) và lịch sử trạng thái Undo/Redo."""

    def __init__(self, storage_path: str | Path = "data/orders.json") -> None:
        """Khởi tạo OrderManager và nạp dữ liệu từ file JSON."""
        self.storage_path: Path | str = storage_path
        self.orders: dict[str, Order] = {}
        self.last_error: str = ""

        # Hệ thống chỉ mục phục vụ tìm kiếm Nhị phân O(log n)
        self.name_index: SortedIndex = SortedIndex()
        self.email_index: SortedIndex = SortedIndex()

        # Ngăn xếp phục vụ Hoàn tác / Làm lại trạng thái
        self.undo_stack: CustomStack = CustomStack()
        self.redo_stack: CustomStack = CustomStack()

        self.load_orders()

    def _create_snapshot(self) -> dict[str, str]:
        """Tạo bản sao trạng thái hiện tại của toàn bộ đơn hàng.

        # Độ phức tạp: O(n).
        """
        return {order_id: order.status for order_id, order in self.orders.items()}

    def _restore_snapshot(self, snapshot: dict[str, str]) -> None:
        """Khôi phục trạng thái đơn hàng từ bản snapshot bằng order.restore_status.

        # Độ phức tạp: O(n) khôi phục và ghi file.
        """
        for order_id, status in snapshot.items():
            if order_id in self.orders:
                self.orders[order_id].restore_status(status)
        self.save_orders()

    def load_orders(self) -> None:
        """Đọc danh sách đơn hàng từ file JSON an toàn qua storage.load_json.

        # Độ phức tạp: O(n log n) với n đơn hàng nạp vào và chèn vào 2 SortedIndex.
        """
        self.orders.clear()
        self.name_index.clear()
        self.email_index.clear()

        data = load_json(self.storage_path, default={})
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, dict):
                    order = Order.from_dict(v)
                    self.orders[order.id] = order
                    self.name_index.insert(order.customer_name, order.id)
                    self.email_index.insert(order.customer_email, order.id)
        elif isinstance(data, list):
            for v in data:
                if isinstance(v, dict):
                    order = Order.from_dict(v)
                    self.orders[order.id] = order
                    self.name_index.insert(order.customer_name, order.id)
                    self.email_index.insert(order.customer_email, order.id)

    def save_orders(self) -> None:
        """Ghi dữ liệu đơn hàng hiện tại vào file JSON qua storage.save_json.

        # Độ phức tạp: O(n) theo kích thước dữ liệu đơn hàng cần ghi.
        """
        data = {k: v.to_dict() for k, v in self.orders.items()}
        save_json(self.storage_path, data)

    def next_id(self) -> str:
        """Tự động sinh mã đơn hàng mới không trùng lặp (ví dụ O001, O002, ...).

        # Độ phức tạp: O(n) duyệt qua danh sách mã đơn hiện có.
        """
        max_num = 0
        for order_id in self.orders:
            if order_id.startswith("O") and order_id[1:].isdigit():
                num = int(order_id[1:])
                if num > max_num:
                    max_num = num

        candidate_num = max_num + 1
        new_id = f"O{candidate_num:03d}"
        while new_id in self.orders:
            candidate_num += 1
            new_id = f"O{candidate_num:03d}"
        return new_id

    def get_orders_by_status(self, status: str) -> list[Order]:
        """Lấy danh sách các đơn hàng theo trạng thái chỉ định.

        # Độ phức tạp: O(n) duyệt qua danh sách đơn hàng.
        """
        return [order for order in self.orders.values() if order.status == status]

    def create_order(
        self,
        order_id: str,
        customer_name: str,
        customer_email: str,
        items: list[Any],
        created_at: float,
        shipper_status: str,
        is_vip: bool = False,
        delivery_node_id: str | None = None,
    ) -> bool:
        """Tạo đơn hàng mới: kiểm tra shipper_status và tính hợp lệ trước khi nhận đơn.

        # Độ phức tạp: O(log n) chèn vào 2 SortedIndex + O(n) lưu file JSON.
        """
        if shipper_status not in {"IDLE", "BATCHING_ALLOWED"}:
            self.last_error = f"Shipper đang bận ({shipper_status}), không thể nhận đơn mới."
            return False

        clean_id = str(order_id).strip()
        if not clean_id:
            self.last_error = "Mã đơn hàng không được để trống."
            return False

        if clean_id in self.orders:
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
                delivery_node_id=delivery_node_id,
            )
        except Exception as err:
            self.last_error = str(err)
            return False

        self.orders[new_order.id] = new_order
        # Cập nhật cả 2 index
        self.name_index.insert(new_order.customer_name, new_order.id)
        self.email_index.insert(new_order.customer_email, new_order.id)
        self.save_orders()
        self.last_error = ""
        return True

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Thay đổi trạng thái đơn hàng có lưu vết Snapshot để thực hiện Undo/Redo.

        # Độ phức tạp: O(1) tra cứu và cập nhật trạng thái + O(n) lưu snapshot và ghi file.
        """
        if order_id not in self.orders:
            self.last_error = f"Không tìm thấy đơn hàng '{order_id}'."
            return False

        order = self.orders[order_id]

        # Biên kiểm tra chặn: không được huỷ đơn khi đã PAID hoặc đang DELIVERING
        if new_status == OrderStatus.CANCELLED and order.status in {
            OrderStatus.PAID,
            OrderStatus.DELIVERING,
        }:
            self.last_error = f"Không thể hủy đơn hàng đang ở trạng thái {order.status}."
            return False

        # Lưu snapshot trước khi thực hiện biến đổi trạng thái
        snapshot = self._create_snapshot()

        if order.change_status(new_status):
            self.undo_stack.push(snapshot)
            self.redo_stack.clear()  # Thao tác mới trực tiếp xóa hoàn toàn redo_stack
            self.save_orders()
            self.last_error = ""
            return True

        self.last_error = f"Không thể chuyển trạng thái từ {order.status} sang {new_status}."
        return False

    def undo(self) -> bool:
        """Hoàn tác hành động gần nhất."""
        if self.undo_stack.is_empty():
            return False

        current_snapshot = self._create_snapshot()
        self.redo_stack.push(current_snapshot)

        previous_snapshot = self.undo_stack.pop()
        self._restore_snapshot(previous_snapshot)
        return True

    def redo(self) -> bool:
        """Làm lại hành động vừa hoàn tác."""
        if self.redo_stack.is_empty():
            return False

        current_snapshot = self._create_snapshot()
        self.undo_stack.push(current_snapshot)

        next_snapshot = self.redo_stack.pop()
        self._restore_snapshot(next_snapshot)
        return True

    def find_by_name(self, name: str) -> list[Order]:
        """Tìm đơn theo Tên khách hàng dùng Binary Search trên SortedIndex.

        # Độ phức tạp: O(log n) tìm kiếm Binary Search + O(k) với k kết quả khớp.
        """
        matched_ids = self.name_index.find_all(name)
        return [self.orders[oid] for oid in matched_ids if oid in self.orders]

    def find_by_email(self, email: str) -> list[Order]:
        """Tìm đơn theo Email khách hàng dùng Binary Search trên SortedIndex.

        # Độ phức tạp: O(log n) tìm kiếm Binary Search + O(k) với k kết quả khớp.
        """
        matched_ids = self.email_index.find_all(email)
        return [self.orders[oid] for oid in matched_ids if oid in self.orders]
