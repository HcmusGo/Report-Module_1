## 2026-11-01T04:13:21Z
You are m5_worker, a teamwork_worker subagent.
Your working directory is: D:\Module 1\.agents\teamwork\m5_worker
Original Request path: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md
Project plan path: D:\Module 1\PROJECT.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All work must be genuine. A teamwork_auditor will independently verify your work.

MANDATORY CONSTRAINTS:
- NEVER touch any of the 7 core files:
  1. src/core/routing_algo.py
  2. src/core/priority_engine.py
  3. src/models/graph_node.py
  4. src/models/base.py
  5. src/core/storage.py
  6. src/core/structures.py
  7. src/core/menu_manager.py
- DO NOT edit pyproject.toml or uv.lock.
- DO NOT git push. DO NOT switch or modify the main branch. Stay on `feat/connect-routing-order`.
- DO NOT commit cache files, `.venv`, `.agents/`, or `data/orders.json`.
- Keep lines in documentation <= 100 characters.

TASK SPECIFICATIONS (Milestone M5: Documentation, CODEOWNERS, Git Commits & Final Acceptance):

1. Documentation (`README.md`):
   - Add section "## Cách dùng app theo đúng nghiệp vụ" into `README.md` (place right after "Cài đặt và chạy" / before "Dữ liệu").
   - Detail the 7-step standard demo:
     - Bước 1: Tạo đơn hàng tại tab "Đơn hàng" (chọn khách hàng U001, U002, U003; thông tin khách hàng và điểm giao hiển thị tự động; chọn món và số lượng; tạo đơn).
     - Bước 2: Chuyển trạng thái đơn sang CONFIRMED.
     - Bước 3: Chế biến tại tab "Hàng đợi chế biến" theo đúng thứ tự ưu tiên của PriorityEngine sang PREPARING rồi READY.
     - Bước 4: Chuyển sang tab "Bản đồ / Lộ trình", xem danh sách đơn READY và quãng đường đơn lẻ từ Quán.
     - Bước 5: Gom chuyến (chọn các đơn READY), xem lộ trình gom chuyến (thứ tự thăm CUSTOMER_3 -> CUSTOMER -> CUSTOMER_2, quãng đường 16.0 km), xem bảng so sánh Dijkstra vs A*.
     - Bước 6: Bấm "Bắt đầu giao" (chuyển sang DELIVERING, Shipper chuyển sang BUSY; khi BUSY hệ thống từ chối tạo đơn mới).
     - Bước 7: Bấm "Đã giao" cho từng đơn trong chuyến để chuyển sang PAID; khi đơn cuối cùng hoàn thành, Shipper tự động quay về IDLE.
   - Add note on the `.bak` backup mechanism: Khi file JSON bị sai cú pháp, storage tự động đổi tên thành `<file>.bak` và trả về dữ liệu mặc định rỗng để không làm crash ứng dụng, người dùng có thể sửa file `.bak` rồi đổi tên lại.
   - Keep line lengths <= 100 characters.

2. `.github/CODEOWNERS`:
   - Append the required owner mappings:
     `/src/models/customer.py @thanvanthelam`
     `/src/core/customer_manager.py @thanvanthelam`
     `/tests/test_customer_manager.py @thanvanthelam`
     `/tests/test_routing_service.py @DUT26DoQuyen`

3. Git Commits Workflow on `feat/connect-routing-order`:
   - Verify current branch is `feat/connect-routing-order`.
   - Organize and stage specific files to create clean, modular commits for each Part with standard prefixes:
     - Part 0: `feat(data): setup canonical map graph and users dataset` (stage `data/map_graph.json`, `data/users.json`)
     - Part 1: `feat(routing): implement business routing service and nearest-neighbor batch planning` (stage `src/core/routing_service.py`)
     - Part 2: `feat(order): refactor order manager with derived shipper status and atomic batch delivery` (stage `src/core/order_manager.py`)
     - Part 3: `feat(customer): implement customer entity and read-only customer manager` (stage `src/models/customer.py`, `src/core/customer_manager.py`)
     - Part 4 & 5: `feat(ui): refactor streamlit order and map tabs with reactive widgets and altair` (stage `src/app.py`)
     - Part 6: `test: add comprehensive test suites for routing, order, customer and app smoke` (stage `tests/test_routing_service.py`, `tests/test_customer_manager.py`, `tests/test_order_manager.py`, `tests/test_app_smoke.py`)
     - Part 7: `docs: document business demo workflow and json backup mechanism in README` (stage `README.md`)
     - Part 8: `chore: update CODEOWNERS and clean menu_item import` (stage `.github/CODEOWNERS`, `src/models/menu_item.py`)
   - Check `git status` after all commits: working directory should be clean (except untracked `.agents/`).

4. Full Verification & Acceptance Criteria:
   - Run `uv run python -m unittest discover -v -s tests -t .` -> all tests pass.
   - Check `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py` -> 0 diff.
   - Check `git grep -rnE "(import|from) +(heapq|bisect|queue|networkx|collections)" src` -> 0 matches.
   - Check `git grep -i "shipper_status" src/app.py` -> 0 matches.
   - Check `git log -n 10 --oneline` -> verify commit log structure.

5. Prepare Final Summary Report data:
   Include in handoff:
   (1) List of modified/created files grouped by part.
   (2) Test results (passed/total) and `git diff --stat` of 7 core files.
   (3) Notes on skipped optional items (T1, T2 of Part 8 skipped as requested).
   (4) Impact warning for PR reviewer.
