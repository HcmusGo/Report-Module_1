# Handoff Report: Specification Survey & Mining

**Agent**: `survey_spec_1` (`teamwork_spec_miner`)  
**Date**: 2026-11-01  
**Working Directory**: `D:\Module 1\.agents\teamwork\survey_spec_1`  
**Authoritative Source Documents**:
- `D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md`
- Verbatim prompt record: `C:\Users\LENOVO\.gemini\antigravity\brain\2cc1d68e-e76d-4014-b201-0dbcf2baba3b\.system_generated\messages\fad69f40-3cc1-4448-94c7-8b1b82f136da.json`
- `D:\Module 1\README.md`
- Codebase baseline: `src/core/`, `src/models/`, `data/`, `tests/`

---

## 1. Observation

### 1.1 Data Files Status & Differences
- **`data/map_graph.json`**:
  - *Current state*: Contains only 4 nodes (`RESTAURANT`, `A`, `B`, `C`) and 5 edges (`[RESTAURANT, A, 2.2]`, `[RESTAURANT, B, 4.0]`, `[A, B, 2.2]`, `[A, C, 3.6]`, `[B, C, 3.2]`).
  - *Required standard state*: Must contain 8 nodes (6 mentor nodes + 2 customer nodes `CUSTOMER_2`, `CUSTOMER_3`) and 12 bidirectional edges with exact coordinates and weights specified in Phần 0.
- **`data/users.json`**:
  - *Current state*: Contains only 2 users (`U001` with `node_id: "C"`, `U002` with `node_id: "B"`).
  - *Required standard state*: Must contain 4 users (`U001` to `U004`) pointing to `CUSTOMER`, `CUSTOMER_2`, `CUSTOMER_3`.
- **`data/orders.json`**:
  - *Current state*: Contains 3 orders (`O001`, `O002`, `O003`) with `status: "PAID"` and `delivery_node_id: null`.
  - *Constraint*: Must not crash when loaded, must safely record malformed entries to `load_errors`, and should not be tracked/committed to git when populated during manual app runs.

### 1.2 Baseline Codebase State
- Executed `uv run python -m unittest discover -s tests -t .`:
  - 20 tests run, 20 tests pass (`Ran 20 tests in 0.108s, OK`).
- The 7 core files are currently intact:
  1. `src/core/routing_algo.py`
  2. `src/core/priority_engine.py`
  3. `src/models/graph_node.py`
  4. `src/models/base.py`
  5. `src/core/storage.py`
  6. `src/core/structures.py`
  7. `src/core/menu_manager.py`
- In `src/models/menu_item.py`, lines 14–17 contain a fallback `try...except from models.base import BaseEntity` which must be replaced with `from src.models.base import BaseEntity`.

---

## 2. Logic Chain & Comprehensive Specifications

### 2.1 Standard Data Specifications (Phần 0)

#### `data/map_graph.json`
Must be overwritten only if the current file is still the template skeleton (4 nodes, no CUSTOMER).
```json
{
  "nodes": {
    "RESTAURANT": {"name": "Quán ăn", "x": 0.0, "y": 0.0},
    "A": {"name": "Ngã tư A", "x": 2.0, "y": 2.0},
    "B": {"name": "Ngã tư B", "x": 3.0, "y": -1.0},
    "C": {"name": "Ngã ba C", "x": 5.0, "y": 2.0},
    "D": {"name": "Ngã tư D", "x": 6.0, "y": -1.0},
    "CUSTOMER": {"name": "Nhà khách hàng", "x": 8.0, "y": 1.0},
    "CUSTOMER_2": {"name": "Nhà khách hàng 2", "x": 7.0, "y": 4.0},
    "CUSTOMER_3": {"name": "Nhà khách hàng 3", "x": 4.0, "y": -4.0}
  },
  "edges": [
    ["RESTAURANT", "A", 2.8],
    ["RESTAURANT", "B", 3.2],
    ["A", "B", 3.2],
    ["A", "C", 3.0],
    ["B", "D", 3.0],
    ["C", "D", 3.2],
    ["C", "CUSTOMER", 3.2],
    ["D", "CUSTOMER", 2.8],
    ["C", "CUSTOMER_2", 2.8],
    ["CUSTOMER", "CUSTOMER_2", 3.2],
    ["B", "CUSTOMER_3", 3.2],
    ["D", "CUSTOMER_3", 3.6]
  ]
}
```
**Verified Map Properties**:
- `RESTAURANT -> CUSTOMER`: Path `["RESTAURANT", "A", "C", "CUSTOMER"]`, cost = `9.0` (also `["RESTAURANT", "B", "D", "CUSTOMER"]` = 9.0).
- `RESTAURANT -> CUSTOMER_2`: Path `["RESTAURANT", "A", "C", "CUSTOMER_2"]`, cost = `8.6`.
- `RESTAURANT -> CUSTOMER_3`: Path `["RESTAURANT", "B", "CUSTOMER_3"]`, cost = `6.4`.
- **Gom chuyến 3 điểm (Nearest-Neighbor)**:
  - Starting at `RESTAURANT`, nearest unvisited: `CUSTOMER_3` (cost 6.4). Leg 1: `RESTAURANT -> CUSTOMER_3`.
  - From `CUSTOMER_3`, nearest unvisited: `CUSTOMER` (via D, cost 6.4 vs to `CUSTOMER_2` cost 9.6). Leg 2: `CUSTOMER_3 -> CUSTOMER`.
  - From `CUSTOMER`, nearest unvisited: `CUSTOMER_2` (cost 3.2). Leg 3: `CUSTOMER -> CUSTOMER_2`.
  - Visit order: `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`.
  - Concatenated `full_path`: `["RESTAURANT", "B", "CUSTOMER_3", "D", "CUSTOMER", "CUSTOMER_2"]`.
  - Total distance: `6.4 + 6.4 + 3.2 = 16.0`.
  - Dijkstra and A* both yield `16.0`.

