# Supplying Duelingbook replay data

## Preferred: native JSON export

In the replay page's browser developer tools, open Network, select Fetch/XHR,
reload and complete normal browser verification. Open the `view-replay` request
and copy its response into a UTF-8 `.json` file. Supply it with the replay URL.
Do not send a HAR, browser cookies, verification tokens or Copy as cURL output.
The converter imports the supplied file offline and never fetches protected data.

The [selected native export](../fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.json)
is the primary source for the sample match. It contains both players' private
draw logs, card definitions, runtime references, shuffle arrays and absolute LP
updates. It improves reconstruction evidence, but does not establish a historical
rules profile or complete named decklists. See [native JSON importing](native-json.md).

## Fallback: copied text

Open the replay in Duelingbook and copy its displayed duel/game log as text.
Include the full match: timestamped lines, turn headers and later games. The
copied date, chat, connection messages and search footer may remain in the text.
Use the [included sample](../fixtures/duelingbook/aco77-sdesowitz02-2026-10-07.txt)
as a format reference.

Supply the replay URL alongside the log when available, for example:
https://www.duelingbook.com/replay?id=40753-85958923.
A link identifies the source; importing uses the supplied text and does not
fetch the replay or require browser verification.

You can paste the text into the conversation, or save each match as a UTF-8
`.txt` file. For many matches, keep one file per match. Preserve line order and
repeated timestamps, and include hosting/acceptance lines so both participants
can be identified. For a partial export, supply both player names explicitly.
Do not fill in unknown cards or remove manual corrections.

The log may show private card names for one participant while hiding the other
hand. Keep this source evidence separate from a player prompt; reviewer filtering
and reconstruction are required before benchmark play.

Maintainers can use `convert-text` for a single log with its source URL, or
`import-texts` for a directory of `.txt` files. See [text-log importing](text-logs.md)
for commands, limits, deduplication and source linkage. Keep unselected raw logs
in ignored `imports/`; version selected fixtures deliberately.

The former archived API fixture, API-response/HAR importer and automated browser
capture remain retired. Native JSON is supported through the new explicit
`duelingbook-json-v1` adapter; unrelated legacy API bundles remain rejected.
