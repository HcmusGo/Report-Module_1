# Original User Request

## Initial Request — 2026-11-01T02:44:33Z

Kết nối phần tìm đường (routing) với phần đơn hàng (order) theo đúng nghiệp vụ cho hệ thống Quản lý Đơn hàng, Ưu tiên Chế biến & Tìm đường Shipper (1 Quán - 1 Shipper). Sửa chính xác các điểm trong danh sách nghiệp vụ được giao; không làm thêm việc ngoài danh sách; gặp mâu thuẫn hoặc chỗ không chắc thì ghi vào báo cáo cuối.

Working directory: D:\Module 1
Integrity mode: demo
The team must NOT: Use pre-built libraries or frameworks for core functionality (CẤM import collections/deque, heapq, bisect, queue, networkx; KHÔNG thêm dependency ngoài uv.lock; KHÔNG sửa pyproject.toml/uv.lock; KHÔNG sao chép logic hay sửa 7 file cốt lõi).

## Requirements

### R1. Dữ liệu chuẩn và kiểm tra baseline
Nạp và kiểm tra dữ liệu chuẩn theo Bước 0 và Phần 0:
- Đọc trước toàn bộ mã nguồn và tài liệu liên quan (`README.md`, `src/app.py`, `src/core/*.py`, `src/models/*.py`, `data/*.json`, `tests/*.py`) trước khi sửa bất kỳ file nào.
- Chạy kiểm tra baseline hiện tại bằng `uv run python -m unittest discover -s tests -t .` (đảm bảo 20 tests hiện có đều đạt).
- Kiểm tra dữ liệu: Ghi đè `data/map_graph.json` (6 đỉnh mentor + 2 nhà khách CUSTOMER_2, CUSTOMER_3; 12 cạnh hai chiều theo đúng tọa độ và trọng số quy định) và `data/users.json` (4 người dùng U001, U002, U003, U004) nếu file hiện tại vẫn là bản mẫu của bộ khung (map_graph 4 đỉnh, users 2 người). Nếu đã khác thì giữ nguyên và báo cáo.

### R2. routing_service và tìm đường gom chuyến (Phần 1)
Cập nhật `src/core/routing_service.py` hỗ trợ đầy đủ các chức năng định tuyến nghiệp vụ:
- Giữ nguyên chữ ký và hành vi của `path_to_coordinates(path, graph)` và `get_map_render_data(graph, start_id, goal_id)`, chỉ đổi typing sang kiểu dựng sẵn (list/dict/tuple).
- Định nghĩa các hằng số và ngoại lệ: `RESTAURANT_NODE_ID = "RESTAURANT"`, `MAP_PATH = "data/map_graph.json"`, và lớp ngoại lệ `MapDataError(Exception)`.
- Hàm `load_map_graph(path=MAP_PATH) -> Graph`: nạp bản đồ và phân biệt rõ 6 trường hợp lỗi bằng thông báo tiếng Việt cụ thể (raise MapDataError): (a) file không tồn tại; (b) file rỗng; (c) JSON sai cú pháp: sau khi `load_json` trả {} mà tồn tại `<path>.bak` thì thông báo cụ thể; (d) thiếu "nodes" hoặc không có đỉnh; (e) không có đỉnh `RESTAURANT_NODE_ID`; (f) `Graph.from_dict` ném `ValueError` thì bọc lại thành `MapDataError`.
- Hàm `is_valid_delivery_node(graph, node_id) -> bool`: kiểm tra node có trên bản đồ, khác `RESTAURANT_NODE_ID` và có đường đi từ Quán.
- NamedTuple `SingleRoute(delivery_node_id, path, coords, cost, expanded)` và hàm `route_single_order(graph, delivery_node_id, algorithm="dijkstra") -> SingleRoute` (ném ValueError nếu điểm giao không hợp lệ hoặc không có đường).
- NamedTuple `RouteLeg(start, end, path, cost)` và `BatchRoute(visit_order, legs, full_path, coords, total_cost, expanded_total, algorithm)`.
- Hàm `plan_batch_route(graph, delivery_node_ids, algorithm="dijkstra") -> BatchRoute` theo thuật toán NEAREST-NEIGHBOR:
  - Bỏ trùng điểm giao nhưng giữ nguyên thứ tự xuất hiện; danh sách rỗng hoặc có điểm không hợp lệ ném `ValueError`.
  - Bắt đầu tại `RESTAURANT_NODE_ID`; mỗi bước tính đường tới mọi điểm chưa thăm bằng `dijkstra()` hoặc `a_star()` của `routing_algo`, chọn điểm có chi phí nhỏ nhất (nếu hòa thì chọn id nhỏ hơn theo thứ tự chữ), di chuyển tới đó và lặp lại; không quay về Quán.
  - Nối `full_path`: path chặng đầu + path các chặng sau bỏ đỉnh đầu (không lặp đỉnh nối); `coords` ánh xạ từ `full_path`.
  - `expanded_total` = tổng `expanded` của các chặng được chọn (không cộng các lần tính ứng viên); `total_cost` = tổng cost các chặng.
  - Thêm chú thích độ phức tạp: O(k^2 (V+E) log V) với k điểm giao.
