"""Hằng số dùng chung. Người phụ trách: Tiên.

Mọi con số nghiệp vụ nằm ở đây, không rải trong code.
Công thức là đề xuất, nhóm chốt rồi sửa tại đây.
"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"          # file chạy thật (nằm trong .gitignore)
SAMPLE_DIR = DATA_DIR / "sample"      # dữ liệu mẫu (có commit)

BASE_FEE = 15_000        # VNĐ, phí ship cơ bản
FEE_PER_KM = 5_000       # VNĐ / km
AVG_SPEED_KMH = 25.0     # tốc độ trung bình, đổi km -> phút (đề xuất)
