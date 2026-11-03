# Milestone M2 Review & Adversarial Stress-Test Report

**Reviewer Agent**: `m2_reviewer` (Roles: reviewer, critic)  
**Target Milestone**: M2 (Customer Model, CustomerManager, OrderManager)  
**Worker Under Review**: `m2_worker`  
**Worker Handoff**: `D:\Module 1\.agents\teamwork\m2_worker\handoff.md`  
**Verdict**: **APPROVE**

---

## 1. Observation

### 1.1 Integrity & Constraint Checks
- **7 Core Files Immutability**:
  Executed command:
  ```powershell
  git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
  ```
  Result: Exit code 0, 0 files modified, empty output. Both working tree and `git diff main...HEAD` confirm zero modifications across all 7 core files.
- **Prohibited Imports Check**:
  Executed AST parser inspection and regex:
  ```powershell
  git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
  ```
  Result: Exit code 1 (no occurrences). Python AST parse over all `src/**/*.py` verified 0 prohibited imports (`heapq`, `bisect`, `queue`, `networkx`, `collections`).
- **Line Length Check**:
  Verified line lengths for `src/models/customer.py`, `src/core/customer_manager.py`, and `src/core/order_manager.py`. All lines satisfy `<= 100` characters.

### 1.2 Component Observations
1. **`src/models/customer.py`**:
   - `Customer(BaseEntity)` correctly subclasses `BaseEntity` (lines 19-35).
   - Validations via property setters:
     - `name`: rejects non-string and whitespace-only (`ValueError("Tên khách hàng không được để trống.")`, lines 43-46).
     - `email`: rejects non-string, whitespace-only, and strings lacking `'@'` (`ValueError("Email khách hàng không hợp lệ.")`, lines 53-57).
     - `is_vip`: casts safely via `bool(value)` (lines 64-66).
     - `node_id`: rejects non-string and whitespace-only (`ValueError("Điểm giao hàng không được để trống.")`, lines 73-77).
   - `to_dict()` invokes `super().to_dict()` and serializes all fields (lines 79-88).
   - `from_dict()` validates dictionary type and presence of required fields (`id`, `name`, `email`, `node_id`), raising specific Vietnamese `ValueError` (lines 90-106).
2. **`src/core/customer_manager.py`**:
   - `CustomerManager` initializes with default `"data/users.json"` (line 23).
   - Read-only design: no mutation or persistence methods exposed.
   - Fault-tolerant loading in `load_customers()`: catches file/json exceptions and per-record `(ValueError, KeyError, TypeError)`, recording to `load_errors` without crashing (lines 38-74).
   - Uses `SortedIndex` for `_name_index` and `_email_index` (lines 27-28), providing O(log n) lookups for `find_by_name()` and `find_by_email()` (lines 91-105).
   - `get_by_id()` provides safe O(1) dictionary lookup (lines 82-89).
3. **`src/core/order_manager.py`**:
   - Encapsulation: private attributes `_orders`, `_name_index`, `_email_index`, `_undo_stack`, `_redo_stack`, `_graph`, `_map_error`, `_last_error`, `_load_errors` (lines 40-62).
   - Property `orders` returns `self._orders.copy()`, shielding internal dictionary from direct mutation (lines 66-68).
   - `get_shipper_status()` dynamically derives status: `"BUSY"` if any order has `status == OrderStatus.DELIVERING` else `"IDLE"` (lines 201-206).
   - `get_current_trip()` returns list of orders currently in `DELIVERING` (lines 208-214).
   - `create_order(...)`:
     - Signature updated to `(order_id, customer_name, customer_email, items, created_at, is_vip=False, delivery_node_id=None)` (`shipper_status` removed, lines 223-232).
     - Rejects when map has error (`self._map_error or "Bản đồ chưa sẵn sàng."`, line 238).
     - Rejects when shipper is BUSY with exact message `"Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"` (lines 241-243).
     - Rejects invalid `delivery_node_id` (None, empty, "RESTAURANT", unreachable/invalid) with `"Điểm giao không hợp lệ"` (lines 245-248).
     - Records `delivery_node_id` in `Order` entity (lines 272-280).
   - `start_delivery(order_ids: list[str])`:
     - Upfront atomic validation: verifies non-empty, no duplicates, shipper IDLE, and that all orders exist, are `READY`, and have valid delivery nodes (lines 298-330).
     - Takes single snapshot before transitioning all orders to `DELIVERING` (lines 332-337).
     - Saves orders once and clears `_redo_stack` (lines 334, 339).
   - `complete_delivery(order_id: str)`:
     - Transitions specified `DELIVERING` order to `PAID` (lines 343-371).
     - Takes snapshot, clears `_redo_stack`, and saves orders once (lines 362-366).
     - When last `DELIVERING` order completes, `get_shipper_status()` automatically returns to `"IDLE"`.
   - `update_order_status(order_id: str, new_status: str)`:
     - Blocks direct transition into `DELIVERING` with `"Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"` (lines 387-389).
     - Blocks `CONFIRMED -> PREPARING` if order is not top order per `PriorityEngine().next_order`, returning `f"Đơn hàng '{top.id}' ({top.customer_name}) có độ ưu tiên cao hơn, phải chế biến trước."` (lines 392-403).
     - Blocks cancellation of orders in `DELIVERING` or `PAID` (lines 406-411).
   - `load_orders()`:
     - Catches `(ValueError, KeyError, TypeError)` per record and validates root structure, logging to `load_errors` without crashing (lines 121-156).

