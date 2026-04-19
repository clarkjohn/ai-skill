---
summary: "Audit Java Spring or Spring Boot environment config for production-readiness, verify critical properties, and list smells."
read_when:
  - Reviewing Spring Boot `application*.yml` or `application*.properties`.
  - Auditing prod environment config, profiles, actuator exposure, secrets, logging, or DB safety.
---
# Spring Prod Config Audit

Purpose: audit a Java Spring / Spring Boot repo for missed prod overrides, config/code gaps, and production smells.

Origin:
- Built from Spring Boot reference docs for profiles, externalized config, actuator endpoints, SSL, and H2 console.
- Primary refs:
  - https://docs.spring.io/spring-boot/reference/features/profiles.html
  - https://docs.spring.io/spring-boot/reference/features/external-config.html
  - https://docs.spring.io/spring-boot/3.5/reference/actuator/endpoints.html
  - https://docs.spring.io/spring-boot/reference/features/ssl.html

Rules:
- Be version-aware. Detect Spring Boot major version first.
- Do not claim a property is wrong if Spring Boot’s default is already production-safe.
- Separate `confirmed issue` from `smell` from `missing evidence`.
- Prefer repo facts over generic advice.
- Call out when a finding is an inference.
- Run the bundled script first. Add manual review only where the script is weak or repo context demands it.
- Prioritize `prod override completeness gaps` over generic smell hunting.
- Use the full property matrix only when needed; default report should stay short.

## Default path

Run the bundled entrypoint first:

```bash
scripts/audit_spring_env [repo]
```

Default auto-detect:
- target: first prod-like profile such as `prod`, `production`, `prd`, `live`
- source: prefer `qa`, `uat`, `stage`, `staging`, `preprod`; otherwise fall back to `base`

If the repo uses different names, pass the pair explicitly:

```bash
scripts/audit_spring_env [repo] --from staging --to production
scripts/audit_spring_env [repo] --from base --to prod
```

Use JSON only when you need the full matrix or machine-readable output:

```bash
scripts/audit_spring_env [repo] --format json
```

Use raw resolver output only for debugging or source-tracing:

```bash
tools/spring-config-dump/run.sh --repo [repo] --profile prod
```

Read [references/smells.md](references/smells.md) only when the script output needs interpretation.

## What the script answers first

- `Prod override completeness gaps`
- `Code references missing in prod`
- `Prod properties likely unused by application code`
- `Prod property code coverage`
- effective-config-derived prod smells

## Add manual review only for

- runtime-only env vars
- Config Server / secret manager injection
- deployment manifests: Helm, K8s, ECS, Docker, Terraform, systemd
- custom `SecurityFilterChain` or unusual profile activation
- cases where the resolver output and repo structure disagree

## Output

Keep the main report short:

1. `Environment map`
   - Boot version
   - config files found
   - compared profiles
   - where prod values appear to come from
2. `Confirmed issues`
   - start with override completeness gaps
   - then code refs missing in prod
3. `Smells / weak signals`
   - only repo-backed smells
   - mark inference clearly
4. `Coverage summary`
   - counts by status: `application_exact`, `application_prefix`, `framework_managed`, `not_found`
   - list only the highest-signal `not_found` keys in the main report
5. `Gaps`
   - missing runtime evidence
6. `Fix next`
   - first 3 actions

Put the full property-by-property matrix in JSON or appendix form only when asked.

## Notes

- If the repo is plain Spring Framework and not Spring Boot, adapt the audit and say Boot-specific checks are only partially applicable.
- If deployment config is outside the repo, say exactly which runtime facts are missing.
- If the repo uses Boot 2.x, most heuristics still apply, but note any property-name differences before calling something wrong.
- When `qa` and `prod` use different file structures, normalize to effective property keys before comparing.
- `spring-config-dump` is the preferred resolver because it uses Spring Boot’s config loading APIs directly.
- Code-usage scan is heuristic. It checks `@Value`, `Environment#getProperty`, binder calls, and `@ConfigurationProperties` prefixes, so treat `unused` as a smell until confirmed.
