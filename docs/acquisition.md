# Save a DuelingBook replay as JSON

Use this guide to get the file an agent needs to import a replay into this
repository. You need a replay link and a browser. No Python commands or
CapSolver API key are needed for these steps.

## Chrome or Edge on a computer

1. Open the DuelingBook replay link.
2. Open Developer Tools: **F12** or **Ctrl + Shift + I** on Windows/Linux,
   or **Command + Option + I** on macOS. You can also use the browser menu.
3. Select the **Network** tab. If it is hidden, look in the **>>** overflow menu.
4. Make sure network recording is enabled, select **All**, and reload the replay
   page while Developer Tools stays open. Complete any normal browser verification.
5. Type **`view-replay`** in the Network filter box. Look for a request such as
   `view-replay?id=2178594` or `view-replay?id=678633-59711433`. Its replay ID must
   match the link you opened.
6. Select the request and open **Response**. Wait until its response is available.
   It should be JSON containing a nonempty **`plays`** array and **`player1`** and
   **`player2`** objects with usernames. An `action: "Error"` response is not a replay,
   even if the HTTP status is 200. If there are several attempts, choose the one
   with the actual replay data.
7. Right-click that request in the request list and choose
   **Copy → Copy response**. Copy the complete response body.
8. Paste it into a plain-text editor and save it as **`replay.json`**, using UTF-8.
   In Windows Notepad, choose **All files** in the Save dialog so the filename
   stays `replay.json` rather than `replay.json.txt`. Keep the JSON unchanged.
9. Upload **`replay.json`** to the agent and include the original replay link.
   For example: "Import this replay JSON into yugioh-benchmark. Source: [replay link]."

You do not have to watch the entire match. Once the successful response has
arrived, it contains the recorded operations supplied for that replay.
The agent validates the file, converts it into the repository format and records
its source. Missing hidden information is marked as a gap rather than invented.

Chrome documents [copying a response and exporting network data](https://developer.chrome.com/docs/devtools/network/reference#copy).
Menu wording can vary slightly between browser versions.

## If you cannot find the request

- Open **Network before reloading**; requests made before it started recording
  may not be listed.
- Select **All**, clear any other filters and confirm recording is enabled.
  Then reload and filter for `view-replay` again.
- If verification is still showing, finish it normally. A failed verification
  may prevent the replay request or return an error instead of JSON.
- If **Copy response** is unavailable, wait for the request to finish and check
  its **Response** tab.
- If the body is HTML, an error or a list of available replays, it is the wrong
  response. Open the specific replay link and capture its successful response.
- Opening `/view-replay` directly in the address bar is insufficient: the viewer
  submits a verified POST request; a direct request can return "Missing token".

## On mobile

Desktop Chrome or Edge is the simplest option. Ordinary mobile Chrome and Safari
do not provide the same on-device Network panel. These remote-inspection options
require a computer; a phone-only export workflow has not been tested here.

### Android with a computer

1. Enable **Developer options → USB debugging** on the phone.
2. Connect it to a computer by USB and approve the phone's debugging prompt.
3. On the computer, open Chrome and visit **`chrome://inspect/#devices`**.
   Enable **Discover USB devices**.
4. Open the replay in Chrome on the phone. On the computer, choose **Inspect**
   for that phone tab.
5. Use the inspected tab's **Network** panel, reload the replay on the phone,
   and follow the desktop steps above to copy and save the response on the computer.

See Google's [Android remote-debugging guide](https://developer.chrome.com/docs/devtools/remote-debugging)
for device detection and setup issues.

### iPhone or iPad with a Mac

1. On the device, enable Safari's **Advanced → Web Inspector** in Settings.
   Depending on the iOS version, Safari settings are under **Settings → Safari**
   or **Settings → Apps → Safari**.
2. Connect it to a Mac and approve the device's trust prompt if needed.
3. Enable Safari's developer features on the Mac. In Safari's **Develop** menu,
   select the device and its replay tab.
4. In Web Inspector, open **Network** before reloading the replay on the device.
   Find the matching `view-replay` request and copy its complete JSON response
   into a plain-text `replay.json` file on the Mac.

See WebKit's [Web Inspector setup guide](https://webkit.org/web-inspector/enabling-web-inspector/).
Safari's menus differ from Chrome's; the required file is still the full JSON
response body.

## Alternative: a browser HAR export

If copying the response is inconvenient, the importer also accepts a **HAR file
with response content**. In Chrome's Network panel, filter to the successful
`view-replay` request and use **Export HAR (sanitized)** or the corresponding
**Save all listed as HAR (sanitized)** menu option. Include the original replay
link when handing the file to the agent. Menu labels vary by browser version.

The HAR must contain exactly one valid replay response matching that link.
The importer keeps the replay body, not the surrounding request headers or
cookies. Prefer the single-response JSON for sharing: HAR files contain additional
network information. Keep raw HARs and imports local in ignored `imports/`.

## Acquisition implementation and current status

The public viewer loads replay data through a POST to `/view-replay?id=...`
after its normal browser verification. Downloading the HTML alone is insufficient.
An error or replay listing is rejected by the importer rather than stored as a duel.

Public archived API responses are another accepted source. Ambiguous multiple
valid HAR responses must be narrowed to the intended capture.

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
