"""Tab 2: Điều phối đơn. Người phụ trách: Lâm."""
from __future__ import annotations

import streamlit as st

from controllers.dispatch_controller import DispatchController


def render_dispatch_tab(controller: DispatchController) -> None:
    """Tạo đơn, hàng đợi bếp, nút 'Bếp xong món' / 'Gán shipper', bản đồ tuyến
    shipper -> quán -> khách, ETA, phí ship, nút Undo / Redo (disable khi stack rỗng,
    bấm xong gọi st.rerun())."""
    st.info("TODO(Lâm): Tab 2 - tạo đơn, bếp, gán shipper, Undo / Redo")
