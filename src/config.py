"""Hằng số dùng chung. Người phụ trách: Tiên.

Mọi con số nghiệp vụ nằm ở đây, không rải trong code.
Công thức là đề xuất, nhóm chốt rồi sửa tại đây.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"          # dữ liệu khởi tạo sẵn (có commit), app đọc / ghi trực tiếp

BASE_FEE = 15_000        # VNĐ, phí ship cơ bản
FEE_PER_KM = 5_000       # VNĐ / km
AVG_SPEED_KMH = 25.0     # tốc độ trung bình, đổi km -> phút (đề xuất)
