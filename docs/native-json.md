# Native Duelingbook JSON

The user-supplied `view-replay` response is now the primary source for
[replay 40753-85958923](https://www.duelingbook.com/replay?id=40753-85958923).
The selected [JSON fixture](../fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.json)
and [native bundle](../replays/db-json-40753-85958923) are linked in
[the source registry](../benchmarks/sources.json). The text fixture/bundle and
their original event numbers remain separately identified companions.

## Import

```sh
yugioh-benchmark convert-json imports/replay.json --source https://www.duelingbook.com/replay?id=40753-85958923 --output replays/my-native-replay
yugioh-benchmark inspect replays/db-json-40753-85958923
yugioh-benchmark candidates replays/db-json-40753-85958923
```

The importer runs offline without a browser, credentials or a card-effect engine.
It checks the supplied URL against the native duel ID, rejects duplicate JSON
keys/nonfinite values, and creates the existing hashed observation bundle.
Tag duels are rejected until a four-player adapter exists.

Native IDs are `db-json-<replay ID>`, with adapter `duelingbook-json-v1`.
There is one event per source `plays` entry; batched opening draws remain within
their original `Pick first` entry. Native sequence numbers therefore differ from
text sequence numbers. Rebuild and review cases against the native digest/index;
never reuse a text sequence with the new source ID. Candidate indexes are
review work items, not certified decisions or player prompts.

## What this export adds

| Evidence | Selected export |
| --- | --- |
| Source plays / games | 554 / 2 |
| Review candidates | 174, all unreviewed |
| Private named draw observations | Aco77: 19; sdesowitz02: 25 |
| Draw observations without private names | None |
| Starting LP from explicit signed/absolute updates | 8000 for both players in both games |
| Main / Extra / Side arrays | Runtime references and counts; not complete named decklists |
| Card definitions | Names, text, stats, native catalog IDs, serial numbers and object IDs where supplied |
| Hand/deck shuffles | Literal arrays and source references preserved |
| Source format / rules code | `uu` / `*`; historical rules remain unverified |

The LP audit subtracts cumulative explicit changes from absolute recorded LP;
all observations agree on those baselines. It does not assume 8000 or certify
the rules behind each LP change. No engine state is reconstructed by importing.

`id` on a native action, card `id`, `object_id`, serial number and player
Main/Extra/Side arrays have distinct roles. Do not turn catalog IDs into physical
copies, conflate player namespaces, or assume shuffle-generated runtime handles
are persistent. Preserve all references and review their mapping before creating
harness copy identities or effect checkpoints. Unseen card names are not inferred.

The embedded descriptions can be current text even when the recorded game uses
historical effects. For example, exported Dark Magician of Chaos describes
End Phase spell recovery, while the text companion records immediate recovery.
Neither the source format code nor current card-limit fields establish the agreed
historical rules/banlist. This still blocks certified rule-correctness scoring.

## Provenance and privacy

The selected fixture removes account/display data such as ratings, user IDs,
sleeves and token-art selections; gameplay entries, private/public logs and card
definitions remain. The source digest covers canonical selected JSON. The
registry separately pins uploaded raw bytes and selected fixture bytes. Original
uploaded data remains local; it is not a model run or harness save.

Loading verifies file hashes and re-derives annotations from the selected source.
`restore_source` returns a copy of that JSON object. This is a deterministic
gameplay-source round trip, not a byte-for-byte restoration of removed cosmetics
or original JSON whitespace.

`conceal: false` provides private observations for both players and future cards.
The complete export/bundle is evaluator data, never a player packet. Reconstruct
and review each checkpoint, then use the harness's permitted views and separate
player histories. Later-revealed identities, opponent hands and future draws must
not leak backward into player context. Original attribution and source-data
rights remain in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

This import improves the evidence for all three KPIs; it does not calculate a
model score. State reconstruction, response/effect windows, historical rules and
ground-truth decisions still require review. Do not treat native event counts,
candidate counts or old text diagnostic scores as a complete game benchmark.

## Card references

[YGOPRODeck metadata](card-metadata.md) resolves all 42 distinct passcodes
explicitly defined here to names and current texts. It is a separate dated
snapshot; it does not replace this source, name unobserved deck slots or verify
historical rules. The source registry links the snapshot.
