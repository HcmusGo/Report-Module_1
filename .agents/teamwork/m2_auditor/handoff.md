# Forensic Audit Report: Milestone M2 (Customer & Order Management)

**Work Product**: Milestone M2 (`src/models/customer.py`, `src/core/customer_manager.py`, `src/core/order_manager.py`)  
**Profile**: General Project (Demo Mode)  
**Verdict**: **CLEAN**

---

### Phase Results
- **Check 1 (7 Core Files Diff)**: **PASS** — Exactly 0 bytes / 0 lines modified across all 7 core files.
- **Check 2 (Prohibited Imports)**: **PASS** — Zero prohibited imports (`collections`, `deque`, `heapq`, `bisect`, `queue`, `networkx`) across all files in `src/`.
- **Check 3 (Dependency Lock Files)**: **PASS** — Both `pyproject.toml` and `uv.lock` are completely untouched (0 diff).
- **Check 4 (Authentic Implementation & Logic Inspection)**: **PASS** —
  - `src/models/customer.py`: Authentic `Customer(BaseEntity)` with private fields, property validation, clean `to_dict()` and `@classmethod from_dict()`. No facades.
  - `src/core/customer_manager.py`: Authentic read-only manager, per-record exception handling recording to `load_errors`, `SortedIndex` O(log n) searches.
  - `src/core/order_manager.py`: Authentic state encapsulation, derived shipper status, `PriorityEngine().next_order` priority enforcement on `CONFIRMED -> PREPARING`, atomic batch `start_delivery`, single `complete_delivery`, and full snapshot create/restore for multi-order `undo()`/`redo()`.
  - Zero hardcoding of test outputs or mock facades.
- **Check 5 (Empirical Behavioral & Guardrail Verification)**: **PASS** — All business rules, error cases, and guardrails verified empirically in Python runtime.
- **Check 6 (Style & Formatting)**: **PASS** — All lines across all 3 M2 files are <= 100 characters.

---

## 1. Observation

### Observation 1.1: Git Diff on 7 Core Files
Executing:
```powershell
git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
```
Output:
```
(empty - 0 files changed, 0 insertions, 0 deletions)
```
Status check:
```powershell
git status --porcelain -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
```
Output:
```
(empty - working tree clean for 7 core files)
```

### Observation 1.2: Prohibited Imports Inspection
Executing:
```powershell
git grep --untracked -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
```
Output:
```
Command exited with code 1. No matches found.
```
Ripgrep search for `deque` in `src/`:
Only references found in comments/docs in `structures.py` and method calls `pq.dequeue()` in `src/core/priority_engine.py` / `src/core/structures.py`. No imports of `collections.deque`.

### Observation 1.3: Dependency Lock Files
Executing:
```powershell
git diff --stat pyproject.toml uv.lock
git status --porcelain pyproject.toml uv.lock
```
Output:
```
(empty - 0 changes)
```

### Observation 1.4: Source Code Inspection of M2 Files
- `src/models/customer.py` (113 lines):
  - Line 19: `class Customer(BaseEntity):`
  - Lines 37-77: Encapsulated properties `@property def name`, `@property def email`, `@property def is_vip`, `@property def node_id` with strict validation (e.g. lines 44-45 non-empty name, lines 55-56 non-empty email with `@`, lines 75-76 non-empty node_id).
  - Lines 79-88: `to_dict()` calling `super().to_dict()` and including all four customer attributes.
  - Lines 90-106: `@classmethod def from_dict(cls, data: dict[str, Any]) -> Customer` enforcing dictionary type and requiring fields `id`, `name`, `email`, `node_id`.
- `src/core/customer_manager.py` (112 lines):
  - Line 20: `class CustomerManager:`
  - Lines 23-31: Initializes read-only storage path, `_customers: dict[str, Customer]`, `_name_index: SortedIndex`, `_email_index: SortedIndex`, `_load_errors: list[str]`.
  - Lines 48-74: `load_customers()` wraps record processing in `try/except (ValueError, KeyError, TypeError) as err:` appending to `self._load_errors` without crashing.
  - Lines 91-105: `find_by_name` and `find_by_email` utilize `self._name_index.find_all(name)` and `self._email_index.find_all(email)` achieving O(log n) + O(k) lookups.
