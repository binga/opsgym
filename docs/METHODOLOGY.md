# Methodology

## Reconstruction from local conversations

The seed corpus is a bounded sample of accessible local ChatGPT and Codex task histories. We retain workflow structure rather than conversation content:

- user-visible objective and requirement changes
- tool classes and ordering constraints
- state observed before a mutation
- safety or approval boundaries
- verification steps and final observable outcome
- failure, retry, interruption, and deployment patterns

The benchmark excludes names, emails, account IDs, local absolute paths, credentials, private document contents, exact user prose, exact agent answers, and implementation patches. Checked-in tasks use synthetic entities and fixtures.

## Terminal-Universe adaptation

Terminal-Universe reconstructs workspaces by replaying file operations, completing missing context, and retaining task-sufficient environments. It then expands them through intent recovery, new tasks within one workspace, cross-workspace dependencies, and multi-round requirement changes. OpsGym applies the same pipeline to workplace tool traces rather than only terminal repositories.

| Paper stage | OpsGym stage |
| --- | --- |
| Deterministic replay | Normalize read, search, update, delete, publish, and finish events |
| Agentic completion | Add synthetic records and policies required for a solvable task |
| Sufficiency filtering | Require a complete fixture, callable tools, and a passing reference trajectory |
| Intent recovery | Preserve the observable user goal, not the agent solution |
| Single-workspace synthesis | Vary records, policies, errors, and objectives in one app suite |
| Cross-workspace synthesis | Require facts from one system to make a safe change in another |
| Multi-round synthesis | Add compatible extensions, revisions, and conflicts to persistent state |
| Verification | Assert final state, invariants, evidence access, and step budgets |

Sources: [Terminal-Universe paper](https://arxiv.org/html/2609.04148v1), [FrontierSWE benchmark site](https://www.frontierswe.com/).

## Acceptance gate

A task is publishable only if:

1. The initial fixture is sufficient to solve the stated goal offline.
2. The goal does not reveal the hidden answer or target implementation.
3. At least one reference trajectory passes.
4. A prohibited mutation fails or lowers policy compliance.
5. The grader checks state rather than exact action sequence whenever possible.
6. No source-conversation identifiers or sensitive literals remain.
7. Synthetic or estimated benchmark results are labeled.

## Known limitations

- Six reconstructed tasks are a small, selected sample rather than a representative personal-agent corpus.
- The current fixtures are structured simulators, not full clones of production applications.
- Reference trajectories demonstrate solvability but not frontier difficulty.
- The synthetic leaderboard cannot support model comparisons.
- Raw histories are not packaged, preserving privacy but limiting external reconstruction audit.
