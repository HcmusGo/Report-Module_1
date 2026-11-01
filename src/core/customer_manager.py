"""
[M2] Owner: Thân Văn Thế Lâm
File: src/core/customer_manager.py

Nhiệm vụ:
- CustomerManager: quản lý danh sách khách hàng chỉ đọc (read-only).
- Nạp dữ liệu an toàn từ JSON, ghi nhận lỗi từng bản ghi vào load_errors thay vì crash.
- Tìm kiếm khách hàng theo tên và email đạt O(log n) bằng SortedIndex và Binary Search.
"""

from __future__ import annotations

from pathlib import Path

from src.core.storage import load_json
from src.core.structures import SortedIndex
from src.models.customer import Customer


class CustomerManager:
    """Lớp quản lý khách hàng chỉ đọc với chỉ mục tìm kiếm O(log n)."""

    def __init__(self, storage_path: str | Path = "data/users.json") -> None:
        """Khởi tạo CustomerManager và nạp dữ liệu khách hàng từ file JSON."""
        self.storage_path: Path | str = storage_path
        self._customers: dict[str, Customer] = {}
        self._name_index: SortedIndex = SortedIndex()
        self._email_index: SortedIndex = SortedIndex()
        self._load_errors: list[str] = []

        self.load_customers()

    @property
    def load_errors(self) -> list[str]:
        """Danh sách thông báo lỗi phát sinh khi nạp dữ liệu khách hàng."""
        return self._load_errors

    def load_customers(self) -> None:
        """Đọc danh sách khách hàng từ file JSON và cập nhật các chỉ mục tìm kiếm.

        # Độ phức tạp: O(n log n) với n khách hàng nạp vào và chèn vào 2 SortedIndex.
        """
        self._customers.clear()
        self._name_index.clear()
        self._email_index.clear()
        self._load_errors.clear()

        try:
            data = load_json(self.storage_path, default=[])
        except Exception as err:
            self._load_errors.append(f"Không thể đọc file dữ liệu khách hàng: {err}")
            return

        if not isinstance(data, (list, dict)):
            self._load_errors.append(
                "Dữ liệu khách hàng không hợp lệ (phải là danh sách hoặc từ điển)."
            )
            return

        records = data.values() if isinstance(data, dict) else data
        for item in records:
            if not isinstance(item, dict):
                self._load_errors.append(
                    f"Bản ghi khách hàng không phải từ điển: {item}"
                )
                continue
            try:
                customer = Customer.from_dict(item)
                self._customers[customer.id] = customer
                self._name_index.insert(customer.name, customer.id)
                self._email_index.insert(customer.email, customer.id)
            except (ValueError, KeyError, TypeError) as err:
                self._load_errors.append(f"Bản ghi khách hàng lỗi: {err}")

    def get_all(self) -> list[Customer]:
        """Lấy toàn bộ danh sách khách hàng.

        # Độ phức tạp: O(n).
        """
        return list(self._customers.values())

    def get_by_id(self, customer_id: str) -> Customer | None:
        """Tìm khách hàng theo mã ID.

        # Độ phức tạp: O(1) tra cứu từ điển.
        """
        if not isinstance(customer_id, str):
            return None
        return self._customers.get(customer_id.strip())

    def find_by_name(self, name: str) -> list[Customer]:
        """Tìm kiếm khách hàng theo tên (không phân biệt hoa thường).

        # Độ phức tạp: O(log n) tìm kiếm Binary Search + O(k) với k kết quả khớp.
        """
        matched_ids = self._name_index.find_all(name)
        return [self._customers[cid] for cid in matched_ids if cid in self._customers]

    def find_by_email(self, email: str) -> list[Customer]:
        """Tìm kiếm khách hàng theo email (không phân biệt hoa thường).

        # Độ phức tạp: O(log n) tìm kiếm Binary Search + O(k) với k kết quả khớp.
        """
        matched_ids = self._email_index.find_all(email)
        return [self._customers[cid] for cid in matched_ids if cid in self._customers]

    def __repr__(self) -> str:
        return (
            f"CustomerManager(customers={len(self._customers)}, "
            f"errors={len(self._load_errors)})"
        )
