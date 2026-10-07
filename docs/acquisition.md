# Obtain an actual replay

The public viewer loads replay data through a POST to `/view-replay?id=...`
after its normal browser verification. Downloading the HTML alone is insufficient.
An error or replay listing is rejected by the importer rather than stored as a duel.

Preferred inputs are a public archived API response or the response body from a
legitimate browser session. A HAR export **with response content** also works:
the importer selects the exact replay ID and strips the surrounding HTTP headers,
cookies and verification request. Keep the original HAR in ignored `imports/`.
Ambiguous multiple valid responses must be narrowed to the intended capture.

The optional `tools/capture_browser.py` operates the normal viewer in Microsoft
Edge through Playwright. The agent may run it internally on a compatible host.
It requires the optional `capture` dependency and Edge installed. Capture has
a 45-second response deadline and a total deadline 10 seconds longer. It reports
verification failure honestly and never substitutes synthetic replay data.
It is not required for conversion or regular CI.

The initial Edison candidate was
https://www.duelingbook.com/replay?id=678633-59711433.
Direct fetching returned “Missing token”; hosted browser verification did not
complete. To avoid blocking the implementation, the first import uses the
public archived match at https://www.duelingbook.com/replay?id=2178594.
Its pinned source blob and attribution are recorded in the bundle's provenance.
This is an archived-source import, not a claim that live extraction succeeded.