- Hàm `compare_trip_algorithms(graph, delivery_node_ids) -> {"dijkstra": BatchRoute, "astar": BatchRoute}` so sánh hai thuật toán.
- Hàm `build_map_figure_data(graph, full_path) -> dict` xuất dữ liệu gồm "nodes" (id, name, x, y, on_route), "edges" (x, y, x2, y2 - mỗi cạnh một lần), và "route" (step, node_id, x, y với step tăng theo thứ tự đi).
- Dùng đúng hàm `dijkstra`/`a_star` có sẵn trong `routing_algo`, tuyệt đối không viết lại thuật toán tìm đường.

### R3. order_manager, ràng buộc 1 shipper và quản lý khách hàng (Phần 2 & Phần 3)
Cập nhật `src/core/order_manager.py` và tạo mới mô-đun khách hàng:
- Khởi tạo `OrderManager.__init__(storage_path="data/orders.json", graph: Graph | None = None)`: nếu `graph=None` thì thử gọi `load_map_graph()`; nếu lỗi thì gán `self._graph = None` và `self.map_error = str(lỗi)`, không để app crash.
- Đóng gói private: đổi thành `_orders`, `_name_index`, `_email_index`, `_undo_stack`, `_redo_stack`, `_graph`. Thêm property `orders` chỉ đọc (trả bản sao dict), `get_order(id) -> Order | None`, `get_all_orders() -> list[Order]`, `can_undo() -> bool`, `can_redo() -> bool`. Giữ nguyên chữ ký các hàm tìm kiếm và lấy trạng thái.
- Trạng thái Shipper suy ra từ đơn: `get_shipper_status() -> "BUSY"` nếu có đơn DELIVERING, ngược lại `"IDLE"`; `get_current_trip() -> list[Order]` trả về các đơn đang DELIVERING.
- Hàm `create_order(order_id, customer_name, customer_email, items, created_at, is_vip=False, delivery_node_id=None) -> bool`: Bỏ tham số `shipper_status`. Từ chối (return False kèm `last_error` rõ ràng) khi: map lỗi; shipper BUSY ("Shipper đang giao chuyến hiện tại, chưa nhận đơn mới"); `delivery_node_id` rỗng/None hoặc không hợp lệ theo `is_valid_delivery_node` ("Điểm giao không hợp lệ"); và mọi kiểm tra cũ. Lưu `delivery_node_id` vào `Order`.
- Hàm `start_delivery(order_ids: list[str]) -> bool`: gom chuyến nguyên tử chỉ khi shipper IDLE, danh sách không rỗng/không trùng, mọi đơn tồn tại, đều READY và có điểm giao hợp lệ. Kiểm tra toàn bộ trước; chụp một snapshot duy nhất, chuyển tất cả sang DELIVERING bằng `order.change_status`, lưu file một lần, xóa redo stack (Undo một lần đưa cả chuyến về READY).
- Hàm `complete_delivery(order_id) -> bool`: đơn DELIVERING -> PAID (chụp một snapshot); khi đơn cuối cùng hoàn thành, shipper tự động về IDLE.
- Hàm `update_order_status(order_id, new_status)`: chặn mọi chuyển trạng thái VÀO DELIVERING ("Hãy dùng 'Bắt đầu giao' ở tab Bản đồ"); chặn CONFIRMED -> PREPARING nếu không phải đơn đứng đầu hàng đợi ưu tiên theo `PriorityEngine().next_order(self.get_orders_by_status(CONFIRMED), now=time.time())` (đơn khác bị từ chối kèm tên đơn đứng đầu).
- Hàm `load_orders` an toàn: bắt `(ValueError, KeyError, TypeError)` cho từng bản ghi, bỏ bản ghi hỏng và ghi vào `self.load_errors: list[str]`; nếu dữ liệu gốc không phải dict/list thì coi như rỗng và ghi `load_errors`. Tuyệt đối không để crash app vì orders.json.
- Tạo mới `src/models/customer.py`: Lớp `Customer(BaseEntity)` với `_name`, `_email`, `_is_vip`, `_node_id` (thuộc tính private + `@property` kiểm tra tên/email không rỗng, email có '@', node_id không rỗng), `to_dict()` dựa trên `super().to_dict()`, `@classmethod from_dict` ném `ValueError` tiếng Việt khi thiếu trường.
- Tạo mới `src/core/customer_manager.py`: Lớp `CustomerManager(storage_path="data/users.json")` CHỈ ĐỌC, đọc qua `load_json(default=[])`, bỏ qua bản ghi hỏng và ghi vào `self.load_errors`. Cung cấp `get_all()`, `get_by_id(id)`, `find_by_name(name)`, `find_by_email(email)` sử dụng `SortedIndex` (O(log n) + O(k)).

