# Project: Connect Routing & Order Management

## Architecture
The system integrates an order management and kitchen prioritization workflow with a single-shipper delivery routing engine for "1 Restaurant - 1 Shipper".

### Data Flow & Component Interaction
```
[ users.json ] ───> [ CustomerManager ]
                            │ (Customer info, VIP, delivery node)
                            ▼
[ MenuManager ] ───> [ OrderManager ] <─── [ PriorityEngine ] (Kitchen queue priority)
                            │
                            ▼ (Map loading, node validation, single & batch routing)
[ map_graph.json ] ─> [ routing_service ] <─── [ routing_algo ] (dijkstra, a_star)
                            │
                            ▼
                     [ src/app.py ] (Streamlit UI: Order Tab, Kitchen Tab, Map Tab)
                            │
                            ▼ (Altair 3-layer map rendering)
                     [ User Interface ]
```

### Core Integrity Constraints
- 7 Core Files (STRICTLY UNMODIFIED):
  1. `src/core/routing_algo.py`
  2. `src/core/priority_engine.py`
  3. `src/models/graph_node.py`
  4. `src/models/base.py`
  5. `src/core/storage.py`
  6. `src/core/structures.py`
  7. `src/core/menu_manager.py`
- Prohibited Libraries (STRICT ZERO-IMPORT): `collections/deque`, `heapq`, `bisect`, `queue`, `networkx`.
- Dependency lock: No edits to `pyproject.toml` or `uv.lock`.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Standard Map Data | 8 nodes (RESTAURANT, A, B, C, D, CUSTOMER, CUSTOMER_2, CUSTOMER_3), 12 bidirectional edges with exact coordinates and weights | M0 | ORIGINAL_REQUEST §R1 |
| 2 | Standard User Data | 4 users (U001 to U004) with VIP flags and delivery node IDs | M0 | ORIGINAL_REQUEST §R1 |
| 3 | Menu Item Import Fix | Replace fallback try/except in `src/models/menu_item.py` with `from src.models.base import BaseEntity` | M0 | ORIGINAL_REQUEST §R5 |
| 4 | Map Loading & 6 Vietnamese Error Cases | `load_map_graph` raises `MapDataError` distinguishing 6 failure cases (nonexistent, empty, syntax error with .bak, missing nodes, missing RESTAURANT, Graph.from_dict ValueError) | M1 | ORIGINAL_REQUEST §R2 |
| 5 | Delivery Node Validation | `is_valid_delivery_node` checks node presence, non-restaurant, and reachable from Quán | M1 | ORIGINAL_REQUEST §R2 |
| 6 | Single Order Route | NamedTuple `SingleRoute` and `route_single_order` from Quán to delivery node | M1 | ORIGINAL_REQUEST §R2 |
| 7 | Batch Route Planning | Nearest-Neighbor `plan_batch_route` with tie-breaking, non-repeating path joining, expanded_total semantics, O(k^2 (V+E) log V) annotation | M1 | ORIGINAL_REQUEST §R2 |
| 8 | Trip Algorithm Comparison | `compare_trip_algorithms` comparing Dijkstra vs A* on batch delivery points | M1 | ORIGINAL_REQUEST §R2 |
| 9 | Map Visualization Data Exporter | `build_map_figure_data` preparing nodes, edges, and ordered route frames for Altair | M1 | ORIGINAL_REQUEST §R2 |
| 10 | Customer Model | `Customer(BaseEntity)` with encapsulated fields, validation, and dict serialization | M2 | ORIGINAL_REQUEST §R3 |
| 11 | Customer Manager | Read-only `CustomerManager` with O(log n) `SortedIndex` lookups and safe `load_errors` handling | M2 | ORIGINAL_REQUEST §R3 |
| 12 | Order Manager Encapsulation | Private fields, copy-on-read `orders`, `get_order`, `get_all_orders`, `can_undo`, `can_redo` | M2 | ORIGINAL_REQUEST §R3 |
| 13 | Derived Shipper Status | `get_shipper_status` ("BUSY" if any DELIVERING else "IDLE") and `get_current_trip` | M2 | ORIGINAL_REQUEST §R3 |
| 14 | Order Creation Guardrails | `create_order` rejects on map error, shipper BUSY, invalid delivery node, and records node ID | M2 | ORIGINAL_REQUEST §R3 |
| 15 | Atomic Batch Delivery | `start_delivery` atomically transitions valid READY orders to DELIVERING with a single snapshot | M2 | ORIGINAL_REQUEST §R3 |
| 16 | Single Delivery Completion | `complete_delivery` transitions order to PAID, automatically resets shipper to IDLE on last order | M2 | ORIGINAL_REQUEST §R3 |
| 17 | Priority Queue & State Guardrails | `update_order_status` blocks direct transition into DELIVERING and enforces `PriorityEngine` order for CONFIRMED -> PREPARING | M2 | ORIGINAL_REQUEST §R3 |
| 18 | Safe Order Loading | `load_orders` catches ValueError, KeyError, TypeError, logs to `load_errors` without crashing | M2 | ORIGINAL_REQUEST §R3 |
| 19 | Reactive Order Tab UI | Unnested widgets, customer selectbox, read-only details, immediate item quantities, shipper banner | M3 | ORIGINAL_REQUEST §R4 |
| 20 | Delivery Dispatch Map Tab UI | Ready order table, batch planning display, algorithm comparison table, start delivery button, active trip management, 3-layer Altair chart | M3 | ORIGINAL_REQUEST §R4 |
| 21 | Test Suite & Regression Verification | Comprehensive unit tests for `routing_service`, `order_manager`, `customer_manager`, and Streamlit AppTest smoke tests | M4 | ORIGINAL_REQUEST §R5 |
| 22 | Documentation & CODEOWNERS | Update `README.md` with 7-step business demo and add `.github/CODEOWNERS` entries | M5 | ORIGINAL_REQUEST §R5 |
| 23 | Git Branch & Part Commits | Create branch `feat/connect-routing-order` and commit parts 1-8 with standard prefixes | M5 | ORIGINAL_REQUEST §R5 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Baseline Check & Data Setup | Git branch `feat/connect-routing-order`, verify baseline tests, overwrite `data/map_graph.json` and `data/users.json` with standard 8-node map and 4 users, fix `src/models/menu_item.py` import | none | DONE |
| M1 | Routing Service (`routing_service.py`) | Implement `routing_service.py` with 6-error `load_map_graph`, `is_valid_delivery_node`, `SingleRoute`, `route_single_order`, `RouteLeg`, `BatchRoute`, `plan_batch_route`, `compare_trip_algorithms`, `build_map_figure_data` | M0 | DONE |
| M2 | Customer & Order Management | Implement `src/models/customer.py`, `src/core/customer_manager.py`, and refactor `src/core/order_manager.py` with encapsulation, derived shipper status, `start_delivery`, `complete_delivery`, `update_order_status` guards, safe `load_orders` | M1 | DONE |
| M3 | Streamlit UI (`src/app.py`) | Refactor `src/app.py` Order Tab and Map Tab: unnested reactive widgets, Altair 3-layer visualization, remove `st.line_chart`, remove direct file/Graph access | M2 | DONE |
| M4 | Comprehensive Testing & Verification | Implement unit tests in `tests/test_routing_service.py`, `tests/test_customer_manager.py`, update `tests/test_order_manager.py`, add Streamlit `AppTest` smoke test | M3 | DONE |
| M5 | Docs, CODEOWNERS, Git Commits & Final Acceptance | Add 7-step demo to `README.md`, update `.github/CODEOWNERS`, verify acceptance criteria, produce part-by-part Git commits on `feat/connect-routing-order` | M4 | DONE |

