"""
File: src/app.py  -  Giao diện Streamlit

[CHUNG] Mỗi người chỉ viết hàm render của tab mình, đánh dấu bằng comment.
Tuyệt đối KHÔNG viết logic thuật toán hay đọc/ghi file ở đây; chỉ gọi sang src.core.
"""

import sys
import time
from pathlib import Path

import streamlit as st

# Tự động thêm thư mục gốc của project vào sys.path để nhận diện cả 'src.xxx'
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.menu_manager import MenuManager
from src.core.order_manager import OrderManager
from src.models.order import ALLOWED_TRANSITIONS, OrderStatus, make_item_snapshot


def get_order_manager() -> OrderManager:
    """Lấy hoặc khởi tạo instance OrderManager duy nhất trong session_state."""
    if "order_manager" not in st.session_state:
        st.session_state.order_manager = OrderManager()
    return st.session_state.order_manager


def get_menu_manager() -> MenuManager:
    """Lấy hoặc khởi tạo instance MenuManager duy nhất trong session_state."""
    if "menu_manager" not in st.session_state:
        st.session_state.menu_manager = MenuManager()
    return st.session_state.menu_manager


# ===== [M2] Đào Đoàn Đỗ Quyên - TAB BẢN ĐỒ / LỘ TRÌNH SHIPPER =====
def render_map_tab() -> None:
    st.info("TODO [M2]: vẽ lộ trình Shipper lên bản đồ (dữ liệu từ routing_service).")


