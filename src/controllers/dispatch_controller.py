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
        self._dispatch.get_waiting_table()


    def suggest_table(self, order_id: str) -> Result:
        """Result.data = list[dict]: mỗi shipper một dòng (phù hợp hay không, lý do, ETA...)."""
        try 
        self._dispatch.get_suggestions (order_id=order_id) = suggestion
        return Result.success (data = suggestion)
        except AppError as e:
            return Result.fail(str(e))

    def assign(self, order_id: str, shipper_id: str | None = None) -> Result:
        """Gán shipper (mặc định là shipper phù hợp nhất)."""
        try 
        self._dispatch.assign(order_id=order_id, shipper_id=shipper=id)
        return Result.success ("Điều phối đơn hàng {order_id} thành công")
        except AppError as e:
            return Result.fail(str(e))
    def complete_next_stop(self, shipper_id: str) -> Result:
        try 
        self._dispatch.complete_next_stop(shipper_id=shipper_id)
        return Result.success ("Hoàn thành điểm dừng cho shipper_id {shipper_id} thành công")
        except AppError as e:
            return Result.fail(str(e))

    # ---- Lộ trình và bản đồ ----
    def route_table(self) -> list[dict]:
        """Lộ trình hiện tại của từng shipper (các điểm dừng còn lại)."""
       return self._dispatch.route_table()

    def map_figure_data(self, highlight_paths: list[list[str]] | None = None) -> dict:
        """Dữ liệu thuần để vẽ bản đồ: {'nodes': [...], 'edges': [...], 'highlight': [...]}.
        Đường vẽ màu theo mức đông (LOW, MEDIUM, HIGH)."""
       return self._dispatch.map_figure_data (highlight_paths=highlight_paths)

    def compare_routes(self, src: str, dst: str) -> list[dict]:
        """Bảng so sánh đường ngắn nhất theo km với đường nhanh nhất theo phút."""
        return self._dispatch.compare_routes (src=src, dst=dst)

    # ---- Undo / Redo ----
    def undo(self) -> Result:
        try 
        self._history.undo()
        return Result.success ("Đã hoàn tác (undo) hành động trước đó")
        except AppError as e:
            return Result.fail(str(e))

    def redo(self) -> Result:
        try 
        self._history.redo()
        return Result.success ("Đã làm lại (redo) hành động trước đó")
        except AppError as e:
            return Result.fail(str(e))
    def can_undo(self) -> bool:
        return self._history.can_undo()

    def can_redo(self) -> bool:
        return self._history.can_redo()

    def undo_label(self) -> str | None:
        return self._history.can_undo_label()

    def redo_label(self) -> str | None:
        return self._history.can_redo_label()
