# Evaluation of the supplied Duelingbook game

The requested source is [Aco77 vs sdesowitz02, replay 40753-85958923](https://www.duelingbook.com/replay?id=40753-85958923).
Artificial Edison positions are separate diagnostics and do not measure this match.

On October 8, 2026, two fresh native children requested as `gpt-6.1-sol` chose
the next action from source-derived opening positions. Both matched the human:

| Recorded position | Human first action | Model first action | Match |
| --- | --- | --- | --- |
| Game 1, before event 23, 0:39 | Activate Reasoning | Activate Reasoning | Yes |
| Game 2, before event 361, 15:58 | Activate Destiny Draw | Activate Destiny Draw | Yes |

The Game 2 model also proposed discarding Destiny HERO - Dasher, as recorded in
the following event. The scored signature is the first action's verb and card;
this run does not certify every cost, target, slot or later action.

**Limited-information opening-action agreement: 2/2 (100%).** This is not the
complete human-move KPI, full-game accuracy, a win rate or the three-KPI score.
All complete-match KPIs and the final score remain unmeasured.

## Source reconstruction and information boundary

`replay_decisions.opening_diagnostics(replay, actor="p2")` selects the first
voluntary action in each sequential game and reconstructs only the preceding
observations. It requires named own opening draws and rejects unsupported
preceding gameplay. Here it produces two positions for sdesowitz02; it produces
none for Aco77, whose own opening cards are hidden in the supplied text.

The helper returns separate source references, an evaluator reference and a
player `context`. Pass only `frame["context"]` to the harness's
`harness.players.isolated.model_request` / `ContextOnlyPlayer`. Never send the
whole frame, its grading reference or the full source to a player.

Player packets include the six observed own cards and public face-down slots.
They hide opponent card identities and all future events. Hand shuffles prevent
recovering source hand positions; the packet's card names are an unordered
inventory, not persistent physical-copy handles. LP, deck/Extra/Side counts,
decklists and historical rules remain unknown instead of receiving invented
defaults. These are partial observation packets, not authoritative harness
states: do not load them as complete live-duel checkpoints.

Each model child had no inherited conversation and was instructed not to use
tools/files/network even though shared host capabilities were available. The
host condensed the permitted packet into its native message, withholding
reference moves and future source events. This was cooperative isolation, not a
verified sandbox. No child tool use was observed. The host independently
normalized terminal intentions to first-action signatures. No provider usage
attestation is available. Saved responses were subsequently validated with the
harness's context-only adapter; that validation is not a second model run.

## What still blocks a complete game benchmark

The supplied text is labelled Unlimited. It does not pin historical rules,
banlist or card-text version, and it omits full decklists, an explicit initial
LP baseline and some hidden state/response details. The live replay webpage was
retrievable, but its detailed data requires browser verification. No verification
token or protected replay data was obtained. A current card-reference API request
returned HTTP 403, so these choices used model card knowledge with no supplied
historical card text.

Consequently, this run measures two exploratory choices under incomplete
information, not the same complete information the human possessed. Completing
the benchmark requires reviewed checkpoints with known player information and
agreed historical rules/card references. Full state recreation also needs
complete authoritative initial state, copy tracking and reviewed response/effect
checkpoints. Preserve unknowns and report coverage explicitly; do not silently
substitute Edison rules or count artificial positions as this replay's results.

The next preparation work should expand reviewed decisions from this source and
resolve those gaps. Once the agent diverges, continued live play follows its
actual new state; further replay-agreement tests reset to separate reviewed
reference checkpoints. The artificial-pilot percentages do not enter this match's
score. Local prompts, evaluator keys and model outputs stay outside Git.
