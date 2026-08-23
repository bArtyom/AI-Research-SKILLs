import unittest

from diagsql.measurement import Measurement
from diagsql.model import Assumption, AssumptionGraph, Conflict
from diagsql.simulator import ControlledEpisode, ControlledMeasurement, run_active_diagnosis


class SimulatorTests(unittest.TestCase):
    def test_active_measurement_resolves_metric_vs_join(self):
        graph = AssumptionGraph([
            Assumption("metric", "metric", "wrong revenue definition"),
            Assumption("join", "join", "wrong join cardinality"),
        ])
        initial = [Conflict(frozenset({"metric", "join"}), "initial")]
        measurement = Measurement(
            "count_probe",
            cost=0.5,
            outcome_likelihoods={
                "duplication": {("metric",): 0.0, ("join",): 1.0},
                "no_duplication": {("metric",): 1.0, ("join",): 0.0},
            },
        )
        controlled = ControlledMeasurement(
            measurement=measurement,
            actual_outcome_by_fault={("metric",): "no_duplication", ("join",): "duplication"},
            conflicts_by_outcome={
                "duplication": (Conflict(frozenset({"join"}), "probe_join"),),
                "no_duplication": (Conflict(frozenset({"metric"}), "probe_metric"),),
            },
        )
        episode = ControlledEpisode(graph, frozenset({"join"}), tuple(initial), (controlled,))
        trace = run_active_diagnosis(episode, max_steps=2)
        self.assertEqual(trace.final_diagnoses[0].faulty_ids, frozenset({"join"}))
        self.assertEqual(trace.measurement_ids, ("count_probe",))
        self.assertEqual(trace.outcomes, ("duplication",))
        self.assertAlmostEqual(trace.total_cost, 0.5)

    def test_stops_without_measurement_when_already_resolved(self):
        graph = AssumptionGraph([
            Assumption("metric", "metric", "metric"),
            Assumption("join", "join", "join"),
        ])
        episode = ControlledEpisode(
            graph=graph,
            hidden_faults=frozenset({"metric"}),
            initial_conflicts=(Conflict(frozenset({"metric"}), "hard"),),
            measurements=(),
        )
        trace = run_active_diagnosis(episode)
        self.assertEqual(trace.final_diagnoses[0].faulty_ids, frozenset({"metric"}))
        self.assertEqual(trace.measurement_ids, ())
        self.assertEqual(trace.total_cost, 0.0)


if __name__ == "__main__":
    unittest.main()
