"""Kết quả chuẩn mà Controller trả cho giao diện. Người phụ trách: Lâm."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Result:
    ok: bool
    message: str
    data: Any = None

    @classmethod
    def success(cls, message: str, data: Any = None) -> "Result":
        return cls(True, message, data)

    @classmethod
    def fail(cls, message: str) -> "Result":
        return cls(False, message)
