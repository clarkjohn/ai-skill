# Spring Prod Smells

Read this only when the script output needs interpretation.

Scope: Spring environment/config evidence only. Do not turn this into a general application security or code audit.

High:
- plaintext prod secrets in repo
- `spring.jpa.hibernate.ddl-auto=create`
- `spring.jpa.hibernate.ddl-auto=create-drop`
- embedded/in-memory DB configured for prod (`jdbc:h2:`, `jdbc:hsqldb:`, `jdbc:derby:`, `r2dbc:h2:`), unless explicitly intended
- SQL init always active in prod (`spring.sql.init.mode=always`, legacy `spring.datasource.initialization-mode=always`)
- `spring.h2.console.enabled=true`
- `spring.liquibase.drop-first=true`
- Flyway clean allowed in prod (`spring.flyway.clean-disabled=false`)
- `management.endpoints.web.exposure.include=*`
- sensitive actuator endpoints enabled on a public surface
- unsanitized actuator config values (`management.endpoint.env.show-values=always`, `management.endpoint.configprops.show-values=always`, `management.endpoint.quartz.show-values=always`)
- prod activates or includes `dev`, `local`, `test`, `demo`, `sample`, or `sandbox` profiles
- security auto-configuration excluded via prod config

Medium:
- `spring.jpa.hibernate.ddl-auto=update`
- `spring.jpa.generate-ddl=true`
- `spring.jpa.show-sql=true` or Hibernate SQL/bind logging at `DEBUG`/`TRACE`
- `management.endpoint.health.show-details=always`
- `server.error.include-stacktrace=always`
- `server.error.include-message=always`
- `server.error.include-binding-errors=always`
- `server.error.include-exception=true`
- `logging.level.root=DEBUG` or `TRACE`
- devtools on the production runtime path
- `import.sql` or demo seed data active in prod
- broad CORS in prod
- conflicting or unclear prod profile activation
- `spring.config.import=optional:` for Config Server, Vault, config tree, or other required prod config
- `spring.jpa.open-in-view=true` explicitly set for a traffic-serving API
- migration tooling disabled in prod with no separate migration path (`spring.flyway.enabled=false`, `spring.liquibase.enabled=false`)
- risky migration escape hatches (`spring.flyway.baseline-on-migrate=true`, `spring.liquibase.clear-checksums=true`)
- session cookies explicitly not secure or not HTTP-only in an HTTPS app
- Swagger/OpenAPI/GraphiQL/dev UI enabled by prod config on a public surface
- prod dependencies pointing at localhost, test hosts, or non-prod queues/topics

Low:
- duplicated env config
- too many profiles with unclear ownership
- inconsistent secret/env naming
- prod config spread across many places with no obvious source of truth
- no graceful shutdown for an orchestrated web service (`server.shutdown` absent or `immediate`)
- `spring.main.lazy-initialization=true`
- `spring.main.allow-bean-definition-overriding=true`
- forwarded headers disabled behind a proxy/TLS terminator (`server.forward-headers-strategy=none`)
- missing or disabled health probes/metrics where deployment expects them

Use deployment context before escalating:
- runtime-only env vars
- Config Server / Vault / secret manager injection
- ingress or load-balancer TLS termination
- custom security filters around actuator
- one-time migration cutovers (`baseline-on-migrate`, `drop-first`, checksum reset)
- private admin networks for actuator, Swagger, GraphiQL, or dev UI
