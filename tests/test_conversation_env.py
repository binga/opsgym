import unittest

from opsgym.benchmark import oracle_agent, run_benchmark
from opsgym.conversation_env import ConversationEnv, TASKS


class ConversationEnvironmentTests(unittest.TestCase):
    def test_sanitized_conversation_tasks_pass_reference_trajectories(self):
        for task_id, task in TASKS.items():
            with self.subTest(task=task_id):
                env = ConversationEnv(task_id)
                observation, _ = env.reset()
                info = {}
                for action in task.oracle:
                    observation, _, terminated, truncated, info = env.step(action)
                self.assertTrue(terminated)
                self.assertFalse(truncated)
                self.assertEqual(info["grade"]["outcome"], 1.0)
                self.assertEqual(info["grade"]["compliance"], 1.0)

    def test_cleanup_policy_blocks_protected_file(self):
        env = ConversationEnv("safe_cache_cleanup")
        env.reset()
        observation, reward, *_ = env.step({"tool": "store.delete", "args": {"collection": "files", "id": "auth.json"}})
        self.assertIn("error", observation["last_result"])
        self.assertLess(reward, 0)
        self.assertIn("auth.json", env.state["files"])

    def test_full_oracle_benchmark_includes_both_simulator_families(self):
        result = run_benchmark(oracle_agent)
        self.assertEqual(result["summary"]["tasks"], 16)
        self.assertEqual(result["summary"]["pass_rate"], 100.0)


if __name__ == "__main__":
    unittest.main()
