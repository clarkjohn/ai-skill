---
name: spring-traffic-scaling-audit
description: Static/readiness audit of a Spring or Spring Boot microservice for traffic scaling and burst risk without requiring the service to be running. Use when reviewing REST/WebFlux controllers, MVC vs WebFlux failure modes, estimated TPS capacity, downstream timeouts, circuit breakers, JVM CPU/heap/memory, thread/connection pools, upstream/downstream API constraints, autoscaling, and production traffic growth risk.
---

# Spring Traffic Scaling Audit

Purpose: statically audit how a Spring microservice is likely to scale from `1 TPS` through log ramps and bursts, then estimate the first CPU, memory, pool, or dependency limit.

## Rules

- Default to service-not-running static/readiness audit. Treat TPS, burst tolerance, saturation, and memory behavior as `estimated` unless measured evidence is supplied.
- Do not run load against production unless explicitly approved with blast-radius limits.
- If asked for validation, design a test plan using the repo's existing load-test tool first. Do not add a bespoke tool unless asked.
- Use arrival-rate/open-model tests for TPS capacity.
- Prefer p95/p99, error rate, saturation, recovery, and post-cooldown memory over averages.
- Ask for downstream latency/timeout states before a serious capacity estimate. Include acquire/connect/read/response timeouts, retry/backoff, circuit-breaker, fallback, quotas, and degraded/timeout states.
- In static mode, describe capacity, burst, memory, and pool behavior as estimates or risks, not measured results.
- Separate `confirmed bottleneck`, `likely bottleneck`, and `missing evidence`.

## Workflow

1. Map the path
- Controller, request mix, MVC vs WebFlux, filters/auth, DB/cache/broker work, outbound APIs, async boundaries.
- Classify failure mode: MVC usually fails by servlet/request threads, queues, blocking calls, and pools; WebFlux usually fails by event-loop blocking, missing backpressure, scheduler starvation, and reactive client pool pressure.
- For fan-out/orchestrated calls: branches, joins, timeouts, cancellation, fallback, partial failure.

2. Capture limits
- Instances, CPU/memory requests and limits, heap flags, GC, autoscaling, server threads.
- Hikari/HTTP/broker/executor pools: max, pending acquire timeout, connect/read/response timeout, idle/lifetime, per-route limits, shared pools.
- Memory retention: heap after GC, RSS/native/direct memory, metaspace/classes, threads, open connections, queues, caches.

3. Build dependency and timeout model
- Upstream: request mix, concurrency, burst shape, retries, timeout, growth.
- Downstream: owner, p50/p95/p99, timeout state, error/timeout rate, quota, retries, payload, pool.
- Timeout budget: sequential calls sum; fan-out uses max branch budget plus join/fallback overhead. Compare to inbound caller timeout and SLO.
- Detect circuit breakers and related guards by code/config/dependency scan: Resilience4j, Spring Cloud CircuitBreaker, TimeLimiter, Bulkhead, Retry, RateLimiter, fallback methods, and config thresholds. If absent around slow/remote dependencies, call it out.

4. Review or design tests
- Baseline at `1 TPS`; ramp `1, 2, 5, 10, 20, 50, 100, 200, 500, 1000 TPS` as appropriate.
- Burst from baseline or peak; include soak when memory retention matters.
- Read [references/load-profiles.md](references/load-profiles.md) only when writing a detailed plan.

5. Analyze
- If measured evidence exists, track target/achieved TPS, concurrency, p95/p99, errors, CPU, RSS, heap after GC, allocation rate, GC pause, threads, pool wait, downstream p95/p99.
- Apply downstream states: compare p95/p99 to timeout, estimate in-flight calls as `TPS * downstream latency`, flag retry amplification.
- For orchestrated calls, model one downstream timing out while sibling calls are normal; recommend a targeted timeout test if validation is needed.
- Estimate first saturation signal and max sustainable/safe operating TPS. Label estimates clearly.
- Read [references/risk-checks.md](references/risk-checks.md) when looking for failure modes.

## Output

1. `Scope`
2. `Traffic model`
3. `Resource envelope`
4. `Dependency statistics`
5. `Scaling results`
6. `Burst results`
7. `Bottlenecks`
8. `Capacity estimate`
9. `Gaps`
10. `Fix next`

Use [references/report-template.md](references/report-template.md) only when a full table report is useful.
