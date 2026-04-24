# Risk Checks

Load this when reviewing bottlenecks, timeouts, pools, or memory retention.

## Measurement Quality

- Load test reports virtual users, not achieved TPS.
- Average latency is used without p95/p99.
- CPU is low but latency climbs: likely pool, lock, downstream, DB, or queue bottleneck.
- Static audit output presents capacity as measured instead of estimated.

## MVC vs WebFlux

- MVC: slow downstream calls hold servlet/request threads until timeout.
- MVC: Tomcat/Jetty/Undertow max threads, accept queue, executor queues, and Hikari/HTTP pools can saturate before CPU.
- MVC: retries can multiply blocking thread occupancy.
- WebFlux: blocking calls on event loops (`block()`, JDBC, file I/O, sleeps, synchronous clients) can stall unrelated requests.
- WebFlux: boundedElastic or custom schedulers can saturate when blocking work is offloaded.
- WebFlux: missing backpressure or unbounded buffering can turn burst traffic into memory growth.
- WebFlux: Netty connection pool pending-acquire limits/timeouts can become the real bottleneck.

## Downstream Timeouts and Orchestration

- Downstream p99 approaches or exceeds outbound timeout.
- Downstream call has no explicit timeout.
- Total retry budget can outlive inbound caller timeout.
- Degraded downstream latency turns normal TPS into high in-flight concurrency.
- One timed-out branch in a fan-out/orchestrated call blocks the whole response past caller budget.
- Timed-out branch keeps running after cancellation or fallback.
- Retry amplification during timeout states exceeds latency/error budget.
- Downstream quota is below planned upstream burst.

## Circuit Breakers and Guards

- Remote dependency has retries/timeouts but no circuit breaker or bulkhead.
- Circuit breaker is present but timeout budget is longer than caller timeout.
- Resilience4j/Spring Cloud CircuitBreaker config exists but controller path does not use it.
- Circuit breaker opens only after too many slow calls for expected burst size.
- Fallback path calls another slow dependency or allocates/queues unbounded work.
- Bulkhead/thread-pool isolation is absent for a high-latency or flaky downstream.
- Retry and circuit breaker ordering amplifies traffic instead of shedding load.

## Pools

- Shared HTTP/DB pool lets one bad downstream starve unrelated work.
- Pending-acquire timeout is missing or longer than request timeout.
- Pool wait rises while CPU is available.
- Active connections sit near max under normal traffic.
- Per-route HTTP limits are lower than expected fan-out concurrency.

## Memory Retention

- Heap after GC trends upward during steady load or does not return after cooldown.
- RSS grows while heap is stable: suspect direct/native memory, thread stacks, mmap, TLS buffers, or container accounting.
- Thread count, open connections, queue depth, cache entries, or high-cardinality metrics grow without returning after traffic drops.
- GC pause or allocation rate rises sharply at higher TPS.
- Container memory limit is too close to heap max for native/non-heap headroom.
