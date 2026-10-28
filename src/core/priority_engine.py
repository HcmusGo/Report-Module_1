"""
[M4] Owner: Nguyễn Vũ Băng Tâm
File: src/core/priority_engine.py

Nhiệm vụ:
- Tính trọng số ưu tiên của đơn/món: độ ưu tiên VIP, thời gian chờ hiện tại, thời gian chế biến.
- Dùng CustomPriorityQueue (src.core.structures) để chọn đơn/món chế biến tiếp theo.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from core.structures import CustomPriorityQueue
except ModuleNotFoundError:
    from src.core.structures import CustomPriorityQueue


class OrderItem:
    """Đại diện cho đơn hàng trong bếp."""
    def __init__(self, order_id: str, customer_name: str, items: List[str], created_at: str, is_vip: bool = False):
        self.order_id = order_id
        self.customer_name = customer_name
        self.items = items
        self.created_at = created_at
        self.is_vip = is_vip

    def get_priority_tuple(self) -> tuple:
        # Độ ưu tiên: VIP trước (0 < 1), sau đó đến thời gian tạo đơn cũ hơn làm trước
        vip_score = 0 if self.is_vip else 1
        return (vip_score, self.created_at)


class PriorityEngine:
    """
    Bộ xử lý ưu tiên hàng đợi chế biến đơn hàng trong nhà bếp.
    """
    def __init__(self):
        self.queue = CustomPriorityQueue()

    def add_order(self, order: OrderItem) -> None:
        """Thêm đơn hàng mới vào hàng đợi ưu tiên."""
        self.queue.enqueue(order, order.get_priority_tuple())

    def process_next_order(self) -> Optional[OrderItem]:
        """Lấy đơn hàng tiếp theo cần chế biến khỏi hàng đợi."""
        if self.queue.is_empty():
            return None
        return self.queue.dequeue()

    def get_pending_orders(self) -> List[OrderItem]:
        """Lấy danh sách các đơn hàng đang chờ chế biến theo thứ tự ưu tiên."""
        if hasattr(self.queue, "to_list"):
            return self.queue.to_list()
        # Dự phòng nếu queue chưa có to_list: lấy từ mảng nội bộ
        if hasattr(self.queue, "_heap"):
            return [elem[2] if len(elem) > 2 else elem[1] for elem in getattr(self.queue._heap, "_data", [])]
        return []

    def is_empty(self) -> bool:
        return self.queue.is_empty()