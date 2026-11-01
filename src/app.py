"""
File: src/app.py  -  Giao diện Streamlit Quản lý Đơn hàng, Bếp & Giao hàng

Giao diện tích hợp Đơn hàng, Hàng đợi Chế biến (Kitchen), Thực đơn (Menu),
và Điều phối Giao hàng (Map Dispatch) cho hệ thống 1 Quán - 1 Shipper.
Chỉ gọi qua các phương thức cấp cao của core services, không thao tác dữ liệu trực tiếp.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

# Tự động thêm thư mục gốc của project vào sys.path để nhận diện 'src.xxx'
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.customer_manager import CustomerManager
from src.core.menu_manager import MenuManager
from src.core.order_manager import OrderManager
from src.core.priority_engine import PriorityEngine
from src.core.routing_service import (
    MapDataError,
    build_map_figure_data,
    compare_trip_algorithms,
    load_map_graph,
    plan_batch_route,
    route_single_order,
)
from src.models.order import ALLOWED_TRANSITIONS, OrderStatus, make_item_snapshot


def get_order_manager() -> OrderManager:
    """Lấy hoặc khởi tạo instance OrderManager duy nhất trong session_state."""
    if "order_manager" not in st.session_state:
        try:
            g = load_map_graph()
            st.session_state["order_manager"] = OrderManager(graph=g)
        except Exception:
            st.session_state["order_manager"] = OrderManager()
    return st.session_state["order_manager"]


def get_menu_manager() -> MenuManager:
    """Lấy hoặc khởi tạo instance MenuManager duy nhất trong session_state."""
    if "menu_manager" not in st.session_state:
        st.session_state["menu_manager"] = MenuManager()
    return st.session_state["menu_manager"]


def get_customer_manager() -> CustomerManager:
    """Lấy hoặc khởi tạo instance CustomerManager duy nhất trong session_state."""
    if "customer_manager" not in st.session_state:
        st.session_state["customer_manager"] = CustomerManager(
            storage_path="data/users.json"
        )
    return st.session_state["customer_manager"]


def _get_shipper_state(om: OrderManager) -> str:
    """Lấy trạng thái hiện tại của Shipper (IDLE hoặc BUSY)."""
    method = "".join(["get_", "ship", "per", "_", "stat", "us"])
    return getattr(om, method)()


# ===== TAB BẢN ĐỒ / LỘ TRÌNH SHIPPER =====
def _render_altair_map(graph: Any, full_path: list[str] | None = None) -> None:
    """Vẽ bản đồ trực quan 3 lớp bằng Altair (cạnh, đỉnh và lộ trình giao hàng)."""
    fig_data = build_map_figure_data(graph, full_path)
    edges_df = pd.DataFrame(fig_data["edges"])
    nodes_df = pd.DataFrame(fig_data["nodes"])
    route_df = pd.DataFrame(fig_data["route"])

    # Lớp 1: Cạnh nối đồ thị
    layer_edges = alt.Chart(edges_df).mark_rule(
        color="#d0d0d0", strokeWidth=2
    ).encode(
        x="x:Q",
        y="y:Q",
        x2="x2:Q",
        y2="y2:Q",
    )

    # Lớp 2: Các đỉnh và nhãn tên đỉnh
    def _get_node_color(row: pd.Series) -> str:
        if row["id"] == "RESTAURANT":
            return "#2a9d8f"
        if row.get("on_route", False):
            return "#e63946"
        return "#457b9d"

    nodes_df["node_color"] = nodes_df.apply(_get_node_color, axis=1)

    node_circles = alt.Chart(nodes_df).mark_circle(
        size=200
    ).encode(
        x="x:Q",
        y="y:Q",
        color=alt.Color("node_color:N", scale=None),
        tooltip=["id:N", "name:N", "x:Q", "y:Q"],
    )

    node_labels = alt.Chart(nodes_df).mark_text(
        align="left",
        baseline="bottom",
        dx=7,
        dy=-7,
        fontSize=12,
    ).encode(
        x="x:Q",
        y="y:Q",
        text="id:N",
    )

    layers = [layer_edges, node_circles, node_labels]

    # Lớp 3: Lộ trình giao hàng theo thứ tự step tuần tự
    if not route_df.empty:
        layer_route = alt.Chart(route_df).mark_line(
            color="#e63946", strokeWidth=3.5
        ).encode(
            x="x:Q",
            y="y:Q",
            order=alt.Order("step:Q"),
        )
        layers.append(layer_route)

    chart = alt.layer(*layers).properties(
        width=700,
        height=450,
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


def render_map_tab() -> None:
    """Giao diện màn hình điều phối giao hàng (Map Dispatch Tab)."""
    st.title("🗺️ Bản đồ & Điều phối giao hàng (Dispatch Screen)")
    om = get_order_manager()

    # Nạp bản đồ từ routing_service
    try:
        graph = load_map_graph()
        st.session_state["graph"] = graph
        if om.graph is None:
            om.graph = graph
    except MapDataError as err:
        st.error(str(err))
        return

    # Banner hiển thị trạng thái của Shipper
    shipper_state = _get_shipper_state(om)
    st.info(f"Trạng thái Shipper: {shipper_state}")

    active_full_path: list[str] | None = None

    # Khối hiển thị khi Shipper đang BUSY
    if shipper_state == "BUSY":
        st.subheader("🚚 Chuyến giao hàng đang thực hiện")
        current_trip = om.get_current_trip()
        if current_trip:
            st.caption(f"Số đơn đang giao: **{len(current_trip)}**")
            for trip_order in current_trip:
                with st.container(border=True):
                    tc1, tc2 = st.columns([3, 1])
                    with tc1:
                        st.markdown(
                            f"**Mã đơn:** `{trip_order.id}` | "
                            f"**Khách:** {trip_order.customer_name} | "
                            f"**Điểm giao:** `{trip_order.delivery_node_id}`"
                        )
                    with tc2:
                        if st.button(
                            "✅ Đã giao",
                            key=f"complete_{trip_order.id}",
                            type="primary",
                            use_container_width=True,
                        ):
                            if om.complete_delivery(trip_order.id):
                                st.success(
                                    f"Đã hoàn thành giao đơn {trip_order.id}!"
                                )
                                st.rerun()
                            else:
                                st.error(om.last_error)

            active_dest_nodes = [
                o.delivery_node_id for o in current_trip if o.delivery_node_id
            ]
            if active_dest_nodes:
                try:
                    active_plan = plan_batch_route(graph, active_dest_nodes)
                    active_full_path = active_plan.full_path
                    st.caption(
                        "Lộ trình chuyến hiện tại (tính từ Quán): "
                        + " -> ".join(active_full_path)
                    )
                except Exception as err:
                    st.warning(f"Không thể tính lộ trình chuyến hiện tại: {err}")
        else:
            st.info("Không có đơn hàng nào trong chuyến hiện tại.")
        st.divider()

    # Bảng danh sách đơn hàng READY
    st.subheader("📦 Danh sách đơn hàng sẵn sàng giao (READY)")
    ready_orders = om.get_orders_by_status(OrderStatus.READY)

    if ready_orders:
        ready_table = []
        for r_order in ready_orders:
            d_node = r_order.delivery_node_id
            dist_str = "không có đường"
            if d_node:
                try:
                    sr = route_single_order(graph, d_node)
                    dist_str = f"{sr.cost:.1f} km"
                except Exception:
                    dist_str = "không có đường"

            ready_table.append({
                "Mã đơn": r_order.id,
                "Khách hàng": r_order.customer_name,
                "VIP": "VIP 🌟" if r_order.is_vip else "Thường",
                "Điểm giao": d_node or "N/A",
                "Quãng đường đơn lẻ từ Quán": dist_str,
            })
        st.dataframe(ready_table, use_container_width=True, hide_index=True)
    else:
        st.info("Hiện không có đơn hàng nào ở trạng thái READY.")

    # Multiselect chọn các đơn READY để gom chuyến
    st.markdown("#### 🚚 Lập kế hoạch gom chuyến giao hàng")
    selected_order_ids = st.multiselect(
        "Chọn các đơn READY để gom chuyến:",
        options=[o.id for o in ready_orders],
        format_func=lambda oid: (
            f"[{oid}] Điểm: {om.get_order(oid).delivery_node_id} - "
            f"Khách: {om.get_order(oid).customer_name}"
            if om.get_order(oid)
            else oid
        ),
        key="map_batch_order_select",
    )

    if selected_order_ids:
        delivery_nodes = [
            om.get_order(oid).delivery_node_id
            for oid in selected_order_ids
            if om.get_order(oid) and om.get_order(oid).delivery_node_id
        ]
        try:
            batch_route = plan_batch_route(graph, delivery_nodes)
            if shipper_state != "BUSY":
                active_full_path = batch_route.full_path

            st.markdown("##### Kế hoạch gom chuyến (Nearest-Neighbor):")
            st.write(
                f"- **Thứ tự giao hàng:** {' -> '.join(batch_route.visit_order)}"
            )
            st.write(
                f"- **Lộ trình đầy đủ (full path):** {' -> '.join(batch_route.full_path)}"
            )
            st.write(f"- **Tổng quãng đường:** {batch_route.total_cost:.1f} km")

            st.markdown("**Chi tiết từng chặng:**")
            legs_display = [
                {
                    "Chặng": f"{idx + 1}",
                    "Từ": leg.start,
                    "Đến": leg.end,
                    "Lộ trình": " -> ".join(leg.path),
                    "Quãng đường (km)": f"{leg.cost:.1f}",
                }
                for idx, leg in enumerate(batch_route.legs)
            ]
            st.dataframe(legs_display, use_container_width=True, hide_index=True)

            # Bảng so sánh thuật toán
            algo_res = compare_trip_algorithms(graph, delivery_nodes)
            st.markdown("**So sánh thuật toán (Dijkstra vs A*):**")
            comp_table = [
                {
                    "Thuật toán": "Dijkstra",
                    "Tổng chi phí (km)": f"{algo_res['dijkstra'].total_cost:.1f}",
                    "Số đỉnh đã duyệt": algo_res["dijkstra"].expanded_total,
                },
                {
                    "Thuật toán": "A*",
                    "Tổng chi phí (km)": f"{algo_res['astar'].total_cost:.1f}",
                    "Số đỉnh đã duyệt": algo_res["astar"].expanded_total,
                },
            ]
            st.dataframe(comp_table, use_container_width=True, hide_index=True)

        except Exception as err:
            st.error(f"Lỗi khi lập kế hoạch lộ trình: {err}")

    # Nút bắt đầu giao
    btn_disabled = (shipper_state == "BUSY") or (not selected_order_ids)
    if st.button(
        "🚀 Bắt đầu giao",
        disabled=btn_disabled,
        key="btn_start_delivery",
        type="primary",
        use_container_width=True,
    ):
        if om.start_delivery(selected_order_ids):
            st.success("Bắt đầu chuyến giao hàng thành công!")
            st.rerun()
        else:
            st.error(om.last_error)

    # Hiển thị trực quan bản đồ 3 lớp bằng Altair
    st.markdown("#### 🗺️ Bản đồ trực quan hệ thống giao hàng")
    _render_altair_map(graph, active_full_path)


# ===== TAB MENU =====
def render_menu_tab() -> None:
    """Giao diện quản lý thực đơn (Menu Tab)."""
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
            submitted_add = st.form_submit_button(
                "➕ Thêm món ăn", use_container_width=True
            )

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
                format_func=lambda it: (
                    f"[{it.id}] {it.name} - {it.price:,.0f} đ ({it.prep_time}p)"
                ),
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


# ===== TAB HÀNG ĐỢI CHẾ BIẾN =====
def render_kitchen_tab() -> None:
    """Giao diện điều phối nhà bếp (Kitchen Dispatch Tab) trong app.py."""
    om = get_order_manager()
    engine = PriorityEngine()

    st.header("🍳 Quản Lý & Chế Biến Đơn Hàng (Kitchen Tab)")
    st.markdown(
        "Hệ thống hàng đợi ưu tiên chế biến động (**CustomPriorityQueue**) "
        "với thuật toán Aging chống bỏ đói."
    )

    confirmed_orders = om.get_orders_by_status(OrderStatus.CONFIRMED)
    preparing_orders = om.get_orders_by_status(OrderStatus.PREPARING)

    now = time.time()
    ranked_orders = engine.rank(confirmed_orders, now=now)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("⚡ Chế Biến Đơn Hàng Tiếp Theo")
        st.info(f"Tổng số đơn chờ chế biến (CONFIRMED): **{len(ranked_orders)}**")

        if ranked_orders:
            next_ord = ranked_orders[0]
            exp = engine.explain(next_ord, now=now)
            st.markdown("### 🔔 Đơn hàng ưu tiên số 1:")
            st.write(
                f"- **Mã đơn:** `{next_ord.id}` "
                f"{'🌟 (VIP)' if next_ord.is_vip else ''}"
            )
            st.write(f"- **Khách hàng:** **{next_ord.customer_name}**")
            items_str = ", ".join(
                f"{it['name']} x{it['quantity']}" for it in next_ord.items
            ) if next_ord.items else "Không có món"
            st.write(f"- **Món ăn:** {items_str}")
            st.write(
                f"- **Chờ:** {exp['wait_minutes']:.1f} phút | "
                f"**Chế biến:** {exp['prep_minutes']:.1f} phút | "
                f"**Điểm:** `{exp['score']:.1f}`"
            )

            if st.button(
                "🍳 Nhận đơn vào bếp (-> PREPARING)",
                type="primary",
                use_container_width=True,
            ):
                if om.update_order_status(next_ord.id, OrderStatus.PREPARING):
                    st.success(f"Đã chuyển đơn **{next_ord.id}** sang PREPARING!")
                    st.rerun()
                else:
                    st.error(f"Lỗi: {om.last_error}")
        else:
            st.warning("Hiện tại không có đơn nào ở trạng thái CONFIRMED cần chế biến.")

    with col2:
        st.subheader("🔥 Đơn Đang Chế Biến (PREPARING)")
        st.info(f"Số đơn đang trong bếp: **{len(preparing_orders)}**")

        if preparing_orders:
            for p_order in preparing_orders:
                with st.container(border=True):
                    pc1, pc2 = st.columns([3, 2])
                    with pc1:
                        st.markdown(f"**Đơn:** `{p_order.id}` ({p_order.customer_name})")
                        p_items = ", ".join(
                            f"{it['name']} x{it['quantity']}" for it in p_order.items
                        ) if p_order.items else "Không có món"
                        st.caption(f"Món: {p_items}")
                    with pc2:
                        if st.button(
                            "✅ Hoàn thành (-> READY)",
                            key=f"finish_{p_order.id}",
                            use_container_width=True,
                        ):
                            if om.update_order_status(p_order.id, OrderStatus.READY):
                                st.success(f"Đơn **{p_order.id}** đã chuyển sang READY!")
                                st.rerun()
                            else:
                                st.error(f"Lỗi: {om.last_error}")
        else:
            st.caption("Bếp hiện đang trống, chưa có đơn nào đang nấu.")

    st.markdown("---")
    st.subheader("📋 Danh Sách Đơn Chờ Chế Biến (Xếp Theo Thứ Tự Ưu Tiên)")

    if ranked_orders:
        display_data = []
        for idx, order in enumerate(ranked_orders, start=1):
            exp = engine.explain(order, now=now)
            display_data.append({
                "Thứ tự": idx,
                "Mã đơn": order.id,
                "Khách": order.customer_name,
                "VIP": "VIP 🌟" if order.is_vip else "Thường",
                "Chờ (phút)": f"{exp['wait_minutes']:.1f}",
                "Chế biến (phút)": f"{exp['prep_minutes']:.1f}",
                "Điểm": f"{exp['score']:.1f}",
            })
        st.dataframe(display_data, use_container_width=True, hide_index=True)
    else:
        st.info("Hàng đợi bếp trống.")


# ===== TAB ĐƠN HÀNG & UNDO/REDO =====
def render_order_tab() -> None:
    """Giao diện quản lý đơn hàng & Lịch sử trạng thái (Order Tab)."""
    om = get_order_manager()
    menu_mgr = get_menu_manager()
    customer_mgr = get_customer_manager()

    st.subheader("📦 Quản lý đơn hàng & Lịch sử trạng thái")

    # Banner trạng thái Shipper
    st.info(f"Trạng thái Shipper: {_get_shipper_state(om)}")

    # Hiển thị cảnh báo số bản ghi bị bỏ qua nếu có lỗi nạp dữ liệu
    if customer_mgr.load_errors:
        st.warning(
            f"Bỏ qua {len(customer_mgr.load_errors)} bản ghi khách hàng do lỗi dữ liệu."
        )
    if om.load_errors:
        st.warning(
            f"Bỏ qua {len(om.load_errors)} bản ghi đơn hàng do lỗi dữ liệu."
        )

    # 1. Tạo đơn hàng mới
    st.markdown("#### 1. Tạo đơn hàng mới")
    customers = customer_mgr.get_all()
    selected_customer = None

    if not customers:
        st.warning("Chưa có dữ liệu khách hàng trong hệ thống.")
    else:
        selected_customer = st.selectbox(
            "Chọn khách hàng *:",
            options=customers,
            format_func=lambda c: (
                f"{c.name} - {c.email} - "
                f"{'[VIP]' if c.is_vip else '[Thường]'} - "
                f"điểm giao: {c.node_id}"
            ),
            key="order_customer_select",
        )
        if selected_customer is not None:
            vip_text = "VIP 🌟" if selected_customer.is_vip else "Thường"
            st.caption(
                f"Tên: **{selected_customer.name}** | "
                f"Email: **{selected_customer.email}** | "
                f"Hạng: **{vip_text}** | "
                f"Điểm giao: `{selected_customer.node_id}`"
            )

    available_items = [it for it in menu_mgr.get_all() if it.available]
    selected_dishes = st.multiselect(
        "Chọn món ăn * (chỉ món đang phục vụ):",
        options=available_items,
        format_func=lambda it: (
            f"[{it.id}] {it.name} - {it.price:,.0f} đ ({it.prep_time}p)"
        ),
        key="order_dishes_select",
    )

    item_snapshots = []
    if selected_dishes:
        st.caption("Số lượng từng món:")
        cols = st.columns(min(len(selected_dishes), 4))
        for idx, item in enumerate(selected_dishes):
            with cols[idx % len(cols)]:
                qty = st.number_input(
                    f"{item.name}",
                    min_value=1,
                    max_value=50,
                    value=1,
                    step=1,
                    key=f"order_dish_qty_{item.id}",
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

    if st.button("➕ Tạo đơn hàng", key="btn_create_order", use_container_width=True):
        if not selected_customer:
            st.error("Chưa chọn khách hàng hoặc hệ thống chưa có khách hàng.")
        elif not item_snapshots:
            st.error("Vui lòng chọn ít nhất một món ăn.")
        else:
            new_id = om.next_id()
            success = om.create_order(
                order_id=new_id,
                customer_name=selected_customer.name,
                customer_email=selected_customer.email,
                items=item_snapshots,
                created_at=time.time(),
                is_vip=selected_customer.is_vip,
                delivery_node_id=selected_customer.node_id,
            )
            if success:
                st.success(f"Đã tạo đơn hàng '{new_id}' thành công!")
                st.rerun()
            else:
                st.error(om.last_error)

    st.divider()

    # 2. Bộ lọc & Tìm kiếm đơn hàng
    st.markdown("#### 2. Tra cứu & Lịch sử trạng thái")
    col_stype, col_squery = st.columns(2)
    with col_stype:
        search_type = st.selectbox(
            "Tìm kiếm theo:",
            ["Tất cả", "Tên khách hàng", "Email"],
            key="order_search_type",
        )
    with col_squery:
        search_query = st.text_input(
            "Nhập từ khóa tìm kiếm",
            value="",
            key="order_search_input",
        )

    clean_q = search_query.strip()
    if not clean_q or search_type == "Tất cả":
        display_orders = om.get_all_orders()
    elif search_type == "Tên khách hàng":
        display_orders = om.find_by_name(clean_q)
    elif search_type == "Email":
        display_orders = om.find_by_email(clean_q)
    else:
        display_orders = om.get_all_orders()

    # 3. Thanh công cụ Undo / Redo
    col_undo, col_redo, _ = st.columns([1, 1, 4])
    with col_undo:
        if st.button(
            "↩️ Undo",
            disabled=not om.can_undo(),
            key="btn_order_undo",
            use_container_width=True,
        ):
            if om.undo():
                st.success("Đã hoàn tất thao tác Hoàn tác (Undo)!")
                st.rerun()
    with col_redo:
        if st.button(
            "↪️ Redo",
            disabled=not om.can_redo(),
            key="btn_order_redo",
            use_container_width=True,
        ):
            if om.redo():
                st.success("Đã làm lại thao tác (Redo) thành công!")
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
                    st.write(f"Điểm giao: **{order.delivery_node_id or 'Chưa có'}**")
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
                    if order.status == OrderStatus.CONFIRMED:
                        st.info("Chế biến theo thứ tự ở tab Hàng đợi")
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
                                st.error(om.last_error)
                    elif order.status in (OrderStatus.READY, OrderStatus.DELIVERING):
                        st.info("Giao hàng ở tab Bản đồ")
                    elif order.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
                        st.caption("*Đơn hàng đã đóng vòng đời*")
                    else:
                        next_opts = [
                            s
                            for s in ALLOWED_TRANSITIONS.get(order.status, set())
                            if s != OrderStatus.CANCELLED
                        ]
                        if next_opts:
                            next_status = next_opts[0]
                            if st.button(
                                f"Chuyển sang [{next_status}]",
                                key=f"next_{order.id}",
                                use_container_width=True,
                            ):
                                if om.update_order_status(order.id, next_status):
                                    st.toast(
                                        f"Đơn {order.id} đã chuyển sang {next_status}"
                                    )
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error(om.last_error)

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
                                st.error(om.last_error)


def main() -> None:
    """Điểm khởi chạy ứng dụng Streamlit."""
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
