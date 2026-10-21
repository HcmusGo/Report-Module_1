"""
File: src/app.py  -  Giao diện Streamlit

[CHUNG] Mỗi người chỉ viết hàm render của tab mình, đánh dấu bằng comment.
Tuyệt đối KHÔNG viết logic thuật toán hay đọc/ghi file ở đây; chỉ gọi sang src.core.
"""

import streamlit as st


# ===== [M2] Đào Đoàn Đỗ Quyên - TAB BẢN ĐỒ / LỘ TRÌNH SHIPPER =====
def render_map_tab() -> None:
    st.info("TODO [M2]: vẽ lộ trình Shipper lên bản đồ (dữ liệu từ routing_service).")


# ===== [M3] Nguyễn Lê Đức Bảo - TAB MENU =====
def render_menu_tab() -> None:
    st.info("TODO [M3]: thêm / sửa / xóa / tìm kiếm món ăn.")


# ===== [M4] Nguyễn Vũ Băng Tâm - TAB HÀNG ĐỢI CHẾ BIẾN =====
def render_kitchen_tab() -> None:
    st.info("TODO [M4]: hiển thị thứ tự chế biến theo độ ưu tiên.")


# ===== [M5] Thân Văn Thế Lâm - TAB ĐƠN HÀNG & UNDO/REDO =====
def render_order_tab() -> None:
    st.info("TODO [M5]: quản lý đơn hàng, chuyển trạng thái, Undo/Redo, tìm theo Tên/Email.")


def main() -> None:
    st.set_page_config(page_title="Quản lý Đơn hàng & Shipper", layout="wide")
    st.title("Hệ thống Quản lý Đơn hàng, Ưu tiên Chế biến & Tìm đường Shipper")

    tab_map, tab_menu, tab_kitchen, tab_order = st.tabs(
        ["Bản đồ / Lộ trình", "Menu", "Hàng đợi chế biến", "Đơn hàng"]
    )
    with tab_map:
        render_map_tab()
    with tab_menu:
        render_menu_tab()
    with tab_kitchen:
        render_kitchen_tab()
    with tab_order:
        render_order_tab()


if __name__ == "__main__":
    main()
