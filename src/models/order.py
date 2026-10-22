"""
[M5] Owner: Thân Văn Thế Lâm
File: src/models/order.py

Nhiệm vụ:
- Order(BaseEntity): đơn hàng (id, khách hàng, danh sách món, trạng thái, ...).
- Trạng thái: PLACED -> CONFIRMED -> PREPARING -> READY -> DELIVERING -> PAID | CANCELLED.
- Bảng chuyển trạng thái hợp lệ (state machine).
"""
from typing import Dict, List, Set
from src.models.base import BaseEntity

class OrderStatus:
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERING = "DELIVERING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

# Bảng quy định các trạng thái tiếp theo hợp lệ (State Machine)
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    OrderStatus.PLACED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.DELIVERING, OrderStatus.CANCELLED},
    OrderStatus.DELIVERING: {OrderStatus.PAID},  # Đang giao thì không được hủy giữa chừng
    OrderStatus.PAID: set(),                     # Trạng thái cuối, không thể chuyển tiếp
    OrderStatus.CANCELLED: set()                # Trạng thái cuối, không thể chuyển tiếp
class Order(BaseEntity):
    def _init_ (self, order_id : str, customer_name: str, customer_email: str, items: List[str], create_at: float)
    #Gọi hàm khởi tạo của lốp cha (nếu có):
        super()._init_()
        self.id: str = order_id
        self.id: str = customer_name
        self.id: str = customer_email
        self.id: List[str] = items
        self.id: float = create_at
        self.id: str = OrderStatus.PLACED
    def change_status (self, new_status: str)
     """
        Kiểm tra tính hợp lệ thông qua bảng ALLOWED_TRANSITIONS trước khi chuyển trạng thái.
        Trả về True nếu thành công, ngược lại trả về False.
        Độ phức tạp: O(1) do tra cứu tập hợp (set).
     """
     if new_status in ALLOWED_TRANSITIONS.get(self.status, set())
        self.status = new_status
        return True
    return False
    def to_dict (self) -> Dict:
        """Chuyển đổi object thành dict để lưu trữ JSON"""
        return {
            "id" : self.id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "items": self.items,
            "create_at": self.create_at,
            "status": self.status,
        }
@staticmethod
    def from_dict(data: dict) -> 'Order':
    """Khôi phục object từ dữ liệu dict JSON"""
        order = Order (
            order_id = data["id"],
            customer_name = data["customer_name"],
            customer_emai"l = data["customer_email"],
            items = data["items"],
            create_at = data["create_at"],
            status = data["status"],
        )
    order.status = data["status"]
    return Order
