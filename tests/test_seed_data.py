"""Kiểm tra dữ liệu khởi tạo sẵn trong data/sample/ (chỉ đọc JSON, không phụ thuộc code khác).

Ai sửa file mẫu thì chạy test này: nó bảo đảm các id tham chiếu đúng, bản đồ liên thông,
tải trọng khớp với đơn đã gán, và 'đường gần nhưng đông' đúng là chậm hơn 'đường xa nhưng vắng'.
"""
import heapq
import json
from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"
SPEED = {"LOW": 40.0, "MEDIUM": 25.0, "HIGH": 10.0}


def load(name):
    return json.loads((SAMPLE / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def data():
    return {
        "places": load("places.json"), "roads": load("roads.json"),
        "shippers": load("shippers.json"), "orders": load("orders.json"),
    }


def ids(rows):
    return [r["id"] for r in rows]


def test_ids_are_unique(data):
    for name, rows in data.items():
        assert len(ids(rows)) == len(set(ids(rows))), name


def test_exactly_one_shop(data):
    assert sum(1 for p in data["places"] if p["kind"] == "SHOP") == 1


def test_roads_are_valid(data):
    place_ids = set(ids(data["places"]))
    for r in data["roads"]:
        assert r["a"] in place_ids and r["b"] in place_ids and r["a"] != r["b"]
        assert r["distance_km"] > 0
        assert r["traffic"] in SPEED


def test_map_is_connected(data):
    adj = {p["id"]: set() for p in data["places"]}
    for r in data["roads"]:
        adj[r["a"]].add(r["b"])
        adj[r["b"]].add(r["a"])
    start = data["places"][0]["id"]
    seen, stack = {start}, [start]
    while stack:
        for v in adj[stack.pop()] - seen:
            seen.add(v)
            stack.append(v)
    assert seen == set(adj)


def test_orders_reference_real_places_and_shippers(data):
    place_ids, shipper_ids = set(ids(data["places"])), set(ids(data["shippers"]))
    for o in data["orders"]:
        assert o["pickup_node"] in place_ids and o["delivery_node"] in place_ids
        assert o["weight_kg"] > 0
        assert o["status"] in {"WAITING", "ASSIGNED", "DELIVERED"}
        if o["status"] == "WAITING":
            assert o["shipper_id"] is None
        if o["status"] == "ASSIGNED":
            assert o["shipper_id"] in shipper_ids


def test_there_are_waiting_orders_with_distinct_created_at(data):
    waiting = [o["created_at"] for o in data["orders"] if o["status"] == "WAITING"]
    assert len(waiting) >= 3 and len(waiting) == len(set(waiting))


def test_shipper_load_matches_assigned_orders(data):
    orders = {o["id"]: o for o in data["orders"]}
    place_ids = set(ids(data["places"]))
    for s in data["shippers"]:
        assert s["node_id"] in place_ids and 0 <= s["load_kg"] <= s["capacity_kg"]
        route_orders = {st["order_id"] for st in s["route"]}
        for st in s["route"]:
            assert st["node_id"] in place_ids and st["kind"] in {"PICKUP", "DELIVERY"}
            assert orders[st["order_id"]]["status"] == "ASSIGNED"
            assert orders[st["order_id"]]["shipper_id"] == s["id"]
        assert s["load_kg"] == pytest.approx(sum(orders[i]["weight_kg"] for i in route_orders))


def _dijkstra(data, src, dst, by):
    adj = {p["id"]: [] for p in data["places"]}
    for r in data["roads"]:
        mins = r["distance_km"] / SPEED[r["traffic"]] * 60
        adj[r["a"]].append((r["b"], mins, r["distance_km"]))
        adj[r["b"]].append((r["a"], mins, r["distance_km"]))
    dist, prev, heap = {src: 0.0}, {}, [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, mins, km in adj[u]:
            nd = d + (mins if by == "time" else km)
            if nd < dist.get(v, float("inf")):
                dist[v], prev[v] = nd, u
                heapq.heappush(heap, (nd, v))
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return path[::-1], dist[dst]


def test_crowded_shortcut_is_slower_than_longer_free_road(data):
    """Từ cửa hàng (P01) tới Khu Hoa Sen (P07): đường ngắn nhất theo km lại chậm hơn."""
    shop = next(p["id"] for p in data["places"] if p["kind"] == "SHOP")
    km_path, _ = _dijkstra(data, shop, "P07", by="distance")
    time_path, fastest = _dijkstra(data, shop, "P07", by="time")
    assert km_path != time_path
    # thời gian của đường 'ngắn nhất theo km' phải lớn hơn đường 'nhanh nhất'
    adj_minutes = {frozenset((r["a"], r["b"])): r["distance_km"] / SPEED[r["traffic"]] * 60
                   for r in data["roads"]}
    slow = sum(adj_minutes[frozenset(e)] for e in zip(km_path, km_path[1:]))
    assert slow > fastest