### R4. Giao diện Streamlit tab Đơn hàng và tab Bản đồ (Phần 4 & Phần 5)
Cập nhật giao diện người dùng trong `src/app.py`:
- Nguyên tắc: `app.py` không đọc file, không gọi `load_json`/`Graph`/thuật toán trực tiếp; chỉ gọi `routing_service`, `order_manager`, `customer_manager`.
- Tab Đơn hàng (`render_order_tab`):
  - Bỏ `st.form`, sử dụng widget thường có key.
  - Selectbox khách hàng (định dạng: "Tên - email - [VIP] - điểm giao: node") và multiselect món ăn nằm ngoài form để phản hồi tức thì.
  - Thông tin khách hàng lấy từ `CustomerManager`, hiển thị chỉ đọc (không có ô nhập tay; nếu không có khách hiển thị `st.warning`).
  - Ô số lượng của từng món hiển thị ngay khi món được chọn (cho phép đơn hàng đầu tiên có số lượng > 1).
  - Bỏ dropdown trạng thái shipper giả; thay bằng banner `st.info(f"Trạng thái Shipper: {om.get_shipper_status()}")`.
  - Nút "Tạo đơn hàng" gọi `om.create_order(..., is_vip=khách.is_vip, delivery_node_id=khách.node_id)`; hiển thị `st.error(om.last_error)` khi thất bại.
  - Hiển thị `st.warning` nêu số bản ghi bị bỏ qua nếu `om.load_errors` hoặc `customer_manager.load_errors` không rỗng.
  - Danh sách đơn hiển thị thêm cột "Điểm giao". Nút chuyển trạng thái nếu thất bại phải hiển thị `st.error(om.last_error)`. Đơn CONFIRMED hiển thị chú thích "Chế biến theo thứ tự ở tab Hàng đợi", đơn READY và DELIVERING hiển thị chú thích "Giao hàng ở tab Bản đồ" thay cho nút thao tác.
  - Các nút Hủy, Undo, Redo sử dụng `om.can_undo()`, `om.can_redo()`, `om.get_all_orders()` thay vì truy cập thuộc tính private.
  - Giữ nguyên tab Hàng đợi (`render_kitchen_tab`), chỉ cập nhật nếu có truy cập thuộc tính đã chuyển thành private.
