## 2026-11-01T03:35:33Z
You are m3_worker, a teamwork_worker subagent.
Your working directory is: D:\Module 1\.agents\teamwork\m3_worker
Original Request path: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan path: D:\Module 1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONSTRAINTS:
- You ONLY have write ownership of `src/app.py`. DO NOT touch any other file.
- NEVER touch any of the 7 core files.
- DO NOT import collections/deque, heapq, bisect, queue, networkx.
- MUST NOT contain the string "shipper_status" in `src/app.py`! (Zero occurrences of shipper_status in app.py).
- MUST NOT import `load_json` or `Graph` in `src/app.py`.
- MUST NOT call `st.line_chart` in `src/app.py`.
- Keep lines <= 100 characters.

TASK SPECIFICATIONS (Milestone M3: Streamlit UI Refactor):
Refactor `src/app.py`:
1. Architecture:
   - Import and instantiate `CustomerManager(storage_path="data/users.json")` into `st.session_state["customer_manager"]`.
   - `OrderManager` instantiated with `graph=load_map_graph()` (or handles map loading internally).
   - Only call high-level methods of `routing_service`, `order_manager`, `customer_manager`, `menu_manager`.
2. Order Tab (`render_order_tab`):
   - Remove `st.form`. Use individual widgets with unique keys.
   - Customer selectbox outside form with options formatted as:
     `f"{c.name} - {c.email} - {'[VIP]' if c.is_vip else '[Thường]'} - điểm giao: {c.node_id}"`
   - Customer info is displayed read-only (no manual text inputs for name/email; if customer list empty, show `st.warning("Chưa có dữ liệu khách hàng trong hệ thống.")`).
   - Dish multiselect outside form. For each selected dish, quantity number_input appears immediately, allowing qty > 1 on the very first order.
   - Shipper status banner: `st.info(f"Trạng thái Shipper: {om.get_shipper_status()}")`. No fake shipper dropdown or shipper_status parameter!
   - Button "Tạo đơn hàng": calls `om.create_order(..., is_vip=customer.is_vip, delivery_node_id=customer.node_id)`.
     If failed, displays `st.error(om.last_error)`.
   - Displays `st.warning` showing skipped record count if `om.load_errors` or `customer_mgr.load_errors` is not empty.
   - Order table: add column "Điểm giao" displaying `order.delivery_node_id`.
   - For order actions:
     - If order is CONFIRMED: replace status buttons with note `Chế biến theo thứ tự ở tab Hàng đợi`.
     - If order is READY or DELIVERING: replace status buttons with note `Giao hàng ở tab Bản đồ`.
     - If status change fails, display `st.error(om.last_error)`.
   - Cancel, Undo, Redo toolbar uses public API: `om.can_undo()`, `om.can_redo()`, `om.get_all_orders()`, `om.undo()`, `om.redo()`.
3. Kitchen Queue Tab (`render_kitchen_tab`):
   - Ensure it uses public APIs and does not access private `_orders`.
4. Map Tab (`render_map_tab`):
   - Replace old distance calculator completely with the business dispatch screen.
   - Load map via `load_map_graph()`; catch `MapDataError as err`: show `st.error(str(err))` and return early. Store graph in `st.session_state` only on success.
   - Banner displaying `om.get_shipper_status()`.
   - Table of READY orders: Order ID, Customer Name, VIP, Delivery Node, Single route distance from Quán (`route_single_order`; if error, display "không có đường").
   - Multiselect of READY orders to plan a trip:
     - When selected, compute and display `plan_batch_route`: visit order, legs breakdown, full path, total distance.
     - Display algorithm comparison table from `compare_trip_algorithms`: Dijkstra vs A* total cost and nodes expanded.
   - Button "Bắt đầu giao": calls `om.start_delivery(selected_order_ids)`. On success calls `st.rerun()`, on failure displays `st.error(om.last_error)`. Disabled if Shipper is BUSY or no orders selected.
   - When Shipper is BUSY:
     - List current trip orders (`om.get_current_trip()`).
     - Each order has a "Đã giao" button calling `om.complete_delivery(order.id)`. On success calls `st.rerun()`.
     - Draw planned route of active trip (annotated "tính từ Quán").
   - Altair 3-layer map visualization (`st.altair_chart`):
     - Sourced from `build_map_figure_data(graph, full_path)`.
     - Layer 1: Edges with `alt.Chart(edges_df).mark_rule(color="#d0d0d0", strokeWidth=2)`.
     - Layer 2: Nodes with `alt.Chart(nodes_df).mark_circle(size=200)` and labels with `mark_text`.
     - Layer 3: Trip route with `alt.Chart(route_df).mark_line(color="#e63946", strokeWidth=3.5)` with `order=alt.Order("step:Q")` ensuring correct sequential path order.
     - DO NOT call `st.line_chart`!

VERIFICATION:
- Verify with `streamlit.testing.v1.AppTest` that `src/app.py` runs without exceptions across all tabs.
- Verify `grep -i "shipper_status" src/app.py` returns 0 results.
- Verify `src/app.py` does not import `load_json` or `Graph`.
- Verify `src/app.py` does not contain `st.line_chart`.
- Verify 7 core files are untouched.
- Verify zero prohibited imports.
- Verify lines <= 100 characters.

Write your handoff report to `D:\Module 1\.agents\teamwork\m3_worker\handoff.md`. Send a message when complete.
