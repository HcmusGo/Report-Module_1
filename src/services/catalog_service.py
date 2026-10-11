"""CRUD menu, khách hàng, shipper. Người phụ trách: Quyên."""
from __future__ import annotations

from models.customer import Customer
from models.menu_item import MenuItem
from models.shipper import Shipper, ShipperStatus
from repositories.base_repository import Repository


class CatalogService:
    """Validate nghiệp vụ rồi gọi Repository. Lỗi thì ném exceptions.AppError.

    Luật gợi ý: không xóa món đang nằm trong đơn chưa hoàn tất,
    không xóa khách có đơn chưa hoàn tất, không xóa shipper đang BUSY,
    node_id của khách / shipper phải là Place có thật (kiểm tra qua MapService hoặc truyền vào).
    """

    def __init__(self, menu: Repository[MenuItem], customers: Repository[Customer],
                 shippers: Repository[Shipper]) -> None:
        self._menu, self._customers, self._shippers = menu, customers, shippers

    # ---- Menu ----
    def list_menu(self, keyword: str = "", tag: str | None = None) -> list[MenuItem]:
        raise NotImplementedError("TODO(Quyên)")

    def add_menu_item(self, name: str, price: int, prep_minutes: int,
                      tags: set[str] | None = None) -> MenuItem:
        raise NotImplementedError("TODO(Quyên)")

    def update_menu_item(self, item_id: str, **changes) -> MenuItem:
        raise NotImplementedError("TODO(Quyên)")

    def delete_menu_item(self, item_id: str) -> None:
        raise NotImplementedError("TODO(Quyên)")

    # ---- Khách hàng ----
    def list_customers(self, keyword: str = "") -> list[Customer]:
        raise NotImplementedError("TODO(Quyên)")

    def add_customer(self, name: str, phone: str, node_id: str) -> Customer:
        raise NotImplementedError("TODO(Quyên)")

    def update_customer(self, customer_id: str, **changes) -> Customer:
        raise NotImplementedError("TODO(Quyên)")

    def delete_customer(self, customer_id: str) -> None:
        raise NotImplementedError("TODO(Quyên)")

    # ---- Shipper ----
    def list_shippers(self, status: ShipperStatus | None = None) -> list[Shipper]:
        raise NotImplementedError("TODO(Quyên)")

    def add_shipper(self, name: str, phone: str, node_id: str) -> Shipper:
        raise NotImplementedError("TODO(Quyên)")

    def update_shipper(self, shipper_id: str, **changes) -> Shipper:
        raise NotImplementedError("TODO(Quyên)")

    def delete_shipper(self, shipper_id: str) -> None:
        raise NotImplementedError("TODO(Quyên)")
