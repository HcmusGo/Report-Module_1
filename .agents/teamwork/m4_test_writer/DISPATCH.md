## 2026-11-01T03:56:32Z
You are m4_test_writer, a teamwork_test_writer subagent.
Your working directory is: D:\Module 1\.agents\teamwork\m4_test_writer
Original Request path: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan path: D:\Module 1\PROJECT.md
Test infra path: D:\Module 1\TEST_INFRA.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All tests must be genuine and execute against real implementations. DO NOT hardcode test results, create dummy/facade implementations, or bypass real assertions. A teamwork_auditor will independently verify your work.

MANDATORY CONSTRAINTS:
- You ONLY have write ownership of test files:
  - `tests/test_order_manager.py` (update)
  - `tests/test_routing_service.py` (new)
  - `tests/test_customer_manager.py` (new)
  - `tests/test_app_smoke.py` (new smoke test or integrate in test suite)
- DO NOT modify any file in `src/` or `data/`! Use temporary directories (`tempfile.TemporaryDirectory`) for any test JSON files or temporary map graphs.
- NEVER touch any of the 7 core files.
- DO NOT import collections/deque, heapq, bisect, queue, networkx.
- Keep all line lengths <= 100 characters.

TASK SPECIFICATIONS (Milestone M4: Comprehensive Test Suite):

1. Update `tests/test_order_manager.py`:
   - Update existing tests calling `create_order` to the new signature:
     `create_order(order_id, customer_name, customer_email, items, created_at, is_vip, delivery_node_id)`
     (Note: `shipper_status` parameter is REMOVED!).
   - Existing tests that previously tested DELIVERING transitions via `update_order_status` should now test `start_delivery([order_id])`.
   - Preserve all existing test goals (test_legacy_json_compatibility, etc.).
   - Add new tests in `TestOrderManager`:
     - Shipper status derived: IDLE initially, BUSY when an order is DELIVERING, IDLE after complete_delivery.
     - `create_order` rejection: when shipper is BUSY ("Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"), when delivery_node_id is None / "ZZZ" / "RESTAURANT" ("Điểm giao không hợp lệ").
     - `start_delivery`: only with READY orders; rejected when shipper is BUSY; single snapshot undo restores all orders in batch to READY; redo restores to DELIVERING.
     - `complete_delivery`: transitions DELIVERING to PAID; shipper returns to IDLE when last order is completed.
     - `update_order_status`: blocks transition into DELIVERING ("Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"); blocks CONFIRMED -> PREPARING if not top order per PriorityEngine.
     - Safe `load_orders`: malformed JSON or corrupted records safely skipped to `load_errors` without crashing.
     - Immutability of `om.orders` property (mutating returned dict does not mutate internal `_orders`).

2. Create `tests/test_routing_service.py`:
   - Test all 6 error conditions of `load_map_graph(path)`:
     (a) Nonexistent file raises MapDataError
     (b) Empty file (0 bytes or whitespace) raises MapDataError
     (c) Malformed JSON file (with .bak) raises MapDataError with .bak notification
     (d) Missing "nodes" or empty "nodes" raises MapDataError
     (e) Missing "RESTAURANT" node raises MapDataError
     (f) ValueError from Graph.from_dict wrapped as MapDataError
   - Test `is_valid_delivery_node`:
     - "RESTAURANT", "ZZZ", empty string, isolated unreachable node return False.
     - Valid reachable nodes ("CUSTOMER", "CUSTOMER_2", "CUSTOMER_3") return True.
   - Test `route_single_order`:
     - Works for "dijkstra" and "astar" to valid delivery node.
     - Raises ValueError for invalid node or unreachable node.
   - Test `plan_batch_route` on canonical map:
     - Input `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`:
       - Visit order is `["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"]`.
       - `full_path` is `['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']`.
       - Total cost is 16.0 (`assertAlmostEqual`).
       - `full_path` has no two consecutive identical nodes.
       - Total cost equals sum of leg costs.
       - Dijkstra and A* yield identical total cost 16.0.
       - Duplicate delivery points (e.g. `["CUSTOMER_2", "CUSTOMER_2"]`) visited only once.
       - Empty list or invalid node raises ValueError.
     - Test tie-breaking: when two candidates have equal distance, chooses lexicographically smaller node ID.
   - Test `compare_trip_algorithms`: returns dict with "dijkstra" and "astar".
   - Test `build_map_figure_data`: returns nodes (with on_route flag), unique undirected edges (each edge once), and route steps sorted by step 0..N-1.

3. Create `tests/test_customer_manager.py`:
   - Test loading standard users from file.
   - Test `find_by_name` (case-insensitive, duplicates) and `find_by_email` (case-insensitive) via `SortedIndex`.
   - Test corrupted records skipped to `load_errors`.
   - Test missing file returns empty without crash.
   - Test `Customer` model validation (empty name, invalid email without @, empty node_id, from_dict missing fields).

4. Create `tests/test_app_smoke.py`:
   - Using `streamlit.testing.v1.AppTest`, run `src/app.py`:
     - Confirm all 4 tabs exist and no unhandled exceptions.
     - Confirm Map tab displays multiselect of READY orders when orders exist.

VERIFICATION:
- Run: `uv run python -m unittest discover -v -s tests -t .`
- Ensure 100% of all tests pass.
- Verify 7 core files are untouched:
  `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py`
- Verify zero prohibited imports across `src/` and `tests/`.
- Verify line lengths <= 100 characters.
