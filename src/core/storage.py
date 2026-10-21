"""
[M3] Owner: Nguyễn Lê Đức Bảo
File: src/core/storage.py

Nhiệm vụ:
- Hàm đọc/ghi JSON trong thư mục data/.
- Xử lý an toàn khi file chưa tồn tại hoặc rỗng (lần chạy đầu tiên).
- Dùng chung cho menu_manager, order_manager và nạp map_graph.json, users.json.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

# Đường dẫn gốc của dự án và thư mục data mặc định
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"


def _resolve_path(path: str | Path) -> Path:
    """Xác định đường dẫn file JSON thực tế.

    Hỗ trợ cả trường hợp bên gọi truyền 'data/menu.json' lẫn chỉ truyền tên file
    'menu.json' (nếu không có thư mục cha thì tự động trỏ vào data/ của dự án).
    """
    p = Path(path)
    if not p.is_absolute():
        # Nếu đường dẫn không có thư mục cha (chỉ là tên file, ví dụ 'menu.json')
        if len(p.parts) <= 1 or str(p.parent) in ("", "."):
            return DEFAULT_DATA_DIR / p.name
        # Nếu đường dẫn tương đối bắt đầu bằng thư mục 'data'
        if p.parts[0] == "data":
            return PROJECT_ROOT / p
    return p


def load_json(path: str | Path, default: Any = None) -> Any:
    """Đọc dữ liệu từ file JSON an toàn.

    Độ phức tạp: O(n) theo kích thước nội dung JSON trong file.

    Args:
        path: Đường dẫn tới file JSON hoặc tên file (tự động trỏ vào data/).
        default: Giá trị mặc định nếu file không tồn tại, rỗng hoặc hỏng (mặc định là []).

    Returns:
        Dữ liệu đọc được từ file JSON hoặc bản sao của default.
    """
    # Nếu default is None, mặc định trả về []
    if default is None:
        default = []

    file_path = _resolve_path(path)
    # Tự động tạo thư mục cha (data/) nếu chưa tồn tại
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Nếu file chưa tồn tại, trả về bản sao của default
    if not file_path.exists() or not file_path.is_file():
        return copy.deepcopy(default)

    # Nếu file rỗng (kích thước = 0)
    if file_path.stat().st_size == 0:
        return copy.deepcopy(default)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Nếu nội dung rỗng sau khi loại bỏ khoảng trắng
        if not content.strip():
            return copy.deepcopy(default)

        # Parse JSON với độ phức tạp O(n)
        return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # File bị lỗi cú pháp JSON hoặc mã hóa: đổi tên thành <tên_file>.bak
        # Dùng os.replace để không bị lỗi trên Windows nếu file .bak đã có sẵn
        bak_path = file_path.with_name(f"{file_path.name}.bak")
        try:
            os.replace(file_path, bak_path)
        except OSError:
            pass
        return copy.deepcopy(default)


def save_json(path: str | Path, data: Any) -> None:
    """Ghi dữ liệu xuống file JSON với định dạng UTF-8 và thụt lề 2 khoảng trắng.

    Độ phức tạp: O(n) theo kích thước dữ liệu JSON cần ghi.

    Args:
        path: Đường dẫn tới file JSON hoặc tên file (tự động trỏ vào data/).
        data: Dữ liệu cần ghi xuống file.
    """
    file_path = _resolve_path(path)
    # Tự động tạo thư mục cha (data/) nếu chưa tồn tại
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Ghi dữ liệu O(n) với encoding="utf-8", ensure_ascii=False, indent=2
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