# ===== [M3] Nguyễn Lê Đức Bảo - TAB MENU =====
def render_menu_tab() -> None:
    manager: MenuManager = get_menu_manager()

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
            f"⚡ Kết quả tìm kiếm O(log n) cho từ khóa **'{query}'**: "
            f"{len(display_items)} món tìm thấy."
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
                                f"Đã cập nhật món '{updated_item.name}' "
                                f"(Mã: {updated_item.id}) thành công!"
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
    """Giao diện điều phối nhà bếp (Kitchen Dispatch Tab) trong app.py."""
    try:
        from core.priority_engine import PriorityEngine, OrderItem
    except ModuleNotFoundError:
        from src.core.priority_engine import PriorityEngine, OrderItem

    if "priority_engine" not in st.session_state:
        st.session_state.priority_engine = PriorityEngine()
    priority_engine: PriorityEngine = st.session_state.priority_engine

    st.header("🍳 Quản Lý & Chế Biến Đơn Hàng (Kitchen Tab)")
    st.markdown(
        "Hệ thống hàng đợi ưu tiên chế biến dựa trên **CustomMinHeap** & **CustomPriorityQueue**."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("➕ Thêm Đơn Hàng Mới")
        with st.form(key="add_order_form"):
            order_id = st.text_input(
                "Mã Đơn Hàng", value=f"ORD-{st.session_state.get('order_counter', 101)}"
            )
            customer_name = st.text_input("Tên Khách Hàng", value="Nguyễn Văn A")
            items_str = st.text_area(
                "Món Ăn (phân cách bằng dấu phẩy)", value="Cơm tấm, Trà đá"
            )
            is_vip = st.checkbox("Đơn Hàng Ưu Tiên (VIP)")

            submit_button = st.form_submit_button(label="Gửi Vào Bếp")

            if submit_button:
                if not order_id or not customer_name or not items_str:
                    st.error("Vui lòng điền đầy đủ thông tin đơn hàng!")
                else:
                    items = [item.strip() for item in items_str.split(",") if item.strip()]
                    import datetime
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_order = OrderItem(
                        order_id=order_id,
                        customer_name=customer_name,
                        items=items,
                        created_at=now_str,
                        is_vip=is_vip,
                    )
                    priority_engine.add_order(new_order)
                    st.session_state['order_counter'] = (
                        st.session_state.get('order_counter', 101) + 1
                    )
                    st.success(f"Đã thêm đơn hàng **{order_id}** vào hàng đợi nhà bếp!")
                    st.rerun()

    with col2:
        st.subheader("⚡ Chế Biến Đơn Hàng Tiếp Theo")
        pending_orders = priority_engine.get_pending_orders()
        st.info(f"Tổng số đơn đang chờ: **{len(pending_orders)}**")

        if pending_orders:
            next_order = pending_orders[0]
            st.markdown("### 🔔 Đơn hàng ưu tiên nhất:")
            st.write(
                f"- **Mã đơn:** {next_order.order_id} "
                f"{'🌟 (VIP)' if next_order.is_vip else ''}"
            )
            st.write(f"- **Khách hàng:** {next_order.customer_name}")
            st.write(f"- **Món ăn:** {', '.join(next_order.items)}")
            st.write(f"- **Thời gian:** {next_order.created_at}")

            if st.button("✅ Hoàn Thành & Chuyển Đơn Tiếp Theo", type="primary"):
                processed = priority_engine.process_next_order()
                if processed:
                    st.success(f"Đã hoàn thành chế biến đơn hàng **{processed.order_id}**!")
                    st.rerun()
        else:
            st.warning("Hiện tại không có đơn hàng nào trong hàng đợi.")

    st.markdown("---")
    st.subheader("📋 Danh Sách Đơn Hàng Đang Chờ Chế Biến (Theo Thứ Tự Ưu Tiên)")

    if pending_orders:
        display_data = []
        for idx, order in enumerate(pending_orders, start=1):
            display_data.append({
                "Thứ Tự": idx,
                "Mã Đơn": order.order_id,
                "Khách Hàng": order.customer_name,
                "Loại Đơn": "VIP 🌟" if order.is_vip else "Thường",
                "Danh Sách Món": ", ".join(order.items),
                "Thời Gian Tạo": order.created_at,
            })
        st.table(display_data)
    else:
        st.info("Hàng đợi trống.")


# ===== [M5] Thân Văn Thế Lâm - TAB ĐƠN HÀNG & UNDO/REDO =====
def render_order_tab() -> None:
    om = get_order_manager()
    menu_mgr = get_menu_manager()

    st.subheader("📦 Quản lý đơn hàng & Lịch sử trạng thái")

    # 1. Form tạo đơn mới
    st.markdown("#### 1. Tạo đơn hàng mới")
    available_items = [item for item in menu_mgr.get_all() if item.available]

    with st.form("create_order_form"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            customer_name = st.text_input("Tên khách hàng *", placeholder="VD: Nguyễn Văn A")
            customer_email = st.text_input("Email khách hàng *", placeholder="VD: a@example.com")
            is_vip = st.checkbox("Khách hàng VIP 🌟", value=False)
        with col_c2:
            shipper_status = st.selectbox(
                "Trạng thái Shipper *",
                ["IDLE", "BUSY", "BATCHING_ALLOWED"],
                help="Chỉ nhận đơn khi Shipper ở trạng thái IDLE hoặc BATCHING_ALLOWED",
            )
            selected_items = st.multiselect(
                "Chọn món ăn * (chỉ món đang phục vụ):",
                options=available_items,
                format_func=lambda it: (
                    f"[{it.id}] {it.name} - {it.price:,.0f} đ ({it.prep_time}p)"
                ),
            )

        item_snapshots = []
        if selected_items:
            st.caption("Số lượng từng món:")
            cols = st.columns(min(len(selected_items), 4))
            for idx, item in enumerate(selected_items):
                with cols[idx % len(cols)]:
                    qty = st.number_input(
                        f"{item.name}",
                        min_value=1,
                        max_value=50,
                        value=1,
                        step=1,
                        key=f"order_qty_{item.id}",
                    )
                    item_snapshots.append(
                        make_item_snapshot(
                            item_id=item.id,
                            name=item.name,
                            quantity=qty,
                            price=item.price,
                            prep_minutes=item.prep_time,
                        )
                    )

        submitted_order = st.form_submit_button("➕ Tạo đơn hàng", use_container_width=True)
        if submitted_order:
            new_id = om.next_id()
            success = om.create_order(
                order_id=new_id,
                customer_name=customer_name,
                customer_email=customer_email,
                items=item_snapshots,
                created_at=time.time(),
                shipper_status=shipper_status,
                is_vip=is_vip,
            )
            if success:
                st.success(f"Đã tạo đơn hàng '{new_id}' thành công!")
                st.rerun()
            else:
                st.error(f"Tạo đơn thất bại: {om.last_error}")

    st.divider()

    # 2. Bộ lọc & Tìm kiếm đơn hàng tối ưu O(log n)
    st.markdown("#### 2. Tra cứu & Lịch sử trạng thái")
    col_search_type, col_search_value = st.columns(2)
    with col_search_type:
        search_type = st.selectbox("Tìm kiếm theo:", ["Tất cả", "Tên khách hàng", "Email"])
    with col_search_value:
        search_query = st.text_input("Nhập từ khóa tìm kiếm", value="")

    # Lọc dữ liệu bằng Binary Search
    if search_query.strip() == "":
        display_orders = list(om.orders.values())
    else:
        if search_type == "Tên khách hàng":
            display_orders = om.find_by_name(search_query.strip())
        elif search_type == "Email":
            display_orders = om.find_by_email(search_query.strip())
        else:
            display_orders = list(om.orders.values())

    # 3. Thanh công cụ Undo / Redo
    col_undo, col_redo, _ = st.columns([1, 1, 4])
    with col_undo:
        undo_disabled = om.undo_stack.is_empty()
        if st.button("↩️ Undo", disabled=undo_disabled, use_container_width=True):
            if om.undo():
                st.success("Đã hoàn tất trạng thái")
                st.rerun()
    with col_redo:
        redo_disabled = om.redo_stack.is_empty()
        if st.button("↪️ Redo", disabled=redo_disabled, use_container_width=True):
            if om.redo():
                st.success("Đã làm lại trạng thái thành công")
                st.rerun()

    st.write("---")

    # 4. Danh sách hiển thị và Chuyển trạng thái
    if not display_orders:
        st.info("Không tìm thấy đơn hàng nào phù hợp.")
    else:
        for order in display_orders:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1:
                    vip_badge = " 🌟 [VIP]" if order.is_vip else ""
                    st.markdown(f"**Mã Đơn:** `{order.id}`{vip_badge}")
                    st.write(f"Khách hàng: **{order.customer_name}**")
                    st.write(f"Email: {order.customer_email}")
                with c2:
                    if order.items:
                        items_str = ", ".join(
                            f"{it['name']} x{it['quantity']}" for it in order.items
                        )
                    else:
                        items_str = "Không có món"
                    st.write(f"Món ăn: {items_str}")
                    st.caption(f"Tổng chế biến: {order.total_prep_minutes:.0f} phút")
                    color = (
                        "green"
                        if order.status == OrderStatus.PAID
                        else "blue"
                        if order.status == OrderStatus.DELIVERING
                        else "red"
                        if order.status == OrderStatus.CANCELLED
                        else "orange"
                    )
                    st.markdown(f"Trạng thái hiện tại: **:{color}[{order.status}]**")
                with c3:
                    st.caption("Hành động xử lý đơn:")
                    if order.status not in [OrderStatus.PAID, OrderStatus.CANCELLED]:
                        next_options = [
                            status
                            for status in ALLOWED_TRANSITIONS.get(order.status, set())
                            if status != OrderStatus.CANCELLED
                        ]
                        if next_options:
                            next_status = next_options[0]
                            if st.button(
                                f"Chuyển sang [{next_status}]",
                                key=f"next_{order.id}",
                                use_container_width=True,
                            ):
                                if om.update_order_status(order.id, next_status):
                                    st.toast(f"Đơn {order.id} đã chuyển sang {next_status}")
                                    time.sleep(0.3)
                                    st.rerun()

                        if order.status not in [OrderStatus.DELIVERING, OrderStatus.PAID]:
                            if st.button(
                                "Hủy Đơn Hàng",
                                key=f"cancel_{order.id}",
                                type="secondary",
                                use_container_width=True,
                            ):
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
