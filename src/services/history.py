"""Undo / Redo bằng 2 Stack theo Command pattern. Người phụ trách: Tiên."""
from __future__ import annotations

from abc import ABC, abstractmethod


class Command(ABC):
    """Một thao tác có thể hoàn tác. Lớp con cụ thể nằm trong commands.py."""

    description: str = ""   # mô tả ngắn để hiện trên UI, ví dụ "Tạo đơn O001"

    @abstractmethod
    def apply(self) -> None:
        """Thực hiện thao tác (và lưu dữ liệu)."""

    @abstractmethod
    def undo(self) -> None:
        """Đảo ngược đúng thao tác trên, trả mọi thứ về trạng thái trước đó."""


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
        """Mô tả thao tác sẽ bị hoàn tác, để hiện trên nút Undo."""
        raise NotImplementedError("TODO(Tiên)")

    def redo_label(self) -> str | None:
        raise NotImplementedError("TODO(Tiên)")
