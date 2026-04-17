---
summary: "Audit Java Spring or Spring Boot environment config for production-readiness, verify critical properties, and list smells."
read_when:
  - Reviewing Spring Boot `application*.yml` or `application*.properties`.
  - Auditing prod environment config, profiles, actuator exposure, secrets, logging, or DB safety.
---
# Spring Prod Config Audit

Purpose: audit a Java Spring / Spring Boot repo for environment layout, production-critical properties, and configuration smells, with primary focus on missed prod overrides.

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
- Run the bundled script first, then use judgment on top.
- Trace how values are overridden from base config into each environment.
- Check for override gaps: values explicitly overridden in `qa` but left at base in `prod`.
- Prioritize `prod override completeness gaps` over generic smells.
- Check code-to-config coverage in both directions:
  - Java/Kotlin classes loading properties missing from prod
  - prod properties that appear unused by application code
- For each effective prod property, classify it as:
  - `application_exact`
  - `application_prefix`
  - `framework_managed`
  - `not_found`

## Quick scan

Run in the target repo:

```bash
/Users/john/ws/projects/skills/spring-prod-config-audit/scripts/audit_spring_env . --from qa --to prod

/Users/john/ws/projects/skills/spring-prod-config-audit/tools/spring-config-dump/run.sh --repo . --profile qa

/Users/john/ws/projects/skills/spring-prod-config-audit/tools/spring-config-dump/run.sh --repo . --profile prod

/Users/john/ws/projects/skills/spring-prod-config-audit/tools/spring-config-dump/run.sh --repo .

/Users/john/ws/projects/skills/spring-prod-config-audit/scripts/audit_spring_env . --from qa --to prod --format json

rg -n "spring-boot|org.springframework.boot" pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts gradle.properties 2>/dev/null

rg --files -g 'application*.properties' -g 'application*.yaml' -g 'application*.yml' -g 'bootstrap*.properties' -g 'bootstrap*.yaml' -g 'bootstrap*.yml' .

rg -n "spring\\.profiles|spring\\.config\\.activate|management\\.|server\\.error\\.|logging\\.level|spring\\.h2\\.console|spring\\.jpa\\.hibernate\\.ddl-auto|spring\\.sql\\.init|spring\\.devtools|springdoc|graphiql|cors|allowed-origins|forward-headers|ssl|truststore|keystore|datasource|vault|secret|password|token|key" \
  src main config helm charts deploy k8s kubernetes infra . 2>/dev/null
```

Also inspect:
- `pom.xml`, `build.gradle`, or `build.gradle.kts`
- all `application*.yml` / `application*.properties`
- deployment manifests: Helm, K8s, Docker, Terraform, ECS, systemd, etc
- CI/CD or runtime launch flags that set `SPRING_*` env vars
- Prefer `spring-config-dump` for effective config resolution. Use the Python audit script for comparison, smells, and code-usage reporting.

## Audit workflow

1. Detect config topology
- List every config file and which profiles exist: `dev`, `local`, `test`, `staging`, `prod`, `production`, etc.
- If `qa` exists, compare it directly with `prod` / `production`.
- Find how profiles are activated:
  - `spring.profiles.active`
  - `spring.profiles.include`
  - `spring.profiles.group.*`
  - `spring.config.activate.on-profile`
  - CLI / env vars / manifests
- Find whether prod config lives in repo, external files, env vars, config trees, or secret stores.
- Explicitly list properties set in `qa` but not set in `prod`.
- Treat this as a smell, not an automatic issue, until runtime defaults or external env injection are checked.
- Also inspect override chains for key properties: which base file sets them, which env file overrides them, and where `prod` falls back to base while `qa` diverges.
- Treat the top script section, `Prod override completeness gaps`, as the main answer to "was anything missed in prod overrides?"
- Also inspect `Code references missing in prod` and `Prod properties likely unused by application code`.
- Also inspect `Prod property code coverage` for a property-by-property answer.

2. Detect Spring Boot version
- Boot 2.x vs 3.x/4.x matters for some property names and defaults.
- If version is unclear, say so and keep findings conservative.

3. Check profile correctness
- Per Spring docs, `spring.profiles.active` and `spring.profiles.default` only belong in non-profile-specific documents.
- Same caution for `spring.profiles.include` and `spring.profiles.group.*`.
- Flag invalid usage inside profile-specific files or docs activated by `spring.config.activate.on-profile`.
- Smell: prod profile includes `dev`, `local`, or `test`.
- Smell: multiple competing activation mechanisms with unclear precedence.
- Smell: `qa` carries explicit overrides that `prod` does not, especially for datasource, security, actuator, CORS, logging, caches, queues, or third-party endpoints.
- Smell: `qa` overrides a base property while `prod` silently inherits base, unless there is clear evidence that base is the intended prod value.

4. Check secret handling
- Flag plaintext secrets committed in repo: passwords, API keys, tokens, private keys.
- Smell: prod credentials hardcoded in `application-prod.*`.
- Good signal: env vars, mounted config trees, Vault, or other external secret stores.
- From Spring docs: externalized config is preferred; Spring Boot itself does not provide built-in property encryption.

