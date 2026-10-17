import pytest
from src.models.order import Order, OrderStatus
from src.models.shipper import Shipper, Stop, StopKind
from src.models.map_entities import Place, Road, PlaceKind, TrafficLevel

def test_order_model_roundtrip():
    data = {
        "id": "O001",
        "customer_name": "Nguyen Van A",
        "pickup_node": "P01",
        "delivery_node": "P07",
        "weight_kg": 3.0,
        "deadline_min": 20,
        "status": "WAITING",
        "shipper_id": None,
        "note": "Giao nhanh",
        "created_at": "2026-10-12T08:00:00"
    }
    order = Order.from_dict(data)
    assert order.id == "O001"
    assert order.weight_kg == 3.0
    assert order.status == OrderStatus.WAITING
    
    exported = order.to_dict()
    assert exported == data

def test_order_validation():
    # Khối lượng <= 0 phải báo lỗi validation
    with pytest.raises(Exception):
        Order(id="O999", customer_name="Test", pickup_node="P01", delivery_node="P02", weight_kg=0)

def test_shipper_and_stop_roundtrip():
    stop_data = {"order_id": "O001", "node_id": "P07", "kind": "DELIVERY"}
    stop = Stop.from_dict(stop_data)
    assert stop.kind == StopKind.DELIVERY

    shipper_data = {
        "id": "S01",
        "name": "Nguyen Van An",
        "node_id": "P01",
        "capacity_kg": 20.0,
        "load_kg": 3.0,
        "route": [stop_data]
    }
    shipper = Shipper.from_dict(shipper_data)
    assert shipper.id == "S01"
    assert len(shipper.route) == 1
    assert shipper.to_dict() == shipper_data

def test_place_and_road_roundtrip():
    place_data = {"id": "P01", "name": "Cua Hang", "x": 10.0, "y": 20.0, "kind": "SHOP"}
    place = Place.from_dict(place_data)
    assert place.kind == PlaceKind.SHOP
    assert place.to_dict() == place_data

    road_data = {"id": "R01", "a": "P01", "b": "P02", "distance_km": 1.5, "traffic": "LOW"}
    road = Road.from_dict(road_data)
    assert road.traffic == TrafficLevel.LOW
    assert road.to_dict() == road_data
