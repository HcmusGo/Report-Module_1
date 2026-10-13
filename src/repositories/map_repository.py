"""Lưu bản đồ vào data/map.json. Người phụ trách: Tâm.

Khác các repository còn lại: một file chứa cả hai danh sách
{"places": [...], "roads": [...]} nên có giao diện riêng.
Áp dụng cùng quy tắc: dữ liệu khởi tạo có sẵn trong file, load() chỉ đọc (thiếu file thì
trả hai danh sách rỗng, không ghi), bắt JSON hỏng, UTF-8. Chỉ save() mới ghi file.
"""
from __future__ import annotations

from pathlib import Path

from config import DATA_DIR
from models.map_entities import Place, Road


class MapRepository:
    filename = "map.json"

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir

    def load(self) -> tuple[list[Place], list[Road]]:
        raise NotImplementedError("TODO(Tâm)")

    def save(self, places: list[Place], roads: list[Road]) -> None:
        raise NotImplementedError("TODO(Tâm)")
