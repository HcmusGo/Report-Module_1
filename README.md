# Hệ thống Quản lý Đơn hàng, Ưu tiên Chế biến & Tìm đường Shipper

Đồ án Module 1 — mô hình **1 Quán – 1 Shipper**. Hệ thống quản lý menu, nhận và xử lý đơn hàng theo độ ưu tiên, theo dõi vòng đời đơn và tìm đường ngắn nhất để Shipper giao hàng, hiển thị trực quan trên giao diện web.

Điểm đặc biệt của đồ án: toàn bộ cấu trúc dữ liệu và thuật toán (Stack, Min-Heap / Priority Queue, Graph, Binary Search) đều **tự cài đặt bằng OOP**, không dùng thư viện có sẵn.

## Tính năng chính

- **Tìm đường cho Shipper:** bản đồ biểu diễn bằng danh sách kề, tìm đường ngắn nhất bằng Dijkstra và A* (so sánh hai thuật toán).
- **Hiển thị bản đồ:** vẽ lộ trình của Shipper lên giao diện Streamlit từ tọa độ (x, y) của các đỉnh.
- **Quản lý Menu:** thêm, sửa, xóa, xem và tìm kiếm món ăn.
- **Ưu tiên chế biến:** sắp xếp đơn/món theo khách VIP, thời gian chờ và thời gian chế biến bằng Priority Queue tự viết.
- **Vòng đời đơn hàng:** state machine chặt chẽ, hỗ trợ Undo / Redo chuyển trạng thái, tìm đơn theo Tên hoặc Email.

### Vòng đời đơn hàng

```
PLACED → CONFIRMED → PREPARING → READY → DELIVERING → PAID
   └────────┴───────────┴──────────┘
                  ↓
              CANCELLED   (không được hủy khi đang DELIVERING hoặc đã PAID)
```

## Công nghệ