- Tab Bản đồ (`render_map_tab`):
  - Thay thế toàn bộ cụm máy tính khoảng cách bằng màn hình giao hàng nghiệp vụ.
  - Nạp bản đồ bằng `load_map_graph()`, bắt `MapDataError -> st.error(thông báo)` và return (chỉ lưu vào session_state khi thành công).
  - Banner trạng thái Shipper (IDLE/BUSY) từ `om.get_shipper_status()`.
  - Bảng danh sách đơn READY: Mã đơn, Khách, VIP, Điểm giao, Quãng đường đơn lẻ từ Quán (`route_single_order`; nếu lỗi hiển thị "không có đường").
  - Multiselect chọn các đơn READY để gom chuyến -> hiển thị kết quả từ `plan_batch_route`: thứ tự thăm, chi tiết từng chặng, full_path, tổng quãng đường, và bảng so sánh Dijkstra vs A* (tổng chi phí, số đỉnh đã duyệt) từ `compare_trip_algorithms`.
  - Nút "Bắt đầu giao" gọi `om.start_delivery(các đơn đã chọn)`; thành công gọi `st.rerun()`, thất bại hiển thị `st.error(om.last_error)`. Nút bị disable khi Shipper BUSY hoặc chưa chọn đơn.
  - Khi Shipper BUSY: liệt kê chuyến hiện tại (`om.get_current_trip()`), mỗi đơn có nút "Đã giao" gọi `om.complete_delivery(id)`. Vẽ lộ trình dự kiến của chuyến (ghi chú "tính từ Quán").
  - Vẽ bản đồ trực quan bằng Altair (`st.altair_chart`), không dùng `st.line_chart`: Dữ liệu từ `build_map_figure_data`. Gồm 3 lớp: Lớp 1 các cạnh (`mark_rule` màu xám nhạt), Lớp 2 các đỉnh (`mark_circle`, nhãn id bằng `mark_text`), Lớp 3 lộ trình (`mark_line` nổi bật với encoding `order=alt.Order("step:Q")` để vẽ đúng thứ tự hành trình).

### R5. Phạm vi tùy chọn, kiểm thử, tài liệu và Git (Phần 6, Phần 7, Phần 8 & Git)
- Phạm vi cốt lõi và tùy chọn:
  - Bỏ qua các mục tùy chọn T1 và T2 của Phần 8 theo đúng phản hồi của người dùng.
  - Tuyệt đối giữ nguyên từng byte 7 file cốt lõi: `src/core/routing_algo.py`, `src/core/priority_engine.py`, `src/models/graph_node.py`, `src/models/base.py`, `src/core/storage.py`, `src/core/structures.py`, `src/core/menu_manager.py`.
- Dọn dẹp mã nguồn:
  - Sửa `src/models/menu_item.py` chỉ dòng import dự phòng thành `from src.models.base import BaseEntity`.
  - Đổi typing cũ sang kiểu dựng sẵn trong `routing_service.py`, ngắt các dòng > 100 ký tự, xóa import thừa trong tests và `app.py`.
  - Bổ sung vào `.github/CODEOWNERS`: `/src/models/customer.py`, `/src/core/customer_manager.py`, `/tests/test_customer_manager.py` gắn `@thanvanthelam`; `/tests/test_routing_service.py` gắn `@DUT26DoQuyen`.
- Bộ kiểm thử tự động (sử dụng thư mục tạm cho file JSON và Graph dict, không sửa data gốc):
  - `tests/test_routing_service.py`: kiểm tra đủ 6 trường hợp lỗi của `load_map_graph` (kể cả trường hợp file .bak), `is_valid_delivery_node` ("ZZZ", "RESTAURANT", đỉnh cô lập trả False), `route_single_order`, `plan_batch_route` trên bản đồ chuẩn (thứ tự thăm [CUSTOMER_3, CUSTOMER, CUSTOMER_2], full_path đúng chuẩn, tổng 16.0 với `assertAlmostEqual`, full_path không có hai đỉnh liên tiếp trùng nhau, tổng bằng tổng các chặng, Dijkstra và A* cùng tổng chi phí, điểm giao trùng chỉ thăm một lần, danh sách rỗng/điểm sai ném ValueError), `build_map_figure_data` có route đúng thứ tự step.
  - `tests/test_order_manager.py`: cập nhật các test gọi `create_order` sang chữ ký mới; test chuyển DELIVERING qua `update_order_status` đổi sang `start_delivery`; giữ nguyên mục đích kiểm thử hiện có. Bổ sung: shipper IDLE/BUSY; `create_order` từ chối khi BUSY hoặc delivery_node_id sai/None/"RESTAURANT"; `start_delivery` chỉ với đơn READY, từ chối khi BUSY; `update_order_status` chặn READY->DELIVERING và chặn PREPARING sai thứ tự ưu tiên; `complete_delivery` chuyển PAID và shipper về IDLE; Undo/Redo cả chuyến một lần; `load_orders` an toàn khi có bản ghi hỏng; tính bất biến của dict trả về từ property `orders`.
  - `tests/test_customer_manager.py`: đọc users, `find_by_name`/`find_by_email` (không phân biệt hoa thường, trùng tên), bỏ qua bản ghi hỏng, file thiếu trả về rỗng.
  - Smoke test: Sử dụng `streamlit.testing.v1.AppTest` mở `src/app.py`, xác nhận 4 tab không có ngoại lệ; tab Bản đồ hiển thị multiselect đơn READY khi có đơn.
