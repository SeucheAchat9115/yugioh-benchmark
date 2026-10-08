# Yu-Gi-Oh Benchmark

Duelingbook replay sources and reviewed decision benchmarks for testing how
well an LLM plays Yu-Gi-Oh through
[yugioh-harness](https://github.com/SeucheAchat9115/yugioh-harness).
The agent interprets card rules and chooses moves; this repository does not
implement a card-effects engine.

**Status: alpha toolkit.** Replay importing, reviewed-case execution and the
three-KPI artifact scorer are implemented. A [first scoped replay suite](docs/replay-review-stage.md) is prepared; a
complete three-KPI model evaluation remains pending. A [small Edison pilot](docs/edison-pilot.md)
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
A high task score alone does not establish competitive playing strength.

## Replay dataset and importing

The selected [Aco77 vs sdesowitz02 replay](https://www.duelingbook.com/replay?id=40753-85958923)
now uses the [supplied native JSON](fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.json)
and [native bundle](replays/db-json-40753-85958923) as its primary source:
**554 source plays, two games, 174 review candidates**. It adds private draw
observations for both players, card definitions, shuffle references and absolute
LP updates. The [source registry](benchmarks/sources.json) links the JSON fixture,
bundle, hashes, card references and review candidates. Its identity is
`db-json-40753-85958923`.

The [whole-match review stage](docs/replay-review-stage.md) indexes 207 work
items across both games. Four simple setting checkpoints are approved for a
small eight-task suite; the other positions remain pending or excluded.
**No model score has been measured on this suite.** The user identifies this
match as **Perfect Circle 2007**. The registry links the September 2007 format
reference; its exact card pool, historical rules and pre-errata texts still need
review. The export itself labels the game Unlimited.

For each new match, open the browser inspector’s **Network → Fetch/XHR** tab,
reload the replay and copy the complete **`view-replay` JSON response** to a file.
Supply the replay URL and played format alongside it. Follow the
[step-by-step acquisition guide](docs/acquisition.md), including its coverage
checks. HTML exports and copied duel text are unsupported.

Importing runs offline without runtime dependencies, browser setup or credentials.
Each native play has a numbered, hashed event file and its original source index.
Unknown cards, missing timestamps and manual operations remain available for review.

An orchestrator can import files internally in response to a natural language
request. Duel players do not need to run Python themselves. Maintainer commands:

```sh
git clone https://github.com/SeucheAchat9115/yugioh-benchmark.git
cd yugioh-benchmark
python -m pip install .
yugioh-benchmark convert-json imports/replay.json --source https://www.duelingbook.com/replay?id=40753-85958923 --output replays/my-native-match
yugioh-benchmark inspect replays/db-json-40753-85958923
# Reconstruct reviewer-only observations; these are not scored cases:
yugioh-benchmark extract replays/db-json-40753-85958923 --output inspection/db-json-40753-85958923
# Score a reviewed suite and its trusted run artifacts:
yugioh-benchmark score-kpis suite.json run.json
python -m unittest discover -s tests -v
```

[Offline CI](.github/workflows/ci.yml) tests Python 3.11–3.13 on Linux and Windows and
checks the filtered benchmark bridge against the pinned harness.
Replay conversion and human-move/legality artifact scoring do not require the harness.
State-recreation KPI scoring requires the harness to verify journals. Running
an agent through the bridge requires a separate harness checkout and your own
bounded model transport; see [harness setup](docs/harness-integration.md).

- [Supplying replay data](docs/acquisition.md)
- [Current card names and texts from YGOPRODeck](docs/card-metadata.md)
- [Native JSON importing and coverage](docs/native-json.md)
- [Whole-match review and the first scoped suite](docs/replay-review-stage.md)
- [Extracting states and preparing reviewed cases](docs/extraction.md)
- [Replay bundle format](docs/replay-format.md)
- [Preparing harness decision positions](docs/harness-integration.md)
- [Agentic workflow KPIs and scoring](docs/agentic-kpis.md)
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