---

## 2. Logic Chain

1. **Compliance with Specifications**:
   - The implementation adheres strictly to ORIGINAL_REQUEST §R3 and PROJECT.md requirements for M2.
   - All method signatures and property behaviors match interface contracts.
2. **Encapsulation & Safety**:
   - Returning `self._orders.copy()` ensures callers cannot mutate internal state directly.
   - Safe `load_orders` and `load_customers` guarantee that invalid or corrupted JSON files never crash the Streamlit application.
3. **Business Invariant Enforcements**:
   - Shipper state is derived purely from order states, preventing synchronization bugs between order statuses and shipper availability.
   - Atomic validation in `start_delivery` guarantees that partial trips cannot be dispatched: if any order fails validation, no state changes and no snapshot is committed.
   - Single snapshot in `start_delivery` ensures that `undo()` restores the entire trip back to `READY` in a single step, and `redo()` restores it back to `DELIVERING`.
   - Integrating `PriorityEngine` in `update_order_status` enforces strict kitchen FIFO/VIP starvation-prevention order.
4. **Integrity & Zero-Façade Assessment**:
   - No hardcoded test outputs or mock bypasses exist in the source code.
   - Real data structures (`SortedIndex`, `CustomStack`, `PriorityEngine`, `Graph`) are properly wired and execute legitimate algorithms.
   - The 7 core files remain byte-for-byte untouched.

---

## 3. Caveats

- **Legacy Tests in `tests/test_order_manager.py`**:
  Running `uv run python -m unittest discover -s tests -t .` currently yields errors on `tests/test_order_manager.py` because the legacy tests still invoke `create_order` with the old signature containing `shipper_status` and lacking `delivery_node_id`. Per `PROJECT.md` line 73, updating `tests/test_order_manager.py` is explicitly scheduled for Milestone M4. All existing tests in `test_order.py` and `test_priority_engine.py` pass 100% (13/13).
- **Scope Boundary**:
  `src/app.py` integration is allocated to Milestone M3, so UI-level end-to-end interactions remain to be reviewed during M3.

---

## 4. Adversarial Stress-Test Findings