#### `data/users.json`
Must be overwritten only if the current file has 2 users:
```json
[
  {"id": "U001", "name": "Nguyễn Văn An", "email": "an@example.com", "is_vip": true, "node_id": "CUSTOMER"},
  {"id": "U002", "name": "Trần Thị Bình", "email": "binh@example.com", "is_vip": false, "node_id": "CUSTOMER_2"},
  {"id": "U003", "name": "Lê Văn Cường", "email": "cuong@example.com", "is_vip": false, "node_id": "CUSTOMER_3"},
  {"id": "U004", "name": "Phạm Thu Dung", "email": "dung@example.com", "is_vip": true, "node_id": "CUSTOMER_2"}
]
```
*Note*: `U004` and `U002` share node `CUSTOMER_2` to test de-duplication of customer delivery points in batch planning.

---

### 2.2 Specifications for `src/core/routing_service.py` (Phần 1)

1. **Constants & Exceptions**:
   - `RESTAURANT_NODE_ID: str = "RESTAURANT"`
   - `MAP_PATH: str = "data/map_graph.json"`
   - `class MapDataError(Exception): pass`

2. **`load_map_graph(path: str = MAP_PATH) -> Graph`**:
   Must raise `MapDataError` in Vietnamese distinguishing all 6 failure modes:
   - **(a) File does not exist**: `Path(path).is_file()` is False -> raise `MapDataError(f"File bản đồ không tồn tại: {path}")`.
   - **(b) File is empty**: `path.stat().st_size == 0` or `.read_text().strip() == ""` -> raise `MapDataError(f"File bản đồ rỗng: {path}")`.
   - **(c) Syntax error in JSON**: If `load_json(path, default={})` returns `{}` and a backup file `path.with_name(f"{path.name}.bak")` exists:
     Raise `MapDataError(f"{Path(path).name} bị sai cú pháp và đã được đổi tên thành {Path(path).name}.bak; hãy sửa file .bak rồi đổi tên lại")`.
   - **(d) Missing or empty "nodes"**: If `"nodes"` not in `raw_data` or not `raw_data["nodes"]`:
     Raise `MapDataError("Dữ liệu bản đồ thiếu 'nodes' hoặc không có đỉnh nào.")`.
   - **(e) Missing `RESTAURANT_NODE_ID`**: If `RESTAURANT_NODE_ID` not in `raw_data["nodes"]` (or list of node dicts):
     Raise `MapDataError(f"Bản đồ thiếu đỉnh xuất phát của quán ({RESTAURANT_NODE_ID}).")`.
   - **(f) `Graph.from_dict` raises `ValueError`**:
     Catch `ValueError as err` and wrap: `raise MapDataError(f"Lỗi cấu trúc đồ thị bản đồ: {err}") from err`.

3. **`is_valid_delivery_node(graph: Graph, node_id: str) -> bool`**:
   - Returns True if and only if:
     1. `graph.has_node(node_id)` is True.
     2. `node_id != RESTAURANT_NODE_ID`.
     3. A valid path exists from `RESTAURANT_NODE_ID` to `node_id` (e.g. `dijkstra(graph, RESTAURANT_NODE_ID, node_id).found` is True, with cost < inf).
   - Returns False for `"ZZZ"`, `"RESTAURANT"`, disconnected nodes, or None/empty strings.

