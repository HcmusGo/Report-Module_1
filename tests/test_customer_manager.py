"""
Test các chức năng của Customer và CustomerManager (Phần 2 và Milestone M4).
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.core.customer_manager import CustomerManager
from src.core.storage import save_json
from src.models.customer import Customer


class TestCustomerManager(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.storage_path = self.temp_path / "test_users.json"

        # Dữ liệu khách hàng mẫu
        self.sample_users = [
            {
                "id": "U001",
                "name": "Nguyễn Văn An",
                "email": "an@example.com",
                "is_vip": True,
                "node_id": "CUSTOMER",
            },
            {
                "id": "U002",
                "name": "Trần Thị Bình",
                "email": "binh@example.com",
                "is_vip": False,
                "node_id": "CUSTOMER_2",
            },
            {
                "id": "U003",
                "name": "Lê Văn Cường",
                "email": "cuong@example.com",
                "is_vip": False,
                "node_id": "CUSTOMER_3",
            },
            {
                "id": "U004",
                "name": "Phạm Thu Dung",
                "email": "dung@example.com",
                "is_vip": True,
                "node_id": "CUSTOMER_2",
            },
        ]
        save_json(self.storage_path, self.sample_users)
        self.cm = CustomerManager(storage_path=self.storage_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # 1. KIỂM TRA NẠP DỮ LIỆU CHUẨN VÀ TRA CỨU
    def test_load_standard_users_and_getters(self) -> None:
        """Kiểm tra nạp 4 người dùng chuẩn và các hàm get_all, get_by_id."""
        customers = self.cm.get_all()
        self.assertEqual(len(customers), 4)

        u1 = self.cm.get_by_id("U001")
        self.assertIsNotNone(u1)
        self.assertEqual(u1.id, "U001")
        self.assertEqual(u1.name, "Nguyễn Văn An")
        self.assertEqual(u1.email, "an@example.com")
        self.assertTrue(u1.is_vip)
        self.assertEqual(u1.node_id, "CUSTOMER")

        # Không tìm thấy id
        self.assertIsNone(self.cm.get_by_id("NON_EXISTENT"))
        self.assertIsNone(self.cm.get_by_id(123))  # type: ignore

    # 2. KIỂM TRA TÌM KIẾM THEO TÊN VÀ EMAIL (SORTEDINDEX, CASE-INSENSITIVE)
    def test_find_by_name(self) -> None:
        """Kiểm tra find_by_name không phân biệt hoa thường và tìm trùng lặp."""
        # Tìm chính xác (hoa / thường)
        res_lower = self.cm.find_by_name("nguyễn văn an")
        self.assertEqual(len(res_lower), 1)
        self.assertEqual(res_lower[0].id, "U001")

        res_upper = self.cm.find_by_name("NGUYỄN VĂN AN")
        self.assertEqual(len(res_upper), 1)
        self.assertEqual(res_upper[0].id, "U001")

        # Thêm khách hàng trùng tên
        dup_users = list(self.sample_users) + [
            {
                "id": "U005",
                "name": "Nguyễn Văn An",
                "email": "an2@example.com",
                "is_vip": False,
                "node_id": "CUSTOMER_3",
            }
        ]
        save_json(self.storage_path, dup_users)
        cm_dup = CustomerManager(storage_path=self.storage_path)

        res_dup = cm_dup.find_by_name("nguyễn văn an")
        self.assertEqual(len(res_dup), 2)
        self.assertEqual({c.id for c in res_dup}, {"U001", "U005"})

        # Tìm không thấy
        self.assertEqual(len(self.cm.find_by_name("Người Lạ")), 0)

    def test_find_by_email(self) -> None:
        """Kiểm tra find_by_email không phân biệt hoa thường và tìm trùng lặp."""
        res = self.cm.find_by_email("AN@EXAMPLE.COM")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "U001")

        # Trùng email
        dup_users = list(self.sample_users) + [
            {
                "id": "U006",
                "name": "An Bản Sao",
                "email": "an@example.com",
                "is_vip": False,
                "node_id": "CUSTOMER",
            }
        ]
        save_json(self.storage_path, dup_users)
        cm_dup = CustomerManager(storage_path=self.storage_path)

        res_dup = cm_dup.find_by_email("an@example.com")
        self.assertEqual(len(res_dup), 2)
        self.assertEqual({c.id for c in res_dup}, {"U001", "U006"})

        # Tìm không thấy
        self.assertEqual(len(self.cm.find_by_email("unknown@example.com")), 0)

    # 3. KIỂM TRA XỬ LÝ DỮ LIỆU HỎNG VÀ FILE THIẾU
    def test_corrupted_records_skipped_to_load_errors(self) -> None:
        """Kiểm tra bản ghi hỏng được bỏ qua và ghi vào load_errors không gây crash."""
        corrupted_data = [
            {"id": "U001", "name": "Hợp Lệ", "email": "valid@test.com", "node_id": "CUSTOMER"},
            "chuỗi không phải dict",
            {"id": "U002", "name": "Thiếu Email", "node_id": "CUSTOMER"},
            {"id": "U003", "name": "Sai Email", "email": "email_khong_co_at",
             "node_id": "CUSTOMER"},
            {"id": "U004", "name": "", "email": "ten_rong@test.com", "node_id": "CUSTOMER"},
        ]
        save_json(self.storage_path, corrupted_data)

        cm_corrupted = CustomerManager(storage_path=self.storage_path)
        # Chỉ có U001 hợp lệ nạp thành công
        self.assertEqual(len(cm_corrupted.get_all()), 1)
        self.assertIsNotNone(cm_corrupted.get_by_id("U001"))

        # Ghi nhận các lỗi vào load_errors
        self.assertGreater(len(cm_corrupted.load_errors), 0)

    def test_invalid_json_type_recorded_to_load_errors(self) -> None:
        """Kiểm tra file chứa dữ liệu không phải list/dict được ghi nhận vào load_errors."""
        save_json(self.storage_path, "Chuỗi ký tự")
        cm = CustomerManager(storage_path=self.storage_path)
        self.assertEqual(len(cm.get_all()), 0)
        self.assertIn("Dữ liệu khách hàng không hợp lệ", cm.load_errors[0])

    def test_missing_file_returns_empty_without_crash(self) -> None:
        """Kiểm tra đường dẫn file không tồn tại trả về rỗng không crash."""
        nonexistent = self.temp_path / "not_found.json"
        cm_missing = CustomerManager(storage_path=nonexistent)
        self.assertEqual(len(cm_missing.get_all()), 0)

    # 4. KIỂM TRA VALIDATION CỦA CUSTOMER MODEL
    def test_customer_model_validation(self) -> None:
        """Kiểm tra các ràng buộc dữ liệu của thực thể Customer."""
        # Tạo hợp lệ
        c = Customer(
            id="U001",
            name="Nguyễn Văn An",
            email="an@example.com",
            is_vip=True,
            node_id="CUSTOMER",
        )
        self.assertEqual(c.id, "U001")
        self.assertEqual(c.name, "Nguyễn Văn An")
        self.assertEqual(c.email, "an@example.com")
        self.assertTrue(c.is_vip)
        self.assertEqual(c.node_id, "CUSTOMER")

        # Tên rỗng hoặc khoảng trắng
        with self.assertRaises(ValueError):
            Customer("U002", "", "b@test.com", False, "CUSTOMER")
        with self.assertRaises(ValueError):
            Customer("U002", "   ", "b@test.com", False, "CUSTOMER")

        # Email không có '@' hoặc rỗng
        with self.assertRaises(ValueError):
            Customer("U003", "Tên", "email_sai", False, "CUSTOMER")
        with self.assertRaises(ValueError):
            Customer("U003", "Tên", "", False, "CUSTOMER")

        # Node id rỗng
        with self.assertRaises(ValueError):
            Customer("U004", "Tên", "test@example.com", False, "")
        with self.assertRaises(ValueError):
            Customer("U004", "Tên", "test@example.com", False, "   ")

        # Serialization to_dict và from_dict
        c_dict = c.to_dict()
        self.assertEqual(c_dict["id"], "U001")
        self.assertEqual(c_dict["name"], "Nguyễn Văn An")
        self.assertEqual(c_dict["email"], "an@example.com")
        self.assertTrue(c_dict["is_vip"])
        self.assertEqual(c_dict["node_id"], "CUSTOMER")

        c_restored = Customer.from_dict(c_dict)
        self.assertEqual(c_restored.id, c.id)
        self.assertEqual(c_restored.name, c.name)
        self.assertEqual(c_restored.email, c.email)
        self.assertEqual(c_restored.is_vip, c.is_vip)
        self.assertEqual(c_restored.node_id, c.node_id)

        # from_dict với dữ liệu không hợp lệ
        with self.assertRaises(ValueError):
            Customer.from_dict("không phải dict")  # type: ignore
        with self.assertRaises(ValueError):
            Customer.from_dict({"id": "U001", "name": "An"})  # thiếu email, node_id

        # Kiểm tra repr
        self.assertIn("Customer(id='U001'", repr(c))


if __name__ == "__main__":
    unittest.main()
