"""Controller cho Tab 1: Quản lý đơn hàng. Người phụ trách: Lâm.

Mỗi hàm thao tác: try gọi Service, bắt AppError -> Result.fail(str(e)),
thành công -> Result.success("Đã tạo đơn O007"). KHÔNG chứa luật nghiệp vụ.
Mỗi hàm *_table() trả list[dict] (một dict một dòng) cho st.dataframe.
"""
from __future__ import annotations

from controllers.result import Result
from services.catalog_service import CatalogService
from services.order_service import OrderService


class OrderController:
    def __init__(self, orders: OrderService, catalog: CatalogService) -> None:
        self._orders, self._catalog = orders, catalog

    # ---- CRUD đơn hàng ----
    def order_table(self, status: str | None = None, keyword: str = "") -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def create_order(self, customer_name: str, pickup_node: str, delivery_node: str,
                     weight_kg: float, deadline_min: int | None = None, note: str = "") -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def update_order(self, order_id: str, **changes) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def delete_order(self, order_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    # ---- Dữ liệu khởi tạo sẵn (chỉ xem) ----
    def place_options(self, kind: str | None = None) -> list[tuple[str, str]]:
        """[(id, tên)] cho ô chọn địa điểm."""
        raise NotImplementedError("TODO(Lâm)")

    def place_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def road_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def shipper_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")
