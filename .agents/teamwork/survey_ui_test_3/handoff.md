# Báo Cáo Khảo Sát Chi Tiết: Giao Diện Streamlit UI, Hạ Tầng Kiểm Thử & Metadata Git/Tài Liệu

**Agent**: `survey_ui_test_3` (teamwork_explorer)  
**Thời gian khảo sát**: 2026-11-01T02:53:00Z  
**Mục tiêu**: Khảo sát hiện trạng UI (`src/app.py`), hạ tầng kiểm thử (`tests/`), Git repo, và tài liệu (`README.md`, `.github/CODEOWNERS`) đối chiếu với yêu cầu `ORIGINAL_REQUEST.md`.

---

## 1. Observation (Các Quan Sát Thực Tế Trực Tiếp)

### 1.1. Hiện trạng Streamlit UI (`src/app.py`)
- **Đường dẫn**: `D:\Module 1\src\app.py` (tổng 559 dòng).
- **Cấu trúc Tab trong hàm `main()` (dòng 544-555)**:
  ```python
  tab_map, tab_menu, tab_kitchen, tab_order = st.tabs(
      ["Bản đồ / Lộ trình", "Menu", "Hàng đợi chế biến", "Đơn hàng"]
  )
  with tab_map:
      render_map_tab()
  with tab_menu:
      render_menu_tab()
  with tab_kitchen:
      render_kitchen_tab()
  with tab_order:
      render_order_tab()
  ```
  Thứ tự tab hiện tại: (1) `render_map_tab`, (2) `render_menu_tab`, (3) `render_kitchen_tab`, (4) `render_order_tab`.

- **Quản lý `session_state` hiện tại**:
  - Dòng 29-34: `get_order_manager()` khởi tạo `st.session_state.order_manager = OrderManager()`.
  - Dòng 36-40: `get_menu_manager()` khởi tạo `st.session_state.menu_manager = MenuManager()`.
  - Dòng 48-55 trong `render_map_tab()`: nạp trực tiếp file `data/map_graph.json` và lưu `st.session_state.graph = Graph.from_dict(raw_data)`.
  - Hiện tại **chưa có** `get_customer_manager()` trong `session_state`.

- **Các vi phạm kiến trúc 3 tầng và lệnh cấm trong `src/app.py`**:
  - **Đọc file JSON và gọi Graph trực tiếp** (dòng 24-25, 49-53):
    ```python
    24: from src.core.storage import load_json
    25: from src.models.graph_node import Graph
    ...
    49: raw_data = load_json("data/map_graph.json", default={})
    ...
    53: st.session_state.graph = Graph.from_dict(raw_data)
    ```
    *Vi phạm*: R4 quy định `app.py` không đọc file, không import `load_json`/`Graph`, nạp bản đồ phải thông qua `routing_service.load_map_graph()`.
  - **Sử dụng `st.line_chart` thay vì Altair** (dòng 73):
    ```python
    73: st.line_chart(chart_data, x="x", y="y")
    ```
    *Vi phạm*: Tiêu chí chấp nhận AC yêu cầu `src/app.py` không gọi `st.line_chart`, phải dùng `st.altair_chart` với 3 layer (`mark_rule`, `mark_circle` + `mark_text`, `mark_line` theo `order=alt.Order("step:Q")`).
  - **Trường `shipper_status` giả trong form tạo đơn** (dòng 379-383, 425):
    ```python
    379: shipper_status = st.selectbox(
    380:     "Trạng thái Shipper *",
    381:     ["IDLE", "BUSY", "BATCHING_ALLOWED"],
    ...
    425:     shipper_status=shipper_status,
    ```
    *Vi phạm*: AC yêu cầu `grep "shipper_status" src/app.py` không còn kết quả; trạng thái shipper phải được suy ra từ đơn hàng qua `om.get_shipper_status()`.
  - **Dùng `st.form` và ô nhập tay khách hàng** (dòng 372-433):
    - Đang dùng `with st.form("create_order_form"):`, các widget `customer_name`, `customer_email` là text input tự nhập tay (không liên kết `CustomerManager`).
    - Nút submit nằm trong form làm chậm phản hồi khi chọn món và chọn số lượng.
  - **Truy cập trực tiếp thuộc tính nội bộ / private của `OrderManager`**:
    - Dòng 446, 453: `list(om.orders.values())`
    - Dòng 458: `om.undo_stack.is_empty()`
    - Dòng 464: `om.redo_stack.is_empty()`
    *Vi phạm*: Phải dùng `om.get_all_orders()`, `om.can_undo()`, `om.can_redo()`.
  - **Hiện trạng tab Bản đồ (`render_map_tab`)**:
    - Chỉ là một máy tính khoảng cách điểm-tới-điểm đơn giản (`st.selectbox` chọn start_id, goal_id, nút tính toán).
    - Hoàn toàn chưa có màn hình giao hàng nghiệp vụ: chưa có danh sách đơn READY, chưa có multiselect gom chuyến `plan_batch_route`, chưa có so sánh Dijkstra vs A*, chưa có bảng chuyến đi hiện tại khi BUSY kèm nút "Đã giao" `complete_delivery(id)`.

