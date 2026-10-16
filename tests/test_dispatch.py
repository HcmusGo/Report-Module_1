"""Kiểm thử DispatchService (services/dispatch_service.py). Người phụ trách: Bảo.

Order / Shipper / Stop / Place / Road (Quyên), CommandHistory / OrderQueue / các Command (Tiên)
có thể chưa cài đặt xong ở nhánh hiện tại, nên file này:
- tự định nghĩa entity giả lập; nếu lớp thật đã dùng được thì tự chuyển sang lớp thật;
- dùng FakeHistory ghi lại các Command được execute và MÔ PHỎNG tác dụng của chúng, để
  kiểm thử DispatchService độc lập với phần cài đặt Command của thành viên khác.
"""
from __future__ import annotations

import json
from collections import deque
from typing import Any, Callable, cast

import pytest

from config import SAMPLE_DIR, TRAFFIC_SPEED_KMH
from exceptions import BusinessRuleError, NotFoundError, ValidationError
from models.base import BaseEntity
from models.map_entities import Place, PlaceKind, Road, TrafficLevel
from models.order import Order, OrderStatus
from models.shipper import Shipper, Stop, StopKind
from repositories.base_repository import Repository
from services.commands import AssignOrderCmd, CompleteStopCmd
from services.dispatch_service import (REASON_LATE, REASON_NO_PATH, REASON_OVERLOAD,
                                       DispatchService, Suggestion)
from services.history import Command, CommandHistory
from services.order_queue import OrderQueue
from services.routing import DijkstraRouter, RoadNetwork

INF = float("inf")


# ---------------------------------------------------------------------------
# Entity giả lập (dùng khi lớp thật còn NotImplementedError)
# ---------------------------------------------------------------------------
class FakePlace(BaseEntity):
    def __init__(self, id: str, name: str, x: float, y: float,
                 kind: PlaceKind = PlaceKind.JUNCTION) -> None:
        self._id, self.name, self.x, self.y, self.kind = id, name, x, y, kind

    @property
    def id(self) -> str:
        return self._id

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "x": self.x, "y": self.y,
                "kind": self.kind.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FakePlace":
        return cls(data["id"], data["name"], data["x"], data["y"], PlaceKind(data["kind"]))


class FakeRoad(BaseEntity):
    def __init__(self, id: str, a: str, b: str, distance_km: float,
                 traffic: TrafficLevel = TrafficLevel.MEDIUM) -> None:
        self._id, self.a, self.b = id, a, b
        self.distance_km, self.traffic = distance_km, traffic

    @property
    def id(self) -> str:
        return self._id

    @property
    def minutes(self) -> float:
        return self.distance_km / TRAFFIC_SPEED_KMH[self.traffic.value] * 60

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "a": self.a, "b": self.b,
                "distance_km": self.distance_km, "traffic": self.traffic.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FakeRoad":
        return cls(data["id"], data["a"], data["b"], data["distance_km"],
                   TrafficLevel(data["traffic"]))


