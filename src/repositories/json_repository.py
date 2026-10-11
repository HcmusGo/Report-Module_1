"""Repository lưu bằng file JSON. Người phụ trách: Tâm."""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Generic

from config import DATA_DIR, SAMPLE_DIR
from repositories.base_repository import Repository, T


class JsonRepository(Repository[T], Generic[T]):
    """Cài đặt chung. Lớp con chỉ khai báo filename, entity_cls, id_prefix.

    Yêu cầu khi cài:
    - Dùng self._items: dict[str, T] làm index theo id (tra cứu O(1)).
    - Lần đầu chưa có file: chép từ SAMPLE_DIR, không có mẫu thì tạo danh sách rỗng.
    - File JSON hỏng: bắt json.JSONDecodeError, đổi tên file lỗi thành .bak
      rồi khởi tạo lại, KHÔNG để app crash.
    - Ghi file với encoding="utf-8" và ensure_ascii=False (tiếng Việt có dấu).
    - Mọi thao tác add / update / delete đều ghi file ngay.
    """

    filename: ClassVar[str] = ""
    id_prefix: ClassVar[str] = "X"

    def __init__(self, data_dir: Path = DATA_DIR, sample_dir: Path = SAMPLE_DIR) -> None:
        self._data_dir = data_dir
        self._sample_dir = sample_dir
        self._items: dict[str, T] = {}
        # TODO(Tâm): gọi self._load() ở đây khi đã cài xong.

    @classmethod
    def _entity_from_dict(cls, data: dict) -> T:
        """Lớp con trả về đúng entity, ví dụ MenuItem.from_dict(data)."""
        raise NotImplementedError

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
