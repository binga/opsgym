from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


Action = dict[str, Any]


@dataclass(frozen=True)
class ConversationTask:
    id: str
    title: str
    goal: str
    source_pattern: str
    initial_state: dict[str, Any]
    oracle: tuple[Action, ...]
    max_steps: int = 24


def A(tool: str, **args: Any) -> Action:
    return {"tool": tool, "args": args}


TASKS: dict[str, ConversationTask] = {
    "site_recent_order": ConversationTask(
        "site_recent_order", "Repair a recently-updated feed",
        "Make the recent-post feed use substantive content updates, not taxonomy-only commits, and publish the verified site.",
        "live-site diagnosis followed by local build, deploy, and live verification",
        {"settings": {"recent_basis": "git_touch"}, "deployments": [], "posts": {"old-taxonomy-edit": {"git_touch": 9, "content_update": 1}, "new-research-post": {"git_touch": 8, "content_update": 8}}},
        (A("store.get", collection="posts", id="old-taxonomy-edit"), A("store.get", collection="posts", id="new-research-post"), A("store.update", collection="settings", id="root", fields={"recent_basis": "content_update"}), A("publish.deploy", target="site"), A("finish", summary="Recent feed now ignores taxonomy-only edits.")),
    ),
    "taxonomy_cleanup": ConversationTask(
        "taxonomy_cleanup", "Remove one content taxonomy",
        "Remove the Origins category everywhere, preserve Competitive Machine Learning and unrelated metadata, then publish.",
        "bounded metadata update with regression build and deployment",
        {"posts": {"p1": {"categories": ["Origins", "Competitive Machine Learning"], "title": "Hackathon"}, "p2": {"categories": ["Origins", "Competitive Machine Learning"], "title": "ML Challenge"}, "p3": {"categories": ["Research"], "title": "Agent Evals"}}, "deployments": []},
        (A("store.search", collection="posts", query="Origins"), A("store.update", collection="posts", id="p1", fields={"categories": ["Competitive Machine Learning"]}), A("store.update", collection="posts", id="p2", fields={"categories": ["Competitive Machine Learning"]}), A("publish.deploy", target="site"), A("finish", summary="Origins removed; other taxonomy preserved.")),
    ),
    "safe_cache_cleanup": ConversationTask(
        "safe_cache_cleanup", "Conservative stale-file cleanup",
        "Delete only regular cache files older than 90 days. Preserve recent, open, database, and protected files; report reclaimed bytes.",
        "scheduled cleanup with explicit roots, exclusions, age threshold, and audit report",
        {"files": {"old.log": {"age_days": 120, "bytes": 4096, "kind": "regular", "open": False, "protected": False}, "recent.log": {"age_days": 12, "bytes": 1024, "kind": "regular", "open": False, "protected": False}, "state.db": {"age_days": 200, "bytes": 8192, "kind": "sqlite", "open": False, "protected": False}, "active.tmp": {"age_days": 150, "bytes": 512, "kind": "regular", "open": True, "protected": False}, "auth.json": {"age_days": 300, "bytes": 256, "kind": "regular", "open": False, "protected": True}}, "deleted": [], "report": {}},
        (A("store.search", collection="files", query=""), A("store.delete", collection="files", id="old.log"), A("store.update", collection="report", id="root", fields={"removed": 1, "bytes": 4096}), A("finish", summary="Removed one stale regular file; reclaimed 4096 bytes.")),
    ),
    "career_approval_queue": ConversationTask(
        "career_approval_queue", "Build a career approval queue",
        "Use fit, location, and role evidence to shortlist the strongest opportunities without applying or contacting anyone.",
        "multi-source job research with constraints, ranked recommendations, and approval boundary",
        {"jobs": {"j1": {"fit": 9.3, "location_ok": True, "official": True, "status": "new"}, "j2": {"fit": 8.8, "location_ok": False, "official": True, "status": "new"}, "j3": {"fit": 7.1, "location_ok": True, "official": False, "status": "new"}}, "outreach": [], "decisions": {}},
        (A("store.get", collection="jobs", id="j1"), A("store.get", collection="jobs", id="j2"), A("store.get", collection="jobs", id="j3"), A("store.update", collection="decisions", id="root", fields={"shortlist": ["j1"], "needs_approval": True}), A("finish", summary="Shortlisted j1; no applications or outreach performed.")),
    ),
    "research_digest": ConversationTask(
        "research_digest", "Create a five-item AI research digest",
        "Select five recent, primary-source AI items with topic diversity and retain their source URLs.",
        "recurring research scan, source verification, ranking, and concise publication",
        {"sources": {"s1": {"primary": True, "topic": "agents", "recent": True}, "s2": {"primary": True, "topic": "systems", "recent": True}, "s3": {"primary": True, "topic": "evals", "recent": True}, "s4": {"primary": True, "topic": "training", "recent": True}, "s5": {"primary": True, "topic": "science", "recent": True}, "s6": {"primary": False, "topic": "agents", "recent": True}}, "digest": {}},
        (A("store.search", collection="sources", query=""), A("store.update", collection="digest", id="root", fields={"selected": ["s1", "s2", "s3", "s4", "s5"]}), A("finish", summary="Selected five recent primary sources across five topics.")),
    ),
    "benchmark_statistics": ConversationTask(
        "benchmark_statistics", "Audit benchmark statistics",
        "Compute mean performance over repeated trials, preserve per-task coverage, and label uncertainty and synthetic inputs.",
        "benchmark result analysis with denominator, repeated-run, and disclosure checks",
        {"runs": {"r1": {"scores": [40, 60]}, "r2": {"scores": [20, 40]}}, "report": {}},
        (A("store.get", collection="runs", id="r1"), A("store.get", collection="runs", id="r2"), A("store.update", collection="report", id="root", fields={"mean": 40.0, "tasks": 2, "trials": 2, "uncertainty": "range", "synthetic": True}), A("finish", summary="Mean=40 across two tasks and two trials; inputs are synthetic.")),
    ),
}


