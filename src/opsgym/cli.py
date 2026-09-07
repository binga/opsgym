from __future__ import annotations

import argparse
import json
from pathlib import Path

from .env import OpsGymEnv
from .benchmark import oracle_agent, random_agent, run_benchmark, write_json
from .ideas import environment_ideas
from .tasks import TASKS
from .conversation_env import ConversationEnv, TASKS as CONVERSATION_TASKS


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the OpsGym workplace simulator")
    all_tasks = {**TASKS, **CONVERSATION_TASKS}
    parser.add_argument("task", nargs="?", choices=sorted(all_tasks))
    parser.add_argument("--list", action="store_true", help="list available tasks")
    parser.add_argument("--oracle", action="store_true", help="run the task's reference trajectory")
    parser.add_argument("--benchmark", choices=("oracle", "random"), help="run every task with a built-in baseline")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--output", help="write benchmark JSON to this path")
    parser.add_argument("--export-catalog", help="write the environment idea catalog as JSON")
    args = parser.parse_args()
    if args.export_catalog:
        Path(args.export_catalog).write_text(json.dumps(environment_ideas(), indent=2) + "\n")
        print(f"wrote {len(environment_ideas())} ideas to {args.export_catalog}")
        return
    if args.benchmark:
        agent = oracle_agent if args.benchmark == "oracle" else random_agent
        write_json(run_benchmark(agent, trials=args.trials), args.output)
        return
    if args.list or not args.task:
        for task in all_tasks.values():
            source = getattr(task, "source_pattern", "designed enterprise fixture")
            print(f"{task.id:24} {task.title} [{source}]")
        return
    env = OpsGymEnv(args.task) if args.task in TASKS else ConversationEnv(args.task)
    observation, info = env.reset()
    print(json.dumps({"observation": observation, "info": info}, indent=2))
    if args.oracle:
        total = 0.0
        for action in all_tasks[args.task].oracle:
            observation, reward, terminated, truncated, info = env.step(action)
            total += reward
            print(json.dumps({"action": action, "result": observation["last_result"], "reward": reward}, indent=2))
            if terminated or truncated:
                print(json.dumps({"total_reward": total, "info": info}, indent=2))
                break


if __name__ == "__main__":
    main()
