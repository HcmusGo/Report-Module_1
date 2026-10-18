"""Kiểm thử RoadNetwork và DijkstraRouter (services/routing.py). Người phụ trách: Bảo.

Place / Road (Quyên) và JsonRepository (Tâm) có thể chưa cài đặt xong ở nhánh hiện tại,
nên file này tự định nghĩa entity giả lập + Repository trong bộ nhớ. Nếu Place / Road thật
đã dùng được thì test sẽ tự chuyển sang dùng lớp thật.
"""
from __future__ import annotations

import json
from typing import Any, Callable, cast

import pytest

from config import SAMPLE_DIR, TRAFFIC_SPEED_KMH
from exceptions import ValidationError
from models.base import BaseEntity
from models.map_entities import Place, PlaceKind, Road, TrafficLevel
from repositories.base_repository import Repository
from services.routing import DijkstraRouter, PathResult, RoadNetwork

INF = float("inf")


# ---------------------------------------------------------------------------
# Entity giả lập (dùng khi Place / Road thật còn NotImplementedError)
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
        # Cùng công thức với docstring của Road thật.
        return self.distance_km / TRAFFIC_SPEED_KMH[self.traffic.value] * 60

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "a": self.a, "b": self.b,
                "distance_km": self.distance_km, "traffic": self.traffic.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FakeRoad":
        return cls(data["id"], data["a"], data["b"], data["distance_km"],
                   TrafficLevel(data["traffic"]))


def _real_entities_ready() -> bool:
    try:
        # Place/Road còn abstract khi chưa cài xong -> TypeError, được bắt ở dưới.
        Place("PX", "x", 0, 0, PlaceKind.SHOP)  # type: ignore
        road = Road("RX", "PX", "PY", 1.0, TrafficLevel.LOW)  # type: ignore
        return road.minutes == pytest.approx(1.5) and road.a == "PX" and road.b == "PY"
    except Exception:   # NotImplementedError hoặc cài đặt dở dang
        return False


# Chọn lớp lúc runtime; khai báo kiểu Callable để type checker không coi đây là
# lời gọi khởi tạo Place/Road (vẫn còn abstract khi chưa cài đặt xong).
PlaceCls: Callable[..., Any]
RoadCls: Callable[..., Any]
if _real_entities_ready():
    # cast: nếu chỉ khai báo kiểu, checker vẫn thu hẹp về type[Place] khi gán.
    PlaceCls = cast(Callable[..., Any], Place)
    RoadCls = cast(Callable[..., Any], Road)
else:
    PlaceCls, RoadCls = FakePlace, FakeRoad


def make_place(id: str, name: str = "", x: float = 0, y: float = 0,
               kind: str = "JUNCTION"):
    return PlaceCls(id, name or id, x, y, PlaceKind(kind))


def make_road(id: str, a: str, b: str, distance_km: float, traffic: str = "MEDIUM"):
    return RoadCls(id, a, b, distance_km, TrafficLevel(traffic))


# ---------------------------------------------------------------------------
# Repository giả lập trong bộ nhớ, có đếm số lần get_all để kiểm tra lazy init
# ---------------------------------------------------------------------------
class FakeRepository(Repository):
    def __init__(self, items: list | None = None) -> None:
        self._items = {e.id: e for e in (items or [])}
        self.get_all_calls = 0

    def get_all(self) -> list:
        self.get_all_calls += 1
        return list(self._items.values())

    def get_by_id(self, entity_id: str):
        return self._items.get(entity_id)

    def add(self, entity) -> None:
        if entity.id in self._items:
            raise ValidationError(f"Trùng id {entity.id}")
        self._items[entity.id] = entity

    def update(self, entity) -> None:
        self._items[entity.id] = entity

    def delete(self, entity_id: str):
        return self._items.pop(entity_id, None)

    def next_id(self) -> str:
        return f"X{len(self._items) + 1:03d}"


