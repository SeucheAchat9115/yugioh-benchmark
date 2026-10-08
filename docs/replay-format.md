# Replay bundle, version 1.0

`replays/<folder>/replay.json` is the manifest. `events/000001.json` and subsequent
files hold one native JSON play, timestamped text observation or turn header each. All strings are
UTF-8. The folder is a readable storage path; the manifest holds the source ID.

| Manifest field | Meaning |
| --- | --- |
| schema_version, id | Schema version and adapter-scoped ID: `db-json-<replay ID>` for native JSON; `db-<replay ID>` / `db-text-<sha256>` for text |
| source | Viewer URL/ID, source digest, adapter version and acquisition time |
| format | Unreviewed profile, banlist and rules identifiers; no inferred format |
| players | Stable p1/p2 slots and source usernames |
| coverage | Completeness/review status; hidden-card and physical-copy gaps |
| source_metadata | Text and participant names, or selected native JSON data and coverage audit |
| event_count | Number of observations and turn headers |
| events | Ordered `{sequence, path, sha256}` file references |

| Event field | Meaning |
| --- | --- |
| sequence | Consecutive one-based sequence |
| source_index | Zero-based index among parsed observations and turn headers |
| game | Sequential game, incremented on a later Turn 1 header |
| kind | Observational grouping such as summon, move, phase or unclassified |
| actor | p1/p2 when the speaker identifies a player; otherwise null |
| payload | Text message/line references, or literal `native` play structure plus observed annotations |

Timestamped payloads retain elapsed seconds, username and current observed turn.
Turn headers retain the original optional Game label, which may differ from the
sequential game. Duplicate timestamps preserve source order. Unknown non-event
lines remain in the full source text. No missing moves or card identities are
invented.

`kind` does not assert a legal action, effect resolution or priority window.
Match logs contain hidden information and outcomes; the full bundle is reviewer
data and must never enter a player prompt. `restore_source` validates the bundle
and returns its complete decoded source text or a copy of its selected native JSON.

The source hash covers decoded UTF-8 text after optional BOM removal. Event
hashes cover stored canonical JSON bytes including the final newline. Checkouts
preserve LF line endings via `.gitattributes`. Loading verifies paths, event
order, hashes, source identity and derived fields by reconversion. Conversion
refuses an existing output directory and writes through a temporary directory.
External provenance stays separate from derived metadata.

Text logs do not supply persistent physical-copy IDs or full decklists. Reviewers
must resolve card instances and check historical card text and rules before
producing a harness state. Machine-readable definitions are in [schemas](../schemas);
Python validation additionally verifies hashes and source derivation.

The supported adapters are `duelingbook-text-v1` and `duelingbook-json-v1`.
For JSON, the source digest covers canonical selected gameplay JSON, not raw
uploaded whitespace. Native entries retain source order, nullable elapsed time,
batched logs/card definitions and literal runtime references. Read
[native JSON importing](native-json.md) before resolving references or filtering
private data. Separate adapter IDs prevent old text sequences from becoming
native JSON sequences silently. Legacy API-observation adapters remain rejected.
