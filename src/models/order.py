"""
[M5] Owner: Thân Văn Thế Lâm
File: src/models/order.py

Nhiệm vụ:
- Order(BaseEntity): đơn hàng (id, khách hàng, danh sách món, trạng thái, VIP, điểm giao...).
- Đóng gói đầy đủ các thuộc tính với private _attr và @property kiểm tra tính hợp lệ.
- Trạng thái: PLACED -> CONFIRMED -> PREPARING -> READY -> DELIVERING -> PAID | CANCELLED.
- Bảng chuyển trạng thái hợp lệ ALLOWED_TRANSITIONS (State Machine).
"""

from __future__ import annotations

import time
from typing import Any

from src.models.base import BaseEntity


class OrderStatus:
    """Các trạng thái khả dĩ trong vòng đời đơn hàng."""
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERING = "DELIVERING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


# Bảng quy định các trạng thái tiếp theo hợp lệ (State Machine duy nhất)
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PLACED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.DELIVERING, OrderStatus.CANCELLED},
    OrderStatus.DELIVERING: {OrderStatus.PAID},  # Đang giao không được hủy giữa chừng
    OrderStatus.PAID: set(),                     # Trạng thái kết thúc
    OrderStatus.CANCELLED: set(),                # Trạng thái kết thúc
}


def make_item_snapshot(
    item_id: str,
    name: str,
    quantity: int = 1,
    price: float | int = 0.0,
    prep_minutes: float | int = 0.0,
) -> dict[str, Any]:
    """Tạo bản chụp (snapshot) thông tin món ăn cho đơn hàng.

    # Độ phức tạp: O(1).
    """
    return {
        "item_id": str(item_id).strip(),
        "name": str(name).strip(),
        "quantity": max(1, int(quantity)),
        "price": float(price),
        "prep_minutes": float(prep_minutes),
    }


