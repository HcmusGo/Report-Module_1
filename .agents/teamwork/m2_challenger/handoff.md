# Adversarial Challenge & Stress Test Report — Milestone M2: Customer & Order Management

**Verdict**: **APPROVE**  
**Overall Risk Assessment**: **LOW**

---

## 1. Observation

All empirical tests and inspections were performed directly by `m2_challenger` in workspace `D:\Module 1`.

### Observation 1: Architectural Integrity & Constraints Check
1. **7 Core Files Diff Check**:
   - Command:
     ```powershell
     cd 'D:\Module 1'; git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
     ```
   - Verbatim Output: Empty (0 bytes modified across all 7 core files, exit code 0).
2. **Zero Prohibited Libraries Search**:
   - Command:
     ```powershell
     cd 'D:\Module 1'; git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
     ```
   - Verbatim Output: Empty (0 matches, exit code 1).
3. **Max Line Length Check in M2 Files**:
   - Verified that every line in `src/models/customer.py` (113 lines), `src/core/customer_manager.py` (112 lines), and `src/core/order_manager.py` (465 lines) is $\le 100$ characters. Output: `Line length check: OK`.

---

### Observation 2: Mission Area 1 — `Customer` Model Validations
Empirically tested via unit and property checks:
- **Empty / whitespace name**:
  - `Customer("U1", "", "a@b.com", False, "CUSTOMER")` -> raises `ValueError("Tên khách hàng không được để trống.")`.
  - `Customer("U1", "   ", "a@b.com", False, "CUSTOMER")` -> raises `ValueError("Tên khách hàng không được để trống.")`.
  - `c.name = ""` -> raises `ValueError`.
- **Invalid email**:
  - `Customer("U1", "An", "", False, "CUSTOMER")` -> raises `ValueError("Email khách hàng không hợp lệ.")`.
  - `Customer("U1", "An", "invalid_email_no_at", False, "CUSTOMER")` -> raises `ValueError("Email khách hàng không hợp lệ.")`.
  - `c.email = "no_at_symbol"` -> raises `ValueError`.
- **Empty / whitespace node_id**:
  - `Customer("U1", "An", "a@b.com", False, "")` -> raises `ValueError("Điểm giao hàng không được để trống.")`.
  - `Customer("U1", "An", "a@b.com", False, "   ")` -> raises `ValueError("Điểm giao hàng không được để trống.")`.
  - `c.node_id = ""` -> raises `ValueError`.
- **`from_dict` validation**:
  - Passing non-dict (`"not a dict"`) -> raises `ValueError("Dữ liệu đầu vào phải là dictionary.")`.
  - Missing any of `id`, `name`, `email`, `node_id` -> raises `ValueError("Dữ liệu thiếu trường '<field>'.")`.
  - None values in required fields -> raises `ValueError`.
  - Valid dict roundtrip `c.to_dict()` -> `Customer.from_dict(...)` preserves all fields (`id`, `name`, `email`, `is_vip`, `node_id`).

---

### Observation 3: Mission Area 2 — `CustomerManager`
Empirically tested against `data/users.json` and adversarial datasets:
- **Loading standard `data/users.json`**:
  - `CustomerManager("data/users.json")` yields exactly 4 users: `U001` (Nguyễn Văn An, VIP=True, CUSTOMER), `U002` (Trần Thị Bình, VIP=False, CUSTOMER_2), `U003` (Lê Văn Cường, VIP=False, CUSTOMER_3), `U004` (Phạm Thu Dung, VIP=True, CUSTOMER_2).
  - `cm.load_errors` has 0 errors.
- **SortedIndex case-insensitive & duplicate search**:
  - `cm.find_by_name("nguyễn văn an")` and `cm.find_by_name("NGUYỄN VĂN AN")` return `[U001]`.
  - `cm.find_by_name("   nguyễn văn an   ")` returns `[U001]` (whitespace tolerance).
  - Search on dataset with duplicate customer names returns all matching customer instances in $O(\log n) + O(k)$.
  - `cm.find_by_email("AN@EXAMPLE.COM")` returns `[U001]`.
  - Unmatched queries return `[]`.
