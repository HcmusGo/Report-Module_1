## 2026-11-01T02:56:25Z
You are m0_worker, a teamwork_worker subagent.
Your working directory is: D:\Module 1\.agents\teamwork\m0_worker
Original Request path: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan path: D:\Module 1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY CONSTRAINTS:
- NEVER modify any of the 7 core files:
  1. src/core/routing_algo.py
  2. src/core/priority_engine.py
  3. src/models/graph_node.py
  4. src/models/base.py
  5. src/core/storage.py
  6. src/core/structures.py
  7. src/core/menu_manager.py
- DO NOT import collections/deque, heapq, bisect, queue, networkx.
- DO NOT edit pyproject.toml or uv.lock.

SCOPE OF WORK (Milestone M0: Baseline & Data Setup):
1. Git branch:
   - Create and checkout branch `feat/connect-routing-order` from `main`: `git checkout -b feat/connect-routing-order`.
2. Standard data files:
   - Overwrite `data/map_graph.json` with the standard 8-node map (6 mentor + 2 customer nodes CUSTOMER_2, CUSTOMER_3; 12 bidirectional edges with exact coordinates and weights):
     Nodes:
     - RESTAURANT: name="Quán ăn", x=0.0, y=0.0
     - A: name="Ngã tư A", x=2.0, y=2.0
     - B: name="Ngã tư B", x=3.0, y=-1.0
     - C: name="Ngã ba C", x=5.0, y=2.0
     - D: name="Ngã tư D", x=6.0, y=-1.0
     - CUSTOMER: name="Nhà khách hàng", x=8.0, y=1.0
     - CUSTOMER_2: name="Nhà khách hàng 2", x=7.0, y=4.0
     - CUSTOMER_3: name="Nhà khách hàng 3", x=4.0, y=-4.0
     Edges (12 bidirectional):
     ["RESTAURANT", "A", 2.8], ["RESTAURANT", "B", 3.2], ["A", "B", 3.2], ["A", "C", 3.0], ["B", "D", 3.0], ["C", "D", 3.2], ["C", "CUSTOMER", 3.2], ["D", "CUSTOMER", 2.8], ["C", "CUSTOMER_2", 2.8], ["CUSTOMER", "CUSTOMER_2", 3.2], ["B", "CUSTOMER_3", 3.2], ["D", "CUSTOMER_3", 3.6]
   - Overwrite `data/users.json` with 4 users:
     [
       {"id": "U001", "name": "Nguyễn Văn An", "email": "an@example.com", "is_vip": true, "node_id": "CUSTOMER"},
       {"id": "U002", "name": "Trần Thị Bình", "email": "binh@example.com", "is_vip": false, "node_id": "CUSTOMER_2"},
       {"id": "U003", "name": "Lê Văn Cường", "email": "cuong@example.com", "is_vip": false, "node_id": "CUSTOMER_3"},
       {"id": "U004", "name": "Phạm Thu Dung", "email": "dung@example.com", "is_vip": true, "node_id": "CUSTOMER_2"}
     ]
3. Code cleanup:
   - In `src/models/menu_item.py`, replace lines 14-17 (the try/except block) with exactly:
     `from src.models.base import BaseEntity`
4. Verification:
   - Run `uv run python -m unittest discover -s tests -t .` and verify 20 tests pass.
   - Run `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py` and confirm 0 diff lines.

Deliver your handoff report to `D:\Module 1\.agents\teamwork\m0_worker\handoff.md`. Send a message when complete.