---

## Interface Contracts

### `src/core/routing_service.py`
```python
RESTAURANT_NODE_ID: str = "RESTAURANT"
MAP_PATH: str = "data/map_graph.json"

class MapDataError(Exception):
    pass

class SingleRoute(NamedTuple):
    delivery_node_id: str
    path: list[str]
    coords: list[tuple[float, float]]
    cost: float
    expanded: int

class RouteLeg(NamedTuple):
    start: str
    end: str
    path: list[str]
    cost: float

class BatchRoute(NamedTuple):
    visit_order: list[str]
    legs: list[RouteLeg]
    full_path: list[str]
    coords: list[tuple[float, float]]
    total_cost: float
    expanded_total: int
    algorithm: str

def load_map_graph(path: str = MAP_PATH) -> Graph: ...
def is_valid_delivery_node(graph: Graph, node_id: str) -> bool: ...
def route_single_order(graph: Graph, delivery_node_id: str, algorithm: str = "dijkstra") -> SingleRoute: ...
def plan_batch_route(graph: Graph, delivery_node_ids: list[str], algorithm: str = "dijkstra") -> BatchRoute: ...
def compare_trip_algorithms(graph: Graph, delivery_node_ids: list[str]) -> dict[str, BatchRoute]: ...
def build_map_figure_data(graph: Graph, full_path: list[str] | None = None) -> dict[str, Any]: ...
def path_to_coordinates(path: list[str], graph: Graph) -> list[tuple[float, float]]: ...
def get_map_render_data(graph: Graph, start_id: str, goal_id: str) -> dict[str, Any]: ...
```