- **Corrupt file / record safety**:
  - Nonexistent file path -> records `load_errors`, returns `[]` from `get_all()`, does not crash.
  - Broken JSON syntax -> records `load_errors`, does not crash.
  - Non-list/non-dict JSON root -> records `load_errors`, does not crash.
  - Corrupt records (non-dict items, invalid email, missing required fields) -> safely skipped to `load_errors`, valid records in the same file are successfully loaded.
  - Idempotent reload: calling `cm.load_customers()` multiple times refreshes indices cleanly without duplicate entries.

---

### Observation 4: Mission Area 3 — `OrderManager`
Empirically tested all guardrails, immutability, atomic trip lifecycle, and error handling:
- **Immutability of `om.orders`**:
  - `om.orders` returns a shallow copy of internal `_orders`.
  - Deleting an entry (`del ext_orders["O1"]`) or adding entries (`ext_orders["FAKE"] = ...`) on the returned dict does not mutate internal `om._orders`. Subsequent calls to `om.orders` and `om.get_order("O1")` remain completely intact.
- **`create_order` validations**:
  - Rejects `delivery_node_id=None`, `""`, `"   "`, `"ZZZ"`, `"RESTAURANT"`, or unreachable nodes with `last_error == "Điểm giao không hợp lệ"`.
  - Rejects when shipper is BUSY with exact verbatim error: `"Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"`.
  - Rejects duplicate `order_id`, empty name, empty email, empty items list.
  - Rejects when graph is None / map error.
  - Generates auto-incrementing IDs via `next_id()` correctly (`O001`, `O002`, `O006` after `O005`).
- **`start_delivery` validation & atomic trip**:
  - Empty `order_ids` -> returns `False`, `last_error == "Danh sách đơn hàng rỗng."`.
  - Duplicate `order_ids` (e.g. `["O1", "O1"]`) -> returns `False`, `last_error == "Danh sách đơn hàng có mã trùng lặp."`.
  - Non-existent order id -> returns `False`, `last_error == "Không tìm thấy đơn hàng '<id>'."`.
  - Non-READY order -> returns `False`, `last_error` specifies order status and that only READY orders can be delivered.
  - Atomicity: If one order in a batch is not READY, none of the orders are transitioned to DELIVERING.
  - Valid batch: Transitions all orders in batch to `DELIVERING`, flips `get_shipper_status()` to `"BUSY"`, populates `get_current_trip()`.
  - Single Undo/Redo: Calling `om.undo()` ONCE reverts all orders in the trip back to `READY` and flips shipper to `"IDLE"`; calling `om.redo()` restores all orders in the trip back to `DELIVERING` and flips shipper to `"BUSY"`.
- **`complete_delivery`**:
  - Rejects non-existent orders or orders not currently in `DELIVERING`.
  - For a multi-order trip (`["O1", "O2"]`), completing `O1` transitions `O1` to `PAID`, while `O2` remains `DELIVERING` and shipper status remains `"BUSY"`.
  - Completing `O2` transitions `O2` to `PAID`; with no remaining DELIVERING orders, shipper status automatically flips from `"BUSY"` to `"IDLE"`.
  - Calling `om.undo()` reverts `O2` to `DELIVERING` and flips shipper back to `"BUSY"`. Calling `om.redo()` restores `O2` to `PAID` and flips shipper to `"IDLE"`.
- **`update_order_status` guardrails**:
  - Attempting transition to `DELIVERING` is blocked with exact verbatim error: `"Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"`.
  - Attempting `CONFIRMED -> PREPARING` on an order that is NOT the top order per `PriorityEngine` is blocked with exact message:
    `"Đơn hàng '<top_id>' (<top_name>) có độ ưu tiên cao hơn, phải chế biến trước."`
  - When the top order is moved to `PREPARING`, the next order in priority queue is then permitted to transition.
  - Attempting to cancel orders in `DELIVERING` or `PAID` status is blocked (`"Không thể hủy đơn hàng đang ở trạng thái <status>."`).