class Order(BaseEntity):
    """Thực thể Đơn hàng trong hệ thống, kế thừa từ BaseEntity."""

    def __init__(
        self,
        order_id: str,
        customer_name: str,
        customer_email: str,
        items: list[dict[str, Any]] | list[str],
        created_at: float | None = None,
        is_vip: bool = False,
        delivery_node_id: str | None = None,
        create_at: float | None = None,
    ) -> None:
        """Khởi tạo đơn hàng với các thuộc tính được đóng gói an toàn."""
        super().__init__(id=order_id)
        self.customer_name = customer_name
        self.customer_email = customer_email

        # Hỗ trợ cả created_at và create_at cũ
        if created_at is None:
            created_at = create_at if create_at is not None else time.time()
        self._created_at: float = float(created_at)

        self._is_vip: bool = bool(is_vip)
        self._delivery_node_id: str | None = (
            str(delivery_node_id).strip() if delivery_node_id is not None else None
        )
        self._status: str = OrderStatus.PLACED
        self.items = items

    @property
    def customer_name(self) -> str:
        """Tên khách hàng."""
        return self._customer_name

    @customer_name.setter
    def customer_name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Tên khách hàng phải là chuỗi không rỗng.")
        self._customer_name = value.strip()

    @property
    def customer_email(self) -> str:
        """Email khách hàng."""
        return self._customer_email

    @customer_email.setter
    def customer_email(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Email khách hàng phải là chuỗi không rỗng.")
        self._customer_email = value.strip()

    @property
    def items(self) -> list[dict[str, Any]]:
        """Danh sách snapshot các món ăn trong đơn hàng."""
        return self._items

    @items.setter
    def items(self, new_items: list[Any]) -> None:
        normalized: list[dict[str, Any]] = []
        for it in new_items:
            if isinstance(it, str):
                normalized.append(make_item_snapshot(it, it, 1, 0.0, 0.0))
            elif isinstance(it, dict):
                normalized.append(
                    make_item_snapshot(
                        item_id=str(it.get("item_id", "")),
                        name=str(it.get("name", "")),
                        quantity=int(it.get("quantity", 1)),
                        price=float(it.get("price", 0.0)),
                        prep_minutes=float(it.get("prep_minutes", 0.0)),
                    )
                )
            else:
                raise ValueError(f"Món ăn không hợp lệ: {it}")
        self._items = normalized

    @property
    def created_at(self) -> float:
        """Thời điểm tạo đơn (epoch giây)."""
        return self._created_at

    @property
    def create_at(self) -> float:
        """Bí danh tương thích ngược cho created_at."""
        return self._created_at

    @property
    def is_vip(self) -> bool:
        """Đơn hàng thuộc khách hàng VIP hay không."""
        return self._is_vip

    @is_vip.setter
    def is_vip(self, value: bool) -> None:
        self._is_vip = bool(value)

    @property
    def delivery_node_id(self) -> str | None:
        """Mã điểm giao hàng (node trên đồ thị)."""
        return self._delivery_node_id

    @delivery_node_id.setter
    def delivery_node_id(self, value: str | None) -> None:
        self._delivery_node_id = str(value).strip() if value is not None else None

    @property
    def status(self) -> str:
        """Trạng thái hiện tại của đơn hàng (chỉ đọc)."""
        return self._status

    @property
    def total_prep_minutes(self) -> float:
        """Tổng thời gian chế biến của các món trong đơn hàng (phút).

        # Độ phức tạp: O(m) với m là số món ăn trong đơn hàng.
        """
        return sum(
            float(item.get("prep_minutes", 0.0)) * int(item.get("quantity", 1))
            for item in self._items
        )

    def change_status(self, new_status: str) -> bool:
        """Kiểm tra tính hợp lệ qua ALLOWED_TRANSITIONS trước khi chuyển trạng thái.

        # Độ phức tạp: O(1) tra cứu trên set.
        """
        if new_status in ALLOWED_TRANSITIONS.get(self._status, set()):
            self._status = new_status
            return True
        return False

    def restore_status(self, status: str) -> bool:
        """Khôi phục trạng thái cho Undo/Redo và from_dict (không tra bảng chuyển).

        # Độ phức tạp: O(1).
        """
        valid_statuses = {
            OrderStatus.PLACED,
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.DELIVERING,
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
        }
        if status not in valid_statuses:
            raise ValueError(f"Trạng thái '{status}' không hợp lệ trong OrderStatus.")
        self._status = status
        return True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển đổi thực thể thành dictionary để lưu trữ JSON."""
        data = super().to_dict()
        data.update({
            "customer_name": self._customer_name,
            "customer_email": self._customer_email,
            "items": [dict(it) for it in self._items],
            "created_at": self._created_at,
            "status": self._status,
            "is_vip": self._is_vip,
            "delivery_node_id": self._delivery_node_id,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Order:
        """Khôi phục đối tượng Order từ dictionary đọc từ JSON.

        Hỗ trợ định dạng cũ: key 'create_at' thay cho 'created_at',
        và items là list[str] (chuyển thành snapshot với quantity=1, price=0, prep_minutes=0).
        """
        if not isinstance(data, dict):
            raise ValueError("Dữ liệu đầu vào phải là dictionary.")
        if "id" not in data:
            raise ValueError("Dữ liệu thiếu trường 'id'.")

        order_id = str(data["id"])
        customer_name = str(data.get("customer_name", ""))
        customer_email = str(data.get("customer_email", ""))

        created_at_val = data.get("created_at")
        if created_at_val is None:
            created_at_val = data.get("create_at", time.time())
        created_at = float(created_at_val)

        raw_items = data.get("items", [])
        is_vip = bool(data.get("is_vip", False))
        delivery_node_id = data.get("delivery_node_id")

        order = cls(
            order_id=order_id,
            customer_name=customer_name,
            customer_email=customer_email,
            items=raw_items,
            created_at=created_at,
            is_vip=is_vip,
            delivery_node_id=delivery_node_id,
        )

        status = data.get("status", OrderStatus.PLACED)
        order.restore_status(status)
        return order

    def __repr__(self) -> str:
        return (
            f"Order(id='{self._id}', customer='{self._customer_name}', "
            f"status='{self._status}', vip={self._is_vip}, items={len(self._items)})"
        )
