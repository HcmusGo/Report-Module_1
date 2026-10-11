"""Ghép nối toàn bộ ứng dụng (Dependency Injection). Người phụ trách: Tiên.

Đây là NƠI DUY NHẤT biết lớp cụ thể nào dùng với lớp nào:
Repository -> Service -> Controller. Service chỉ nhận Repository qua constructor.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import DATA_DIR, SAMPLE_DIR
from controllers.catalog_controller import CatalogController
from controllers.dispatch_controller import DispatchController
from repositories.customer_repository import CustomerRepository
from repositories.map_repository import MapRepository
from repositories.menu_repository import MenuRepository
from repositories.order_repository import OrderRepository
from repositories.shipper_repository import ShipperRepository
from services.catalog_service import CatalogService
from services.dispatch_service import DispatchService
from services.history import CommandHistory
from services.kitchen_queue import KitchenQueue
from services.map_service import MapService
from services.order_service import OrderService
from services.road_network import RoadNetwork
from services.routing import DijkstraRouter


@dataclass
class AppContext:
    """Thứ duy nhất app.py giữ trong st.session_state."""

    catalog: CatalogController
    dispatch: DispatchController


def build_container(data_dir: Path = DATA_DIR, sample_dir: Path = SAMPLE_DIR) -> AppContext:
    # Repository
    menu_repo = MenuRepository(data_dir, sample_dir)
    customer_repo = CustomerRepository(data_dir, sample_dir)
    shipper_repo = ShipperRepository(data_dir, sample_dir)
    order_repo = OrderRepository(data_dir, sample_dir)
    map_repo = MapRepository(data_dir, sample_dir)

    # Thành phần dùng chung (một bản duy nhất để Undo / Redo xuyên suốt mọi thao tác)
    history = CommandHistory()
    kitchen = KitchenQueue()
    network = RoadNetwork()
    router = DijkstraRouter()

    # Service
    catalog_service = CatalogService(menu_repo, customer_repo, shipper_repo)
    map_service = MapService(map_repo, network, history)
    order_service = OrderService(order_repo, menu_repo, customer_repo, kitchen, history)
    dispatch_service = DispatchService(order_repo, shipper_repo, customer_repo,
                                       map_service, router, history)

    # TODO(Tiên, Bảo): khi các service đã cài xong, gọi thêm ở đây:
    #   map_service.load()
    #   order_service.restore_kitchen_queue()

    # Controller
    return AppContext(
        catalog=CatalogController(catalog_service, map_service),
        dispatch=DispatchController(order_service, dispatch_service, map_service, history),
    )
