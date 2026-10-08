# Whole-match preparation and the first reviewed suite

This stage prepares the Aco77 versus sdesowitz02 Duelingbook match for evaluation.
It does not run GPT-6.1 Sol or publish a model score. The user requested coverage
of the whole match, expanding the earlier small-subset preparation request.

## Stored result

The [dataset manifest](../benchmarks/review/db-json-40753-85958923/manifest.json)
binds the native source digest, rules/assets, scope and review counts.

| Coverage | Result |
| --- | --- |
| Native timeline | All 554 entries, both games |
| Decision review work items | 207 |
| Filtered player packet drafts | 189 |
| Approved scoped checkpoints | 4 |
| Pending review work items | 185 |
| Excluded work items | 18 |
| Scoring suite | 8 tasks: 4 state recreation and 4 human choices |
| Legality denominator for a completed pilot | 8 attempts, independently graded |
| Model attempts / measured score | None |

The [timeline](../benchmarks/review/db-json-40753-85958923/timeline.json) accounts
for every source entry. The [review index](../benchmarks/review/db-json-40753-85958923/review-index.json)
includes all original 174 candidates plus 33 supplementary work items: first-player
selection, numeric Reasoning declarations, effect targets, card-return/search/cost
observations, battle-position changes and concessions. These are review boundaries,
not a claim that all 207 are independent strategic choices. Source references
remain exact; response windows omitted by the recording cannot be manufactured.
Fifteen automatic turn starts, two concessions and one post-concession activation
are excluded from this action-initiation suite. Supporting events, including chat,
remain linked through the timeline and original bundle.

Every non-excluded work item has a separate player packet under
`benchmarks/review/db-json-40753-85958923/player-packets/`. Pending packets have
`runnable: false`. Their `unreviewed_observation` window and context-limit notice
explicitly mark missing bookkeeping; empty chain/effect arrays in these drafts
are scaffolding, not certification that no chain or effect existed. The loader
rejects them for evaluation. Do not send drafts to a model as approved positions.

## What was reviewed and approved

Four successive setting actions in the second game's opening Main Phase are
simple enough to assess without resolving an unknown deck or a historically
errata-sensitive effect. Approval covers these **fixed, independently reset
checkpoints**, not the whole game, complete deck legality or optimal play.

| Source index (zero-based) | Sequence | Replay time | Recorded human decision |
| --- | --- | --- | --- |
| 333 | 334 | 15:31 | Set D.D. Warrior Lady in M-3 |
| 334 | 335 | 15:32 | Set Mirror Force in S-3 |
| 335 | 336 | 15:34 | Set Dark Bribe in S-4 |
| 336 | 337 | 15:48 | Set Soul Exchange in S-2 |

The private opening logs identify Aco77's five cards; the subsequent private
draw identifies Soul Exchange. Previous set logs establish the field and remaining
hand at each boundary. LP is consistently 8000. There is no prior activation,
trigger or battle in game 2 at these checkpoints. D.D. Warrior Lady is a Level 4
monster, the Normal Summon/Set allowance is initially unused, and the recorded
slots are empty. Its Normal Set consumes the allowance. The three subsequent
Spell/Trap sets do not consume another Normal Summon or activate their effects.

The named review is a **Codex evaluator preparation review**, not approval from
an external human expert. The reference moves are the recorded human choices;
we do not certify the players' expertise or that these choices are optimal.
The four positions are correlated and very small; report those limits with scores.

[The suite](../benchmarks/review/db-json-40753-85958923/suite.json) satisfies the
existing three-KPI scorer contract. Each checkpoint supplies two tasks:

- **State recreation:** execute the declared setting play into its requested
  slot, consume the Normal Set allowance where needed, preserve all other state
  and stop with the opponent's `after_set` response decision. This response-window
  endpoint is an explicit harness task convention; the replay does not record
  all passes. Reference patches are not supplied to the evaluated orchestrator.
- **Human agreement:** choose a next action from the filtered checkpoint without
  being told the human reference. Compare action kind, card, zone type and Defense
  Position for a monster Set. Ignore wording and interchangeable field slots for
  this pilot; state recreation still tests the specifically requested slot.