5. Check actuator / management exposure
- From Spring docs, only `/health` is exposed over HTTP by default.
- Flag `management.endpoints.web.exposure.include=*` unless clearly justified and secured.
- Flag exposure of `env`, `configprops`, `beans`, `mappings`, `heapdump`, `threaddump`, `loggers`, or `shutdown` on public interfaces.
- If a custom `SecurityFilterChain` exists, note that Spring Boot auto-config backs off; actuator protection must then be reviewed explicitly.
- Smell: `management.endpoint.health.show-details=always` without clear network or auth controls.
- Smell: management endpoints share public port and no evidence of auth, firewalling, or path isolation.

6. Check database safety
- Flag `spring.jpa.hibernate.ddl-auto=create` or `create-drop` in prod as high risk.
- Flag `spring.jpa.hibernate.ddl-auto=update` in prod as a smell unless there is an explicit accepted reason.
- Prefer `validate` or `none` plus Flyway/Liquibase for production schema changes.
- Smell: `import.sql`, `data.sql`, or demo seed paths active in prod.
- Smell: embedded DB dependencies or H2 usage outside test/dev.

7. Check dev-only features
- Flag `spring.h2.console.enabled=true` in prod. Spring docs say H2 console is intended for development only.
- Flag `spring-boot-devtools` on production runtime path.
- Flag dev toggles in prod:
  - `server.error.include-stacktrace=always`
  - `server.error.include-message=always`
  - `spring.mvc.log-request-details=true`
  - `spring.http.codecs.log-request-details=true`
  - GraphiQL or Swagger UI exposed without controls

8. Check logging / observability safety
- Smell: `logging.level.root=DEBUG` or `TRACE` in prod.
- Smell: verbose SQL logging in prod without a narrow reason.
- Good signal: health, metrics, tracing, structured logs, correlation ids.

9. Check network / TLS / proxy handling
- If app terminates TLS itself, look for SSL config or documented platform termination.
- If behind a proxy or load balancer, verify forwarded-header handling is intentional.
- Smell: no evidence of TLS or proxy-awareness in a public-facing app.
- This check is contextual: deployment manifests may be the source of truth, not app config.

10. Check CORS / cookies / session safety
- Smell: `allowed-origins=*` with credentials.
- Smell: overly broad CORS in prod without justification.
- Smell: insecure cookie/session settings for browser apps.

## Smell catalog

High:
- plaintext prod secrets in repo
- `ddl-auto=create` or `create-drop`
- H2 console enabled in prod
- actuator `include=*` on public surface
- sensitive actuator endpoints exposed without clear auth
- custom `SecurityFilterChain` present but no clear actuator rules

Medium:
- `ddl-auto=update`
- `health.show-details=always`
- root logging `DEBUG` / `TRACE`
- devtools present outside dev-only scope
- `import.sql` / demo data likely active in prod
- open CORS
- prod profile activation unclear or conflicting

Low:
- duplicated env config
- too many profiles with unclear ownership
- secrets referenced with inconsistent naming
- prod config spread across many places with no obvious source of truth

## Output

Use this structure:

1. `Environment map`
- Spring Boot version
- config files found
- profiles found
- how prod is activated
- where prod secrets/config come from
- include script output summary first
- include notable override chains first

2. `Confirmed issues`
- bullet list
- include file/path and exact property
- explain why it is risky
- mark severity: `high`, `medium`, `low`
- start with prod override completeness gaps
- then code references missing in prod

3. `Smells / weak signals`
- things that look risky but need deployment context
- explicit note when this is an inference
- include `set in qa, missing in prod` diffs with likely impact
- include `qa overrides base, prod does not` gaps with likely impact
- include prod properties that look unused by application code

4. `Prod property coverage`
- for each effective prod property, show:
  - property key
  - source config file/doc
  - status: exact, prefix, framework-managed, or not found
  - matching code locations if found

5. `Production-safe settings confirmed`
- list properties or defaults that look correct
- include good defaults when relevant, not only explicit properties

6. `Gaps`
- what cannot be verified from repo alone
- ex: ingress TLS termination, secret manager wiring, runtime env vars

7. `Fix next`
- short ordered list of the first 3 remediation steps

## Notes

- If the repo is plain Spring Framework and not Spring Boot, adapt the audit and say Boot-specific checks are only partially applicable.
- If deployment config is outside the repo, say exactly which runtime facts are missing.
- If the repo uses Boot 2.x, most heuristics still apply, but note any property-name differences before calling something wrong.
- When `qa` and `prod` use different file structures, normalize to effective property keys before comparing.
- Script caveat: it merges repo-local config with Spring-like profile handling, but it cannot see runtime-only env vars, Config Server, or secret manager injection unless those are in repo manifests.
- `spring-config-dump` is the preferred resolver because it uses Spring Boot’s config loading APIs directly.
- Treat override-chain output as the source of truth for "how is this property overridden?" inside the repo.
- Treat prod override completeness gaps as the source of truth for "what did qa override that prod may have missed?" inside the repo.
- Code-usage scan is heuristic. It checks `@Value`, `Environment#getProperty`, `Binder.bind`, and `@ConfigurationProperties` prefixes, so treat "unused" as a smell until confirmed.
