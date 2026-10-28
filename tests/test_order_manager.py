"""
Test các chức năng của OrderManager (Phần B).
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core.order_manager import OrderManager
from src.models.order import OrderStatus, make_item_snapshot


class TestOrderManager(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_orders.json"
        self.om = OrderManager(storage_path=self.storage_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_order_shipper_status_and_errors(self) -> None:
        """Kiểm tra tạo đơn: shipper IDLE/BATCHING_ALLOWED được, BUSY bị từ chối kèm last_error."""
        items = [make_item_snapshot("M001", "Cơm tấm", quantity=1, price=45000, prep_minutes=15)]

        # Shipper BUSY -> Thất bại
        success = self.om.create_order(
            order_id="O001",
            customer_name="Khách 1",
            customer_email="k1@example.com",
            items=items,
            created_at=1700000000.0,
            shipper_status="BUSY",
        )
        self.assertFalse(success)
        self.assertIn("Shipper đang bận", self.om.last_error)
        self.assertEqual(len(self.om.orders), 0)

        # Shipper IDLE -> Thành công
        success_idle = self.om.create_order(
            order_id="O001",
            customer_name="Khách 1",
            customer_email="k1@example.com",
            items=items,
            created_at=1700000000.0,
            shipper_status="IDLE",
        )
        self.assertTrue(success_idle)
        self.assertEqual(self.om.last_error, "")
        self.assertEqual(len(self.om.orders), 1)

        # Trùng mã đơn -> Thất bại
        dup_success = self.om.create_order(
            order_id="O001",
            customer_name="Khách 2",
            customer_email="k2@example.com",
            items=items,
            created_at=1700000001.0,
            shipper_status="IDLE",
        )
        self.assertFalse(dup_success)
        self.assertIn("đã tồn tại", self.om.last_error)

        # Shipper BATCHING_ALLOWED -> Thành công
        success_batch = self.om.create_order(
            order_id="O002",
            customer_name="Khách 2",
            customer_email="k2@example.com",
            items=items,
            created_at=1700000002.0,
            shipper_status="BATCHING_ALLOWED",
            is_vip=True,
        )
        self.assertTrue(success_batch)
        self.assertTrue(self.om.orders["O002"].is_vip)

    def test_cannot_cancel_delivering_or_paid(self) -> None:
        """Kiểm tra không thể hủy đơn khi ở trạng thái DELIVERING hoặc PAID."""
        items = [make_item_snapshot("M001", "Cơm tấm", quantity=1, price=45000, prep_minutes=15)]
        self.om.create_order("O001", "A", "a@test.com", items, 1700000000.0, "IDLE")

        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.om.update_order_status("O001", OrderStatus.READY)
        self.om.update_order_status("O001", OrderStatus.DELIVERING)

        # Cố gắng hủy đơn khi DELIVERING -> Thất bại
        self.assertFalse(self.om.update_order_status("O001", OrderStatus.CANCELLED))
        self.assertIn("Không thể hủy", self.om.last_error)
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.DELIVERING)

        # Chuyển sang PAID
        self.assertTrue(self.om.update_order_status("O001", OrderStatus.PAID))
        # Cố gắng hủy đơn khi PAID -> Thất bại
        self.assertFalse(self.om.update_order_status("O001", OrderStatus.CANCELLED))
        self.assertIn("Không thể hủy", self.om.last_error)

    def test_undo_redo_and_clear_redo_on_new_action(self) -> None:
        """Kiểm tra Undo/Redo nhiều bước và thao tác mới làm xóa redo_stack."""
        items = [make_item_snapshot("M001", "Cơm tấm", 1, 45000, 15)]
        self.om.create_order("O001", "A", "a@test.com", items, 1700000000.0, "IDLE")

        # PLACED -> CONFIRMED
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        # CONFIRMED -> PREPARING
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.PREPARING)

        # Undo lần 1 -> về CONFIRMED
        self.assertTrue(self.om.undo())
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.CONFIRMED)

        # Undo lần 2 -> về PLACED
        self.assertTrue(self.om.undo())
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.PLACED)

        # Redo lần 1 -> lại CONFIRMED
        self.assertTrue(self.om.redo())
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.CONFIRMED)

        # Thao tác mới từ CONFIRMED -> CANCELLED
        self.assertTrue(self.om.update_order_status("O001", OrderStatus.CANCELLED))
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.CANCELLED)

        # Redo phải bị xóa (trả về False vì redo_stack rỗng)
        self.assertFalse(self.om.redo())

    def test_find_by_name_and_email_with_duplicates_and_case_insensitive(self) -> None:
        """Kiểm tra tìm kiếm theo tên và email không phân biệt hoa thường và tìm được nhiều kết quả trùng lặp."""
        items = [make_item_snapshot("M001", "Cơm tấm", 1, 45000, 15)]
        self.om.create_order("O001", "Nguyễn Văn A", "shared@test.com", items, 100.0, "IDLE")
        self.om.create_order("O002", "nguyễn văn a", "shared@test.com", items, 200.0, "IDLE")
        self.om.create_order("O003", "Trần Văn B", "b@test.com", items, 300.0, "IDLE")

        # Tìm theo tên (hoa / thường)
        results_name = self.om.find_by_name("NGUYỄN VĂN A")
        self.assertEqual(len(results_name), 2)
        res_ids = {o.id for o in results_name}
        self.assertEqual(res_ids, {"O001", "O002"})

        # Tìm theo email
        results_email = self.om.find_by_email("SHARED@TEST.COM")
        self.assertEqual(len(results_email), 2)
        self.assertEqual({o.id for o in results_email}, {"O001", "O002"})

        # Tìm không thấy
        self.assertEqual(len(self.om.find_by_name("Không Có Ai")), 0)

    def test_save_and_reload(self) -> None:
        """Kiểm tra lưu dữ liệu và nạp lại chính xác từ file JSON."""
        items = [make_item_snapshot("M001", "Cơm", 2, 45000, 15)]
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, "IDLE", is_vip=True)
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)

        # Tạo instance mới trỏ cùng storage_path
        om2 = OrderManager(storage_path=self.storage_path)
        self.assertEqual(len(om2.orders), 1)
        self.assertIn("O001", om2.orders)
        order = om2.orders["O001"]
        self.assertEqual(order.status, OrderStatus.CONFIRMED)
        self.assertTrue(order.is_vip)
        self.assertEqual(len(om2.find_by_name("A")), 1)

    def test_corrupted_json_handling(self) -> None:
        """Kiểm tra file JSON bị hỏng không làm crash, bắt đầu rỗng và tự đổi tên .bak."""
        # Ghi nội dung lỗi cú pháp vào file JSON
        with open(self.storage_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON CONTENT !!!")

        om_corrupted = OrderManager(storage_path=self.storage_path)
        self.assertEqual(len(om_corrupted.orders), 0)

        # File hỏng phải được đổi thành .bak
        bak_file = self.storage_path.with_name(f"{self.storage_path.name}.bak")
        self.assertTrue(bak_file.exists())

    def test_next_id_and_get_orders_by_status(self) -> None:
        """Kiểm tra next_id tự tăng và get_orders_by_status lọc đúng."""
        self.assertEqual(self.om.next_id(), "O001")
        items = [make_item_snapshot("M001", "Cơm", 1, 45000, 15)]
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, "IDLE")
        self.assertEqual(self.om.next_id(), "O002")

        self.om.create_order("O002", "B", "b@test.com", items, 200.0, "IDLE")
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)

        placed = self.om.get_orders_by_status(OrderStatus.PLACED)
        confirmed = self.om.get_orders_by_status(OrderStatus.CONFIRMED)
        self.assertEqual(len(placed), 1)
        self.assertEqual(placed[0].id, "O002")
        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].id, "O001")


if __name__ == "__main__":
    unittest.main()
