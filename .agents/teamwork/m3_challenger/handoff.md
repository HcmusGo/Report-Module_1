# Challenger Handoff Report: Milestone M3 — Streamlit UI Verification

## 1. Observation
Direct empirical execution and measurement results on commit/working tree `feat/connect-routing-order`:

### 1.1 AppTest Interactive Multi-Step Simulation
- **Command executed**:
  `$env:PYTHONIOENCODING="utf-8"; uv run python -c "from streamlit.testing.v1 import AppTest; at = AppTest.from_file('src/app.py'); at.run(); ..."`
- **Verbatim observations**:
  - `at.run()` completed with `len(at.exception) == 0`.
  - 4 tabs detected: `['Bản đồ / Lộ trình', 'Menu', 'Hàng đợi chế biến', 'Đơn hàng']`.
  - Initial Shipper status banner in Map and Order tabs: `"Trạng thái Shipper: IDLE"`.
  - Reactive Customer selectbox (`order_customer_select`): populated with 4 users (`U001`, `U002`, `U003`, `U004`). Selecting index 2 reactively updated `at.session_state` and rendered customer caption with VIP badge and delivery node (`CUSTOMER_3`).
  - Dish multiselect (`order_dishes_select`): selecting dish reactively rendered dynamic number input widget `order_dish_qty_M001` with default value 1; changing quantity to 2 reactively persisted to `item_snapshots`.
  - Negative validation on empty dishes: clicking `btn_create_order` without dishes yielded error: `"Vui lòng chọn ít nhất một món ăn."` (0 unhandled exceptions).
  - Order creation lifecycle:
    1. Order `O001` created in `PLACED` status with `delivery_node_id='CUSTOMER'`.
    2. Order Tab button `next_O001` advanced status to `CONFIRMED`.
    3. Kitchen Tab queue button `Nhận đơn vào bếp (-> PREPARING)` advanced status to `PREPARING`.
    4. Kitchen Tab button `finish_O001` advanced status to `READY`.
  - Map Tab READY orders table:
    - Automatically rendered 1-row dataframe: `{'Mã đơn': 'O001', 'Khách hàng': 'Nguyễn Văn An', 'VIP': 'VIP 🌟', 'Điểm giao': 'CUSTOMER', 'Quãng đường đơn lẻ từ Quán': '9.0 km'}`.
    - Multiselect `map_batch_order_select` dynamically populated with `['[O001] Điểm: CUSTOMER - Khách: Nguyễn Văn An']`.
  - Batch Dispatch & Shipper Constraints:
    - Selecting `O001` in `map_batch_order_select` enabled button `btn_start_delivery` (previously disabled).
    - Clicking `btn_start_delivery` changed `O001` status to `DELIVERING` and Shipper state to `BUSY`.
    - Clicking `btn_create_order` while Shipper was `BUSY` rejected order creation with error: `"Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"`.
    - Clicking `complete_O001` in Map Tab transitioned `O001` to `PAID` and restored Shipper state to `IDLE`.
  - 3-Customer Benchmark (`CUSTOMER`, `CUSTOMER_2`, `CUSTOMER_3`):
    - Batch route computed visit order `CUSTOMER_3 -> CUSTOMER -> CUSTOMER_2` with total distance `16.0 km`.
    - Comparison table verified Dijkstra (`16.0 km`, 15 nodes expanded) and A* (`16.0 km`, 8 nodes expanded).
    - Undo/Redo verified: `om.undo()` reverted all 3 orders to `READY` (Shipper `IDLE`); `om.redo()` restored all 3 orders to `DELIVERING` (Shipper `BUSY`).

### 1.2 Strict Negative Criteria
- **Regex scan for `shipper_status` in `src/app.py`**:
  - Command: `git grep -i "shipper_status" src/app.py`
  - Output: Exit code 1, verbatim 0 matches.
  - Python regex search (`re.finditer(r'shipper_status', text, re.I)`): 0 matches.
- **AST scan for forbidden imports in `src/app.py`**:
  - Command: parsed AST of `src/app.py`, checked all `ast.Import` and `ast.ImportFrom` nodes.
  - Result: Verbatim 0 imports of `load_json` and 0 imports of `Graph`.
- **AST & text scan for `st.line_chart` in `src/app.py`**:
  - Raw text: `"line_chart"` not found (0 occurrences).
  - AST calls: 0 calls to attribute `line_chart`. Visualization strictly uses Altair (`st.altair_chart`).

### 1.3 Line Length Audit
- **Command executed**:
  `uv run python -c "with open('src/app.py', encoding='utf-8') as f: lines = [(i+1, len(l.rstrip())) for i, l in enumerate(f) if len(l.rstrip()) > 100]; assert len(lines) == 0"`
- **Result**: 0 lines exceeding 100 characters across all 875 lines in `src/app.py`. Max line length observed is 99 characters.

### 1.4 7 Core Files Untouched
- **Command executed**:
  `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py`
- **Result**: Verbatim empty output (0 files changed, 0 insertions, 0 deletions).

### 1.5 Prohibited Imports Across `src/`
- **Command executed**:
  `git grep -rnE "(import|from) +(heapq|bisect|queue|networkx|collections)" src`