- Python, quản lý package bằng [`uv`](https://docs.astral.sh/uv/)
- Giao diện: [Streamlit](https://streamlit.io/)
- Lưu trữ: file JSON trong thư mục `data/` (không dùng database)

## Ràng buộc kỹ thuật

1. **Cấm** `collections.deque`, `heapq`, `bisect`, `queue`, `networkx` và mọi thư viện CTDL/đồ thị ngoài. Chỉ dùng `list`, `dict`, `set`, `tuple`.
2. Mọi tìm kiếm đạt **O(log n)**: sorted index `(search_key, id)` + Binary Search tự viết, sau đó tra `dict` chính trong O(1).
3. Lưu trữ bằng JSON, xử lý an toàn khi file chưa tồn tại hoặc rỗng. `map_graph.json` và `users.json` có sẵn; chỉ viết CRUD đầy đủ cho `menu.json`.
4. OOP: đóng gói bằng `_attr` và `@property`, các entity kế thừa `BaseEntity`.
5. Kiến trúc 3 tầng tách biệt: `src/models/` (entities), `src/core/` (CTDL, thuật toán, đọc/ghi JSON), `src/app.py` (giao diện). Không viết logic thuật toán hay đọc/ghi file trong `app.py`.
6. Type hints đầy đủ, tuân thủ PEP8, comment ngắn về độ phức tạp ở các hàm quan trọng.

## Cấu trúc thư mục

Tag ở cuối mỗi dòng cho biết thành viên phụ trách (xem bảng bên dưới).

```
order-shipper-system/
├── README.md
├── pyproject.toml
├── data/
│   ├── map_graph.json          # bản đồ (có sẵn)
│   ├── users.json              # khách hàng (có sẵn)
│   ├── menu.json               # tự tạo khi chạy lần đầu          [M3]
│   └── orders.json             # tự tạo khi chạy lần đầu          [M5]
└── src/
    ├── app.py                  # giao diện Streamlit, mỗi tab một người
    ├── models/
    │   ├── base.py             # BaseEntity                       [CHUNG]
    │   ├── graph_node.py       #                                  [M1]
    │   ├── menu_item.py        #                                  [M3]
    │   └── order.py            #                                  [M5]
    └── core/
        ├── structures.py       # CTDL tự viết, nhiều người dùng   [M4 chủ file]
        ├── routing_algo.py     # Dijkstra / A*                    [M1]
        ├── routing_service.py  # lộ trình → tọa độ để vẽ          [M2]
        ├── storage.py          # đọc/ghi JSON                     [M3]
        ├── menu_manager.py     # CRUD + tìm món                   [M3]
        ├── priority_engine.py  # trọng số ưu tiên                 [M4]
        └── order_manager.py    # state machine + Undo/Redo        [M5]
```

## Thành viên và phân công

| Module | Thành viên | Phụ trách |
|:------:|------------|-----------|
| M1 | Lê Trí Tiên | `models/graph_node.py`, `core/routing_algo.py` — bản đồ và thuật toán tìm đường |
| M2 | Đào Đoàn Đỗ Quyên | `core/routing_service.py`, tab Bản đồ trong `app.py` — hiển thị lộ trình |
| M3 | Nguyễn Lê Đức Bảo | `models/menu_item.py`, `core/storage.py`, `core/menu_manager.py` — CRUD Menu, JSON, tìm kiếm |
| M4 | Nguyễn Vũ Băng Tâm | `core/structures.py`, `core/priority_engine.py` — Min-Heap, Priority Queue, trọng số ưu tiên |
| M5 | Thân Văn Thế Lâm | `models/order.py`, `core/order_manager.py` — vòng đời đơn, Undo/Redo, tìm đơn |

File dùng chung:

- `models/base.py`: cần chốt đầu tiên vì mọi entity kế thừa (đề xuất Bảo viết trước).
- `core/structures.py`: Tâm là chủ file; `SortedIndex` do Bảo viết, `CustomStack` do Lâm viết. Mỗi người chỉ sửa class của mình.
- `app.py`: mỗi người viết hàm `render_*_tab()` của mình, có comment đánh dấu.

## Cài đặt và chạy

```bash
uv sync
uv run python -m streamlit run src/app.py
```

Chạy từ thư mục gốc dự án, dùng `python -m streamlit` để import `src.models...` và `src.core...` hoạt động đúng.

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
   - Lần lượt chuyển đơn từ `CONFIRMED` sang `PREPARING`, sau đó hoàn tất sang `READY`.
4. **Bước 4: Xem quãng đường đơn lẻ tại tab "Bản đồ / Lộ trình"**
   - Tab hiển thị danh sách các đơn hàng đang ở trạng thái `READY`.
   - Xem quãng đường và chi phí di chuyển đơn lẻ từ Quán đến từng điểm giao.
5. **Bước 5: Gom chuyến giao hàng đa điểm**
   - Chọn các đơn `READY` cần giao trong cùng một chuyến gom.
   - Hệ thống lập lộ trình tối ưu bằng Nearest-Neighbor: thứ tự thăm
     `CUSTOMER_3` -> `CUSTOMER` -> `CUSTOMER_2`, tổng quãng đường 16.0 km.
   - Xem bảng so sánh thuật toán Dijkstra vs A* (chi phí quãng đường và số đỉnh duyệt).
6. **Bước 6: Bắt đầu giao hàng**
   - Bấm **Bắt đầu giao**: toàn bộ đơn được chọn chuyển nguyên tử sang `DELIVERING`.
   - Trạng thái Shipper chuyển sang `BUSY`.
   - Trong khi Shipper `BUSY`, hệ thống từ chối tiếp nhận thêm đơn mới để tránh quá tải.
7. **Bước 7: Hoàn tất giao hàng và thanh toán**
   - Bấm **Đã giao** cho từng đơn trong chuyến giao khi giao thành công sang `PAID`.
   - Khi đơn cuối cùng trong chuyến hoàn tất, Shipper tự động quay về trạng thái `IDLE`.

### Cơ chế sao lưu an toàn khi lỗi dữ liệu (.bak)

- Khi file JSON lưu trữ (như `map_graph.json`, `orders.json`) bị sai cú pháp, tầng storage
  tự động đổi tên file lỗi thành `<file>.bak` và trả về cấu trúc mặc định rỗng.
- Cơ chế này giúp ứng dụng không bị crash đột ngột; người dùng có thể kiểm tra, sửa lỗi
  cú pháp trong file `.bak` và đổi tên lại để khôi phục dữ liệu bình thường.

## Dữ liệu

- `data/map_graph.json` và `data/users.json` trong bộ khung chỉ là **dữ liệu mẫu nhỏ** để chạy thử; thay bằng dữ liệu thật của nhóm.
- `data/menu.json` và `data/orders.json` được tạo tự động ở lần chạy đầu tiên nếu chưa có.

## Quy ước làm việc nhóm

- Mỗi người một nhánh git: `feature/m1-tien`, `feature/m2-quyen`, `feature/m3-bao`, `feature/m4-tam`, `feature/m5-lam`.
- Chỉ sửa file của mình; cần sửa file người khác thì báo chủ file.
- Merge vào `main` qua Pull Request, có ít nhất một thành viên khác review.
- Đầu mỗi file có dòng `[M#] Owner: ...` ghi rõ người phụ trách.
