---
name: new-relic-frontend-coverage
description: Audit New Relic browser-based synthetic monitors plus browser/session-replay data to estimate frontend coverage percentage, identify uncovered routes and flows, and review monitor evidence such as results, screenshots, and logs.
---

# New Relic Frontend Coverage

Purpose: use New Relic Synthetics plus Browser monitoring to answer:
- what frontend pages or flows are covered by browser-based synthetic monitors
- what percentage of the intended frontend surface is covered
- which uncovered routes, browsers, or device classes still need monitors

## Feature toggles

Keep feature flags in scope from the start.

Rules:
- A route or flow behind a feature toggle is not automatically a coverage gap.
- Only count toggle-gated routes in the denominator when:
  - the flag is enabled in the target environment, or
  - the user explicitly wants pre-launch or dormant-flag coverage.
- If a route is hidden by a disabled flag in production, classify it as `out of scope by flag`, not `uncovered`.
- If a route is only enabled for a cohort, region, tenant, or role, mark coverage as conditional and say which audience the monitor covers.
- If monitors do not set the required flag state, identity, cookie, or query param to expose the feature, call that out as a monitor-scope limitation, not necessarily a missing monitor.

## Important distinction

If the user says `synthetic replay`, do not assume New Relic Synthetics has full session replay for monitor runs.

Use this split:
- `Synthetics evidence`: monitor results, step details, screenshots, and script logs
- `Browser replay`: Session Replay from Browser monitoring for real-user sessions

This distinction is an inference from current New Relic docs:
- Synthetics docs describe results, screenshots, and script logs for browser monitors.
- Session Replay is a Browser monitoring feature, not a Synthetics monitor-run playback feature.

## Use this skill when

- The user wants to review New Relic synthetic monitor runs for a frontend.
- The user wants a coverage percentage for routes, pages, or critical flows.
- The user wants to know which pages are observed by synthetics versus missing.
- The user wants to combine synthetic evidence with Browser Session Replay or BrowserInteraction data.

## Required inputs

Collect or infer these first:
- New Relic account or sub-account
- browser app name
- monitor IDs or monitor names, if known
- coverage window: default `7 days`
- coverage denominator:
  - preferred: explicit route/page inventory
  - fallback: router files, sitemap, nav structure, or agreed critical-flow list

If no denominator exists, say coverage % will only be an observed-coverage estimate, not a full frontend coverage number.

## Core workflow

1. Inventory the monitors
- Focus on browser-based monitors:
  - simple browser
  - scripted browser
  - step monitors
- Ignore ping and API monitors for frontend route coverage unless the user explicitly wants API coverage too.
- Record:
  - monitor type
  - runtime currency
  - browser types
  - device emulation settings
  - locations
  - frequency

2. Validate monitor evidence
- For each relevant monitor, inspect:
  - latest results
  - failed runs
  - screenshots
  - script logs
  - step details for step monitors
- Prefer browser-based monitors that actually navigate the frontend and wait long enough for Browser data to be captured.

3. Correlate Synthetics with Browser data
- Use Browser monitoring data to identify synthetic-generated frontend views/interactions.
- Prefer `BrowserInteraction` when route changes or SPA transitions matter.
- Use synthetic correlation fields documented by New Relic:
  - `monitorAccountId`
  - `monitorId`
  - `monitorJobId`
- If the browser comparison data is missing, check whether the monitor is too short-lived.
- Per New Relic docs, a scripted browser monitor may need a post-load wait so BrowserInteraction is captured.

4. Build the denominator
- Best denominator: intended route/flow inventory supplied by the repo or product owner.
- Acceptable sources:
  - router definitions
  - sitemap
  - nav menus
  - key landing pages
  - checkout/auth/onboarding flows
- Reduce the denominator by routes/flows that are disabled by feature flags in the target environment.
- Normalize route names before comparing:
  - use grouped URLs when Browser grouping is configured well
  - if URL grouping is poor, fix naming first
  - consider Browser APIs such as `setPageViewName` or SPA route naming if the app already uses them
- Record flag dependencies for each optional route or flow when known.

5. Compute coverage
- Numerator:
  - routes or flows with at least one qualifying browser-based synthetic observation in the window
- Denominator:
  - intended route/flow inventory after excluding flag-disabled scope
