"""
Test các chức năng của OrderManager (Phần B và Milestone M4).
"""
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from src.core.order_manager import OrderManager
from src.core.storage import save_json
from src.models.graph_node import Graph, GraphNode
from src.models.order import OrderStatus, make_item_snapshot


class TestOrderManager(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "test_orders.json"

        # Khởi tạo đồ thị bản đồ chuẩn cho kiểm thử OrderManager
        self.graph = Graph()
        self.graph.add_node(GraphNode("RESTAURANT", "Quán ăn", 0.0, 0.0))
        self.graph.add_node(GraphNode("A", "Ngã tư A", 2.0, 2.0))
        self.graph.add_node(GraphNode("B", "Ngã tư B", 3.0, -1.0))
        self.graph.add_node(GraphNode("CUSTOMER", "Nhà khách hàng", 8.0, 1.0))
        self.graph.add_node(GraphNode("CUSTOMER_2", "Nhà khách hàng 2", 7.0, 4.0))
        self.graph.add_node(GraphNode("CUSTOMER_3", "Nhà khách hàng 3", 4.0, -4.0))

        self.graph.add_edge("RESTAURANT", "A", 2.8)
        self.graph.add_edge("RESTAURANT", "B", 3.2)
        self.graph.add_edge("A", "CUSTOMER", 3.0)
        self.graph.add_edge("A", "CUSTOMER_2", 2.8)
        self.graph.add_edge("B", "CUSTOMER_3", 3.2)
        self.graph.add_edge("CUSTOMER", "CUSTOMER_2", 3.2)

        self.om = OrderManager(storage_path=self.storage_path, graph=self.graph)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _make_item(self, code: str = "M001", qty: int = 1, prep: int = 15) -> list[dict]:
        return [make_item_snapshot(code, f"Món {code}", quantity=qty, price=45000,
                                   prep_minutes=prep)]

    def test_create_order_shipper_status_and_errors(self) -> None:
        """Kiểm tra tạo đơn: từ chối khi shipper BUSY, trùng mã hoặc thiếu trường."""
        items = self._make_item("M001")

        # Tạo đơn hợp lệ ban đầu
        ok = self.om.create_order(
            order_id="O001",
            customer_name="Khách 1",
            customer_email="k1@example.com",
            items=items,
            created_at=1700000000.0,
            is_vip=False,
            delivery_node_id="CUSTOMER",
        )
        self.assertTrue(ok)
        self.assertEqual(self.om.last_error, "")
        self.assertEqual(len(self.om.orders), 1)

        # Trùng mã đơn -> Thất bại
        dup = self.om.create_order(
            order_id="O001",
            customer_name="Khách 2",
            customer_email="k2@example.com",
            items=items,
            created_at=1700000001.0,
            is_vip=False,
            delivery_node_id="CUSTOMER_2",
        )
        self.assertFalse(dup)
        self.assertIn("đã tồn tại", self.om.last_error)

        # Tạo đơn VIP với node CUSTOMER_2
        ok_vip = self.om.create_order(
            order_id="O002",
            customer_name="Khách 2",
            customer_email="k2@example.com",
            items=items,
            created_at=1700000002.0,
            is_vip=True,
            delivery_node_id="CUSTOMER_2",
        )
        self.assertTrue(ok_vip)
        self.assertTrue(self.om.orders["O002"].is_vip)

    def test_derived_shipper_status_lifecycle(self) -> None:
        """Kiểm tra vòng đời trạng thái Shipper: IDLE -> BUSY -> IDLE."""
        self.assertEqual(self.om.get_shipper_status(), "IDLE")
        self.assertEqual(len(self.om.get_current_trip()), 0)

        items = self._make_item("M001")
        self.om.create_order("O001", "K1", "k1@test.com", items, 100.0, False, "CUSTOMER")
        self.om.create_order("O002", "K2", "k2@test.com", items, 105.0, False, "CUSTOMER_2")

        # Chuyển cả 2 đơn sang READY
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.om.update_order_status("O002", OrderStatus.CONFIRMED)
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.om.update_order_status("O001", OrderStatus.READY)
        self.om.update_order_status("O002", OrderStatus.PREPARING)
        self.om.update_order_status("O002", OrderStatus.READY)

        self.assertEqual(self.om.get_shipper_status(), "IDLE")

        # Bắt đầu giao cả 2 đơn -> Shipper BUSY
        self.assertTrue(self.om.start_delivery(["O001", "O002"]))
        self.assertEqual(self.om.get_shipper_status(), "BUSY")
        current_trip = self.om.get_current_trip()
        self.assertEqual(len(current_trip), 2)
        self.assertEqual({o.id for o in current_trip}, {"O001", "O002"})

        # Hoàn thành 1 đơn -> Vẫn BUSY vì còn O002
        self.assertTrue(self.om.complete_delivery("O001"))
        self.assertEqual(self.om.get_shipper_status(), "BUSY")
        self.assertEqual(len(self.om.get_current_trip()), 1)

        # Hoàn thành nốt đơn cuối -> Tự động chuyển về IDLE
        self.assertTrue(self.om.complete_delivery("O002"))
        self.assertEqual(self.om.get_shipper_status(), "IDLE")
        self.assertEqual(len(self.om.get_current_trip()), 0)

    def test_create_order_rejections(self) -> None:
        """Kiểm tra từ chối tạo đơn khi shipper BUSY hoặc điểm giao không hợp lệ."""
        items = self._make_item("M001")

        # Điểm giao None
        self.assertFalse(self.om.create_order(
            "O001", "A", "a@test.com", items, 100.0, False, None
        ))
        self.assertEqual(self.om.last_error, "Điểm giao không hợp lệ")

        # Điểm giao RESTAURANT
        self.assertFalse(self.om.create_order(
            "O001", "A", "a@test.com", items, 100.0, False, "RESTAURANT"
        ))
        self.assertEqual(self.om.last_error, "Điểm giao không hợp lệ")

        # Điểm giao ZZZ không tồn tại
        self.assertFalse(self.om.create_order(
            "O001", "A", "a@test.com", items, 100.0, False, "ZZZ"
        ))
        self.assertEqual(self.om.last_error, "Điểm giao không hợp lệ")

        # Tạo đơn hợp lệ và chuyển sang DELIVERING để shipper BUSY
        self.assertTrue(self.om.create_order(
            "O001", "A", "a@test.com", items, 100.0, False, "CUSTOMER"
        ))
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.om.update_order_status("O001", OrderStatus.READY)
        self.om.start_delivery(["O001"])

        # Khi shipper BUSY -> từ chối nhận đơn mới
        self.assertFalse(self.om.create_order(
            "O002", "B", "b@test.com", items, 200.0, False, "CUSTOMER_2"
        ))
        self.assertIn("Shipper đang giao chuyến hiện tại, chưa nhận đơn mới", self.om.last_error)

        # Bản đồ bị lỗi -> từ chối nhận đơn
        self.om.complete_delivery("O001")
        self.om.map_error = "Bản đồ hỏng"
        self.assertFalse(self.om.create_order(
            "O003", "C", "c@test.com", items, 300.0, False, "CUSTOMER"
        ))
        self.assertIn("Bản đồ hỏng", self.om.last_error)

    def test_start_delivery_validations_and_snapshot_undo(self) -> None:
        """Kiểm tra điều kiện start_delivery và snapshot undo khôi phục cả chuyến."""
        items = self._make_item("M001")
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, False, "CUSTOMER")
        self.om.create_order("O002", "B", "b@test.com", items, 105.0, False, "CUSTOMER_2")

        # Danh sách rỗng
        self.assertFalse(self.om.start_delivery([]))
        self.assertEqual(self.om.last_error, "Danh sách đơn hàng rỗng.")

        # Danh sách trùng lặp
        self.assertFalse(self.om.start_delivery(["O001", "O001"]))
        self.assertEqual(self.om.last_error, "Danh sách đơn hàng có mã trùng lặp.")

        # Mã đơn không tồn tại
        self.assertFalse(self.om.start_delivery(["UNKNOWN"]))
        self.assertIn("Không tìm thấy đơn hàng", self.om.last_error)

        # Đơn chưa READY (đang PLACED)
        self.assertFalse(self.om.start_delivery(["O001"]))
        self.assertIn("chỉ đơn READY mới có thể giao hàng", self.om.last_error)

        # Chuyển cả 2 đơn sang READY
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.om.update_order_status("O002", OrderStatus.CONFIRMED)
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.om.update_order_status("O001", OrderStatus.READY)
        self.om.update_order_status("O002", OrderStatus.PREPARING)
        self.om.update_order_status("O002", OrderStatus.READY)

        # Gom chuyến thành công
        self.assertTrue(self.om.start_delivery(["O001", "O002"]))
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.DELIVERING)
        self.assertEqual(self.om.orders["O002"].status, OrderStatus.DELIVERING)
        self.assertEqual(self.om.get_shipper_status(), "BUSY")

        # Khi đang BUSY, không thể gọi start_delivery tiếp
        self.assertFalse(self.om.start_delivery(["O001"]))
        self.assertIn("Shipper đang giao chuyến hiện tại", self.om.last_error)

        # Undo 1 lần duy nhất đưa cả 2 đơn về READY và shipper về IDLE
        self.assertTrue(self.om.undo())
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.READY)
        self.assertEqual(self.om.orders["O002"].status, OrderStatus.READY)
        self.assertEqual(self.om.get_shipper_status(), "IDLE")

        # Redo 1 lần khôi phục cả 2 đơn về DELIVERING và shipper về BUSY
        self.assertTrue(self.om.redo())
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.DELIVERING)
        self.assertEqual(self.om.orders["O002"].status, OrderStatus.DELIVERING)
        self.assertEqual(self.om.get_shipper_status(), "BUSY")

    def test_complete_delivery_validations(self) -> None:
        """Kiểm tra điều kiện của complete_delivery."""
        items = self._make_item("M001")
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, False, "CUSTOMER")

        # Mã đơn không tồn tại
        self.assertFalse(self.om.complete_delivery("O999"))
        self.assertIn("Không tìm thấy đơn hàng", self.om.last_error)

        # Đơn đang PLACED, chưa DELIVERING
        self.assertFalse(self.om.complete_delivery("O001"))
        self.assertIn("không ở trạng thái DELIVERING", self.om.last_error)

    def test_cannot_cancel_delivering_or_paid(self) -> None:
        """Kiểm tra không thể hủy đơn khi ở trạng thái DELIVERING hoặc PAID."""
        items = self._make_item("M001")
        self.om.create_order("O001", "A", "a@test.com", items, 1700000000.0, False, "CUSTOMER")

        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.om.update_order_status("O001", OrderStatus.READY)
        self.om.start_delivery(["O001"])

        # Cố gắng hủy đơn khi DELIVERING -> Thất bại
        self.assertFalse(self.om.update_order_status("O001", OrderStatus.CANCELLED))
        self.assertIn("Không thể hủy", self.om.last_error)
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.DELIVERING)

        # Hoàn thành giao -> chuyển sang PAID
        self.assertTrue(self.om.complete_delivery("O001"))
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.PAID)

        # Cố gắng hủy đơn khi PAID -> Thất bại
        self.assertFalse(self.om.update_order_status("O001", OrderStatus.CANCELLED))
        self.assertIn("Không thể hủy", self.om.last_error)

    def test_update_order_status_guardrails(self) -> None:
        """Kiểm tra chặn chuyển DELIVERING và chặn PREPARING sai thứ tự ưu tiên."""
        now = time.time()
        # Đơn 1: Đơn thường, tạo trước 600 giây (đợi 10 phút), prep 10m
        items1 = self._make_item("M001", 1, prep=10)
        self.om.create_order("O001", "Khách thường", "a@test.com", items1, now - 600, False,
                             "CUSTOMER")

        # Đơn 2: Đơn VIP, mới tạo (đợi 0 phút), prep 10m -> VIP ưu tiên hơn theo công thức
        items2 = self._make_item("M002", 1, prep=10)
        self.om.create_order("O002", "Khách VIP", "b@test.com", items2, now, True,
                             "CUSTOMER_2")

        # Chặn chuyển thẳng vào DELIVERING
        self.assertFalse(self.om.update_order_status("O001", OrderStatus.DELIVERING))
        self.assertEqual(self.om.last_error, "Hãy dùng 'Bắt đầu giao' ở tab Bản đồ")

        # Cả 2 đơn chuyển sang CONFIRMED
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.om.update_order_status("O002", OrderStatus.CONFIRMED)

        # Cố chế biến O001 (đơn thường) khi O002 (VIP) đứng đầu -> Bị chặn
        self.assertFalse(self.om.update_order_status("O001", OrderStatus.PREPARING))
        self.assertIn("O002", self.om.last_error)
        self.assertIn("Khách VIP", self.om.last_error)
        self.assertIn("phải chế biến trước", self.om.last_error)

        # Chế biến O002 trước -> Thành công
        self.assertTrue(self.om.update_order_status("O002", OrderStatus.PREPARING))
        self.assertEqual(self.om.orders["O002"].status, OrderStatus.PREPARING)

    def test_undo_redo_and_clear_redo_on_new_action(self) -> None:
        """Kiểm tra Undo/Redo nhiều bước và thao tác mới làm xóa redo_stack."""
        items = self._make_item("M001")
        self.om.create_order("O001", "A", "a@test.com", items, 1700000000.0, False, "CUSTOMER")

        self.assertFalse(self.om.can_undo())
        self.assertFalse(self.om.can_redo())

        # PLACED -> CONFIRMED
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)
        self.assertTrue(self.om.can_undo())

        # CONFIRMED -> PREPARING
        self.om.update_order_status("O001", OrderStatus.PREPARING)
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.PREPARING)

        # Undo lần 1 -> về CONFIRMED
        self.assertTrue(self.om.undo())
        self.assertEqual(self.om.orders["O001"].status, OrderStatus.CONFIRMED)
        self.assertTrue(self.om.can_redo())

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
        self.assertFalse(self.om.can_redo())
        self.assertFalse(self.om.redo())

    def test_find_by_name_and_email_with_duplicates_and_case_insensitive(self) -> None:
        """Kiểm tra tìm kiếm theo tên và email không phân biệt hoa thường và tìm trùng lặp."""
        items = self._make_item("M001")
        self.om.create_order("O001", "Nguyễn Văn A", "shared@test.com", items, 100.0, False,
                             "CUSTOMER")
        self.om.create_order("O002", "nguyễn văn a", "shared@test.com", items, 200.0, False,
                             "CUSTOMER")
        self.om.create_order("O003", "Trần Văn B", "b@test.com", items, 300.0, False,
                             "CUSTOMER_2")

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
        items = self._make_item("M001", qty=2)
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, True, "CUSTOMER")
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)

        # Tạo instance mới trỏ cùng storage_path và graph
        om2 = OrderManager(storage_path=self.storage_path, graph=self.graph)
        self.assertEqual(len(om2.orders), 1)
        self.assertIn("O001", om2.orders)
        order = om2.orders["O001"]
        self.assertEqual(order.status, OrderStatus.CONFIRMED)
        self.assertTrue(order.is_vip)
        self.assertEqual(order.delivery_node_id, "CUSTOMER")
        self.assertEqual(len(om2.find_by_name("A")), 1)

    def test_corrupted_json_handling(self) -> None:
        """Kiểm tra file JSON bị hỏng cú pháp không làm crash, tự đổi tên .bak."""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON CONTENT !!!")

        om_corrupted = OrderManager(storage_path=self.storage_path, graph=self.graph)
        self.assertEqual(len(om_corrupted.orders), 0)

        # File hỏng phải được đổi thành .bak
        bak_file = self.storage_path.with_name(f"{self.storage_path.name}.bak")
        self.assertTrue(bak_file.exists())

    def test_safe_load_orders_corrupted_records(self) -> None:
        """Kiểm tra nạp dữ liệu an toàn khi có bản ghi cá biệt bị hỏng."""
        corrupted_data = [
            {"id": "O001", "customer_name": "A", "customer_email": "a@test.com",
             "status": "PLACED", "items": [{"item_id": "M001", "name": "Cơm", "quantity": 1,
                                            "price": 10000, "prep_minutes": 5}],
             "created_at": 100.0, "is_vip": False, "delivery_node_id": "CUSTOMER"},
            "chuỗi không phải dict",
            {"id": "O002", "customer_name": "B"},  # Thiếu trường email, items,...
            {"id": "O003", "customer_name": "C", "customer_email": "c@test.com",
             "status": "UNKNOWN_STATUS", "items": [{"item_id": "M001", "name": "Cơm",
                                                   "quantity": 1, "price": 10000,
                                                   "prep_minutes": 5}],
             "created_at": 100.0, "is_vip": False, "delivery_node_id": "CUSTOMER"},
        ]
        save_json(self.storage_path, corrupted_data)

        om_safe = OrderManager(storage_path=self.storage_path, graph=self.graph)
        # O001 hợp lệ nạp thành công
        self.assertEqual(len(om_safe.orders), 1)
        self.assertIn("O001", om_safe.orders)
        # Các bản ghi lỗi được ghi nhận vào load_errors mà không crash
        self.assertGreater(len(om_safe.load_errors), 0)

    def test_orders_property_immutability(self) -> None:
        """Kiểm tra thuộc tính om.orders trả về bản sao, không thể sửa đổi nội bộ."""
        items = self._make_item("M001")
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, False, "CUSTOMER")

        orders_copy = self.om.orders
        self.assertIn("O001", orders_copy)

        # Xóa trên bản sao
        orders_copy.clear()
        self.assertEqual(len(orders_copy), 0)

        # Dữ liệu nội bộ vẫn còn nguyên
        self.assertEqual(len(self.om.orders), 1)
        self.assertIsNotNone(self.om.get_order("O001"))

    def test_next_id_and_get_orders_by_status(self) -> None:
        """Kiểm tra next_id tự tăng và get_orders_by_status lọc đúng."""
        self.assertEqual(self.om.next_id(), "O001")
        items = self._make_item("M001")
        self.om.create_order("O001", "A", "a@test.com", items, 100.0, False, "CUSTOMER")
        self.assertEqual(self.om.next_id(), "O002")

        self.om.create_order("O002", "B", "b@test.com", items, 200.0, False, "CUSTOMER_2")
        self.om.update_order_status("O001", OrderStatus.CONFIRMED)

        placed = self.om.get_orders_by_status(OrderStatus.PLACED)
        confirmed = self.om.get_orders_by_status(OrderStatus.CONFIRMED)
        self.assertEqual(len(placed), 1)
        self.assertEqual(placed[0].id, "O002")
        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0].id, "O001")
        self.assertEqual(len(self.om.get_all_orders()), 2)


if __name__ == "__main__":
    unittest.main()
