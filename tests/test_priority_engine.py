"""
Test các chức năng của PriorityEngine (Phần C).
"""
import unittest

from src.core.priority_engine import (
    PREP_WEIGHT,
    VIP_BONUS,
    WAIT_WEIGHT,
    OrderLike,
    PriorityEngine,
    compute_priority,
)


class DummyOrder:
    """Lớp giả lập đơn hàng thỏa mãn Protocol OrderLike."""

    def __init__(
        self,
        id: str,
        customer_name: str,
        is_vip: bool,
        created_at: float,
        total_prep_minutes: float,
    ) -> None:
        self.id = id
        self.customer_name = customer_name
        self.is_vip = is_vip
        self.created_at = created_at
        self.total_prep_minutes = total_prep_minutes


class TestPriorityEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PriorityEngine()
        self.now = 10000.0

    def test_compute_priority_formula(self) -> None:
        """Kiểm tra công thức tính điểm: PREP_WEIGHT*prep - WAIT_WEIGHT*wait - (VIP_BONUS if vip)."""
        # Đơn thường: prep=15, wait=10 -> 1*15 - 1*10 - 0 = 5.0
        score_normal = compute_priority(is_vip=False, wait_minutes=10.0, prep_minutes=15.0)
        self.assertEqual(score_normal, 5.0)

        # Đơn VIP: prep=15, wait=10 -> 1*15 - 1*10 - 30 = -25.0
        score_vip = compute_priority(is_vip=True, wait_minutes=10.0, prep_minutes=15.0)
        self.assertEqual(score_vip, -25.0)

        # wait_minutes âm được làm tròn về 0
        score_negative_wait = compute_priority(is_vip=False, wait_minutes=-5.0, prep_minutes=10.0)
        self.assertEqual(score_negative_wait, 10.0)

    def test_case_a_normal_wait_10m_vs_new_vip(self) -> None:
        """(a) Đơn thường chờ 10 phút vs VIP mới (chờ 0 phút), cùng chế biến 10 phút -> VIP trước."""
        # now = 10000.0
        # Đơn thường: tạo lúc now - 600 (10 phút trước), prep = 10
        # Score = 1*10 - 1*10 - 0 = 0.0
        order_normal = DummyOrder(
            id="NORM",
            customer_name="Thường",
            is_vip=False,
            created_at=self.now - 600,
            total_prep_minutes=10.0,
        )

        # VIP mới: tạo lúc now (0 phút chờ), prep = 10
        # Score = 1*10 - 1*0 - 30 = -20.0
        order_vip = DummyOrder(
            id="VIP",
            customer_name="VIP",
            is_vip=True,
            created_at=self.now,
            total_prep_minutes=10.0,
        )

        ranked = self.engine.rank([order_normal, order_vip], now=self.now)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].id, "VIP")
        self.assertEqual(ranked[1].id, "NORM")

    def test_case_b_normal_wait_40m_vs_new_vip_anti_starvation(self) -> None:
        """(b) Đơn thường chờ 40 phút vs VIP mới -> Đơn thường trước (chống bỏ đói)."""
        # Đơn thường: chờ 40 phút (2400s), prep = 10
        # Score = 1*10 - 1*40 - 0 = -30.0
        order_normal = DummyOrder(
            id="NORM",
            customer_name="Thường",
            is_vip=False,
            created_at=self.now - 2400,
            total_prep_minutes=10.0,
        )

        # VIP mới: chờ 0 phút, prep = 10
        # Score = 1*10 - 1*0 - 30 = -20.0
        order_vip = DummyOrder(
            id="VIP",
            customer_name="VIP",
            is_vip=True,
            created_at=self.now,
            total_prep_minutes=10.0,
        )

        # Vì -30.0 < -20.0 nên đơn thường có điểm nhỏ hơn -> làm trước!
        ranked = self.engine.rank([order_normal, order_vip], now=self.now)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].id, "NORM")
        self.assertEqual(ranked[1].id, "VIP")

    def test_case_c_different_prep_times(self) -> None:
        """(c) Cùng điều kiện khác thời gian chế biến 5 vs 20 phút -> 5 phút trước."""
        # Cùng tạo tại self.now, cùng là đơn thường
        order_fast = DummyOrder(
            id="FAST",
            customer_name="Nhanh",
            is_vip=False,
            created_at=self.now,
            total_prep_minutes=5.0,
        )
        order_slow = DummyOrder(
            id="SLOW",
            customer_name="Chậm",
            is_vip=False,
            created_at=self.now,
            total_prep_minutes=20.0,
        )

        ranked = self.engine.rank([order_slow, order_fast], now=self.now)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].id, "FAST")
        self.assertEqual(ranked[1].id, "SLOW")

    def test_case_d_tie_breaking_by_created_at(self) -> None:
        """(d) Hòa điểm -> Đơn tạo sớm hơn được làm trước."""
        # Hai đơn thường cùng prep = 10. Đơn 1 tạo lúc now - 60s, đơn 2 tạo lúc now.
        # Để hòa điểm:
        # Giả sử cả 2 đều có wait_minutes = 0 (tạo tại cùng thời điểm nhưng cách nhau vài giây epoch)
        # hoặc gán created_at sao cho score bằng nhau:
        # Đơn 1: prep = 10, wait = 5m (created_at = now - 300) -> score = 10 - 5 = 5.
        # Đơn 2: prep = 15, wait = 10m (created_at = now - 600) -> score = 15 - 10 = 5.
        # Cả 2 cùng có score = 5.0!
        # Đơn 2 tạo sớm hơn (now - 600 < now - 300) nên created_at nhỏ hơn -> phải làm trước!
        order_earlier = DummyOrder(
            id="EARLY",
            customer_name="Sớm",
            is_vip=False,
            created_at=self.now - 600,
            total_prep_minutes=15.0,
        )
        order_later = DummyOrder(
            id="LATE",
            customer_name="Muộn",
            is_vip=False,
            created_at=self.now - 300,
            total_prep_minutes=10.0,
        )

        # Điểm của 2 đơn:
        exp_early = self.engine.explain(order_earlier, now=self.now)
        exp_late = self.engine.explain(order_later, now=self.now)
        self.assertEqual(exp_early["score"], 5.0)
        self.assertEqual(exp_late["score"], 5.0)

        ranked = self.engine.rank([order_later, order_earlier], now=self.now)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].id, "EARLY")
        self.assertEqual(ranked[1].id, "LATE")

    def test_next_order_and_explain(self) -> None:
        """Kiểm tra next_order và explain."""
        self.assertIsNone(self.engine.next_order([]))

        order = DummyOrder("O001", "A", True, self.now - 120, 15.0)
        top = self.engine.next_order([order], now=self.now)
        self.assertIsNotNone(top)
        self.assertEqual(top.id, "O001")

        exp = self.engine.explain(order, now=self.now)
        self.assertAlmostEqual(exp["wait_minutes"], 2.0)
        self.assertEqual(exp["prep_minutes"], 15.0)
        self.assertEqual(exp["vip_bonus"], 30.0)
        self.assertAlmostEqual(exp["score"], 15.0 - 2.0 - 30.0)


if __name__ == "__main__":
    unittest.main()
