"""Đề xuất shipper phù hợp cho đơn và tìm đường. Người phụ trách: Bảo."""
from __future__ import annotations

from dataclasses import dataclass, field

from models.order import Order
from models.shipper import Shipper
from repositories.base_repository import Repository
from services.history import CommandHistory
from services.order_queue import OrderQueue
from services.routing import RoadNetwork, Router


@dataclass(frozen=True)
class Suggestion:
    """Đánh giá một shipper cho một đơn (UI chỉ việc hiển thị)."""

    order_id: str
    shipper_id: str
    feasible: bool = True
    reason: str = ""                      # khi không phù hợp: 'vượt tải', 'trễ hạn', 'không có đường'
    free_capacity_kg: float = 0.0
    minutes_to_pickup: float = 0.0        # từ điểm cuối lộ trình hiện tại tới điểm lấy hàng
    minutes_pickup_to_delivery: float = 0.0
    eta_minutes: float = 0.0              # = thời gian hoàn thành lộ trình hiện tại + 2 chặng trên
    path_to_pickup: list[str] = field(default_factory=list)
    path_to_delivery: list[str] = field(default_factory=list)


class DispatchService:
    def __init__(self, orders: Repository[Order], shippers: Repository[Shipper],
                 network: RoadNetwork, router: Router, queue: OrderQueue,
                 history: CommandHistory) -> None:
        self._orders, self._shippers = orders, shippers
        self._network, self._router = network, router
        self._queue, self._history = queue, history

    def suggest(self, order_id: str) -> list[Suggestion]:
        """Đánh giá MỌI shipper cho đơn, trả về danh sách đã sắp xếp: phù hợp trước (eta tăng
        dần, hòa thì tải nhẹ hơn trước), không phù hợp sau kèm lý do. Với mỗi shipper:
        1. start = điểm cuối lộ trình hiện tại (route rỗng thì vị trí hiện tại).
        2. Loại 'vượt tải' nếu load_kg + weight_kg > capacity_kg.
        3. eta = thời gian đi hết lộ trình hiện tại + Dijkstra(start -> pickup)
           + Dijkstra(pickup -> delivery), tính theo thời gian.
        4. Loại 'trễ hạn' nếu đơn có deadline_min và eta > deadline_min.
        5. Loại 'không có đường' nếu một chặng không tìm được đường."""
        raise NotImplementedError("TODO(Bảo)")

    def best(self, order_id: str) -> Suggestion | None:
        """Shipper phù hợp nhất, không có ai phù hợp thì trả None."""
        raise NotImplementedError("TODO(Bảo)")

    def assign(self, order_id: str, shipper_id: str | None = None) -> Suggestion:
        """Gán đơn cho shipper (mặc định là best). Đơn phải WAITING, shipper phải phù hợp.
        Dùng AssignOrderCmd qua self._history.execute() để Undo được."""
        raise NotImplementedError("TODO(Bảo)")

    def complete_next_stop(self, shipper_id: str) -> Order | None:
        """Shipper hoàn thành điểm dừng đầu lộ trình (CompleteStopCmd). Trả đơn vừa giao xong
        (nếu điểm dừng là DELIVERY), ngược lại trả None."""
        raise NotImplementedError("TODO(Bảo)")

    def route_minutes(self, shipper: Shipper) -> float:
        """Thời gian đi lần lượt qua các điểm dừng còn lại, bắt đầu từ vị trí hiện tại."""
        raise NotImplementedError("TODO(Bảo)")

    def compare_time_vs_distance(self, src: str, dst: str) -> list[dict]:
        """Trả 2 dòng: đường NGẮN NHẤT theo km và đường NHANH NHẤT theo phút trên cùng cặp điểm,
        mỗi dòng {'tiêu chí', 'đường đi', 'km', 'phút'} để chứng minh vì sao phải dùng thời gian."""
        raise NotImplementedError("TODO(Bảo)")