- **Safe `load_orders`**:
  - Nonexistent file loads empty dictionary without crashing.
  - Malformed syntax JSON skips safely to `load_errors`.
  - Scalar root skips safely to `load_errors`.
  - Corrupt records skip safely to `load_errors` while valid order records in the same file are loaded into `om.orders`.

---

## 2. Logic Chain

1. **Integrity & Constraints**:
   - Observation 1 establishes that 0 lines were modified across all 7 core files, zero prohibited libraries are imported, and line length is $\le 100$ characters. All project non-negotiables are intact.
2. **Validation & Immutability**:
   - Observation 2 proves that `Customer` encapsulates all state with strict property setters, rejecting empty/invalid values and catching malformed dictionaries in `from_dict`.
   - Observation 4 confirms that `om.orders` returns a shallow copy, preventing unauthorized external tampering with `_orders`.
3. **Repository Search & Robustness**:
   - Observation 3 confirms that `CustomerManager` successfully indexes customers with `SortedIndex`, supporting case-insensitive binary search lookups in $O(\log n) + O(k)$, and safely handles corrupt JSON files and records via `load_errors`.
4. **Business Process & Shipper State Synchronization**:
   - Observation 4 demonstrates that shipper status (`IDLE` / `BUSY`) is truthfully derived from active `DELIVERING` orders.
   - When BUSY, `create_order` and `start_delivery` are rejected.
   - `start_delivery` batches trip orders atomically with a single snapshot, allowing 1-step undo back to `READY`.
   - `complete_delivery` accurately decrements delivering orders until the last one resets the shipper to `IDLE`.
5. **Kitchen Priority & Safety Guardrails**:
   - Observation 4 confirms that `update_order_status` prevents out-of-order preparation by enforcing `PriorityEngine().next_order`, blocks direct transition into `DELIVERING`, and disallows cancelling delivered/in-flight orders.

---

## 3. Caveats

- `tests/test_order_manager.py` contains legacy tests designed for the old `create_order(..., shipper_status)` signature; updating these unit tests is formally allocated to Milestone M4 per `PROJECT.md`.
- No other caveats. All Milestone M2 requirements and edge cases have been empirically exercised and verified.

---

## 4. Conclusion

- **Verdict**: **APPROVE**
- The Milestone M2 implementation (`src/models/customer.py`, `src/core/customer_manager.py`, `src/core/order_manager.py`) fully satisfies all functional specifications, constraints, and edge case resilience requirements.

---

## 5. Verification Method

To independently reproduce the empirical findings, run the following commands in PowerShell from `D:\Module 1`:

