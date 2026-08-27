import json
import tempfile
import unittest
from pathlib import Path

from diagsql.bird_interact import (
    load_bird_jsonl,
    map_ambiguity_type,
    parse_bird_interact_record,
    recommend_measurements,
    single_fault_cases,
    summarize_bird_records,
    to_runtime_task,
)


class BirdInteractAdapterTests(unittest.TestCase):
    def sample_raw(self):
        return {
            "instance_id": "news_5",
            "selected_database": "news",
            "query": "Unambiguous evaluator-only query",
            "amb_user_query": "Show relatively high response times and category.",
            "high_level": True,
            "category": "Query",
            "user_query_ambiguity": {
                "critical_ambiguity": [
                    {
                        "term": "category",
                        "sql_snippet": "CASE WHEN resptime > 200 THEN 'Critical' END",
                        "is_mask": True,
                        "type": "intent_ambiguity",
                    },
                    {
                        "term": "relatively high response times",
                        "sql_snippet": "resptime > 150",
                        "is_mask": False,
                        "type": "semantic_ambiguity",
                    },
                ],
                "non_critical_ambiguity": [
                    {
                        "term": "sort",
                        "sql_snippet": "ORDER BY resptime DESC",
                        "is_mask": False,
                        "type": "non_critical_order",
                    }
                ],
            },
            "knowledge_ambiguity": [
                {
                    "term": "System Performance Index (SPI)",
                    "sql_snippet": "perfscore - loadscore",
                    "is_mask": False,
                    "type": "knowledge_ambiguity",
                    "deleted_knowledge": 4,
                }
            ],
            "sol_sql": ["SELECT secret"],
            "test_cases": [{"secret": True}],
        }

    def test_parse_normalizes_ambiguity_groups_without_evaluator_details_by_default(self):
        record = parse_bird_interact_record(self.sample_raw())
        self.assertEqual(record.instance_id, "news_5")
        self.assertEqual(len(record.critical_ambiguities), 2)
        self.assertEqual(len(record.noncritical_ambiguities), 1)
        self.assertEqual(len(record.knowledge_ambiguities), 1)
        self.assertIsNone(record.critical_ambiguities[0].sql_snippet)
        self.assertIsNone(record.knowledge_ambiguities[0].deleted_knowledge)

    def test_explicit_evaluator_mode_can_preserve_labels(self):
        record = parse_bird_interact_record(self.sample_raw(), preserve_evaluator_details=True)
        self.assertIn("CASE WHEN", record.critical_ambiguities[0].sql_snippet)
        self.assertEqual(record.knowledge_ambiguities[0].deleted_knowledge, 4)

    def test_runtime_view_excludes_evaluator_only_fields(self):
        record = parse_bird_interact_record(self.sample_raw(), preserve_evaluator_details=True)
        runtime = to_runtime_task(record)
        self.assertEqual(runtime.instance_id, "news_5")
        self.assertEqual(runtime.ambiguous_query, self.sample_raw()["amb_user_query"])
        self.assertFalse(hasattr(runtime, "query"))
        self.assertFalse(hasattr(runtime, "critical_ambiguities"))
        self.assertFalse(hasattr(runtime, "sol_sql"))
        self.assertFalse(hasattr(runtime, "test_cases"))

    def test_missing_required_fields_are_rejected(self):
        raw = self.sample_raw()
        del raw["amb_user_query"]
        with self.assertRaisesRegex(ValueError, "amb_user_query"):
            parse_bird_interact_record(raw)

    def test_fault_mapping_is_deterministic(self):
        self.assertEqual(map_ambiguity_type("knowledge_linking_ambiguity"), "business_rule")
        self.assertEqual(map_ambiguity_type("knowledge_ambiguity"), "business_rule")
        self.assertEqual(map_ambiguity_type("schema_linking_ambiguity"), "schema")
        self.assertEqual(map_ambiguity_type("semantic_ambiguity"), "semantic")
        self.assertEqual(map_ambiguity_type("intent_ambiguity"), "intent")
        self.assertEqual(map_ambiguity_type("new_future_type"), "other")

    def test_each_critical_ambiguity_becomes_a_single_fault_case(self):
        record = parse_bird_interact_record(self.sample_raw())
        cases = single_fault_cases(record)
        self.assertEqual([case.case_id for case in cases], ["news_5::critical:0", "news_5::critical:1"])
        self.assertEqual(cases[0].fault_family, "intent")
        self.assertEqual(cases[1].fault_family, "semantic")
        self.assertEqual(cases[0].hidden_faults, frozenset({"critical:0"}))

    def test_measurement_recommendations_match_fault_family(self):
        record = parse_bird_interact_record(self.sample_raw())
        semantic_actions = [m.action for m in recommend_measurements(record.critical_ambiguities[1])]
        self.assertEqual(semantic_actions, ["ask_user", "run_diagnostic_sql"])

        knowledge = record.knowledge_ambiguities[0]
        knowledge_actions = [m.action for m in recommend_measurements(knowledge)]
        self.assertEqual(knowledge_actions, ["retrieve_knowledge", "ask_user"])

    def test_jsonl_loader_and_statistics(self):
        first = self.sample_raw()
        second = {
            "instance_id": "news_9",
            "selected_database": "news",
            "amb_user_query": "Return total num by recommendation position.",
            "high_level": False,
            "category": "Query",
            "user_query_ambiguity": {
                "critical_ambiguity": [
                    {
                        "term": "total num",
                        "sql_snippet": "COUNT(*)",
                        "is_mask": False,
                        "type": "schema_linking_ambiguity",
                    }
                ],
                "non_critical_ambiguity": [],
            },
            "knowledge_ambiguity": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mini.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in (first, second)) + "\n", encoding="utf-8")
            records = load_bird_jsonl(path)
        stats = summarize_bird_records(records)
        self.assertEqual(stats.records, 2)
        self.assertEqual(stats.critical_ambiguities, 3)
        self.assertEqual(stats.noncritical_ambiguities, 1)
        self.assertEqual(stats.knowledge_ambiguities, 1)
        self.assertEqual(stats.records_with_multiple_critical, 1)
        self.assertEqual(stats.masked_ambiguities, 1)
        self.assertEqual(stats.ambiguity_type_counts["intent_ambiguity"], 1)
        self.assertEqual(stats.ambiguity_type_counts["schema_linking_ambiguity"], 1)

    def test_cli_summary_helper_returns_json_serializable_stats(self):
        from bird_adapter import summarize_path

        raw = {
            "instance_id": "one",
            "selected_database": "db",
            "amb_user_query": "Ambiguous query",
            "user_query_ambiguity": {"critical_ambiguity": [], "non_critical_ambiguity": []},
            "knowledge_ambiguity": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mini.jsonl"
            path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
            summary = summarize_path(path)
        self.assertEqual(summary["records"], 1)
        json.dumps(summary)

    def test_adapter_symbols_are_public_package_exports(self):
        import diagsql

        self.assertIs(diagsql.parse_bird_interact_record, parse_bird_interact_record)
        self.assertIs(diagsql.single_fault_cases, single_fault_cases)


if __name__ == "__main__":
    unittest.main()