4. **Data Structures (NamedTuples)**:
   - `class SingleRoute(NamedTuple)`:
     - `delivery_node_id: str`
     - `path: list[str]`
     - `coords: list[tuple[float, float]]`
     - `cost: float`
     - `expanded: int`
   - `class RouteLeg(NamedTuple)`:
     - `start: str`
     - `end: str`
     - `path: list[str]`
     - `cost: float`
   - `class BatchRoute(NamedTuple)`:
     - `visit_order: list[str]`
     - `legs: list[RouteLeg]`
     - `full_path: list[str]`
     - `coords: list[tuple[float, float]]`
     - `total_cost: float`
     - `expanded_total: int`
     - `algorithm: str`

5. **`route_single_order(graph: Graph, delivery_node_id: str, algorithm: str = "dijkstra") -> SingleRoute`**:
   - If `not is_valid_delivery_node(graph, delivery_node_id)`: raise `ValueError(f"Điểm giao không hợp lệ hoặc không có đường đi từ Quán: {delivery_node_id}")`.
   - If `algorithm == "dijkstra"`: `res = dijkstra(graph, RESTAURANT_NODE_ID, delivery_node_id)`.
   - If `algorithm == "astar"`: `res = a_star(graph, RESTAURANT_NODE_ID, delivery_node_id)`.
   - Else: raise `ValueError(f"Thuật toán không hỗ trợ: {algorithm}")`.
   - If not `res.found`: raise `ValueError(f"Không có đường đi từ Quán tới {delivery_node_id}")`.
   - Returns `SingleRoute(delivery_node_id=delivery_node_id, path=res.path, coords=path_to_coordinates(res.path, graph), cost=res.cost, expanded=res.expanded)`.

6. **`plan_batch_route(graph: Graph, delivery_node_ids: list[str], algorithm: str = "dijkstra") -> BatchRoute`**:
   - Deduplicate `delivery_node_ids` while preserving order of first occurrence.
   - If empty after deduplication or if any node fails `is_valid_delivery_node(graph, node)`: raise `ValueError`.
   - Nearest-Neighbor greedy algorithm:
     - `current_node = RESTAURANT_NODE_ID`
     - `unvisited = list(deduped_delivery_node_ids)`
     - `legs: list[RouteLeg] = []`
     - `expanded_total = 0`
     - Loop while `unvisited`:
       - For each `target` in `unvisited`: compute route using `dijkstra` or `a_star`.
       - Select `target` with minimum `cost`.
       - **Tie-breaking**: If multiple targets have the exact same minimum cost, select the one with lexicographically smaller id (`min(candidates, key=lambda c: (c.cost, c.target_id))`).
       - Leg added: `RouteLeg(start=current_node, end=best.target_id, path=best.path, cost=best.cost)`.
       - Accumulate `expanded_total += best.expanded` (accumulate ONLY for the chosen leg; candidate probes do NOT count towards `expanded_total`).
       - `current_node = best.target_id`
       - Remove `best.target_id` from `unvisited`.
     - Concatenation of `full_path`:
       - First leg: `legs[0].path`
       - Subsequent legs: `leg.path[1:]` (omitting index 0 so juncture nodes are never repeated).
     - `coords = path_to_coordinates(full_path, graph)`.
     - `total_cost = sum(leg.cost for leg in legs)`.
     - `visit_order = [leg.end for leg in legs]`.
     - Complexity annotation: `O(k^2 (V+E) log V)` where `k` is the number of delivery nodes.
     - Return `BatchRoute(visit_order, legs, full_path, coords, total_cost, expanded_total, algorithm)`.

7. **`compare_trip_algorithms(graph: Graph, delivery_node_ids: list[str]) -> dict[str, BatchRoute]`**:
   - Returns `{"dijkstra": plan_batch_route(graph, delivery_node_ids, "dijkstra"), "astar": plan_batch_route(graph, delivery_node_ids, "astar")}`.

8. **`build_map_figure_data(graph: Graph, full_path: list[str] | None = None) -> dict[str, Any]`**:
   - Exports graph structures for Altair UI rendering:
     - `"nodes"`: list of `{"id": n.id, "name": n.name, "x": n.x, "y": n.y, "on_route": n.id in route_nodes_set}`.
     - `"edges"`: unique undirected segments `{"x": u.x, "y": u.y, "x2": v.x, "y2": v.y}` (each undirected edge included once).
     - `"route"`: list along `full_path`: `{"step": i, "node_id": nid, "x": node.x, "y": node.y}` where `step` increments `0, 1, 2, ...` in trip order.

9. **Existing functions to preserve**:
   - `path_to_coordinates(path: list[str], graph: Graph) -> list[tuple[float, float]]`
   - `get_map_render_data(graph: Graph, start_id: str, goal_id: str) -> dict[str, Any]` (change typing hints to built-ins).

---

