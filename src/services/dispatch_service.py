"""Điều phối shipper: gán shipper gần nhất, lộ trình 2 chặng, ETA, phí ship. Người phụ trách: Bảo."""
from __future__ import annotations

from dataclasses import dataclass, field

from models.customer import Customer
from models.order import Order
from models.shipper import Shipper
from repositories.base_repository import Repository
from services.history import CommandHistory
from services.map_service import MapService
from services.routing import Router


@dataclass(frozen=True)
class RoutePlan:
    """Kết quả lập lộ trình giao một đơn (UI chỉ việc hiển thị)."""

    order_id: str
    shipper_id: str
    path_to_restaurant: list[str] = field(default_factory=list)   # shipper -> quán (id nút)
    path_to_customer: list[str] = field(default_factory=list)     # quán -> khách (id nút)
    minutes_to_restaurant: float = 0.0
    minutes_to_customer: float = 0.0
    distance_km: float = 0.0          # quãng đường quán -> khách, dùng tính phí ship
    eta_minutes: float = 0.0          # = bếp còn lại + shipper -> quán + quán -> khách
    delivery_fee: int = 0
    nodes_visited: int = 0


class DispatchService:
    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 customers: Repository[Customer], maps: MapService, router: Router,
                 history: CommandHistory) -> None:
        self._orders, self._shippers, self._customers = orders, shippers, customers
        self._maps, self._router, self._history = maps, router, history

    def find_nearest_idle_shipper(self) -> tuple[Shipper, float] | None:
        """Chạy router.distances_from() MỘT LẦN từ quán, chọn shipper IDLE có thời gian
        đến quán nhỏ nhất. Không có shipper rảnh thì trả None."""
        raise NotImplementedError("TODO(Bảo)")

    def plan_delivery(self, order_id: str, shipper_id: str | None = None) -> RoutePlan:
        """Lập lộ trình (chưa thay đổi dữ liệu). Không có đường đến khách thì ném BusinessRuleError."""
        raise NotImplementedError("TODO(Bảo)")

    def assign_shipper(self, order_id: str) -> RoutePlan:
        """Đơn phải READY. Lập kế hoạch rồi history.execute(AssignShipperCmd)."""
        raise NotImplementedError("TODO(Bảo)")

    def complete_delivery(self, order_id: str) -> Order:
        """DELIVERING -> DELIVERED, shipper về IDLE và đứng tại nút của khách."""
        raise NotImplementedError("TODO(Bảo)")

    def calculate_fee(self, distance_km: float) -> int:
        """Phí ship theo config.BASE_FEE và config.FEE_PER_KM."""
        raise NotImplementedError("TODO(Bảo)")

    def estimate_eta(self, order: Order, minutes_to_restaurant: float, minutes_to_customer: float) -> float:
        """Thời gian bếp còn lại + shipper -> quán + quán -> khách."""
        raise NotImplementedError("TODO(Bảo)")

    def compare_routers(self, src: str, dst: str, routers: list[Router]) -> list[dict]:
        """Chạy từng router, trả [{'router': 'Dijkstra', 'cost': 12.4, 'nodes_visited': 31, 'ms': 0.2}, ...]."""
        raise NotImplementedError("TODO(Bảo)")
