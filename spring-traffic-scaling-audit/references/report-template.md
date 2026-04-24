# Spring Traffic Scaling Audit Template

## Scope

- Service:
- Spring stack:
- Environment:
- Endpoints:
- Audit mode: static estimate / measured
- Test status: service not running / measured / planned
- Confidence:

## Web Stack Failure Mode

- Stack: MVC / WebFlux / mixed / unknown
- Primary static risk:
- Evidence:

## Traffic Model

| Flow | Method/path | Mix % | Payload | Auth/data notes |
| --- | --- | ---: | --- | --- |

| Profile | Target | Duration | Notes |
| --- | --- | --- | --- |
| Baseline | 1 TPS |  |  |
| Log ramp | 1 -> ... TPS |  |  |
| Burst |  |  |  |
| Soak |  |  | optional |

## Resource Envelope

- Instances:
- CPU request/limit:
- Memory request/limit:
- Heap flags:
- GC:
- Autoscaling:
- Server/thread config:
- DB/client/executor pools:

## Memory Retention

| Phase | Heap after GC | RSS/container memory | Allocation rate | GC pause | Threads | Open conns | Queue/cache size | Returned to baseline? |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline |  |  |  |  |  |  |  |  |
| peak |  |  |  |  |  |  |  |  |
| post-cooldown |  |  |  |  |  |  |  |  |

Retention suspects:
- 

## Connection Pools

| Pool/dependency | Type | Max | Pending queue/timeout | Connect timeout | Read/response timeout | Idle/lifetime | Shared? | Saturation evidence |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
|  | HTTP/DB/broker/executor |  |  |  |  |  |  |  |

## Dependency Statistics

| Direction | Dependency | Endpoint/flow | State | p50/p95/p99 | Acquire/connect/read/response timeout | Error/timeout rate | Quota/rate limit | Retry/backoff/bulkhead | Pool | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| upstream |  |  | normal/degraded/burst |  |  |  |  |  |  |  |
| downstream |  |  | normal/degraded/timeout |  |  |  |  |  |  |  |

## Orchestration Timeout Checks

| Flow | Inbound caller timeout/SLO | Timed-out branch | Branch timeout budget | Sibling branches | Join/fallback behavior | Cancellation cleanup | Shared pool impact | Caller result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | acquire + connect + read + retries + fallback |  |  |  |  |  |

Derived dependency checks:
- Downstream timeout budget:
- Inbound caller budget fit:
- Estimated in-flight downstream calls at peak:
- Estimated in-flight downstream calls during degraded state:
- Retry amplification risk:
- Pool starvation risk:

## Circuit Breakers

| Dependency/flow | Library/config | Timeout/slow-call threshold | Failure threshold | Bulkhead/rate limiter | Fallback | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | Resilience4j/Spring Cloud CircuitBreaker/none |  |  |  |  |  |  |

## Scaling Results or Estimates

| Target TPS | Achieved TPS or estimate | p50 | p95 | p99 | Errors | CPU | RSS | Heap after GC | Alloc rate | GC pause | Pool wait | Downstream p99 | Evidence basis | Notes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |

## Burst Results or Estimates

| Burst | Accepted estimate/result | Rejected/throttled estimate/result | p99 | Recovery time | Bottleneck | Graceful? | Evidence basis |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |

## Bottlenecks

Confirmed:
- 

Likely:
- 

## Capacity Estimate

- Estimated max sustainable TPS:
- Estimated safe operating TPS:
- Estimated burst tolerance:
- Confidence:

## Gaps

- 

## Fix Next

1. 
2. 
3. 