---

### 1.2. Hiện trạng Hạ Tầng Kiểm Thử (`tests/`)

- **Danh sách file kiểm thử hiện có**:
  ```
  tests/
  ├── __init__.py
  ├── test_order.py           (7 tests)
  ├── test_order_manager.py   (7 tests)
  └── test_priority_engine.py (6 tests)
  ```
  Tổng cộng: 20 test cases.

- **Kết quả chạy kiểm tra baseline**:
  Lệnh chạy: `cd 'D:\Module 1'; uv run python -m unittest discover -s tests -t .`
  Kết quả:
  ```
  ....................
  ----------------------------------------------------------------------
  Ran 20 tests in 0.088s

  OK
  ```
  100% (20/20 tests) đạt OK.

- **Chi tiết `tests/test_order_manager.py` (hiện tại)**:
  - Dòng 23-77 (`test_create_order_shipper_status_and_errors`): truyền tham số `shipper_status="BUSY"`, `"IDLE"`, `"BATCHING_ALLOWED"` vào `om.create_order(...)`. Không truyền `delivery_node_id`.
  - Dòng 86 (`test_cannot_cancel_delivering_or_paid`): gọi `self.om.update_order_status("O001", OrderStatus.DELIVERING)` trực tiếp.
  - Cả hai chỗ này sẽ bị vỡ (fail) khi cài đặt R3 (vì `create_order` bỏ tham số `shipper_status` và bắt buộc `delivery_node_id` hợp lệ; `update_order_status` chặn chuyển sang DELIVERING).
  - Thiếu các test nghiệp vụ mới theo R5:
    - Kiểm tra shipper IDLE/BUSY tự động suy ra từ trạng thái đơn.
    - `create_order` từ chối khi shipper BUSY hoặc `delivery_node_id` không hợp lệ (None, "ZZZ", "RESTAURANT").
    - `start_delivery` chỉ gom đơn READY, từ chối khi BUSY, chuyển nguyên tử sang DELIVERING.
    - `complete_delivery` chuyển PAID và shipper tự về IDLE khi xong đơn cuối.
    - Undo/Redo nguyên tử cả chuyến đi trong một lần gọi.
    - `update_order_status` chặn CONFIRMED -> PREPARING nếu sai thứ tự ưu tiên `PriorityEngine`.
    - Tính bất biến (read-only copy) của property `orders`.
    - `load_orders` an toàn không crash khi có bản ghi hỏng (bỏ qua và ghi `self.load_errors`).

