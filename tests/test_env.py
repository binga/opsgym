import unittest

from opsgym import OpsGymEnv, TASKS


class OpsGymTests(unittest.TestCase):
    def test_all_oracle_trajectories_reach_full_outcome(self):
        for task_id, task in TASKS.items():
            with self.subTest(task=task_id):
                env = OpsGymEnv(task_id)
                env.reset()
                final_info = {}
                terminated = truncated = False
                for action in task.oracle:
                    _, _, terminated, truncated, final_info = env.step(action)
                self.assertTrue(terminated)
                self.assertFalse(truncated)
                self.assertEqual(final_info["grade"]["outcome"], 1.0)
                self.assertEqual(final_info["grade"]["evidence"], 1.0)

    def test_invalid_action_is_safe_and_penalized(self):
        env = OpsGymEnv("crm_address")
        env.reset()
        observation, reward, terminated, truncated, _ = env.step({"tool": "crm.update_account", "args": {"account_id": "acct_acme", "fields": {"plan": "free"}}})
        self.assertLess(reward, 0)
        self.assertIn("error", observation["last_result"])
        self.assertFalse(terminated)
        self.assertFalse(truncated)

    def test_broken_tool_recovers_on_retry(self):
        env = OpsGymEnv("broken_tool")
        env.reset()
        first, _, _, _, _ = env.step({"tool": "crm.search", "args": {"query": "Acme"}})
        second, _, _, _, _ = env.step({"tool": "crm.search", "args": {"query": "Acme"}})
        self.assertTrue(first["last_result"]["retryable"])
        self.assertEqual(second["last_result"][0]["id"], "acct_acme")


if __name__ == "__main__":
    unittest.main()