- `src/core/order_manager.py` (465 lines):
  - Lines 40-50: Encapsulates `_orders`, `_name_index`, `_email_index`, `_undo_stack`, `_redo_stack`, `_graph`, `_map_error`, `_last_error`, `_load_errors`.
  - Line 68: `@property def orders` returns `self._orders.copy()`.
  - Lines 104-109: `_create_snapshot()` captures `{order_id: order.status for order_id, order in self._orders.items()}`.
  - Lines 111-120: `_restore_snapshot(snapshot)` restores each status via `order.restore_status(status)` and saves to storage.
  - Lines 201-206: `get_shipper_status()` inspects `_orders.values()` returning `"BUSY"` if any order has `OrderStatus.DELIVERING`, otherwise `"IDLE"`.
  - Lines 241-248: `create_order` rejects with `"Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"` when BUSY, and rejects with `"Điểm giao không hợp lệ"` when `delivery_node_id` is invalid or unreachable.
  - Lines 292-341: `start_delivery(order_ids)` validates all orders upfront (exist, status == READY, valid delivery node), pushes 1 snapshot to `_undo_stack`, clears `_redo_stack`, transitions all to `OrderStatus.DELIVERING`, and saves once.
  - Lines 343-372: `complete_delivery(order_id)` transitions order to `OrderStatus.PAID`, pushes snapshot, clears `_redo_stack`, and saves once. Shipper returns to `"IDLE"` when all orders are completed.
  - Lines 386-389: `update_order_status` blocks direct transition into `DELIVERING` with `"Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"`.
  - Lines 391-404: `update_order_status` enforces `PriorityEngine().next_order` when moving `CONFIRMED -> PREPARING`, rejecting if not top priority order.

### Observation 1.5: Empirical Runtime Test Results
Executed comprehensive test script verifying:
1. Customer property setters and validations (`ValueError` on empty name, empty node_id, missing '@').
2. CustomerManager loading from `data/users.json` (4 users), binary search case-insensitive lookups, corrupted record handling (logged to `load_errors` without crashing).
3. OrderManager initial state (`get_shipper_status() == 'IDLE'`, `can_undo() is False`, `can_redo() is False`).
4. OrderManager property immutability (mutating `om.orders` shallow copy does not pollute `_orders`).
5. `create_order` rejection on invalid delivery nodes (None, empty string, "RESTAURANT", "ZZZ").
6. Kitchen priority queue enforcement: VIP order prioritized; non-VIP blocked with message naming top priority order; aging-based order of earlier created normal order prioritized over later created normal order.
7. Block on direct transition to `DELIVERING` via `update_order_status`.
8. Atomic batch `start_delivery` transitioning multiple orders together, switching shipper to `BUSY`, and blocking new orders.
9. Single `om.undo()` restoring all trip orders back to `READY` and resetting shipper to `IDLE`; single `om.redo()` restoring all back to `DELIVERING` and shipper back to `BUSY`.
10. `complete_delivery` transitioning orders to `PAID`, with automatic return of shipper to `IDLE` upon completing the final order.
11. Corrupted order records safely caught and logged to `load_errors` without application crash.

Execution Output:
```
ALL ORDER MANAGER TESTS PASSED EMPIRICALLY!
```

### Observation 1.6: Code Formatting Check
Running line length check across `src/models/customer.py`, `src/core/customer_manager.py`, `src/core/order_manager.py`:
Output:
```
ALL LINES <= 100 CHARACTERS: PASS
```

---

## 2. Logic Chain

1. **Baseline and Zero-Diff Verification**:
   The assignment forbids modifying the 7 core files (`src/core/routing_algo.py`, `src/core/priority_engine.py`, `src/models/graph_node.py`, `src/models/base.py`, `src/core/storage.py`, `src/core/structures.py`, `src/core/menu_manager.py`) and the dependency manifests (`pyproject.toml`, `uv.lock`). `git diff --stat` and `git status --porcelain` showed zero changes across all these files (Observation 1.1, 1.3). Therefore, core file integrity is strictly preserved.

2. **Zero Prohibited Imports**:
   `ORIGINAL_REQUEST.md` and `PROJECT.md` prohibit importing `collections/deque`, `heapq`, `bisect`, `queue`, and `networkx`. Ripgrep and git grep confirmed zero occurrences across `src/` (Observation 1.2). Therefore, data structure constraints are strictly respected.

3. **Authentic Business Logic vs. Facades**:
   Analysis of `Customer`, `CustomerManager`, and `OrderManager` confirmed genuine implementations. `OrderManager` directly queries `PriorityEngine().next_order` using the runtime priority queue and dynamically derives `shipper_status` from active orders. Undo/redo leverages genuine snapshot stacks storing status states and invoking `restore_status` (Observation 1.4). No hardcoded strings, dummy return constants, or mock facades exist.

4. **Empirical Behavioral Verification**:
   Running functional and adversarial tests against the M2 codebase confirmed that all state transitions, error paths, validation guards, and batch operations function as specified (Observation 1.5).