### 2.3 Specifications for Customer Model & CustomerManager (Phần 3)

#### `src/models/customer.py`
- Inherits from `BaseEntity`.
- Attributes: private `_name`, `_email`, `_is_vip`, `_node_id`.
- Properties with validation:
  - `name`: string, `value.strip()` non-empty, raises `ValueError("Tên khách hàng không được để trống.")`.
  - `email`: string, `value.strip()` non-empty, must contain `'@'`, raises `ValueError("Email khách hàng không hợp lệ.")`.
  - `is_vip`: boolean.
  - `node_id`: string, `value.strip()` non-empty, raises `ValueError("Điểm giao hàng không được để trống.")`.
- `to_dict() -> dict[str, Any]`:
  - `data = super().to_dict()`
  - `data.update({"name": self._name, "email": self._email, "is_vip": self._is_vip, "node_id": self._node_id})`
  - Returns `data`.
- `@classmethod from_dict(cls, data: dict[str, Any]) -> Customer`:
  - Validates `isinstance(data, dict)` -> raises `ValueError("Dữ liệu đầu vào phải là dictionary.")`.
  - Checks presence of required keys: `"id"`, `"name"`, `"email"`, `"node_id"`.
  - Missing field raises `ValueError(f"Dữ liệu khách hàng thiếu trường '{missing_key}'.")`.

#### `src/core/customer_manager.py`
- `CustomerManager(storage_path: str | Path = "data/users.json")`:
  - Read-Only repository (no write/CRUD methods).
  - Storage loading: `load_json(storage_path, default=[])`.
  - Safe error handling: If a record fails validation (`ValueError`, `KeyError`, `TypeError`), skip the record and record error in `self.load_errors: list[str]`.
  - If root data is not `list` or `dict`, treat as empty and record to `self.load_errors`.
  - Sorted index integration:
    - Maintains `self._customers: dict[str, Customer] = {}`.
    - Maintains `self._name_index: SortedIndex = SortedIndex()`.
    - Maintains `self._email_index: SortedIndex = SortedIndex()`.
  - Methods:
    - `get_all() -> list[Customer]`: Returns `list(self._customers.values())`.
    - `get_by_id(customer_id: str) -> Customer | None`: `self._customers.get(customer_id)`.
    - `find_by_name(name: str) -> list[Customer]`: `self._name_index.find_all(name)` -> maps matching IDs to `Customer` objects in O(log n) + O(k).
    - `find_by_email(email: str) -> list[Customer]`: `self._email_index.find_all(email)` -> maps matching IDs to `Customer` objects in O(log n) + O(k).

---

### 2.4 Specifications for `src/core/order_manager.py` (Phần 2)

1. **Encapsulation & Private State**:
   - `self._orders: dict[str, Order]`
   - `self._name_index: SortedIndex`
   - `self._email_index: SortedIndex`
   - `self._undo_stack: CustomStack`
   - `self._redo_stack: CustomStack`
   - `self._graph: Graph | None`
   - `self.map_error: str = ""`
   - `self.last_error: str = ""`
   - `self.load_errors: list[str] = []`

2. **Read-Only Properties & Methods**:
   - `@property orders(self) -> dict[str, Order]`: Returns a shallow copy: `self._orders.copy()`.
     *Constraint*: Mutating the returned dictionary must NOT affect the internal manager state.
   - `get_order(self, order_id: str) -> Order | None`: Returns `self._orders.get(order_id)`.
   - `get_all_orders(self) -> list[Order]`: Returns `list(self._orders.values())`.
   - `can_undo(self) -> bool`: Returns `not self._undo_stack.is_empty()`.
   - `can_redo(self) -> bool`: Returns `not self._redo_stack.is_empty()`.

3. **`__init__(storage_path: str | Path = "data/orders.json", graph: Graph | None = None)`**:
   - If `graph is None`: Attempt to load map via `load_map_graph()`.
   - If `load_map_graph()` raises `MapDataError` or any Exception:
     `self._graph = None`, `self.map_error = str(err)`. Do NOT let application crash!
   - If `graph` is provided: `self._graph = graph`, `self.map_error = ""`.
   - Calls `self.load_orders()`.

4. **Derived Shipper Status (1 Quán - 1 Shipper Invariant)**:
   - `get_shipper_status() -> str`:
     - Checks if any order in `self._orders.values()` has `status == OrderStatus.DELIVERING`.
     - If yes: returns `"BUSY"`.
     - Else: returns `"IDLE"`.
   - `get_current_trip() -> list[Order]`:
     - Returns `[o for o in self._orders.values() if o.status == OrderStatus.DELIVERING]`.

