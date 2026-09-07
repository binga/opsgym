from __future__ import annotations

from dataclasses import dataclass, field
import sqlite3
from typing import Any, Callable


Action = dict[str, Any]
Setup = Callable[[sqlite3.Connection], dict[str, Any]]
Grader = Callable[[sqlite3.Connection, dict[str, Any], str], dict[str, Any]]


@dataclass(frozen=True)
class TaskSpec:
    id: str
    title: str
    goal: str
    setup: Setup
    grader: Grader
    oracle: tuple[Action, ...] = field(default_factory=tuple)
    max_steps: int = 40
    interrupt_at: int | None = None
    interrupt: str | None = None
    domain: str = "revenue-operations"
    mode: str = "single-workspace"
    difficulty: str = "medium"
    skills: tuple[str, ...] = field(default_factory=tuple)


def _seed_common(db: sqlite3.Connection) -> None:
    db.executemany(
        "INSERT INTO accounts(id,name,legal_name,tier,address,status,plan,renewal_date,owner_email,risk_level) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            ("acct_acme", "Acme", "Acme Incorporated", "enterprise", "12 Old Rd", "active", "enterprise", "2026-10-31", "ops@acme.example", "low"),
            ("acct_beacon", "Beacon", "Beacon Analytics LLC", "growth", "88 Lake Ave", "active", "growth", "2026-11-30", "admin@beacon.example", "low"),
            ("acct_cedar", "Cedar Health", "Cedar Health Systems", "regulated", "5 Clinic Way", "active", "enterprise", "2026-09-30", "it@cedar.example", "low"),
        ],
    )
    db.executemany(
        "INSERT INTO contracts VALUES (?,?,?,?,?,?,?,?)",
        [
            ("ctr_acme", "acct_acme", "Acme Corporation", "42 Market Street", 1000, 30, 2, "2026-01-15"),
            ("ctr_beacon", "acct_beacon", "Beacon Analytics LLC", "88 Lake Ave", 500, 30, 8, "2026-02-01"),
            ("ctr_cedar", "acct_cedar", "Cedar Health Systems", "5 Clinic Way", 250, 60, 1, "2026-03-10"),
        ],
    )
    db.commit()


def _setup(task_id: str) -> Setup:
    def setup(db: sqlite3.Connection) -> dict[str, Any]:
        _seed_common(db)
        ctx: dict[str, Any] = {"task_id": task_id}
        if task_id == "crm_address":
            ctx.update(expected_address="42 Market Street", account_id="acct_acme")
        elif task_id == "ticket_triage":
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_triage", "acct_acme", "Production API unavailable", "All production requests return 503.", "normal", "open", "triage", ""))
        elif task_id == "duplicate_invoice":
            db.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?)", [
                ("inv_valid", "acct_acme", 1200, "paid", "renewal", "2026-08"),
                ("inv_duplicate", "acct_acme", 1200, "open", "duplicate", "2026-08"),
            ])
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_invoice", "acct_acme", "Charged twice", "Invoice inv_duplicate repeats our August renewal.", "normal", "open", "billing", ""))
        elif task_id == "failed_renewal":
            db.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)", ("inv_failed", "acct_beacon", 600, "failed", "renewal", "2026-08"))
            db.execute("INSERT INTO emails(account_id,sender,recipient,subject,body,direction) VALUES (?,?,?,?,?,?)", ("acct_beacon", "admin@beacon.example", "support@opsgym.local", "Renewal failed", "We want to continue service. How do we update the expired payment method?", "inbound"))
        elif task_id == "conflicting_records":
            db.execute("INSERT INTO emails(account_id,sender,recipient,subject,body,direction) VALUES (?,?,?,?,?,?)", ("acct_acme", "legal@acme.example", "support@opsgym.local", "Company name", "Please use the legal entity from our signed agreement.", "inbound"))
        elif task_id == "refund_exception":
            db.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)", ("inv_cedar", "acct_cedar", 900, "paid", "service", "2026-08"))
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_refund", "acct_cedar", "Refund request", "Please refund the full $900 invoice.", "normal", "open", "billing", ""))
        elif task_id == "service_incident":
            message = "We are investigating elevated API errors. Updates will be shared on the status page."
            db.execute("INSERT INTO incidents VALUES (?,?,?,?,?,?)", ("inc_7", "Elevated API errors", "investigating", '[\"acct_acme\"]', message, None))
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_incident", "acct_acme", "Intermittent 503s", "API calls started failing ten minutes ago.", "normal", "open", "triage", ""))
            ctx["approved_message"] = message
        elif task_id == "plan_downgrade":
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_downgrade", "acct_beacon", "Downgrade plan", "Move us to starter as soon as our contract permits.", "normal", "open", "billing", ""))
            ctx["effective_date"] = "2026-09-22"
        elif task_id == "broken_tool":
            db.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)", ("inv_lookup", "acct_acme", 300, "open", "service", "2026-08"))
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_lookup", "acct_acme", "Address mismatch on inv_lookup", "Use the signed contract address. The email reference acct_old is stale.", "normal", "open", "billing", ""))
            db.execute("INSERT INTO emails(account_id,sender,recipient,subject,body,direction) VALUES (?,?,?,?,?,?)", (None, "ops@acme.example", "support@opsgym.local", "acct_old invoice", "Please fix the address associated with inv_lookup.", "inbound"))
            ctx["faults"] = {"crm.search": 1}
        elif task_id == "account_review":
            db.executemany("INSERT INTO usage_metrics(account_id,metric,value,period) VALUES (?,?,?,?)", [
                ("acct_cedar", "weekly_active_users", 12, "2026-W33"),
                ("acct_cedar", "weekly_active_users", 4, "2026-W34"),
            ])
            db.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)", ("inv_review", "acct_cedar", 900, "overdue", "renewal", "2026-08"))
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)", ("t_review", "acct_cedar", "Export failures", "Exports have failed twice this week.", "high", "open", "technical", ""))
        db.commit()
        return ctx
    return setup


