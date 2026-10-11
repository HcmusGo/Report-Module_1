"""Controller cho Tab 2: Điều phối đơn. Người phụ trách: Lâm.

Cùng quy ước với CatalogController: bắt AppError, trả Result, không chứa luật nghiệp vụ.
"""
from __future__ import annotations

from controllers.result import Result
from services.dispatch_service import DispatchService, RoutePlan
from services.history import CommandHistory
from services.map_service import MapService
from services.order_service import OrderService


class DispatchController:
    def __init__(self, orders: OrderService, dispatch: DispatchService,
                 maps: MapService, history: CommandHistory) -> None:
        self._orders, self._dispatch, self._maps, self._history = orders, dispatch, maps, history

    # ---- Đơn hàng và bếp ----
    def create_order(self, customer_id: str, items: dict[str, int], note: str = "") -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def cancel_order(self, order_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def start_next_in_kitchen(self) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def mark_ready(self, order_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def orders_table(self, status: str | None = None, keyword: str = "") -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    def kitchen_table(self) -> list[dict]:
        raise NotImplementedError("TODO(Lâm)")

    # ---- Giao hàng ----
    def assign_shipper(self, order_id: str) -> Result:
        """Result.data là RoutePlan khi thành công."""
        raise NotImplementedError("TODO(Lâm)")

    def complete_delivery(self, order_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def route_plan(self, order_id: str) -> RoutePlan | None:
        """Lộ trình của đơn đang giao, để vẽ lên bản đồ."""
        raise NotImplementedError("TODO(Lâm)")

    def map_figure_data(self, highlight_paths: list[list[str]] | None = None) -> dict:
        """Dữ liệu thuần để vẽ bản đồ: {'nodes': [...], 'edges': [...], 'highlight': [...]}."""
        raise NotImplementedError("TODO(Lâm)")

    def compare_routers(self, src: str, dst: str) -> list[dict]:
        """Bảng so sánh Dijkstra với BFS (cost, nodes_visited, ms)."""
        raise NotImplementedError("TODO(Lâm)")

    # ---- Undo / Redo ----
    def undo(self) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def redo(self) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    def can_undo(self) -> bool:
        raise NotImplementedError("TODO(Lâm)")

    def can_redo(self) -> bool:
        raise NotImplementedError("TODO(Lâm)")

    def undo_label(self) -> str | None:
        raise NotImplementedError("TODO(Lâm)")

    def redo_label(self) -> str | None:
        raise NotImplementedError("TODO(Lâm)")
