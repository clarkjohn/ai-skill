---
name: new-relic-frontend-coverage
description: Audit New Relic browser-based synthetic monitors to estimate frontend coverage percentage, identify uncovered or weak routes, and review monitor evidence. Supports SPA and non-SPA frontends, with feature flags excluded from coverage when disabled.
---

# New Relic Frontend Coverage

Purpose: answer three things fast:
- which frontend routes or flows are covered by browser-based synthetic monitors
- what coverage % is reasonable for the target environment
- which routes are weak, uncovered, or out of scope because of feature flags
- how to improve or implement monitors without over-counting superficial checks

## Rules

- Use browser-based synthetic monitors only: simple browser, scripted browser, or step monitors.
- Count ping, API, broken-link, and certificate monitors as supporting signals, not frontend UX coverage.
- Do not treat feature-flagged routes as gaps when the flag is disabled in the target environment.
- Do not assume `synthetic replay` exists as full monitor-run playback.
- Use Session Replay only as optional real-user evidence, not as the primary coverage source.
- Prefer current New Relic runtimes. Treat legacy runtimes as migration work, not a target.

## Coverage mode

Pick one first:

- `SPA mode`
  - Use `BrowserInteraction` as primary evidence.
  - Best when the app uses the SPA-capable browser agent and route changes matter.
- `MPA/basic mode`
  - Use Browser page-view/grouped-URL evidence plus Synthetics screenshots/logs/results.
  - Use this when `BrowserInteraction` is sparse, missing, or the app is not really SPA-instrumented.

If unclear, say which mode you chose and why.

## Implementation stance

When asked to improve the monitors, recommend the smallest monitor set that covers real user risk:

- `Simple browser`: public landing pages, static pages, and single URL page-load checks.
- `Step monitor`: stable click/form flows that do not need custom code.
- `Scripted browser`: login, tenant/role setup, conditional UI, dynamic assertions, shadow DOM, or helper logic.
- `API/certificate/ping`: backend, SSL, and availability support; useful, but not route/flow UX coverage.

Default implementation standards:
- Manage monitors with NerdGraph or Terraform when possible; avoid UI-only drift for production-critical coverage.
- Use non-legacy browser runtime. New scripted browser code should use `$selenium` and `$webDriver`, with explicit `await`.
- Use stable selectors such as `data-testid` or accessible roles/names. Avoid brittle CSS chains and text that changes often.
- End every flow with a business assertion, not just a successful navigation.
- Store usernames, passwords, tokens, and tenant IDs in New Relic secure credentials. Do not inline secrets in scripts.
- Use at least three relevant locations for public checks unless cost/noise is a known constraint.
- Cover the browser/device mix users actually use. For broad public web, include Chrome and Firefox plus mobile portrait for critical flows.
- Enable failure screenshots and useful script logs, but avoid logging secrets or PII.
- Add monitor downtimes or muting rules for planned maintenance instead of disabling monitors silently.
- Private/internal apps need private locations on synthetics job manager; verify private location health before blaming the app.

## Inputs

Collect or infer:
- New Relic account
- browser app name
- target environment
- coverage window: default `7 days`
- monitor names or IDs, if known
- implementation owner/IaC source, if known
- public vs private location requirements
- denominator source:
  - `authoritative`: route inventory from router, sitemap, product list, or explicit flow list
  - `estimated`: observed nav/routes with best-effort inference

If the denominator is not authoritative, still compute coverage if useful, but label it `estimated`.

## Workflow

1. Inventory monitors
- Keep only browser-based monitors relevant to the frontend.
- Record: monitor, entity GUID, monitor ID, type, runtime, browser/device, location, frequency, status, alert coverage.
- Flag legacy runtimes, single-location monitors, single-browser critical flows, disabled monitors, and monitors without alert conditions.

2. Define denominator
- Build the intended route/flow list.
- Exclude routes disabled by feature flags in the target environment.
- Mark cohort/tenant/role-limited routes as conditional.
- Weight critical business flows separately from route count when a flat route percentage would be misleading.

3. Collect evidence
- Synthetics evidence:
  - latest results
  - failed runs
  - screenshots
  - script logs
  - step details
  - runtime, browser, device, and location dimensions
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
- `Weak`: covered, but only one monitor, browser, device profile, location, run, or no final business assertion
- `Uncovered`: in denominator, but no qualifying observation
- `Out of scope by flag`: intentionally excluded because the flag is disabled
- `Conditional`: covered only for a flag state, cohort, tenant, or role

Coverage %:
- numerator = covered routes/flows
- denominator = intended routes/flows minus out-of-scope-by-flag items

For implementation reviews, add a second score when useful:
- `Critical flow coverage`: covered critical flows / all critical flows
- `Quality coverage`: covered flows that also meet runtime, assertion, location, alert, and credential standards

## NRQL starting points

### Monitor inventory and runtime

```sql
FROM SyntheticCheck
SELECT latest(monitorName), latest(type), latest(monitorExtendedType),
       latest(runtimeType), latest(runtimeTypeVersion),
       uniques(locationLabel), uniques(browserVersion),
       uniques(deviceType), uniques(deviceOrientation), count(*)
WHERE type IN ('BROWSER', 'SCRIPT_BROWSER')
   OR monitorExtendedType = 'STEP_MONITOR'
SINCE 7 days ago
FACET monitorId
```

### Failed or noisy monitors

```sql
FROM SyntheticCheck
SELECT count(*) AS 'runs',
       filter(count(*), WHERE result = 'FAILED') AS 'failures',
       percentage(count(*), WHERE result = 'FAILED') AS 'failure rate'
WHERE type IN ('BROWSER', 'SCRIPT_BROWSER')
   OR monitorExtendedType = 'STEP_MONITOR'
SINCE 7 days ago
FACET monitorName, locationLabel
```

### SPA mode

```sql
FROM BrowserInteraction
SELECT uniques(browserInteractionName, 2000), uniques(targetRouteName, 2000), uniques(targetGroupedUrl, 2000)
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
- critical flow coverage, when known
- quality coverage, when useful

2. `Monitor inventory`
- monitor
- type
- runtime
- browser/device/location coverage
- alert coverage
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

5. `Implementation gaps`
- gap
- impact
- recommended fix
- owner/source file when known

6. `Out of scope by flag`
- route or flow
- controlling flag when known
- target environment assumption

7. `Next actions`
- first 3 improvements

## Notes

- If feature-flag state is unknown, lower confidence.
- If route grouping is poor, lower confidence.
- If denominator is estimated, say the % is directional, not exact.
- Prefer account behavior over documentation if they disagree, but state the discrepancy clearly.
- If New Relic docs and account behavior disagree, verify with a small monitor validation run before recommending broad rollout.
