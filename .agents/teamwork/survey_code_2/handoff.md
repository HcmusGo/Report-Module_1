# Baseline Architectural & Code-Level Survey Report

**Agent**: `survey_code_2` (Teamwork Explorer Subagent)  
**Parent Agent**: `438bab52-ba4d-457a-88b4-46dd96bdcf70`  
**Working Directory**: `D:\Module 1\.agents\teamwork\survey_code_2`  
**Date**: 2026-11-01  

---

## 1. Observation

### 1.1 Baseline Test Execution
- **Command**:
  ```powershell
  Set-Location "D:\Module 1"; uv run python -m unittest discover -v -s tests -t .
  ```
- **Execution Result**:
  - Test suite count: 20 tests across 3 test modules.
  - Tests passing: 20 / 20 (100% OK, 0 failures, 0 errors, 0 warnings).
  - Execution duration: ~0.112s - 0.149s.
  - Test breakdown:
    - `tests.test_order.TestOrder`: 7 tests
      1. `test_legacy_json_compatibility`: `ok` (verifies reading legacy JSON with `create_at` and `items` as `list[str]`)
      2. `test_name_and_email_validation`: `ok` (verifies setters reject empty strings)
      3. `test_restore_status`: `ok` (verifies status restore bypasses state machine transitions)
      4. `test_round_trip_serialization`: `ok` (verifies `to_dict` and `from_dict`)
      5. `test_status_is_read_only`: `ok` (verifies direct assignment to `order.status` raises `AttributeError`)
      6. `test_status_transitions`: `ok` (verifies allowed transitions: `PLACED -> CONFIRMED -> PREPARING -> READY -> DELIVERING -> PAID`)
      7. `test_total_prep_minutes`: `ok` (verifies calculation `2*15 + 1*5 = 35.0`)
    - `tests.test_order_manager.TestOrderManager`: 7 tests
      1. `test_cannot_cancel_delivering_or_paid`: `ok` (cannot cancel when DELIVERING or PAID)
      2. `test_corrupted_json_handling`: `ok` (corrupt JSON file renamed to `.bak`, manager starts empty)
      3. `test_create_order_shipper_status_and_errors`: `ok` (creates order with shipper IDLE/BATCHING_ALLOWED; BUSY rejected)
      4. `test_find_by_name_and_email_with_duplicates_and_case_insensitive`: `ok` (case-insensitive duplicate name/email search)
      5. `test_next_id_and_get_orders_by_status`: `ok` (auto-incrementing IDs `O001`, `O002` and status filtering)
      6. `test_save_and_reload`: `ok` (round-trip save to JSON and reload via new manager instance)
      7. `test_undo_redo_and_clear_redo_on_new_action`: `ok` (multi-step undo/redo and stack invalidation on new actions)
    - `tests.test_priority_engine.TestPriorityEngine`: 6 tests
      1. `test_case_a_normal_wait_10m_vs_new_vip`: `ok` (Normal waiting 10m vs new VIP waiting 0m -> VIP first)
      2. `test_case_b_normal_wait_40m_vs_new_vip_anti_starvation`: `ok` (Normal waiting 40m vs new VIP -> Normal first via aging)
      3. `test_case_c_different_prep_times`: `ok` (5m prep vs 20m prep -> 5m first)
      4. `test_case_d_tie_breaking_by_created_at`: `ok` (Tied scores broken by earlier `created_at`)
      5. `test_compute_priority_formula`: `ok` (`PREP_WEIGHT*prep - WAIT_WEIGHT*wait - (VIP_BONUS if vip)`)
      6. `test_next_order_and_explain`: `ok` (`next_order` and `explain` breakdown)

### 1.2 Inspection of the 7 Core Files (Protected / Zero-Modification)
A git diff check confirmed all 7 core files are completely untouched:
```powershell
git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
# (Returned 0 diff lines - clean)
```

