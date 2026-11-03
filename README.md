# Hệ thống Quản lý Đơn hàng, Ưu tiên Chế biến & Tìm đường Shipper

Đồ án Module 1 — mô hình **1 Quán – 1 Shipper**. Hệ thống quản lý menu, nhận và xử lý đơn hàng theo độ ưu tiên, theo dõi vòng đời đơn, **gom chuyến giao nhiều điểm** và tìm đường ngắn nhất cho Shipper, hiển thị trực quan trên giao diện web Streamlit.

Điểm đặc biệt của đồ án: toàn bộ cấu trúc dữ liệu và thuật toán (Stack, Min-Heap / Priority Queue, Graph, Binary Search, Dijkstra, A*) đều **tự cài đặt bằng OOP**, không dùng thư viện có sẵn.

## Tính năng chính

- **Tìm đường cho Shipper:** bản đồ biểu diễn bằng danh sách kề, tìm đường ngắn nhất bằng Dijkstra và A* (so sánh chi phí và số đỉnh đã duyệt).
- **Gom chuyến giao hàng:** chọn nhiều đơn `READY`, lập lộ trình theo giải thuật tham lam Nearest-Neighbor, không quay về Quán.
- **Hiển thị bản đồ:** biểu đồ Altair 3 lớp (cạnh, đỉnh, lộ trình) vẽ từ tọa độ (x, y) của các đỉnh.
- **Quản lý Menu:** thêm, sửa, xóa, xem và tìm kiếm món ăn theo tên.
- **Ưu tiên chế biến:** xếp hạng đơn theo khách VIP, thời gian chờ và thời gian chế biến bằng Priority Queue tự viết, có cơ chế Aging chống bỏ đói.
- **Vòng đời đơn hàng:** state machine chặt chẽ, Undo / Redo bằng snapshot, tìm đơn theo Tên hoặc Email.
- **Trạng thái Shipper suy diễn:** `BUSY` nếu có đơn đang `DELIVERING`, ngược lại `IDLE`; khi `BUSY` hệ thống từ chối nhận đơn mới.
- **An toàn dữ liệu:** file JSON hỏng cú pháp được tự động đổi thành `.bak`, bản ghi lỗi được ghi vào `load_errors` thay vì làm app crash.

## Kiến trúc

Ba tầng tách biệt: `src/models/` (entity) → `src/core/` (CTDL, thuật toán, nghiệp vụ, đọc/ghi JSON) → `src/app.py` (giao diện). `app.py` chỉ gọi các phương thức cấp cao của `core`, không chứa logic thuật toán hay đọc/ghi file.

```
[ users.json ] ───> [ CustomerManager ]
                           │ (thông tin khách, VIP, điểm giao)
                           ▼
[ MenuManager ] ──> [ OrderManager ] <─── [ PriorityEngine ]   (thứ tự chế biến)
 (menu.json)         (orders.json)               │
                           │                     ▼
                           │            [ CustomPriorityQueue ← CustomMinHeap ]
                           ▼  (nạp bản đồ, kiểm tra điểm giao, lộ trình đơn/chuyến)
[ map_graph.json ] ─> [ routing_service ] <─── [ routing_algo ]  (dijkstra, a_star)
                           │
                           ▼
                    [ src/app.py ]   4 tab: Bản đồ / Menu / Hàng đợi chế biến / Đơn hàng
```

`storage.py` (đọc/ghi JSON an toàn) và `structures.py` (`SortedIndex`, `CustomStack`, `CustomMinHeap`, `CustomPriorityQueue`) được dùng chung bởi nhiều module.

### Vòng đời đơn hàng

```
PLACED → CONFIRMED → PREPARING → READY → DELIVERING → PAID
   │          │           │         │
   └──────────┴───────────┴─────────┴──→ CANCELLED
```

- `PAID` và `CANCELLED` là trạng thái kết thúc.
- **Không được hủy** khi đang `DELIVERING` hoặc đã `PAID`.
- **Không chuyển trực tiếp vào `DELIVERING`** bằng `update_order_status`; phải dùng **Bắt đầu giao** (`start_delivery`) ở tab Bản đồ.
- `CONFIRMED → PREPARING` chỉ được phép với đơn đứng đầu hàng đợi ưu tiên của `PriorityEngine`.

