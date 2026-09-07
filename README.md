# OpsGym

OpsGym is an open benchmark for agents that operate across realistic workplace systems. It turns patterns from real local AI-agent conversations into sanitized, reusable task environments with executable state-based graders.

**Website:** https://binga.github.io/opsgym/  
**Repository:** https://github.com/binga/opsgym

The repository includes:

- 16 executable tasks across two simulator families
- 6 tasks reconstructed from sanitized local conversation patterns
- 60 environment concepts across 12 operational domains
- deterministic hidden-state grading for outcome, policy, evidence, and communication
- a benchmark runner with oracle and random baselines
- a static leaderboard and task-explorer website
- CI and GitHub Pages workflows

All website leaderboard numbers are explicitly synthetic. They demonstrate the reporting interface and are not claimed model evaluations.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
opsgym --list
opsgym site_recent_order --oracle
opsgym --benchmark oracle --trials 1
```

Run without installation:

```bash
PYTHONPATH=src python3 -m opsgym.cli --list
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m http.server 8080 --directory website
```

Then open `http://localhost:8080`.

## Design

The implementation applies four ideas from [Terminal-Universe](https://arxiv.org/html/2609.04148v1):

1. Recover environment state from observed agent trajectories.
2. Complete only the missing context needed to make the environment executable.
3. Re-query each environment with single-workspace, cross-workspace, and multi-round tasks.
4. Keep tasks only when an independent, executable verifier can score them.

`ConversationEnv` is the first reconstruction track. Its initial tasks derive from recurring patterns in accessible local histories: website diagnosis and deployment, taxonomy cleanup, guarded file cleanup, job-screening approval queues, research digests, and benchmark-statistics audits. Names, account identifiers, private paths, credentials, exact prose, and original solutions are excluded.

`OpsGymEnv` is the operational expansion track. It models CRM, billing, support, status, usage, email, and calendar systems. Its ten tasks test record reconciliation, incident handling, authorization boundaries, tool failure recovery, interruptions, and long-horizon account review.

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for reconstruction and contamination controls, and [docs/ENVIRONMENT_IDEAS.md](docs/ENVIRONMENT_IDEAS.md) for the 60-environment roadmap.

## Python API

```python
from opsgym import ConversationEnv

env = ConversationEnv("safe_cache_cleanup")
observation, info = env.reset(seed=0)
observation, reward, terminated, truncated, info = env.step({
    "tool": "store.search",
    "args": {"collection": "files", "query": ""},
})
```

Both environments use the Gymnasium step convention without requiring Gymnasium.

## Scoring

Each task is scored on a 0–100 scale:

```text
(1.00 × outcome + 0.30 × policy + 0.20 × communication + 0.15 × evidence) / 1.65
```

Action and error penalties remain in episode reward. The benchmark score uses the terminal state grade so different valid paths remain comparable.

## Bring your own agent

Implement a callable receiving `(observation, task)` and returning `{"tool": "tool.name", "args": {}}`, then pass it to `opsgym.benchmark.run_benchmark`. The observation exposes the goal, last tool result, remaining step budget, notifications, and available tool names. It does not expose grader logic or target state.

## Conversation ingestion

Checked-in data contains only reviewed, abstracted patterns. To bootstrap from another ChatGPT/Codex JSON export:

```bash
python scripts/ingest_conversations.py export.json --output private-seeds.json
```

The script extracts structural features and redacts emails, URLs, home-directory paths, and likely secret values. Keep raw exports and generated private seeds outside Git. Review every seed before turning it into a fixture.

## Repository map

```text
src/opsgym/             simulators, task fixtures, graders, benchmark harness
tests/                  oracle, safety, and cross-suite regression tests
data/seed-patterns.json sanitized reconstruction inventory
website/                static leaderboard and environment explorer
docs/                   methodology, roadmap, and research record
.github/workflows/      CI and Pages deployment
```

## Status

This is a working MVP, not a validated frontier leaderboard. The oracle baseline is a regression check. Real model runs require an external model adapter, repeated trials, trace storage, cost accounting, and independent task review.

## License

MIT
