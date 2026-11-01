"""
Test các chức năng của RoutingService (Phần 1 và Milestone M4).
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.core.routing_service import (
    BatchRoute,
    MapDataError,
    SingleRoute,
    build_map_figure_data,
    compare_trip_algorithms,
    get_map_render_data,
    is_valid_delivery_node,
    load_map_graph,
    path_to_coordinates,
    plan_batch_route,
    route_single_order,
)
from src.models.graph_node import Graph, GraphNode


class TestRoutingService(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Dựng đồ thị chuẩn 8 đỉnh 12 cạnh
        self.canonical_graph = Graph()
        self.canonical_graph.add_node(GraphNode("RESTAURANT", "Quán ăn", 0.0, 0.0))
        self.canonical_graph.add_node(GraphNode("A", "Ngã tư A", 2.0, 2.0))
        self.canonical_graph.add_node(GraphNode("B", "Ngã tư B", 3.0, -1.0))
        self.canonical_graph.add_node(GraphNode("C", "Ngã ba C", 5.0, 2.0))
        self.canonical_graph.add_node(GraphNode("D", "Ngã tư D", 6.0, -1.0))
        self.canonical_graph.add_node(GraphNode("CUSTOMER", "Nhà khách hàng", 8.0, 1.0))
        self.canonical_graph.add_node(GraphNode("CUSTOMER_2", "Nhà khách hàng 2", 7.0, 4.0))
        self.canonical_graph.add_node(GraphNode("CUSTOMER_3", "Nhà khách hàng 3", 4.0, -4.0))

        edges = [
            ("RESTAURANT", "A", 2.8),
            ("RESTAURANT", "B", 3.2),
            ("A", "B", 3.2),
            ("A", "C", 3.0),
            ("B", "D", 3.0),
            ("C", "D", 3.2),
            ("C", "CUSTOMER", 3.2),
            ("D", "CUSTOMER", 2.8),
            ("C", "CUSTOMER_2", 2.8),
            ("CUSTOMER", "CUSTOMER_2", 3.2),
            ("B", "CUSTOMER_3", 3.2),
            ("D", "CUSTOMER_3", 3.6),
        ]
        for u, v, w in edges:
            self.canonical_graph.add_edge(u, v, w)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # 1. KIỂM TRA 6 TRƯỜNG HỢP LỖI CỦA load_map_graph
    def test_load_map_graph_error_nonexistent_file(self) -> None:
        """(a) File không tồn tại -> MapDataError."""
        fake_path = self.temp_path / "nonexistent_map.json"
        with self.assertRaises(MapDataError) as ctx:
            load_map_graph(str(fake_path))
        self.assertIn("không tồn tại", str(ctx.exception))

    def test_load_map_graph_error_empty_file(self) -> None:
        """(b) File rỗng 0 bytes hoặc chỉ chứa khoảng trắng -> MapDataError."""
        empty_file = self.temp_path / "empty_map.json"
        empty_file.write_text("", encoding="utf-8")
        with self.assertRaises(MapDataError) as ctx1:
            load_map_graph(str(empty_file))
        self.assertIn("rỗng", str(ctx1.exception))

        ws_file = self.temp_path / "whitespace_map.json"
        ws_file.write_text("   \n\t  \n  ", encoding="utf-8")
        with self.assertRaises(MapDataError) as ctx2:
            load_map_graph(str(ws_file))
        self.assertIn("rỗng", str(ctx2.exception))

    def test_load_map_graph_error_syntax_with_bak_file(self) -> None:
        """(c) JSON sai cú pháp: load_json đổi tên thành .bak -> MapDataError kèm thông báo .bak."""
        corrupt_file = self.temp_path / "corrupt_map.json"
        corrupt_file.write_text("{ GIA_TRI_SAI_CU_PHAP: ???", encoding="utf-8")

        with self.assertRaises(MapDataError) as ctx:
            load_map_graph(str(corrupt_file))
        self.assertIn(".bak", str(ctx.exception))
        self.assertIn("sai cú pháp", str(ctx.exception))

        # Xác nhận file .bak đã được sinh ra
        bak_file = self.temp_path / "corrupt_map.json.bak"
        self.assertTrue(bak_file.exists())

    def test_load_map_graph_error_missing_or_empty_nodes(self) -> None:
        """(d) Thiếu trường 'nodes' hoặc 'nodes' rỗng -> MapDataError."""
        no_nodes_file = self.temp_path / "no_nodes.json"
        no_nodes_file.write_text(json.dumps({"edges": []}), encoding="utf-8")
        with self.assertRaises(MapDataError) as ctx1:
            load_map_graph(str(no_nodes_file))
        self.assertIn("nodes", str(ctx1.exception))

        empty_nodes_file = self.temp_path / "empty_nodes.json"
        empty_nodes_file.write_text(json.dumps({"nodes": {}}), encoding="utf-8")
        with self.assertRaises(MapDataError) as ctx2:
            load_map_graph(str(empty_nodes_file))
        self.assertIn("nodes", str(ctx2.exception))

    def test_load_map_graph_error_missing_restaurant_node(self) -> None:
        """(e) Thiếu đỉnh xuất phát RESTAURANT -> MapDataError."""
        no_rest_file = self.temp_path / "no_restaurant.json"
        data = {
            "nodes": {
                "CUSTOMER_1": {"name": "Khách 1", "x": 1.0, "y": 2.0},
                "CUSTOMER_2": {"name": "Khách 2", "x": 3.0, "y": 4.0},
            },
            "edges": [],
        }
        no_rest_file.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(MapDataError) as ctx:
            load_map_graph(str(no_rest_file))
        self.assertIn("RESTAURANT", str(ctx.exception))

    def test_load_map_graph_error_graph_from_dict_value_error(self) -> None:
        """(f) Graph.from_dict ném ValueError -> bọc lại thành MapDataError."""
        bad_graph_file = self.temp_path / "bad_edge.json"
        data = {
            "nodes": {
                "RESTAURANT": {"name": "Quán", "x": 0.0, "y": 0.0},
            },
            # Cạnh nối tới đỉnh NON_EXISTENT chưa có trong nodes
            "edges": [["RESTAURANT", "NON_EXISTENT", 5.0]],
        }
        bad_graph_file.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(MapDataError) as ctx:
            load_map_graph(str(bad_graph_file))
        self.assertIn("Lỗi cấu trúc đồ thị bản đồ", str(ctx.exception))

    def test_load_map_graph_success(self) -> None:
        """Nạp thành công đồ thị hợp lệ từ file JSON tạm."""
        valid_file = self.temp_path / "valid_map.json"
        data = {
            "nodes": {
                "RESTAURANT": {"name": "Quán", "x": 0.0, "y": 0.0},
                "CUSTOMER": {"name": "Khách", "x": 2.0, "y": 0.0},
            },
            "edges": [["RESTAURANT", "CUSTOMER", 2.0]],
        }
        valid_file.write_text(json.dumps(data), encoding="utf-8")
        g = load_map_graph(str(valid_file))
        self.assertIsInstance(g, Graph)
        self.assertEqual(len(g), 2)
        self.assertTrue(g.has_node("RESTAURANT"))
        self.assertTrue(g.has_node("CUSTOMER"))

    # 2. KIỂM TRA is_valid_delivery_node
    def test_is_valid_delivery_node(self) -> None:
        """Kiểm tra hợp lệ: đỉnh nhận hàng phải khác quán, tồn tại và có đường đi."""
        # Hợp lệ và đến được
        self.assertTrue(is_valid_delivery_node(self.canonical_graph, "CUSTOMER"))
        self.assertTrue(is_valid_delivery_node(self.canonical_graph, "CUSTOMER_2"))
        self.assertTrue(is_valid_delivery_node(self.canonical_graph, "CUSTOMER_3"))
        self.assertTrue(is_valid_delivery_node(self.canonical_graph, "A"))

        # Không hợp lệ: là Quán ăn
        self.assertFalse(is_valid_delivery_node(self.canonical_graph, "RESTAURANT"))

        # Không hợp lệ: đỉnh không tồn tại
        self.assertFalse(is_valid_delivery_node(self.canonical_graph, "ZZZ"))
        self.assertFalse(is_valid_delivery_node(self.canonical_graph, ""))
        self.assertFalse(is_valid_delivery_node(self.canonical_graph, "   "))

        # Không hợp lệ: kiểu dữ liệu không phải chuỗi
        self.assertFalse(is_valid_delivery_node(self.canonical_graph, None))  # type: ignore

        # Không hợp lệ: đỉnh cô lập không có đường đi từ RESTAURANT
        isolated_graph = Graph()
        isolated_graph.add_node(GraphNode("RESTAURANT", "Quán", 0.0, 0.0))
        isolated_graph.add_node(GraphNode("ISOLATED", "Cô lập", 10.0, 10.0))
        self.assertFalse(is_valid_delivery_node(isolated_graph, "ISOLATED"))

    # 3. KIỂM TRA route_single_order
    def test_route_single_order(self) -> None:
        """Kiểm tra tìm đường đơn lẻ với Dijkstra và A*."""
        route_dijkstra = route_single_order(self.canonical_graph, "CUSTOMER_3", "dijkstra")
        self.assertIsInstance(route_dijkstra, SingleRoute)
        self.assertEqual(route_dijkstra.delivery_node_id, "CUSTOMER_3")
        self.assertEqual(route_dijkstra.path, ["RESTAURANT", "B", "CUSTOMER_3"])
        self.assertAlmostEqual(route_dijkstra.cost, 6.4)
        self.assertGreater(route_dijkstra.expanded, 0)
        self.assertEqual(len(route_dijkstra.coords), 3)

        route_astar = route_single_order(self.canonical_graph, "CUSTOMER_3", "astar")
        self.assertEqual(route_astar.path, ["RESTAURANT", "B", "CUSTOMER_3"])
        self.assertAlmostEqual(route_astar.cost, 6.4)

        # Lỗi khi node không hợp lệ hoặc không có đường
        with self.assertRaises(ValueError):
            route_single_order(self.canonical_graph, "RESTAURANT")
        with self.assertRaises(ValueError):
            route_single_order(self.canonical_graph, "ZZZ")
        with self.assertRaises(ValueError):
            route_single_order(self.canonical_graph, "CUSTOMER", algorithm="invalid_algo")

    # 4. KIỂM TRA plan_batch_route TRÊN BẢN ĐỒ CHUẨN
    def test_plan_batch_route_canonical(self) -> None:
        """Kiểm tra gom chuyến 3 điểm chuẩn: thứ tự, full_path, chi phí 16.0."""
        batch_dijkstra = plan_batch_route(
            self.canonical_graph,
            ["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"],
            algorithm="dijkstra",
        )
        self.assertIsInstance(batch_dijkstra, BatchRoute)

        # Thứ tự thăm theo Nearest-Neighbor
        self.assertEqual(
            batch_dijkstra.visit_order,
            ["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"],
        )

        # Lộ trình đầy đủ không lặp đỉnh nối
        expected_full_path = [
            "RESTAURANT", "B", "CUSTOMER_3", "D", "CUSTOMER", "CUSTOMER_2"
        ]
        self.assertEqual(batch_dijkstra.full_path, expected_full_path)

        # Tổng quãng đường đúng 16.0
        self.assertAlmostEqual(batch_dijkstra.total_cost, 16.0)

        # Kiểm tra không có hai đỉnh liên tiếp trùng nhau
        for i in range(len(batch_dijkstra.full_path) - 1):
            self.assertNotEqual(
                batch_dijkstra.full_path[i],
                batch_dijkstra.full_path[i + 1],
                f"Trùng lặp đỉnh liên tiếp tại vị trí {i}",
            )

        # Tổng chi phí bằng tổng chi phí các chặng
        sum_legs = sum(leg.cost for leg in batch_dijkstra.legs)
        self.assertAlmostEqual(batch_dijkstra.total_cost, sum_legs)

        # Chạy với A* cho cùng tổng chi phí 16.0
        batch_astar = plan_batch_route(
            self.canonical_graph,
            ["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"],
            algorithm="astar",
        )
        self.assertEqual(batch_astar.visit_order, batch_dijkstra.visit_order)
        self.assertAlmostEqual(batch_astar.total_cost, 16.0)

        # Trùng lặp điểm giao chỉ thăm 1 lần
        batch_dup = plan_batch_route(
            self.canonical_graph,
            ["CUSTOMER_2", "CUSTOMER_2"],
            algorithm="dijkstra",
        )
        self.assertEqual(batch_dup.visit_order, ["CUSTOMER_2"])
        self.assertEqual(len(batch_dup.legs), 1)

    def test_plan_batch_route_tie_breaking(self) -> None:
        """Kiểm tra hòa khoảng cách: ưu tiên chọn đỉnh có ID nhỏ hơn theo từ điển."""
        tie_graph = Graph()
        tie_graph.add_node(GraphNode("RESTAURANT", "Quán", 0.0, 0.0))
        # Hai đỉnh B_NODE và A_NODE cùng có khoảng cách 5.0 từ Quán
        tie_graph.add_node(GraphNode("B_NODE", "Điểm B", 0.0, 5.0))
        tie_graph.add_node(GraphNode("A_NODE", "Điểm A", 5.0, 0.0))
        tie_graph.add_edge("RESTAURANT", "B_NODE", 5.0)
        tie_graph.add_edge("RESTAURANT", "A_NODE", 5.0)

        # Truyền B_NODE trước, nhưng A_NODE có id nhỏ hơn theo từ điển
        batch = plan_batch_route(tie_graph, ["B_NODE", "A_NODE"])
        self.assertEqual(batch.visit_order[0], "A_NODE")

    def test_plan_batch_route_errors(self) -> None:
        """Kiểm tra các lỗi đầu vào của plan_batch_route."""
        # Danh sách rỗng
        with self.assertRaises(ValueError):
            plan_batch_route(self.canonical_graph, [])

        # Có điểm không hợp lệ
        with self.assertRaises(ValueError):
            plan_batch_route(self.canonical_graph, ["CUSTOMER", "INVALID_NODE"])

        # Chứa Quán ăn
        with self.assertRaises(ValueError):
            plan_batch_route(self.canonical_graph, ["RESTAURANT"])

    # 5. KIỂM TRA compare_trip_algorithms
    def test_compare_trip_algorithms(self) -> None:
        """Kiểm tra so sánh Dijkstra vs A* trả về đúng cấu trúc dict."""
        res = compare_trip_algorithms(
            self.canonical_graph,
            ["CUSTOMER_3", "CUSTOMER", "CUSTOMER_2"],
        )
        self.assertIn("dijkstra", res)
        self.assertIn("astar", res)
        self.assertIsInstance(res["dijkstra"], BatchRoute)
        self.assertIsInstance(res["astar"], BatchRoute)
        self.assertAlmostEqual(res["dijkstra"].total_cost, 16.0)
        self.assertAlmostEqual(res["astar"].total_cost, 16.0)

    # 6. KIỂM TRA build_map_figure_data VÀ CÁC HELPER
    def test_build_map_figure_data(self) -> None:
        """Kiểm tra xuất dữ liệu bản đồ 3 lớp (nodes, edges, route)."""
        full_path = ["RESTAURANT", "B", "CUSTOMER_3"]
        data = build_map_figure_data(self.canonical_graph, full_path)

        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertIn("route", data)

        # Kiểm tra cờ on_route
        nodes_dict = {n["id"]: n for n in data["nodes"]}
        self.assertTrue(nodes_dict["RESTAURANT"]["on_route"])
        self.assertTrue(nodes_dict["B"]["on_route"])
        self.assertTrue(nodes_dict["CUSTOMER_3"]["on_route"])
        self.assertFalse(nodes_dict["CUSTOMER_2"]["on_route"])

        # Kiểm tra mỗi cạnh vô hướng xuất hiện đúng 1 lần
        self.assertEqual(len(data["edges"]), 12)

        # Kiểm tra route có step tăng dần 0..N-1
        route = data["route"]
        self.assertEqual(len(route), len(full_path))
        for step, item in enumerate(route):
            self.assertEqual(item["step"], step)
            self.assertEqual(item["node_id"], full_path[step])

        # Khi full_path là None
        empty_data = build_map_figure_data(self.canonical_graph, None)
        self.assertEqual(empty_data["route"], [])
        self.assertTrue(all(not n["on_route"] for n in empty_data["nodes"]))

    def test_helpers(self) -> None:
        """Kiểm tra path_to_coordinates và get_map_render_data."""
        coords = path_to_coordinates(["RESTAURANT", "A"], self.canonical_graph)
        self.assertEqual(coords, [(0.0, 0.0), (2.0, 2.0)])

        render_data = get_map_render_data(self.canonical_graph, "RESTAURANT", "A")
        self.assertEqual(render_data["path"], ["RESTAURANT", "A"])
        self.assertEqual(render_data["path_coords"], [(0.0, 0.0), (2.0, 2.0)])
        self.assertAlmostEqual(render_data["total_distance"], 2.8)


if __name__ == "__main__":
    unittest.main()
