# Yu-Gi-Oh Benchmark

Duelingbook text replay sources and reviewed decision benchmarks for testing how
well an LLM plays Yu-Gi-Oh through
[yugioh-harness](https://github.com/SeucheAchat9115/yugioh-harness).
The agent interprets card rules and chooses moves; this repository does not
implement a card-effects engine.

**Status: alpha toolkit.** Text importing and reviewed-case execution are
implemented; the dataset currently contains no approved, scored decision cases.
This project is independent of Duelingbook and the Yu-Gi-Oh rights holders.

The selected [Aco77 vs sdesowitz02 replay](https://www.duelingbook.com/replay?id=40753-85958923)
is included as a [complete supplied text export](fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.txt)
and [converted bundle](replays/db-text-aco77-sdesowitz02-2026-10-07):
**565 observations, two games, 159 review candidates**. The
[benchmark source registry](benchmarks/sources.json) links the text, bundle,
payload digest and candidate index. Its identity is `db-40753-85958923`.

There are currently **no scored decision cases**. Imported observations are
unreviewed; positions, information visibility, historical rules and decision
boundaries must be checked before gameplay scoring.

Supply more matches as copied Duelingbook Chat/Duel/Game text, with each replay
URL when available. Importing works offline with no runtime dependencies or
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
yugioh-benchmark inspect replays/db-text-aco77-sdesowitz02-2026-10-07
python -m unittest discover -s tests -v
```

[Offline CI](.github/workflows/ci.yml) tests Python 3.11–3.13 on Linux and Windows and
checks the filtered benchmark bridge against the pinned harness.
Replay conversion and saved-result scoring do not require the harness. Running
an agent through the bridge requires a separate harness checkout and your own
bounded model transport; see [harness setup](docs/harness-integration.md).

- [Supplying text replays](docs/acquisition.md)
- [Replay bundle format](docs/replay-format.md)
- [Text importing and reviewed-suite scoring](docs/text-logs.md)
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
