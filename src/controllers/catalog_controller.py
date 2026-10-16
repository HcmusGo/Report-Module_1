"""Controller cho Tab 1: Quản lý dữ liệu. Người phụ trách: Lâm.

Mỗi hàm thao tác: try gọi Service, bắt AppError -> Result.fail(str(e)),
thành công -> Result.success("Đã thêm món ..."). KHÔNG chứa luật nghiệp vụ.
Mỗi hàm *_table() trả list[dict] (một dict một dòng) để st.dataframe hiển thị.
"""
from __future__ import annotations

from controllers.result import Result
from services.catalog_service import CatalogService
from services.map_service import MapService


class CatalogController:
    def __init__(self, catalog: CatalogService, maps: MapService) -> None:
        self._catalog, self._maps = catalog, maps

    # ---- Menu ----
    def menu_table(self, keyword: str = "") -> list[dict]:
        return self._catalog.get_menu_table(keyword) 

    def add_menu_item(self, name: str, price: int, prep_minutes: int, tags_text: str = "") -> Result:
        """tags_text: chuỗi 'cay, bán chạy' do người dùng gõ, tách thành set ở đây."""
        try
        tags_text 
        self._catalog.add_menu_item(name=name, price=price, prep_minutes=prep_minutes)
        return Result.success ("Đã thêm món {name} thành công")
         except AppError as e:
            return Result.fail(str(e))
    def update_menu_item(self, item_id: str, **changes) -> Result:
        try
        self._catalog.update_menu_item(item_id=item_id, **changes)
             return Result.success("Cập nhật thông tin món ăn thành công")
        except AppError as e:
             return Result.fail(str(e)) 
    def delete_menu_item(self, item_id: str) -> Result:
        try
        self._catalog.delete_menu_item(item_id=item_id)
             return Result.success("Xóa món ăn thành công")
        except AppError as e:
            return Result.fail(str(e))
    # ---- Khách hàng ----
    def customer_table(self, keyword: str = "") -> list[dict]:
        self._catalog.customer_table(keyword)
    def add_customer(self, name: str, phone: str, node_id: str) -> Result:
        try
        self._catalog.add_customer(name=name, phone=phone, node_id=node_id)
        return Result.success ("Thêm khách hàng {name} thành công")
         except AppError as e:
            return Result.fail(str(e))

    def update_customer(self, customer_id: str, **changes) -> Result:
        try
        self._catalog.update_customer(customer_id=customer_id, **changes)
             return Result.success("Cập nhật thông tin khách hàng thành công")
        except AppError as e:
             return Result.fail(str(e))
    def delete_customer(self, customer_id: str) -> Result:
        try 
        self._catalog.delete_customer(customer_id=customer_id)
             return Result.success("Xóa thông tin khách hàng thành công")
        except AppError as e:
            return Result.fail(str(e))
    # ---- Shipper ----
    def shipper_table(self) -> list[dict]: 
        self._catalog.get_shipper_table()

    def add_shipper(self, name: str, phone: str, node_id: str) -> Result:
        try 
        self._catalog.add_shipper(name=name, phone=phone, node_id=node_id)
        return Result.success("Đã thêm shipper {name} thành công")
        except AppError as e:
            return Result.fail(str(e))

    def update_shipper(self, shipper_id: str, **changes) -> Result:
        try 
        self._catalog.update_shipper(shipper_id=shipper_id, **changes)
        return Result.success("Cập nhật thông tin shipper thành công")
        except AppError as e:
            return Result.fail(str(e))
    def delete_shipper(self, shipper_id: str) -> Result:
        try 
        self._catalog.delete_shipper(shipper_id=shipper_id)
        return Result.success("Xóa thông tin shipper thành công")
        except AppError as e:
            return Result.fail(str(e))
    # ---- Bản đồ ----
    def place_table(self) -> list[dict]:
        self._maps.get_place_table()
    def road_table(self) -> list[dict]:
        self._maps.get_road_table()

    def add_place(self, name: str, x: float, y: float, kind: str = "JUNCTION") -> Result:
        try 
        self._maps.add_place(name=name, x=x, y=y, kind=kind)
        return Result.success("Thêm địa điểm {name} thành công")
        except AppError as e:
            return Result.fail(str(e))
    def add_road(self, a: str, b: str, distance_km: float, traffic_factor: float = 1.0) -> Result:
        try
        self._maps.add_road(a=a, b=b, distance_km=distance_km, traffic_factor=traffic_factor)
        return Result.success("Đã thêm đoạn đường nối từ {a} đến {b} với chiều dài là {distance_km} thành công")
        except AppError as e:
            return Result.fail(str(e))
    def update_road(self, road_id: str, **changes) -> Result:
        try 
        self._máp.update_road(road_id=road_id)
        return Result.success("Cập nhật thông tin đường thành công")
        except AppError as e:
            return Result.fail(str(e))
    def delete_road(self, road_id: str) -> Result:
        try 
        self._map.delete_road(road_id=road_id)
        return Result.success("Xóa đoạn đường thành công")
        except AppError as e:
            return Result.fail(str(e))
    def set_road_blocked(self, road_id: str, blocked: bool) -> Result:
        try 
        self._map.set_road_blocked(road_id=road_id, blocked=blocked)
        status = "chặn" if blocked else status = "bị chặn"
        return Result.success("Đã chuyển đoạn đường sang trạng thái {status} thành công")
        except AppError as e:
            return Result.fail(str(e))
