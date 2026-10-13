"""Repository lưu bằng file JSON. Người phụ trách: Tâm."""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Generic

from config import DATA_DIR
from repositories.base_repository import Repository, T


class JsonRepository(Repository[T], Generic[T]):
    """Cài đặt chung. Lớp con chỉ khai báo filename, entity_cls, id_prefix.

    Dữ liệu khởi tạo đã nằm sẵn trong data/*.json (có commit). Repository KHÔNG sinh dữ liệu
    mẫu và KHÔNG tự tạo file lúc khởi động.

    Yêu cầu khi cài:
    - Dùng self._items: dict[str, T] làm index theo id (tra cứu O(1)).
    - _load() chỉ ĐỌC, không bao giờ ghi file.
    - Chưa có file: bắt FileNotFoundError, giữ danh sách rỗng trong bộ nhớ, không ghi gì ra đĩa
      (file chỉ xuất hiện khi người dùng thật sự thêm dữ liệu đầu tiên).
    - File JSON hỏng: bắt json.JSONDecodeError, đổi tên file lỗi thành .bak
      rồi dùng danh sách rỗng, KHÔNG để app crash.
    - Ghi file với encoding="utf-8" và ensure_ascii=False (tiếng Việt có dấu).
    - Chỉ add / update / delete mới gọi _flush(), mỗi thao tác đúng một lần.
      Không nạp dữ liệu bằng vòng lặp add() (mỗi add ghi lại cả file).
    """

    filename: ClassVar[str] = ""
    id_prefix: ClassVar[str] = "X"

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir
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
