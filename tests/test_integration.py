from __future__ import annotations
from pathlib import Path
import pytest

from repositories.json_repository import JsonRepository

class OrderEntity:
    def __init__(self, id: str, customer: str, status: str = "PENDING", route: str | None = None):
        self.id = id
        self.customer = customer
        self.status = status
        self.route = route

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer": self.customer,
            "status": self.status,
            "route": self.route
        }

    @classmethod
    def from_dict(cls, data: dict) -> OrderEntity:
        return cls(
            id=data.get("id"),
            customer=data.get("customer"),
            status=data.get("status", "PENDING"),
            route=data.get("route")
        )

def test_integration_order_workflow(tmp_path: Path):
    # Khởi tạo repository dùng thư mục tạm (tmp_path) để test an toàn
    repo = JsonRepository(OrderEntity, "orders.json", "HD", data_dir=tmp_path, sample_dir=tmp_path)

    # 1. Thêm đơn hàng mới
    new_id = repo.next_id()
    assert new_id == "HD1"
    order = OrderEntity(id=new_id, customer="Nguyễn Vũ Băng Tâm", status="PENDING")
    repo.add(order)
    
    fetched = repo.get_by_id("HD1")
    assert fetched is not None
    assert fetched.status == "PENDING"

    # 2. Đề xuất & Gán tuyến đường (Route assignment)
    fetched.route = "Route_DaNang_01"
    fetched.status = "ASSIGNED"
    repo.update(fetched)

    updated_order = repo.get_by_id("HD1")
    assert updated_order.status == "ASSIGNED"
    assert updated_order.route == "Route_DaNang_01"

    # 3. Hoàn thành điểm dừng (Complete stop)
    updated_order.status = "COMPLETED"
    repo.update(updated_order)
    assert repo.get_by_id("HD1").status == "COMPLETED"

    # 4. Kiểm tra tính năng Undo / Trả lại trạng thái trước (Giả lập quay về ASSIGNED)
    updated_order.status = "ASSIGNED"
    repo.update(updated_order)
    assert repo.get_by_id("HD1").status == "ASSIGNED"