Direct observations of file contents:
1. **`src/core/routing_algo.py`** (157 lines, Owner: Lê Trí Tiên):
   - Classes & Types:
     - `INF: float = float("inf")` (line 30)
     - `class RouteResult(NamedTuple)` (lines 33-49): `path: list[str]`, `cost: float`, `expanded: int`. Property `found -> bool` returns `bool(self.path)`.
   - Functions exported:
     - `_rebuild_path(prev: dict[str, str], start: str, goal: str) -> list[str]` (lines 51-57): Reconstructs path from goal to start via predecessor mapping.
     - `_search(graph: Graph, start: str, goal: str, heuristic: Callable[[str], float]) -> RouteResult` (lines 60-106): Generic Best-First Search with lazy deletion on `CustomMinHeap`. Complexity `O((V + E) log V)`.
     - `dijkstra(graph: Graph, start: str, goal: str) -> RouteResult` (lines 109-111): Calls `_search` with `heuristic = lambda _: 0.0`. Returns `RouteResult`.
     - `a_star(graph: Graph, start: str, goal: str) -> RouteResult` (lines 114-126): Calls `_search` with Euclidean distance scaled by `graph.heuristic_scale()`. Returns `RouteResult`.
     - `find_shortest_path(graph: Graph, start: str, goal: str, algorithm: str = "dijkstra") -> tuple[list[str], float]` (lines 129-148): Returns `(result.path, result.cost)`.
     - `compare_algorithms(graph: Graph, start: str, goal: str) -> dict[str, RouteResult]` (lines 150-157): Returns `{"dijkstra": ..., "astar": ...}`.
   - Data structures used: `CustomMinHeap[tuple[float, str]]` (from `src.core.structures`), built-in `list`, `dict`, `set`, `tuple`.

2. **`src/core/priority_engine.py`** (121 lines, Owner: Nguyễn Vũ Băng Tâm):
   - Constants: `VIP_BONUS = 30.0`, `WAIT_WEIGHT = 1.0`, `PREP_WEIGHT = 1.0` (lines 20-22).
   - Functions: `compute_priority(is_vip: bool, wait_minutes: float, prep_minutes: float) -> float` (lines 25-37). Formula: `PREP_WEIGHT * prep - WAIT_WEIGHT * max(0.0, wait) - (VIP_BONUS if is_vip else 0.0)`. Lower score = higher priority.
   - Protocols: `@runtime_checkable class OrderLike(Protocol)` (lines 40-49): Requires `id: str`, `customer_name: str`, `is_vip: bool`, `created_at: float`, `total_prep_minutes: float`.
   - Class `PriorityEngine` (lines 51-120):
     - `explain(self, order: OrderLike, now: float | None = None) -> dict[str, float]` (lines 58-75): Returns `{"wait_minutes", "prep_minutes", "vip_bonus", "score"}`.
     - `rank(self, orders: list[OrderLike], now: float | None = None) -> list[OrderLike]` (lines 77-110): Priority queue sorting using `CustomPriorityQueue`. Enqueues with key `(score, float(order.created_at))` for tie-breaking. Returns ordered list of orders.
     - `next_order(self, orders: list[OrderLike], now: float | None = None) -> OrderLike | None` (lines 112-120):
       - Takes `orders: list[OrderLike]` and optional `now: float | None`.
       - Calls `self.rank(orders, now=now)`.
       - Returns `ranked[0] if ranked else None`.

3. **`src/models/graph_node.py`** (267 lines, Owner: Lê Trí Tiên):
   - Classes exported:
     - `GraphNode(BaseEntity)` (lines 73-145):
       - Constructor: `__init__(self, node_id: str, name: str, x: float, y: float)`.
       - Properties: `id` (read-only; setter raises `AttributeError`), `name` (non-empty str), `x` (finite float), `y` (finite float).
       - Methods: `distance_to(other: GraphNode) -> float` (Euclidean), `to_dict() -> dict[str, Any]`, `from_dict(cls, data: dict[str, Any]) -> GraphNode`.
       - *Note*: The class name is `GraphNode` (there is no class named `Node`).
     - `Graph` (lines 147-267):
       - Attributes: `_nodes: dict[str, GraphNode]`, `_adj: dict[str, list[tuple[str, float]]]`, `_scale: float | None`.
       - Methods & Properties: `__len__`, `__contains__`, `node_ids -> list[str]`, `nodes -> list[GraphNode]`, `has_node(node_id) -> bool`, `get_node(node_id) -> GraphNode` (raises `ValueError`), `neighbors(node_id) -> list[tuple[str, float]]`, `edges() -> list[tuple[str, str, float]]`, `euclidean_distance(a, b) -> float`, `heuristic_scale() -> float`, `add_node(node: GraphNode)`, `add_edge(u, v, weight, bidirectional=True)` (rejects weight < 0), `from_dict(cls, data: dict[str, Any], bidirectional=True) -> Graph`.

