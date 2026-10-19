from __future__ import annotations

from models.menu_item import MenuItem
from repositories.json_repository import JsonRepository


class MenuRepository(JsonRepository[MenuItem]):
    filename = "menu.json"
    id_prefix = "M"

    @classmethod
    def _entity_from_dict(cls, data: dict) -> MenuItem:
        return MenuItem.from_dict(data)
