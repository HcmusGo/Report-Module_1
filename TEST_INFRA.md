# E2E Test Infra: Connect Routing & Order Management

## Test Philosophy
- Opaque-box, requirement-driven. Derived from `ORIGINAL_REQUEST.md` and user-facing specifications.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial + Real-World Workload Testing.

## Feature Inventory & Test Coverage Goals
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Standard Map & User Datasets | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | `load_map_graph` (6 discrete error cases) | ORIGINAL_REQUEST §R2 | 6 | 6 | ✓ |
| 3 | `is_valid_delivery_node` | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 4 | `route_single_order` | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 5 | `plan_batch_route` (nearest-neighbor & tie-break) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 6 | `compare_trip_algorithms` | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 7 | `build_map_figure_data` | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 8 | `Customer` model & validation | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 9 | `CustomerManager` (read-only & SortedIndex) | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 10 | `OrderManager` encapsulation & copy-on-read | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 11 | Derived shipper status (BUSY/IDLE) | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 12 | `create_order` validations & rejection messages | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 13 | `start_delivery` atomic batch & snapshot undo | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 14 | `complete_delivery` & automatic IDLE flip | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 15 | `update_order_status` guardrails (DELIVERING & Priority) | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 16 | `load_orders` safe corrupt entry handling | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| 17 | Streamlit AppTest smoke tests | ORIGINAL_REQUEST §R5 | 4 | 4 | ✓ |

## Test Architecture
- Test runner: `uv run python -m unittest discover -s tests -t .`
- Test case format: Python `unittest.TestCase` using temporary isolated directories and in-memory mock data (never polluting production `data/` or mutating core files).
- Directory layout:
  - `tests/test_routing_service.py`
  - `tests/test_order_manager.py`
  - `tests/test_customer_manager.py`
  - `tests/test_app_smoke.py`

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Standard 3-order batch delivery on 8-node map: U001, U002, U003 -> CONFIRMED -> Priority preparation order -> READY -> batch route calculation (16.0 km) -> start_delivery (BUSY) -> create_order rejected -> complete deliveries -> auto IDLE -> single undo reverts to READY. | F1-F16 | High |
| 2 | Out-of-order kitchen preparation attempt: Normal order waiting attempted before VIP order -> rejected by PriorityEngine guard with explicit top order name. | F10, F15 | Medium |
| 3 | Corrupt data resilience: orders.json containing invalid/truncated records -> loaded safely without crash, error logged to load_errors. | F16 | Medium |
| 4 | Map file corruption: map.json replaced with syntax error -> .bak notification triggered, OrderManager loads without crash, create_order informs map unavailable. | F2, F10, F12 | High |
| 5 | Streamlit AppTest smoke flow: Initial render -> verify Order and Map tabs -> simulate order creation -> verify reactive rendering. | F17 | High |
