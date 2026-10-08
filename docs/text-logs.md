# Duelingbook text exports and benchmarks

Copied Chat/Duel/Game exports work offline, without a browser token or card-effect
engine. Keep each match in a UTF-8 `.txt` file. The included Aco77 vs sdesowitz02
fixture was supplied in the conversation on 2026-10-08; the log's displayed date
is retained as text, with no timezone assumption. The user also supplied its
[replay URL](https://www.duelingbook.com/replay?id=40753-85958923), which identifies
the sample as `db-40753-85958923`; its text digest is preserved for integrity.

Maintainer commands:

```sh
yugioh-benchmark convert-text imports/match.txt --output replays/my-match
yugioh-benchmark convert-text imports/match.txt --source https://www.duelingbook.com/replay?id=123 --output replays/db-123
yugioh-benchmark import-texts imports --output replays
yugioh-benchmark inspect replays/my-match
yugioh-benchmark candidates replays/my-match
```

Batch import reads sorted `.txt` files, validates the entire batch before writing,
deduplicates identical decoded text, and refuses existing output bundles. A
filesystem failure during writing can leave completed bundles; no batch
transaction is claimed. Truncated exports without hosting/acceptance lines need
`--players NAME NAME`. Unknown speakers remain unattributed, not new participants.
Imports are limited to 64 MiB per file. UTF-8 BOMs are removed on ingestion;
otherwise the decoded text, whitespace and newline spelling are retained.

Each timestamped observation and turn header gets a numbered event file, hashed
in the existing bundle manifest. Events link to the original 1-based line
number, raw line, elapsed seconds (when supplied), actor and sequential game.
Equal timestamps retain source order. A later Turn 1 starts a new sequential
game; the original optional Game label stays in the payload. Here the second
game says `Game 1`; its sequential bundle game is 2.

The full decoded source, including date, blanks, unknown lines and search footer,
is stored in `source_metadata.text`. `replay.restore_source` returns that string
for text bundles. Loading verifies both source
digest and derived annotations by reconversion, as well as individual event
hashes. When the URL is unknown, `source.url` and `source.replay_id` are null and
the ID is `db-text-<sha256>`. An explicitly supplied Duelingbook ID/URL uses the
existing `db-<id>` convention.

Quoted names are observations, not physical-copy IDs. An unknown draw/set remains
unknown; numbered hand positions do not establish persistent card identity.
LP deltas are explicit changes, not assumed initial or current totals. Chat
is retained as communication, never converted into card effects or strategic
labels. Logs may include actions after concession, lag, manual corrections,
control transfers and historical rules. All remain in source order.

The [source registry](../benchmarks/sources.json) links the selected fixture,
bundle, payload digest and review-candidate index. Candidate entries point to
source action observations; they are reviewer work items, not certified decision
windows, grading answers or player prompts. New imports can generate the same
index with `candidates`; deliberately selected sources can then be added to the
registry. Keep whole matches together when assigning train/test splits.

## Reviewed decision suites

Follow [harness integration](harness-integration.md) to reconstruct and review
positions. The sample has incomplete hidden information and no pinned rules,
so it supplies no approved decision cases. Review must establish the player's
actual information and decision window before supplying a filtered harness
context. Never pass a complete text log, candidate index or replay to a player.

`benchmark.run_suite(cases, transport, replays)` runs a list of reviewed harness
cases and returns results plus aggregate response agreement. `replays` maps
bundle IDs to loaded replay objects. The trusted transport must enforce a deadline;
only the harness player packet enters its stateless, tool-free request. The
suite validates all sources and contexts before its first model call.

Each case uses the existing case schema and additionally needs:

```json
{
  "review": {
    "status": "approved",
    "reviewer": "reviewer identity",
    "source_payload_sha256": "the linked bundle's source digest"
  },
  "grading": {
    "metric": "exact_response_agreement",
    "accepted_responses": ["reviewed response", 1]
  }
}
```

This fragment supplements a full case with `id`, `schema_version`, `source`
and `player_context`. Accepted responses can be text or integer choices.
Exact response agreement is a deliberately narrow metric: it measures agreement
with reviewer-approved answers, not independent legality, strategic optimality
or counterfactual win rate. Use a separate reviewer/rubric for those judgments.

Saved results can be scored offline without installing the harness:

```sh
yugioh-benchmark score cases/reviewed.json runs/results.json --replays replays
```

Cases and results are JSON arrays; each result contains `case_id` and `response`.
All suite cases stay in the denominator. Missing responses score zero; duplicate
or unknown IDs, unreviewed cases, invalid source sequences and digest mismatches
are rejected. Runs remain local in ignored `runs/`; selected reviewed cases may
be versioned. Model provider configuration is supplied through the transport.

For live agentic evaluation, see [the three-KPI score](agentic-kpis.md): state
recreation, human-move agreement and format-specific rule correctness. Structural
operation coverage is separate and does not enter that score.
