# Agentic workflow evaluation

The intended evaluation measures the model working through yugioh-harness. The
selected target is GPT-6.1 Sol (`gpt-6.1-sol`), with equal weights for three KPIs.
The instructions, harness implementation and reviewed suite are pinned per run.

| KPI | What the agent does | What earns credit |
| --- | --- | --- |
| State recreation | Orchestrates a player-declared play through the normal moderator workflow | The resulting authoritative gameplay state matches the reviewed state |
| Human-move agreement | Chooses a move from the same reviewed information available to the recorded player | The semantic move matches the reviewed human move |
| Rule correctness | Chooses or orchestrates a play under a pinned format | An independent referee approves its legality under those exact rules |

Each KPI is passed cases divided by all applicable cases. The final percentage
is `(state recreation + human-move agreement + rule correctness) / 3`, where the
three inputs are percentages. For example, 90%, 75% and 95% produce 86.7%.
This example is illustrative; no complete three-KPI score has been measured yet.
The [first Edison pilot](edison-pilot.md) measured two KPIs on six micro-positions;
human-move agreement and the final score remain unavailable.

A different legal move fails human agreement but passes rule correctness.
Semantic comparison ignores wording but retains consequential choices such as
cards, targets, costs, positions and effect modes. Recorded human choices are
reference decisions, not proof of optimality or legality.

## Execute through the harness

Use the existing harness orchestrator, player tasks, response windows and sole
moderator writer. For state recreation, the agent interprets the declared play
and submits reviewed action records; an adapter must not supply the correct
patches. For move reproduction, the player receives only its reviewed filtered
context. Expected moves, future replay events, opponent hidden cards and grading
keys stay outside the player's context. Moderator context and independent
grading remain separate from player history.

Replay the authoritative action journal to score state recreation. Verify that
its initial state matches the reviewed checkpoint and that all transitions and
hashes verify. Compare all gameplay roots, including both players, ordered zones,
phase, turn, active player, chain, pending decisions/effects and game status.
Ignore administrative game IDs, revisions and rendering only.

Rule correctness needs an independent referee with the exact format, rules
version, banlist and card-text snapshots. Runtime acceptance alone does not
certify legality. The model being evaluated must not grade itself.

Once an agent chooses a different move, continue the simulation from its actual
state. Subsequent human replay moves cannot label that counterfactual position.
Further human-agreement tests must reset to independently reviewed reference
checkpoints. Report those as separate decisions, not an uninterrupted match.

## Scoring artifact contract

`python -m yugioh_benchmark.kpis suite.json run.json` scores trusted artifacts
collected by the existing workflow; this command does not launch a model or
simulate a duel. Install the pinned harness on the Python path for journal replay.
Keep run artifacts and game saves local and ignored.

The suite has `schema_version: "1.0"`, an `id` and a nonempty `cases` list.
Every case has a unique `id`, approved `review` with a named `reviewer`, and an
`initial_state_sha256`. Its `rules` object contains `format`, `rules_version`,
and SHA-256 values for `rules_sha256`, `banlist_sha256`, and `card_text_sha256`.

- `task: "state_recreation"` requires `declared_play` and a complete `expected_state`.
- `task: "human_move_reproduction"` requires a reviewed `human_move` dictionary
  with `kind`, and a source reference with `replay`, `before_sequence` and
  `payload_sha256`. Reviewers must verify those source links against the bundle.
- `task: "rule_correctness"` scores a separately reviewed player choice for
  legality only. It does not enter state recreation or human-move agreement.

The run records `suite_sha256`, `model`, `agent_instructions_sha256`,
`harness_fingerprint_sha256` and a `results` list. Each result has `case_id` and
`status` (`completed`, `timeout` or `missing`). Completed results carry:

- For state recreation: the authoritative `journal` from harness actions.
- For human agreement: `response`, `normalized_move`, and an approved
  `move_normalization_review` binding `response_sha256` and `move_sha256`.
- For legality: an approved `legality_review` with a named independent reviewer,
  `verdict` (`valid` or `invalid`), a `reason`, `rules_sha256` binding the entire
  case rules object, and `attempt_sha256` binding the result without that review.

Hashes use canonical sorted JSON with compact separators and UTF-8. Review
records are trusted evaluator artifacts, never accepted from the player as
self-certification. Digest bindings detect changed inputs; they do not authenticate
reviewer identity. Reports include denominators, pending grades and format counts.
Missing attempts and timeouts score zero. Present but ungraded attempts stay
pending and block a final score. A missing KPI also blocks the final score.

## Current replay and limits

The supplied native JSON replay is linked as `db-json-40753-85958923`;
the text companion retains `db-40753-85958923`. Its export labels the format
Unlimited. The user identifies it as Perfect Circle 2007. The declaration and
[September 2007 format reference](https://www.formatlibrary.com/formats/perfect-circle)
are recorded separately; exact card pool, historical rules and pre-errata texts
still require review. Do not infer
Edison, Goat or Advanced from its cards. Its states and decision boundaries still
need review. The native export supplies both players’ private draw logs and
absolute LP updates, but complete named decklists and reviewed checkpoints remain
pending. Hidden information cannot be invented; each player receives only the
information available at that decision. See [native JSON](native-json.md). It may provide reviewed move
references, but legality scoring requires a separately established rules profile.
Known-format cases can supply that KPI without relying on this replay's rules.

The configured target and weights are in `benchmarks/evaluation-config.json`.
The earlier 71.5% structural operation coverage contributes nothing to this score.
The scorer is available; the replay's reviewed checkpoints and a complete
three-KPI run remain pending. A 99% score would describe performance on these tested tasks. Competitive
training suitability additionally needs diverse positions, formats, matchups and
full games against strong opponents; human-move agreement alone cannot establish it.
