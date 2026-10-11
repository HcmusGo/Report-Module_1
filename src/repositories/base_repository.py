"""Giao diện Repository dùng chung. Người phụ trách: Tâm.

Service chỉ biết giao diện này, không biết dữ liệu nằm ở JSON hay nơi khác.
Muốn đổi JSON sang CSV / SQLite: viết repository mới, Service giữ nguyên.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from models.base import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class Repository(ABC, Generic[T]):
    @abstractmethod
    def get_all(self) -> list[T]:
        """Toàn bộ đối tượng, theo thứ tự thêm vào."""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> T | None:
        """Tra theo id (O(1) nhờ dict). Không thấy thì trả None."""

    @abstractmethod
    def add(self, entity: T) -> None:
        """Thêm mới và lưu file. Trùng id thì ném ValidationError."""

    @abstractmethod
    def update(self, entity: T) -> None:
        """Ghi đè đối tượng cùng id và lưu file. Không có id thì ném NotFoundError."""

    @abstractmethod
    def delete(self, entity_id: str) -> T | None:
        """Xóa và lưu file. Trả về đối tượng đã xóa (để Undo khôi phục)."""

    @abstractmethod
    def next_id(self) -> str:
        """Sinh id mới, ví dụ 'M001', 'O017'."""