- **Hiện trạng `tests/test_routing_service.py`**:
  - **CHƯA TỒN TẠI** trong thư mục `tests/`.
  - Cần phải tạo mới hoàn toàn để kiểm thử:
    1. Đủ 6 trường hợp ngoại lệ của `load_map_graph(path)` raise `MapDataError`: file không tồn tại, file rỗng, JSON hỏng (kèm kiểm tra `.bak`), thiếu nodes / rỗng, thiếu RESTAURANT, Graph.from_dict ValueError.
    2. `is_valid_delivery_node`: kiểm tra node lạ ("ZZZ"), node "RESTAURANT", node cô lập trả False; node hợp lệ có đường từ Quán trả True.
    3. `route_single_order`: trả về SingleRoute chuẩn.
    4. `plan_batch_route`: trên bản đồ chuẩn thứ tự thăm `[CUSTOMER_3, CUSTOMER, CUSTOMER_2]`, full_path `['RESTAURANT', 'B', 'CUSTOMER_3', 'D', 'CUSTOMER', 'CUSTOMER_2']`, tổng chi phí 16.0 (`assertAlmostEqual`), Dijkstra và A* có cùng tổng chi phí, không trùng lặp đỉnh liên tiếp, danh sách rỗng/node sai raise ValueError.
    5. `compare_trip_algorithms`: so sánh 2 thuật toán.
    6. `build_map_figure_data`: route có step tăng dần.

- **Hiện trạng `tests/test_customer_manager.py`**:
  - **CHƯA TỒN TẠI** trong thư mục `tests/`.
  - Cần tạo mới để kiểm thử `CustomerManager(storage_path)`: nạp `users.json`, tìm kiếm `find_by_name`/`find_by_email` (không phân biệt hoa thường, trùng lặp tên), xử lý an toàn khi file thiếu (trả về rỗng) hoặc có bản ghi hỏng (bỏ qua và ghi `load_errors`).

- **Khảo sát tính khả thi của `streamlit.testing.v1.AppTest`**:
  - Đã thực hiện kiểm tra thực tế:
    ```bash
    uv run python -c "from streamlit.testing.v1 import AppTest; at = AppTest.from_file('src/app.py', default_timeout=15); at.run(); print('Exceptions:', len(at.exception))"
    ```
  - **Kết quả thực tế**:
    - `AppTest run completed, len exceptions: 0` (0 ngoại lệ phát sinh!).
    - Thống kê phần tử UI bắt được qua AppTest: `Title: 2`, `Subheader: 5`, `Tabs: 4`, `Selectbox: 7`, `Button: 8`.
    - **Lưu ý kỹ thuật quan trọng**: Streamlit AppTest có `default_timeout=3` giây theo mặc định. Trong môi trường kiểm thử không có GPU/chạy bare mode lần đầu, khởi động mất khoảng 4-6 giây. Do đó khi viết smoke test bằng `AppTest`, **BẮT BUỘC** cấu hình `default_timeout=15` hoặc `at.run(timeout=15)` để tránh lỗi `RuntimeError: AppTest script run timed out after 3(s)`.

---

### 1.3. Hiện trạng Git Repository & Metadata

- **Kết quả `git status`**:
  ```
  On branch main
  Your branch is up to date with 'origin/main'.

  Untracked files:
    .agents/
    data/orders.json
  ```
  - Working tree trên `main` hiện đang sạch (chỉ có `.agents/` và file data sinh ra khi chạy thử).
  - Không có uncommitted changes trên code nguồn.

- **Kết quả `git branch`**:
  Các nhánh hiện có:
  `chore/reset-project`, `feat/m1-routing`, `feat/m4-priority`, `fix/order-priority-integration`, `* main`, `models`, `review/lam-order-manager`, `test-pr-14`, `test-pr-15`, `test-pr-24`.
  - Nhánh mới theo R8 phải là: `feat/connect-routing-order` checkout từ `main`.

- **Kết quả `git log -n 5`**:
  ```
  1d542dc Merge pull request #24 from HcmusGo/feat/m2-map
  5255a81 fix: load map_graph.json vào Graph object, sửa routing_service dùng đúng interface
  661204e feat: implement routing service and map tab UI
  1f9edda Merge branch 'fix/order-priority-integration'
  c460c22 refactor: don dep imports, bo sung type hints va complexity comments (Phan D)
  ```

- **Kiểm tra 7 file cốt lõi cấm sửa**:
  Lệnh: `git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py`
  - Kết quả: Rỗng (hoàn toàn nguyên vẹn 100%).

