# Replay bundle, version 1.0

`replays/<id>/replay.json` is the manifest. `events/000001.json` and subsequent
files hold one original simulator operation each. Reading the manifest and a
selected event does not require opening the entire match. All strings are UTF-8.

| Manifest field | Meaning |
| --- | --- |
| schema_version, id | Schema version and `db-<replay ID>` identity |
| source | Original viewer URL, canonical source-payload SHA-256, adapter version and acquisition time |
| format | Source format code, suggested profile, unreviewed banlist/rules identifiers |
| players | Stable p1/p2 slots and source usernames |
| coverage | Explicit completeness/review status; no inferred hidden cards or certified legality |
| source_metadata | All original top-level fields except `plays`, retained losslessly |
| event_count | Number of source operations |
| events | Ordered `{sequence, path, sha256}` file references |

| Event field | Meaning |
| --- | --- |
| sequence | Consecutive one-based sequence |
| source_index | Zero-based index into the original plays array |
| game | Starts at 1; increments on observed `Begin next duel` |
| kind | Observational grouping such as summon, move, phase or unclassified |
| actor | p1/p2 when username identifies a player; otherwise null |
| payload | Complete original source operation, including cards, logs and timing when supplied |

`kind` does not assert a legal action, effect resolution or priority window.
Match metadata and source logs can contain hidden information and outcomes;
the full bundle is moderator/reviewer data and must never enter a player prompt.
The original source JSON can be reconstructed exactly with `restore_source`.
No duplicate raw source file is stored beside the converted bundle.

The source hash uses sorted-key, compact JSON with UTF-8 text and no NaN values.
Event hashes cover the stored file bytes, including the final newline. Bundle
checkouts preserve LF line endings via `.gitattributes` on every platform.
loading verifies file paths, order, hashes, source identity and all derived fields.
Conversion refuses an existing output directory and writes through a temporary
directory. External provenance is separate from the replay's derived metadata.

DuelingBook card `id`, physical-copy IDs and YGO `serial_number` are distinct.
They remain unchanged in payloads. A reviewer must map physical instances and
verified passcodes before producing a harness state. Historical effect text
and rules must be checked against the format/date rather than assumed current.

Machine-readable definitions are in [schemas](../schemas). JSON Schema checks
structure; the Python validator additionally checks hashes and source derivation.
