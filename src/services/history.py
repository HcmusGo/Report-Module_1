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
        """cmd.apply(), push vào undo, XÓA redo_stack.
        Nếu apply() ném lỗi thì lệnh không được ghi vào lịch sử."""
        cmd.apply()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()

    def undo(self) -> Command | None:
        """Pop undo, gọi undo(), push sang redo. Stack rỗng thì trả None.
        Nếu undo() ném lỗi, lệnh được trả lại đỉnh undo_stack để không mất lịch sử."""
        if not self._undo_stack:
            return None
        cmd = self._undo_stack.pop()
        try:
            cmd.undo()
        except Exception:
            self._undo_stack.append(cmd)
            raise
        self._redo_stack.append(cmd)
        return cmd

    def redo(self) -> Command | None:
        """Pop redo, gọi apply(), push lại undo. Stack rỗng thì trả None."""
        if not self._redo_stack:
            return None
        cmd = self._redo_stack.pop()
        try:
            cmd.apply()
        except Exception:
            self._redo_stack.append(cmd)
            raise
        self._undo_stack.append(cmd)
        return cmd

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo_label(self) -> str | None:
        """Mô tả thao tác sắp bị hoàn tác, hiện trên nút Undo."""
        return self._undo_stack[-1].description if self._undo_stack else None

    def redo_label(self) -> str | None:
        """Mô tả thao tác sắp được làm lại, hiện trên nút Redo."""
        return self._redo_stack[-1].description if self._redo_stack else None