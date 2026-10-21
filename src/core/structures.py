"""
[M4] Chủ file: Nguyễn Vũ Băng Tâm
File: src/core/structures.py

File dùng chung. Mỗi người chỉ thêm/sửa class của mình, KHÔNG sửa class người khác.
Chỉ dùng list, dict, set, tuple (cấm heapq, deque, bisect, queue).
"""

# ===== [M4] Nguyễn Vũ Băng Tâm =====
# TODO: CustomMinHeap (Min-Heap tự viết từ list) - Module 1 (Dijkstra/A*) đang chờ class này.
#       push(priority, item) / pop() / peek() / is_empty() / __len__()
# TODO: CustomPriorityQueue (dựa trên Min-Heap) - dùng trong priority_engine.py

# ===== [M3] Nguyễn Lê Đức Bảo =====
# TODO: SortedIndex - sorted list tuple (search_key, id) + Binary Search tự viết.
#       insert(key, id) / remove(key, id) / find_all(key) -> list[id]  (tìm O(log n))
#       Dùng chung với Module 5 (tìm đơn theo Tên/Email).
class SortedIndex:
    """Chỉ mục sắp xếp các cặp (search_key_chuẩn_hóa, item_id) sử dụng Binary Search tự viết."""

    def __init__(self) -> None:
        self._data: list[tuple[str, str]] = []

    @staticmethod
    def _normalize(key: str) -> str:
        """Chuẩn hóa khóa tìm kiếm: đưa chuỗi về dạng chữ thường và loại bỏ khoảng trắng hai đầu."""
        return str(key).strip().lower()

    def _bisect_left_pair(self, target: tuple[str, str]) -> int:
        """Tìm vị trí đầu tiên có phần tử >= target trong O(log n) bằng Binary Search."""
        low = 0
        high = len(self._data)
        while low < high:
            mid = (low + high) // 2
            if self._data[mid] < target:
                low = mid + 1
            else:
                high = mid
        return low

    def _bisect_left_key(self, norm_key: str) -> int:
        """Tìm vị trí lower bound đầu tiên có entry[0] >= norm_key trong O(log n) bằng Binary Search."""
        low = 0
        high = len(self._data)
        while low < high:
            mid = (low + high) // 2
            if self._data[mid][0] < norm_key:
                low = mid + 1
            else:
                high = mid
        return low

    def insert(self, key: str, item_id: str) -> None:
        """Chèn cặp (key, item_id) vào chỉ mục đảm bảo thứ tự tăng dần.

        # Độ phức tạp: tìm vị trí O(log n) bằng Binary Search; chèn list.insert O(n) do dịch phần tử
        """
        norm_key = self._normalize(key)
        entry = (norm_key, str(item_id))
        idx = self._bisect_left_pair(entry)
        # Nếu cặp (norm_key, item_id) chưa tồn tại tại vị trí đó thì chèn vào
        if idx < len(self._data) and self._data[idx] == entry:
            return
        self._data.insert(idx, entry)

    def remove(self, key: str, item_id: str) -> bool:
        """Xóa cặp (key, item_id) khỏi chỉ mục nếu tồn tại.

        # Độ phức tạp: tìm vị trí O(log n) bằng Binary Search; xóa list.pop O(n) do dịch phần tử
        """
        norm_key = self._normalize(key)
        entry = (norm_key, str(item_id))
        idx = self._bisect_left_pair(entry)
        if idx < len(self._data) and self._data[idx] == entry:
            self._data.pop(idx)
            return True
        return False

    def find_all(self, key: str) -> list[str]:
        """Tìm tất cả các item_id có khóa trùng khớp hoàn toàn với key (sau chuẩn hóa).

        # Độ phức tạp: tìm kiếm O(log n) bằng Binary Search (+ O(k) với k là số kết quả khớp)
        """
        norm_key = self._normalize(key)
        idx = self._bisect_left_key(norm_key)
        results: list[str] = []
        n = len(self._data)
        while idx < n and self._data[idx][0] == norm_key:
            results.append(self._data[idx][1])
            idx += 1
        return results

    def clear(self) -> None:
        """Xóa toàn bộ phần tử trong chỉ mục. Độ phức tạp: O(1)."""
        self._data.clear()

    def is_empty(self) -> bool:
        """Kiểm tra chỉ mục có đang rỗng không. Độ phức tạp: O(1)."""
        return len(self._data) == 0

    def __len__(self) -> int:
        """Trả về số lượng phần tử trong chỉ mục. Độ phức tạp: O(1)."""
        return len(self._data)

    def __repr__(self) -> str:
        return f"SortedIndex(len={len(self._data)})"

# ===== [M5] Thân Văn Thế Lâm =====
# TODO: CustomStack (LIFO tự viết) - dùng cho Undo/Redo trong order_manager.py
#       push(item) / pop() / peek() / is_empty() / __len__()
