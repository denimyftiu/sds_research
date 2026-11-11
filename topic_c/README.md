# C — initial handoff after A and B

C has been started only as a policy interface and replay plan. `make c` applies three illustrative policies to B's latest completed pilot finding file (located through `artifacts/b/latest.json`) and writes `artifacts/c/policies.json`. It does not run CI, measure fix time or replay commits. Do not interpret this as an evaluated gate policy.

Planned inputs from A: frozen tool versions/rules and severity calibration. Planned inputs from B: audited true/false/uncertain labels, tool/style metadata, measured triage effort and (where actually observed) fix time. Bandit severities and Semgrep ERROR/WARNING/INFO are different scales. The current high policy's ERROR→HIGH mapping is illustrative only and must be calibrated before any comparison.

Next work, after B has real reviewed data:

1. Choose at least three eligible projects and pin the same commit sequences for every policy. Target 200 commits for the bonus, recording whether this means aggregate or per-project with the course supervisor. Keep seeded changes separate from real histories.
2. Author GitHub Actions or GitLab pipelines using the frozen images. Compare baseline CI and SAST jobs on the same runner class; capture checkout/setup/scan/total time, CPU/memory, exit states and image-cache conditions.
3. Evaluate block-on-any, block-on-high, and report-only on identical findings. A scanner crash is an infrastructure error, not a clean build. Persist per-commit/tool/policy data; do not use one aggregate scan to claim a replay result.
4. Join independently reviewed alerts to estimate false-alarm cost with sample uncertainty. Measure actual triage/fix time where observed; estimates from B must be labelled estimates. Report blocked builds, surviving issues, costs and limitations.

No CI workflow is published yet: the target projects, runner environment and definitive tool pair have not been selected.
