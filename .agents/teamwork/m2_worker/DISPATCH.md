## 2026-11-01T03:17:44Z
You are m2_worker, a teamwork_worker subagent.
Your working directory is: D:\Module 1\.agents\teamwork\m2_worker
Original Request path: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan path: D:\Module 1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONSTRAINTS:
- You ONLY have write ownership of:
  - `src/models/customer.py` (new)
  - `src/core/customer_manager.py` (new)
  - `src/core/order_manager.py` (modify)
- NEVER touch any of the 7 core files (routing_algo, priority_engine, graph_node, base, storage, structures, menu_manager).
- DO NOT import collections/deque, heapq, bisect, queue, networkx.
- Keep all line lengths <= 100 characters.

TASK SPECIFICATIONS (Milestone M2: Customer & Order Management):

1. Create `src/models/customer.py`:
   - `Customer(BaseEntity)` inheriting from `src.models.base.BaseEntity`.
   - Constructor: `__init__(self, id: str, name: str, email: str, is_vip: bool, node_id: str)`.
   - Private fields: `_name`, `_email`, `_is_vip`, `_node_id`.
   - Properties with validation:
     - `name`: string, stripped non-empty, raises `ValueError("Tên khách hàng không được để trống.")`.
     - `email`: string, stripped non-empty, must contain `'@'`, raises `ValueError("Email khách hàng không hợp lệ.")`.
     - `is_vip`: boolean.
     - `node_id`: string, stripped non-empty, raises `ValueError("Điểm giao hàng không được để trống.")`.
   - `to_dict() -> dict[str, Any]`: calls `super().to_dict()` and merges `{"name": self._name, "email": self._email, "is_vip": self._is_vip, "node_id": self._node_id}`.
   - `@classmethod from_dict(cls, data: dict[str, Any]) -> Customer`: validates data is dict, required fields `"id", "name", "email", "node_id"`, raises `ValueError` in Vietnamese if missing.

2. Create `src/core/customer_manager.py`:
   - `CustomerManager(storage_path: str | Path = "data/users.json")`:
   - Read-only manager (no create/update/delete).
   - Loads via `load_json(storage_path, default=[])`.
   - Per-record exception handling: catches `(ValueError, KeyError, TypeError)`, skips bad record, appends to `self.load_errors: list[str]`. If root data not list/dict, treats as empty and records to `load_errors`.
   - Uses `SortedIndex` (from `src.core.structures`) for `_name_index` and `_email_index`.
   - Methods:
     - `get_all() -> list[Customer]`
     - `get_by_id(customer_id: str) -> Customer | None`
     - `find_by_name(name: str) -> list[Customer]`
     - `find_by_email(email: str) -> list[Customer]`

3. Update `src/core/order_manager.py`:
   - Encapsulate private state: `_orders`, `_name_index`, `_email_index`, `_undo_stack`, `_redo_stack`, `_graph`.
   - `__init__(self, storage_path="data/orders.json", graph: Graph | None = None)`:
     If `graph is None`, try `load_map_graph()`; on error, set `self._graph = None` and `self.map_error = str(err)`, NEVER crash.
   - Properties:
     - `@property orders(self) -> dict[str, Order]`: returns shallow copy `self._orders.copy()`. Mutating it must not affect `self._orders`.
     - `get_order(order_id) -> Order | None`
     - `get_all_orders() -> list[Order]`
     - `can_undo() -> bool`, `can_redo() -> bool`
     - `get_shipper_status() -> str`: returns `"BUSY"` if any order has `status == OrderStatus.DELIVERING` (or `"DELIVERING"`), else `"IDLE"`.
     - `get_current_trip() -> list[Order]`: list of orders currently `DELIVERING`.
   - `create_order(...)`:
     Signature: `create_order(self, order_id: str, customer_name: str, customer_email: str, items: list[Any], created_at: float, is_vip: bool = False, delivery_node_id: str | None = None) -> bool`.
     REMOVE `shipper_status` argument!
     Rejection rules (sets `self.last_error`, returns `False`):
     - If `self._graph is None` or `self.map_error`: reject with `self.map_error or "Bản đồ chưa sẵn sàng."`
     - If `self.get_shipper_status() == "BUSY"`: `self.last_error = "Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"`
     - If `delivery_node_id` is None, empty, or not `is_valid_delivery_node(self._graph, delivery_node_id)`: `self.last_error = "Điểm giao không hợp lệ"`
     - Standard validations (order_id, name, email, items).
     Pass `delivery_node_id` to `Order(..., delivery_node_id=delivery_node_id)`.
   - `start_delivery(self, order_ids: list[str]) -> bool`:
     - Reject if `get_shipper_status() == "BUSY"`.
     - Reject if `order_ids` empty or has duplicates.
     - Validate upfront: every order exists, status == OrderStatus.READY, valid `delivery_node_id`.
     - If valid: take 1 snapshot `self._create_snapshot()`, push to `_undo_stack`, clear `_redo_stack`.
     - Change all to `OrderStatus.DELIVERING` via `order.change_status(OrderStatus.DELIVERING)`.
     - Save once via `self.save_orders()`. Return True. (A single Undo reverts all orders in the trip back to READY).
   - `complete_delivery(self, order_id: str) -> bool`:
     - Order must exist and have status `OrderStatus.DELIVERING`. If not, reject.
     - Take 1 snapshot, push to `_undo_stack`, clear `_redo_stack`.
     - Change order to `OrderStatus.PAID` via `order.change_status(OrderStatus.PAID)`.
     - Save once. Return True.
     - When last order is completed, `get_shipper_status()` automatically returns `"IDLE"`.
   - `update_order_status(self, order_id: str, new_status: str) -> bool`:
     - Block direct transition into DELIVERING:
       If `new_status == OrderStatus.DELIVERING` (or `"DELIVERING"`):
       `self.last_error = "Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"` -> return False.
     - Block CONFIRMED -> PREPARING if not top order:
       If current status is CONFIRMED and `new_status == OrderStatus.PREPARING` (or `"PREPARING"`):
       `confirmed = self.get_orders_by_status(OrderStatus.CONFIRMED)`
       `top = PriorityEngine().next_order(confirmed, now=time.time())`
       If `top and order_id != top.id`:
       `self.last_error = f"Đơn hàng '{top.id}' ({top.customer_name}) có độ ưu tiên cao hơn, phải chế biến trước."` -> return False.
     - Preserve existing checks (cannot cancel if PAID or DELIVERING).
   - `load_orders()` safe error handling:
     Catch `(ValueError, KeyError, TypeError)`, record to `self.load_errors: list[str]`. If root data not dict/list, record to `load_errors`. Never crash.

VERIFICATION:
- Verify that customer models and manager work as expected.
- Verify order manager shipper status, atomic start_delivery, undo/redo whole trip, complete_delivery, kitchen queue priority guard in update_order_status.
- Verify 7 core files are untouched.
- Verify zero prohibited imports.
- Verify line lengths <= 100 characters.

Write your handoff report to `D:\Module 1\.agents\teamwork\m2_worker\handoff.md`. Send a message when complete.
