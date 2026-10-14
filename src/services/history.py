"""Undo / Redo bằng 2 Stack theo Command pattern. Người phụ trách: Tiên."""
from __future__ import annotations

from abc import ABC, abstractmethod


class Command(ABC):
    """Một thao tác có thể hoàn tác. Lớp con cụ thể nằm trong commands.py.

    QUY TẮC SNAPSHOT (góp ý của mentor):
    - apply() phải CHỤP LẠI trạng thái trước khi thay đổi (ví dụ order.to_dict(),
      vị trí trong hàng đợi) và lưu vào thuộc tính của Command.
    - undo() chỉ KHÔI PHỤC từ snapshot đó. KHÔNG gán cứng giá trị mặc định
      (ví dụ không viết `status = WAITING` hay `load_kg = 0`), vì trạng thái trước
      đó có thể khác.
    - apply() bị gọi lại khi Redo nên chụp snapshot MỚI ở mỗi lần gọi.
    - Snapshot phải là bản sao độc lập (to_dict() hoặc copy.deepcopy), không giữ
      tham chiếu tới đối tượng đang bị sửa.
    """

    description: str = ""   # mô tả ngắn để hiện trên UI, ví dụ "Gán O003 cho S01"

    @abstractmethod
    def apply(self) -> None:
        """Chụp snapshot rồi thực hiện thao tác (và lưu dữ liệu)."""

    @abstractmethod
    def undo(self) -> None:
        """Khôi phục dữ liệu từ snapshot do apply() chụp."""


class CommandHistory:
    """Hai Stack: _undo_stack và _redo_stack (list: append = push, pop = pop)."""

    def __init__(self) -> None:
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []

    def execute(self, cmd: Command) -> None:
        """cmd.apply(), push vào undo, XÓA redo_stack."""
        raise NotImplementedError("TODO(Tiên)")

    def undo(self) -> Command | None:
        """Pop undo, gọi undo(), push sang redo. Stack rỗng thì trả None."""
        raise NotImplementedError("TODO(Tiên)")

    def redo(self) -> Command | None:
        """Pop redo, gọi apply(), push lại undo. Stack rỗng thì trả None."""
        raise NotImplementedError("TODO(Tiên)")

    def can_undo(self) -> bool:
        raise NotImplementedError("TODO(Tiên)")

    def can_redo(self) -> bool:
        raise NotImplementedError("TODO(Tiên)")

    def undo_label(self) -> str | None:
        """Mô tả thao tác sắp bị hoàn tác, hiện trên nút Undo."""
        raise NotImplementedError("TODO(Tiên)")

    def redo_label(self) -> str | None:
        raise NotImplementedError("TODO(Tiên)")
