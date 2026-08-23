import unittest

from benchmark import run_benchmark


class BenchmarkTests(unittest.TestCase):
    def test_controlled_benchmark_improves_diagnosis_after_measurement(self):
        report = run_benchmark()
        self.assertEqual(report["aggregate"]["episodes"], 3)
        self.assertEqual(report["aggregate"]["fixed_top1_diagnosis_accuracy"], 0.0)
        self.assertEqual(report["aggregate"]["active_top1_diagnosis_accuracy"], 1.0)
        self.assertGreater(report["aggregate"]["mean_measurement_cost"], 0.0)
        self.assertTrue(all(item["diagnosis_correct"] for item in report["episodes"]))


if __name__ == "__main__":
    unittest.main()
