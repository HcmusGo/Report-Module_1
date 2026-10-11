"""Kiểm tra khung dự án: import được, nối dây được, quy tắc trạng thái đúng.

Mỗi người tự thêm file test cho phần của mình (test_models.py, test_repository.py,
test_history.py, test_routing.py...). Dùng `uv run pytest`.
"""
import importlib

import pytest

from container import build_container
from controllers.result import Result
from models.order import OrderStatus, can_transition
from services.routing import PathResult

MODULES = [
    "config", "exceptions",
    "models.base", "models.menu_item", "models.customer", "models.shipper",
    "models.order", "models.map_entities",
    "repositories.base_repository", "repositories.json_repository",
    "repositories.menu_repository", "repositories.customer_repository",
    "repositories.shipper_repository", "repositories.order_repository",
    "repositories.map_repository",
    "services.kitchen_queue", "services.history", "services.commands",
    "services.road_network", "services.routing", "services.catalog_service",
    "services.map_service", "services.order_service", "services.dispatch_service",
    "controllers.result", "controllers.catalog_controller", "controllers.dispatch_controller",
    "container",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(name)


def test_container_builds():
    ctx = build_container()
    assert ctx.catalog is not None and ctx.dispatch is not None


def test_order_status_transitions():
    assert can_transition(OrderStatus.NEW, OrderStatus.PREPARING)
    assert can_transition(OrderStatus.READY, OrderStatus.CANCELLED)
    assert not can_transition(OrderStatus.DELIVERED, OrderStatus.CANCELLED)
    assert not can_transition(OrderStatus.NEW, OrderStatus.DELIVERING)


def test_result_helpers():
    assert Result.success("ok").ok is True
    assert Result.fail("lỗi").ok is False


def test_path_result_not_found():
    assert PathResult.not_found().found is False
