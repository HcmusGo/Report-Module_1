"""Kiểm tra khung dự án: import được, nối dây được, luật trạng thái đúng.

Mỗi người tự thêm file test cho phần của mình (test_models.py, test_repository.py,
test_history.py, test_routing.py, test_dispatch.py...). Dùng `uv run pytest`.
"""
import importlib

import pytest

from container import build_container
from controllers.result import Result
from models.order import OrderStatus, can_transition
from services.routing import PathResult

MODULES = [
    "config", "exceptions",
    "models.base", "models.map_entities", "models.order", "models.shipper",
    "repositories.base_repository", "repositories.json_repository",
    "services.order_queue", "services.history", "services.commands",
    "services.order_service", "services.catalog_service",
    "services.routing", "services.dispatch_service",
    "controllers.result", "controllers.order_controller", "controllers.dispatch_controller",
    "container",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(name)


def test_container_builds():
    ctx = build_container()
    assert ctx.orders is not None and ctx.dispatch is not None


def test_order_status_transitions():
    assert can_transition(OrderStatus.WAITING, OrderStatus.ASSIGNED)
    assert can_transition(OrderStatus.ASSIGNED, OrderStatus.DELIVERED)
    assert not can_transition(OrderStatus.DELIVERED, OrderStatus.WAITING)
    assert not can_transition(OrderStatus.WAITING, OrderStatus.DELIVERED)


def test_result_helpers():
    assert Result.success("ok").ok is True
    assert Result.fail("lỗi").ok is False


def test_path_result_not_found():
    assert PathResult.not_found().found is False
