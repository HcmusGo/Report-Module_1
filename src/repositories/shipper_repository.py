"""Lưu shipper vào data/shippers.json. Người phụ trách: Tâm."""
from __future__ import annotations

from models.shipper import Shipper, ShipperStatus
from repositories.json_repository import JsonRepository


class ShipperRepository(JsonRepository[Shipper]):
    filename = "shippers.json"
    id_prefix = "S"

    @classmethod
    def _entity_from_dict(cls, data: dict) -> Shipper:
        return Shipper.from_dict(data)

    def find_by_status(self, status: ShipperStatus) -> list[Shipper]:
        """Shipper theo trạng thái, ví dụ IDLE để Dispatcher chọn."""
        raise NotImplementedError("TODO(Tâm)")