5. **`create_order(...)`**:
   - Signature:
     `create_order(order_id: str, customer_name: str, customer_email: str, items: list[Any], created_at: float, is_vip: bool = False, delivery_node_id: str | None = None) -> bool`
   - *Parameter removed*: `shipper_status` is REMOVED.
   - Rejections (sets `self.last_error` and returns `False`):
     - Map error check: If `self._graph is None` or `self.map_error`:
       `self.last_error = self.map_error or "Bản đồ chưa sẵn sàng."` -> return `False`.
     - Shipper busy check: If `self.get_shipper_status() == "BUSY"`:
       `self.last_error = "Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"` -> return `False`.
     - Delivery node check: If `delivery_node_id` is None, empty, or `not is_valid_delivery_node(self._graph, delivery_node_id)`:
       `self.last_error = "Điểm giao không hợp lệ"` -> return `False`.
     - Standard checks: empty `order_id`, duplicate `order_id`, empty `customer_name`, empty `customer_email`, empty `items`.
   - On success: Creates `Order(..., delivery_node_id=delivery_node_id)`, adds to `self._orders`, indexes in `_name_index` and `_email_index`, saves via `self.save_orders()`, sets `self.last_error = ""`, returns `True`.

6. **`start_delivery(order_ids: list[str]) -> bool`**:
   - Atomic batch dispatch:
     - Check: If `self.get_shipper_status() == "BUSY"`:
       `self.last_error = "Shipper đang giao chuyến hiện tại, chưa thể bắt đầu chuyến mới."` -> return `False`.
     - Check: If not `order_ids`:
       `self.last_error = "Danh sách đơn hàng gom chuyến không được rỗng."` -> return `False`.
     - Check: If `len(order_ids) != len(set(order_ids))`:
       `self.last_error = "Danh sách đơn hàng gom chuyến có mã trùng lặp."` -> return `False`.
     - Validate all orders upfront before changing any state:
       - Every `oid` must exist in `self._orders`.
       - Every order must have `status == OrderStatus.READY`.
       - Every order must have `order.delivery_node_id` valid per `is_valid_delivery_node(self._graph, order.delivery_node_id)`.
       - If any fails: set `self.last_error` -> return `False`.
     - Once all pass:
       - Take ONE single snapshot: `snapshot = self._create_snapshot()`.
       - `self._undo_stack.push(snapshot)`.
       - `self._redo_stack.clear()`.
       - For each `oid` in `order_ids`: `self._orders[oid].change_status(OrderStatus.DELIVERING)`.
       - `self.save_orders()`.
       - Returns `True`. (Single Undo reverts ALL orders of the trip back to READY).

7. **`complete_delivery(order_id: str) -> bool`**:
   - Order must exist in `self._orders` and currently have `status == OrderStatus.DELIVERING`.
   - If not: `self.last_error = "Chỉ có thể hoàn thành đơn hàng đang ở trạng thái DELIVERING."` -> return `False`.
   - Take snapshot, push to `self._undo_stack`, clear `self._redo_stack`.
   - `order.change_status(OrderStatus.PAID)`.
   - `self.save_orders()`.
   - Returns `True`.
   - *Automatic IDLE*: When the last DELIVERING order is paid, `get_shipper_status()` evaluates to `"IDLE"`.

8. **`update_order_status(order_id: str, new_status: str) -> bool` Guardrails**:
   - **Block transition into DELIVERING**:
     If `new_status == OrderStatus.DELIVERING`:
     `self.last_error = "Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"` -> return `False`.
   - **Block out-of-order kitchen prep**:
     If current order is `OrderStatus.CONFIRMED` and `new_status == OrderStatus.PREPARING`:
     - Query: `confirmed = self.get_orders_by_status(OrderStatus.CONFIRMED)`.
     - `top_order = PriorityEngine().next_order(confirmed, now=time.time())`.
     - If `top_order` and `order_id != top_order.id`:
       `self.last_error = f"Đơn hàng '{top_order.id}' ({top_order.customer_name}) có độ ưu tiên cao hơn, phải chế biến trước."` -> return `False`.
   - Existing guardrails preserved: Cannot cancel if `PAID` or `DELIVERING`.
   - Snapshot pushed to `_undo_stack`, `_redo_stack.clear()`, `save_orders()`.

9. **`load_orders() -> None` Safe Loading**:
   - `self._orders.clear()`, `self._name_index.clear()`, `self._email_index.clear()`, `self.load_errors.clear()`.
   - Read via `load_json(self.storage_path, default={})`.
   - If raw data is not `dict` and not `list`:
     `self.load_errors.append(f"Dữ liệu orders.json không đúng định dạng: {type(data).__name__}")`.
     Return.
   - For each entry:
     Wrap `Order.from_dict` and index insertion in `try...except (ValueError, KeyError, TypeError) as err: self.load_errors.append(f"Bỏ qua bản ghi đơn hàng hỏng: {err}")`.
   - Never crash the application on corrupted order files.

