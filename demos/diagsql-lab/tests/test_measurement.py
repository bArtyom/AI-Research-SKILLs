import unittest

from diagsql.measurement import Measurement, choose_measurement, expected_information_gain
from diagsql.model import Diagnosis


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.diagnoses = [
            Diagnosis(frozenset({"metric"}), 0.0),
            Diagnosis(frozenset({"join"}), 0.0),
        ]
        self.probs = [0.5, 0.5]

    def test_perfect_split_has_one_bit_information_gain(self):
        measurement = Measurement(
            "ask_metric",
            cost=1.0,
            outcome_likelihoods={
                "metric": {("metric",): 1.0, ("join",): 0.0},
                "join": {("metric",): 0.0, ("join",): 1.0},
            },
        )
        self.assertAlmostEqual(expected_information_gain(measurement, self.diagnoses, self.probs), 1.0)

    def test_cost_can_make_cheaper_test_preferred(self):
        expensive = Measurement(
            "ask_user",
            cost=4.0,
            outcome_likelihoods={
                "metric": {("metric",): 1.0, ("join",): 0.0},
                "join": {("metric",): 0.0, ("join",): 1.0},
            },
        )
        cheap = Measurement(
            "count_probe",
            cost=0.5,
            outcome_likelihoods={
                "high_dup": {("metric",): 0.2, ("join",): 0.8},
                "low_dup": {("metric",): 0.8, ("join",): 0.2},
            },
        )
        choice = choose_measurement([expensive, cheap], self.diagnoses, self.probs, lambda_cost=0.25)
        self.assertEqual(choice.measurement.id, "count_probe")

    def test_rejects_incomplete_likelihood_distribution(self):
        measurement = Measurement(
            "bad",
            cost=0.0,
            outcome_likelihoods={
                "x": {("metric",): 0.8, ("join",): 1.0},
            },
        )
        with self.assertRaisesRegex(ValueError, "must sum to 1"):
            expected_information_gain(measurement, self.diagnoses, self.probs)


if __name__ == "__main__":
    unittest.main()
