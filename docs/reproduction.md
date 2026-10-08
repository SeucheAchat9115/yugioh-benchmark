# Recorded-operation reproduction

The benchmark imports `harness.runner.state_tools.build` and the harness's
real action/journal engine. It translates an observed operation into guarded
harness operations, executes it, compares the resulting state with an
independently constructed expected state, and verifies journal replay.

This tests backend execution of a supplied operation. It does not ask an AI to
choose a move. It also does not reconstruct or replay the complete duel.

These probes are regression checks for the harness adapter and journal engine.
They are separate from [the three agentic KPIs](agentic-kpis.md) and contribute
nothing to their final score, including the state-recreation KPI. That KPI tests
the agent interpreting a declared play; these probes supply the operations.

## Actual run on replay 40753-85958923

On 2026-10-08, the supplied replay was tested against public harness commit
`1d54835a8e239160f8e5dc4f01c8589506669ac0`. All 41 imported harness Python
modules were checked against that commit's Git blob hashes before the run.
Source payload SHA-256:
`ea5f2953dbc0111abd6a3da4b1f850a34b0149e3682b0681f5c50aec568b54a0`.

| Measure | Result |
| --- | --- |
| Source observations and headers | 565 |
| Excluded metadata/chat/viewing/headers/leave messages | 197 |
| Gameplay observations in coverage denominator | 368 |
| Reproduced with matching expected state and journal replay | 263 |
| Unsupported by this adapter/context | 105 |
| Executed but failed state/replay checks | 0 |
| Recorded-operation coverage | **263 / 368 = 71.5%** |
| Execution fidelity among executed probes | **263 / 263 = 100%** |
| Full-match accuracy | Not measured |
| AI move-choice accuracy | Not measured |

The denominator includes unsupported gameplay observations. It does not count
chat/viewing as successful moves. Coverage describes this replay and this
adapter; it is not an accuracy score for the harness's rule adjudication.

| Operation | Reproduced | Unsupported |
| --- | ---: | ---: |
| Draws | 44 | 0 |
| Phase changes | 55 | 0 |
| Card moves | 98 | 0 |
| Summons | 21 | 0 |
| Sets | 16 | 0 |
| Token/counter/stat/position observations | 15 | 7 |
| LP changes | 12 | 0 |
| Concessions | 2 | 0 |
| Activations/effect declarations | 0 | 43 |
| Attacks | 0 | 9 |
| Shuffles | 0 | 31 |
| End-turn observations | 0 | 15 |

The last groups need more context: verified chain/response/effect checkpoints,
battle checkpoints, observed shuffle results or complete end-turn checkpoints.
Seven pointing observations also lack their associated target/decision context.
The harness supports activation and battle records, but this adapter does not
invent their missing context just to report a successful execution.

## Scope of each probe

Each event starts from a fresh, minimal controlled state. A named card is given
its explicitly observed name; unnamed cards remain unnamed. Probe IDs are
synthetic fixture handles, not recovered physical-copy IDs. No card passcodes,
full decks, hidden hands, rule profiles or card effects are fabricated.
LP probes use a documented synthetic baseline rather than assuming the match's
starting LP. Five-slot fixtures support the observed zone labels, not a claimed
reconstruction of the historical rules.

For example, a recorded draw is tested with that single observed card at the top
of a synthetic deck, then checked in the hand. That verifies draw execution; it
does not prove the real game's earlier shuffle produced that card.
The test authorization flag is required by the engine and applies to these
isolated structural fixtures; it does not certify the original play's legality.
No probe is made into an approved gameplay benchmark case.

## Run it again

Install the benchmark package and use the public harness checkout described in
[harness integration](harness-integration.md). On Linux/macOS:

```sh
PYTHONPATH=../yugioh-harness yugioh-benchmark reproduce replays/db-text-aco77-sdesowitz02-2026-10-07 --output runs/reproduction.json
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "../yugioh-harness"
yugioh-benchmark reproduce replays/db-text-aco77-sdesowitz02-2026-10-07 --output runs/reproduction.json
```

The CLI prints the summary and writes a per-event report if requested. It refuses
to overwrite an existing report. Reports include the source digest, hashes of
the imported harness modules, exclusion/unsupported reasons and exact per-event
outcomes. Keep runs local in ignored `runs/`; no harness game saves are committed.
CI executes the same probes against the pinned public harness.

Measuring full-match reproduction needs reviewed initial state, card-copy
mapping, decks, rules and decision/effect checkpoints. Measuring AI move-choice
accuracy additionally needs a specified agent, filtered positions and accepted
answers. Follow [the agentic evaluation contract](agentic-kpis.md) for state
recreation, human-move agreement and independent rule-correctness grading.