- **Hiện trạng `.github/CODEOWNERS`**:
  Nội dung hiện tại (10 dòng):
  ```
  /src/models/graph_node.py      @HcmusGo
  /src/core/routing_algo.py      @HcmusGo
  /src/core/routing_service.py   @DUT26DoQuyen
  /src/models/menu_item.py       @cleivoid
  /src/core/storage.py           @cleivoid
  /src/core/menu_manager.py      @cleivoid
  /src/core/structures.py        @btam200801
  /src/core/priority_engine.py   @btam200801
  /src/models/order.py           @thanvanthelam
  /src/core/order_manager.py     @thanvanthelam
  ```
  - Các mục cần bổ sung theo R5 / R8:
    ```
    /src/models/customer.py        @thanvanthelam
    /src/core/customer_manager.py  @thanvanthelam
    /tests/test_customer_manager.py @thanvanthelam
    /tests/test_routing_service.py @DUT26DoQuyen
    ```

- **Hiện trạng cấu trúc `README.md`**:
  - Hiện tại gồm 105 dòng với các mục:
    1. Tiêu đề & Giới thiệu
    2. `## Tính năng chính` (kèm `### Vòng đời đơn hàng`)
    3. `## Công nghệ`
    4. `## Ràng buộc kỹ thuật`
    5. `## Cấu trúc thư mục`
    6. `## Thành viên và phân công`
    7. `## Cài đặt và chạy` (dòng 85-93)
    8. `## Dữ liệu` (dòng 94-98)
    9. `## Quy ước làm việc nhóm` (dòng 99-105)
  - **Vị trí đề xuất đặt mục 7 bước demo chuẩn**:
    - Ngay sau mục `## Cài đặt và chạy` (trước mục `## Dữ liệu`), đặt thành `## Cách dùng app theo đúng nghiệp vụ (7 bước demo chuẩn)`. Đây là vị trí người dùng/giảng viên/mentor sẽ đọc ngay sau khi biết cách chạy lệnh `uv run python -m streamlit run src/app.py`.

---

## 2. Logic Chain (Chuỗi Lập Luận Từ Quan Sát Đến Kết Luận)

1. **Từ Quan Sát 1.1**:
   - `src/app.py` đang import trực tiếp `load_json` và `Graph`, tự đọc file `data/map_graph.json` tại dòng 49.
   - Do đó, để tuân thủ kiến trúc 3 tầng và tiêu chí chấp nhận AC, `src/app.py` phải gỡ bỏ hoàn toàn `from src.core.storage import load_json` và `from src.models.graph_node import Graph`.
   - Toàn bộ việc nạp bản đồ trong `app.py` phải chuyển sang gọi `routing_service.load_map_graph()`, đồng thời bắt ngoại lệ `MapDataError` để hiển thị `st.error(str(err))`.

2. **Từ Quan Sát 1.1 về `shipper_status` và Tab Đơn hàng**:
   - AC yêu cầu: `grep "shipper_status" src/app.py` không còn kết quả.
   - Hiện tại dòng 379 và 425 vẫn chứa `shipper_status` (selectbox và đối số truyền vào `create_order`).
   - Hơn nữa, việc sử dụng `st.form` khiến giao diện không thể phản hồi tức thì khi người dùng chọn khách hàng hay chọn món để hiện số lượng.
   - Do đó, cần loại bỏ `st.form`, sử dụng widget thường kèm `key`, lấy khách hàng từ `CustomerManager` (định dạng: `Tên - email - [VIP] - điểm giao: node`), hiển thị banner thông tin shipper qua `om.get_shipper_status()`, và nút tạo đơn gọi `om.create_order(..., is_vip=khách.is_vip, delivery_node_id=khách.node_id)`.

