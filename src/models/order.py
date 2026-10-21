"""
[M5] Owner: Thân Văn Thế Lâm
File: src/models/order.py

Nhiệm vụ:
- Order(BaseEntity): đơn hàng (id, khách hàng, danh sách món, trạng thái, ...).
- Trạng thái: PLACED -> CONFIRMED -> PREPARING -> READY -> DELIVERING -> PAID | CANCELLED.
- Bảng chuyển trạng thái hợp lệ (state machine).
"""