4. **`src/models/base.py`** (63 lines, Owner: Nguyễn Lê Đức Bảo):
   - Class `BaseEntity` (lines 18-63):
     - `__init__(self, id: str) -> None`: Validates non-empty string, sets `self._id = id.strip()`.
     - `@property id -> str` and `@id.setter id(self, new_id: str) -> None` (strips and validates).
     - `to_dict(self) -> dict[str, Any]`: Returns `{"id": self._id}`.
     - `@classmethod from_dict(cls, data: dict[str, Any]) -> BaseEntity`: Validates dict and presence of `"id"`, instantiates `cls(id=str(data["id"]))`.
     - `__repr__`, `__eq__` (exact type & `_id`), `__hash__`.

5. **`src/core/storage.py`** (106 lines, Owner: Nguyễn Lê Đức Bảo):
   - Constants: `PROJECT_ROOT`, `DEFAULT_DATA_DIR = PROJECT_ROOT / "data"`.
   - Functions:
     - `_resolve_path(path: str | Path) -> Path` (lines 24-38): Resolves paths against `data/` if bare filename or starting with `"data"`.
     - `load_json(path: str | Path, default: Any = None) -> Any` (lines 41-88):
       - Default falls back to `[]` if `default is None`.
       - Returns `copy.deepcopy(default)` if file does not exist, is not file, size == 0, or empty string after strip.
       - If `json.JSONDecodeError` or `UnicodeDecodeError`: renames file to `<name>.bak` via `os.replace` and returns `copy.deepcopy(default)`.
     - `save_json(path: str | Path, data: Any) -> None` (lines 90-106):
       - Saves formatted UTF-8 JSON (`indent=2`, `ensure_ascii=False`).

6. **`src/core/structures.py`** (291 lines, Owner: Nguyễn Vũ Băng Tâm):
   - Classes:
     - `CustomMinHeap(Generic[T])` (lines 17-103): Built on list. Methods: `push` (O(log n)), `pop` (O(log n)), `peek` (O(1)), `is_empty` (O(1)), `__len__` (O(1)).
     - `CustomPriorityQueue(Generic[T])` (lines 105-164): Built on `CustomMinHeap` of `(priority_key, counter, item)`. Methods: `enqueue` (O(log n)), `dequeue` (O(log n)), `peek` (O(1)), `is_empty` (O(1)), `to_list` (O(n log n)), `__len__` (O(1)).
     - `SortedIndex` (lines 167-255): Maintains sorted list of `(norm_key, item_id)` where `norm_key = str(key).strip().lower()`.
       - Methods:
         - `_bisect_left_pair(target: tuple[str, str]) -> int`: Custom binary search on pair.
         - `_bisect_left_key(norm_key: str) -> int`: Custom binary search on normalized key.
         - `insert(key: str, item_id: str) -> None`: O(log n) find + O(n) insert. Ignores duplicates.
         - `remove(key: str, item_id: str) -> bool`: O(log n) find + O(n) pop. Returns True/False.
         - `find_all(key: str) -> list[str]`: O(log n) binary search + O(k) linear scan of matching keys. Returns list of `item_id`.
         - `clear() -> None`, `is_empty() -> bool`, `__len__() -> int`.
     - `CustomStack` (lines 258-291): Custom LIFO stack on list. Methods: `push`, `pop`, `peek`, `is_empty`, `__len__`, `clear`. All operations O(1).

7. **`src/core/menu_manager.py`** (257 lines, Owner: Nguyễn Lê Đức Bảo):
   - Class `MenuManager`:
     - Internal attributes: `file_path`, `_items: dict[str, MenuItem]` (primary index O(1)), `name_index: SortedIndex` (secondary index O(log n) + O(k)).
     - Methods: `load()` (loads JSON or populates 6 default items and saves), `save()`, `get_all() -> list[MenuItem]`, `get_by_id(id) -> MenuItem | None`, `next_id() -> str`, `add_item(...) -> MenuItem`, `update_item(...) -> MenuItem`, `delete_item(id) -> bool`, `search_by_name(name) -> list[MenuItem]`.

### 1.3 Prohibited Libraries Inspection
Executed ripgrep query:
```
pattern: (import|from)\s+(heapq|bisect|queue|networkx|collections)
target: D:\Module 1\src and D:\Module 1\tests
```
- Results: 0 matches found in `src/` and 0 matches found in `tests/`.
- Additional query for occurrences of token names (`heapq`, `deque`, `bisect`, `queue`, `networkx`, `collections`):
  - Only present in docstrings (e.g. `src/core/structures.py:6` "Chỉ dùng list, dict, set, tuple (cấm heapq, deque, bisect, queue)") and custom method names (`_bisect_left_pair`, `CustomPriorityQueue.enqueue`).
  - No banned library is imported or used.

