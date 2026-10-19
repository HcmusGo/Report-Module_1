from typing import List, Optional
from exceptions import NotFoundError
from models.map_entities import Place, Road
from models.shipper import Shipper
from repositories.base_repository import Repository

class CatalogService:
    def __init__(
        self,
        place_repo: Repository[Place],
        road_repo: Repository[Road],
        shipper_repo: Repository[Shipper]
    ):
        self._place_repo = place_repo
        self._road_repo = road_repo
        self._shipper_repo = shipper_repo

    def get_place(self, place_id: str) -> Place:
        place = self._place_repo.get_by_id(place_id)
        if not place:
            raise NotFoundError(f"Không tìm thấy địa điểm với ID: {place_id}")
        return place

    def place_name(self, place_id: str) -> str:
        """Trả về tên địa điểm, ném NotFoundError nếu không thấy."""
        place = self._place_repo.get_by_id(place_id)
        if not place:
            raise NotFoundError(f"Không tìm thấy địa điểm với ID: {place_id}")
        return place.name

    def list_places(self) -> List[Place]:
        return self._place_repo.get_all()

    def list_roads(self) -> List[Road]:
        return self._road_repo.get_all()

    def list_shippers(self) -> List[Shipper]:
        return self._shipper_repo.get_all()
