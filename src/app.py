"""Giao diện Streamlit (View). Người phụ trách: Lâm.

File này CHỈ dựng khung trang và gọi các hàm trong views/.
Không viết luật nghiệp vụ, không đọc ghi file ở đây.
"""
import streamlit as st

from container import build_container
from views.dispatch_tab import render_dispatch_tab
from views.orders_tab import render_orders_tab

st.set_page_config(page_title="Quản lý đơn hàng & gợi ý shipper", layout="wide")

# Streamlit chạy lại toàn bộ script sau mỗi lần bấm nút, nên phải giữ AppContext
# trong session_state, nếu không Stack Undo / Redo bị reset mỗi lần.
if "ctx" not in st.session_state:
    st.session_state.ctx = build_container()
ctx = st.session_state.ctx

st.title("Quản lý đơn hàng & gợi ý shipper")
tab_orders, tab_dispatch = st.tabs(["1. Quản lý đơn hàng", "2. Điều phối đơn"])

with tab_orders:
    render_orders_tab(ctx.orders)

with tab_dispatch:
    render_dispatch_tab(ctx.dispatch)