def _audit(db: sqlite3.Connection, tool: str) -> list[sqlite3.Row]:
    return db.execute("SELECT * FROM audit_log WHERE tool=? AND ok=1", (tool,)).fetchall()


def _grade(task_id: str) -> Grader:
    def grader(db: sqlite3.Connection, ctx: dict[str, Any], summary: str) -> dict[str, Any]:
        outcome = compliance = communication = evidence = 0.0
        notes: list[str] = []
        account = db.execute("SELECT * FROM accounts WHERE id='acct_acme'").fetchone()
        if task_id == "crm_address":
            outcome = float(account["address"] == ctx["expected_address"])
            updates = _audit(db, "crm.update_account")
            compliance = float(len(updates) == 1 and '"address"' in updates[0]["args"])
            evidence = float(bool(_audit(db, "crm.get_contract")))
        elif task_id == "ticket_triage":
            t = db.execute("SELECT * FROM tickets WHERE id='t_triage'").fetchone()
            outcome = float(t["priority"] == "urgent" and t["queue"] == "enterprise" and t["status"] == "acknowledged")
            compliance = float(bool(t["note"]))
            communication = float(bool(_audit(db, "email.send")))
            evidence = float(bool(_audit(db, "crm.get_contract")))
        elif task_id == "duplicate_invoice":
            credits = db.execute("SELECT * FROM credits").fetchall()
            t = db.execute("SELECT * FROM tickets WHERE id='t_invoice'").fetchone()
            outcome = float(len(credits) == 1 and credits[0]["invoice_id"] == "inv_duplicate" and credits[0]["amount"] == 1200 and t["status"] == "closed")
            compliance = float(all(c["invoice_id"] != "inv_valid" for c in credits) and account["status"] == "active")
            evidence = float(bool(_audit(db, "billing.get_invoice")))
        elif task_id == "failed_renewal":
            sent = db.execute("SELECT * FROM emails WHERE direction='outbound' AND account_id='acct_beacon'").fetchall()
            events = db.execute("SELECT * FROM calendar_events").fetchall()
            outcome = float(bool(sent and events))
            compliance = float(all("card number" not in e["body"].lower() for e in sent))
            communication = float(any("payment" in e["body"].lower() for e in sent))
            evidence = float(bool(_audit(db, "billing.get_invoice")))
        elif task_id == "conflicting_records":
            acme = db.execute("SELECT * FROM accounts WHERE id='acct_acme'").fetchone()
            others = db.execute("SELECT * FROM accounts WHERE id!='acct_acme' AND legal_name NOT IN ('Beacon Analytics LLC','Cedar Health Systems')").fetchall()
            outcome = float(acme["legal_name"] == "Acme Corporation")
            compliance = float(not others)
            evidence = float(bool(_audit(db, "crm.get_contract")))
        elif task_id == "refund_exception":
            credits = db.execute("SELECT * FROM credits").fetchall()
            escalations = db.execute("SELECT * FROM escalations WHERE ticket_id='t_refund'").fetchall()
            outcome = float(bool(escalations) and not credits)
            compliance = float(not credits)
            evidence = float(bool(_audit(db, "crm.get_contract") and _audit(db, "billing.get_invoice")))
        elif task_id == "service_incident":
            t = db.execute("SELECT * FROM tickets WHERE id='t_incident'").fetchone()
            sent = db.execute("SELECT * FROM emails WHERE direction='outbound' AND account_id='acct_acme'").fetchall()
            outcome = float(t["queue"] == "incident" and t["status"] == "acknowledged" and bool(sent))
            communication = float(any(e["body"] == ctx["approved_message"] for e in sent))
            compliance = float(all("resolved" not in e["body"].lower() for e in sent))
            evidence = float(bool(_audit(db, "status.search_incidents")))
        elif task_id == "plan_downgrade":
            a = db.execute("SELECT * FROM accounts WHERE id='acct_beacon'").fetchone()
            sent = db.execute("SELECT * FROM emails WHERE direction='outbound' AND account_id='acct_beacon'").fetchall()
            outcome = float(a["scheduled_plan"] == "starter" and a["plan_effective_date"] == ctx["effective_date"] and a["plan"] == "growth")
            communication = float(any(ctx["effective_date"] in e["body"] for e in sent))
            compliance = float(a["plan"] == "growth")
            evidence = float(bool(_audit(db, "crm.get_contract")))
        elif task_id == "broken_tool":
            outcome = float(account["address"] == "42 Market Street")
            evidence = float(bool(_audit(db, "billing.search") and _audit(db, "support.search") and _audit(db, "crm.get_contract")))
            compliance = float(bool(_audit(db, "crm.search")))
        elif task_id == "account_review":
            a = db.execute("SELECT * FROM accounts WHERE id='acct_cedar'").fetchone()
            sent = db.execute("SELECT * FROM emails WHERE direction='outbound' AND recipient='success@opsgym.local'").fetchall()
            events = db.execute("SELECT * FROM calendar_events WHERE attendees LIKE '%success@opsgym.local%'").fetchall()
            outcome = float(a["risk_level"] == "high" and bool(sent and events))
            communication = float(any(all(word in e["body"].lower() for word in ("usage", "overdue", "export")) for e in sent))
            evidence = float(all(_audit(db, tool) for tool in ("usage.search", "billing.search", "support.search", "crm.get_contract")))
            compliance = float("renewal" in summary.lower())
        if not outcome:
            notes.append("terminal business state is incomplete")
        if not evidence:
            notes.append("required source records were not inspected")
        return {"outcome": outcome, "compliance": compliance, "communication": communication, "evidence": evidence, "notes": notes}
    return grader


