# Risk Checks

Load this when reviewing bottlenecks, timeouts, pools, or memory retention.

## Measurement Quality

- Load test reports virtual users, not achieved TPS.
- Average latency is used without p95/p99.
- CPU is low but latency climbs: likely pool, lock, downstream, DB, or queue bottleneck.

## Downstream Timeouts and Orchestration

- Downstream p99 approaches or exceeds outbound timeout.
- Downstream call has no explicit timeout.
- Total retry budget can outlive inbound caller timeout.
- Degraded downstream latency turns normal TPS into high in-flight concurrency.
- One timed-out branch in a fan-out/orchestrated call blocks the whole response past caller budget.
- Timed-out branch keeps running after cancellation or fallback.
- Retry amplification during timeout states exceeds latency/error budget.
- Downstream quota is below planned upstream burst.

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
