"""Test OrderService và các lệnh Undo / Redo theo quy tắc Snapshot.

Dùng Repository giả trong bộ nhớ (tests/fakes.py) và models THẬT của Quyên, nên khi models
chưa được merge, cả file này tự bỏ qua thay vì báo lỗi. Người phụ trách: Tiên.
"""
from collections import deque
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from exceptions import BusinessRuleError, NotFoundError, ValidationError
from fakes import InMemoryRepository
from models.map_entities import Place, PlaceKind
from models.order import Order, OrderStatus
from models.shipper import Shipper, Stop, StopKind
from services.commands import AssignOrderCmd, CompleteStopCmd
from services.history import CommandHistory
from services.order_queue import OrderQueue
from services.order_service import OrderService

try:
    Order("O000", "x", "P01", "P07", 1.0)
except (NotImplementedError, TypeError):   # khung v2: Order còn là lớp trừu tượng / chưa cài
    pytest.skip("Chờ PR models của Quyên được merge", allow_module_level=True)


def make_order(order_id, minute=0, status=OrderStatus.WAITING, shipper_id=None,
               weight=3.0, delivery="P07", deadline=None):
    return Order(id=order_id, customer_name=f"Khách {order_id}", pickup_node="P01",
                 delivery_node=delivery, weight_kg=weight, deadline_min=deadline,
                 status=status, shipper_id=shipper_id, note="",
                 created_at=f"2026-10-15T08:{minute:02d}:00")


@pytest.fixture
def env():
    places = InMemoryRepository(
        [Place("P01", "Cửa hàng", 5, 5, PlaceKind.SHOP), Place("P05", "Công viên", 2, 3, PlaceKind.JUNCTION),
         Place("P07", "Hoa Sen", 1, 8, PlaceKind.HOME), Place("P08", "Phú Mỹ", 9, 8, PlaceKind.HOME),
         Place("P11", "Trường học", 5, 1, PlaceKind.HOME)], prefix="P")
    orders = InMemoryRepository(
        [make_order("O003", 2), make_order("O001", 0), make_order("O002", 1),     # cố ý chèn lộn thứ tự
         make_order("O005", 50, OrderStatus.ASSIGNED, "S02", weight=10.0, delivery="P11")], prefix="O")
    shippers = InMemoryRepository(
        [Shipper("S01", "An", "P01", 20.0, 0.0, deque()),
         Shipper("S02", "Đức", "P05", 15.0, 10.0,
                 deque([Stop("O005", "P01", StopKind.PICKUP), Stop("O005", "P11", StopKind.DELIVERY)]))],
        prefix="S")
    queue, history = OrderQueue(), CommandHistory()
    now = [datetime(2026, 10, 15, 9, 0, 0)]

    def clock():                       # mỗi lần gọi tăng 1 phút để thứ tự created_at rõ ràng
        now[0] += timedelta(minutes=1)
        return now[0]

    service = OrderService(orders, places, queue, history, clock=clock)
    service.restore_queue()
    return SimpleNamespace(places=places, orders=orders, shippers=shippers,
                           queue=queue, history=history, service=service)


# ------------------------------------------------------------ khởi động và truy vấn
def test_restore_queue_sorts_by_created_at_and_skips_non_waiting(env):
    assert env.queue.to_list() == ["O001", "O002", "O003"]


def test_waiting_orders_follow_queue_order(env):
    assert [o.id for o in env.service.waiting_orders()] == ["O001", "O002", "O003"]


def test_list_orders_filters_and_sorts_newest_first(env):
    assert [o.id for o in env.service.list_orders()] == ["O005", "O003", "O002", "O001"]
    assert [o.id for o in env.service.list_orders(status=OrderStatus.ASSIGNED)] == ["O005"]
    assert [o.id for o in env.service.list_orders(keyword="khách o002")] == ["O002"]


def test_get_order_not_found(env):
    with pytest.raises(NotFoundError):
        env.service.get_order("O999")


# ------------------------------------------------------------ tạo đơn
def test_create_order_goes_to_queue_end_with_new_id(env):
    order = env.service.create_order("  Nguyễn Văn A  ", "P01", "P08", 4.5, deadline_min=25, note=" gấp ")
    assert order.id == "O006" and order.status == OrderStatus.WAITING and order.shipper_id is None
    assert order.customer_name == "Nguyễn Văn A" and order.note == "gấp"
    assert env.queue.to_list() == ["O001", "O002", "O003", "O006"]
    assert env.history.undo_label() == "Tạo đơn O006"


