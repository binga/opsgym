from __future__ import annotations

from typing import Any


DOMAINS: dict[str, dict[str, Any]] = {
    "revenue-ops": {"workspace": "CRM, contracts, billing, email", "tools": ["crm", "billing", "email"], "tasks": ["territory reassignment", "renewal rescue", "quote reconciliation", "discount approval", "duplicate-account merge"]},
    "customer-support": {"workspace": "tickets, SLA policy, status page, knowledge base", "tools": ["support", "status", "kb"], "tasks": ["outage triage", "escalation routing", "entitlement check", "root-cause clustering", "handoff recovery"]},
    "security-operations": {"workspace": "SIEM alerts, identity, endpoint, runbooks", "tools": ["siem", "iam", "edr"], "tasks": ["phishing containment", "access-key rotation", "alert correlation", "privilege review", "incident timeline"]},
    "cloud-operations": {"workspace": "metrics, deploys, infrastructure state, tickets", "tools": ["cloud", "observability", "git"], "tasks": ["rollback decision", "capacity incident", "certificate renewal", "cost anomaly", "region failover"]},
    "finance": {"workspace": "ledger, invoices, purchase orders, bank feed", "tools": ["ledger", "ap", "bank"], "tasks": ["three-way match", "close reconciliation", "cash forecast", "expense exception", "revenue recognition"]},
    "procurement": {"workspace": "vendors, contracts, risk reviews, purchase requests", "tools": ["vendor", "contract", "risk"], "tasks": ["vendor onboarding", "renewal negotiation", "sanctions screening", "SLA comparison", "purchase approval"]},
    "hr-operations": {"workspace": "HRIS, recruiting, payroll, policy documents", "tools": ["hris", "ats", "payroll"], "tasks": ["onboarding repair", "leave reconciliation", "payroll correction", "candidate scheduling", "policy exception"]},
    "healthcare-admin": {"workspace": "scheduling, eligibility, claims, referrals", "tools": ["ehr", "claims", "payer"], "tasks": ["prior authorization", "claim denial appeal", "referral routing", "schedule recovery", "eligibility conflict"]},
    "supply-chain": {"workspace": "orders, inventory, carriers, warehouse events", "tools": ["erp", "wms", "carrier"], "tasks": ["stockout recovery", "shipment reroute", "supplier delay", "return disposition", "demand exception"]},
    "legal-operations": {"workspace": "matters, contracts, holds, policy library", "tools": ["clm", "matters", "ediscovery"], "tasks": ["clause deviation", "legal hold", "obligation tracking", "intake routing", "renewal notice"]},
    "data-operations": {"workspace": "catalog, warehouse, lineage, quality monitors", "tools": ["catalog", "sql", "lineage"], "tasks": ["schema incident", "metric reconciliation", "PII classification", "backfill planning", "pipeline recovery"]},
    "research-operations": {"workspace": "papers, experiment registry, datasets, compute queue", "tools": ["literature", "experiments", "compute"], "tasks": ["replication audit", "dataset provenance", "ablation planning", "compute allocation", "result reconciliation"]},
}


def environment_ideas() -> list[dict[str, Any]]:
    ideas: list[dict[str, Any]] = []
    modes = ("single-workspace", "cross-workspace", "multi-round")
    difficulties = ("medium", "hard", "frontier")
    for domain_index, (domain, spec) in enumerate(DOMAINS.items()):
        for task_index, task in enumerate(spec["tasks"]):
            mode = modes[(domain_index + task_index) % len(modes)]
            ideas.append({
                "id": f"{domain}-{task.replace(' ', '-')}",
                "domain": domain,
                "title": task.title(),
                "workspace": spec["workspace"],
                "tools": spec["tools"],
                "mode": mode,
                "difficulty": difficulties[(domain_index * 2 + task_index) % len(difficulties)],
                "observable_goal": f"Resolve the {task} case and leave auditable state changes.",
                "verifier": "Final-state assertions, policy invariants, evidence-access checks, and action-budget limits.",
                "expansion": "Generate entity, policy, failure, interruption, and requirement-revision variants.",
            })
    return ideas