- Tài liệu: Bổ sung mục "Cách dùng app theo đúng nghiệp vụ" vào `README.md` theo 7 bước demo chuẩn với dữ liệu mẫu và ghi chú về file backup .bak.
- Quy trình Git: Tạo nhánh mới `feat/connect-routing-order` từ nhánh hiện tại. Mỗi phần 1-8 tạo một commit riêng với tiền tố chuẩn (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`). Chỉ git add đúng các file được phép sửa; không commit cache, `.venv`, `data/orders.json` chạy thật; không push, không sửa nhánh main.
- Báo cáo cuối (bắt buộc): (1) danh sách file đã sửa/tạo theo từng phần; (2) kết quả test (đạt/tổng) và kết quả `git diff --stat` của 7 file cấm sửa; (3) các điểm không làm được hoặc quyết định khác kèm lý do; (4) cảnh báo ảnh hưởng các file để trưởng nhóm thông báo trước khi tạo PR.

## Acceptance Criteria

### Kiểm thử và Độ toàn vẹn mã nguồn
- [ ] Lệnh `uv run python -m unittest discover -s tests -t .` chạy đạt 100% test cases (toàn bộ tests đạt OK).
- [ ] Lệnh `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py` trả về kết quả rỗng.
- [ ] Lệnh `grep -rnE "(import|from) +(heapq|bisect|queue|networkx|collections)" src` không tìm thấy dòng nào.
- [ ] Lệnh `grep "shipper_status" src/app.py` không còn kết quả; `src/app.py` không import `load_json`/`Graph` và không gọi `st.line_chart`.

### Kịch bản nghiệp vụ chuẩn
- [ ] Kịch bản end-to-end trên dữ liệu chuẩn hoạt động chính xác:
  - Tạo 3 đơn cho U001, U002, U003 -> chuyển sang CONFIRMED.
  - Chuyển sang PREPARING tuân thủ đúng thứ tự ưu tiên của `PriorityEngine` -> chuyển sang READY.
  - Gom chuyến 3 điểm qua `plan_batch_route` cho thứ tự thăm CUSTOMER_3 -> CUSTOMER -> CUSTOMER_2 với full_path = RESTAURANT, B, CUSTOMER_3, D, CUSTOMER, CUSTOMER_2 và tổng quãng đường = 16.0 (Dijkstra và A* cho cùng tổng chi phí).
  - Bắt đầu giao (`start_delivery`) đưa cả 3 đơn sang DELIVERING, trạng thái shipper chuyển sang BUSY.
  - Khi shipper BUSY, thao tác `create_order` đơn mới bị từ chối với thông báo "Shipper đang giao chuyến hiện tại, chưa nhận đơn mới".
  - Bấm "Đã giao" (`complete_delivery`) từng đơn chuyển sang PAID; khi đơn cuối cùng hoàn thành, shipper tự động chuyển về IDLE.
  - Undo một lần sau `start_delivery` đưa toàn bộ chuyến về READY; Redo khôi phục lại trạng thái.
- [ ] Hàm `create_order` từ chối (trả về False) với `delivery_node_id` là None, "ZZZ", hoặc "RESTAURANT".
- [ ] Hàm `update_order_status` từ chối chuyển trạng thái từ READY sang DELIVERING.
