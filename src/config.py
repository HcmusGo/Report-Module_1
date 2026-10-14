"""Hằng số dùng chung. Người phụ trách: Tiên."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"          # file chạy thật (nằm trong .gitignore)
SAMPLE_DIR = DATA_DIR / "sample"      # dữ liệu khởi tạo sẵn (có commit)

# Tốc độ trung bình (km/h) theo mức đông đúc của đường.
# Đường gần nhưng đông (HIGH) có thể chậm hơn đường xa nhưng vắng (LOW),
# nên Dijkstra phải tính theo THỜI GIAN chứ không chỉ theo km.
TRAFFIC_SPEED_KMH = {"LOW": 40.0, "MEDIUM": 25.0, "HIGH": 10.0}
