"""Repository lưu bằng file JSON dùng chung cho mọi entity. Người phụ trách: Tâm."""
from __future__ import annotations

from pathlib import Path
from typing import Generic

from config import DATA_DIR, SAMPLE_DIR
from repositories.base_repository import Repository, T


class JsonRepository(Repository[T], Generic[T]):
    """Một lớp cho cả 4 loại dữ liệu, khác nhau ở entity_cls và filename:
    JsonRepository(Order, "orders.json", "O"), JsonRepository(Place, "places.json", "P"), ...

    Yêu cầu khi cài:
    - self._items: dict[str, T] làm index theo id (tra cứu O(1)), giữ thứ tự thêm vào.
    - Lần đầu chưa có file trong data/: chép từ data/sample/ (dữ liệu khởi tạo sẵn);
      không có mẫu thì tạo danh sách rỗng.
    - File JSON hỏng: bắt json.JSONDecodeError, đổi tên file lỗi thành .bak rồi
      khởi tạo lại từ mẫu, KHÔNG để app crash.
    - Ghi file encoding="utf-8", ensure_ascii=False (tiếng Việt có dấu), ghi ngay sau
      mỗi add / update / delete.
    - Entity được dựng qua entity_cls.from_dict(data), lưu qua entity.to_dict().
    """

    def __init__(self, entity_cls: type[T], filename: str, id_prefix: str,
                 data_dir: Path = DATA_DIR, sample_dir: Path = SAMPLE_DIR) -> None:
        self._entity_cls = entity_cls
        self._filename = filename
        self._id_prefix = id_prefix
        self._data_dir = data_dir
        self._sample_dir = sample_dir
        self._items: dict[str, T] = {}
        # TODO(Tâm): gọi self._load() ở đây khi đã cài xong.

    def _load(self) -> None:
        raise NotImplementedError("TODO(Tâm)")

    def _flush(self) -> None:
        raise NotImplementedError("TODO(Tâm)")

    def get_all(self) -> list[T]:
        raise NotImplementedError("TODO(Tâm)")

    def get_by_id(self, entity_id: str) -> T | None:
        raise NotImplementedError("TODO(Tâm)")

    def add(self, entity: T) -> None:
        raise NotImplementedError("TODO(Tâm)")

    def update(self, entity: T) -> None:
        raise NotImplementedError("TODO(Tâm)")

    def delete(self, entity_id: str) -> T | None:
        raise NotImplementedError("TODO(Tâm)")

    def next_id(self) -> str:
        raise NotImplementedError("TODO(Tâm)")
