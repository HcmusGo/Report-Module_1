"""
[M4] Chủ file: Nguyễn Vũ Băng Tâm
File: src/core/structures.py

File dùng chung. Mỗi người chỉ thêm/sửa class của mình, KHÔNG sửa class người khác.
Chỉ dùng list, dict, set, tuple (cấm heapq, deque, bisect, queue).
"""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


# ===== [M4] Nguyễn Vũ Băng Tâm =====
class CustomMinHeap(Generic[T]):
    """Cấu trúc dữ liệu Min-Heap tự định nghĩa sử dụng danh sách (List).

    Phần tử nhỏ nhất luôn nằm ở gốc (chỉ số 0).
    Hỗ trợ so sánh trực tiếp các giá trị hoặc so sánh theo key_func.
    """

    def __init__(self, key_func: Callable[[T], Any] | None = None) -> None:
        self._heap: list[T] = []
        self._key_func: Callable[[T], Any] = key_func if key_func is not None else lambda x: x

    def _get_key(self, item: T) -> Any:
        return self._key_func(item)

    def _sift_up(self, index: int) -> None:
        """Đẩy phần tử lên trên đảm bảo tính chất Min-Heap. Độ phức tạp: O(log n)."""
        parent = (index - 1) // 2
        while index > 0 and self._get_key(self._heap[index]) < self._get_key(self._heap[parent]):
            self._heap[index], self._heap[parent] = self._heap[parent], self._heap[index]
            index = parent
            parent = (index - 1) // 2

    def _sift_down(self, index: int) -> None:
        """Hạ phần tử xuống dưới đảm bảo tính chất Min-Heap. Độ phức tạp: O(log n)."""
        size = len(self._heap)
        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if (
                left < size
                and self._get_key(self._heap[left]) < self._get_key(self._heap[smallest])
            ):
                smallest = left
            if (
                right < size
                and self._get_key(self._heap[right]) < self._get_key(self._heap[smallest])
            ):
                smallest = right

            if smallest != index:
                self._heap[index], self._heap[smallest] = self._heap[smallest], self._heap[index]
                index = smallest
            else:
                break

    def push(self, item: T) -> None:
        """Thêm một phần tử vào Min-Heap.

        # Độ phức tạp: O(log n).
        """
        self._heap.append(item)
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> T:
        """Lấy và xóa phần tử nhỏ nhất khỏi Min-Heap.

        # Độ phức tạp: O(log n).
        """
        if self.is_empty():
            raise IndexError("pop from an empty heap")
        root = self._heap[0]
        last_item = self._heap.pop()
        if not self.is_empty():
            self._heap[0] = last_item
            self._sift_down(0)
        return root

    def peek(self) -> T | None:
        """Xem phần tử nhỏ nhất mà không xóa.

        # Độ phức tạp: O(1).
        """
        return self._heap[0] if not self.is_empty() else None

    def is_empty(self) -> bool:
        """Kiểm tra heap có rỗng hay không. Độ phức tạp: O(1)."""
        return len(self._heap) == 0

    def __len__(self) -> int:
        """Số lượng phần tử trong heap. Độ phức tạp: O(1)."""
        return len(self._heap)

    def __repr__(self) -> str:
        return f"<CustomMinHeap size={len(self._heap)}>"


