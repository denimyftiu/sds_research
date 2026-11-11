# Database-access SAST research lab (work in progress)

For a shareable progress update, open [Topic B presentation](topic_b/presentation/PROGRESS.md) and [team structure and handoffs](TEAM_GUIDE.md). The presentation includes a frozen synthetic evidence extract.

The assignment is in [research.txt](research.txt). Work proceeds **A → B → C**; B is the main deliverable. B covers Python and JavaScript as requested. TypeScript candidates may be screened separately; they are not automatically an additional included language.

- [A: benchmark/tool setup](topic_a/README.md): 16 labelled pilot cases in two languages; pinned scanner versions; scoring harness. Tool selection is provisional.
- [B: empirical-study WIP](topic_b/README.md): classification candidates, snapshot-fetch workflow, normalized findings, reproducible review sample, and candidate density report. Only synthetic fixtures have been processed so far.
- [C: workflow handoff](topic_c/README.md): initial policy illustration and a protocol for later replay work.

## Run in Docker

Requirements: Docker Engine with a reachable daemon, Compose, and internet during image build and project fetching. No database server is needed: this study statically inspects code without running applications or installing their dependencies.

```bash
# Linux: match artifact ownership to your account
export LAB_UID=$(id -u) LAB_GID=$(id -g)
make build
make test
make a
make b
make c
```

These commands execute in order. `make b` uses **synthetic smoke fixtures**, not open-source project observations. Output goes under `artifacts/`. The analysis container has networking disabled; the separate `fetch` service allows GitHub fetching. Both use the same image. Targets' source is never imported or executed. Only use trusted files for the harness itself.

Each `make b` creates a fresh directory under `artifacts/b/runs/`, preserving earlier inventories and reviews. `artifacts/b/latest.json` points to the latest completed run; `make c` reads that pointer. Individual inventory/review commands still refuse replacement to protect edits. See [B's guide](topic_b/README.md). Scanner JSON is regenerated when its scan command runs; archive completed experiment directories before rerunning them.

## Reproducibility boundary

The Dockerfile pins Python's base-image tag, Semgrep 1.185.0, Opengrep 1.33.1, and Bandit 1.9.4. The amd64 Opengrep release asset is checksum-verified. Local custom rules are tracked and hashed in scan provenance; scanning does not fetch changing registry rule packs. Each scan records tool versions, commands, source hashes, elapsed scanner time and the build's Python package inventory.

**Build reproducibility is not yet bit-for-bit locked:** the base tag, apt repositories and transitive pip dependencies can change. Before collecting study data, build successfully, archive the image (`docker image save`), record its image ID/base digest (`docker image inspect`), and freeze a hash-locked dependency file or use that archived image for every run. Source snapshots require full commit SHAs. This is a bootstrap environment, not a completed archival release.

## Verified in the preparation session

- Local standard-library tests: 10 passed; see `STATUS.md` for final checks.
- Compose configuration parses.
- B's synthetic inventory runs without third-party packages.
- Docker execution **blocked**: daemon socket permission denied. Shell DNS access also failed. No image build, scanner run, fetched project, benchmark performance result or container test is claimed.

For development only, the dependency-free harness tests can run with `python3 shared/lab.py test`. Study commands should run via Compose. See [STATUS.md](STATUS.md) for the current handoff.