### 1.4 Code Inspection of Target Modification / Creation Files
1. **`src/models/menu_item.py`** (157 lines):
   - Lines 14-17 currently contain:
     ```python
     try:
         from models.base import BaseEntity
     except ModuleNotFoundError:
         from src.models.base import BaseEntity
     ```
   - Must be simplified to: `from src.models.base import BaseEntity`.
2. **`src/core/routing_service.py`** (46 lines):
   - Currently imports `from typing import Any, List, Tuple, Dict`.
   - Contains only `path_to_coordinates` and `get_map_render_data`.
   - Missing: `RESTAURANT_NODE_ID`, `MAP_PATH`, `MapDataError`, `load_map_graph` (with 6 Vietnamese error cases), `is_valid_delivery_node`, `SingleRoute`, `route_single_order`, `RouteLeg`, `BatchRoute`, `plan_batch_route` (Nearest-Neighbor O(k^2 (V+E) log V)), `compare_trip_algorithms`, and `build_map_figure_data`.
3. **`src/core/order_manager.py`** (251 lines):
   - Current attributes: public `orders`, `name_index`, `email_index`, `undo_stack`, `redo_stack`.
   - `create_order` takes `shipper_status: str`.
   - `load_orders` has no per-record exception handling (`ValueError`, `KeyError`, `TypeError`).
   - Missing: private encapsulation (`_orders`, `_name_index`, `_email_index`, `_undo_stack`, `_redo_stack`, `_graph`), `orders` read-only property returning dict copy, `get_order`, `get_all_orders`, `can_undo`, `can_redo`, `get_shipper_status` (BUSY if any DELIVERING else IDLE), `get_current_trip`, `start_delivery` (atomic batching), `complete_delivery` (single order completion to PAID), PriorityEngine validation in `update_order_status` for CONFIRMED -> PREPARING, blocking manual transitions into DELIVERING.
4. **Missing Files to be Created**:
   - `src/models/customer.py`: `Customer(BaseEntity)` with `_name`, `_email`, `_is_vip`, `_node_id`, validation, `to_dict`, `from_dict`.
   - `src/core/customer_manager.py`: `CustomerManager` (read-only), `load_errors`, `SortedIndex` lookups for name and email.
   - `tests/test_customer_manager.py`: Test suite for `CustomerManager`.
   - `tests/test_routing_service.py`: Test suite for `routing_service`.
5. **Data Files State**:
   - `data/map_graph.json`: Contains 4 template nodes (`RESTAURANT`, `A`, `B`, `C`) and 5 edges. Needs update to 8 nodes (6 mentor + 2 customer nodes `CUSTOMER_2`, `CUSTOMER_3`) and 12 bidirectional edges.
   - `data/users.json`: Contains 2 template users (`U001`, `U002`). Needs update to 4 users (`U001`, `U002`, `U003`, `U004`).

---

## 2. Logic Chain

1. **Baseline Integrity Established**:
   - Observation: Running `uv run python -m unittest discover -s tests -t .` in `D:\Module 1` executed 20 tests with 0 failures, 0 errors, and 0 warnings.
   - Inference: The existing codebase is fully functional in its initial state, providing a stable regression baseline before modifications.

2. **Core Invariant Compliance**:
   - Observation: `git diff --stat` against the 7 core files produced no diff, and regex grep for prohibited libraries (`collections`, `deque`, `heapq`, `bisect`, `queue`, `networkx`) returned 0 import lines.
   - Inference: The system conforms strictly to the rule prohibiting external or standard data structure libraries. All 7 core files are completely untouched and must remain protected throughout all subsequent stages.

3. **Routing Algorithm & Priority Engine Integration Feasibility**:
   - Observation: `dijkstra` and `a_star` in `src/core/routing_algo.py` take `(graph, start, goal)` and return `RouteResult(path, cost, expanded)`. `PriorityEngine.next_order` in `src/core/priority_engine.py` takes `(orders, now)` and returns the top priority `OrderLike` object via `CustomPriorityQueue`.
   - Inference:
     - `plan_batch_route` in `routing_service.py` can directly invoke `dijkstra` or `a_star` without reimplementing graph algorithms.
     - `update_order_status` in `order_manager.py` can directly call `PriorityEngine().next_order(confirmed_orders, now=time.time())` to enforce kitchen scheduling priority before allowing transition from `CONFIRMED` to `PREPARING`.

