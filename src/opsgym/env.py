from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from .database import connect, log_action, row, rows
from .tasks import TASKS, TaskSpec


class OpsGymEnv:
    """A compact, Gym-style workplace simulator with state-based grading."""

    def __init__(self, task_id: str = "crm_address") -> None:
        if task_id not in TASKS:
            raise KeyError(f"Unknown task {task_id!r}; choose one of {sorted(TASKS)}")
        self.task: TaskSpec = TASKS[task_id]
        self.db = connect()
        self.context: dict[str, Any] = {}
        self.step_count = 0
        self.done = False
        self.last_result: Any = None
        self.notifications: list[str] = []
        self.faults: dict[str, int] = {}

    def reset(self, *, seed: int | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        del seed  # Fixtures are deterministic; the API leaves room for generated variants.
        self.db.close()
        self.db = connect()
        self.context = self.task.setup(self.db)
        self.faults = dict(self.context.get("faults", {}))
        self.step_count = 0
        self.done = False
        self.last_result = None
        self.notifications = []
        return self._observation(), {"task_id": self.task.id, "title": self.task.title}

    def step(self, action: dict[str, Any]) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        if self.done:
            raise RuntimeError("Episode is finished; call reset() before stepping again")
        if not isinstance(action, dict) or "tool" not in action:
            raise ValueError("Action must be {'tool': <name>, 'args': {...}}")
        self.step_count += 1
        tool = str(action["tool"])
        args = dict(action.get("args", {}))
        if self.task.interrupt_at == self.step_count and self.task.interrupt:
            self.notifications.append(self.task.interrupt)

        if self.faults.get(tool, 0) > 0:
            self.faults[tool] -= 1
            result = {"error": "temporary service unavailable", "retryable": True}
            log_action(self.db, self.step_count, tool, args, False, result)
            self.last_result = result
            return self._observation(), -0.1, False, False, {"error": result["error"]}

        try:
            result = self._dispatch(tool, args)
            ok = "error" not in result if isinstance(result, dict) else True
        except (KeyError, TypeError, ValueError) as exc:
            result, ok = {"error": str(exc)}, False
        log_action(self.db, self.step_count, tool, args, ok, result)
        self.last_result = result

        terminated = tool == "finish" and ok
        truncated = self.step_count >= self.task.max_steps and not terminated
        reward = -0.02 if ok else -0.1
        info: dict[str, Any] = {}
        if terminated or truncated:
            self.done = True
            summary = str(args.get("summary", ""))
            report = self.task.grader(self.db, self.context, summary)
            terminal_reward = (
                report["outcome"]
                + 0.30 * report["compliance"]
                + 0.20 * report["communication"]
                + 0.15 * report["evidence"]
            )
            reward += terminal_reward
            info["grade"] = report
            info["terminal_reward"] = terminal_reward
        return self._observation(), reward, terminated, truncated, info

    def _observation(self) -> dict[str, Any]:
        return {
            "goal": self.task.goal,
            "last_result": self.last_result,
            "notifications": list(self.notifications),
            "steps_remaining": max(0, self.task.max_steps - self.step_count),
            "available_tools": [
                "crm.search", "crm.get_account", "crm.get_contract", "crm.update_account",
                "email.search", "email.read", "email.send",
                "billing.search", "billing.get_invoice", "billing.issue_credit", "billing.schedule_downgrade",
                "support.search", "support.read_ticket", "support.update_ticket", "support.escalate",
                "status.search_incidents", "usage.search", "calendar.schedule", "finish",
            ],
        }

    def _dispatch(self, tool: str, args: dict[str, Any]) -> Any:
        if tool == "finish":
            return {"finished": True, "summary": str(args.get("summary", ""))}
        if tool == "crm.search":
            q = f"%{args['query']}%"
            return rows(self.db, "SELECT * FROM accounts WHERE id LIKE ? OR name LIKE ? OR legal_name LIKE ?", (q, q, q))
        if tool == "crm.get_account":
            return row(self.db, "SELECT * FROM accounts WHERE id=?", (args["account_id"],)) or {"error": "account not found"}
        if tool == "crm.get_contract":
            return row(self.db, "SELECT * FROM contracts WHERE account_id=?", (args["account_id"],)) or {"error": "contract not found"}
        if tool == "crm.update_account":
            allowed = {"legal_name", "address", "status", "risk_level"}
            fields = dict(args["fields"])
            if not fields or not set(fields) <= allowed:
                return {"error": f"allowed fields: {sorted(allowed)}"}
            assignments = ", ".join(f"{key}=?" for key in fields)
            cur = self.db.execute(f"UPDATE accounts SET {assignments} WHERE id=?", (*fields.values(), args["account_id"]))
            self.db.commit()
            return {"updated": cur.rowcount, "fields": fields}
        if tool == "email.search":
            q = f"%{args['query']}%"
            return rows(self.db, "SELECT * FROM emails WHERE subject LIKE ? OR body LIKE ? OR account_id LIKE ?", (q, q, q))
        if tool == "email.read":
            return row(self.db, "SELECT * FROM emails WHERE id=?", (args["email_id"],)) or {"error": "email not found"}
        if tool == "email.send":
            self.db.execute(
                "INSERT INTO emails(account_id,sender,recipient,subject,body,direction) VALUES (?,?,?,?,?,'outbound')",
                (args.get("account_id"), "agent@opsgym.local", args["to"], args["subject"], args["body"]),
            )
            self.db.commit()
            return {"sent": True, "to": args["to"]}
        if tool == "billing.search":
            q = f"%{args['query']}%"
            return rows(self.db, "SELECT * FROM invoices WHERE id LIKE ? OR account_id LIKE ? OR period LIKE ?", (q, q, q))
        if tool == "billing.get_invoice":
            return row(self.db, "SELECT * FROM invoices WHERE id=?", (args["invoice_id"],)) or {"error": "invoice not found"}
        if tool == "billing.issue_credit":
            inv = row(self.db, "SELECT * FROM invoices WHERE id=?", (args["invoice_id"],))
            if not inv:
                return {"error": "invoice not found"}
            contract = row(self.db, "SELECT * FROM contracts WHERE account_id=?", (inv["account_id"],))
            if inv["kind"] != "duplicate" and float(args["amount"]) > float(contract["refund_limit"]):
                return {"error": "amount exceeds authorization limit; escalate"}
            if float(args["amount"]) > float(inv["amount"]):
                return {"error": "credit exceeds invoice amount"}
            self.db.execute("INSERT INTO credits(invoice_id,amount,reason) VALUES (?,?,?)", (args["invoice_id"], args["amount"], args["reason"]))
            self.db.execute("UPDATE invoices SET status='credited' WHERE id=?", (args["invoice_id"],))
            self.db.commit()
            return {"credited": args["amount"], "invoice_id": args["invoice_id"]}
        if tool == "billing.schedule_downgrade":
            contract = row(self.db, "SELECT * FROM contracts WHERE account_id=?", (args["account_id"],))
            earliest = date(2026, 8, 23) + timedelta(days=int(contract["notice_days"]))
            requested = date.fromisoformat(args["effective_date"])
            if requested < earliest:
                return {"error": f"earliest permitted date is {earliest.isoformat()}"}
            self.db.execute("UPDATE accounts SET scheduled_plan=?, plan_effective_date=? WHERE id=?", (args["plan"], args["effective_date"], args["account_id"]))
            self.db.commit()
            return {"scheduled": True, "effective_date": args["effective_date"]}
        if tool == "support.search":
            q = f"%{args['query']}%"
            return rows(self.db, "SELECT * FROM tickets WHERE id LIKE ? OR account_id LIKE ? OR subject LIKE ? OR body LIKE ?", (q, q, q, q))
        if tool == "support.read_ticket":
            return row(self.db, "SELECT * FROM tickets WHERE id=?", (args["ticket_id"],)) or {"error": "ticket not found"}
        if tool == "support.update_ticket":
            allowed = {"priority", "status", "queue", "note"}
            fields = dict(args["fields"])
            if not fields or not set(fields) <= allowed:
                return {"error": f"allowed fields: {sorted(allowed)}"}
            assignments = ", ".join(f"{key}=?" for key in fields)
            cur = self.db.execute(f"UPDATE tickets SET {assignments} WHERE id=?", (*fields.values(), args["ticket_id"]))
            self.db.commit()
            return {"updated": cur.rowcount, "fields": fields}
        if tool == "support.escalate":
            self.db.execute("INSERT INTO escalations(ticket_id,reason) VALUES (?,?)", (args["ticket_id"], args["reason"]))
            self.db.execute("UPDATE tickets SET status='escalated', note=? WHERE id=?", (args["reason"], args["ticket_id"]))
            self.db.commit()
            return {"escalated": True}
        if tool == "status.search_incidents":
            q = f"%{args['query']}%"
            return rows(self.db, "SELECT * FROM incidents WHERE title LIKE ? OR status LIKE ?", (q, q))
        if tool == "usage.search":
            q = f"%{args['query']}%"
            return rows(self.db, "SELECT * FROM usage_metrics WHERE account_id LIKE ? OR metric LIKE ? OR period LIKE ?", (q, q, q))
        if tool == "calendar.schedule":
            attendees = json.dumps(args["attendees"])
            self.db.execute("INSERT INTO calendar_events(attendees,event_time,subject) VALUES (?,?,?)", (attendees, args["time"], args["subject"]))
            self.db.commit()
            return {"scheduled": True, "attendees": args["attendees"], "time": args["time"]}
        return {"error": f"unknown tool: {tool}"}

