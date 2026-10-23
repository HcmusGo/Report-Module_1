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
    try:
        from core.menu_manager import MenuManager
    except ModuleNotFoundError:
        from src.core.menu_manager import MenuManager

    if "menu_manager" not in st.session_state:
        st.session_state.menu_manager = MenuManager()
    manager: MenuManager = st.session_state.menu_manager

    st.subheader("📋 Quản lý Thực đơn (Menu)")

    # Khu vực 1 - Tìm kiếm món ăn O(log n) và Bảng danh sách Menu
    st.markdown("#### 1. Tra cứu & Danh sách món ăn")
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input(
            "🔍 Tìm kiếm món ăn theo tên (Binary Search - O(log n)):",
            placeholder="Nhập tên món ăn chính xác (VD: Phở bò tái lăn)...",
            key="menu_search_input",
        )
    with search_col2:
        st.write("")
        st.write("")
        if st.button("Làm mới danh sách", use_container_width=True):
            manager.load()
            st.rerun()

    query = search_query.strip()
    if query:
        display_items = manager.search_by_name(query)
        st.caption(
            f"⚡ Kết quả tìm kiếm O(log n) cho từ khóa **'{query}'**: {len(display_items)} món tìm thấy."
        )
    else:
        display_items = manager.get_all()

    if display_items:
        table_rows = [
            {
                "Mã món": item.id,
                "Tên món": item.name,
                "Giá (VNĐ)": f"{item.price:,.0f} đ",
                "Thời gian chế biến": f"{item.prep_time} phút",
                "Danh mục": item.category,
                "Trạng thái": "🟢 Đang phục vụ" if item.available else "🔴 Tạm hết",
            }
            for item in display_items
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
    else:
        st.warning("Không tìm thấy món ăn nào phù hợp.")

    st.divider()

    # Hai cột cho Khu vực 2 và Khu vực 3
    col_add, col_edit = st.columns(2)

    # Khu vực 2 - Thêm món ăn mới
    with col_add:
        st.markdown("#### 2. Thêm món ăn mới")
        with st.form("add_item_form", clear_on_submit=True):
            new_name = st.text_input("Tên món ăn *", placeholder="VD: Gà rán giòn cay")
            c_price, c_time = st.columns(2)
            with c_price:
                new_price = st.number_input(
                    "Giá (VNĐ) *", min_value=0, step=5000, value=35000
                )
            with c_time:
                new_prep_time = st.number_input(
                    "Thời gian chế biến (phút) *", min_value=1, step=1, value=10
                )
            new_category = st.selectbox(
                "Danh mục", ["Món chính", "Món phụ", "Ăn vặt", "Đồ uống", "Tráng miệng"]
            )
            new_available = st.checkbox("Đang phục vụ", value=True)
            submitted_add = st.form_submit_button("➕ Thêm món ăn", use_container_width=True)

            if submitted_add:
                try:
                    added_item = manager.add_item(
                        name=new_name,
                        price=new_price,
                        prep_time=new_prep_time,
                        category=new_category,
                        available=new_available,
                    )
                    st.success(
                        f"Đã thêm món '{added_item.name}' (Mã: {added_item.id}) thành công!"
                    )
                    st.rerun()
                except ValueError as err:
                    st.error(f"Lỗi: {err}")

    # Khu vực 3 - Sửa / Xóa món ăn
    with col_edit:
        st.markdown("#### 3. Sửa / Xóa món ăn")
        all_items = manager.get_all()
        if not all_items:
            st.info("Hiện chưa có món ăn nào trong thực đơn.")
        else:
            selected_item = st.selectbox(
                "Chọn món ăn cần chỉnh sửa hoặc xóa:",
                options=all_items,
                format_func=lambda it: f"[{it.id}] {it.name} - {it.price:,.0f} đ ({it.prep_time}p)",
                key="menu_item_selector",
            )

            if selected_item:
                with st.form("edit_item_form"):
                    edit_name = st.text_input("Tên món ăn", value=selected_item.name)
                    c_eprice, c_etime = st.columns(2)
                    with c_eprice:
                        edit_price = st.number_input(
                            "Giá (VNĐ)",
                            min_value=0,
                            step=5000,
                            value=int(selected_item.price),
                        )
                    with c_etime:
                        edit_prep_time = st.number_input(
                            "Thời gian chế biến (phút)",
                            min_value=1,
                            step=1,
                            value=int(selected_item.prep_time),
                        )
                    categories = [
                        "Món chính",
                        "Món phụ",
                        "Ăn vặt",
                        "Đồ uống",
                        "Tráng miệng",
                    ]
                    cat_index = (
                        categories.index(selected_item.category)
                        if selected_item.category in categories
                        else 0
                    )
                    edit_category = st.selectbox(
                        "Danh mục", categories, index=cat_index
                    )
                    edit_available = st.checkbox(
                        "Đang phục vụ", value=selected_item.available
                    )
                    submitted_edit = st.form_submit_button(
                        "💾 Cập nhật món ăn", use_container_width=True
                    )

                    if submitted_edit:
                        try:
                            updated_item = manager.update_item(
                                item_id=selected_item.id,
                                name=edit_name,
                                price=edit_price,
                                prep_time=edit_prep_time,
                                category=edit_category,
                                available=edit_available,
                            )
                            st.success(
                                f"Đã cập nhật món '{updated_item.name}' (Mã: {updated_item.id}) thành công!"
                            )
                            st.rerun()
                        except (ValueError, KeyError) as err:
                            st.error(f"Lỗi: {err}")

                col_dtext, col_dbtn = st.columns([2, 1])
                with col_dtext:
                    st.caption(
                        f"Hành động xóa món **[{selected_item.id}] {selected_item.name}**:"
                    )
                with col_dbtn:
                    if st.button("🗑️ Xóa món", use_container_width=True):
                        if manager.delete_item(selected_item.id):
                            st.success(f"Đã xóa món [{selected_item.id}] thành công!")
                            st.rerun()
                        else:
                            st.error("Không tìm thấy món ăn để xóa.")


# ===== [M4] Nguyễn Vũ Băng Tâm - TAB HÀNG ĐỢI CHẾ BIẾN =====
def render_kitchen_tab() -> None:
    st.info("TODO [M4]: hiển thị thứ tự chế biến theo độ ưu tiên.")


# ===== [M5] Thân Văn Thế Lâm - TAB ĐƠN HÀNG & UNDO/REDO =====
def render_order_tab() -> None:
    st.subheader ("Quản lý đơn hàng & Lịch sử trạng thái")

#1: Bộ lọc & Tìm kiếm đơn hàng tối ưu O(log n)
col_search_type, col_search_value = st.columns (2)
    with col_search_type:
        search_type = st.selectbox ("Tìm kiếm theo:", ["Tất cả", "Tên khách hàng", "Email"])
    with col_search_value:
        search_query = st.text_input ("Nhập từ khóa tìm kiếm", value=)
# Tiến hành lọc dữ liệu dựa trên kết quả thuật toán Tìm kiếm nhị phân
if search_query.strip() == "":
    display_orders = list(om.orders.values())
else:
    if search_type == "Tên khách hàng":
        display_orders = om.find_by_name(search_query.strip())
    elif search_type == "Email":
        display_orders = om.find_by_email(search_query.strip())
    else:
        display_orders = list (om.orders.values())

#2: Thanh công cụ điều khiển Hệ thống Undo/Redo
col_undo, col_redo = st.columns ([1,1,4])
with col_undo:
    undo.disabled = om.undo.stack.is_empty ()
    if st.button ("Undo", disabled=undo.disabled, use_container_width = True):
        if om.undo ():
            st.success ("Đã hoàn tất trạng thái")
            st.rerun ()
with col_redo:
    redo.disabled = om.redo.stack.is_empty ()
    if st.button ("Redo", disabled=redo.disabled, use_container_width = True):
        if om.redo ():
            st.success ("Đã làm lại trạng thái thành công")
            st.rerun ()

st.write ("---")

# 3. Danh sách hiển thị và Chuyển trạng thái trực tiếp (Biên kiểm tra hợp lệ)
    if not display_orders:
        st.info("Không tìm thấy đơn hàng nào phù hợp.")
    else:
        for order in display_orders:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1:
                    st.markdown(f"**Mã Đơn:** `{order.id}`")
                    st.write(f" Khách hàng: {order.customer_name}")
                    st.write(f"Email: {order.customer_email}")
                with c2:
                    st.write(f" Món ăn: {', '.join(order.items)}")
                    # Định dạng màu sắc trực quan cho từng loại trạng thái đơn hàng
                    color = 'green' if order.status == OrderStatus.PAID else 'blue' if order.status == OrderStatus.DELIVERING else 'red' if order.status == OrderStatus.CANCELLED else 'orange'
                    st.markdown(f" Trạng thái hiện tại: **:{color}[{order.status}]**")
                with c3:
                    st.caption("Hành động xử lý đơn:")
                    
                    if order.status not in [OrderStatus.PAID, OrderStatus.CANCELLED]:
                        # Tra cứu danh sách các trạng thái kế tiếp khả thi từ bảng cấu hình ALLOWED_TRANSITIONS
                        from src.models.order import ALLOWED_TRANSITIONS
                        next_options = [status for status in ALLOWED_TRANSITIONS.get(order.status, set()) if status != OrderStatus.CANCELLED]
                        
                        if next_options:
                            next_status = next_options[0]
                            if st.button(f"Chuyển sang [{next_status}]", key=f"next_{order.id}", use_container_width=True):
                                if om.update_order_status(order.id, next_status):
                                    st.toast(f"Đơn {order.id} đã chuyển sang {next_status}")
                                    time.sleep(0.3)
                                    st.rerun()
                                    
                        # Biên kiểm tra chặn: Ẩn hoặc chặn nút Hủy nếu đơn đang đi giao (DELIVERING) hoặc đã thanh toán (PAID)
                        if order.status not in [OrderStatus.DELIVERING, OrderStatus.PAID]:
                            if st.button("Hủy Đơn Hàng", key=f"cancel_{order.id}", type="secondary", use_container_width=True):
                                if om.update_order_status(order.id, OrderStatus.CANCELLED):
                                    st.toast(f"Đã hủy thành công đơn {order.id}")
                                    time.sleep(0.3)
                                    st.rerun()
                        else:
                            st.caption("*Không thể hủy đơn ở giai đoạn này*")
                    else:
                        st.caption("*Đơn hàng đã đóng vòng đời*")
                        
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