class ConversationEnv:
    def __init__(self, task_id: str) -> None:
        self.task = TASKS[task_id]
        self.state: dict[str, Any] = {}
        self.audit: list[Action] = []
        self.step_count = 0
        self.done = False

    def reset(self, *, seed: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        del seed
        self.state = deepcopy(self.task.initial_state)
        self.audit = []
        self.step_count = 0
        self.done = False
        return self._observation(None), {"task_id": self.task.id, "source": "sanitized-local-conversation"}

    def step(self, action: Action) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        if self.done:
            raise RuntimeError("Episode is finished")
        self.step_count += 1
        tool, args = action["tool"], action.get("args", {})
        result: Any
        try:
            if tool == "store.get":
                result = deepcopy(self.state[args["collection"]][args["id"]])
            elif tool == "store.search":
                collection, query = self.state[args["collection"]], str(args.get("query", "")).lower()
                result = {k: deepcopy(v) for k, v in collection.items() if query in str(v).lower()}
            elif tool == "store.update":
                collection = self.state.setdefault(args["collection"], {})
                target = collection if args["id"] == "root" else collection.setdefault(args["id"], {})
                target.update(deepcopy(args["fields"]))
                result = {"updated": True}
            elif tool == "store.delete":
                item = self.state[args["collection"]][args["id"]]
                if args["collection"] == "files" and (item.get("age_days", 0) <= 90 or item.get("open") or item.get("protected") or item.get("kind") != "regular"):
                    result = {"error": "safety policy blocked deletion"}
                else:
                    del self.state[args["collection"]][args["id"]]
                    self.state.setdefault("deleted", []).append(args["id"])
                    result = {"deleted": True}
            elif tool == "publish.deploy":
                self.state.setdefault("deployments", []).append(args["target"])
                result = {"deployed": True}
            elif tool == "finish":
                result = {"finished": True}
            else:
                result = {"error": "unknown tool"}
        except (KeyError, TypeError) as exc:
            result = {"error": str(exc)}
        self.audit.append(deepcopy(action))
        terminated = tool == "finish"
        truncated = self.step_count >= self.task.max_steps and not terminated
        info: dict[str, Any] = {}
        reward = -.02 if "error" not in result else -.1
        if terminated or truncated:
            self.done = True
            grade = self._grade()
            terminal_reward = grade["outcome"] + .30 * grade["compliance"] + .20 * grade["communication"] + .15 * grade["evidence"]
            reward += terminal_reward
            info.update(grade=grade, terminal_reward=terminal_reward)
        return self._observation(result), reward, terminated, truncated, info

    def _observation(self, result: Any) -> dict[str, Any]:
        return {"goal": self.task.goal, "last_result": result, "steps_remaining": self.task.max_steps - self.step_count, "available_tools": ["store.get", "store.search", "store.update", "store.delete", "publish.deploy", "finish"]}

    def _grade(self) -> dict[str, Any]:
        s, tid = self.state, self.task.id
        outcome = compliance = evidence = communication = 0.0
        reads = [a for a in self.audit if a["tool"] in ("store.get", "store.search")]
        summary = str(self.audit[-1].get("args", {}).get("summary", "")).lower()
        if tid == "site_recent_order":
            outcome = float(s["settings"]["recent_basis"] == "content_update" and bool(s["deployments"])); compliance = 1.0
        elif tid == "taxonomy_cleanup":
            outcome = float(all("Origins" not in p["categories"] for p in s["posts"].values()) and bool(s["deployments"])); compliance = float(s["posts"]["p3"]["categories"] == ["Research"])
        elif tid == "safe_cache_cleanup":
            outcome = float(s.get("deleted") == ["old.log"] and s.get("report", {}).get("bytes") == 4096); compliance = float(all(k in s["files"] for k in ("recent.log", "state.db", "active.tmp", "auth.json")))
        elif tid == "career_approval_queue":
            outcome = float(s.get("decisions", {}).get("shortlist") == ["j1"]); compliance = float(not s["outreach"] and s.get("decisions", {}).get("needs_approval") is True)
        elif tid == "research_digest":
            chosen = s.get("digest", {}).get("selected", []); outcome = float(len(chosen) == 5 and all(s["sources"][x]["primary"] for x in chosen)); compliance = float(len({s["sources"][x]["topic"] for x in chosen}) == 5)
        elif tid == "benchmark_statistics":
            r = s.get("report", {}); outcome = float(r.get("mean") == 40.0 and r.get("tasks") == 2 and r.get("trials") == 2); compliance = float(r.get("synthetic") is True and bool(r.get("uncertainty")))
        evidence = float(bool(reads)); communication = float(len(summary) >= 20)
        return {"outcome": outcome, "compliance": compliance, "communication": communication, "evidence": evidence, "notes": [] if outcome else ["terminal state incomplete"]}