@pytest.mark.parametrize("pickup,delivery", [("P99", "P07"), ("P01", "P99"), ("P01", "P01")])
def test_create_order_rejects_bad_places(env, pickup, delivery):
    with pytest.raises(ValidationError):
        env.service.create_order("An", pickup, delivery, 2.0)
    assert not env.history.can_undo() and len(env.orders.get_all()) == 4


def test_create_order_rejects_non_positive_weight(env):
    with pytest.raises(ValidationError):
        env.service.create_order("An", "P01", "P07", 0)
    assert not env.history.can_undo()


def test_undo_and_redo_create_order(env):
    order = env.service.create_order("An", "P01", "P08", 2.0)
    created = order.to_dict()
    env.history.undo()
    assert env.orders.get_by_id("O006") is None and "O006" not in env.queue
    env.history.redo()
    assert env.orders.get_by_id("O006").to_dict() == created
    assert env.queue.to_list()[-1] == "O006"


# ------------------------------------------------------------ sửa đơn
def test_update_order_and_undo_restores_exact_before_state(env):
    before = env.service.get_order("O002").to_dict()
    updated = env.service.update_order("O002", weight_kg=7.5, note="  đổi  ")
    assert updated.weight_kg == 7.5 and updated.note == "đổi"
    env.history.undo()
    assert env.service.get_order("O002").to_dict() == before
    env.history.redo()
    assert env.service.get_order("O002").weight_kg == 7.5


def test_update_order_invalid_value_changes_nothing(env):
    before = env.service.get_order("O002").to_dict()
    with pytest.raises(ValidationError):
        env.service.update_order("O002", weight_kg=-1)
    assert env.service.get_order("O002").to_dict() == before and not env.history.can_undo()


def test_update_order_rules(env):
    with pytest.raises(BusinessRuleError):
        env.service.update_order("O005", note="x")                  # đã gán, không sửa được
    with pytest.raises(ValidationError):
        env.service.update_order("O001", status="DELIVERED")        # trường không được sửa
    with pytest.raises(ValidationError):
        env.service.update_order("O001")                            # không có gì để sửa
    with pytest.raises(ValidationError):
        env.service.update_order("O001", delivery_node="P01")       # trùng điểm lấy
    with pytest.raises(ValidationError):
        env.service.update_order("O001", pickup_node="P99")
    with pytest.raises(NotFoundError):
        env.service.update_order("O999", note="x")


# ------------------------------------------------------------ xóa đơn
def test_delete_order_then_undo_restores_queue_position(env):
    before = env.service.get_order("O002").to_dict()
    env.service.delete_order("O002")
    assert env.orders.get_by_id("O002") is None and env.queue.to_list() == ["O001", "O003"]
    env.history.undo()
    assert env.queue.to_list() == ["O001", "O002", "O003"]           # đúng vị trí thứ hai, không xuống cuối
    assert env.service.get_order("O002").to_dict() == before
    env.history.redo()
    assert env.queue.to_list() == ["O001", "O003"]


def test_delete_order_rules(env):
    with pytest.raises(BusinessRuleError):
        env.service.delete_order("O005")
    with pytest.raises(NotFoundError):
        env.service.delete_order("O999")


def test_new_command_after_undo_clears_redo(env):
    env.service.delete_order("O001")
    env.history.undo()
    assert env.history.can_redo()
    env.service.create_order("An", "P01", "P08", 2.0)
    assert not env.history.can_redo()


# ------------------------------------------------------------ AssignOrderCmd (snapshot)
def assign(env, order_id, shipper_id):
    env.history.execute(AssignOrderCmd(env.orders, env.shippers, env.queue, order_id, shipper_id))


def test_assign_changes_order_shipper_and_queue(env):
    assign(env, "O001", "S02")
    order, shipper = env.orders.get_by_id("O001"), env.shippers.get_by_id("S02")
    assert order.status == OrderStatus.ASSIGNED and order.shipper_id == "S02"
    assert shipper.load_kg == 13.0
    assert [(s.order_id, s.kind) for s in shipper.route] == [
        ("O005", StopKind.PICKUP), ("O005", StopKind.DELIVERY),
        ("O001", StopKind.PICKUP), ("O001", StopKind.DELIVERY)]
    assert env.queue.to_list() == ["O002", "O003"]


