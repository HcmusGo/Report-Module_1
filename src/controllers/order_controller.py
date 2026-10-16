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
        return self._orders.order_table (status=status, keyword=keyword)

    def create_order(self, customer_name: str, pickup_node: str, delivery_node: str,
                     weight_kg: float, deadline_min: int | None = None, note: str = "") -> Result:
        try 
        self._orders.create_order(customer_name=customer_namej, pickup_node=pickup_node, delivery_node=delivery_node, weight_kg=weight_kg, deadline_min=deadline_min, note=note) = order_id
        return Result.success ("Đã tạo đơn {order_id} thành công")
        except AppError as e:
            return Result.fail(str(e))
    def update_order(self, order_id: str, **changes) -> Result:
        try 
        self._orders.update.order(order_id=order_id)
        return Result.success ("Cập nhật đơn hàng thành công")
        except AppError as e:
            return Result.fail(str(e))

    def delete_order(self, order_id: str) -> Result:
        try 
        self._orders.delete_order(order_id=order_id)
        return Result.success ("Xóa đơn hàng thành công")
        except AppError as e:
            return Result.fail(str(e))

    # ---- Dữ liệu khởi tạo sẵn (chỉ xem) ----
    def place_options(self, kind: str | None = None) -> list[tuple[str, str]]:
        """[(id, tên)] cho ô chọn địa điểm."""
        return self._catalog.place_options (kind=kind)
    def place_table(self) -> list[dict]:
        return self._catalog.place_table ()

    def road_table(self) -> list[dict]:
        return self._catalog.road_table ()

    def shipper_table(self) -> list[dict]:
        return self._catalog.shipper_table ()
