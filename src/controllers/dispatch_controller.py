"""Controller cho Tab 2: Điều phối đơn. Người phụ trách: Lâm.

Cùng quy ước với OrderController: bắt AppError, trả Result, không chứa luật nghiệp vụ.
"""
from __future__ import annotations

from controllers.result import Result
from services.catalog_service import CatalogService
from services.dispatch_service import DispatchService
from services.history import CommandHistory
from services.order_service import OrderService


class DispatchController:
    def __init__(self, orders: OrderService, dispatch: DispatchService,
                 catalog: CatalogService, history: CommandHistory) -> None:
        self._orders, self._dispatch = orders, dispatch
        self._catalog, self._history = catalog, history

    # ---- Hàng đợi và đề xuất ----
    def waiting_table(self) -> list[dict]:
        """Các đơn đang chờ theo đúng thứ tự hàng đợi."""
        raise NotImplementedError("TODO(Lâm)")

    def suggest_table(self, order_id: str) -> Result:
        """Result.data = list[dict]: mỗi shipper một dòng (phù hợp hay không, lý do, ETA...)."""
        raise NotImplementedError("TODO(Lâm)")

    def assign(self, order_id: str, shipper_id: str | None = None) -> Result:
        """Gán shipper (mặc định là shipper phù hợp nhất)."""
        raise NotImplementedError("TODO(Lâm)")

    def complete_next_stop(self, shipper_id: str) -> Result:
        raise NotImplementedError("TODO(Lâm)")

    # ---- Lộ trình và bản đồ ----
    def route_table(self) -> list[dict]:
        """Lộ trình hiện tại của từng shipper (các điểm dừng còn lại)."""
        raise NotImplementedError("TODO(Lâm)")

    def map_figure_data(self, highlight_paths: list[list[str]] | None = None) -> dict:
        """Dữ liệu thuần để vẽ bản đồ: {'nodes': [...], 'edges': [...], 'highlight': [...]}.
        Đường vẽ màu theo mức đông (LOW, MEDIUM, HIGH)."""
        raise NotImplementedError("TODO(Lâm)")

    def compare_routes(self, src: str, dst: str) -> list[dict]:
        """Bảng so sánh đường ngắn nhất theo km với đường nhanh nhất theo phút."""
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
