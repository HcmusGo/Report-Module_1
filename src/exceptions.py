"""Lỗi nghiệp vụ dùng chung. Người phụ trách: Tiên.

Service ném các lỗi này, Controller bắt và đổi thành thông báo cho UI.
"""


class AppError(Exception):
    """Lỗi có thể hiển thị cho người dùng."""


class ValidationError(AppError):
    """Dữ liệu đầu vào không hợp lệ (tên rỗng, khối lượng <= 0...)."""


class NotFoundError(AppError):
    """Không tìm thấy đối tượng theo id."""


class BusinessRuleError(AppError):
    """Vi phạm luật nghiệp vụ (sửa đơn đã gán, shipper vượt tải, không có đường...)."""