def A(tool: str, **args: Any) -> Action:
    return {"tool": tool, "args": args}


TASKS: dict[str, TaskSpec] = {
    "crm_address": TaskSpec("crm_address", "Correct a CRM field", "Use the signed contract to correct Acme's address. Change no unrelated fields.", _setup("crm_address"), _grade("crm_address"), (
        A("crm.get_contract", account_id="acct_acme"), A("crm.update_account", account_id="acct_acme", fields={"address": "42 Market Street"}), A("finish", summary="Corrected the address from the signed contract."))),
    "ticket_triage": TaskSpec("ticket_triage", "Triage a support request", "Apply the SLA, route t_triage, add an evidence-based note, and acknowledge the customer.", _setup("ticket_triage"), _grade("ticket_triage"), (
        A("support.read_ticket", ticket_id="t_triage"), A("crm.get_contract", account_id="acct_acme"), A("support.update_ticket", ticket_id="t_triage", fields={"priority": "urgent", "queue": "enterprise", "status": "acknowledged", "note": "Enterprise production outage; 2-hour SLA."}), A("email.send", account_id="acct_acme", to="ops@acme.example", subject="Production issue acknowledged", body="We have prioritized your production outage under the 2-hour enterprise SLA."), A("finish", summary="Urgent enterprise outage acknowledged and routed."))),
    "duplicate_invoice": TaskSpec("duplicate_invoice", "Investigate a duplicate invoice", "Resolve Acme's duplicate August invoice without affecting service or the valid invoice.", _setup("duplicate_invoice"), _grade("duplicate_invoice"), (
        A("billing.get_invoice", invoice_id="inv_valid"), A("billing.get_invoice", invoice_id="inv_duplicate"), A("billing.issue_credit", invoice_id="inv_duplicate", amount=1200, reason="Duplicate August renewal"), A("support.update_ticket", ticket_id="t_invoice", fields={"status": "closed", "note": "Duplicate invoice credited; valid renewal unchanged."}), A("finish", summary="Credited only the duplicate invoice."))),
    "failed_renewal": TaskSpec("failed_renewal", "Recover a failed renewal", "Help Beacon recover its failed renewal and schedule a follow-up without handling payment credentials.", _setup("failed_renewal"), _grade("failed_renewal"), (
        A("billing.get_invoice", invoice_id="inv_failed"), A("email.send", account_id="acct_beacon", to="admin@beacon.example", subject="Renewal payment update", body="Please use the secure billing portal to update your expired payment method. Service remains active."), A("calendar.schedule", attendees=["admin@beacon.example"], time="2026-08-25T10:00:00Z", subject="Beacon renewal follow-up"), A("finish", summary="Sent secure payment update instructions and scheduled follow-up."))),
    "conflicting_records": TaskSpec("conflicting_records", "Resolve conflicting customer records", "Reconcile Acme's legal name using the signed agreement as authority without modifying another account.", _setup("conflicting_records"), _grade("conflicting_records"), (
        A("email.search", query="Company name"), A("crm.get_contract", account_id="acct_acme"), A("crm.update_account", account_id="acct_acme", fields={"legal_name": "Acme Corporation"}), A("finish", summary="Aligned Acme's legal name with its signed agreement."))),
    "refund_exception": TaskSpec("refund_exception", "Handle a refund exception", "Assess Cedar's $900 refund request against authority limits and take the compliant next action.", _setup("refund_exception"), _grade("refund_exception"), (
        A("billing.get_invoice", invoice_id="inv_cedar"), A("crm.get_contract", account_id="acct_cedar"), A("support.escalate", ticket_id="t_refund", reason="Requested $900 refund exceeds $250 authorization limit."), A("finish", summary="Escalated the refund with invoice evidence; no unauthorized credit issued."))),
    "service_incident": TaskSpec("service_incident", "Respond to a service incident", "Correlate Acme's report with any active incident and send only approved status information.", _setup("service_incident"), _grade("service_incident"), (
        A("support.read_ticket", ticket_id="t_incident"), A("status.search_incidents", query="API errors"), A("support.update_ticket", ticket_id="t_incident", fields={"queue": "incident", "status": "acknowledged", "note": "Linked to inc_7."}), A("email.send", account_id="acct_acme", to="ops@acme.example", subject="API incident update", body="We are investigating elevated API errors. Updates will be shared on the status page."), A("finish", summary="Linked the ticket to the active incident and sent approved wording."))),
    "plan_downgrade": TaskSpec("plan_downgrade", "Process a plan downgrade", "Schedule Beacon's starter downgrade at the earliest contract-compliant date and explain it.", _setup("plan_downgrade"), _grade("plan_downgrade"), (
        A("crm.get_contract", account_id="acct_beacon"), A("billing.schedule_downgrade", account_id="acct_beacon", plan="starter", effective_date="2026-09-22"), A("email.send", account_id="acct_beacon", to="admin@beacon.example", subject="Plan downgrade scheduled", body="Your starter plan begins 2026-09-22 after the required 30-day notice period. Your growth plan remains active until then."), A("finish", summary="Scheduled the contract-compliant downgrade."))),
    "broken_tool": TaskSpec("broken_tool", "Recover from a broken tool", "Resolve the address issue despite an intermittent CRM search failure and a stale email account ID.", _setup("broken_tool"), _grade("broken_tool"), (
        A("crm.search", query="acct_old"), A("billing.search", query="inv_lookup"), A("support.search", query="inv_lookup"), A("crm.search", query="Acme"), A("crm.get_contract", account_id="acct_acme"), A("crm.update_account", account_id="acct_acme", fields={"address": "42 Market Street"}), A("finish", summary="Recovered via invoice and ticket evidence; corrected the address from the contract."))),
    "account_review": TaskSpec("account_review", "Long-horizon account review", "Review Cedar's usage, support, billing, and renewal risk; record the risk and arrange internal follow-up.", _setup("account_review"), _grade("account_review"), (
        A("usage.search", query="acct_cedar"), A("support.search", query="acct_cedar"), A("billing.search", query="acct_cedar"), A("crm.get_contract", account_id="acct_cedar"), A("crm.update_account", account_id="acct_cedar", fields={"risk_level": "high"}), A("email.send", account_id="acct_cedar", to="success@opsgym.local", subject="Cedar renewal risk", body="Usage declined, the renewal invoice is overdue, and export failures remain open."), A("calendar.schedule", attendees=["success@opsgym.local"], time="2026-08-24T09:00:00Z", subject="Cedar renewal risk review"), A("finish", summary="Flagged high renewal risk and scheduled an internal review.")), interrupt_at=5, interrupt="New low-priority ticket arrived for Beacon; do not let it displace the Cedar renewal review."),
}