---

### 2.5 Specifications for Streamlit UI (`src/app.py`) (Phần 4 & Phần 5)

1. **Architecture Rule**:
   - `app.py` MUST NOT call `load_json`, instantiate `Graph`, or run `dijkstra`/`a_star` directly.
   - `app.py` MUST NOT import `heapq`, `bisect`, `queue`, `networkx`, `collections`.
   - `app.py` MUST NOT contain the string `"shipper_status"` in dropdowns/forms.
   - `app.py` MUST NOT call `st.line_chart` for routing.

2. **Order Tab (`render_order_tab`)**:
   - No `st.form` for customer and item selection: use individual widgets with keys for instant reactivity.
   - Customer selectbox displays: `f"{c.name} - {c.email} - {'[VIP]' if c.is_vip else '[Thường]'} - điểm giao: {c.node_id}"`.
   - Shows warning if `CustomerManager` has no customers.
   - Quantity inputs appear immediately when items are selected (allowing the very first created order to have qty > 1).
   - Shipper status displayed as an informative banner: `st.info(f"Trạng thái Shipper: {om.get_shipper_status()}")`.
   - Button "Tạo đơn hàng" invokes `om.create_order(..., is_vip=selected_customer.is_vip, delivery_node_id=selected_customer.node_id)`.
   - Displays `st.error(om.last_error)` on failure.
   - Displays `st.warning` if `om.load_errors` or `customer_mgr.load_errors` are non-empty.
   - Order table includes "Điểm giao" column.
   - Status transitions:
     - For CONFIRMED orders: annotation "Chế biến theo thứ tự ở tab Hàng đợi" replaces direct action buttons.
     - For READY and DELIVERING orders: annotation "Giao hàng ở tab Bản đồ" replaces direct action buttons.
   - Undo/Redo toolbar uses public properties: `om.can_undo()`, `om.can_redo()`, `om.get_all_orders()`.

3. **Map Tab (`render_map_tab`)**:
   - Loaded via `load_map_graph()`; catches `MapDataError as err -> st.error(str(err))` and returns early.
   - Banner displaying `om.get_shipper_status()`.
   - Table of READY orders: `Mã đơn`, `Khách`, `VIP`, `Điểm giao`, `Quãng đường đơn lẻ từ Quán` (computed via `route_single_order`; if error, displays "không có đường").
   - Multiselect of READY orders to plan a trip:
     - Displays `plan_batch_route` output: visit order, legs breakdown, full path, total distance.
     - Displays comparison table from `compare_trip_algorithms`: Dijkstra vs A* total cost and nodes expanded.
   - Button "Bắt đầu giao": calls `om.start_delivery(selected_order_ids)`. Disabled if Shipper is BUSY or no orders selected.
   - When Shipper is BUSY:
     - Lists current trip orders (`om.get_current_trip()`).
     - Each order has a "Đã giao" button calling `om.complete_delivery(order.id)`.
     - Draws expected trip route (annotated "tính từ Quán").
   - **Altair Map Rendering (`st.altair_chart`)**:
     - Data sourced from `build_map_figure_data(graph, full_path)`.
     - Layer 1: Edges using `alt.Chart(edges_df).mark_rule(color="#d0d0d0", strokeWidth=2)`.
     - Layer 2: Nodes using `mark_circle(size=200)` + labels with `mark_text`.
     - Layer 3: Trip route using `mark_line(color="#e63946", strokeWidth=3.5)` with `order=alt.Order("step:Q")` ensuring correct sequential path rendering.

---

## 3. Discovered Features & Edge Cases

### Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Data | Standard Map 8 Nodes | Map with 6 mentor + 2 customer nodes (`CUSTOMER_2`, `CUSTOMER_3`) | JSON file `data/map_graph.json` | Graph dict | Raises MapDataError if corrupt | ORIGINAL_REQUEST.md Phần 0 |
| 2 | Data | Standard Users 4 Records | 4 customers U001-U004 with VIP status and delivery nodes | JSON file `data/users.json` | List of customer dicts | Skipped to load_errors if corrupt | ORIGINAL_REQUEST.md Phần 0 |
| 3 | Routing | `load_map_graph` | Loads map and enforces 6 discrete Vietnamese error cases | `path: str` | `Graph` | `MapDataError` with distinct message | ORIGINAL_REQUEST.md Phần 1 |
| 4 | Routing | `is_valid_delivery_node` | Checks node presence, non-restaurant, reachable from Quán | `graph: Graph, node_id: str` | `bool` | Returns `False` on invalid/unreachable | ORIGINAL_REQUEST.md Phần 1 |
| 5 | Routing | `route_single_order` | Computes shortest path from RESTAURANT to delivery node | `graph, delivery_node_id, algorithm` | `SingleRoute` | `ValueError` if invalid/no path | ORIGINAL_REQUEST.md Phần 1 |
| 6 | Routing | `plan_batch_route` | Nearest-neighbor route planning with tie-break & clean concat | `graph, delivery_node_ids, algorithm` | `BatchRoute` | `ValueError` if empty or invalid node | ORIGINAL_REQUEST.md Phần 1 |
| 7 | Routing | `compare_trip_algorithms` | Compares Dijkstra vs A* on identical batch delivery points | `graph, delivery_node_ids` | `dict[str, BatchRoute]` | Propagates ValueError | ORIGINAL_REQUEST.md Phần 1 |
| 8 | Routing | `build_map_figure_data` | Prepares node, edge, and ordered route frames for Altair | `graph, full_path` | `dict[str, list]` | None (returns empty route if None) | ORIGINAL_REQUEST.md Phần 1 |
| 9 | Customer | `Customer` Model | Customer entity with encapsulation and validation | `id, name, email, is_vip, node_id` | `Customer` instance | `ValueError` if name/email/node empty or email lacks @ | ORIGINAL_REQUEST.md Phần 3 |
| 10 | Customer | `CustomerManager` | Read-only manager with O(log n) SortedIndex lookup | `storage_path` | `CustomerManager` instance | Records invalid entries to `load_errors` | ORIGINAL_REQUEST.md Phần 3 |
| 11 | Order | Encapsulation & Copy | Private attributes and copy-on-read `orders` property | None | `dict[str, Order]` (copy) | Prevents direct state tampering | ORIGINAL_REQUEST.md Phần 2 |
| 12 | Order | Derived Shipper Status | Shipper state derived dynamically from active orders | None | `"BUSY"` or `"IDLE"` | None | ORIGINAL_REQUEST.md Phần 2 |
| 13 | Order | `create_order` Map & Shipper Guard | Validates delivery node and blocks order creation when BUSY | `order_id, name, email, items, created_at, is_vip, delivery_node_id` | `bool` | Returns `False` + `last_error` | ORIGINAL_REQUEST.md Phần 2 |
| 14 | Order | `start_delivery` | Atomic trip dispatch of READY orders with single snapshot | `order_ids: list[str]` | `bool` | Returns `False` + `last_error` | ORIGINAL_REQUEST.md Phần 2 |
| 15 | Order | `complete_delivery` | Marks DELIVERING order as PAID; returns shipper to IDLE | `order_id: str` | `bool` | Returns `False` + `last_error` | ORIGINAL_REQUEST.md Phần 2 |
| 16 | Order | `update_order_status` Guard | Blocks DELIVERING and enforces kitchen queue priority | `order_id: str, new_status: str` | `bool` | Returns `False` + `last_error` | ORIGINAL_REQUEST.md Phần 2 |
| 17 | Order | Safe `load_orders` | Loads orders without crashing on corrupt records | None | None | Records to `load_errors: list[str]` | ORIGINAL_REQUEST.md Phần 2 |
| 18 | UI | Reactive Order Tab | Unnested inputs with instant customer autocompletion | User selections | Streamlit widgets | Displays `st.error` on failure | ORIGINAL_REQUEST.md Phần 4 |
| 19 | UI | Dispatch Map Tab | Delivery planning screen with Altair 3-layer map rendering | Streamlit state | Altair visualization | Displays `st.error` on map errors | ORIGINAL_REQUEST.md Phần 5 |
| 20 | Codebase | CODEOWNERS Maintenance | Maps responsible modules to team member GitHub handles | Codeowners file | Codeowners mapping | None | ORIGINAL_REQUEST.md Phần 8 |

