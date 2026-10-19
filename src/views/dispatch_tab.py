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

#1. HÀNG ĐỢI ĐƠN CHỜ GIAO (FIFO)
st.subheader ("Hàng đợi đơn hàng đang chờ")
    waiting_orders = controller.waiting_table()
if waiting_orders:
    st.dataframe (waiting_orders, use_container_width=True)
else 
    st.info("Hiện tại không có đơn hàng nào đang điều phối")
st.markdown ("---")

#2. ĐỀ XUẤT SHIPPER & XÁC NHẬN GÁN ĐƠN
st.subheader ("Đề xuất & phân công đơn cho shipper")    
    if not waiting_orders:
        st.caption ("Hiện tại không có đơn hàng nào cần được thực hiện đề xuất shipper")
    else 
        order_ids = [str(o.["id"]) for o in waiting_orders if "id" in o]
        selected_orders = st.selectbox ("Chọn đơn hàng muốn xử lý", options= order_ids)
    column_suggest, column_assign = st.columns (2)
    suggestion_list = []
    with column_suggest:
        if st.button ("Đề xuất shipper tối ưu", use_container_width=True)
        result_suggest = controller.suggest_table (selected_orders)
    st.session_state[f"suggest_{selected_orders}"] = suggestion_list
    else
        st.error (result_suggest.message)
    if suggestion_list:
        st.markdown ("**Bảng đánh giá mức độ phù hợp của các tài xế:**")
        st.dataframe (suggestion_list, use_container_width=True)
    with st.form ("form_assign_shipper")
        shipper_ids =[str(s.["id"]) for s in suggestion_list]
        selected_shipper = st.selectbox ("Chọn tài xế để phân công", options= shipper_ids)
        submit_assign = st.form_submit_button ("Xác nhận gán")
        if submit_assign:
            result_assign = controller.assign(order_id= selected_orders, shipper_id= selected_shipper)
            if result_assign.is_success:
                st.success (result_assign.message)
                if f"suggest_{selected_order}" in st.session_state
                del st.session_state [f"suggest_{selected_order}"]
            st.rerun ()
        else
            st.error (result_assign.message)
        
        st.markdown ("---")
        
#3. QUẢN LÝ LỘ TRÌNH SHIPPER
st.subheader ("Quản lý lộ trình Shipper")
st.caption ("Hiển thị danh sách các điểm (PICKUP, DELIVERY) còn lại trong route và tải trọng hiện tại của từng shipper")

route_data = controller.route_table ()
    if route_data:
        st.dataframe (route_data, use_container_width=True)
    with st.form ("form_complete_stop")
    active_shipper = list ({str(r["shipper_data"]) for r in route_data})
    shipper_to_update = st.selectbox ("Chọn tài xế để cập nhật trạng thái di chuyển", options=active_shipper)
    submit_stop = st.form_submit_button ("Hoàn thành điểm dừng tiếp theo")

    if submit_stop:
        result_stop = controller.complete_next_stop (shipper_to_update)
        if result_stop.is_success:
            st.success (result_stop.message)
            st.rerun
        else
        st.error (result_stop.message)
    else
    st.info ("Hiện tại chưa có lộ trình PICKUP, DELIVERY nào đang hoạt động")

st.markdown ("...")

#4. THÀNH LẬP THANH CÔNG CỤ (UNDO/REDO)
st.subheader ("Thanh công cụ Undo/Redo")
st.caption ("Hoàn tất hoặc làm lại tức thì các thao tác điều phối đơn hàng")

column_undo, column_redo: st.columns (2)
with column_undo:
    undo_disabled = not controller.can_undo ()
    label_undo = controller.undo_label () or "Undo"
if st.button ("{label_undo}", disabled= undo_disabled, use_container_width=True):
    result_undo = controller.undo ()
    if result_undo.is_success:
        st.success (result_undo.message)
        st.rerun
    else
    st.error (result_undo.message)

with column_redo:
    redo_disabled = not controller.can_redo ()
    label_redo = controller.redo_label () or "Redo"
if st.button ("{label_redo}", disabled= redo_disabled, use_container_width=True):
    result_redo = controller.redo ()
    if result_undo.is_success:
        st.success (result_undo.message)
        st.rerun
    else
    st.error (result_undo.message)

st.markdown ("---")

#5: BẢN ĐỒ PLOTLY & SO SÁNH ĐƯỜNG
st.subheader("Bản đồ Plotly & So sánh đường")
    
    
    st.markdown("**Bảng đối chiếu trực tiếp lộ trình tối ưu:**")
    col_src, col_dst = st.columns(2)
    with col_src:
        src_node = st.text_input("Điểm xuất phát", value="N1")
    with col_dst:
        dst_node = st.text_input("Điểm đích đến", value="N5")
        
    if src_node and dst_node:
        comparison = controller.compare_routes(src=src_node, dst=dst_node)
        if comparison:
            st.markdown(f"Đang so sánh tuyến đường **ngắn nhất theo km** với **nhanh nhất theo phút** từ `{src_node}` tới `{dst_node}`:")
            st.dataframe(comparison, use_container_width=True)
            
    # Lấy dữ liệu đồ họa bao gồm cả highlight_paths của shipper được chọn để tô đậm
    # Nếu hệ thống có shipper được chọn hoặc đang quét lộ trình, bạn có thể truyền biến vào đây
    map_data = controller.map_figure_data()
    
    if map_data:
        fig = go.Figure()
        
        # Vẽ các tuyến đường nền và tô màu dựa theo mức độ đông (LOW, MEDIUM, HIGH)
        for edge in map_data.get("edges", []):
            x_coords = [edge.get("x1"), edge.get("x2")]
            y_coords = [edge.get("y1"), edge.get("y2")]
            traffic = edge.get("traffic", "LOW")
            
            # Quy ước bảng màu trực quan theo đặc tả
            color_map = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
            edge_color = color_map.get(traffic, "green")
            
            # Kiểm tra xem đoạn đường này có nằm trong danh sách lộ trình được chọn để tô đậm không
            is_highlighted = edge.get("highlighted", False)
            line_width = 5 if is_highlighted else 2  # Tô đậm đường nếu được chọn
            
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode="lines",
                line=dict(color=edge_color, width=line_width),
                hoverinfo="none",
                showlegend=False
            ))
            
        # Vẽ các nút giao và trạm dừng (markers+text) lên trên cùng bản đồ
        node_x = [node.get("x") for node in map_data.get("nodes", [])]
        node_y = [node.get("y") for node in map_data.get("nodes", [])]
        node_labels = [node.get("name", "") for node in map_data.get("nodes", [])]
        
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            marker=dict(size=12, color="blue"),
            text=node_labels,
            textposition="top center",
            name="Trạm dừng"
        ))
        
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode="closest"
        )

          st.plotly_chart(fig, use_container_width=True)
