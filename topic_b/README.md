# B — raw SQL, query builders and ORMs (WIP)

Ready to present: [progress presentation and speaker notes](presentation/PROGRESS.md), with a shareable [evidence snapshot](presentation/evidence/README.md). See the root [team guide](../TEAM_GUIDE.md) for ownership and handoffs.

The primary deliverable studies Python and JavaScript. The current contribution is a reproducible **pilot workflow and study protocol**, not evidence about real-project vulnerabilities. `pilot/` is synthetic and must never be counted toward the project sample.

## Research protocol

**RQ1:** access-style distribution. Unit: a database operation at a source call site, not SQL strings, generated queries or physical lines. Raw SQL passed through an ORM is `raw`, not `orm`. A fluent operation is one point at its terminal database operation; nested `execute(text(...))` is one point. Define lazy ORM/query-builder evaluation sites consistently during the audit. Distinguish API-level candidate detection from verified database use.

**RQ2:** findings per 100 audited access points, grouped by tool, project, language and style. Also report the share of unique access points flagged; several alerts can map to one point. Keep duplicate cross-tool alerts for per-tool precision, but deduplicate them for combined analyses. Preserve unresolved and ambiguous mappings separately; never guess them into a style denominator. Separate scan failures, unsupported language coverage and zero findings.

**RQ3:** manually confirmed problems / reviewed findings, per tool and style, with uncertainty intervals and sample counts. Findings are not automatically vulnerabilities. Review data flow from untrusted source, query construction, binding/escaping/allowlists, receiver/library semantics and reachability; record file, line, snapshot and evidence. Verdicts: `true_problem`, `false_alarm`, `uncertain`. Record uncertain and nonreviewed separately; do not silently label them safe. Review ambiguous locations before sampling the final cohort.

### Cohort and scope (not yet frozen)

Target **at least 20 eligible SQL-using applications**, initially aiming for 10 Python and 10 JavaScript, with variation in framework and application size. `data/candidates.json` is a **screening pool only**, not an included cohort: it intentionally includes framework/library repositories and possibly unsuitable database/language choices. Replace unsuitable candidates. Do not infer that every candidate uses relational storage or is primarily in its suggested language. No candidate has been downloaded or eligibility-checked yet.

Include public repositories with a clear license, identifiable relational DB access, a reproducible commit and enough application source to audit. Exclude forks/duplicates, tutorial-only repos and MongoDB-only applications. Prefer applications over framework implementations; libraries in this pool are useful for API reconnaissance, not automatically part of the application cohort. Record reasons for inclusion/exclusion, license, framework/version, language composition, production source roots and snapshot date. Restrict JS/TS mixed repositories to documented JavaScript roots or agree an amended language protocol before including TypeScript. Freeze exclusions for tests, migrations, generated files and vendored code **before** counting; analyse sensitivity to scope where relevant.

A complete access-point inventory requires manual full-source audits: scripts miss aliases, wrapper functions, custom managers and dynamically constructed methods. Add missed points and remove non-DB candidates, keep an audit log and mark reviewed styles. Use a second reviewer on a subset if available, document disagreements and adjudication. Script output alone cannot establish “every access point classified.”

### Statistical analysis planned

Project/language/framework differences are confounders. Report per-project style counts and densities before pooling; prefer within-project comparisons for projects containing multiple styles. Treat projects as clusters, not individual alerts as independent replicates. Predefine a project-level paired comparison or cluster bootstrap, minimum group sizes, effect sizes and uncertainty. A Mann–Whitney test on project-level style densities is an optional unpaired sensitivity analysis, not a substitute for a paired design. Use chi-square/Fisher only where independence and expected-count assumptions are defensible. Report multiplicity handling and sampling weights for unequal strata. No p-values will be generated from synthetic fixtures or an unreviewed pilot.

Aim for at least 100 manually reviewed real-project findings, randomly stratified by validated style (and record tool/language/project representation). If fewer exist, report the actual count and limited power; do not seed findings into the empirical cohort to reach the quota.

## Run the synthetic workflow

From the root: `make build && make test && make a && make b`. `make b` creates a fresh `artifacts/b/runs/pilot-*/` directory each time and prints its path. Existing runs are preserved. `artifacts/b/latest.json` identifies the latest successfully completed run, which `make c` uses. A failed run is retained for diagnosis and does not change that pointer. Each run contains:

| Artifact | Meaning |
|---|---|
| `access_points.csv` | Candidate locations/styles; all initially pending review |
| `access_points.csv.coverage.json` | File count, Python parse failures and classification limitations |
| `scans/*.json`, `run.json` | Raw engine results, validity, timings and provenance |
| `findings.csv` | Normalized alerts, stable identifiers and location mapping status |
| `review.csv`, sampling metadata | Seeded sample, empty human verdict/evidence/time fields |
| `report.json` | Candidate density tables, explicitly not validated results |

Python candidates use AST call locations; JavaScript/TypeScript candidates use lexical matching and require substantially more manual checking, especially comments, multiline calls and fluent chains. Generic `query`, `filter`, `select` etc. may refer to non-database APIs. ORM versus query-builder meaning depends on receiver types. Initial `reviewed_style` is blank; the current report intentionally uses `candidate_style` only. Final analysis must consume an adjudicated inventory and reviews; review ingestion and inferential analysis remain TODO.

Sampling uses seed 20261111 and up to 34 findings per candidate style, retaining unmapped findings in an `unknown` stratum. This can fall short of 100, and an unknown stratum does not count toward a valid style quota. The final sample must be drawn again after mapping/classification review. Existing review/inventory files are never overwritten.

## Transition to real projects

1. Screen candidates and record eligibility decisions in a separate tracked table. Add eligible projects to `data/projects.lock.json` with `id`, `repository`, `language`, **full 40-character `commit` SHA**, scope and inclusion rationale. Do not use branches or floating tags. The empty lock currently prevents accidental candidate inclusion.
2. Fetch without executing target code:

   ```bash
   docker compose run --rm fetch fetch topic_b/data/projects.lock.json artifacts/sources
   ```

3. Use a fresh experiment directory and run:

   ```bash
   docker compose run --rm lab inventory artifacts/sources artifacts/real-v1/access_points.csv
   docker compose run --rm lab scan artifacts/sources artifacts/real-v1/scans
   docker compose run --rm lab normalize artifacts/sources artifacts/real-v1/scans artifacts/real-v1/access_points.csv artifacts/real-v1/findings.csv
   docker compose run --rm lab sample artifacts/real-v1/findings.csv artifacts/real-v1/review.csv
   docker compose run --rm lab report artifacts/real-v1/access_points.csv artifacts/real-v1/findings.csv artifacts/real-v1/report.json
   ```

4. Audit the inventory and joins, then resample to a new review file using frozen reviewed styles once that analysis step is implemented. Scanner rules and source hashes must remain identical across compared runs. Record exclusions and engine parse/timeout errors; a failed scan currently aborts normalization rather than supplying misleading zero counts.
5. Complete A's tool selection, review findings, implement the predeclared final statistical analysis, and write B's results. Pass triage/fix-time fields and confirmed/false-alarm labels to C; empty times are missing, never zero.

Do not cite the current synthetic six-point inventory as evidence for any research question.
