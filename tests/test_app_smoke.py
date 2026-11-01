"""
Smoke tests cho ứng dụng Streamlit src/app.py sử dụng AppTest (Milestone M4).
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.core.order_manager import OrderManager
from src.core.routing_service import load_map_graph
from src.models.order import OrderStatus, make_item_snapshot


APP_PATH = str(Path(__file__).resolve().parent.parent / "src" / "app.py")


class TestAppSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "test_smoke_orders.json"
        graph = load_map_graph()
        self.om = OrderManager(storage_path=self.storage_path, graph=graph)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_app_smoke_all_tabs_and_no_exceptions(self) -> None:
        """Xác nhận ứng dụng khởi chạy bình thường, có đủ 4 tab và không có ngoại lệ."""
        at = AppTest.from_file(APP_PATH)
        at.session_state["order_manager"] = self.om
        at.run(timeout=10)

        # Không có ngoại lệ chưa xử lý
        self.assertEqual(len(at.exception), 0, f"App gặp ngoại lệ: {at.exception}")

        # Xác nhận đủ 4 tab nghiệp vụ
        self.assertEqual(len(at.tabs), 4)
        tab_labels = {t.label for t in at.tabs}
        expected_labels = {
            "Bản đồ / Lộ trình",
            "Menu",
            "Hàng đợi chế biến",
            "Đơn hàng",
        }
        self.assertEqual(tab_labels, expected_labels)

    def test_map_tab_displays_multiselect_when_ready_orders_exist(self) -> None:
        """Xác nhận tab Bản đồ hiển thị multiselect gom chuyến khi có đơn hàng READY."""
        # Tạo đơn hàng và chuyển trạng thái sang READY
        items = [make_item_snapshot("M001", "Cơm tấm", 1, 45000, 15)]
        created = self.om.create_order(
            order_id="O_SMOKE_1",
            customer_name="Nguyễn Văn An",
            customer_email="an@example.com",
            items=items,
            created_at=1700000000.0,
            is_vip=True,
            delivery_node_id="CUSTOMER",
        )
        self.assertTrue(created)
        self.om.update_order_status("O_SMOKE_1", OrderStatus.CONFIRMED)
        self.om.update_order_status("O_SMOKE_1", OrderStatus.PREPARING)
        self.om.update_order_status("O_SMOKE_1", OrderStatus.READY)

        at = AppTest.from_file(APP_PATH)
        at.session_state["order_manager"] = self.om
        at.run(timeout=10)

        self.assertEqual(len(at.exception), 0, f"App gặp ngoại lệ: {at.exception}")

        # Tìm multiselect gom chuyến có key map_batch_order_select
        batch_multiselects = [
            ms for ms in at.multiselect if ms.key == "map_batch_order_select"
        ]
        self.assertEqual(len(batch_multiselects), 1)
        ms_widget = batch_multiselects[0]
        self.assertTrue(
            any("O_SMOKE_1" in opt for opt in ms_widget.options),
            f"O_SMOKE_1 không có trong danh sách options: {ms_widget.options}",
        )


if __name__ == "__main__":
    unittest.main()
