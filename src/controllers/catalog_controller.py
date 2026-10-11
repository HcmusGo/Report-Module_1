"""Controller cho Tab 1: Quản lý dữ liệu. Người phụ trách: Lâm.

Mỗi hàm thao tác: try gọi Service, bắt AppError -> Result.fail(str(e)),
thành công -> Result.success("Đã thêm món ..."). KHÔNG chứa luật nghiệp vụ.
Mỗi hàm *_table() trả list[dict] (một dict một dòng) để st.dataframe hiển thị.
"""
from __future__ import annotations

from controllers.result import Result
from services.catalog_service import CatalogService
from services.map_service import MapService


class CatalogController:
    def __init__(self, catalog: CatalogService, maps: MapService) -> None:
        self._catalog, self._maps = catalog, maps

    # ---- Menu ----
    def menu_table(self, keyword: str = "") -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def add_menu_item(self, name: str, price: int, prep_minutes: int, tags_text: str = "") -> Result:
        """tags_text: chuỗi 'cay, bán chạy' do người dùng gõ, tách thành set ở đây."""
        raise NotImplementedError("TODO(Lâm)")

    def update_menu_item(self, item_id: str, **changes) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def delete_menu_item(self, item_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    # ---- Khách hàng ----
    def customer_table(self, keyword: str = "") -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def add_customer(self, name: str, phone: str, node_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def update_customer(self, customer_id: str, **changes) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def delete_customer(self, customer_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    # ---- Shipper ----
    def shipper_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def add_shipper(self, name: str, phone: str, node_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def update_shipper(self, shipper_id: str, **changes) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def delete_shipper(self, shipper_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    # ---- Bản đồ ----
    def place_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def road_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def add_place(self, name: str, x: float, y: float, kind: str = "JUNCTION") -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def add_road(self, a: str, b: str, distance_km: float, traffic_factor: float = 1.0) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def update_road(self, road_id: str, **changes) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def delete_road(self, road_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def set_road_blocked(self, road_id: str, blocked: bool) -> Result:
        raise NotImplementedError("TODO(Lâm)")
