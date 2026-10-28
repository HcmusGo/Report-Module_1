"""
Test các chức năng của thực thể Order (Phần A).
"""
import unittest

from src.models.order import Order, OrderStatus, make_item_snapshot


class TestOrder(unittest.TestCase):
    def setUp(self) -> None:
        self.item1 = make_item_snapshot("M001", "Cơm tấm", quantity=2, price=45000, prep_minutes=15)
        self.item2 = make_item_snapshot("M002", "Trà đào", quantity=1, price=30000, prep_minutes=5)
        self.order = Order(
            order_id="O001",
            customer_name="Nguyễn Văn A",
            customer_email="a@example.com",
            items=[self.item1, self.item2],
            created_at=1700000000.0,
            is_vip=True,
            delivery_node_id="N01",
        )

    def test_status_is_read_only(self) -> None:
        """Kiểm tra gán status trực tiếp phải báo AttributeError."""
        with self.assertRaises(AttributeError):
            self.order.status = OrderStatus.PAID  # type: ignore

    def test_status_transitions(self) -> None:
        """Kiểm tra các bước chuyển trạng thái hợp lệ và không hợp lệ."""
        self.assertEqual(self.order.status, OrderStatus.PLACED)

        # Chuyển không hợp lệ: PLACED -> PREPARING (phải qua CONFIRMED trước)
        self.assertFalse(self.order.change_status(OrderStatus.PREPARING))
        self.assertEqual(self.order.status, OrderStatus.PLACED)

        # Chuyển hợp lệ: PLACED -> CONFIRMED
        self.assertTrue(self.order.change_status(OrderStatus.CONFIRMED))
        self.assertEqual(self.order.status, OrderStatus.CONFIRMED)

        # CONFIRMED -> PREPARING -> READY -> DELIVERING -> PAID
        self.assertTrue(self.order.change_status(OrderStatus.PREPARING))
        self.assertTrue(self.order.change_status(OrderStatus.READY))
        self.assertTrue(self.order.change_status(OrderStatus.DELIVERING))

        # DELIVERING không được hủy
        self.assertFalse(self.order.change_status(OrderStatus.CANCELLED))
        self.assertEqual(self.order.status, OrderStatus.DELIVERING)

        # DELIVERING -> PAID
        self.assertTrue(self.order.change_status(OrderStatus.PAID))
        self.assertEqual(self.order.status, OrderStatus.PAID)

        # PAID là trạng thái cuối, không chuyển tiếp được
        self.assertFalse(self.order.change_status(OrderStatus.CANCELLED))

    def test_restore_status(self) -> None:
        """Kiểm tra restore_status bỏ qua bảng chuyển nhưng kiểm tra OrderStatus."""
        self.order.restore_status(OrderStatus.DELIVERING)
        self.assertEqual(self.order.status, OrderStatus.DELIVERING)

        with self.assertRaises(ValueError):
            self.order.restore_status("INVALID_STATUS")

    def test_total_prep_minutes(self) -> None:
        """Kiểm tra tính tổng thời gian chế biến: 2*15 + 1*5 = 35."""
        self.assertEqual(self.order.total_prep_minutes, 35.0)

    def test_round_trip_serialization(self) -> None:
        """Kiểm tra to_dict và from_dict khôi phục đúng hoàn toàn."""
        self.order.change_status(OrderStatus.CONFIRMED)
        data = self.order.to_dict()
        restored = Order.from_dict(data)

        self.assertEqual(restored.id, self.order.id)
        self.assertEqual(restored.customer_name, self.order.customer_name)
        self.assertEqual(restored.customer_email, self.order.customer_email)
        self.assertEqual(restored.created_at, self.order.created_at)
        self.assertEqual(restored.is_vip, self.order.is_vip)
        self.assertEqual(restored.delivery_node_id, self.order.delivery_node_id)
        self.assertEqual(restored.status, OrderStatus.CONFIRMED)
        self.assertEqual(len(restored.items), 2)
        self.assertEqual(restored.total_prep_minutes, 35.0)

    def test_legacy_json_compatibility(self) -> None:
        """Kiểm tra đọc dữ liệu JSON định dạng cũ (create_at và items là list[str])."""
        legacy_data = {
            "id": "O999",
            "customer_name": "Trần Thị B",
            "customer_email": "b@example.com",
            "items": ["M001", "M002"],
            "create_at": 1699999999.0,
            "status": "PREPARING",
        }
        order = Order.from_dict(legacy_data)
        self.assertEqual(order.id, "O999")
        self.assertEqual(order.created_at, 1699999999.0)
        self.assertEqual(order.create_at, 1699999999.0)
        self.assertEqual(order.status, OrderStatus.PREPARING)
        self.assertFalse(order.is_vip)
        self.assertIsNone(order.delivery_node_id)
        self.assertEqual(len(order.items), 2)
        self.assertEqual(order.items[0]["name"], "M001")
        self.assertEqual(order.items[0]["quantity"], 1)
        self.assertEqual(order.items[0]["price"], 0.0)
        self.assertEqual(order.items[0]["prep_minutes"], 0.0)
        self.assertEqual(order.total_prep_minutes, 0.0)

    def test_name_and_email_validation(self) -> None:
        """Kiểm tra setter của customer_name và customer_email không nhận chuỗi rỗng."""
        with self.assertRaises(ValueError):
            self.order.customer_name = ""
        with self.assertRaises(ValueError):
            self.order.customer_name = "   "
        with self.assertRaises(ValueError):
            self.order.customer_email = ""


if __name__ == "__main__":
    unittest.main()
