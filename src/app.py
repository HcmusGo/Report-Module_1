"""Giao diện Streamlit (View). Người phụ trách: Lâm.

File này CHỈ dựng khung trang và gọi các hàm trong views/.
Không viết luật nghiệp vụ, không đọc ghi file ở đây.
"""
import streamlit as st

from container import build_container
from views.catalog_tab import render_catalog_tab
from views.dispatch_tab import render_dispatch_tab

st.set_page_config(page_title="Quản lý đơn hàng & điều phối shipper", layout="wide")

# Streamlit chạy lại toàn bộ script sau mỗi lần bấm nút, nên phải giữ AppContext
# trong session_state, nếu không Stack Undo / Redo bị reset mỗi lần.
if "ctx" not in st.session_state:
    st.session_state.ctx = build_container()
ctx = st.session_state.ctx

st.title("Quản lý đơn hàng & điều phối shipper")
tab_catalog, tab_dispatch = st.tabs(["1. Quản lý dữ liệu", "2. Điều phối đơn"])

with tab_catalog:
    render_catalog_tab(ctx.catalog)

with tab_dispatch:
    render_dispatch_tab(ctx.dispatch)
