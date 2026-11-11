# Preparation status — 2026-11-11

Requested scope: A just sufficient to bootstrap B; B work in progress; C started afterward. Python and JavaScript selected by the user.

## Completed preparation

- Separate `topic_a/`, `topic_b/`, `topic_c/` folders and dependency/handoff documentation.
- A: 16 labelled static snippets; three scanner candidates pinned; local pilot rules; scoring/provenance/error handling.
- B: synthetic two-language fixture; unchecked 20-entry screening pool; empty lock to prevent accidental inclusion; pinned-snapshot fetcher; candidate inventory; finding mapping; seeded, overwrite-protected review queue; descriptive candidate density report.
- C: initial three-policy illustration and a deferred replay protocol.
- Local checks: 10 standard-library tests passed, Compose configuration validated, synthetic inventory generated (6 pending candidate points).

## Not yet validated or completed

Docker client and Compose are installed, but daemon access in this session fails with `permission denied` on `/var/run/docker.sock`. Shell network access also fails DNS resolution. Browser research could verify upstream documentation and version references, but could not build containers or fetch repositories into the workspace. No permission change was attempted.

**No container was built or run, and no scanner result exists.** The scanners' CLI/rule compatibility is therefore unverified. The dependency lock is not complete (see root README). Synthetic inventory execution and unit tests ran locally only.

No real project is pinned/fetched, no access point manually audited, no finding manually reviewed, no statistical inference performed, and no best-tool claim established. A's 60-case/default+tuned requirement and B/C bonus scales remain future work. This is an honest pilot scaffold and B WIP, not a completed study.

## Next concrete action

Make the Docker daemon reachable from the working session, then run `make build`, `make test`, `make a`, `make b`, `make c`. Fix any scanner/image compatibility failures before collecting data. Complete A's selection evidence and screen/freeze B's cohort before final results. The Docker socket was owned by `nobody:nogroup`, mode `0660`; the process listed membership in `nogroup` but access still failed, so installation alone does not resolve the session's access restriction.

## Direct Docker CLI retry

On the user's instruction to proceed with Docker commands, attempted `docker compose build lab`. Buildx first failed writing under the read-only `/home/d3ni/.docker/buildx/activity` directory. Retried with `DOCKER_CONFIG=/tmp/sds-docker-config BUILDX_CONFIG=/tmp/sds-docker-buildx`; the build then failed with Docker's own daemon-access `permission denied` error. A direct `docker run --rm hello-world` also failed with the same error. These were actual build/run attempts, not socket probes. Container execution remains blocked by the session environment.

## User-run container feedback and CLI fix

The user successfully built/started the container outside this agent session. The saved A run confirms Semgrep 1.185.0 and Bandit 1.9.4 completed valid scans. Opengrep failed because its native CLI rejects `--metrics=off`; this Semgrep-only flag has now been removed from Opengrep's command. The remaining scan flags were checked against the pinned release's source: https://raw.githubusercontent.com/opengrep/opengrep/v1.33.1/src/osemgrep/cli_scan/Scan_CLI.ml . Failure provenance now preserves the exit code, command, version and stderr even when stdout is not JSON, and displays diagnostics directly. Local regression suite: 11 passed. A successful full three-tool rerun is still pending; no scoring result is claimed yet. The fix is in bind-mounted source and does not require rebuilding the image.


## A completed; repeatable B command fix

The user's rerun completed all A scans and scoring. Saved pilot scores: Semgrep/Opengrep each 7 TP, 1 FP, 7 TN, 1 FN on 16 cases; Bandit 3 TP, 0 FP, 4 TN, 1 FN on the 8 Python cases. These are pilot-profile results, not a final tool ranking.

`make b` initially stopped on the earlier locally generated inventory, as the no-overwrite guard intended. The default command now creates a fresh isolated run under `artifacts/b/runs/`, publishes `latest.json` only after successful completion, and preserves all previous review/inventory files. `make c` follows this pointer. Local suite: 12 tests passed, including repeat runs, preservation of human review data, and retention of the last successful pointer after a failed scan. Full B container run remains pending the user's retry. No image rebuild is required.


## B publication path fix

The user's B container run completed inventory, all three scans, normalization, sampling and reporting in `artifacts/b/runs/pilot-m_18yke3`, but failed publishing `latest.json`: Python 3.12 returned an absolute temporary directory while the output root remained relative. The harness now resolves the root before creating the run directory. A regression test simulates absolute temporary-directory returns with a relative root and verifies pointer publication and C consumption. All 13 local tests pass; a container rerun of the fix remains pending. The existing run artifacts are preserved. No image rebuild is required.


## Pilot completed and report aggregation corrected

The user completed B and C. Latest B run `pilot-rbq2l5l9` has six pending access candidates, five normalized alerts, and five unreviewed queue entries. C processed five alerts. A's provisional benchmark metrics remain as recorded above. No real project has been pinned yet.

Output inspection found that report density grouped by project/style but omitted the per-tool filter. Fixed this and added a regression test; 14 local tests pass. Generated `report.corrected.json` beside the latest original report using the dependency-free local harness; original container output is preserved. Future container runs use the corrected implementation.


## Shareable Topic B progress material

Added `topic_b/presentation/PROGRESS.md`: seven-part progress presentation with verified synthetic counts, corrected per-tool density table, speaker notes, limitations and a Docker demo. Added a tracked evidence extract with checksum manifest so teams can share it despite `artifacts/` being ignored. Added `TEAM_GUIDE.md` explaining folder ownership, shared infrastructure, CSV joins, handoffs and the next real-project checkpoint. Presentation checks verify counts, tool-specific alerts, manifest checksums and relative document links; no new empirical data or manual review labels were created.