1. **Verify 7 core files untouched**:
   ```powershell
   Set-Location "D:\Module 1"
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   *Expected*: Empty output (0 diff lines).

2. **Verify zero prohibited library imports**:
   ```powershell
   Set-Location "D:\Module 1"
   git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   ```
   *Expected*: Empty output (exit code 1).

3. **Verify max line lengths**:
   ```powershell
   Set-Location "D:\Module 1"
   uv run python -c "
   for f in ['src/models/customer.py', 'src/core/customer_manager.py', 'src/core/order_manager.py']:
       with open(f, encoding='utf-8') as fp:
           for idx, l in enumerate(fp, 1):
               assert len(l.rstrip('\r\n')) <= 100, f'{f}:{idx}'
   print('Line length check: OK')
   "
   ```
   *Expected*: `Line length check: OK`.

4. **Verify all M2 specifications and edge cases via inline stress script**:
   ```powershell
   Set-Location "D:\Module 1"
   $env:PYTHONIOENCODING = "utf-8"
   uv run python -c "
   import tempfile, json
   from pathlib import Path
   from src.models.customer import Customer
   from src.core.customer_manager import CustomerManager
   from src.core.order_manager import OrderManager
   from src.core.routing_service import load_map_graph
   from src.models.order import OrderStatus, make_item_snapshot

   # 1. Customer Validations
   try: Customer('U1', '  ', 'a@b.com', False, 'CUSTOMER'); assert False
   except ValueError: pass
   try: Customer('U1', 'An', 'no_at', False, 'CUSTOMER'); assert False
   except ValueError: pass
   try: Customer('U1', 'An', 'a@b.com', False, '  '); assert False
   except ValueError: pass
   try: Customer.from_dict({'id': 'U1'}); assert False
   except ValueError: pass

   # 2. CustomerManager
   cm = CustomerManager('data/users.json')
   assert len(cm.get_all()) == 4
   assert len(cm.find_by_name('nguyễn văn an')) == 1
   assert len(cm.find_by_email('AN@EXAMPLE.COM')) == 1
   assert len(cm.load_errors) == 0

   # 3. OrderManager Lifecycle, Guardrails, and Undo/Redo
   with tempfile.TemporaryDirectory() as tmp:
       graph = load_map_graph()
       om = OrderManager(storage_path=Path(tmp)/'orders.json', graph=graph)
       items = [make_item_snapshot('M1', 'Phở', 1, 50000, 10)]

       # Immutability
       om.create_order('O1', 'An', 'a@b.com', items, 100.0, False, 'CUSTOMER')
       ext_orders = om.orders
       del ext_orders['O1']
       assert 'O1' in om.orders

       # Rejection of invalid nodes & BUSY
       assert not om.create_order('O2', 'B', 'b@b.com', items, 101.0, False, None)
       assert not om.create_order('O2', 'B', 'b@b.com', items, 101.0, False, 'ZZZ')
       assert not om.create_order('O2', 'B', 'b@b.com', items, 101.0, False, 'RESTAURANT')

       # Priority queue enforcement
       om.create_order('O2', 'Bình VIP', 'b@b.com', items, 200.0, True, 'CUSTOMER_2')
       om.update_order_status('O1', OrderStatus.CONFIRMED)
       om.update_order_status('O2', OrderStatus.CONFIRMED)
       assert not om.update_order_status('O1', OrderStatus.PREPARING)
       assert 'O2' in om.last_error
       assert om.update_order_status('O2', OrderStatus.PREPARING)
       assert om.update_order_status('O2', OrderStatus.READY)
       assert om.update_order_status('O1', OrderStatus.PREPARING)
       assert om.update_order_status('O1', OrderStatus.READY)

       # Block transition into DELIVERING
       assert not om.update_order_status('O1', OrderStatus.DELIVERING)
       assert 'Hãy dùng' in om.last_error

       # Start delivery
       assert om.start_delivery(['O1', 'O2'])
       assert om.get_shipper_status() == 'BUSY'
       assert not om.create_order('O3', 'C', 'c@b.com', items, 300.0, False, 'CUSTOMER_3')

       # Undo/Redo trip
       assert om.undo()
       assert om.get_order('O1').status == OrderStatus.READY
       assert om.get_shipper_status() == 'IDLE'
       assert om.redo()
       assert om.get_shipper_status() == 'BUSY'

       # Complete deliveries
       assert om.complete_delivery('O1')
       assert om.get_shipper_status() == 'BUSY'
       assert om.complete_delivery('O2')
       assert om.get_shipper_status() == 'IDLE'

   print('ALL M2 EMPIRICAL TESTS PASSED')
   "
   ```
   *Expected*: `ALL M2 EMPIRICAL TESTS PASSED`.

5. **Invalidation conditions**:
   - Any assertion failure in the verification script.
   - Any non-empty output from the 7 core files diff check.
   - Any prohibited import detected in `src/`.
