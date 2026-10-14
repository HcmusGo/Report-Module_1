"""Xem dữ liệu khởi tạo sẵn: địa điểm, đường, shipper (chỉ đọc). Người phụ trách: Quyên."""
from __future__ import annotations

from models.map_entities import Place, PlaceKind, Road
from models.shipper import Shipper
from repositories.base_repository import Repository


class CatalogService:
    """Không có thêm / sửa / xóa: các dữ liệu này nạp sẵn từ data/*.json."""

    def __init__(self, places: Repository[Place], roads: Repository[Road],
                 shippers: Repository[Shipper]) -> None:
        self._places, self._roads, self._shippers = places, roads, shippers

    def list_places(self, kind: PlaceKind | None = None) -> list[Place]:
        raise NotImplementedError("TODO(Quyên)")

    def list_roads(self) -> list[Road]:
        raise NotImplementedError("TODO(Quyên)")

    def list_shippers(self) -> list[Shipper]:
        raise NotImplementedError("TODO(Quyên)")

    def place_name(self, place_id: str) -> str:
        """Tên hiển thị của một địa điểm; không thấy thì ném NotFoundError."""
        raise NotImplementedError("TODO(Quyên)")