class FakeStop:
    def __init__(self, order_id: str, node_id: str, kind: StopKind) -> None:
        self.order_id, self.node_id, self.kind = order_id, node_id, kind

    def to_dict(self) -> dict[str, Any]:
        return {"order_id": self.order_id, "node_id": self.node_id, "kind": self.kind.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FakeStop":
        return cls(data["order_id"], data["node_id"], StopKind(data["kind"]))


class FakeOrder(BaseEntity):
    def __init__(self, id: str, customer_name: str, pickup_node: str, delivery_node: str,
                 weight_kg: float, deadline_min: int | None = None,
                 status: OrderStatus = OrderStatus.WAITING, shipper_id: str | None = None,
                 note: str = "", created_at: str = "") -> None:
        self._id, self.customer_name = id, customer_name
        self.pickup_node, self.delivery_node = pickup_node, delivery_node
        self.weight_kg, self.deadline_min = weight_kg, deadline_min
        self.status, self.shipper_id = status, shipper_id
        self.note, self.created_at = note, created_at

    @property
    def id(self) -> str:
        return self._id

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "customer_name": self.customer_name,
                "pickup_node": self.pickup_node, "delivery_node": self.delivery_node,
                "weight_kg": self.weight_kg, "deadline_min": self.deadline_min,
                "status": self.status.value, "shipper_id": self.shipper_id,
                "note": self.note, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FakeOrder":
        return cls(data["id"], data["customer_name"], data["pickup_node"],
                   data["delivery_node"], data["weight_kg"], data.get("deadline_min"),
                   OrderStatus(data.get("status", "WAITING")), data.get("shipper_id"),
                   data.get("note", ""), data.get("created_at", ""))


class FakeShipper(BaseEntity):
    def __init__(self, id: str, name: str, node_id: str, capacity_kg: float,
                 load_kg: float = 0.0, route: "deque | None" = None) -> None:
        self._id, self.name, self.node_id = id, name, node_id
        self.capacity_kg, self.load_kg = capacity_kg, load_kg
        self.route: deque = deque(route or [])

    @property
    def id(self) -> str:
        return self._id

    @property
    def free_capacity_kg(self) -> float:
        return self.capacity_kg - self.load_kg

    @property
    def last_node_id(self) -> str:
        return self.route[-1].node_id if self.route else self.node_id

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "node_id": self.node_id,
                "capacity_kg": self.capacity_kg, "load_kg": self.load_kg,
                "route": [s.to_dict() for s in self.route]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FakeShipper":
        return cls(data["id"], data["name"], data["node_id"], data["capacity_kg"],
                   data.get("load_kg", 0.0),
                   deque(FakeStop.from_dict(s) for s in data.get("route", [])))


# ---------------------------------------------------------------------------
# Chọn lớp thật nếu đã cài xong, ngược lại dùng lớp giả lập
# ---------------------------------------------------------------------------
def _real_map_ready() -> bool:
    try:
        Place("PX", "x", 0, 0, PlaceKind.SHOP)  # type: ignore
        road = Road("RX", "PX", "PY", 1.0, TrafficLevel.LOW)  # type: ignore
        return road.minutes == pytest.approx(1.5) and road.a == "PX" and road.b == "PY"
    except Exception:
        return False


def _real_models_ready() -> bool:
    try:
        stop = Stop("OX", "PY", StopKind.DELIVERY)  # type: ignore
        order = Order("OX", "Khách", "PX", "PY", 2.0, 10)  # type: ignore
        shipper = Shipper("SX", "Shipper", "PX", 10.0, 1.0, deque([stop]))  # type: ignore
        return (order.weight_kg == 2.0 and order.status == OrderStatus.WAITING
                and shipper.free_capacity_kg == pytest.approx(9.0)
                and shipper.last_node_id == "PY" and stop.kind == StopKind.DELIVERY)
    except Exception:
        return False


PlaceCls: Callable[..., Any]
RoadCls: Callable[..., Any]
OrderCls: Callable[..., Any]
ShipperCls: Callable[..., Any]
StopCls: Callable[..., Any]
if _real_map_ready():
    PlaceCls, RoadCls = cast(Callable[..., Any], Place), cast(Callable[..., Any], Road)
else:
    PlaceCls, RoadCls = FakePlace, FakeRoad
if _real_models_ready():
    OrderCls = cast(Callable[..., Any], Order)
    ShipperCls = cast(Callable[..., Any], Shipper)
    StopCls = cast(Callable[..., Any], Stop)
else:
    OrderCls, ShipperCls, StopCls = FakeOrder, FakeShipper, FakeStop


# ---------------------------------------------------------------------------
# Repository / Queue / History giả lập
# ---------------------------------------------------------------------------
class FakeRepository(Repository):
    def __init__(self, items: list | None = None) -> None:
        self._items = {e.id: e for e in (items or [])}

    def get_all(self) -> list:
        return list(self._items.values())

    def get_by_id(self, entity_id: str):
        return self._items.get(entity_id)

    def add(self, entity) -> None:
        if entity.id in self._items:
            raise ValidationError(f"Trùng id {entity.id}")
        self._items[entity.id] = entity

    def update(self, entity) -> None:
        if entity.id not in self._items:
            raise NotFoundError(entity.id)
        self._items[entity.id] = entity

    def delete(self, entity_id: str):
        return self._items.pop(entity_id, None)

    def next_id(self) -> str:
        return f"X{len(self._items) + 1:03d}"


class FakeQueue(OrderQueue):
    """Hàng đợi FIFO tối giản trên list (OrderQueue thật có thể chưa cài)."""

    def __init__(self, items: list[str] | None = None) -> None:
        self._items: list[str] = list(items or [])

    def enqueue(self, order_id: str) -> None:
        self._items.append(order_id)

    def dequeue(self) -> str | None:
        return self._items.pop(0) if self._items else None

    def peek(self) -> str | None:
        return self._items[0] if self._items else None

    def remove(self, order_id: str) -> bool:
        if order_id in self._items:
            self._items.remove(order_id)
            return True
        return False

    def index_of(self, order_id: str) -> int | None:
        return self._items.index(order_id) if order_id in self._items else None

    def insert_at(self, index: int, order_id: str) -> None:
        self._items.insert(index, order_id)

    def to_list(self) -> list[str]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)


