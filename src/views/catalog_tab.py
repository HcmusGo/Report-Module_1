"""Tab 1: Quản lý dữ liệu. Người phụ trách: Lâm."""
from __future__ import annotations

import streamlit as st

from controllers.catalog_controller import CatalogController


def render_catalog_tab(controller: CatalogController) -> None:
    """Bảng danh sách + form thêm / sửa / xóa cho menu, khách hàng, shipper, địa điểm, đường
    (chỉnh trọng số, khóa đường). Gọi controller.*, hiển thị Result bằng st.success / st.error."""
    st.info("TODO(Lâm): Tab 1 - bảng và form CRUD")
