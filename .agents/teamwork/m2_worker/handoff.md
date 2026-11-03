# Handoff Report: Milestone M2 (Customer & Order Management)

## 1. Observation
- `src/models/customer.py` was created with `Customer(BaseEntity)`, validating `name` (non-empty string), `email` (non-empty string containing `'@'`), `is_vip` (bool), `node_id` (non-empty string), `to_dict()`, and `@classmethod from_dict()`.
- `src/core/customer_manager.py` was created with read-only `CustomerManager(storage_path="data/users.json")`, loading via `load_json()`, per-record exception handling recording errors to `self.load_errors`, and indexing via `_name_index: SortedIndex` and `_email_index: SortedIndex` for `get_all()`, `get_by_id()`, `find_by_name()`, `find_by_email()`.
- `src/core/order_manager.py` was updated:
  - Private state encapsulated: `_orders`, `_name_index`, `_email_index`, `_undo_stack`, `_redo_stack`, `_graph`, `_map_error`, `_last_error`, `_load_errors`.
  - Properties implemented: `@property orders` returns `self._orders.copy()`, `get_order()`, `get_all_orders()`, `can_undo()`, `can_redo()`, `get_shipper_status()` returning `"BUSY"` if any order is `DELIVERING` else `"IDLE"`, `get_current_trip()`.
  - `create_order` signature updated to `(order_id, customer_name, customer_email, items, created_at, is_vip=False, delivery_node_id=None)` with `shipper_status` argument removed. Rejects if `_graph` is None or map error, if `get_shipper_status() == "BUSY"` with `"Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"`, if `delivery_node_id` is invalid with `"Điểm giao không hợp lệ"`.
  - `start_delivery(order_ids)` validates all orders upfront (exist, status == READY, valid delivery_node_id), takes 1 snapshot to `_undo_stack`, clears `_redo_stack`, changes all to `DELIVERING`, and saves once.
  - `complete_delivery(order_id)` validates status == DELIVERING, takes snapshot to `_undo_stack`, clears `_redo_stack`, changes to `PAID`, saves once; shipper returns to `"IDLE"` when last order completes.
  - `update_order_status` blocks direct transition to `DELIVERING` (`"Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"`), and blocks `CONFIRMED -> PREPARING` if not top order according to `PriorityEngine().next_order` (`"Đơn hàng '{top.id}' ({top.customer_name}) có độ ưu tiên cao hơn, phải chế biến trước."`).
  - `load_orders` catches `(ValueError, KeyError, TypeError)` and non-dict/list root, recording to `load_errors` without crashing.
- `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py` returned empty output (0 bytes modified across all 7 core files).
- `git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src` returned exit code 1 (zero prohibited imports found).
- Python check confirmed all lines in `src/models/customer.py`, `src/core/customer_manager.py`, `src/core/order_manager.py` are <= 100 characters.

## 2. Logic Chain
1. By inheriting `Customer` from `BaseEntity`, ID handling is unified and consistent with the codebase entity model.
2. Encapsulating private fields in `Customer` and providing property getters/setters with Vietnamese error messages prevents bad entity states from entering the system.
3. In `CustomerManager`, read-only operations backed by `SortedIndex` provide O(log n) lookups without modifying storage. Wrapping per-record loading in try/except catches corrupted entries safely into `load_errors`.
4. In `OrderManager`, returning a shallow copy from `orders` property prevents external mutation of `_orders`.
5. Defining `get_shipper_status()` derived purely from `_orders` ensures that shipper availability is always truthful and synchronized with active orders.
6. In `start_delivery`, performing atomic batch validation followed by a single snapshot ensures full consistency: either the entire trip transitions to `DELIVERING` or none does, and a single `undo()` restores all trip orders back to `READY`.
7. Enforcing `PriorityEngine().next_order` in `update_order_status` prevents out-of-order kitchen preparation, fulfilling the kitchen queue requirement.

## 3. Caveats
- `tests/test_order_manager.py` still contains legacy tests written with the old `create_order` signature (including positional `shipper_status`). Updating `tests/test_order_manager.py` belongs to Milestone M4 per `PROJECT.md`.
- No modifications were made outside the three files allocated to this worker (`src/models/customer.py`, `src/core/customer_manager.py`, `src/core/order_manager.py`).

## 4. Conclusion
Milestone M2 is fully implemented and verified against all constraints, functional specifications, and business rules.

## 5. Verification Method
1. Verify 7 core files are untouched:
   ```bash
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   ```
   (Must output nothing).

2. Verify zero prohibited imports:
   ```bash
   git grep -En "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   ```
   (Must return no matches / exit code 1).

3. Verify line lengths <= 100:
   ```powershell
   uv run python -c "
   for f in ['src/models/customer.py', 'src/core/customer_manager.py', 'src/core/order_manager.py']:
       with open(f, encoding='utf-8') as fp:
           for idx, l in enumerate(fp, 1):
               assert len(l.rstrip('\r\n')) <= 100, f'{f}:{idx}'
   print('OK')
   "
   ```

4. Verify Customer and CustomerManager behavior:
   ```powershell
   uv run python -c "
   from src.core.customer_manager import CustomerManager
   cm = CustomerManager('data/users.json')
   assert len(cm.get_all()) == 4
   assert cm.get_by_id('U001').name == 'Nguyễn Văn An'
   print('Customer verification OK')
   "
   ```

5. Verify OrderManager guards, shipper status, start_delivery, undo/redo, complete_delivery:
   ```powershell
   uv run python -c "
   import tempfile
   from pathlib import Path
   from src.core.order_manager import OrderManager
   from src.core.routing_service import load_map_graph
   from src.models.order import OrderStatus, make_item_snapshot

   with tempfile.TemporaryDirectory() as tmp:
       om = OrderManager(storage_path=Path(tmp)/'orders.json', graph=load_map_graph())
       it = [make_item_snapshot('M1', 'Food', 1, 10000, 5)]
       assert om.create_order('O1', 'A', 'a@a.com', it, 100.0, delivery_node_id='CUSTOMER')
       assert not om.create_order('O2', 'B', 'b@b.com', it, 100.0, delivery_node_id='RESTAURANT')
       assert om.update_order_status('O1', OrderStatus.CONFIRMED)
       assert om.update_order_status('O1', OrderStatus.PREPARING)
       assert om.update_order_status('O1', OrderStatus.READY)
       assert not om.update_order_status('O1', OrderStatus.DELIVERING)
       assert om.start_delivery(['O1'])
       assert om.get_shipper_status() == 'BUSY'
       assert om.undo()
       assert om.get_order('O1').status == OrderStatus.READY
       assert om.redo()
       assert om.complete_delivery('O1')
       assert om.get_shipper_status() == 'IDLE'
       print('OrderManager verification OK')
   "
   ```
