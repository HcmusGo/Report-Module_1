"""Đề xuất shipper phù hợp cho đơn và tìm đường. Người phụ trách: Bảo."""
from __future__ import annotations

from dataclasses import dataclass, field

from exceptions import BusinessRuleError, NotFoundError, ValidationError
from models.order import Order, OrderStatus
from models.shipper import Shipper, StopKind
from repositories.base_repository import Repository
from services.commands import AssignOrderCmd, CompleteStopCmd
from services.history import CommandHistory
from services.order_queue import OrderQueue
from services.routing import RoadNetwork, Router

# Lý do loại shipper (đúng các giá trị ghi trong Suggestion.reason).
REASON_OVERLOAD = "vượt tải"
REASON_LATE = "trễ hạn"
REASON_NO_PATH = "không có đường"

_INF = float("inf")
_EPS = 1e-9   # dung sai so sánh số thực (tránh 20.000000001 > 20 do làm tròn)


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

    # ------------------------------------------------------------------ helpers
    def _get_order(self, order_id: str) -> Order:
        order = self._orders.get_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Không tìm thấy đơn {order_id}")
        return order

    def _get_shipper(self, shipper_id: str) -> Shipper:
        shipper = self._shippers.get_by_id(shipper_id)
        if shipper is None:
            raise NotFoundError(f"Không tìm thấy shipper {shipper_id}")
        return shipper

    def _evaluate(self, order: Order, shipper: Shipper) -> Suggestion:
        """Đánh giá một shipper cho một đơn theo 5 bước trong docstring của suggest()."""
        # 1. Điểm xuất phát cho đơn mới = điểm cuối lộ trình (route rỗng -> vị trí hiện tại).
        start = shipper.last_node_id

        # 2. Tải trọng.
        overloaded = shipper.load_kg + order.weight_kg > shipper.capacity_kg + _EPS

        # 3. ETA = đi hết lộ trình hiện tại + start -> pickup + pickup -> delivery (theo phút).
        to_pickup = self._router.shortest_path(self._network, start, order.pickup_node, by="time")
        to_delivery = self._router.shortest_path(
            self._network, order.pickup_node, order.delivery_node, by="time")
        current_route = self.route_minutes(shipper)
        has_path = to_pickup.found and to_delivery.found and current_route != _INF
        eta = current_route + to_pickup.minutes + to_delivery.minutes if has_path else _INF

        # 4. Hạn giao.
        late = (has_path and order.deadline_min is not None
                and eta > order.deadline_min + _EPS)

        # Một lý do duy nhất, ưu tiên: vượt tải > không có đường > trễ hạn.
        if overloaded:
            reason = REASON_OVERLOAD
        elif not has_path:   # 5. Một chặng không tìm được đường.
            reason = REASON_NO_PATH
        elif late:
            reason = REASON_LATE
        else:
            reason = ""

        return Suggestion(
            order_id=order.id,
            shipper_id=shipper.id,
            feasible=not reason,
            reason=reason,
            free_capacity_kg=shipper.free_capacity_kg,
            minutes_to_pickup=to_pickup.minutes,
            minutes_pickup_to_delivery=to_delivery.minutes,
            eta_minutes=eta,
            path_to_pickup=list(to_pickup.path),
            path_to_delivery=list(to_delivery.path),
        )

    # ------------------------------------------------------------------ API
    def suggest(self, order_id: str) -> list[Suggestion]:
        """Đánh giá MỌI shipper cho đơn, trả về danh sách đã sắp xếp: phù hợp trước (eta tăng
        dần, hòa thì tải nhẹ hơn trước), không phù hợp sau kèm lý do. Với mỗi shipper:
        1. start = điểm cuối lộ trình hiện tại (route rỗng thì vị trí hiện tại).
        2. Loại 'vượt tải' nếu load_kg + weight_kg > capacity_kg.
        3. eta = thời gian đi hết lộ trình hiện tại + Dijkstra(start -> pickup)
           + Dijkstra(pickup -> delivery), tính theo thời gian.
        4. Loại 'trễ hạn' nếu đơn có deadline_min và eta > deadline_min.
        5. Loại 'không có đường' nếu một chặng không tìm được đường."""
        order = self._get_order(order_id)
        rated: list[tuple[Suggestion, float]] = [
            (self._evaluate(order, shipper), shipper.load_kg)
            for shipper in self._shippers.get_all()
        ]
        # Phù hợp trước; trong mỗi nhóm: eta tăng dần, hòa thì tải nhẹ hơn, rồi theo id cho ổn định.
        rated.sort(key=lambda item: (not item[0].feasible, item[0].eta_minutes,
                                     item[1], item[0].shipper_id))
        return [s for s, _ in rated]

    def best(self, order_id: str) -> Suggestion | None:
        """Shipper phù hợp nhất, không có ai phù hợp thì trả None."""
        suggestions = self.suggest(order_id)
        if suggestions and suggestions[0].feasible:
            return suggestions[0]
        return None

    def assign(self, order_id: str, shipper_id: str | None = None) -> Suggestion:
        """Gán đơn cho shipper (mặc định là best). Đơn phải WAITING, shipper phải phù hợp.
        Dùng AssignOrderCmd qua self._history.execute() để Undo được."""
        order = self._get_order(order_id)
        if order.status != OrderStatus.WAITING:
            status = getattr(order.status, "value", order.status)
            raise BusinessRuleError(
                f"Chỉ gán được đơn đang chờ (WAITING); đơn {order_id} đang ở trạng thái {status}")

        if shipper_id is None:
            chosen = self.best(order_id)
            if chosen is None:
                raise BusinessRuleError(f"Không có shipper nào phù hợp cho đơn {order_id}")
        else:
            if not str(shipper_id).strip():
                raise ValidationError("Mã shipper không được để trống")
            self._get_shipper(shipper_id)   # NotFoundError nếu không tồn tại
            chosen = next(s for s in self.suggest(order_id) if s.shipper_id == shipper_id)
            if not chosen.feasible:
                raise BusinessRuleError(
                    f"Shipper {shipper_id} không phù hợp cho đơn {order_id}: {chosen.reason}")

        self._history.execute(AssignOrderCmd(
            self._orders, self._shippers, self._queue, order_id, chosen.shipper_id))
        return chosen

    def complete_next_stop(self, shipper_id: str) -> Order | None:
        """Shipper hoàn thành điểm dừng đầu lộ trình (CompleteStopCmd). Trả đơn vừa giao xong
        (nếu điểm dừng là DELIVERY), ngược lại trả None."""
        shipper = self._get_shipper(shipper_id)
        if not shipper.route:
            raise BusinessRuleError(f"Shipper {shipper_id} không còn điểm dừng nào")

        # Ghi lại thông tin điểm dừng TRƯỚC khi lệnh popleft khỏi route.
        stop = shipper.route[0]
        stop_order_id, stop_kind = stop.order_id, stop.kind

        self._history.execute(CompleteStopCmd(self._orders, self._shippers, shipper_id))

        if stop_kind == StopKind.DELIVERY:
            return self._orders.get_by_id(stop_order_id)
        return None

    def route_minutes(self, shipper: Shipper) -> float:
        """Thời gian đi lần lượt qua các điểm dừng còn lại, bắt đầu từ vị trí hiện tại."""
        total = 0.0
        current = shipper.node_id
        for stop in shipper.route:
            leg = self._router.shortest_path(self._network, current, stop.node_id, by="time")
            if not leg.found:
                return _INF
            total += leg.minutes
            current = stop.node_id
        return total

    def compare_time_vs_distance(self, src: str, dst: str) -> list[dict]:
        """Trả 2 dòng: đường NGẮN NHẤT theo km và đường NHANH NHẤT theo phút trên cùng cặp điểm,
        mỗi dòng {'tiêu chí', 'đường đi', 'km', 'phút'} để chứng minh vì sao phải dùng thời gian."""
        rows: list[dict] = []
        for label, by in (("Ngắn nhất (km)", "distance"), ("Nhanh nhất (phút)", "time")):
            result = self._router.shortest_path(self._network, src, dst, by=by)
            rows.append({
                "tiêu chí": label,
                "đường đi": " → ".join(result.path) if result.found else REASON_NO_PATH,
                "km": round(result.distance_km, 2),
                "phút": round(result.minutes, 2),
            })
        return rows
