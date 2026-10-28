"""
[M4] Owner: Nguyễn Vũ Băng Tâm
File: src/core/priority_engine.py

Nhiệm vụ:
- Tính trọng số ưu tiên chế biến đơn hàng: độ ưu tiên VIP, thời gian chờ, thời gian chế biến.
- Thuật toán Aging chống bỏ đói (starvation) cho các đơn hàng thường chờ lâu.
- Dùng CustomPriorityQueue (src.core.structures) để xếp hạng thứ tự chế biến O(n log n).
- Không giữ trạng thái nội bộ; dùng Protocol OrderLike để giảm thiểu phụ thuộc với model.
"""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

from src.core.structures import CustomPriorityQueue

# Hằng số cấu hình thuật toán xếp hạng ưu tiên
VIP_BONUS: float = 30.0    # Điểm thưởng ưu tiên cho khách VIP (tương đương giảm 30 phút chờ)
WAIT_WEIGHT: float = 1.0   # Trọng số thời gian chờ (càng chờ lâu, điểm càng giảm -> làm trước)
PREP_WEIGHT: float = 1.0   # Trọng số thời gian chế biến (món chế biến nhanh làm trước)


def compute_priority(is_vip: bool, wait_minutes: float, prep_minutes: float) -> float:
    """Tính điểm ưu tiên chế biến của đơn hàng. Số nhỏ hơn = ưu tiên làm trước.

    score = PREP_WEIGHT * prep_minutes - WAIT_WEIGHT * max(0, wait_minutes)
            - (VIP_BONUS if is_vip else 0)

    # Độ phức tạp: O(1).
    """
    return (
        PREP_WEIGHT * float(prep_minutes)
        - WAIT_WEIGHT * max(0.0, float(wait_minutes))
        - (VIP_BONUS if is_vip else 0.0)
    )


@runtime_checkable
class OrderLike(Protocol):
    """Protocol mô tả các thuộc tính của đơn hàng cần thiết cho PriorityEngine."""

    id: str
    customer_name: str
    is_vip: bool
    created_at: float
    total_prep_minutes: float


class PriorityEngine:
    """Bộ xử lý ưu tiên hàng đợi chế biến đơn hàng trong nhà bếp (Stateless).

    Không lưu trữ trạng thái đơn hàng trong class; trạng thái do OrderManager quản lý.
    Điểm ưu tiên được tính động theo thời gian thực (aging) để chống bỏ đói đơn thường.
    """

    def explain(
        self, order: OrderLike, now: float | None = None
    ) -> dict[str, float]:
        """Giải thích chi tiết các thành phần tính điểm ưu tiên của đơn hàng.

        # Độ phức tạp: O(1).
        """
        current_time = time.time() if now is None else float(now)
        wait_minutes = max(0.0, (current_time - float(order.created_at)) / 60.0)
        prep_minutes = float(order.total_prep_minutes)
        vip_bonus = VIP_BONUS if order.is_vip else 0.0
        score = compute_priority(order.is_vip, wait_minutes, prep_minutes)
        return {
            "wait_minutes": wait_minutes,
            "prep_minutes": prep_minutes,
            "vip_bonus": vip_bonus,
            "score": score,
        }

    def rank(
        self, orders: list[OrderLike], now: float | None = None
    ) -> list[OrderLike]:
        """Xếp hạng các đơn hàng theo độ ưu tiên từ cao xuống thấp (điểm score nhỏ làm trước).

        # Độ phức tạp: O(n log n) khi enqueue n phần tử vào CustomPriorityQueue (mỗi enqueue
        # O(log n))
        # và dequeue n phần tử (mỗi dequeue O(log n)).
        #
        # Giải thích cơ chế chống bỏ đói (Aging):
        # Điểm ưu tiên phải tính lại tại thời điểm hiện tại `now` vì wait_minutes tăng dần theo
        # thời gian. Ngay cả khi đơn hàng VIP mới đến nhận được điểm thưởng VIP_BONUS = 30.0,
        # nếu đơn thường chờ lâu hơn (ví dụ wait_minutes = 40.0), điểm của đơn thường sẽ thấp hơn
        # (-30 < -20), đảm bảo đơn thường được phục vụ trước và không bị bỏ đói (starvation).
        """
        if not orders:
            return []

        current_time = time.time() if now is None else float(now)
        pq: CustomPriorityQueue[OrderLike] = CustomPriorityQueue()

        for order in orders:
            wait_minutes = max(0.0, (current_time - float(order.created_at)) / 60.0)
            score = compute_priority(
                order.is_vip, wait_minutes, float(order.total_prep_minutes)
            )
            # Khóa ưu tiên là tuple (score, created_at)
            # Khi score bằng nhau, đơn tạo sớm hơn (created_at nhỏ hơn) sẽ làm trước
            pq.enqueue(order, (score, float(order.created_at)))

        ranked: list[OrderLike] = []
        while not pq.is_empty():
            ranked.append(pq.dequeue())
        return ranked

    def next_order(
        self, orders: list[OrderLike], now: float | None = None
    ) -> OrderLike | None:
        """Lấy đơn hàng tiếp theo có độ ưu tiên cao nhất, hoặc None nếu rỗng.

        # Độ phức tạp: O(n log n).
        """
        ranked = self.rank(orders, now=now)
        return ranked[0] if ranked else None