class FakeHistory(CommandHistory):
    """Ghi lại các Command được execute và mô phỏng tác dụng của AssignOrderCmd /
    CompleteStopCmd theo đúng docstring trong commands.py (không phụ thuộc cài đặt thật)."""

    def __init__(self) -> None:
        super().__init__()
        self.executed: list[Command] = []

    def execute(self, cmd: Command) -> None:
        self.executed.append(cmd)
        if isinstance(cmd, AssignOrderCmd):
            self._simulate_assign(cmd)
        elif isinstance(cmd, CompleteStopCmd):
            self._simulate_complete(cmd)

    @staticmethod
    def _simulate_assign(cmd: AssignOrderCmd) -> None:
        order = cmd._orders.get_by_id(cmd._order_id)
        shipper = cmd._shippers.get_by_id(cmd._shipper_id)
        order.status = OrderStatus.ASSIGNED
        order.shipper_id = shipper.id
        shipper.load_kg += order.weight_kg
        shipper.route.append(StopCls(order.id, order.pickup_node, StopKind.PICKUP))
        shipper.route.append(StopCls(order.id, order.delivery_node, StopKind.DELIVERY))
        cmd._queue.remove(order.id)
        cmd._orders.update(order)
        cmd._shippers.update(shipper)

    @staticmethod
    def _simulate_complete(cmd: CompleteStopCmd) -> None:
        shipper = cmd._shippers.get_by_id(cmd._shipper_id)
        stop = shipper.route.popleft()
        shipper.node_id = stop.node_id
        if stop.kind == StopKind.DELIVERY:
            order = cmd._orders.get_by_id(stop.order_id)
            order.status = OrderStatus.DELIVERED
            shipper.load_kg -= order.weight_kg
            cmd._orders.update(order)
        cmd._shippers.update(shipper)


