# Real product screenshot capture

For a product demo or launch video, prefer supplied real screens or capture the
actual product. Never substitute generated UI illustrations for missing evidence.
Use `tools/capture_product_screens.py`; it prepares private Node, Playwright and
Chromium on first use, independent of any desktop app. Run the OS setup launcher
first if Python is absent, then use its returned `pythonExecutable`.

## Choose the capture layout

Match the product experience to the intended video: mobile product/mobile demo
uses `mobile`, desktop software uses `desktop`, and a comparison uses both.
Portrait video alone does not mean desktop software becomes a mobile app. Record
the choice in `style.md`. Default desktop is 1920×1080; mobile is iPhone 13 with
its responsive viewport, touch, device scale and mobile user agent. Set
`mobileDevice` to another Playwright mobile preset or `desktopViewport` to the
required size. These are responsive web captures, not native iOS/Android app
screenshots. Use supplied native-app footage or a separate emulator tool there.

## Identify and inspect the product

Use a supplied URL, running local app, or a repository's documented dev URL.
Start a local app only within the authorized project scope. If no product can
be identified, ask for its URL or local project; never guess a login destination.
Inspect the public landing page first using the agent's browser tools, or make
a preliminary one-screen capture with this tool. Identify 3–6 screens that
support the brief (overview, main task, feature detail, verified result). Inspect
each image and iterate selectors/routes; this tool executes an agent-authored
plan rather than autonomously discovering arbitrary applications.

## Login and capture plan

Credentials are read from environment variables, never literal plan values or
command-line arguments. Ask the user to provide them through the host's private
secret mechanism. Do not echo values, store them in the brief, or commit them.
Alternatively pass `--session /private/path/session.json` for an existing
Playwright storage-state file outside the project/export directory. The tool
never exports or saves session state. Exclude session files from Git.

```json
{
  "baseUrl": "http://localhost:3000",
  "profiles": ["desktop", "mobile"],
  "mobileDevice": "iPhone 13",
  "desktopViewport": {"width": 1920, "height": 1080},
  "maskSelectors": ["[data-private]", "[data-testid='account-email']"],
  "login": {
    "url": "/login",
    "steps": [
      {"action": "fill", "selector": "input[name='email']", "valueEnv": "PRODUCT_LOGIN_EMAIL"},
      {"action": "fill", "selector": "input[name='password']", "valueEnv": "PRODUCT_LOGIN_PASSWORD"},
      {"action": "click", "selector": "button[type='submit']"}
    ],
    "readySelector": "[data-testid='dashboard']"
  },
  "screens": [
    {"name": "overview", "url": "/dashboard", "readySelector": "main", "alt": "Product dashboard"},
    {"name": "feature", "url": "/reports", "steps": [{"action": "click", "selector": "[data-testid='report-tab']"}], "readySelector": "[data-testid='report-chart']"}
  ]
}
```

Omit `login` for public pages or an already authenticated session. Routes and
explicit navigation stay on the product origin; login redirects may reach an
identity provider. Steps support `click`, `fill` (environment values), `wait`
and `press` (with `key`). Screen `selector` captures one element;
`fullPage: true` captures a full page; viewport capture is the default for video.
Use stable selectors and readiness elements instead of arbitrary sleep delays.

```sh
python3 tools/capture_product_screens.py capture-plan.json --out captures
```

Use `--headed` for user-assisted MFA/SSO; the login readiness selector waits up
to 120 seconds (`login.timeoutMs` overrides it). Never bypass CAPTCHA or assume
successful login. Missing credentials or access is required input and cannot
be auto-selected after an optional-question timeout. During exploration only
perform navigation/filter/tab actions; do not submit purchases, send messages,
delete data, or change account settings without explicit authorization.

## Review and handoff

Outputs are `<screen>-desktop.png` / `<screen>-mobile.png` and `manifest.json`
with sanitized source URLs (no query/hash), viewport/device, timestamp, digest,
alt text and review status. URL paths may still contain private identifiers:
review them too. Mask private selectors before capture. Password inputs are
always masked, but other personal data needs explicit selectors. Inspect every
image for login failures, loading states, unreadable crops and private data
before selecting it. Mark reviewed assets in the working asset manifest, copy
only selected screenshots into video assets, and retain their capture provenance.
Keep private capture plans/session files outside the editable video source tree.
Failed captures may leave partial images; review or discard those before retrying
into a new empty directory. Do not claim a screenshot proves an unseen workflow.