### `src/models/customer.py`
```python
class Customer(BaseEntity):
    def __init__(self, id: str, name: str, email: str, is_vip: bool, node_id: str) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def email(self) -> str: ...
    @property
    def is_vip(self) -> bool: ...
    @property
    def node_id(self) -> str: ...
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Customer: ...
```

### `src/core/customer_manager.py`
```python
class CustomerManager:
    def __init__(self, storage_path: str | Path = "data/users.json") -> None: ...
    @property
    def load_errors(self) -> list[str]: ...
    def get_all(self) -> list[Customer]: ...
    def get_by_id(self, customer_id: str) -> Customer | None: ...
    def find_by_name(self, name: str) -> list[Customer]: ...
    def find_by_email(self, email: str) -> list[Customer]: ...
```

### `src/core/order_manager.py`
```python
class OrderManager:
    def __init__(self, storage_path: str | Path = "data/orders.json", graph: Graph | None = None) -> None: ...
    @property
    def orders(self) -> dict[str, Order]: ...  # shallow copy
    @property
    def map_error(self) -> str: ...
    @property
    def last_error(self) -> str: ...
    @property
    def load_errors(self) -> list[str]: ...
    def get_order(self, order_id: str) -> Order | None: ...
    def get_all_orders(self) -> list[Order]: ...
    def can_undo(self) -> bool: ...
    def can_redo(self) -> bool: ...
    def get_shipper_status(self) -> str: ...  # "BUSY" or "IDLE"
    def get_current_trip(self) -> list[Order]: ...
    def create_order(self, order_id: str, customer_name: str, customer_email: str, items: list[Any], created_at: float, is_vip: bool = False, delivery_node_id: str | None = None) -> bool: ...
    def start_delivery(self, order_ids: list[str]) -> bool: ...
    def complete_delivery(self, order_id: str) -> bool: ...
    def update_order_status(self, order_id: str, new_status: str) -> bool: ...
    def undo(self) -> bool: ...
    def redo(self) -> bool: ...
    def load_orders(self) -> None: ...
    def save_orders(self) -> None: ...
```

---

## Code Layout
- `data/map_graph.json`: 8 nodes, 12 bidirectional edges.
- `data/users.json`: 4 customer records.
- `src/models/menu_item.py`: cleaned import statement.
- `src/models/customer.py`: Customer entity.
- `src/core/customer_manager.py`: Customer manager repository.
- `src/core/routing_service.py`: Routing service layer.
- `src/core/order_manager.py`: Order manager and shipper state engine.
- `src/app.py`: Streamlit front-end.
- `tests/test_routing_service.py`: Routing service test suite.
- `tests/test_customer_manager.py`: Customer manager test suite.
- `tests/test_order_manager.py`: Order manager updated test suite.
- `.github/CODEOWNERS`: GitHub ownership mappings.
- `README.md`: Business guide & documentation.
