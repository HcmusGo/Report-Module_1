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
    OrderStatus.DELIVERING: {OrderStatus.PAID},       # Đang giao thì không được hủy giữa chừng
    OrderStatus.PAID: set(),                           # Trạng thái cuối
    OrderStatus.CANCELLED: set(),                      # Trạng thái cuối
}  # ← LỖI 1: Thiếu đóng }


class Order(BaseEntity):
    def __init__(self, order_id: str, customer_name: str, customer_email: str,
                 items: List[str], create_at: float):  # ← LỖI 2,3: __init__ + dấu :
        # Gọi hàm khởi tạo của lớp cha
        super().__init__()                              # ← LỖI 4: __init__()
        self.id: str = order_id                         # ← LỖI 5: Mỗi thuộc tính
        self.customer_name: str = customer_name         #    phải có tên riêng
        self.customer_email: str = customer_email
        self.items: List[str] = items
        self.create_at: float = create_at
        self.status: str = OrderStatus.PLACED

    def change_status(self, new_status: str):           # ← LỖI 6: thiếu :
        """
        Kiểm tra tính hợp lệ thông qua bảng ALLOWED_TRANSITIONS trước khi chuyển trạng thái.
        Trả về True nếu thành công, ngược lại trả về False.
        Độ phức tạp: O(1) do tra cứu tập hợp (set).
        """
        if new_status in ALLOWED_TRANSITIONS.get(self.status, set()):  # ← LỖI 7: thiếu :
            self.status = new_status
            return True
        return False                                    # ← LỖI 8: indentation phải ngang if

    def to_dict(self) -> Dict:
        """Chuyển đổi object thành dict để lưu trữ JSON"""
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "items": self.items,
            "create_at": self.create_at,
            "status": self.status,
        }

    @staticmethod                                       # ← LỖI 9: phải nằm trong class
    def from_dict(data: dict) -> 'Order':
        """Khôi phục object từ dữ liệu dict JSON"""
        order = Order(                                  # ← LỖI 10,11: indentation + bỏ status
            order_id=data["id"],
            customer_name=data["customer_name"],
            customer_email=data["customer_email"],
            items=data["items"],
            create_at=data["create_at"],
        )
        order.status = data["status"]                   # Gán status riêng vì __init__ mặc định PLACED
        return order                                    # ← LỖI 12: trả về order (instance), không phải Order (class)
