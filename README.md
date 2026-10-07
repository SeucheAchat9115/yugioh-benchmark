# Yu-Gi-Oh Benchmark

Replay sources and reviewed decision benchmarks for testing how well an LLM
plays Yu-Gi-Oh through [yugioh-harness](https://github.com/SeucheAchat9115/yugioh-harness).
The agent interprets card rules and chooses moves; this repository does not
implement a card-effects engine.

The first real import is [Noxjja vs Drew Carter](https://www.duelingbook.com/replay?id=2178594),
a 2017 Advanced-format match: **962 source events, three games**. Its public
archived JSON was converted into [replays/db-2178594](replays/db-2178594).
See [provenance](replays/db-2178594/provenance.json) and [third-party notices](THIRD_PARTY_NOTICES.md).
The archive supplies card data and simulator operations. Legality, historical
rules, hidden-state completeness and decision boundaries remain unreviewed.
There are currently **no scored decision cases**; importing a replay does not
create a validated benchmark automatically.

An orchestrator can import and inspect files internally in response to a natural
language request. Duel players do not need to run Python themselves. These are
maintainer commands:

```sh
python -m pip install .
yugioh-benchmark convert imports/replay.json --source 2178594 --output replays/db-2178594-new
yugioh-benchmark inspect replays/db-2178594
python -m unittest discover -s tests -v
```

Conversion accepts a DuelingBook `/view-replay` response JSON or a browser HAR
with exactly one matching successful response. It works offline with no runtime
dependencies. Each event has its own numbered file; the manifest indexes their
paths and hashes. Source operations and card identifiers are preserved without
inventing missing moves. Unknown operation labels remain available for review.

[Offline CI](.github/workflows/ci.yml) tests the package on Windows with Python
3.11–3.13. Live capture is a separate, explicitly triggered integration workflow
with a 45-second capture deadline. DuelingBook currently requires browser
verification: direct requests return “Missing token”, and verification did not
complete in the hosted browser. The included match was obtained from a public
archive instead. There are no endless retries or fabricated tokens.

- [Replay JSON format](docs/replay-format.md)
- [How to save replay JSON (desktop and mobile)](docs/acquisition.md)
- [Preparing and running harness benchmarks](docs/harness-integration.md)

Raw imports/HARs and evaluation runs stay local and ignored. Deliberately selected
source fixtures and reviewed cases may be versioned. Harness game saves belong
in the harness's local storage.
