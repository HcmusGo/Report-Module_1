"""Kiểm tra dữ liệu khởi tạo trong data/*.json: đủ file, đúng định dạng, các khóa ngoại khớp nhau.

Chỉ dùng thư viện chuẩn (không import models / repositories) nên chạy được độc lập với phần cài đặt.
Mỗi lần sửa tay data/*.json, chạy `uv run pytest tests/test_data_files.py` để chắc chắn không làm hỏng dữ liệu.
"""
import json
from collections import defaultdict, deque

import pytest

from config import DATA_DIR

ORDER_STATUSES = {"NEW", "PREPARING", "READY", "DELIVERING", "DELIVERED", "CANCELLED"}
SHIPPER_STATUSES = {"IDLE", "BUSY", "OFFLINE"}
PLACE_KINDS = {"RESTAURANT", "JUNCTION", "HOME"}


def _load(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def data():
    m = _load("map.json")
    return {
        "menu": _load("menu.json"),
        "customers": _load("customers.json"),
        "shippers": _load("shippers.json"),
        "orders": _load("orders.json"),
        "places": m["places"],
        "roads": m["roads"],
    }


@pytest.mark.parametrize("name", ["menu.json", "customers.json", "shippers.json", "orders.json", "map.json"])
def test_file_exists_and_is_utf8_json(name):
    assert (DATA_DIR / name).is_file(), f"thiếu data/{name}"
    _load(name)


@pytest.mark.parametrize("key,prefix", [
    ("menu", "M"), ("customers", "C"), ("shippers", "S"), ("orders", "O"), ("places", "P"), ("roads", "R"),
])
def test_ids_unique_and_prefixed(data, key, prefix):
    ids = [x["id"] for x in data[key]]
    assert ids, f"{key} đang rỗng"
    assert len(ids) == len(set(ids)), f"{key}: trùng id"
    assert all(i.startswith(prefix) and i[1:].isdigit() for i in ids)


def test_menu_fields(data):
    for m in data["menu"]:
        assert m["name"].strip()
        assert isinstance(m["price"], int) and m["price"] > 0
        assert isinstance(m["prep_minutes"], int) and m["prep_minutes"] >= 0
        assert isinstance(m["tags"], list) and len(m["tags"]) == len(set(m["tags"]))


def test_map_shape(data):
    assert 25 <= len(data["places"]) <= 40  # phạm vi trong README
    kinds = [p["kind"] for p in data["places"]]
    assert set(kinds) <= PLACE_KINDS
    assert kinds.count("RESTAURANT") == 1, "phải có đúng 1 quán"


def test_roads_valid(data):
    place_ids = {p["id"] for p in data["places"]}
    seen = set()
    for r in data["roads"]:
        assert r["a"] in place_ids and r["b"] in place_ids, r["id"]
        assert r["a"] != r["b"], f"{r['id']}: đường tự nối chính nó"
        assert r["distance_km"] > 0, r["id"]
        assert r["traffic_factor"] >= 1.0, r["id"]  # trọng số không âm cho Dijkstra
        assert isinstance(r["blocked"], bool)
        pair = frozenset((r["a"], r["b"]))
        assert pair not in seen, f"{r['id']}: trùng đường"
        seen.add(pair)


def test_map_is_connected(data):
    adj = defaultdict(list)
    for r in data["roads"]:
        adj[r["a"]].append(r["b"])
        adj[r["b"]].append(r["a"])
    start = data["places"][0]["id"]
    seen, queue = {start}, deque([start])
    while queue:
        for v in adj[queue.popleft()]:
            if v not in seen:
                seen.add(v)
                queue.append(v)
    assert seen == {p["id"] for p in data["places"]}, "bản đồ có nút bị cô lập"


def test_customers_and_shippers_sit_on_real_places(data):
    kind = {p["id"]: p["kind"] for p in data["places"]}
    for c in data["customers"]:
        assert c["name"].strip() and c["phone"].isdigit()
        assert kind.get(c["node_id"]) == "HOME", f"{c['id']} phải ở nút HOME"
    for s in data["shippers"]:
        assert s["status"] in SHIPPER_STATUSES
        assert s["node_id"] in kind, s["id"]


def test_orders_reference_existing_data(data):
    menu = {m["id"]: m for m in data["menu"]}
    customers = {c["id"] for c in data["customers"]}
    shippers = {s["id"] for s in data["shippers"]}
    for o in data["orders"]:
        assert o["status"] in ORDER_STATUSES
        assert o["customer_id"] in customers, o["id"]
        assert o["items"], f"{o['id']}: đơn không có món"
        for it in o["items"]:
            assert it["menu_id"] in menu, o["id"]
            assert it["quantity"] >= 1
            assert it["unit_price"] > 0
        assert o["delivery_fee"] >= 0
        if o["status"] in {"DELIVERING", "DELIVERED"}:
            assert o["shipper_id"] in shippers, f"{o['id']} đã giao nhưng thiếu shipper"
        if o["shipper_id"]:
            assert o["shipper_id"] in shippers


def test_busy_shippers_match_delivering_orders(data):
    busy = {s["id"] for s in data["shippers"] if s["status"] == "BUSY"}
    delivering = [o["shipper_id"] for o in data["orders"] if o["status"] == "DELIVERING"]
    assert busy == set(delivering)
    assert len(delivering) == len(set(delivering)), "một shipper đang giao hai đơn"
