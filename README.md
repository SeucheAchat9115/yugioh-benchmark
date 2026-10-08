# Yu-Gi-Oh Benchmark

Duelingbook replay sources and reviewed decision benchmarks for testing how
well an LLM plays Yu-Gi-Oh through
[yugioh-harness](https://github.com/SeucheAchat9115/yugioh-harness).
The agent interprets card rules and chooses moves; this repository does not
implement a card-effects engine.

**Status: alpha toolkit.** Replay importing, reviewed-case execution and the
three-KPI artifact scorer are implemented. Reviewed replay cases and a
complete three-KPI evaluation remain pending. A [small Edison pilot](docs/edison-pilot.md)
measured state recreation and legality; human-move agreement and a final score
remain unavailable.
This project is independent of Duelingbook and the Yu-Gi-Oh rights holders.

## Agentic benchmark score

The benchmark evaluates an agent working through the harness, with three equally
weighted KPIs:

| KPI | What it measures | Weight |
| --- | --- | --- |
| State recreation | Does the agent orchestrate a player-declared play and produce the correct game state? | ⅓ |
| Human-move agreement | Does the agent choose the same semantic move as the reviewed human replay? | ⅓ |
| Rule correctness | Is the agent's play legal under the pinned format, banlist and card text? | ⅓ |

**Final score = the average of the three KPI percentages.** A different legal
move can pass rule correctness while failing human-move agreement. The selected
evaluation target is **GPT-6.1 Sol** (`gpt-6.1-sol`); see the
[evaluation configuration](benchmarks/evaluation-config.json).

Use the existing live harness workflow to collect attempts, authoritative
journals and independent grades. The [KPI scorer](docs/agentic-kpis.md) consumes
those artifacts; it does not launch a model or simulate a duel by itself.
Missing attempts score zero, while unfinished grading blocks a final score.
Neither the older exact-response scorer nor the **71.5% structural operation
coverage** is this final score. Even a high task score alone does not establish
competitive playing strength.

## Replay dataset and importing

The selected [Aco77 vs sdesowitz02 replay](https://www.duelingbook.com/replay?id=40753-85958923)
now uses the [supplied native JSON](fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.json)
and [native bundle](replays/db-json-40753-85958923) as its primary source:
**554 source plays, two games, 174 review candidates**. It adds private draw
observations for both players, card definitions, shuffle references and absolute
LP updates. The [original text](fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.txt)
and [text bundle](replays/db-text-aco77-sdesowitz02-2026-10-07) remain companions
with their original event numbers. The
[benchmark source registry](benchmarks/sources.json) links the sources, bundles,
payload digests and candidate indexes. The primary identity is
`db-json-40753-85958923`; the text companion remains `db-40753-85958923`.

There are currently **no scored decision cases**. Imported observations are
unreviewed; positions, information visibility, historical rules and decision
boundaries must be checked before gameplay scoring. This replay is labelled
Unlimited; its rules, banlist and card-text version remain unknown. Legality
evaluation needs cases with an established rules profile.

Prefer native `view-replay` JSON responses for additional matches; copied
Duelingbook Chat/Duel/Game text is also supported. Include the replay URL.
Importing works offline with no runtime dependencies or
browser setup. Each observation has a numbered event file; the manifest records
its path and hash. Original text and source-line references are preserved.
Unknown draws, set cards and operations remain available for review.

An orchestrator can import files internally in response to a natural language
request. Duel players do not need to run Python themselves. Maintainer commands:

```sh
git clone https://github.com/SeucheAchat9115/yugioh-benchmark.git
cd yugioh-benchmark
python -m pip install .
yugioh-benchmark convert-text imports/match.txt --source https://www.duelingbook.com/replay?id=40753-85958923 --output replays/my-match
yugioh-benchmark import-texts imports --output replays
yugioh-benchmark convert-json imports/replay.json --source https://www.duelingbook.com/replay?id=40753-85958923 --output replays/my-native-match
yugioh-benchmark inspect replays/db-json-40753-85958923
python -m unittest discover -s tests -v
```

[Offline CI](.github/workflows/ci.yml) tests Python 3.11–3.13 on Linux and Windows and
checks the filtered benchmark bridge against the pinned harness.
Replay conversion and saved exact-response scoring do not require the harness.
State-recreation KPI scoring requires the harness to verify journals. Running
an agent through the bridge requires a separate harness checkout and your own
bounded model transport; see [harness setup](docs/harness-integration.md).

- [Supplying replay data](docs/acquisition.md)
- [Native JSON importing and coverage](docs/native-json.md)
- [Replay bundle format](docs/replay-format.md)
- [Text importing and the separate exact-response scorer](docs/text-logs.md)
- [Preparing harness decision positions](docs/harness-integration.md)
- [Agentic workflow KPIs and scoring](docs/agentic-kpis.md)
- [Structural operation regression checks (separate from agent scores)](docs/reproduction.md)
- [Contributing](CONTRIBUTING.md)
- [Release notes and public release preparation](docs/releasing.md)

Raw imports and evaluation runs stay local and ignored. Deliberately selected
source fixtures and reviewed cases may be versioned. Harness game saves belong
in the harness's local storage.

The code and documentation use the [MIT license](LICENSE). Replay fixtures,
derived observations and candidate indexes are source data with separate
[attribution and rights information](THIRD_PARTY_NOTICES.md); they are not
relicensed under MIT. A replay URL records provenance, not a redistribution
license.