3. **Từ Quan Sát 1.1 về Tab Bản đồ và Altair**:
   - Hiện tại `render_map_tab` chỉ tính khoảng cách đơn lẻ giữa 2 điểm và vẽ bằng `st.line_chart`.
   - Để kết nối nghiệp vụ Order và Routing theo R4, Tab Bản đồ cần được tái cấu trúc hoàn toàn thành màn hình giao hàng nghiệp vụ:
     - Bảng đơn READY kèm khoảng cách đơn lẻ từ Quán (`route_single_order`).
     - Multiselect chọn các đơn READY để gom chuyến theo Nearest-Neighbor (`plan_batch_route`).
     - Bảng so sánh hiệu năng Dijkstra vs A* (`compare_trip_algorithms`).
     - Nút "Bắt đầu giao" kích hoạt gom chuyến nguyên tử (`om.start_delivery`).
     - Bảng quản lý chuyến đi đang giao khi Shipper BUSY kèm nút "Đã giao" (`om.complete_delivery`).
     - Biểu đồ Altair 3 lớp trực quan hóa đồ thị và hành trình từ `build_map_figure_data(graph, full_path)`.

4. **Từ Quan Sát 1.2 về Test Baseline & Test Mới**:
   - 20 test hiện có đều PASS, nhưng `test_order_manager.py` sử dụng chữ ký cũ (`shipper_status`) và gọi `update_order_status(..., DELIVERING)`. Khi `OrderManager` được cập nhật theo R3, các test này sẽ FAIL nếu không được cập nhật song song.
   - Hiện tại chưa hề có test cho `routing_service` và `customer_manager`. Cần viết mới hoàn toàn `tests/test_routing_service.py` và `tests/test_customer_manager.py`.
   - Kết quả thử nghiệm `AppTest` khẳng định smoke test giao diện Streamlit hoàn toàn khả thi và chạy ổn định khi đặt timeout >= 10s (đã xác thực len(at.exception) == 0). Có thể tạo `tests/test_app_smoke.py` sử dụng `streamlit.testing.v1.AppTest`.

5. **Từ Quan Sát 1.3 về Git và Tài Liệu**:
   - Git working tree sạch trên nhánh `main`. Nhánh mới `feat/connect-routing-order` cần được tạo từ `main` trước khi tiến hành code.
   - File `.github/CODEOWNERS` cần thêm 4 dòng phân quyền cho các file mới/file test.
   - `README.md` cần bổ sung mục hướng dẫn 7 bước chuẩn nghiệp vụ ngay sau mục cài đặt.

---

## 3. Caveats (Các Điểm Lưu Ý & Giới Hạn)

1. **Tốc độ thực thi của Streamlit AppTest**:
   - Khởi tạo `AppTest` lần đầu có thể mất từ 3-5 giây trên Windows. Nếu không chỉ định `default_timeout=15`, test smoke có thể bị timeout ngẫu nhiên. Cần đặt timeout rõ ràng trong code test smoke.
2. **Altair Deprecation Warning**:
   - Streamlit hiển thị warning: `Please replace use_container_width with width`. Dù hiện tại vẫn hoạt động tốt, nên lưu ý nếu Streamlit nâng cấp phiên bản trong tương lai. Hiện tại giữ `use_container_width=True` theo đúng yêu cầu đề bài.
3. **Độ bất biến của Dữ liệu Test**:
   - Khi chạy test cho `OrderManager` và `CustomerManager`, luôn dùng `tempfile.TemporaryDirectory` để tạo file JSON tạm, tuyệt đối không trỏ vào `data/orders.json` hay `data/users.json` thật làm thay đổi dữ liệu gốc.
4. **Giới hạn khảo sát**:
   - Agent này là `survey_ui_test_3` (read-only investigation), không trực tiếp sửa đổi code hay tạo branch git. Mọi triển khai code sẽ do các agent implementer thực hiện theo kế hoạch phân công của orchestrator.

---

## 4. Conclusion (Kết Luận & Đề Xuất Hành Động Cụ Thể)

