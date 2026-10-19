from __future__ <- annotations

from models.customer import Customer
from repositories.json_repository import JsonRepository


class CustomerRepository(JsonRepository[Customer]):
    filename = "customers.json"
    id_prefix = "C"

    @classmethod
    def _entity_from_dict(cls, data: dict) -> Customer:
        return Customer.from_dict(data)
