import unittest

from diagsql.delta import ddmin


class DeltaTests(unittest.TestCase):
    def test_finds_one_minimal_semantic_failure_set(self):
        def fails(items: tuple[str, ...]) -> bool:
            values = set(items)
            return {"fiscal_calendar", "comparison_window"}.issubset(values)

        result = ddmin(
            ["enterprise", "active", "fiscal_calendar", "comparison_window", "region"],
            fails,
        )
        self.assertEqual(set(result), {"fiscal_calendar", "comparison_window"})

    def test_requires_initial_failure(self):
        with self.assertRaisesRegex(ValueError, "full input does not fail"):
            ddmin(["a", "b"], lambda _: False)

    def test_result_is_one_minimal(self):
        def fails(items: tuple[str, ...]) -> bool:
            values = set(items)
            return {"a", "b"}.issubset(values)

        result = ddmin(["a", "b", "c"], fails)
        self.assertTrue(fails(result))
        for item in result:
            smaller = tuple(x for x in result if x != item)
            self.assertFalse(fails(smaller))


if __name__ == "__main__":
    unittest.main()
