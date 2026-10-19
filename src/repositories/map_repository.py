from __future__ import annotations

import json
from pathlib import Path

from config import DATA_DIR
from models.map_entities import Place, Road


class MapRepository:
    filename = "map.json"

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir
        self._file_path = self._data_dir / self.filename

    def load(self) -> tuple[list[Place], list[Road]]:
        if not self._file_path.exists():
            return [], []

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    return [], []
                
                places_data = data.get("places", [])
                roads_data = data.get("roads", [])
                
                places = [Place.from_dict(p) for p in places_data]
                roads = [Road.from_dict(r) for r in roads_data]
                
                return places, roads
        except (json.JSONDecodeError, IOError):
            return [], []

    def save(self, places: list[Place], roads: list[Road]) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "places": [p.to_dict() for p in places],
            "roads": [r.to_dict() for r in roads],
        }
        
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
