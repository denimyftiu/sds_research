# Repository structure and team handoffs

This repository shares one Docker environment and one analysis harness across three related topics. B is the current focus. A has pilot benchmark infrastructure; C has an initial policy illustration. Neither A's full evaluation nor C's real CI replay is complete.

## Where things live

```text
sds_assignment/
├── research.txt                   Original assignment; common scope reference
├── README.md                      Setup, commands and reproducibility limits
├── STATUS.md                      Dated progress and fixes; latest entries supersede old status
├── TEAM_GUIDE.md                  This guide
├── Dockerfile                     Common pinned scanner/bootstrap image
├── compose.yaml                   Offline lab service; network-enabled fetch service
├── Makefile                       build, test, a, b, c entry points
├── shared/
│   └── lab.py                     Shared CLI: scan, classify, score, map, sample, report, fetch
├── tests/
│   └── test_lab.py                Regression checks for scoring and data handling
├── topic_a/
│   ├── README.md                  A's scope, limitations and tool-selection work
│   ├── benchmark/                 Labelled Python/JavaScript static snippets
│   ├── labels.json                Case IDs, ground truth and expected case ranges
│   └── rules/pilot.json           Local pilot rules used by Semgrep and Opengrep
├── topic_b/
│   ├── README.md                  B protocol, manual-review requirements and commands
│   ├── data/candidates.json       Unchecked screening pool; not the included cohort
│   ├── data/projects.lock.json    Included snapshots; currently empty
│   ├── pilot/                     Synthetic Python/JavaScript smoke fixtures
│   └── presentation/
│       ├── PROGRESS.md            Ready-to-present B progress outline and speaker notes
│       └── evidence/              Frozen pilot CSV/JSON files and provenance note
├── topic_c/
│   └── README.md                  Gate illustration and future commit-replay plan
└── artifacts/                     Generated runs and fetched sources; ignored by Git
    ├── a/scans/ and a/scores.json
    ├── b/latest.json              Pointer to most recent successful B run
    ├── b/runs/pilot-*/            Separate inventories, scans, findings, reviews, reports
    └── c/policies.json            Illustrative policy outcomes
```

Python and JavaScript subfolders in `topic_b/pilot/` are language fixtures, not two sampled projects. The current report's `project` values `python` and `javascript` are synthetic grouping labels only.

## Ownership

| Area | Primary owner | Coordination rule |
|---|---|---|
| `research.txt` | All teams / course scope | Agree scope changes together |
| `topic_a/` | Team A | Publish versions, rules, evaluation evidence and selection rationale |
| `topic_b/` | Team B | Own cohort decisions, snapshots, access audits, reviews and comparative analysis |
| `topic_c/` | Team C | Own CI/replay design, measured costs and gate comparisons |
| `shared/`, Docker files, Makefile, tests | Shared infrastructure | Notify all teams before changing CLI/schema/tool behavior; run regression checks |
| `artifacts/` | Producing team | Preserve source commit, rule hash and run metadata; do not edit raw scan JSON |

B currently reads A's local pilot rules directly. A rule change therefore changes B's experiment. Freeze an agreed rule snapshot/image for a data-collection batch instead of silently rerunning against changing rules. Benchmark ground truth belongs to A; B's manual review labels are separate empirical data.

## Data contracts between teams

### A → B and C: scanner release

Agree a versioned release containing scanner versions/image identity, default/tuned rule snapshots and hashes, supported languages, benchmark metrics, known blind spots, and a reasoned selection of two tools. The current `scores.json` is only a development pilot. Bandit is Python-only, and the two cross-language candidates are related engines.

### B's internal files

| File | Key fields | Meaning and current limits |
|---|---|---|
| `projects.lock.json` | `id`, repository URL, language, full commit SHA | Only screened, included projects belong here; currently empty |
| `access_points.csv` | `id`, project/path/language, line range, callee, `candidate_style`, `reviewed_style`, `review_status` | Script candidates; reviewed style starts blank |
| `*.coverage.json` | File count, parse failures, coverage limitations | Helps identify gaps; does not certify a complete manual audit |
| `scans/run.json` | Tool versions, commands, validity, elapsed seconds, rules/source hashes | Provenance and failure status; scanner time is not CI overhead |
| `findings.csv` | Alert `id`, tool/profile, location/rule/severity, `access_id`, style and match status | Tool alerts, not confirmed vulnerabilities |
| `review.csv` | Alert fields plus verdict/reviewer/evidence/triage/fix minutes | Human work; unreviewed and empty time fields must remain missing |
| `report.json` | Project/style counts and per-tool candidate densities | Descriptive pilot output; currently does not consume adjudicated labels |

Within a run, `findings.access_id` joins to `access_points.id`, and `review.id` joins to `findings.id`. Preserve the project snapshot and rule identity alongside these IDs when sharing across runs. An ID alone does not encode a commit. Cross-tool alerts on one access point remain separate for per-tool analysis.

Use review verdicts `true_problem`, `false_alarm`, `uncertain`; initial `unreviewed` means no review decision. An audited access point needs a reviewed style, a consistent reviewed status, and audit evidence in a separate log. Scripts do not currently import that audit log into a final validated statistical report.

### B → C: reviewed empirical data

Supply reviewed alerts with snapshot/tool/style context, evidence and actual recorded effort. Describe the sampling design and unresolved cases. C must distinguish observed times from estimates and account for B's sampling uncertainty. B does not yet have real-project reviews or effort measurements to hand off.

C's current `policies.json` applies three illustrative decisions to one synthetic finding set. It is not a replay dataset. Severity calibration between tools remains unresolved.

## Sharing and reproduction

1. Share the repository source, including `topic_b/presentation/`, through the team's chosen source-control process. No push, message or publication has been performed automatically.
2. Do not assume `artifacts/` travels with Git: it is deliberately ignored. Share a named immutable artifact bundle separately for each real experiment, including raw scans, metadata, snapshot lock, scope/exclusion records and reviewed CSVs. Record a checksum manifest for that bundle.
3. Keep human review data outside destructive rerun paths. `make b` creates a new run and changes `latest.json` only after success. Individual inventory/review commands refuse to overwrite existing files.
4. For a fresh machine, build with `make build`; then run `make test`, `make a`, `make b`, `make c`. Linux users should export their UID/GID as explained in the root README. Docker is needed to execute scanners; application dependencies and database servers are not needed for static scanning.
5. Before real data collection, archive/freeze the working image. Scanner pins and source hashes exist, but the current Docker build is not fully hash-locked for its base/transitive dependencies.

## Next shared checkpoint

Team A: agree the provisional tool/profile release and identify what evidence is still needed for final selection.

Team B: screen and pin one Python and one JavaScript SQL-using application; audit both; review their findings; document gaps before expanding to at least 20 projects.

Team C: agree the review/effort fields it needs from B and the future replay protocol. Real CI policy conclusions wait for measured runs.