- **Legality:** independently review each attempted action. Different legal choices
  can fail human agreement and pass legality. Runtime acceptance alone earns no
  legality credit. Leave historical-text-dependent or unavailable-information
  alternatives pending rather than guessing.

## Information and asset boundaries

The evaluator-only [grading file](../benchmarks/review/db-json-40753-85958923/evaluator.json)
contains recorded operations and, for the four approved positions, reference
checkpoint fixtures, expected set states and rubrics. It is not a runtime game
save or an action journal. Public player packets are built with the harness's
`DuelRunner.context` filtering/compaction and validated with its isolated request
validator. Opponent hands, face-down identities, future draws, future actions and
grading keys are absent. Card descriptions include only cards visible to that
player; the full catalog is evaluator data. No recommendations reveal the answer.
Only `player_context` goes to a tool-free model transport; publishing evaluator
fixtures in the repository does not authorize giving models repository access.

Unobserved Deck/Extra/Side identities are **anonymous count carriers** in author
checkpoint fixtures. They assert neither card identity nor real shuffle order.
Case-local hand copy IDs do not claim to resolve replay shuffle lineage; known
field/pile references remain literal. These placeholders are unchanged in approved
set tasks. Stop before drawing, searching, selecting unknown Extra Deck cards or
resolving effects requiring those identities. This is a scoped checkpoint pilot,
not fully reconstructed decks or an uninterrupted duel simulation.

Rules and the dated banlist are copied from harness commit
`d3f5a4193cdc81dea033742f9c639b63f21427eb`, with the Perfect Circle profile taking
precedence over shared basics. Exact source hashes are in the manifest. The
current YGOPRODeck metadata snapshot supplies card texts. Complete historical
text overrides remain deferred as requested. The reference setting actions do not
use those disputed effects; broader legality remains provisional.

## Run and score these cases

Use the [harness setup](harness-integration.md) and import its `harness` package.
The reviewer loader provides approved inputs to the trusted evaluator:

```python
from yugioh_benchmark.review_cases import load_reviewed_case

bridge, initial_state = load_reviewed_case(
    "benchmarks/review/db-json-40753-85958923",
    "db-json-40753-85958923-before-000334-choice",
)
```

For a human-choice task, use `harness_bridge.run_case(bridge, bounded_transport)`;
the bridge sends only the filtered context. It returns an intention, not a scored
execution. For a state task, load the corresponding `-state` case, reconstruct the
fixed checkpoint locally, and give the orchestrator the case's `declared_play`.
Use the normal sole-moderator harness workflow; do not execute expected-state
patches on behalf of the evaluated model. Keep evaluator answers separate.
Independent graders normalize decisions and assess legality. Collect the
journals/results and provenance described in [agentic KPIs](agentic-kpis.md).
The four checkpoints must reset between tasks; later human labels do not apply
after a different model move.

Then score the trusted local run artifact:

```sh
yugioh-benchmark score-kpis benchmarks/review/db-json-40753-85958923/suite.json runs/pilot.json
```

A model/provider transport and actual agent workflow execution are still required.
This preparation does not claim they have run or automate checkpoint installation.
Keep live checkpoints, journals and model logs outside Git.

## Reproduce or continue preparation

From the installed benchmark checkout, with the pinned harness available:

```sh
PYTHONPATH=../yugioh-harness python scripts/prepare_replay_review.py
PYTHONPATH=../yugioh-harness python -m unittest discover -s tests -p test_review_cases.py -v
```

On PowerShell, set `$env:PYTHONPATH = "../yugioh-harness"` first. Generation is offline
and reconstructs the selected fixtures from the pinned source and checked-in
asset snapshots. It deliberately reproduces only the four explicit approval
records; it does not automatically approve arbitrary candidates. Source replay
fixtures, native bundle and extraction summary are unchanged.

For each remaining work item, resolve its listed blockers, verify actual response
and effect boundaries, establish only the missing facts it needs, and add a reviewed
case with its filtered input and separate grading key. Document additional source
information or exclusions. Source index 313's ownership conflict remains open;
affected later game-1 positions carry that blocker. The whole match is prepared
for review, but has not been certified as 207 runnable benchmark decisions.