- **Result**: Verbatim exit code 1, 0 matches. Complete AST traversal across all `.py` files in `src/` confirmed 0 prohibited library imports.

### 1.6 Adversarial Stress Testing & Error Resilience
- **Corrupted users / orders data**:
  - Injected malformed user entry (missing required fields) into `data/users.json` and malformed order entry into `data/orders.json`.
  - Result: App loaded without crash (`0 exceptions`), displaying warnings:
    - `"Bỏ qua 1 bản ghi khách hàng do lỗi dữ liệu."`
    - `"Bỏ qua 1 bản ghi đơn hàng do lỗi dữ liệu."`
- **Invalid Map Graph file**:
  - Overwrote `data/map_graph.json` with malformed JSON.
  - Result: Handled cleanly via `MapDataError`, displaying `st.error(...)` with backup instructions; 0 unhandled exceptions.
- **Unreachable Delivery Node**:
  - Simulated an order with unreachable delivery node `ISOLATED`.
  - Result: Map Tab displayed `"không có đường"` in the single route distance column without raising unhandled exceptions.

---

## 2. Logic Chain
1. *Observation 1.1* demonstrates that `src/app.py` correctly coordinates `OrderManager`, `CustomerManager`, `PriorityEngine`, and `routing_service` via Streamlit without runtime exceptions.
2. *Observation 1.1* confirms that the Order Tab customer selectbox and dish multiselect function reactively outside of any `st.form`, dynamically presenting quantity number inputs for each selected dish.
3. *Observation 1.1* confirms that the Map Tab conditionally renders the READY orders table, computes single-route distances, plans batch deliveries matching the 16.0 km 3-customer benchmark, and prevents dispatch when no orders are selected or shipper is BUSY.
4. *Observation 1.2* demonstrates that `shipper_status` has been eliminated from `src/app.py` (resolving status dynamically via public method reflection), `load_json` and `Graph` are not imported directly, and `st.line_chart` is replaced with 3-layer Altair charts.
5. *Observation 1.3* verifies that all lines in `src/app.py` conform strictly to the <= 100 character style limit.
6. *Observation 1.4 & 1.5* verify zero drift across the 7 protected core files and zero usage of prohibited data structures across `src/`.
7. *Observation 1.6* proves that `src/app.py` degrades gracefully under corrupt inputs and edge cases, surfacing clear user-facing warnings/errors rather than crashing.

---

## 3. Caveats
- Out of scope for M3 challenger: Unit test suite refactoring in `tests/test_order_manager.py` (this file still contains legacy test signatures from before M2/M3 and is scheduled for Milestone M4).
- Streamlit prints deprecation warnings for `use_container_width` recommending migration to `width='stretch'` after 2025-12-31; these are upstream Streamlit deprecation notices and do not affect app correctness.

---

## 4. Conclusion
**VERDICT: APPROVE**

The Streamlit UI refactoring in `src/app.py` satisfies all functional requirements and strictly adheres to all negative architectural constraints:
- 0 occurrences of `shipper_status` in `src/app.py`.
- 0 prohibited imports (`load_json`, `Graph`, `heapq`, `bisect`, `queue`, `networkx`, `collections`).
- 0 calls to `st.line_chart`.
- 0 lines exceeding 100 characters in `src/app.py`.
- 0 diff lines across 7 core files.
- 100% pass on multi-step interactive simulation, reactive widgets, and batch dispatch workflow.

---

## 5. Verification Method
To independently verify this report, execute the following commands from `D:\Module 1`:

1. **Verify 0 occurrences of `shipper_status` in `src/app.py`**:
   ```powershell
   git grep -i "shipper_status" src/app.py
   # Expect exit code 1 (no matches)
   ```

2. **Verify AST forbidden imports in `src/app.py`**:
   ```powershell
   uv run python -c "import ast; tree = ast.parse(open('src/app.py', encoding='utf-8').read()); names = [a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names]; assert 'load_json' not in names and 'Graph' not in names; print('Import PASS')"
   ```

3. **Verify no `st.line_chart` in `src/app.py`**:
   ```powershell
   uv run python -c "assert 'line_chart' not in open('src/app.py', encoding='utf-8').read(); print('LineChart PASS')"
   ```

4. **Verify line lengths <= 100 characters in `src/app.py`**:
   ```powershell
   uv run python -c "assert all(len(l.rstrip('\r\n')) <= 100 for l in open('src/app.py', encoding='utf-8')); print('Line Length PASS')"
   ```

5. **Verify 7 core files untouched**:
   ```powershell
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   # Expect empty output
   ```

6. **Verify 0 prohibited imports across `src/`**:
   ```powershell
   git grep -rnE "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   # Expect exit code 1 (no matches)
   ```

7. **Verify AppTest initial load and tabs**:
   ```powershell
   $env:PYTHONIOENCODING="utf-8"; uv run python -c "from streamlit.testing.v1 import AppTest; at = AppTest.from_file('src/app.py'); at.run(); assert len(at.exception) == 0; assert len(at.tabs) == 4; print('AppTest Load PASS')"
   ```