class CustomPriorityQueue(Generic[T]):
    """Hàng đợi ưu tiên (Priority Queue) xây dựng dựa trên CustomMinHeap.

    Các phần tử được đưa vào kèm độ ưu tiên (priority_key). Độ ưu tiên nhỏ hơn = ưu tiên cao hơn.
    """

    def __init__(self) -> None:
        # Lưu trữ tuple: (priority_key, counter, item)
        self._counter: int = 0
        self._heap: CustomMinHeap[tuple[Any, int, T]] = CustomMinHeap(
            key_func=lambda x: (x[0], x[1])
        )

    def enqueue(self, item: T, priority_key: Any) -> None:
        """Thêm phần tử vào hàng đợi với độ ưu tiên xác định.

        # Độ phức tạp: O(log n).
        """
        self._heap.push((priority_key, self._counter, item))
        self._counter += 1

    def dequeue(self) -> T:
        """Lấy ra phần tử có độ ưu tiên cao nhất.

        # Độ phức tạp: O(log n).
        """
        if self.is_empty():
            raise IndexError("dequeue from an empty priority queue")
        priority_key, count, item = self._heap.pop()
        return item

    def peek(self) -> T | None:
        """Xem phần tử có độ ưu tiên cao nhất.

        # Độ phức tạp: O(1).
        """
        if self.is_empty():
            return None
        top_entry = self._heap.peek()
        return top_entry[2] if top_entry is not None else None

    def is_empty(self) -> bool:
        """Kiểm tra hàng đợi có rỗng hay không. Độ phức tạp: O(1)."""
        return self._heap.is_empty()

    def to_list(self) -> list[T]:
        """Trả về danh sách các phần tử theo thứ tự ưu tiên mà không làm biến đổi hàng đợi.

        # Độ phức tạp: O(n log n).
        """
        items_sorted = sorted(self._heap._heap, key=lambda x: (x[0], x[1]))
        return [item[2] for item in items_sorted]

    def __len__(self) -> int:
        """Số lượng phần tử trong hàng đợi. Độ phức tạp: O(1)."""
        return len(self._heap)

    def __repr__(self) -> str:
        return f"<CustomPriorityQueue size={len(self._heap)}>"


# ===== [M3] Nguyễn Lê Đức Bảo =====
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
        """Tìm vị trí lower bound đầu tiên có entry[0] >= norm_key trong O(log n)."""
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

        # Độ phức tạp: tìm vị trí O(log n) bằng Binary Search; chèn list.insert O(n).
        """
        norm_key = self._normalize(key)
        entry = (norm_key, str(item_id))
        idx = self._bisect_left_pair(entry)
        if idx < len(self._data) and self._data[idx] == entry:
            return
        self._data.insert(idx, entry)

    def remove(self, key: str, item_id: str) -> bool:
        """Xóa cặp (key, item_id) khỏi chỉ mục nếu tồn tại.

        # Độ phức tạp: tìm vị trí O(log n) bằng Binary Search; xóa list.pop O(n).
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

        # Độ phức tạp: tìm kiếm O(log n) bằng Binary Search (+ O(k) với k kết quả khớp).
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
class CustomStack:
    """Cấu trúc dữ liệu Ngăn xếp LIFO tự viết từ list, các thao tác đều đạt O(1)."""

    def __init__(self) -> None:
        self._data: list[dict[str, Any]] = []

    def push(self, item: dict[str, Any]) -> None:
        """Đẩy phần tử vào đỉnh ngăn xếp. Độ phức tạp: O(1)."""
        self._data.append(item)

    def pop(self) -> dict[str, Any]:
        """Lấy phần tử trên cùng ra khỏi ngăn xếp. Độ phức tạp: O(1)."""
        if self.is_empty():
            raise IndexError("Stack rỗng")
        return self._data.pop()

    def peek(self) -> dict[str, Any] | None:
        """Xem phần tử trên cùng mà không xóa. Độ phức tạp: O(1)."""
        if self.is_empty():
            return None
        return self._data[-1]

    def is_empty(self) -> bool:
        """Kiểm tra ngăn xếp có rỗng không. Độ phức tạp: O(1)."""
        return len(self._data) == 0

    def __len__(self) -> int:
        """Số lượng phần tử trong ngăn xếp. Độ phức tạp: O(1)."""
        return len(self._data)

    def clear(self) -> None:
        """Xóa toàn bộ phần tử trong ngăn xếp. Độ phức tạp: O(1)."""
        self._data.clear()