# ---------------------------------------------------------------------------
# Nạp dữ liệu mẫu
# ---------------------------------------------------------------------------
def _load(name: str) -> list[dict[str, Any]]:
    with open(SAMPLE_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def make_order(id: str, pickup: str, delivery: str, weight: float,
               deadline: int | None = None, status: str = "WAITING",
               shipper_id: str | None = None):
    return OrderCls(id, f"Khách {id}", pickup, delivery, weight, deadline,
                    OrderStatus(status), shipper_id, "", "")


def make_shipper(id: str, node_id: str, capacity: float, load: float = 0.0,
                 route: list[tuple[str, str, str]] | None = None):
    stops = deque(StopCls(o, n, StopKind(k)) for o, n, k in (route or []))
    return ShipperCls(id, f"Shipper {id}", node_id, capacity, load, stops)


def sample_orders() -> list:
    return [make_order(d["id"], d["pickup_node"], d["delivery_node"], d["weight_kg"],
                       d["deadline_min"], d["status"], d["shipper_id"])
            for d in _load("orders.json")]


def sample_shippers() -> list:
    return [make_shipper(d["id"], d["node_id"], d["capacity_kg"], d["load_kg"],
                         [(s["order_id"], s["node_id"], s["kind"]) for s in d["route"]])
            for d in _load("shippers.json")]


def sample_network(extra_places: list | None = None) -> RoadNetwork:
    places = [PlaceCls(d["id"], d["name"], d["x"], d["y"], PlaceKind(d["kind"]))
              for d in _load("places.json")]
    places += extra_places or []
    roads = [RoadCls(d["id"], d["a"], d["b"], d["distance_km"], TrafficLevel(d["traffic"]))
             for d in _load("roads.json")]
    return RoadNetwork(FakeRepository(places), FakeRepository(roads))


class Env:
    """Bộ đồ nghề cho một test: service + các thành phần giả lập để kiểm tra."""

    def __init__(self, orders: list | None = None, shippers: list | None = None,
                 extra_places: list | None = None) -> None:
        orders = sample_orders() if orders is None else orders
        shippers = sample_shippers() if shippers is None else shippers
        self.orders = FakeRepository(orders)
        self.shippers = FakeRepository(shippers)
        self.queue = FakeQueue([o.id for o in orders if o.status == OrderStatus.WAITING])
        self.history = FakeHistory()
        self.service = DispatchService(self.orders, self.shippers,
                                       sample_network(extra_places), DijkstraRouter(),
                                       self.queue, self.history)


@pytest.fixture
def env() -> Env:
    return Env()


def by_id(suggestions: list[Suggestion]) -> dict[str, Suggestion]:
    return {s.shipper_id: s for s in suggestions}


# ===========================================================================
# route_minutes
# ===========================================================================
class TestRouteMinutes:
    def test_empty_route_is_zero(self, env):
        assert env.service.route_minutes(env.shippers.get_by_id("S01")) == 0.0
        assert env.service.route_minutes(env.shippers.get_by_id("S03")) == 0.0

    def test_sums_every_leg_from_current_position(self, env):
        # S02: P05 -> P01 (7.2, R04 MEDIUM) -> P11 (6.0, R06 LOW)
        assert env.service.route_minutes(env.shippers.get_by_id("S02")) == pytest.approx(13.2)

    def test_stop_at_current_node_costs_nothing(self):
        s = make_shipper("S09", "P01", 20, 3, [("OX", "P01", "PICKUP"), ("OX", "P07", "DELIVERY")])
        e = Env(shippers=[s])
        assert e.service.route_minutes(s) == pytest.approx(6.15)

    def test_unreachable_stop_is_inf(self):
        island = PlaceCls("P99", "Đảo", 0, 0, PlaceKind.HOME)
        s = make_shipper("S09", "P01", 20, 3, [("OX", "P99", "DELIVERY")])
        e = Env(shippers=[s], extra_places=[island])
        assert e.service.route_minutes(s) == INF


# ===========================================================================
# suggest trên dữ liệu mẫu
# ===========================================================================
class TestSuggestSample:
    def test_o001_s02_late(self, env):
        result = env.service.suggest("O001")
        assert [s.shipper_id for s in result] == ["S01", "S03", "S02"]
        s01, s03, s02 = result

        assert s01.feasible and s01.reason == ""
        assert s01.eta_minutes == pytest.approx(6.15)
        assert s01.minutes_to_pickup == pytest.approx(0.0)
        assert s01.minutes_pickup_to_delivery == pytest.approx(6.15)
        assert s01.path_to_pickup == ["P01"]
        assert s01.path_to_delivery == ["P01", "P03", "P07"]
        assert s01.free_capacity_kg == pytest.approx(20.0)

        assert s03.feasible and s03.eta_minutes == pytest.approx(13.35)
        assert s03.minutes_to_pickup == pytest.approx(7.2)
        assert s03.path_to_pickup == ["P06", "P01"]

        assert not s02.feasible and s02.reason == REASON_LATE
        assert s02.eta_minutes == pytest.approx(25.35)   # 13.2 + 6.0 (P11->P01) + 6.15
        assert s02.eta_minutes > 20
        # điểm xuất phát của S02 là điểm cuối route (P11), không phải vị trí hiện tại (P05)
        assert s02.path_to_pickup[0] == "P11"
        assert s02.minutes_to_pickup == pytest.approx(6.0)

    def test_o002_s02_overloaded(self, env):
        result = env.service.suggest("O002")
        assert [s.shipper_id for s in result] == ["S01", "S03", "S02"]
        s01, s03, s02 = result
        assert s01.feasible and s01.eta_minutes == pytest.approx(10.5)
        assert s01.path_to_delivery == ["P01", "P06", "P10"]
        assert s03.feasible and s03.eta_minutes == pytest.approx(17.7)
        assert not s02.feasible and s02.reason == REASON_OVERLOAD   # 10 + 8 > 15
        assert s02.free_capacity_kg == pytest.approx(5.0)

    def test_o004_only_s01(self, env):
        result = env.service.suggest("O004")
        assert result[0].shipper_id == "S01"
        assert result[0].feasible and result[0].eta_minutes == pytest.approx(10.5)
        rest = by_id(result[1:])
        assert set(rest) == {"S02", "S03"}
        for s in rest.values():
            assert not s.feasible and s.reason == REASON_OVERLOAD
        assert [s.feasible for s in result] == [True, False, False]

    def test_feasible_always_before_infeasible(self, env):
        for oid in ("O001", "O002", "O003", "O004"):
            flags = [s.feasible for s in env.service.suggest(oid)]
            assert flags == sorted(flags, reverse=True)

    def test_every_shipper_evaluated(self, env):
        result = env.service.suggest("O001")
        assert len(result) == 3 and all(s.order_id == "O001" for s in result)

    def test_unknown_order(self, env):
        with pytest.raises(NotFoundError):
            env.service.suggest("O999")


# ===========================================================================
# suggest: các trường hợp biên
# ===========================================================================
class TestSuggestRules:
    def test_tie_eta_lighter_load_first(self):
        orders = [make_order("O100", "P01", "P07", 2.0)]
        shippers = [make_shipper("S10", "P01", 20, load=5.0),
                    make_shipper("S11", "P01", 20, load=1.0)]
        result = Env(orders, shippers).service.suggest("O100")
        assert [s.shipper_id for s in result] == ["S11", "S10"]
        assert result[0].eta_minutes == pytest.approx(result[1].eta_minutes)

    def test_exact_capacity_is_allowed(self):
        orders = [make_order("O100", "P01", "P07", 5.0)]
        shippers = [make_shipper("S10", "P01", 15, load=10.0)]
        (s,) = Env(orders, shippers).service.suggest("O100")
        assert s.feasible

    def test_no_deadline_never_late(self):
        orders = [make_order("O100", "P09", "P10", 1.0, deadline=None)]
        (s,) = Env(orders, [make_shipper("S10", "P08", 20)]).service.suggest("O100")
        assert s.feasible and s.eta_minutes > 20

    def test_no_path(self):
        island = PlaceCls("P99", "Đảo", 0, 0, PlaceKind.HOME)
        orders = [make_order("O100", "P01", "P99", 1.0, deadline=30)]
        e = Env(orders, [make_shipper("S10", "P01", 20)], extra_places=[island])
        (s,) = e.service.suggest("O100")
        assert not s.feasible and s.reason == REASON_NO_PATH
        assert s.eta_minutes == INF and s.path_to_delivery == []

    def test_overload_has_priority_over_late(self):
        orders = [make_order("O100", "P01", "P07", 50.0, deadline=1)]
        (s,) = Env(orders, [make_shipper("S10", "P06", 20)]).service.suggest("O100")
        assert s.reason == REASON_OVERLOAD

    def test_eta_counts_current_route_after_assign(self, env):
        env.service.assign("O001", "S01")      # S01.route = [P01 PICKUP, P07 DELIVERY]
        s01 = by_id(env.service.suggest("O002"))["S01"]
        # 6.15 (hết route) + 6.15 (P07 -> P01) + 10.5 (P01 -> P10)
        assert s01.eta_minutes == pytest.approx(22.8)
        assert s01.path_to_pickup[0] == "P07"
        assert env.service.suggest("O002")[0].shipper_id == "S03"


# ===========================================================================
# best
# ===========================================================================
class TestBest:
    @pytest.mark.parametrize("oid", ["O001", "O002", "O004"])
    def test_best_is_s01(self, env, oid):
        best = env.service.best(oid)
        assert best is not None and best.shipper_id == "S01" and best.feasible

    def test_none_when_nobody_fits(self):
        orders = [make_order("O100", "P01", "P07", 3.0, deadline=5)]   # S01 cần 6.15
        assert Env(orders).service.best("O100") is None


# ===========================================================================
# assign
# ===========================================================================
class TestAssign:
    def test_default_assigns_best(self, env):
        result = env.service.assign("O001")
        assert result.shipper_id == "S01" and result.feasible
        assert result.eta_minutes == pytest.approx(6.15)

        (cmd,) = env.history.executed
        assert isinstance(cmd, AssignOrderCmd)
        assert cmd._order_id == "O001" and cmd._shipper_id == "S01"
        assert cmd._orders is env.orders and cmd._shippers is env.shippers
        assert cmd._queue is env.queue

        # tác dụng (mô phỏng) của lệnh
        assert env.orders.get_by_id("O001").status == OrderStatus.ASSIGNED
        s01 = env.shippers.get_by_id("S01")
        assert [(s.node_id, s.kind) for s in s01.route] == [
            ("P01", StopKind.PICKUP), ("P07", StopKind.DELIVERY)]
        assert "O001" not in env.queue.to_list()

    def test_explicit_feasible_shipper(self, env):
        result = env.service.assign("O001", "S03")
        assert result.shipper_id == "S03"
        assert result.eta_minutes == pytest.approx(13.35)
        assert env.history.executed[0]._shipper_id == "S03"

    @pytest.mark.parametrize("oid, sid", [("O001", "S02"), ("O002", "S02"), ("O004", "S03")])
    def test_infeasible_shipper_rejected(self, env, oid, sid):
        with pytest.raises(BusinessRuleError):
            env.service.assign(oid, sid)
        assert env.history.executed == []

    @pytest.mark.parametrize("oid", ["O005", "O006"])   # ASSIGNED, DELIVERED
    def test_order_must_be_waiting(self, env, oid):
        with pytest.raises(BusinessRuleError):
            env.service.assign(oid, "S01")
        assert env.history.executed == []

    def test_assign_twice_rejected(self, env):
        env.service.assign("O001")
        with pytest.raises(BusinessRuleError):
            env.service.assign("O001")
        assert len(env.history.executed) == 1

    def test_no_feasible_shipper(self):
        orders = [make_order("O100", "P01", "P07", 3.0, deadline=5)]
        e = Env(orders)
        with pytest.raises(BusinessRuleError):
            e.service.assign("O100")
        assert e.history.executed == []

    def test_unknown_order(self, env):
        with pytest.raises(NotFoundError):
            env.service.assign("O999", "S01")

    def test_unknown_shipper(self, env):
        with pytest.raises(NotFoundError):
            env.service.assign("O001", "S99")
        assert env.history.executed == []

    @pytest.mark.parametrize("sid", ["", "   "])
    def test_blank_shipper_id(self, env, sid):
        with pytest.raises(ValidationError):
            env.service.assign("O001", sid)


# ===========================================================================
# complete_next_stop
# ===========================================================================
class TestCompleteNextStop:
    def test_pickup_then_delivery(self, env):
        # S02: [O005 PICKUP @P01, O005 DELIVERY @P11]
        assert env.service.complete_next_stop("S02") is None
        (cmd,) = env.history.executed
        assert isinstance(cmd, CompleteStopCmd)
        assert cmd._shipper_id == "S02"
        assert cmd._orders is env.orders and cmd._shippers is env.shippers
        assert env.shippers.get_by_id("S02").node_id == "P01"

        delivered = env.service.complete_next_stop("S02")
        assert delivered is not None and delivered.id == "O005"
        assert delivered.status == OrderStatus.DELIVERED
        s02 = env.shippers.get_by_id("S02")
        assert s02.node_id == "P11" and len(s02.route) == 0
        assert s02.load_kg == pytest.approx(0.0)
        assert len(env.history.executed) == 2

    def test_full_cycle_after_assign(self, env):
        env.service.assign("O001", "S01")
        assert env.service.complete_next_stop("S01") is None
        order = env.service.complete_next_stop("S01")
        assert order is not None and order.id == "O001"

    def test_empty_route(self, env):
        with pytest.raises(BusinessRuleError):
            env.service.complete_next_stop("S01")
        assert env.history.executed == []

    def test_unknown_shipper(self, env):
        with pytest.raises(NotFoundError):
            env.service.complete_next_stop("S99")


# ===========================================================================
# compare_time_vs_distance
# ===========================================================================
class TestCompare:
    def test_p01_p07(self, env):
        rows = env.service.compare_time_vs_distance("P01", "P07")
        assert len(rows) == 2
        for row in rows:
            assert set(row) == {"tiêu chí", "đường đi", "km", "phút"}
        shortest, fastest = rows

        # Ngắn nhất theo km: P01 -> P02 -> P07 (1.0 + 2.0 km, đường đông HIGH)
        assert shortest["đường đi"] == "P01 → P02 → P07"
        assert shortest["km"] == pytest.approx(3.0)
        assert shortest["phút"] == pytest.approx(18.0)

        # Nhanh nhất theo phút: P01 -> P03 -> P07 (1.6 + 2.5 km, đường vắng LOW)
        assert fastest["đường đi"] == "P01 → P03 → P07"
        assert fastest["km"] == pytest.approx(4.1)
        assert fastest["phút"] == pytest.approx(6.15)

        # Lý do phải dùng thời gian: đường dài hơn nhưng nhanh hơn
        assert fastest["km"] > shortest["km"] and fastest["phút"] < shortest["phút"]

    def test_same_point(self, env):
        rows = env.service.compare_time_vs_distance("P01", "P01")
        assert all(r["đường đi"] == "P01" and r["km"] == 0 and r["phút"] == 0 for r in rows)

    def test_no_path(self):
        island = PlaceCls("P99", "Đảo", 0, 0, PlaceKind.HOME)
        rows = Env(extra_places=[island]).service.compare_time_vs_distance("P01", "P99")
        assert all(r["đường đi"] == REASON_NO_PATH and r["phút"] == INF for r in rows)
