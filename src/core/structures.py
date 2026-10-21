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

# ===== [M5] Thân Văn Thế Lâm =====
# TODO: CustomStack (LIFO tự viết) - dùng cho Undo/Redo trong order_manager.py
#       push(item) / pop() / peek() / is_empty() / __len__()