### Edge Cases
| # | Feature | Input | Observed / Required Behavior |
|---|---------|-------|------------------------------|
| 1 | `load_map_graph` | Non-existent file path | Raises `MapDataError` stating file does not exist |
| 2 | `load_map_graph` | Empty file (0 bytes or whitespace) | Raises `MapDataError` stating file is empty |
| 3 | `load_map_graph` | Malformed JSON file (resulting in `.bak` file) | Raises `MapDataError` notifying user of `.bak` rename and remediation |
| 4 | `load_map_graph` | JSON without `"nodes"` or with empty `"nodes": {}` | Raises `MapDataError` stating missing nodes |
| 5 | `load_map_graph` | JSON missing `"RESTAURANT"` node | Raises `MapDataError` stating missing restaurant origin node |
| 6 | `load_map_graph` | Edges with negative weight or invalid endpoints | `Graph.from_dict` raises `ValueError`, wrapped into `MapDataError` |
| 7 | `is_valid_delivery_node`| `"RESTAURANT"` or `"ZZZ"` or disconnected node | Returns `False` |
| 8 | `route_single_order` | `delivery_node_id="RESTAURANT"` | Raises `ValueError` |
| 9 | `route_single_order` | Disconnected node with no path from Quán | Raises `ValueError` |
| 10 | `plan_batch_route` | Empty list `[]` | Raises `ValueError` |
| 11 | `plan_batch_route` | Duplicate delivery IDs (e.g. `["CUSTOMER_2", "CUSTOMER_2"]`) | Deduplicates while preserving order -> visits `CUSTOMER_2` once |
| 12 | `plan_batch_route` | Candidates with identical distance | Tie-breaks by choosing the node with lexicographically smaller ID |
| 13 | `plan_batch_route` | Juncture concatenation | Junctures between legs are merged without duplicate consecutive nodes |
| 14 | `create_order` | When Shipper is `BUSY` | Returns `False`, `last_error="Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"` |
| 15 | `create_order` | `delivery_node_id=None` or `"ZZZ"` or `"RESTAURANT"` | Returns `False`, `last_error="Điểm giao không hợp lệ"` |
| 16 | `start_delivery` | Order list containing non-READY or non-existent order | Entire batch rejected, no state change |
| 17 | `start_delivery` | Duplicate order IDs in input list | Entire batch rejected, no state change |
| 18 | `start_delivery` | Single Undo after start_delivery | Reverts all orders in the batch back to `READY` in one step |
| 19 | `complete_delivery` | Called on an order that is not `DELIVERING` | Returns `False`, `last_error` explains requirement |
| 20 | `complete_delivery` | Last order completed | Shipper status automatically flips from `BUSY` to `IDLE` |
| 21 | `update_order_status` | Any transition directly into `DELIVERING` | Returns `False`, `last_error="Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"` |
| 22 | `update_order_status` | `CONFIRMED -> PREPARING` on non-top priority order | Returns `False`, `last_error` names top priority order |
| 23 | `load_orders` | JSON contains malformed order entry | Skips entry, records error to `load_errors`, continues without crash |
| 24 | `Customer` | Email without `'@'` | Raises `ValueError` |
| 25 | `CustomerManager` | User file missing | Returns empty list, does not crash |
| 26 | `OrderManager.orders` | User mutates `om.orders['O001'] = ...` or deletes a key | Mutates copy only; internal `om._orders` remains unaffected |

---

## 4. Caveats

1. **Immutable Core Files**:
   Under no circumstances may the 7 core files (`routing_algo.py`, `priority_engine.py`, `graph_node.py`, `base.py`, `storage.py`, `structures.py`, `menu_manager.py`) be modified. Any optional cleanup (T1, T2) in Phần 8 was explicitly deferred/skipped by user instructions.
2. **Altair Dependency**:
   Altair is already present via Streamlit in `uv.lock`. No new dependencies are needed or permitted in `pyproject.toml`.
3. **Map Figures Coordinates**:
   In `build_map_figure_data`, when plotting edges, each edge must be included once (e.g. ensure `u < v` lexicographically or filter seen undirected pairs).

---

## 5. Conclusion

All specifications, data schemas, algorithmic details, and business rules have been mined from authoritative sources.
The plan is clear and unambiguous:
- **Baseline**: 20 tests pass.
- **Phase 0**: Populate standard 8-node map and 4-user dataset.
- **Phase 1**: Implement `routing_service.py` with 6-error `load_map_graph`, nearest-neighbor `plan_batch_route`, Altair figure exporter.
- **Phase 2 & 3**: Implement `Customer`, `CustomerManager`, update `OrderManager` (private state, derived shipper status, strict start_delivery/complete_delivery, kitchen queue priority guardrails, safe loading).
- **Phase 4 & 5**: Modernize Streamlit UI in `src/app.py` for Order Tab and Map Tab.
- **Phase 6**: Comprehensive unit tests covering all features and edge cases.
- **Phase 7 & 8**: Update `README.md`, `.github/CODEOWNERS`, and Git commits.

---

## 6. Verification Method

To independently verify the specifications documented here:
1. **Run baseline unit tests**:
   ```powershell
   uv run python -m unittest discover -s tests -t .
   ```
   (Must report 20 passed tests).
2. **Inspect authoritative specification sources**:
   - `D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md`
   - `C:\Users\LENOVO\.gemini\antigravity\brain\2cc1d68e-e76d-4014-b201-0dbcf2baba3b\.system_generated\messages\fad69f40-3cc1-4448-94c7-8b1b82f136da.json`
3. **Verify core file immutability check**:
   ```powershell
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   (Must output empty).