5. **Style Compliance**:
   All lines across all three M2 files are within the 100-character line length limit (Observation 1.6).

---

## 3. Caveats

- `tests/test_order_manager.py` still contains legacy tests written for the pre-M2 signature of `create_order` (including `shipper_status="BUSY"`). Updating `tests/test_order_manager.py` is allocated to Milestone M4 per `PROJECT.md` and was appropriately left untouched by the M2 worker. All M2 requirements were independently and empirically verified using dedicated test runs during this audit.

---

## 4. Conclusion

Milestone M2 implementation (`src/models/customer.py`, `src/core/customer_manager.py`, `src/core/order_manager.py`) is completely clean, authentic, robust, and compliant with all project constraints and requirements.

**Final Verdict**: **CLEAN**

---

## 5. Verification Method

To independently reproduce and verify this audit verdict, execute the following commands in powershell from `D:\Module 1`:

1. **Verify 0 diff on 7 core files and dependency locks**:
   ```powershell
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py pyproject.toml uv.lock
   ```
   *Expected output: empty.*

2. **Verify zero prohibited imports**:
   ```powershell
   git grep --untracked -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   ```
   *Expected output: exit code 1 (no matches).*

3. **Verify line length <= 100 characters**:
   ```powershell
   uv run python -c "
   files = ['src/models/customer.py', 'src/core/customer_manager.py', 'src/core/order_manager.py']
   for f in files:
       with open(f, encoding='utf-8') as fp:
           for idx, line in enumerate(fp, 1):
               assert len(line.rstrip('\r\n')) <= 100, f'{f}:{idx}'
   print('ALL LINES <= 100 CHARS: PASS')
   "
   ```

4. **Verify Customer & CustomerManager behavior**:
   ```powershell
   uv run python -c "
   from src.core.customer_manager import CustomerManager
   cm = CustomerManager('data/users.json')
   assert len(cm.get_all()) == 4
   assert cm.get_by_id('U001').name == 'Nguyễn Văn An'
   assert cm.find_by_name('nguyễn văn an')[0].id == 'U001'
   print('Customer verification OK')
   "
   ```

5. **Verify OrderManager guardrails, PriorityEngine integration, batch delivery & undo/redo**:
   ```powershell
   $code = @'
   import sys
   sys.path.insert(0, r"D:\Module 1")
   import tempfile, time
   from pathlib import Path
   from src.core.order_manager import OrderManager
   from src.core.routing_service import load_map_graph
   from src.models.order import OrderStatus, make_item_snapshot

   with tempfile.TemporaryDirectory() as tmp:
       om = OrderManager(storage_path=Path(tmp)/'orders.json', graph=load_map_graph())
       it = [make_item_snapshot('M1', 'Food', 1, 10000, 5)]
       assert om.create_order('O1', 'Khach 1', 'k1@test.com', it, time.time() - 50, is_vip=False, delivery_node_id='CUSTOMER')
       assert om.create_order('O2', 'Khach VIP', 'vip@test.com', it, time.time(), is_vip=True, delivery_node_id='CUSTOMER_2')
       assert not om.create_order('O3', 'Bad', 'b@test.com', it, time.time(), delivery_node_id='RESTAURANT')
       assert om.update_order_status('O1', OrderStatus.CONFIRMED)
       assert om.update_order_status('O2', OrderStatus.CONFIRMED)
       assert not om.update_order_status('O1', OrderStatus.PREPARING) # VIP O2 must be prepared first
       assert om.update_order_status('O2', OrderStatus.PREPARING)
       assert om.update_order_status('O2', OrderStatus.READY)
       assert om.update_order_status('O1', OrderStatus.PREPARING)
       assert om.update_order_status('O1', OrderStatus.READY)
       assert not om.update_order_status('O1', OrderStatus.DELIVERING) # Direct delivering blocked
       assert om.start_delivery(['O1', 'O2'])
       assert om.get_shipper_status() == 'BUSY'
       assert om.undo()
       assert om.get_shipper_status() == 'IDLE'
       assert om.redo()
       assert om.complete_delivery('O1')
       assert om.get_shipper_status() == 'BUSY'
       assert om.complete_delivery('O2')
       assert om.get_shipper_status() == 'IDLE'
   print('OrderManager verification OK')
   '@
   [System.IO.File]::WriteAllText("$env:TEMP\verify_m2_check.py", $code, [System.Text.Encoding]::UTF8)
   uv run python "$env:TEMP\verify_m2_check.py"
   Remove-Item "$env:TEMP\verify_m2_check.py" -Force
   ```
