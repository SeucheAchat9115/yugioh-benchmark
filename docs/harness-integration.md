# Reviewed decisions through the harness

A replay is source evidence. A benchmark case is a reviewed position immediately
before a particular decision. The LLM should receive what that player knew at
that moment, then choose a move. A separate reviewer or grader evaluates legality,
strategic value and reasoning against a rubric. Exact historical-move agreement
alone is not an optimal-play score.

1. Select a source event and reconstruct the position before it. Resolve physical
   card identities, hands, zones, LP, phase, usage limits and public history.
2. Pin historical rules, banlist, card text and deck assets. Verify the position
   and real decision window; mark incomplete positions unsuitable for scoring.
3. Load that reviewed position into a harness runner. Do not start a newly shuffled
   duel to recreate a fixed decision. Checkpoint reconstruction is currently manual.
4. Call `harness_bridge.prepare_case` with the runner, actor, source sequence,
   reviewer approval and a grading rubric. It calls `runner.context(actor,
   compact=True)` and the harness's existing isolated-player validator.
5. Call `harness_bridge.run_case` with the case and a bounded model transport.
   Only the player context goes to the model; source references, grading data and
   future moves stay outside its prompt. Returned text is data, never executed.
6. Assess the response separately. Record correctness, alternatives, rationale,
   model/prompt versions, pinned asset hashes, latency and actual usage/cost
   metadata when available. Runs belong in ignored `runs/`.

The bridge imports the harness only when used. Install/check out the harness in
the same environment and make its `harness` package importable; standalone replay
conversion does not depend on it. The trusted model transport must enforce its
own request timeout and send only the supplied messages, with no inherited
orchestrator transcript, filesystem access or tools.

Cases use `{schema_version, id, source, review, player_context, grading}`;
`source.before_sequence` identifies the source boundary. `review` includes
`status: approved` and `reviewer`; keep pinning/reconstruction evidence there.
`player_context` uses the harness's existing schema, not a second game-state
format. `grading` can contain acceptable lines, illegal options and a rubric;
never pass the case object itself to a player. Store moderator snapshots separately
if needed for adjudication. They must contain all known hidden state, while player
contexts contain only information available to that actor.

`run_case` currently returns a decision, measured latency and `assessment: null`.
Automated rubric grading, checkpoint reconstruction, model provider transports
and a reviewed suite are future additions. Historical replays cannot evaluate a
counterfactual win rate once the model diverges; that requires actual new duels
in the harness against controlled opponents with repeated seeds and side swaps.
