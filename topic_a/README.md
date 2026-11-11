# A — minimum pilot foundation for B

## Implemented

`benchmark/` contains **16 labelled cases (8 safe/unsafe pairs)**: DB-API execute, Django raw/extra, SQLAlchemy text, Sequelize query, Knex raw/whereRaw, and JavaScript concatenation/template strings. `labels.json` states the assumed untrusted input and case ranges. The examples are static fragments; no endpoints or database instances are executed. They establish CWE-89 ground truth under the stated API semantics, not deployable exploit demonstrations.

`make a` scans with three pinned candidates and scores case-level TP/FP/TN/FN, precision, recall and lists of misses/false alarms. Multiple alerts on one case count once. Missing/failed scan results stop scoring; unsupported Bandit JavaScript cases are excluded, not treated as misses or successes.

| Tool | Pilot scope | Configuration |
|---|---|---|
| Semgrep CE 1.185.0 | Python, JavaScript | Local `rules/pilot.json` |
| Opengrep 1.33.1 | Python, JavaScript | Same local rules |
| Bandit 1.9.4 | Python only | Explicit B608 selection, all confidence/severity levels |

These are **pilot profiles**, not vendor defaults or a completed default-versus-tuned experiment. The local rules are deliberately narrow syntax heuristics and can produce false positives and miss taint flows. They have not been executed by scanners in this environment. Semgrep and Opengrep share ancestry and rules, so agreement is not independent corroboration. Bandit is an independent Python baseline but cannot be one of B's two full cross-language tools.

## Decision carried into B

Semgrep and Opengrep are **provisional integration candidates**, not empirically “the two best tools.” B can exercise the input/output workflow now. Its definitive scanning configuration is blocked on A's expanded evaluation and a documented selection decision. Reconsider whether two related engines provide a defensible comparison; evaluate an independent cross-language candidate before freezing the final study if feasible.

For A's full/bonus study, expand to at least 60 cases across both languages, including safe ORM/query-builder examples, aliases, multiline and interprocedural flows, sanitizer/allowlist controls and harder negatives. Freeze development versus held-out cases before tuning. Add default and tuned rule snapshots, per-language and per-pattern results, pairwise agreement/union metrics and a manually checked pattern catalogue. Select tools on held-out recall/precision and language coverage, with a stated tradeoff rule; do not rank on this tiny development fixture.

## Sources used to prepare the environment

Checked 2026-11-11. These support installation and tool behavior, not any empirical result:

- [Semgrep CLI reference](https://docs.semgrep.dev/cli-reference): local configuration, JSON output and exit status options.
- [Semgrep 1.185.0 on PyPI](https://pypi.org/project/semgrep/1.185.0/).
- [Opengrep v1.33.1 release](https://github.com/opengrep/opengrep/releases/tag/v1.33.1), [release assets and checksums](https://github.com/opengrep/opengrep/releases/expanded_assets/v1.33.1).
- [Bandit 1.9.4 on PyPI](https://pypi.org/project/bandit/1.9.4/), [B608 documented SQL-string heuristics](https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html).
