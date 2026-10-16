"""Test OrderQueue (Queue) và CommandHistory (2 Stack). Không phụ thuộc models hay repository.

Người phụ trách: Tiên.
"""
import pytest

from services.history import Command, CommandHistory
from services.order_queue import OrderQueue


# ---------------------------------------------------------------- OrderQueue
def test_queue_is_fifo():
    q = OrderQueue()
    for order_id in ("O1", "O2", "O3"):
        q.enqueue(order_id)
    assert q.peek() == "O1"
    assert [q.dequeue(), q.dequeue(), q.dequeue()] == ["O1", "O2", "O3"]


def test_queue_empty_returns_none():
    q = OrderQueue()
    assert q.dequeue() is None and q.peek() is None and len(q) == 0


def test_queue_remove_and_index_of():
    q = OrderQueue()
    for order_id in ("O1", "O2", "O3"):
        q.enqueue(order_id)
    assert q.index_of("O2") == 1 and q.index_of("O9") is None
    assert q.remove("O2") is True and q.remove("O2") is False
    assert q.to_list() == ["O1", "O3"]


def test_queue_insert_at_restores_position():
    q = OrderQueue()
    for order_id in ("O1", "O2", "O3"):
        q.enqueue(order_id)
    index = q.index_of("O2")
    q.remove("O2")
    q.insert_at(index, "O2")
    assert q.to_list() == ["O1", "O2", "O3"]


def test_queue_insert_at_clamps_out_of_range_index():
    q = OrderQueue()
    q.enqueue("O1")
    q.insert_at(99, "O2")
    q.insert_at(-5, "O0")
    assert q.to_list() == ["O0", "O1", "O2"]


def test_queue_rejects_duplicates():
    q = OrderQueue()
    q.enqueue("O1")
    with pytest.raises(ValueError):
        q.enqueue("O1")
    with pytest.raises(ValueError):
        q.insert_at(0, "O1")


def test_queue_to_list_is_a_copy_and_clear():
    q = OrderQueue()
    q.enqueue("O1")
    snapshot = q.to_list()
    snapshot.append("HACK")
    assert q.to_list() == ["O1"] and "O1" in q
    q.clear()
    assert len(q) == 0


# ------------------------------------------------------- CommandHistory
class Add(Command):
    """Lệnh thử: cộng vào một số dùng chung. Chụp snapshot giá trị cũ trong apply()."""

    def __init__(self, box: dict, step: int) -> None:
        self._box, self._step = box, step
        self._before: int | None = None
        self.description = f"+{step}"

    def apply(self) -> None:
        self._before = self._box["v"]          # snapshot
        self._box["v"] += self._step

    def undo(self) -> None:
        self._box["v"] = self._before          # khôi phục từ snapshot, không tự tính ngược


class Broken(Command):
    description = "hỏng"

    def __init__(self, fail_on: str) -> None:
        self._fail_on = fail_on

    def apply(self) -> None:
        if self._fail_on == "apply":
            raise RuntimeError("apply lỗi")

    def undo(self) -> None:
        if self._fail_on == "undo":
            raise RuntimeError("undo lỗi")


def test_undo_redo_roundtrip():
    box, h = {"v": 10}, CommandHistory()
    h.execute(Add(box, 5))
    h.execute(Add(box, 7))
    assert box["v"] == 22
    assert h.undo().description == "+7" and box["v"] == 15
    assert h.undo().description == "+5" and box["v"] == 10
    assert h.redo().description == "+5" and box["v"] == 15
    assert h.redo().description == "+7" and box["v"] == 22


def test_empty_stacks_return_none_and_flags():
    h = CommandHistory()
    assert h.undo() is None and h.redo() is None
    assert not h.can_undo() and not h.can_redo()
    assert h.undo_label() is None and h.redo_label() is None


def test_new_command_clears_redo_stack():
    box, h = {"v": 0}, CommandHistory()
    h.execute(Add(box, 1))
    h.execute(Add(box, 2))
    h.undo()
    assert h.can_redo() and h.redo_label() == "+2"
    h.execute(Add(box, 3))
    assert not h.can_redo() and h.undo_label() == "+3"


def test_labels_follow_the_top_of_each_stack():
    box, h = {"v": 0}, CommandHistory()
    h.execute(Add(box, 1))
    h.execute(Add(box, 2))
    assert h.undo_label() == "+2"
    h.undo()
    assert h.undo_label() == "+1" and h.redo_label() == "+2"


def test_failed_apply_is_not_recorded():
    h = CommandHistory()
    with pytest.raises(RuntimeError):
        h.execute(Broken("apply"))
    assert not h.can_undo()


def test_failed_undo_keeps_command_on_undo_stack():
    h = CommandHistory()
    h.execute(Broken("undo"))
    with pytest.raises(RuntimeError):
        h.undo()
    assert h.can_undo() and not h.can_redo()