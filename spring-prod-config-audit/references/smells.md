# Spring Prod Smells

Read this only when the script output needs interpretation.

High:
- plaintext prod secrets in repo
- `spring.jpa.hibernate.ddl-auto=create`
- `spring.jpa.hibernate.ddl-auto=create-drop`
- `spring.h2.console.enabled=true`
- `management.endpoints.web.exposure.include=*`
- sensitive actuator endpoints enabled on a public surface

Medium:
- `spring.jpa.hibernate.ddl-auto=update`
- `management.endpoint.health.show-details=always`
- `logging.level.root=DEBUG` or `TRACE`
- devtools on the production runtime path
- `import.sql` or demo seed data active in prod
- broad CORS in prod
- conflicting or unclear prod profile activation

Low:
- duplicated env config
- too many profiles with unclear ownership
- inconsistent secret/env naming
- prod config spread across many places with no obvious source of truth

Use deployment context before escalating:
- runtime-only env vars
- Config Server / Vault / secret manager injection
- ingress or load-balancer TLS termination
- custom security filters around actuator
