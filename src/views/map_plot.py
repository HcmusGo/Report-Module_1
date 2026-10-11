"""Vẽ bản đồ bằng Plotly. Người phụ trách: Lâm."""
from __future__ import annotations


def build_map_figure(data: dict):
    """Nhận dict từ DispatchController.map_figure_data(), trả plotly.graph_objects.Figure:
    nút là điểm, đường là line (đường khóa vẽ nét đứt / màu đỏ), tuyến đang chọn tô đậm.
    (st.map không vẽ được đường nối nên dùng Plotly.)"""
    raise NotImplementedError("TODO(Lâm)")
