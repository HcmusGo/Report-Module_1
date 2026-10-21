"""
[CHUNG] Owner: Cả nhóm (đề xuất: Nguyễn Lê Đức Bảo viết trước)
File: src/models/base.py

Nhiệm vụ:
- BaseEntity: lớp cha của mọi entity (GraphNode, MenuItem, Order, ...).
- Thuộc tính private `_id`, `@property id`.
- Phương thức `to_dict()` và `from_dict()` để ghi/đọc JSON.
- Cần chốt sớm vì mọi model đều kế thừa file này.
"""
