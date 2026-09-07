# OpsGym research and build record

Audience: benchmark builders and agent researchers  
Date: 2026-09-08  
Scope: adapt Terminal-Universe to local personal-agent histories and ship an executable MVP

## Direct answer

Local agent histories are viable environment seeds because they contain repeated tool interactions, state mutations, failures, user revisions, safety boundaries, and observable completion checks. The useful unit is not the assistant answer. It is the latent workspace reconstructed from what the trajectory read and changed.

This repository implements that approach with a privacy boundary: 16 local workflow patterns are abstracted; six are implemented as synthetic executable fixtures; ten additional enterprise-operations tasks expand the same tool-use capabilities; 60 future environment concepts define the breadth roadmap.

## Evidence synthesis

Terminal-Universe reconstructs initial file states through deterministic replay, uses a completion agent to restore omitted context without solving the task, and filters for sufficient workspaces. It expands each environment through intent recovery, new tasks inside one workspace, cross-workspace dependency tasks, and persistent multi-round requests. Each task has an executable verifier, and only passing trajectories are retained. Source: [Terminal-Universe](https://arxiv.org/html/2609.04148v1), Qwen Team and Tsinghua University, 2026-09-03.

FrontierSWE demonstrates the desired benchmark product surface: a public task set, repeated runs, aggregate leaderboard, uncertainty range, per-task coverage, traces, cost/time reporting, task filters, and explicit task categories. Source: [FrontierSWE V2](https://www.frontierswe.com/), accessed 2026-09-08.

The sampled local histories support environment families spanning content publishing, site diagnosis, taxonomy revision, document editing, guarded system maintenance, career research, research curation, benchmark statistics, product comparison, visual composition, and troubleshooting. This observation comes from the user's accessible local task index and selected recent task histories. The raw histories are not copied into the repository.

## Design decision

The MVP uses deterministic in-memory state rather than cloning production services. This keeps tasks fast, offline, inspectable, and safe. The next fidelity step is to replace generic stores with containerized replicas of the applications exposed by each source trajectory while preserving the same hidden verifier contract.

## Limitations

The local-history sample is selected and small. The reconstructed fixtures preserve workflow structure but do not claim exact environment recovery. Synthetic leaderboard values are UI fixtures. No real model comparison is supported yet. GitHub publication and website deployment require authenticated external accounts.

## Recommendations

1. Add an authenticated model adapter and JSONL trace format.
2. Run at least five trials per task and publish mean, range, time, and cost.
3. Expand the six conversation-derived tasks by varying policies, distractors, failures, and user revisions.
4. Add independent verifier review and canary tasks before public claims.
5. Use opt-in, local-only raw trajectory ingestion; publish only sanitized fixtures.
