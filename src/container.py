"""Ghép nối toàn bộ ứng dụng (Dependency Injection). Người phụ trách: Tiên.

Đây là NƠI DUY NHẤT biết lớp cụ thể nào dùng với lớp nào: Repository -> Service -> Controller.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config import DATA_DIR, SAMPLE_DIR
from controllers.dispatch_controller import DispatchController
from controllers.order_controller import OrderController
from models.map_entities import Place, Road
from models.order import Order
from models.shipper import Shipper
from repositories.json_repository import JsonRepository
from services.catalog_service import CatalogService
from services.dispatch_service import DispatchService
from services.history import CommandHistory
from services.order_queue import OrderQueue
from services.order_service import OrderService
from services.routing import DijkstraRouter, RoadNetwork


log = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Thứ duy nhất app.py giữ trong st.session_state."""

    orders: OrderController
    dispatch: DispatchController


def build_container(data_dir: Path = DATA_DIR, sample_dir: Path = SAMPLE_DIR,
                    restore_queue: bool = True) -> AppContext:
    """Dựng toàn bộ ứng dụng. restore_queue=False dùng khi chỉ muốn kiểm tra việc ghép nối
    mà chưa đọc dữ liệu (ví dụ test khi JsonRepository chưa được cài)."""
    # Repository: một lớp JsonRepository dùng cho cả 4 loại dữ liệu
    order_repo = JsonRepository(Order, "orders.json", "O", data_dir, sample_dir)
    shipper_repo = JsonRepository(Shipper, "shippers.json", "S", data_dir, sample_dir)
    place_repo = JsonRepository(Place, "places.json", "P", data_dir, sample_dir)
    road_repo = JsonRepository(Road, "roads.json", "R", data_dir, sample_dir)

    # Thành phần dùng chung (MỘT bản duy nhất để Undo / Redo xuyên suốt mọi thao tác)
    history = CommandHistory()
    queue = OrderQueue()
    network = RoadNetwork(place_repo, road_repo)
    router = DijkstraRouter()

    # Service
    catalog_service = CatalogService(place_repo, road_repo, shipper_repo)
    order_service = OrderService(order_repo, place_repo, queue, history)
    dispatch_service = DispatchService(order_repo, shipper_repo, network, router, queue, history)

    # Dựng lại hàng đợi đơn chờ từ dữ liệu đã lưu.
    if restore_queue:
        try:
            order_service.restore_queue()
        except NotImplementedError:
            # TẠM THỜI: JsonRepository (Tâm) hoặc models (Quyên) chưa cài xong thì vẫn cho app mở
            # được để Lâm làm giao diện. TODO(Tiên): xóa khối try / except này sau khi hai PR đó merge.
            log.warning("Chưa khôi phục được hàng đợi: repository hoặc models chưa được cài đặt")

    # Controller
    return AppContext(
        orders=OrderController(order_service, catalog_service),
        dispatch=DispatchController(order_service, dispatch_service, catalog_service, history),
    )