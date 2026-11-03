## 2026-11-01T02:47:48Z
You are survey_spec_1, a teamwork_spec_miner subagent.
Your working directory is: D:\Module 1\.agents\teamwork\survey_spec_1
Original Request file: D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md

MISSION:
Conduct a comprehensive survey of all specifications, requirements, data schemas, business rules, and error conditions for the project.
Read D:\Module 1\.agents\teamwork\ORIGINAL_REQUEST.md and README.md.

Specifically investigate and detail:
1. Data files (data/map_graph.json, data/users.json, data/orders.json):
   - Current contents vs required contents (6 mentor nodes + 2 customer nodes CUSTOMER_2, CUSTOMER_3; 12 bidirectional edges with exact coordinates and weights; 4 users U001-U004).
   - What data needs to be populated or preserved.
2. Specifications for routing_service.py:
   - 6 error conditions of load_map_graph raising MapDataError in Vietnamese (non-existent file, empty file, invalid JSON with .bak fallback detection, missing/empty nodes, missing RESTAURANT node, ValueError from Graph.from_dict wrapped as MapDataError).
   - is_valid_delivery_node rules.
   - NamedTuples SingleRoute, RouteLeg, BatchRoute fields.
   - route_single_order and plan_batch_route (nearest-neighbor logic, tie-breaking by lexicographical id, full_path concatenation without duplicating juncture nodes, expanded_total semantics, complexity annotation).
   - compare_trip_algorithms and build_map_figure_data specifications.
3. Specifications for Customer and CustomerManager:
   - Customer model attributes, validation, to_dict, from_dict.
   - CustomerManager interface, read-only behavior, error handling, SortedIndex integration.
4. Specifications for OrderManager:
   - Encapsulation (_orders, _name_index, _email_index, _undo_stack, _redo_stack, _graph).
   - Read-only properties (orders, get_order, get_all_orders, can_undo, can_redo).
   - Shipper status logic (BUSY if any DELIVERING order, else IDLE).
   - create_order validation (map error, shipper BUSY, delivery_node_id validation, error messages).
   - start_delivery atomic batch transition & undo/redo semantics.
   - complete_delivery single order transition to PAID and shipper IDLE transition.
   - update_order_status guardrails (block manual DELIVERING, enforce PriorityEngine order for CONFIRMED -> PREPARING).
   - safe load_orders handling corrupt entries into load_errors without crashing.
5. Exact error message strings and business invariants specified in ORIGINAL_REQUEST.md.

Deliver your detailed findings to:
D:\Module 1\.agents\teamwork\survey_spec_1\handoff.md
Send a completion message back to the orchestrator once done.
