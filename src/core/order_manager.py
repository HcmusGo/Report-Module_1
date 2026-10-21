"""
[M5] Owner: Thân Văn Thế Lâm
File: src/core/order_manager.py

Nhiệm vụ:
- Quản lý vòng đời đơn hàng, kiểm tra các trường hợp biên (không hủy đơn PAID/DELIVERING; chỉ nhận đơn mới khi Shipper rảnh hoặc gom chuyến hợp lệ).
- Undo/Redo chuyển trạng thái bằng CustomStack (LIFO) tự viết.
- Tìm đơn theo Tên người dùng O(log n) và theo Email O(log n): name_index, email_index + Binary Search.
"""