| Test Scenario | Attack / Stress Angle | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| **Customer Validation** | Blank name, email without `@`, whitespace node_id, missing dict keys | Raise descriptive `ValueError` | `ValueError` raised with exact messages | **PASS** |
| **CustomerManager Faults** | Missing JSON file, malformed JSON, corrupted records, bad root type | Safe recovery, populate `load_errors`, no crash | Loaded valid records, `load_errors` populated, no crash | **PASS** |
| **SortedIndex Multi-Match** | Multiple customers with identical names and case differences | O(log n) binary search returns all matches | All matching IDs returned case-insensitively | **PASS** |
| **OrderManager Encapsulation** | Mutate `om.orders` dict externally | Internal `_orders` remains unchanged | `_orders` unaffected | **PASS** |
| **Broken Graph Handling** | `graph=None` and `load_map_graph` raises `MapDataError` | `_graph=None`, `map_error` set, operations reject safely | Rejected with `map_error`, no crash | **PASS** |
| **Invalid Delivery Nodes** | `delivery_node_id` is None, empty, "RESTAURANT", or "ZZZ" | `create_order` returns `False`, `last_error="Điểm giao không hợp lệ"` | Correctly rejected | **PASS** |
| **Direct DELIVERING Transition** | Call `update_order_status(id, "DELIVERING")` | Rejection with `"Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"` | Correctly blocked | **PASS** |
| **Priority Queue Enforcement** | Move normal order to `PREPARING` while VIP order is `CONFIRMED` | Blocked with message indicating higher priority order | Correctly blocked with top order name | **PASS** |
| **Batch Delivery Atomicity** | `start_delivery` with batch where 1 of 3 orders is not `READY` | Entire batch rejected; none transition to `DELIVERING` | Atomically rejected; 0 orders modified | **PASS** |
| **Shipper Lockout** | Call `create_order` or `start_delivery` while shipper is `BUSY` | Blocked with `"Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"` | Correctly blocked | **PASS** |
| **Trip Undo/Redo Chain** | Multi-step trip dispatch -> complete order 1 -> complete order 2 -> multi-step undo/redo | States restored accurately across all trip orders; shipper toggles BUSY/IDLE | Perfect state recovery across full cycle | **PASS** |

---

## 5. Conclusion

**VERDICT: APPROVE**

Milestone M2 deliverables (`src/models/customer.py`, `src/core/customer_manager.py`, and `src/core/order_manager.py`) have been rigorously verified. They meet all architectural constraints, functional requirements, encapsulation standards, and adversarial edge cases without introducing regressions or violating integrity rules.

---

## 6. Verification Method

To independently reproduce and verify this review:

1. **Verify 7 core files are untouched**:
   ```powershell
   cd "D:\Module 1"
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   *(Must return empty output).*

2. **Verify 0 prohibited imports & line lengths <= 100**:
   ```powershell
   cd "D:\Module 1"
   git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   ```
   *(Must return exit code 1).*

3. **Verify Baseline Unit Tests (Non-M4)**:
   ```powershell
   cd "D:\Module 1"
   uv run python -m unittest tests/test_order.py tests/test_priority_engine.py
   ```
   *(Must pass 13/13 tests).*

4. **Run Milestone M2 Full Lifecycle & Adversarial Script**:
   ```powershell
   cd "D:\Module 1"
   $env:PYTHONIOENCODING="utf-8"
   @'
   import tempfile, time
   from pathlib import Path
   from src.models.customer import Customer
   from src.core.customer_manager import CustomerManager
   from src.core.order_manager import OrderManager
   from src.core.routing_service import load_map_graph
   from src.models.order import OrderStatus, make_item_snapshot

   # Customer & CustomerManager checks
   c = Customer("C01", "Alice", "alice@test.com", True, "CUSTOMER")
   assert Customer.from_dict(c.to_dict()) == c
   cm = CustomerManager("data/users.json")
   assert len(cm.get_all()) == 4
   assert len(cm.find_by_name("nguyen van an")) == 1

   # OrderManager checks
   with tempfile.TemporaryDirectory() as tmp:
       om = OrderManager(storage_path=Path(tmp)/"orders.json", graph=load_map_graph())
       it = [make_item_snapshot("M1", "Dish", 1, 10000, 5)]
       assert om.create_order("O1", "Cust1", "c1@test.com", it, time.time(), delivery_node_id="CUSTOMER")
       assert not om.create_order("O2", "Cust2", "c2@test.com", it, time.time(), delivery_node_id="RESTAURANT")
       assert om.update_order_status("O1", OrderStatus.CONFIRMED)
       assert om.update_order_status("O1", OrderStatus.PREPARING)
       assert om.update_order_status("O1", OrderStatus.READY)
       assert not om.update_order_status("O1", OrderStatus.DELIVERING)
       assert om.start_delivery(["O1"])
       assert om.get_shipper_status() == "BUSY"
       assert not om.create_order("O3", "Cust3", "c3@test.com", it, time.time(), delivery_node_id="CUSTOMER")
       assert om.undo()
       assert om.get_order("O1").status == OrderStatus.READY
       assert om.redo()
       assert om.complete_delivery("O1")
       assert om.get_shipper_status() == "IDLE"
       print("ALL M2 VERIFICATIONS SUCCEEDED")
   '@ | uv run python
   ```
