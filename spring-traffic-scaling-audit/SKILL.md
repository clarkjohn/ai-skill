---
name: spring-traffic-scaling-audit
description: Audit a Spring or Spring Boot microservice for traffic scaling and burst readiness. Use when reviewing REST/WebFlux controllers, load-test plans/results, capacity limits, TPS ramps, burst traffic behavior, JVM CPU/heap/memory, thread/connection pools, downstream or upstream API constraints, autoscaling, and production traffic growth risk.
---

# Spring Traffic Scaling Audit

Purpose: audit how a Spring microservice scales from `1 TPS` through log ramps and bursts, then identify the first CPU, memory, pool, or dependency limit.

## Rules

- Static/readiness audit does not require the service running. Measured TPS, burst recovery, CPU, heap, GC, and pool saturation require a safe test environment.
- Do not run load against production unless explicitly approved with blast-radius limits.
- Use the repo's existing load-test tool first. If none exists, recommend one; do not add a bespoke tool unless asked.
- Use arrival-rate/open-model tests for TPS capacity.
- Prefer p95/p99, error rate, saturation, recovery, and post-cooldown memory over averages.
- Ask for downstream latency/timeout states before a serious capacity estimate. Include acquire/connect/read/response timeouts, retry/backoff, circuit-breaker, fallback, quotas, and degraded/timeout states.
- Separate `confirmed bottleneck`, `likely bottleneck`, and `missing evidence`.

## Workflow

1. Map the path
- Controller, request mix, MVC vs WebFlux, filters/auth, DB/cache/broker work, outbound APIs, async boundaries.
- For fan-out/orchestrated calls: branches, joins, timeouts, cancellation, fallback, partial failure.

2. Capture limits
- Instances, CPU/memory requests and limits, heap flags, GC, autoscaling, server threads.
- Hikari/HTTP/broker/executor pools: max, pending acquire timeout, connect/read/response timeout, idle/lifetime, per-route limits, shared pools.
- Memory retention: heap after GC, RSS/native/direct memory, metaspace/classes, threads, open connections, queues, caches.

3. Build dependency and timeout model
- Upstream: request mix, concurrency, burst shape, retries, timeout, growth.
- Downstream: owner, p50/p95/p99, timeout state, error/timeout rate, quota, retries, payload, pool.
- Timeout budget: sequential calls sum; fan-out uses max branch budget plus join/fallback overhead. Compare to inbound caller timeout and SLO.

4. Review or design tests
- Baseline at `1 TPS`; ramp `1, 2, 5, 10, 20, 50, 100, 200, 500, 1000 TPS` as appropriate.
- Burst from baseline or peak; include soak when memory retention matters.
- Read [references/load-profiles.md](references/load-profiles.md) only when writing a detailed plan.

5. Analyze
- Track target/achieved TPS, concurrency, p95/p99, errors, CPU, RSS, heap after GC, allocation rate, GC pause, threads, pool wait, downstream p95/p99.
- Apply downstream states: compare p95/p99 to timeout, estimate in-flight calls as `TPS * downstream latency`, flag retry amplification.
- For orchestrated calls, test one downstream timing out while sibling calls are normal.
- Find first saturation signal and estimate max sustainable TPS plus safe operating TPS.
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