def _load(name: str) -> list[dict[str, Any]]:
    with open(SAMPLE_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def build_network(places: list, roads: list) -> tuple[RoadNetwork, FakeRepository, FakeRepository]:
    p_repo, r_repo = FakeRepository(places), FakeRepository(roads)
    return RoadNetwork(p_repo, r_repo), p_repo, r_repo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_places() -> list:
    return [make_place(d["id"], d["name"], d["x"], d["y"], d["kind"]) for d in _load("places.json")]


@pytest.fixture
def sample_roads() -> list:
    return [make_road(d["id"], d["a"], d["b"], d["distance_km"], d["traffic"])
            for d in _load("roads.json")]


@pytest.fixture
def sample_net(sample_places, sample_roads) -> RoadNetwork:
    return build_network(sample_places, sample_roads)[0]


@pytest.fixture
def router() -> DijkstraRouter:
    return DijkstraRouter()


def path_cost(net: RoadNetwork, path: list[str]) -> tuple[float, float]:
    """Tự cộng (minutes, km) dọc path để đối chiếu với PathResult."""
    minutes = km = 0.0
    for u, v in zip(path, path[1:]):
        road = min((r for n, r in net.neighbors(u) if n == v), key=lambda r: r.minutes)
        minutes += road.minutes
        km += road.distance_km
    return minutes, km


# ===========================================================================
# Entity giả lập
# ===========================================================================
@pytest.mark.parametrize("traffic, km, expected", [
    ("LOW", 1.6, 2.4), ("MEDIUM", 3.0, 7.2), ("HIGH", 1.0, 6.0), ("LOW", 2.5, 3.75),
])
def test_road_minutes_formula(traffic, km, expected):
    assert make_road("R", "A", "B", km, traffic).minutes == pytest.approx(expected)


# ===========================================================================
# RoadNetwork
# ===========================================================================
class TestRoadNetwork:
    def test_lazy_not_built_on_construct(self, sample_places, sample_roads):
        net, p_repo, r_repo = build_network(sample_places, sample_roads)
        assert net._adj is None
        assert p_repo.get_all_calls == 0 and r_repo.get_all_calls == 0

    def test_lazy_built_once_on_first_use(self, sample_places, sample_roads):
        net, p_repo, r_repo = build_network(sample_places, sample_roads)
        net.has_node("P01")
        assert net._adj is not None
        net.neighbors("P01")
        net.has_node("P99")
        DijkstraRouter().shortest_path(net, "P01", "P10")
        assert p_repo.get_all_calls == 1 and r_repo.get_all_calls == 1

    def test_lazy_built_by_neighbors_first(self, sample_places, sample_roads):
        net, _, r_repo = build_network(sample_places, sample_roads)
        assert len(net.neighbors("P01")) == 6
        assert r_repo.get_all_calls == 1

    def test_has_node_all_sample_places(self, sample_net, sample_places):
        for p in sample_places:
            assert sample_net.has_node(p.id)

    def test_has_node_unknown(self, sample_net):
        assert not sample_net.has_node("P99")
        assert not sample_net.has_node("")

    def test_every_road_added_both_directions(self, sample_net, sample_roads):
        for road in sample_roads:
            assert (road.b, road) in sample_net.neighbors(road.a)
            assert (road.a, road) in sample_net.neighbors(road.b)

    def test_total_degree_is_twice_edges(self, sample_net, sample_places, sample_roads):
        total = sum(len(sample_net.neighbors(p.id)) for p in sample_places)
        assert total == 2 * len(sample_roads)

    def test_neighbors_of_p07(self, sample_net):
        nbrs = {n: r.id for n, r in sample_net.neighbors("P07")}
        assert nbrs == {"P03": "R09", "P02": "R10"}

    def test_neighbors_of_p01(self, sample_net):
        assert {n for n, _ in sample_net.neighbors("P01")} == {"P02", "P03", "P04", "P05", "P06", "P11"}

    def test_neighbors_unknown_node_is_empty(self, sample_net):
        assert sample_net.neighbors("P99") == []

    def test_neighbors_returns_copy(self, sample_net):
        sample_net.neighbors("P01").clear()
        assert len(sample_net.neighbors("P01")) == 6

    def test_isolated_place_is_a_node(self):
        net, _, _ = build_network([make_place("A"), make_place("B"), make_place("Z")],
                                  [make_road("R1", "A", "B", 1.0)])
        assert net.has_node("Z")
        assert net.neighbors("Z") == []

    def test_empty_network(self):
        net, _, _ = build_network([], [])
        assert not net.has_node("P01")
        assert net.neighbors("P01") == []

    def test_parallel_roads_kept(self):
        net, _, _ = build_network([make_place("A"), make_place("B")],
                                  [make_road("R1", "A", "B", 1.0, "HIGH"),
                                   make_road("R2", "A", "B", 2.0, "LOW")])
        assert sorted(r.id for _, r in net.neighbors("A")) == ["R1", "R2"]
        assert sorted(r.id for _, r in net.neighbors("B")) == ["R1", "R2"]


# ===========================================================================
# DijkstraRouter.shortest_path
# ===========================================================================
class TestShortestPath:
    # ---- 2 test case chuẩn của dự án ----
    def test_p01_to_p07_by_time(self, sample_net, router):
        res = router.shortest_path(sample_net, "P01", "P07", by="time")
        assert res.found
        assert res.path == ["P01", "P03", "P07"]
        assert res.minutes == pytest.approx(6.15)
        assert res.distance_km == pytest.approx(4.1)

    def test_p01_to_p07_by_distance(self, sample_net, router):
        res = router.shortest_path(sample_net, "P01", "P07", by="distance")
        assert res.found
        assert res.path == ["P01", "P02", "P07"]
        assert res.distance_km == pytest.approx(3.0)
        assert res.minutes == pytest.approx(18.0)

    def test_default_by_is_time(self, sample_net, router):
        assert router.shortest_path(sample_net, "P01", "P07").path == ["P01", "P03", "P07"]

    def test_fastest_vs_shortest_tradeoff(self, sample_net, router):
        fast = router.shortest_path(sample_net, "P01", "P07", by="time")
        short = router.shortest_path(sample_net, "P01", "P07", by="distance")
        assert fast.minutes < short.minutes
        assert short.distance_km < fast.distance_km

    def test_reverse_direction_same_cost(self, sample_net, router):
        fwd = router.shortest_path(sample_net, "P01", "P07", by="time")
        back = router.shortest_path(sample_net, "P07", "P01", by="time")
        assert back.path == ["P07", "P03", "P01"]
        assert back.minutes == pytest.approx(fwd.minutes)
        assert back.distance_km == pytest.approx(fwd.distance_km)

    @pytest.mark.parametrize("by", ["time", "distance"])
    def test_result_totals_match_path(self, sample_net, sample_places, router, by):
        for p in sample_places:
            res = router.shortest_path(sample_net, "P01", p.id, by=by)
            assert res.found and res.path[0] == "P01" and res.path[-1] == p.id
            minutes, km = path_cost(sample_net, res.path)
            assert res.minutes == pytest.approx(minutes)
            assert res.distance_km == pytest.approx(km)

    def test_consecutive_nodes_are_adjacent(self, sample_net, router):
        res = router.shortest_path(sample_net, "P09", "P08", by="time")
        for u, v in zip(res.path, res.path[1:]):
            assert v in {n for n, _ in sample_net.neighbors(u)}

    def test_src_equals_dst(self, sample_net, router):
        res = router.shortest_path(sample_net, "P05", "P05")
        assert res.found
        assert res.path == ["P05"]
        assert res.minutes == 0.0 and res.distance_km == 0.0
        assert res.nodes_visited == 1

    @pytest.mark.parametrize("src, dst", [("P99", "P01"), ("P01", "P99"), ("X", "Y")])
    def test_unknown_node_not_found(self, sample_net, router, src, dst):
        res = router.shortest_path(sample_net, src, dst)
        assert not res.found
        assert res == PathResult.not_found(nodes_visited=0)
        assert res.minutes == INF and res.distance_km == INF

    def test_disconnected_not_found(self, router):
        net, _, _ = build_network(
            [make_place(x) for x in "ABCDE"],
            [make_road("R1", "A", "B", 1.0), make_road("R2", "B", "C", 1.0),
             make_road("R3", "D", "E", 1.0)])
        res = router.shortest_path(net, "A", "E")
        assert not res.found
        assert res.path == []
        assert res.minutes == INF and res.distance_km == INF
        assert res.nodes_visited == 3   # đã duyệt hết thành phần {A, B, C}

    def test_isolated_destination_not_found(self, router):
        net, _, _ = build_network([make_place("A"), make_place("B"), make_place("Z")],
                                  [make_road("R1", "A", "B", 1.0)])
        res = router.shortest_path(net, "A", "Z", by="distance")
        assert res == PathResult.not_found(nodes_visited=2)

    def test_nodes_visited_positive_and_bounded(self, sample_net, sample_places, router):
        res = router.shortest_path(sample_net, "P01", "P10")
        assert 1 <= res.nodes_visited <= len(sample_places)

    def test_early_stop_visits_fewer_nodes(self, router):
        # Chuỗi A-B-C-D-E: tìm A->B không cần duyệt C, D, E.
        net, _, _ = build_network(
            [make_place(x) for x in "ABCDE"],
            [make_road(f"R{i}", u, v, 1.0) for i, (u, v) in enumerate(zip("ABCD", "BCDE"))])
        assert router.shortest_path(net, "A", "B").nodes_visited == 2
        assert router.shortest_path(net, "A", "E").nodes_visited == 5

    def test_stale_heap_entries_skipped(self, router):
        # B được nới lỏng 2 lần (10 rồi 2) -> có bản ghi cũ trong heap, phải bị bỏ qua.
        net, _, _ = build_network(
            [make_place(x) for x in "ABCD"],
            [make_road("R1", "A", "B", 10.0), make_road("R2", "A", "C", 1.0),
             make_road("R3", "C", "B", 1.0), make_road("R4", "B", "D", 1.0)])
        res = router.shortest_path(net, "A", "D", by="distance")
        assert res.path == ["A", "C", "B", "D"]
        assert res.distance_km == pytest.approx(3.0)
        assert res.nodes_visited == 4   # mỗi nút chỉ được "chốt" 1 lần

    def test_parallel_roads_pick_by_criterion(self, router):
        # R1 ngắn nhưng đông (6 phút), R2 dài nhưng vắng (3 phút).
        net, _, _ = build_network([make_place("A"), make_place("B")],
                                  [make_road("R1", "A", "B", 1.0, "HIGH"),
                                   make_road("R2", "A", "B", 2.0, "LOW")])
        t = router.shortest_path(net, "A", "B", by="time")
        assert t.minutes == pytest.approx(3.0) and t.distance_km == pytest.approx(2.0)
        d = router.shortest_path(net, "A", "B", by="distance")
        assert d.distance_km == pytest.approx(1.0) and d.minutes == pytest.approx(6.0)

    def test_invalid_weight_raises(self, sample_net, router):
        with pytest.raises(ValidationError):
            router.shortest_path(sample_net, "P01", "P07", by="money")  # type: ignore[arg-type]


# ===========================================================================
# DijkstraRouter.distances_from
# ===========================================================================
EXPECTED_TIME_FROM_P01 = {
    "P01": 0.0, "P02": 4.5, "P03": 2.4, "P04": 2.4, "P05": 7.2, "P06": 7.2,
    "P07": 6.15, "P08": 6.15, "P09": 10.5, "P10": 10.5, "P11": 6.0,
}
EXPECTED_KM_FROM_P01 = {
    "P01": 0.0, "P02": 1.0, "P03": 1.6, "P04": 1.6, "P05": 3.0, "P06": 3.0,
    "P07": 3.0, "P08": 3.0, "P09": 5.2, "P10": 5.2, "P11": 4.0,
}


class TestDistancesFrom:
    def test_by_time_from_p01(self, sample_net, router):
        dist = router.distances_from(sample_net, "P01", by="time")
        assert dist.keys() == EXPECTED_TIME_FROM_P01.keys()
        for node, cost in EXPECTED_TIME_FROM_P01.items():
            assert dist[node] == pytest.approx(cost), node

    def test_by_distance_from_p01(self, sample_net, router):
        dist = router.distances_from(sample_net, "P01", by="distance")
        assert dist.keys() == EXPECTED_KM_FROM_P01.keys()
        for node, cost in EXPECTED_KM_FROM_P01.items():
            assert dist[node] == pytest.approx(cost), node

    def test_default_by_is_time(self, sample_net, router):
        assert router.distances_from(sample_net, "P01")["P02"] == pytest.approx(4.5)

    @pytest.mark.parametrize("by", ["time", "distance"])
    def test_consistent_with_shortest_path(self, sample_net, sample_places, router, by):
        for src in ("P01", "P07", "P10"):
            dist = router.distances_from(sample_net, src, by=by)
            for p in sample_places:
                res = router.shortest_path(sample_net, src, p.id, by=by)
                cost = res.minutes if by == "time" else res.distance_km
                assert dist[p.id] == pytest.approx(cost)

    def test_symmetric(self, sample_net, sample_places, router):
        for p in sample_places:
            d1 = router.distances_from(sample_net, "P01")[p.id]
            d2 = router.distances_from(sample_net, p.id)["P01"]
            assert d1 == pytest.approx(d2)

    def test_unreachable_nodes_absent(self, router):
        net, _, _ = build_network([make_place(x) for x in "ABCZ"],
                                  [make_road("R1", "A", "B", 2.0), make_road("R2", "B", "C", 3.0)])
        dist = router.distances_from(net, "A", by="distance")
        assert dist == {"A": 0.0, "B": pytest.approx(2.0), "C": pytest.approx(5.0)}
        assert dist.get("Z", INF) == INF

    def test_unknown_src_returns_empty(self, sample_net, router):
        assert router.distances_from(sample_net, "P99") == {}

    def test_isolated_src_only_itself(self, router):
        net, _, _ = build_network([make_place("A"), make_place("B"), make_place("Z")],
                                  [make_road("R1", "A", "B", 1.0)])
        assert router.distances_from(net, "Z") == {"Z": 0.0}

    def test_invalid_weight_raises(self, sample_net, router):
        with pytest.raises(ValidationError):
            router.distances_from(sample_net, "P01", by="km")  # type: ignore[arg-type]
