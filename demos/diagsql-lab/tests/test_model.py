import unittest

from diagsql.model import Assumption, AssumptionGraph, Conflict, Diagnosis, diagnosis_key


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.graph = AssumptionGraph([
            Assumption("metric", "metric", "revenue means net revenue", confidence=0.8),
            Assumption("amount", "schema", "orders.amount is the revenue source", dependencies=("metric",)),
            Assumption("refund", "filter", "refunds must be excluded", dependencies=("amount",)),
            Assumption("region", "schema", "customers.region is the grouping dimension"),
        ])

    def test_descendants_follow_dependency_edges(self):
        self.assertEqual(self.graph.descendants({"metric"}), {"amount", "refund"})

    def test_rejects_unknown_dependencies(self):
        with self.assertRaisesRegex(ValueError, "unknown dependency"):
            AssumptionGraph([Assumption("x", "metric", "x", dependencies=("missing",))])

    def test_conflict_must_not_be_empty(self):
        with self.assertRaisesRegex(ValueError, "at least one assumption"):
            Conflict(frozenset(), evidence_id="e")

    def test_diagnosis_key_is_stable(self):
        diagnosis = Diagnosis(frozenset({"refund", "metric"}), score=2.0)
        self.assertEqual(diagnosis_key(diagnosis), ("metric", "refund"))


if __name__ == "__main__":
    unittest.main()