### Công thức ưu tiên chế biến

```
score = prep_minutes − wait_minutes − (30 nếu khách VIP)
```

Điểm **nhỏ hơn thì làm trước**; hòa điểm thì đơn tạo sớm hơn làm trước. Vì `wait_minutes` tăng theo thời gian nên điểm được tính lại tại thời điểm xếp hạng (Aging): một đơn thường đã chờ 40 phút sẽ vượt qua đơn VIP mới đến (−40 < −30), tránh bị bỏ đói.

## Công nghệ

- Python (`.python-version` = 3.13, `requires-python >= 3.10`), quản lý package bằng [`uv`](https://docs.astral.sh/uv/)
- Giao diện: [Streamlit](https://streamlit.io/) (kéo theo Altair và pandas dùng để vẽ bản đồ và bảng)
- Lưu trữ: file JSON trong thư mục `data/` (không dùng database)
- Kiểm thử: `unittest` + `streamlit.testing.v1.AppTest`

## Ràng buộc kỹ thuật

1. **Cấm** `collections.deque`, `heapq`, `bisect`, `queue`, `networkx` và mọi thư viện CTDL/đồ thị ngoài. Chỉ dùng `list`, `dict`, `set`, `tuple`.
2. Mọi tìm kiếm đạt **O(log n)**: sorted index `(search_key, id)` + Binary Search tự viết, sau đó tra `dict` chính trong O(1). (Chèn/xóa khỏi chỉ mục là O(log n) tìm vị trí + O(n) dịch phần tử do `list.insert` / `list.pop`.)
3. Lưu trữ bằng JSON, xử lý an toàn khi file chưa tồn tại, rỗng hoặc sai cú pháp. `map_graph.json` và `users.json` có sẵn; CRUD đầy đủ cho `menu.json`; `orders.json` do `OrderManager` ghi.
4. OOP: đóng gói bằng `_attr` và `@property` có kiểm tra hợp lệ, các entity kế thừa `BaseEntity`.
5. Kiến trúc 3 tầng tách biệt. Không viết logic thuật toán hay đọc/ghi file trong `app.py`.
6. Type hints đầy đủ, tuân thủ PEP8, comment ngắn về độ phức tạp ở các hàm quan trọng.
7. **Giai đoạn tích hợp:** 7 file lõi không được sửa — `routing_algo.py`, `priority_engine.py`, `graph_node.py`, `base.py`, `storage.py`, `structures.py`, `menu_manager.py`; không sửa `pyproject.toml` và `uv.lock` (chi tiết trong `PROJECT.md`).

## Cấu trúc thư mục

Tag ở cuối mỗi dòng cho biết thành viên phụ trách (xem bảng bên dưới).

```
order-shipper-system/
├── README.md
├── PROJECT.md                   # kiến trúc, feature inventory, interface contracts
├── TEST_INFRA.md                # chiến lược và kịch bản kiểm thử
├── pyproject.toml, uv.lock, .python-version
├── .github/
│   ├── CODEOWNERS               # ánh xạ file → người review
│   └── pull_request_template.md
├── data/
│   ├── map_graph.json           # bản đồ: 8 đỉnh, 12 cạnh hai chiều (có sẵn)
│   ├── users.json               # 4 khách hàng U001–U004 (có sẵn)
│   ├── menu.json                # tự tạo khi chạy lần đầu (6 món mẫu)    [M3]
│   └── orders.json              # tự tạo khi có đơn đầu tiên             [M5]
├── src/
│   ├── app.py                   # giao diện Streamlit, mỗi tab một người
│   ├── models/
│   │   ├── base.py              # BaseEntity                             [CHUNG]
│   │   ├── graph_node.py        # GraphNode, Graph (danh sách kề)        [M1]
│   │   ├── menu_item.py         # MenuItem                               [M3]
│   │   ├── customer.py          # Customer                               [M5]
│   │   └── order.py             # Order, OrderStatus, ALLOWED_TRANSITIONS [M5]
│   └── core/
│       ├── structures.py        # CTDL tự viết, nhiều người dùng         [M4 chủ file]
│       ├── routing_algo.py      # Dijkstra / A*                          [M1]
│       ├── routing_service.py   # nạp bản đồ, lộ trình đơn/chuyến, dữ liệu vẽ [M2]
│       ├── storage.py           # đọc/ghi JSON, sao lưu .bak             [M3]
│       ├── menu_manager.py      # CRUD + tìm món                         [M3]
│       ├── priority_engine.py   # trọng số ưu tiên, Aging                [M4]
│       ├── customer_manager.py  # khách hàng chỉ đọc + tìm kiếm          [M5]
│       └── order_manager.py     # state machine, giao chuyến, Undo/Redo  [M5]
└── tests/
    ├── test_routing_service.py  # 15 test                                [M2]
    ├── test_customer_manager.py #  7 test                                [M5]
    ├── test_order.py            #  7 test
    ├── test_order_manager.py    # 14 test
    ├── test_priority_engine.py  #  6 test
    └── test_app_smoke.py        #  2 test (Streamlit AppTest)
```

## Thành viên và phân công

| Module | Thành viên | Phụ trách |
|:------:|------------|-----------|
| M1 | Lê Trí Tiên | `models/graph_node.py`, `core/routing_algo.py` — bản đồ (danh sách kề) và thuật toán Dijkstra / A* |
| M2 | Đào Đoàn Đỗ Quyên | `core/routing_service.py`, tab Bản đồ trong `app.py` — nạp bản đồ, gom chuyến Nearest-Neighbor, dữ liệu hiển thị lộ trình |
| M3 | Nguyễn Lê Đức Bảo | `models/menu_item.py`, `core/storage.py`, `core/menu_manager.py`, tab Menu — CRUD Menu, JSON an toàn, tìm kiếm; viết `SortedIndex` |
| M4 | Nguyễn Vũ Băng Tâm | `core/structures.py`, `core/priority_engine.py`, tab Hàng đợi chế biến — Min-Heap, Priority Queue, trọng số ưu tiên + Aging |
| M5 | Thân Văn Thế Lâm | `models/order.py`, `models/customer.py`, `core/order_manager.py`, `core/customer_manager.py`, tab Đơn hàng — vòng đời đơn, Undo/Redo, tìm đơn; viết `CustomStack` |

File dùng chung:

- `models/base.py`: mọi entity kế thừa; do Bảo viết.
- `core/structures.py`: Tâm là chủ file (`CustomMinHeap`, `CustomPriorityQueue`); `SortedIndex` do Bảo viết, `CustomStack` do Lâm viết. Mỗi người chỉ sửa class của mình.
- `app.py`: mỗi người viết hàm `render_*_tab()` của mình (`render_map_tab`, `render_menu_tab`, `render_kitchen_tab`, `render_order_tab`).

## Cài đặt và chạy

```bash
uv sync
uv run python -m streamlit run src/app.py
```

Chạy từ thư mục gốc dự án, dùng `python -m streamlit` để import `src.models...` và `src.core...` hoạt động đúng.

### Chạy kiểm thử

```bash
uv run python -m unittest discover -s tests -t .
```

Hiện có **51 test, tất cả đều pass**. Test dùng thư mục tạm và dữ liệu giả lập nên không làm thay đổi `data/` thật.

| File | Số test | Nội dung chính |
|------|:------:|----------------|
| `test_routing_service.py` | 15 | 6 trường hợp lỗi `load_map_graph`, `is_valid_delivery_node`, đường đơn, gom chuyến + tie-break, so sánh Dijkstra/A*, dữ liệu vẽ bản đồ |
| `test_order_manager.py` | 14 | tạo đơn, BUSY/IDLE, `start_delivery` nguyên tử, chặn hủy khi đang giao, guard ưu tiên, Undo/Redo, tìm theo Tên/Email, nạp dữ liệu hỏng, copy-on-read |
| `test_customer_manager.py` | 7 | nạp dữ liệu chuẩn, tìm theo Tên/Email (không phân biệt hoa thường), bản ghi hỏng vào `load_errors`, file thiếu / sai kiểu không crash, validation `Customer` |
| `test_order.py` | 7 | `status` chỉ đọc, bảng chuyển trạng thái, `restore_status`, tổng thời gian chế biến, serialize hai chiều, tương thích JSON cũ, validation tên/email |
| `test_priority_engine.py` | 6 | công thức điểm, VIP vs thường, chống bỏ đói (Aging), thời gian chế biến khác nhau, hòa điểm |
| `test_app_smoke.py` | 2 | app chạy đủ 4 tab không ngoại lệ; tab Bản đồ hiện danh sách chọn đơn khi có đơn `READY` (Streamlit `AppTest`) |

## Cách dùng app theo đúng nghiệp vụ

Quy trình chuẩn mô phỏng luồng vận hành thực tế (1 Quán – 1 Shipper) qua 7 bước:

1. **Bước 1: Tạo đơn hàng tại tab "Đơn hàng"**
   - Chọn lần lượt các khách hàng mẫu `U001`, `U002`, `U003` từ danh sách.
   - Thông tin khách hàng (tên, email, hạng VIP) và điểm giao hiển thị tự động dạng chỉ đọc.
   - Chọn món ăn từ Menu, điều chỉnh số lượng mong muốn và bấm **Tạo đơn hàng**.
2. **Bước 2: Xác nhận đơn hàng**
   - Chuyển trạng thái các đơn vừa tạo từ `PLACED` sang `CONFIRMED`.
3. **Bước 3: Chế biến tại tab "Hàng đợi chế biến"**
   - Các đơn được sắp xếp tự động theo đúng thứ tự ưu tiên của `PriorityEngine`.
   - Lần lượt chuyển đơn từ `CONFIRMED` sang `PREPARING`, sau đó hoàn tất sang `READY`. Chuyển sai thứ tự ưu tiên sẽ bị từ chối kèm tên đơn cần làm trước.
4. **Bước 4: Xem quãng đường đơn lẻ tại tab "Bản đồ / Lộ trình"**
   - Tab hiển thị danh sách các đơn hàng đang ở trạng thái `READY`.
   - Xem quãng đường và chi phí di chuyển đơn lẻ từ Quán đến từng điểm giao.
5. **Bước 5: Gom chuyến giao hàng đa điểm**
   - Chọn các đơn `READY` cần giao trong cùng một chuyến gom.
   - Hệ thống lập lộ trình bằng Nearest-Neighbor: thứ tự thăm `CUSTOMER_3` → `CUSTOMER` → `CUSTOMER_2`, tổng quãng đường **16.0 km** (đường đi `RESTAURANT → B → CUSTOMER_3 → D → CUSTOMER → CUSTOMER_2`).
   - Bảng so sánh Dijkstra vs A*: cùng chi phí 16.0 km, nhưng Dijkstra duyệt **15** đỉnh còn A* chỉ duyệt **8** đỉnh.
6. **Bước 6: Bắt đầu giao hàng**
   - Bấm **Bắt đầu giao**: toàn bộ đơn được chọn chuyển nguyên tử sang `DELIVERING` (một snapshot duy nhất, nên Undo một lần là hoàn tác cả chuyến).
   - Trạng thái Shipper chuyển sang `BUSY`.
   - Trong khi Shipper `BUSY`, hệ thống từ chối tiếp nhận thêm đơn mới để tránh quá tải.
7. **Bước 7: Hoàn tất giao hàng và thanh toán**
   - Bấm **Đã giao** cho từng đơn trong chuyến giao khi giao thành công sang `PAID`.
   - Khi đơn cuối cùng trong chuyến hoàn tất, Shipper tự động quay về trạng thái `IDLE`.

Ngoài luồng trên, tab **Menu** cho phép thêm / sửa / xóa / tìm món (Binary Search, khớp chính xác tên, không phân biệt hoa thường), và tab **Đơn hàng** có nút **Undo / Redo** cùng ô tìm đơn theo Tên hoặc Email.

### Cơ chế sao lưu an toàn khi lỗi dữ liệu (.bak)

- Khi file JSON lưu trữ (như `map_graph.json`, `orders.json`) bị sai cú pháp, tầng storage tự động đổi tên file lỗi thành `<file>.bak` và trả về cấu trúc mặc định rỗng.
- `load_map_graph` phân biệt **6 trường hợp lỗi** bản đồ và báo bằng `MapDataError` (tiếng Việt): file không tồn tại, file rỗng, sai cú pháp (đã chuyển thành `.bak`), thiếu `nodes`, thiếu đỉnh `RESTAURANT`, và lỗi cấu trúc đồ thị.
- Với `orders.json` và `users.json`, từng bản ghi hỏng được bỏ qua và ghi vào `load_errors`; các bản ghi hợp lệ vẫn được nạp.
- Người dùng có thể kiểm tra, sửa lỗi cú pháp trong file `.bak` và đổi tên lại để khôi phục dữ liệu bình thường.

## Độ phức tạp các thành phần chính

| Thành phần | Thao tác | Độ phức tạp |
|------------|----------|-------------|
| `CustomMinHeap` | push / pop | O(log n) |
| | peek / is_empty | O(1) |
| `CustomPriorityQueue` | enqueue / dequeue | O(log n) |
| `PriorityEngine.rank` | xếp hạng n đơn | O(n log n) |
| `SortedIndex` | tìm (`find_all`) | O(log n + k) |
| | chèn / xóa | O(log n) tìm vị trí + O(n) dịch phần tử |
| `CustomStack` (Undo/Redo) | push / pop / peek | O(1) |
| `Graph` | bộ nhớ (danh sách kề) | O(V + E) |
| Dijkstra / A* | một lần tìm đường | O((V + E) log V) |
| `plan_batch_route` | k điểm giao | O(k² (V + E) log V) |
| `OrderManager` | snapshot / Undo / Redo | O(n) |

## Dữ liệu

- `data/map_graph.json`: 8 đỉnh (`RESTAURANT`, `A`, `B`, `C`, `D`, `CUSTOMER`, `CUSTOMER_2`, `CUSTOMER_3`) và 12 cạnh hai chiều có tọa độ, trọng số (km). A* dùng hệ số co `k ≤ 1` tính từ bản đồ để heuristic luôn hợp lệ.
- `data/users.json`: 4 khách hàng mẫu `U001`–`U004` (có cờ VIP và đỉnh giao hàng).
- `data/menu.json`: được tạo tự động ở lần chạy đầu tiên với 6 món mẫu nếu chưa có.
- `data/orders.json`: được tạo tự động khi có đơn hàng đầu tiên; không commit file chạy thật.

## Hạn chế và hướng phát triển

- Nearest-Neighbor là giải thuật tham lam, **không đảm bảo tối ưu toàn cục** cho bài toán nhiều điểm giao (dạng TSP); có thể thử 2-opt hoặc quy hoạch động khi số điểm nhỏ.
- Mô hình chỉ có 1 Shipper; mở rộng nhiều Shipper cần thêm bước phân bổ đơn.
- Undo/Redo lưu snapshot **trạng thái** đơn hàng, chưa bao gồm việc tạo đơn mới.
- `SortedIndex` chèn/xóa O(n) do dùng `list`; có thể thay bằng cây cân bằng nếu dữ liệu lớn.
- Chưa có test riêng cho `menu_manager`, `storage`, `structures`, `graph_node`; hiện các module này được kiểm tra gián tiếp qua test của module khác.

## Quy ước làm việc nhóm

- Mỗi tính năng một nhánh git, đặt tên theo loại thay đổi: `feat/...`, `fix/...`, `test/...`, `docs/...`, `chore/...` (ví dụ `feat/m1-routing`, `feat/m4-priority`, `feat/connect-routing-order`).
- Commit message theo tiền tố chuẩn: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- Chỉ sửa file của mình; cần sửa file người khác thì báo chủ file. Quyền review được khai báo trong `.github/CODEOWNERS`.
- Merge vào `main` qua Pull Request, có ít nhất một thành viên khác review, và điền đủ `pull_request_template.md` (mô tả, cách kiểm tra, checklist).
- Không commit `.venv`, `__pycache__`, hay file JSON dữ liệu chạy thật.
- Đầu mỗi file có dòng `[M#] Owner: ...` ghi rõ người phụ trách.
