"""
[M3] Owner: Nguyễn Lê Đức Bảo
File: src/core/menu_manager.py

Nhiệm vụ:
- CRUD đầy đủ cho Menu (menu.json): thêm, sửa, xóa, đọc.
- Dict chính: id -> MenuItem (truy xuất O(1)).
- Tìm món ăn O(log n): name_index (sorted list tuple (name, id)) + Binary Search tự viết.
"""
