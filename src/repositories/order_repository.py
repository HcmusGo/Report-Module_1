from __future__ import annotations

from models.order import Order, OrderStatus
from repositories.json_repository import JsonRepository


class OrderRepository(JsonRepository[Order]):
    filename = "orders.json"
    id_prefix = "O"

    @classmethod
    def _entity_from_dict(cls, data: dict) -> Order:
        return Order.from_dict(data)

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [order for order in self.get_all() if order.status == status]

    def find_by_customer(self, customer_id: str) -> list[Order]:
        return [order for order in self.get_all() if order.customer_id == customer_id]
	
