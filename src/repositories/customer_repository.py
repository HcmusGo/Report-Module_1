"""Lưu khách hàng vào data/customers.json. Người phụ trách: Tâm."""
from __future__ import annotations

from models.customer import Customer
from repositories.json_repository import JsonRepository


class CustomerRepository(JsonRepository[Customer]):
    filename = "customers.json"
    id_prefix = "C"

    @classmethod
    def _entity_from_dict(cls, data: dict) -> Customer:
        return Customer.from_dict(data)
