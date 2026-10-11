"""Lỗi nghiệp vụ dùng chung. Người phụ trách: Tiên.

Service ném các lỗi này, Controller bắt và đổi thành thông báo cho UI.
"""


class AppError(Exception):
    """Lỗi có thể hiển thị cho người dùng."""


class ValidationError(AppError):
    """Dữ liệu đầu vào không hợp lệ (tên rỗng, giá âm, trọng số âm...)."""


class NotFoundError(AppError):
    """Không tìm thấy đối tượng theo id."""


class BusinessRuleError(AppError):
    """Vi phạm luật nghiệp vụ (hủy đơn đã giao, không có shipper rảnh...)."""