### 4.1. Tóm tắt Đánh Giá
- **UI (`src/app.py`)**: Đang tồn tại 5 điểm cần sửa chữa lớn:
  1. Loại bỏ hoàn toàn import `load_json` và `Graph`, chuyển sang nạp qua `routing_service.load_map_graph()`.
  2. Bỏ `st.form`, bỏ ô nhập tay thông tin khách, chuyển sang selectbox liên kết `CustomerManager`.
  3. Bỏ toàn bộ chữ `shipper_status` trong `app.py`, thay bằng banner đọc từ `om.get_shipper_status()`.
  4. Thay thế toàn bộ cụm máy tính khoảng cách trong `render_map_tab` bằng màn hình gom chuyến, quản lý chuyến giao hàng, và biểu đồ Altair 3 layer.
  5. Thay các truy cập thuộc tính private (`orders.values()`, `undo_stack.is_empty()`) bằng các phương thức public (`get_all_orders()`, `can_undo()`, `can_redo()`).
- **Testing (`tests/`)**:
  1. Cập nhật `tests/test_order_manager.py` (chữ ký `create_order`, gọi `start_delivery`, kiểm tra từ chối sai thứ tự ưu tiên, load_errors).
  2. Tạo mới `tests/test_routing_service.py` (bao phủ đủ 6 lỗi load map, validate delivery node, single route, batch route nearest neighbor, so sánh Dijkstra vs A*, build map figure data).
  3. Tạo mới `tests/test_customer_manager.py` (đọc users, tìm kiếm nhị phân không phân biệt hoa thường, xử lý lỗi an toàn).
  4. Tạo mới test smoke giao diện `tests/test_app_smoke.py` dùng `AppTest` với `default_timeout=15`.
- **Git & Tài liệu**:
  1. Checkout branch `feat/connect-routing-order` từ `main`.
  2. Cập nhật 4 entry mới vào `.github/CODEOWNERS`.
  3. Thêm mục 7 bước demo nghiệp vụ chuẩn vào `README.md`.

---

## 5. Verification Method (Phương Pháp Xác Minh Độc Lập)

Khi các thay đổi được triển khai, người kiểm tra có thể xác minh độc lập theo các bước sau:

1. **Xác minh không vi phạm thư viện cấm**:
   ```powershell
   cd 'D:\Module 1'
   git grep -nE "(import|from) +(heapq|bisect|queue|networkx|collections)" src
   # Kết quả mong đợi: exit code 1 (không có dòng nào)
   ```

2. **Xác minh 7 file cốt lõi không bị chạm vào**:
   ```powershell
   cd 'D:\Module 1'
   git diff --stat -- src/core/routing_algo.py src/core/priority_engine.py src/models/graph_node.py src/models/base.py src/core/storage.py src/core/structures.py src/core/menu_manager.py
   # Kết quả mong đợi: hoàn toàn rỗng
   ```

3. **Xác minh không còn `shipper_status`, `load_json`, `Graph`, `st.line_chart` trong `src/app.py`**:
   ```powershell
   cd 'D:\Module 1'
   git grep -n "shipper_status" src/app.py
   git grep -nE "(from src.core.storage import load_json|from src.models.graph_node import Graph|line_chart)" src/app.py
   # Kết quả mong đợi: đều không tìm thấy kết quả
   ```

4. **Xác minh bộ kiểm thử tự động đạt 100%**:
   ```powershell
   cd 'D:\Module 1'
   uv run python -m unittest discover -s tests -t .
   # Kết quả mong đợi: toàn bộ test (cả test cũ được cập nhật và các test mới) đều đạt OK
   ```

5. **Xác minh smoke test Streamlit AppTest**:
   ```powershell
   cd 'D:\Module 1'
   uv run python -c "from streamlit.testing.v1 import AppTest; at = AppTest.from_file('src/app.py', default_timeout=15); at.run(); assert len(at.exception) == 0; print('Smoke test PASS!')"
   # Kết quả mong đợi: Smoke test PASS!
   ```

6. **Xác minh CODEOWNERS**:
   Kiểm tra 4 dòng bổ sung cho `customer.py`, `customer_manager.py`, `test_customer_manager.py` (@thanvanthelam) và `test_routing_service.py` (@DUT26DoQuyen).
