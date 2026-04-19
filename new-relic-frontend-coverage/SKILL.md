---
name: new-relic-frontend-coverage
description: Audit New Relic browser-based synthetic monitors to estimate frontend coverage percentage, identify uncovered or weak routes, and review monitor evidence. Supports SPA and non-SPA frontends, with feature flags excluded from coverage when disabled.
---

# New Relic Frontend Coverage

Purpose: answer three things fast:
- which frontend routes or flows are covered by browser-based synthetic monitors
- what coverage % is reasonable for the target environment
- which routes are weak, uncovered, or out of scope because of feature flags

## Rules

- Use browser-based synthetic monitors only: simple browser, scripted browser, or step monitors.
- Do not treat feature-flagged routes as gaps when the flag is disabled in the target environment.
- Do not assume `synthetic replay` exists as full monitor-run playback.
- Use Session Replay only as optional real-user evidence, not as the primary coverage source.

## Coverage mode

Pick one first:

- `SPA mode`
  - Use `BrowserInteraction` as primary evidence.
  - Best when the app uses the SPA-capable browser agent and route changes matter.
- `MPA/basic mode`
  - Use Browser page-view/grouped-URL evidence plus Synthetics screenshots/logs/results.
  - Use this when `BrowserInteraction` is sparse, missing, or the app is not really SPA-instrumented.

If unclear, say which mode you chose and why.

## Inputs

Collect or infer:
- New Relic account
- browser app name
- target environment
- coverage window: default `7 days`
- monitor names or IDs, if known
- denominator source:
  - `authoritative`: route inventory from router, sitemap, product list, or explicit flow list
  - `estimated`: observed nav/routes with best-effort inference

If the denominator is not authoritative, still compute coverage if useful, but label it `estimated`.

## Workflow

1. Inventory monitors
- Keep only browser-based monitors relevant to the frontend.
- Record: monitor, type, browser/device, location, frequency.

2. Define denominator
- Build the intended route/flow list.
- Exclude routes disabled by feature flags in the target environment.
- Mark cohort/tenant/role-limited routes as conditional.

3. Collect evidence
- Synthetics evidence:
  - latest results
  - failed runs
  - screenshots
  - script logs
  - step details
- Browser evidence:
  - `BrowserInteraction` in `SPA mode`
  - grouped URL or page-view style evidence in `MPA/basic mode`
- For synthetic/browser correlation, use New Relic fields such as:
  - `monitorAccountId`
  - `monitorId`
  - `monitorJobId`
- If synthetic/browser comparison data is missing for a scripted browser monitor, check whether the run ends too quickly after load.

4. Compute coverage
- `Covered`: at least one qualifying synthetic observation in the window
- `Weak`: covered, but only one monitor, browser, device profile, location, or run
- `Uncovered`: in denominator, but no qualifying observation
- `Out of scope by flag`: intentionally excluded because the flag is disabled
- `Conditional`: covered only for a flag state, cohort, tenant, or role

Coverage %:
- numerator = covered routes/flows
- denominator = intended routes/flows minus out-of-scope-by-flag items

## NRQL starting points

### SPA mode

```sql
FROM BrowserInteraction
SELECT uniques(browserInteractionName, 2000)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId IS NOT NULL
SINCE 7 days ago
```

### Correlation by monitor

```sql
FROM BrowserInteraction
SELECT uniques(browserInteractionName, 2000), latest(monitorJobId)
WHERE appName = 'YOUR_BROWSER_APP'
  AND monitorId IS NOT NULL
SINCE 7 days ago
FACET monitorId
```

If route names are poor, use grouped URL evidence and say coverage confidence is lower.

## Output

Use this exact structure:

1. `Coverage summary`
- overall coverage %
- coverage mode: `SPA` or `MPA/basic`
- denominator basis: `authoritative` or `estimated`
- confidence: `high`, `medium`, or `low`

2. `Monitor inventory`
- monitor
- type
- browser/device coverage
- notes

3. `Covered routes`
- route or flow
- monitor(s)
- evidence used
- conditional audience or flag state when relevant

4. `Uncovered or weak routes`
- route or flow
- gap type
- why
- recommended monitor addition

5. `Out of scope by flag`
- route or flow
- controlling flag when known
- target environment assumption

6. `Next actions`
- first 3 improvements

## Notes

- If feature-flag state is unknown, lower confidence.
- If route grouping is poor, lower confidence.
- If denominator is estimated, say the % is directional, not exact.
- Prefer account behavior over documentation if they disagree, but state the discrepancy clearly.
