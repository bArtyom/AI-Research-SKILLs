import unittest

from diagsql.model import Assumption, AssumptionGraph, Diagnosis
from diagsql.repair import build_repair_plan


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.graph = AssumptionGraph([
            Assumption("metric", "metric", "metric"),
            Assumption("amount", "schema", "amount", dependencies=("metric",)),
            Assumption("refund", "filter", "refund", dependencies=("amount",)),
            Assumption("region", "schema", "region"),
            Assumption("time", "time", "time"),
            Assumption("status", "filter", "status"),
            Assumption("entity", "entity", "entity"),
            Assumption("join", "join", "join"),
        ])

    def test_repair_scope_includes_dependency_descendants_only(self):
        plan = build_repair_plan(self.graph, Diagnosis(frozenset({"metric"}), 0.0))
        self.assertEqual(plan.editable_ids, frozenset({"metric", "amount", "refund"}))
        self.assertNotIn("region", plan.editable_ids)

    def test_small_leaf_fault_uses_patch_mode(self):
        plan = build_repair_plan(self.graph, Diagnosis(frozenset({"region"}), 0.0))
        self.assertEqual(plan.mode, "patch")

    def test_broad_dependency_fault_can_trigger_global_regeneration(self):
        graph = AssumptionGraph([
            Assumption("root", "metric", "root"),
            Assumption("a", "filter", "a", dependencies=("root",)),
            Assumption("b", "filter", "b", dependencies=("root",)),
            Assumption("c", "filter", "c", dependencies=("root",)),
        ])
        plan = build_repair_plan(graph, Diagnosis(frozenset({"root"}), 0.0), global_threshold=0.6)
        self.assertEqual(plan.mode, "global_regenerate")


if __name__ == "__main__":
    unittest.main()
