import unittest

from diagsql.diagnosis import minimal_hitting_sets, rank_diagnoses
from diagsql.model import Assumption, AssumptionGraph, Conflict


class DiagnosisTests(unittest.TestCase):
    def test_minimal_hitting_sets_for_two_conflicts(self):
        conflicts = [
            Conflict(frozenset({"metric", "filter"}), "e1"),
            Conflict(frozenset({"filter", "time"}), "e2"),
        ]
        result = set(minimal_hitting_sets(conflicts, max_cardinality=2))
        self.assertEqual(result, {frozenset({"filter"}), frozenset({"metric", "time"})})

    def test_non_minimal_supersets_are_removed(self):
        conflicts = [Conflict(frozenset({"metric"}), "e1")]
        self.assertEqual(minimal_hitting_sets(conflicts, max_cardinality=3), [frozenset({"metric"})])

    def test_soft_conflict_ranks_consistent_diagnosis_first(self):
        graph = AssumptionGraph([
            Assumption("metric", "metric", "metric"),
            Assumption("filter", "filter", "filter"),
            Assumption("time", "time", "time"),
        ])
        conflicts = [
            Conflict(frozenset({"metric", "filter"}), "hard", hard=True),
            Conflict(frozenset({"metric"}), "soft", hard=False, weight=2.0),
        ]
        ranked = rank_diagnoses(
            graph,
            conflicts,
            fault_priors={"metric": 0.2, "filter": 0.2, "time": 0.2},
            max_cardinality=1,
        )
        self.assertEqual(ranked[0].faulty_ids, frozenset({"metric"}))


if __name__ == "__main__":
    unittest.main()