- Coverage %:
  - `covered / total * 100`
- Produce at least:
  - overall frontend coverage %
  - per-monitor route coverage
  - uncovered routes
  - weakly covered routes:
    - only one monitor
    - only one browser
    - only one device profile
  - out-of-scope-by-flag routes

6. Review replay/evidence for gaps
- For uncovered or suspicious routes:
  - review Synthetics screenshots and logs first
  - review Browser Session Replay only when the user also wants real-user evidence
- If Session Replay is needed:
  - verify Browser Pro or Pro+SPA agent
  - verify replay is enabled
  - verify session tracing is enabled
  - verify replay sampling and permissions

## Coverage rules

Use these rules consistently:

- `Covered`
  - At least one browser-based synthetic monitor observed the route/flow in the window.
- `Weak coverage`
  - Covered, but only:
    - one browser, or
    - one device profile, or
    - one location, or
    - one monitor, or
    - one run in the window
- `Uncovered`
  - In the denominator, but no qualifying synthetic observation in the window.
- `Observed only`
  - Seen in Browser synthetic data, but not mapped to the agreed route inventory.
- `Out of scope by flag`
  - Route or flow exists, but is disabled by feature flag for the target environment or audience.
- `Conditional coverage`
  - Route or flow is covered only for a specific flag state, tenant, role, or cohort.

## NRQL starting points

Adjust names and limits to the account.

### Synthetic-generated browser interactions

```sql
FROM BrowserInteraction
SELECT uniqueCount(browserInteractionName), uniques(browserInteractionName, 2000)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId IS NOT NULL
SINCE 7 days ago
```

### Synthetic-generated interactions by monitor

```sql
FROM BrowserInteraction
SELECT uniques(browserInteractionName, 2000)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId IS NOT NULL
SINCE 7 days ago
FACET monitorId
```

### Synthetic-generated grouped URLs when route names are poor

```sql
FROM BrowserInteraction
SELECT uniques(targetGroupedUrl, 2000)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId IS NOT NULL
SINCE 7 days ago
```

### Synthetic monitor run correlation

```sql
FROM BrowserInteraction
SELECT latest(monitorJobId)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId = 'YOUR_MONITOR_ID'
SINCE 7 days ago
```

### Real-user replay investigation companion query

```sql
FROM BrowserInteraction
SELECT count(*)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId IS NULL
SINCE 7 days ago
FACET browserInteractionName
```

## Monitor design guidance

When the user wants better coverage, recommend:
- scripted browser or step monitors over simple browser when route coverage matters
- multiple browsers where customer traffic justifies it
- device emulation for mobile/tablet-sensitive frontend paths
- explicit waits after page load when BrowserInteraction correlation is missing
- route naming cleanup before chasing exact percentages

Do not over-claim precision:
- if route grouping is poor, say coverage % is low-confidence
- if the denominator is incomplete, say it is partial coverage only
- if monitor data is recent or sparse, say so explicitly
- if feature-flag state is unknown, lower confidence and call out that denominator assumptions may be wrong

## Output

Use this structure:

1. `Coverage summary`
- overall coverage %
- denominator definition
- confidence: `high`, `medium`, or `low`

2. `Monitor inventory`
- monitor
- type
- browser/device coverage
- notes

3. `Covered routes`
- route or flow
- monitor(s)
- evidence type: interaction, screenshot, log, replay
- flag state or audience when relevant

4. `Uncovered or weak routes`
- route or flow
- gap type
- why it is weak or uncovered
- recommended monitor addition

5. `Out of scope by flag`
- route or flow
- controlling flag when known
- target environment assumption
- note that it is intentionally excluded from coverage %

6. `Replay/evidence notes`
- whether Synthetics evidence was enough
- whether Browser Session Replay was also required

7. `Next actions`
- first 3 monitor or instrumentation improvements

## Source notes

Base this skill on current New Relic docs, especially:
- monitor types and browser-based monitor capabilities
- result details, screenshots, and script logs
- Browser Session Replay setup and troubleshooting
- Browser/Synthetics comparison data and `monitorId` correlation
- device emulation and multi-browser support

If the docs or account behavior disagree, prefer the actual account behavior and state the discrepancy clearly.
