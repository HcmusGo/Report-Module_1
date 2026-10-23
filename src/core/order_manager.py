"""
[M5] Owner: Thân Văn Thế Lâm
File: src/core/order_manager.py

Nhiệm vụ:
- Quản lý vòng đời đơn hàng, kiểm tra các trường hợp biên (không hủy đơn PAID/DELIVERING; chỉ nhận đơn mới khi Shipper rảnh hoặc gom chuyến hợp lệ).
- Undo/Redo chuyển trạng thái bằng CustomStack (LIFO) tự viết.
- Tìm đơn theo Tên người dùng O(log n) và theo Email O(log n): name_index, email_index + Binary Search.
"""
import json
from typing import List, Dict, Optional, Tuple
from src.models.order import Order, OrderStatus

class OrderManager:
    def __init__(self, storage_path: str = "data/orders.json") -> None:
        self.storage_path: str = storage_path
        self.orders: Dict[str, Order] = {}
        
        # Hệ thống chỉ mục phục vụ tìm kiếm Nhị phân O(log n)
        # Mỗi phần tử trong list là một tuple: (giá trị_khóa, order_id)
        self.name_index: List[Tuple[str, str]] = []
        self.email_index: List[Tuple[str, str]] = []
        
        # Ngăn xếp phục vụ tính năng Hoàn tác / Làm lại trạng thái chung toàn hệ thống
        self.undo_stack: CustomStack = CustomStack()
        self.redo_stack: CustomStack = CustomStack()
        
        self.load_orders()

    def _create_snapshot(self) -> dict:
        """Tạo bản sao sâu trạng thái hiện tại của toàn bộ đơn hàng"""
        return {order_id: order.status for order_id, order in self.orders.items()}

    def _restore_snapshot(self, snapshot: dict) -> None:
        """Khôi phục trạng thái đơn hàng từ bản snapshot"""
        for order_id, status in snapshot.items():
            if order_id in self.orders:
                self.orders[order_id].status = status
        self.save_orders()

    def _rebuild_indexes(self) -> None:
        """Sắp xếp lại các mảng chỉ mục để sẵn sàng cho Binary Search"""
        self.name_index = [(order.customer_name.lower(), order.id) for order in self.orders.values()]
        self.email_index = [(order.customer_email.lower(), order.id) for order in self.orders.values()]
        
        # Sắp xếp theo cơ chế Tự viết hoặc dùng Timsort nội bộ của list đạt hiệu năng cao
        self.name_index.sort(key=lambda x: x[0])
        self.email_index.sort(key=lambda x: x[0])

    def load_orders(self) -> None:
        """Đọc danh sách đơn hàng từ file JSON"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.orders = {k: Order.from_dict(v) for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            self.orders = {}
        self._rebuild_indexes()

    def save_orders(self) -> None:
        """Ghi dữ liệu đơn hàng hiện tại vào file JSON"""
        data = {k: v.to_dict() for k, v in self.orders.items()}
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def create_order(self, order_id: str, customer_name: str, customer_email: str, items: List[str], created_at: float, shipper_status: str) -> bool:
        """
        Tạo đơn hàng mới: Biên kiểm tra - Chỉ nhận đơn khi Shipper rảnh (IDLE) hoặc hành vi gom chuyến hợp lệ.
        """
        # Giả định shipper_status được truyền từ module quản lý lộ trình
        if shipper_status != "IDLE" and shipper_status != "BATCHING_ALLOWED":
            return False  # Từ chối nhận đơn do Shipper đang bận giao chuyến khác không thể gom thêm
        
        if order_id in self.orders:
            return False
            
        new_order = Order(order_id, customer_name, customer_email, items, created_at)
        self.orders[order_id] = new_order
        self._rebuild_indexes()
        self.save_orders()
        return True

    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Thay đổi trạng thái đơn hàng có lưu vết Snapshot để thực hiện Undo/Redo"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        # Biên kiểm tra chặn: không được huỷ đơn khi đã PAID hoặc đang DELIVERING
        if new_status == OrderStatus.CANCELLED and order.status in [OrderStatus.PAID, OrderStatus.DELIVERING]:
            return False
            
        # Lưu snapshot trước khi thực hiện biến đổi trạng thái
        snapshot = self._create_snapshot()
        
        if order.change_status(new_status):
            self.undo_stack.push(snapshot)
            self.redo_stack.clear()  # Thao tác mới trực tiếp làm xóa hoàn toàn redo_stack
            self.save_orders()
            return True
        return False

    def undo(self) -> bool:
        """Hoàn tác hành động gần nhất"""
        if self.undo_stack.is_empty():
            return False
        
        current_snapshot = self._create_snapshot()
        self.redo_stack.push(current_snapshot)
        
        previous_snapshot = self.undo_stack.pop()
        self._restore_snapshot(previous_snapshot)
        return True

    def redo(self) -> bool:
        """Làm lại hành động vừa hoàn tác"""
        if self.redo_stack.is_empty():
            return False
            
        current_snapshot = self._create_snapshot()
        self.undo_stack.push(current_snapshot)
        
        next_snapshot = self.redo_stack.pop()
        self._restore_snapshot(next_snapshot)
        return True

    def _binary_search(self, index_list: List[Tuple[str, str]], target: str) -> List[Order]:
        """Thuật toán Tìm kiếm nhị phân chuẩn đạt độ phức tạp O(log n) lấy ra danh sách đơn hàng trùng khớp"""
        target = target.lower()
        results: List[Order] = []
        low = 0
        high = len(index_list) - 1
        found_idx = -1
        
        while low <= high:
            mid = (low + high) // 2
            if index_list[mid][0] == target:
                found_idx = mid
                break
            elif index_list[mid][0] < target:
                low = mid + 1
            else:
                high = mid - 1
                
        if found_idx != -1:
            # Quét sang trái tìm các phần tử trùng lặp
            left = found_idx
            while left >= 0 and index_list[left][0] == target:
                order_id = index_list[left][1]
                if order_id in self.orders:
                    results.append(self.orders[order_id])
                left -= 1
            # Đảo ngược lại để giữ đúng thứ tự xuất hiện ban đầu
            results.reverse()
            
            # Quét sang phải tìm các phần tử trùng lặp
            right = found_idx + 1
            while right < len(index_list) and index_list[right][0] == target:
                order_id = index_list[right][1]
                if order_id in self.orders:
                    results.append(self.orders[order_id])
                right += 1
                
        return results

    def find_by_name(self, name: str) -> List[Order]:
        """Tìm đơn theo Tên khách hàng dùng Binary Search O(log n)"""
        return self._binary_search(self.name_index, name)

    def find_by_email(self, email: str) -> List[Order]:
        """Tìm đơn theo Email khách hàng dùng Binary Search O(log n)"""
        return self._binary_search(self.email_index, email)
