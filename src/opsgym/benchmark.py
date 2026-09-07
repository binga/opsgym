from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import random
from pathlib import Path
from typing import Any, Callable

from .env import OpsGymEnv
from .conversation_env import ConversationEnv, TASKS as CONVERSATION_TASKS
from .tasks import TASKS, Action, TaskSpec


Agent = Callable[[dict[str, Any], Any], Action]


@dataclass(frozen=True)
class TrialResult:
    task_id: str
    trial: int
    score: float
    passed: bool
    steps: int
    terminated: bool
    grade: dict[str, Any]


def oracle_agent(observation: dict[str, Any], task: Any) -> Action:
    step = task.max_steps - int(observation["steps_remaining"])
    if step < len(task.oracle):
        return task.oracle[step]
    return {"tool": "finish", "args": {"summary": "Reference trajectory complete."}}


def random_agent(observation: dict[str, Any], task: Any) -> Action:
    del task
    readable = [tool for tool in observation["available_tools"] if ".search" in tool]
    if observation["steps_remaining"] <= 1 or not readable:
        return {"tool": "finish", "args": {"summary": "Unable to complete."}}
    return {"tool": random.choice(readable), "args": {"query": "Acme"}}


def run_trial(task_id: str, agent: Agent, trial: int = 1, seed: int = 0) -> TrialResult:
    random.seed(seed)
    env = OpsGymEnv(task_id) if task_id in TASKS else ConversationEnv(task_id)
    observation, _ = env.reset(seed=seed)
    final_info: dict[str, Any] = {}
    terminated = truncated = False
    while not (terminated or truncated):
        action = agent(observation, env.task)
        observation, _, terminated, truncated, final_info = env.step(action)
    grade = final_info.get("grade", {"outcome": 0, "compliance": 0, "communication": 0, "evidence": 0})
    weighted = grade["outcome"] + .30 * grade["compliance"] + .20 * grade["communication"] + .15 * grade["evidence"]
    score = round(100 * weighted / 1.65, 1)
    return TrialResult(task_id, trial, score, bool(grade["outcome"]), env.step_count, terminated, grade)


def run_benchmark(agent: Agent, trials: int = 1, seed: int = 0) -> dict[str, Any]:
    task_ids = [*TASKS, *CONVERSATION_TASKS]
    results = [run_trial(task_id, agent, trial + 1, seed + trial) for task_id in task_ids for trial in range(trials)]
    return {
        "summary": {
            "score": round(sum(r.score for r in results) / len(results), 1),
            "pass_rate": round(100 * sum(r.passed for r in results) / len(results), 1),
            "tasks": len(task_ids),
            "trials_per_task": trials,
        },
        "results": [asdict(result) for result in results],
    }


def write_json(result: dict[str, Any], output: str | Path | None) -> None:
    payload = json.dumps(result, indent=2) + "\n"
    if output:
        Path(output).write_text(payload)
    else:
        print(payload, end="")
