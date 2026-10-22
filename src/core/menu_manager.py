"""
[M3] Owner: Nguyễn Lê Đức Bảo
File: src/core/menu_manager.py

Nhiệm vụ:
- CRUD đầy đủ cho Menu (menu.json): thêm, sửa, xóa, đọc.
- Dict chính: id -> MenuItem (truy xuất O(1)).
- Tìm món ăn O(log n): name_index (sorted list tuple (name, id)) + Binary Search tự viết.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from core.storage import load_json, save_json
    from core.structures import SortedIndex
    from models.menu_item import MenuItem
except ModuleNotFoundError:
    from src.core.storage import load_json, save_json
    from src.core.structures import SortedIndex
    from src.models.menu_item import MenuItem


class MenuManager:
    """Lớp quản lý thực đơn (Menu) với đầy đủ chức năng CRUD và chỉ mục tìm kiếm O(log n)."""

    def __init__(self, file_path: str | Path = "data/menu.json") -> None:
        """Khởi tạo MenuManager, tải dữ liệu từ file và thiết lập chỉ mục tìm kiếm."""
        self.file_path: Path | str = file_path
        self._items: dict[str, MenuItem] = {}
        self.name_index: SortedIndex = SortedIndex()
        self.load()

    def _init_default_items(self) -> None:
        """Khởi tạo danh sách món ăn mặc định ban đầu nếu file dữ liệu chưa có."""
        default_items = [
            MenuItem(
                id="M001",
                name="Cơm tấm sườn bì chả",
                price=45000,
                prep_time=15,
                category="Món chính",
                available=True,
            ),
            MenuItem(
                id="M002",
                name="Phở bò tái lăn",
                price=50000,
                prep_time=12,
                category="Món chính",
                available=True,
            ),
            MenuItem(
                id="M003",
                name="Bún chả Hà Nội",
                price=45000,
                prep_time=15,
                category="Món chính",
                available=True,
            ),
            MenuItem(
                id="M004",
                name="Bánh mì thịt nướng",
                price=30000,
                prep_time=8,
                category="Ăn vặt",
                available=True,
            ),
            MenuItem(
                id="M005",
                name="Cà phê sữa đá",
                price=25000,
                prep_time=5,
                category="Đồ uống",
                available=True,
            ),
            MenuItem(
                id="M006",
                name="Trà đào cam sả",
                price=30000,
                prep_time=7,
                category="Đồ uống",
                available=True,
            ),
        ]
        for item in default_items:
            self._items[item.id] = item
            # Độ phức tạp: O(log n) tìm vị trí + O(n) chèn list
            self.name_index.insert(item.name, item.id)

    def load(self) -> None:
        """Nạp danh sách món ăn từ file JSON vào _items và name_index.

        Nếu file chưa tồn tại hoặc rỗng, tự động khởi tạo danh sách mặc định và lưu file.
        # Độ phức tạp: O(n log n) với n là số món ăn được nạp và chèn vào SortedIndex.
        """
        self._items.clear()
        self.name_index.clear()

        raw_data = load_json(self.file_path, default=None)
        if not raw_data:
            # File chưa tồn tại hoặc rỗng: tạo dữ liệu mẫu và lưu ngay
            self._init_default_items()
            self.save()
            return

        for entry in raw_data:
            if isinstance(entry, dict):
                item = MenuItem.from_dict(entry)
                self._items[item.id] = item
                # Độ phức tạp: O(log n) tìm vị trí + O(n) chèn list
                self.name_index.insert(item.name, item.id)

    def save(self) -> None:
        """Lưu toàn bộ danh sách món ăn từ _items xuống file JSON.

        # Độ phức tạp: O(n) theo kích thước dữ liệu JSON cần ghi.
        """
        data = [item.to_dict() for item in self._items.values()]
        save_json(self.file_path, data)

    def get_all(self) -> list[MenuItem]:
        """Lấy danh sách tất cả món ăn trong menu.

        # Độ phức tạp: O(n) với n là số món ăn trong menu.
        """
        return list(self._items.values())

    def get_by_id(self, item_id: str) -> MenuItem | None:
        """Tra cứu thông tin món ăn theo mã ID trong dict chính.

        # Độ phức tạp: O(1) tra cứu trực tiếp trên dictionary.
        """
        return self._items.get(item_id)

    def next_id(self) -> str:
        """Tự động sinh mã món mới không trùng lặp (ví dụ M001, M002, ...).

        # Độ phức tạp: O(n) duyệt qua danh sách mã hiện có để tìm số lớn nhất.
        """
        max_num = 0
        for item_id in self._items:
            if item_id.startswith("M") and item_id[1:].isdigit():
                num = int(item_id[1:])
                if num > max_num:
                    max_num = num

        candidate_num = max_num + 1
        new_id = f"M{candidate_num:03d}"
        while new_id in self._items:
            candidate_num += 1
            new_id = f"M{candidate_num:03d}"
        return new_id

    def add_item(
        self,
        name: str,
        price: float | int,
        prep_time: int | float,
        item_id: str | None = None,
        category: str = "Món chính",
        available: bool = True,
    ) -> MenuItem:
        """Thêm món ăn mới vào menu, cập nhật chỉ mục tên và lưu xuống file JSON.

        # Độ phức tạp: O(1) kiểm tra/thêm dict + O(n) chèn SortedIndex + O(n) ghi file JSON.
        """
        if item_id is None or not str(item_id).strip():
            assigned_id = self.next_id()
        else:
            assigned_id = str(item_id).strip()

        if assigned_id in self._items:
            raise ValueError(f"Mã món ăn '{assigned_id}' đã tồn tại.")

        item = MenuItem(
            id=assigned_id,
            name=name,
            price=price,
            prep_time=prep_time,
            category=category,
            available=available,
        )

        self._items[item.id] = item
        # Độ phức tạp: O(log n) tìm vị trí + O(n) chèn list
        self.name_index.insert(item.name, item.id)
        self.save()
        return item

    def update_item(
        self,
        item_id: str,
        name: str | None = None,
        price: float | int | None = None,
        prep_time: int | float | None = None,
        category: str | None = None,
        available: bool | None = None,
    ) -> MenuItem:
        """Cập nhật thông tin món ăn. Nếu đổi tên, cập nhật lại SortedIndex.

        # Độ phức tạp: O(1) tra cứu dict + O(n) cập nhật SortedIndex nếu đổi tên + O(n) ghi file JSON.
        """
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Món ăn với ID '{item_id}' không tồn tại.")

        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                raise ValueError("Tên món ăn không được rỗng.")
            old_name = item.name
            if clean_name != old_name:
                # Gỡ khóa cũ khỏi chỉ mục và chèn khóa mới
                self.name_index.remove(old_name, item.id)
                item.name = clean_name
                # Độ phức tạp: O(log n) tìm vị trí + O(n) chèn list
                self.name_index.insert(item.name, item.id)

        if price is not None:
            item.price = price

        if prep_time is not None:
            item.prep_time = prep_time

        if category is not None:
            item.category = category

        if available is not None:
            item.available = available

        self.save()
        return item

    def delete_item(self, item_id: str) -> bool:
        """Xóa món ăn khỏi menu, đồng thời gỡ khỏi chỉ mục SortedIndex và lưu file.

        # Độ phức tạp: O(1) xóa dict + O(n) xóa SortedIndex + O(n) ghi file JSON.
        """
        item = self._items.pop(item_id, None)
        if item is None:
            return False

        self.name_index.remove(item.name, item.id)
        self.save()
        return True

    def search_by_name(self, name: str) -> list[MenuItem]:
        """Tìm kiếm món ăn theo tên bằng Binary Search trên SortedIndex.

        # Độ phức tạp: O(log n) tìm trên SortedIndex bằng Binary Search + O(1) tra dict cho mỗi kết quả
        """
        # Độ phức tạp: O(log n) tìm trên SortedIndex bằng Binary Search + O(1) tra dict cho mỗi kết quả
        matched_ids = self.name_index.find_all(name)
        results: list[MenuItem] = []
        for item_id in matched_ids:
            item = self._items.get(item_id)
            if item is not None:
                results.append(item)
        return results
