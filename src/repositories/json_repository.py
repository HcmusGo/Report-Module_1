from __future__ import annotations

import json
from pathlib import Path
from typing import Generic

from config import DATA_DIR, SAMPLE_DIR
from repositories.base_repository import Repository, T


class JsonRepository(Repository[T], Generic[T]):
    def __init__(self, entity_cls: type[T], filename: str, id_prefix: str,
                 data_dir: Path = DATA_DIR, sample_dir: Path = SAMPLE_DIR) -> None:
        self._entity_cls = entity_cls
        self._filename = filename
        self._id_prefix = id_prefix
        self._data_dir = data_dir
        self._sample_dir = sample_dir
        self._items: dict[str, T] = {}
        self._load()

    def _load(self) -> None:
        file_path = self._data_dir / self._filename
        sample_path = self._sample_dir / self._filename

        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if sample_path.exists():
                with open(sample_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=4)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except (json.JSONDecodeError, Exception):
            bak_path = file_path.with_suffix(file_path.suffix + '.bak')
            if file_path.exists():
                file_path.rename(bak_path)
            
            if sample_path.exists():
                with open(sample_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

        self._items.clear()
        for item_dict in raw_data:
            if item_dict:  # Kiểm tra item trong JSON không được rỗng
                entity = self._entity_cls.from_dict(item_dict)
                if entity is not None and hasattr(entity, 'id'):
                    self._items[entity.id] = entity

    def _flush(self) -> None:
        file_path = self._data_dir / self._filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')

        try:
            raw_data = [item.to_dict() for item in self._items.values()]
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=4)
            temp_path.replace(file_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Không thể ghi dữ liệu xuống file {file_path}: {e}")

    def get_all(self) -> list[T]:
        return list(self._items.values())

    def get_by_id(self, entity_id: str) -> T | None:
        return self._items.get(entity_id)

    def add(self, entity: T) -> None:
        self._items[entity.id] = entity
        self._flush()

    def update(self, entity: T) -> None:
        if entity.id in self._items:
            self._items[entity.id] = entity
            self._flush()
        else:
            raise ValueError(f"Không tìm thấy thực thể với ID {entity.id} để cập nhật.")

    def delete(self, entity_id: str) -> T | None:
        removed = self._items.pop(entity_id, None)
        if removed is not None:
            self._flush()
        return removed

    def next_id(self) -> str:
        existing_ids = list(self._items.keys())
        if not existing_ids:
            return f"{self._id_prefix}1"
        
        numeric_parts = []
        for eid in existing_ids:
            num_str = eid.replace(self._id_prefix, "")
            if num_str.isdigit():
                numeric_parts.append(int(num_str))
        
        next_num = max(numeric_parts) + 1 if numeric_parts else len(existing_ids) + 1
        return f"{self._id_prefix}{next_num}"