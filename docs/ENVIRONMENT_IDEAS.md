# Environment roadmap

`website/data/catalog.json` contains 60 concrete concepts generated from 12 domain workspaces and five task families per domain. Every item specifies tools, observable goal, verifier shape, difficulty, expansion mode, and variation axes.

## Priority build order

1. **Content operations** — site build, taxonomy repair, publishing, and regression verification.
2. **Personal system maintenance** — guarded cleanup, backup validation, migration, and recovery.
3. **Research operations** — source discovery, primary-source filtering, digest construction, and update detection.
4. **Career operations** — multi-source screening, constraint checks, approval queues, and tailored artifacts.
5. **Benchmark operations** — trace ingestion, score reconciliation, disclosure, uncertainty, and publication.
6. **Cyber defense** — detection, containment, recovery, and governance.

## Expansion axes

- **Entity:** account, repository, post, job, file, incident, vendor, or patient.
- **Policy:** threshold, approval authority, protected resource, SLA, retention rule, or disclosure requirement.
- **Evidence:** authoritative record, stale reference, conflicting source, incomplete source, or provenance tier.
- **Dynamics:** transient outage, reordered results, interruption, new constraint, failed deployment, or stale identifier.
- **Composition:** one workspace, dependent read-only reference workspace, or persistent multi-round state.
- **Difficulty:** system count, dependency length, distractor density, ambiguity, and policy interaction.

Regenerate the catalog with `PYTHONPATH=src python3 -m opsgym.cli --export-catalog website/data/catalog.json`.
