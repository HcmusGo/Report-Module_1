"""Lưu bản đồ vào data/map.json. Người phụ trách: Tâm.

Khác các repository còn lại: một file chứa cả hai danh sách
{"places": [...], "roads": [...]} nên có giao diện riêng.
Áp dụng cùng quy tắc: tạo từ mẫu khi chưa có, bắt JSON hỏng, UTF-8.
"""
from __future__ import annotations

from pathlib import Path

from config import DATA_DIR, SAMPLE_DIR
from models.map_entities import Place, Road


class MapRepository:
    filename = "map.json"

    def __init__(self, data_dir: Path = DATA_DIR, sample_dir: Path = SAMPLE_DIR) -> None:
        self._data_dir = data_dir
        self._sample_dir = sample_dir

    def load(self) -> tuple[list[Place], list[Road]]:
        raise NotImplementedError("TODO(Tâm)")

    def save(self, places: list[Place], roads: list[Road]) -> None:
        raise NotImplementedError("TODO(Tâm)")