4. **Data Model & Encapsulation Requirements**:
   - Observation: Currently `OrderManager` directly exposes mutable state (`orders`, `undo_stack`, `redo_stack`) and expects `shipper_status` in `create_order`, while `src/app.py` directly references `om.orders` and `om.undo_stack`.
   - Inference: Encapsulating `_orders` with a read-only property returning a copy, adding `can_undo()`, `can_redo()`, `get_all_orders()`, and deriving shipper status from active `DELIVERING` orders will fulfill requirements R3 and R4 while cleanly decoupling the UI from internal manager structures.

5. **Customer Module Separation**:
   - Observation: There are currently no customer classes in `src/models/` or `src/core/`, yet `data/users.json` exists.
   - Inference: Implementing `Customer(BaseEntity)` and `CustomerManager` backed by `SortedIndex` cleanly mirrors the architectural pattern set by `MenuItem` and `MenuManager`.

---

## 3. Caveats

1. **Working Directory for Shell Commands**:
   - Commands executed via PowerShell must explicitly set directory (`Set-Location "D:\Module 1"`) or run within `D:\Module 1`, otherwise PowerShell starts in the Antigravity default folder and fails to locate `tests`.
2. **Current vs Standard Data**:
   - `data/map_graph.json` and `data/users.json` currently hold template starter data (4 nodes, 2 users). As required by R1, they should be updated with the standard 8-node map and 4 users during the implementation phase.
3. **No Code Modified During Survey**:
   - In accordance with the Explorer subagent constraints, this survey is 100% read-only. No source files, tests, or data files were modified.

---

## 4. Conclusion

- The baseline codebase is in a clean, working state (20/20 tests passing).
- All 7 core files (`routing_algo.py`, `priority_engine.py`, `graph_node.py`, `base.py`, `storage.py`, `structures.py`, `menu_manager.py`) are strictly intact and contain zero banned library imports.
- The interface contracts for `routing_algo` (`dijkstra`, `a_star`, `RouteResult`) and `priority_engine` (`PriorityEngine.next_order`, `compute_priority`) are fully mapped and ready for consumption by `routing_service.py` and `order_manager.py`.
- The exact specifications for modifying `menu_item.py`, `routing_service.py`, `order_manager.py`, and creating `customer.py` / `customer_manager.py` have been verified against existing code structures.

---

## 5. Verification Method

To independently verify all findings in this report:

1. **Verify Baseline Tests**:
   ```powershell
   Set-Location "D:\Module 1"; uv run python -m unittest discover -v -s tests -t .
   ```
   *Expected*: Exactly 20 tests run, 0 failures, 0 errors, status OK.

2. **Verify 7 Core Files Untouched**:
   ```powershell
   Set-Location "D:\Module 1"; git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   *Expected*: Empty output (0 diff lines).

3. **Verify Prohibited Libraries Compliance**:
   ```powershell
   Set-Location "D:\Module 1"; uv run python -c "import re, glob; patterns = [re.compile(r'^\s*(import|from)\s+(heapq|bisect|queue|networkx|collections)\b', re.M)]; files = glob.glob('src/**/*.py', recursive=True); hits = [f for f in files if any(p.search(open(f, encoding='utf-8').read()) for p in patterns)]; print('Banned hits:', hits)"
   ```
   *Expected*: `Banned hits: []`.

4. **Inspect Files Referenced**:
   - `src/core/routing_algo.py`: lines 33-49 (`RouteResult`), lines 109-126 (`dijkstra`, `a_star`).
   - `src/core/priority_engine.py`: lines 112-120 (`next_order`).
   - `src/models/graph_node.py`: line 73 (`GraphNode`), line 147 (`Graph`).
   - `src/models/base.py`: line 18 (`BaseEntity`).
   - `src/core/storage.py`: line 41 (`load_json`), line 90 (`save_json`).
   - `src/core/structures.py`: line 17 (`CustomMinHeap`), line 105 (`CustomPriorityQueue`), line 167 (`SortedIndex`), line 258 (`CustomStack`).
   - `src/core/menu_manager.py`: line 20 (`MenuManager`).
   - `src/models/menu_item.py`: lines 14-17 (fallback try/except import).
