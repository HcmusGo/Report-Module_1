"""Lớp cơ sở cho entity. Người phụ trách: Quyên."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseEntity(ABC):
    """Mọi entity có id và tự (de)serialize sang dict để lưu JSON."""

    @property
    @abstractmethod
    def id(self) -> str:
        ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEntity":
        ...
