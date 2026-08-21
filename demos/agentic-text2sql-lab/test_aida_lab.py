import unittest
from aida_lab import AIDAAgent, SQLiteWorld, create_demo_db


class AIDALabTests(unittest.TestCase):
    def test_adaptive_agent_reaches_verified_answer(self):
        state, ledger = AIDAAgent(SQLiteWorld(create_demo_db())).run(
            "Which regions grew fastest last quarter?"
        )
        self.assertGreaterEqual(state.verifier_score, 0.9)
        self.assertEqual(state.result[0][0], "North")
        self.assertEqual(ledger.user_interruptions, 1)
        self.assertGreaterEqual(ledger.db_calls, 2)

    def test_read_only_sandbox_rejects_writes(self):
        world = SQLiteWorld(create_demo_db())
        with self.assertRaises(ValueError):
            world.execute("DELETE FROM orders")


if __name__ == "__main__":
    unittest.main()