def test_undo_assign_restores_snapshot_not_defaults(env):
    """S02 đang mang 10 kg: undo phải về 10, không phải 0; đơn ở đầu hàng phải về đầu hàng."""
    order_before = env.orders.get_by_id("O001").to_dict()
    shipper_before = env.shippers.get_by_id("S02").to_dict()
    queue_before = env.queue.to_list()
    assign(env, "O001", "S02")
    env.history.undo()
    assert env.orders.get_by_id("O001").to_dict() == order_before
    assert env.shippers.get_by_id("S02").to_dict() == shipper_before
    assert env.shippers.get_by_id("S02").load_kg == 10.0
    assert env.queue.to_list() == queue_before
    env.history.redo()
    assert env.shippers.get_by_id("S02").load_kg == 13.0 and env.queue.to_list() == ["O002", "O003"]


def test_undo_assign_of_middle_order_keeps_queue_index(env):
    assign(env, "O002", "S01")
    assert env.queue.to_list() == ["O001", "O003"]
    env.history.undo()
    assert env.queue.to_list() == ["O001", "O002", "O003"]


def test_assign_over_capacity_changes_nothing(env):
    env.orders.add(make_order("O010", 5, weight=8.0))
    env.queue.enqueue("O010")
    with pytest.raises(BusinessRuleError):
        assign(env, "O010", "S02")                                   # 10 + 8 > 15
    assert env.shippers.get_by_id("S02").load_kg == 10.0
    assert env.orders.get_by_id("O010").status == OrderStatus.WAITING
    assert "O010" in env.queue and not env.history.can_undo()


def test_assign_non_waiting_order_is_rejected(env):
    with pytest.raises(BusinessRuleError):
        assign(env, "O005", "S01")
    with pytest.raises(NotFoundError):
        assign(env, "O999", "S01")
    with pytest.raises(NotFoundError):
        assign(env, "O001", "S99")


# ------------------------------------------------------------ CompleteStopCmd (snapshot)
def complete(env, shipper_id):
    env.history.execute(CompleteStopCmd(env.orders, env.shippers, shipper_id))


def test_complete_pickup_moves_shipper_only(env):
    complete(env, "S02")
    shipper = env.shippers.get_by_id("S02")
    assert shipper.node_id == "P01" and len(shipper.route) == 1 and shipper.load_kg == 10.0
    assert env.orders.get_by_id("O005").status == OrderStatus.ASSIGNED


def test_complete_delivery_delivers_order_and_lowers_load(env):
    complete(env, "S02")
    complete(env, "S02")
    shipper = env.shippers.get_by_id("S02")
    assert shipper.node_id == "P11" and not shipper.route and shipper.load_kg == 0.0
    assert env.orders.get_by_id("O005").status == OrderStatus.DELIVERED


def test_undo_complete_restores_shipper_and_order_exactly(env):
    shipper_0 = env.shippers.get_by_id("S02").to_dict()
    complete(env, "S02")
    shipper_1 = env.shippers.get_by_id("S02").to_dict()
    order_1 = env.orders.get_by_id("O005").to_dict()
    complete(env, "S02")
    env.history.undo()
    assert env.shippers.get_by_id("S02").to_dict() == shipper_1
    assert env.orders.get_by_id("O005").to_dict() == order_1 and order_1["status"] == "ASSIGNED"
    env.history.undo()
    assert env.shippers.get_by_id("S02").to_dict() == shipper_0
    env.history.redo()
    env.history.redo()
    assert env.orders.get_by_id("O005").status == OrderStatus.DELIVERED


def test_complete_without_route_is_rejected(env):
    with pytest.raises(BusinessRuleError):
        complete(env, "S01")
    with pytest.raises(NotFoundError):
        complete(env, "S99")
    assert not env.history.can_undo()


def test_full_flow_assign_complete_then_undo_everything(env):
    shipper_before = env.shippers.get_by_id("S01").to_dict()
    order_before = env.orders.get_by_id("O001").to_dict()
    assign(env, "O001", "S01")
    complete(env, "S01")
    complete(env, "S01")
    assert env.orders.get_by_id("O001").status == OrderStatus.DELIVERED
    for _ in range(3):
        env.history.undo()
    assert env.shippers.get_by_id("S01").to_dict() == shipper_before
    assert env.orders.get_by_id("O001").to_dict() == order_before
    assert env.queue.to_list() == ["O001", "O002", "O003"]