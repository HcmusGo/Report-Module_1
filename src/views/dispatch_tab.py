"""Tab 2: Điều phối đơn. Người phụ trách: Lâm."""
from __future__ import annotations

import streamlit as st

from controllers.dispatch_controller import DispatchController


def render_dispatch_tab(controller: DispatchController) -> None:
    """Hàng đợi đơn chờ, nút 'Đề xuất shipper' (bảng mọi shipper: phù hợp hay không, lý do,
    ETA), nút 'Xác nhận gán', lộ trình từng shipper và nút 'Hoàn thành điểm dừng tiếp theo',
    bản đồ Plotly (đường tô màu theo mức đông, tuyến được chọn tô đậm), bảng so sánh
    'ngắn nhất theo km' với 'nhanh nhất theo phút', nút Undo / Redo (disable khi Stack
    rỗng, bấm xong gọi st.rerun()). Hàm vẽ bản đồ Plotly đặt trong file này."""
    st.info("TODO(Lâm): Tab 2 - hàng đợi, đề xuất shipper, bản đồ, Undo / Redo")
