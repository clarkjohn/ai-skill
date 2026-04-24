# Load Profiles

Use these profiles as defaults, then adapt to the service SLO, production traffic shape, and test-environment safety limits.

## Baseline

- Start at `1 TPS`.
- Hold for 5-10 minutes or enough requests to confirm correctness and warm caches/JIT.
- Record baseline CPU, RSS, heap after GC, allocation rate, GC pause, threads, connection pools, downstream latency, and errors.

## Logarithmic Ramp

Default request-rate steps:

| Step | Target TPS | Hold |
| --- | ---: | --- |
| 1 | 1 | 5-10 min |
| 2 | 2 | 5 min |
| 3 | 5 | 5 min |
| 4 | 10 | 5 min |
| 5 | 20 | 5 min |
| 6 | 50 | 5-10 min |
| 7 | 100 | 5-10 min |
| 8 | 200 | 5-10 min |
| 9 | 500 | 10 min |
| 10 | 1000 | 10 min |

Stop or pause when latency/error SLOs fail, downstream safety limits are reached, or resource saturation is obvious.

## Burst

Run burst tests after baseline and at least one stable ramp step.

- Idle-to-burst: `1 TPS -> burst target` for 30-120 seconds.
- Peak-to-burst: `expected peak -> 2x or 3x peak` for 30-120 seconds.
- Repeated burst: 3-5 short spikes separated by cool-down windows.

Measure accepted requests, rejected/throttled requests, p99 tail, queue growth, autoscaler response, recovery time, and downstream impact.

## Soak

Use when memory, GC, or downstream leakage is a concern.

- Hold expected peak for 30-120 minutes.
- Prefer 70-80% of discovered capacity if expected peak is unknown.
- Watch heap after GC, RSS, direct memory, open connections, thread count, queue depth, and downstream error drift.
- After load drops, verify heap after GC, RSS, thread count, connection count, queue depth, and cache sizes return near baseline.
- If heap is stable but RSS rises, inspect native/direct memory, thread stacks, mapped files, TLS buffers, and container memory limits.

## Open vs Closed Model

- Use open/arrival-rate model for TPS capacity: the test generates a target request arrival rate regardless of response time.
- Use closed virtual-user model for workflow realism: users wait for responses before the next action.
- Report achieved TPS either way; target TPS without achieved TPS is weak evidence.
