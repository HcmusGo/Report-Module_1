"""Tab 1: Quản lý đơn hàng. Người phụ trách: Lâm."""
from __future__ import annotations

import streamlit as st

from controllers.order_controller import OrderController


def render_orders_tab(controller: OrderController) -> None:
    """Bảng đơn hàng (tìm theo từ khóa, lọc theo trạng thái) + form thêm / sửa / xóa đơn.
    Bên dưới: các bảng chỉ xem cho địa điểm, đường (kèm mức đông) và shipper.
    Hiện Result bằng st.success / st.error."""
    st.info("TODO(Lâm): Tab 1 - bảng đơn hàng và form CRUD")
