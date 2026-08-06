# Hard Tasks — the reliable difficulty lever

This folder holds the generation kit's hard tasks (input bundles + harness run
outputs), plus an honest note on what actually makes a task hard for a frontier
agent (measured on `claude-opus-4-8`).

## TL;DR — what is reliably hard, what is not
| lever | family | correct-but-imperfect solver | opus |
|---|---|---|---|
| **Performance gate** (the reliable one) | `optimize-rangedistinct`, `optimize-primes`, `optimize-dijkstra` | **~0.33** (correct-but-slow → fails the time budget) | test 100, but a correct solution that isn't fast enough **fails** |
| Reverse-engineering | `recover-codec` | ~0.47 (decode ok, byte-exact encoder imperfect) | **100** — opus solves it |

**The performance gate is the only *generatable*, non-noisy way to make a
deterministic score fail:** a correct solution that uses the wrong algorithm
(too slow) fails the hard wall-clock budget, regardless of how capable the agent
is. Reverse-engineering only fails frontier agents at hand-crafted, telemetry-
level complexity (many hidden modes + no hints) — hard to produce parametrically;
at the complexity a generator emits, opus solves it.

## Layout
```
HARD_TASKS/
├── input-tasks/                        # generated task bundles
│   ├── optimize-rangedistinct-h001/    # Software/Algorithms — Fenwick/Mo's (PERF)
│   ├── optimize-primes-h001/           # Science/Math — sieve (PERF)
│   ├── optimize-dijkstra-h001/         # Operations/Logistics — Dijkstra (PERF)
│   └── recover-codec-h001/             # Security/Reverse-eng — byte-exact codec
└── harness-output/                     # real opus-4-8 + sonnet-judge runs
    ├── rangedistinct-check/            # opus: test 100 / rubric 57 / final 78.57
    └── recover-codec-check/            # opus: test 100 / rubric 100 / final 100
```

## The 3 perf-gated hard families (official hard set)
Each ships a **correct but slow** function and grades it by running the agent's
program on large held-out inputs under a **strict per-input time budget** (the
verifier runs it in a subprocess with a timeout; a slow solution raises
`TimeoutExpired` and fails). Passing requires the right algorithm.

| family | slow (shipped) | required | measured (harness) |
|---|---|---|---|
| `optimize-rangedistinct` | O(n·q) per-query scan | offline Fenwick tree | oracle 1.0, naive **0.333**, opus final **78.57** |
| `optimize-primes` | trial division | sieve + prefix sums | oracle 1.0, naive **0.333** |
| `optimize-dijkstra` | Bellman-Ford O(V·E) | heap Dijkstra O(E log V) | oracle 1.0, naive times out |

`optimize-rangedistinct` is the flagship: opus wrote a correct fast algorithm
(test 100) but the judge docked it to **rubric 57 / final 78.57** for shipping
without testing on a large input.

## `recover-codec` (reverse-engineering)
Reverse-engineer an undocumented codec (header + varint + zig-zag + order-dependent
resetting predictor) from examples, implementing a **byte-exact decode AND encode**
that generalize to held-out `(stride, order)`. Measured: oracle 1.0, nop −0.31,
cheat −0.16, and a *decode-correct-but-encoder-imperfect* solver scores **0.47**.
Opus, however, solves it 100% — 2 parameters + instruction hints were not enough to
defeat it. Kept as a solid reverse-engineering task for weaker/sub-opus agents,
**not** an opus-stumper.

## Honest conclusion
- To make a *correct* solution fail on the **deterministic** axis, use a
  **performance gate**. It is reproducible across seeds and does not rely on the
  agent "not noticing" something.
- To make opus fail a **reverse-engineering** task you need real telemetry-level
  complexity (many interacting hidden modes, per-entity selectors, a genuinely
  redacted spec) — a large hand-authored artifact, not a parametric generator.
- The kit's other 9 families are correct, calibratable, moderate-difficulty tasks
  (great for RL data and sub-opus benchmarking); opus caps them at test 100.

## Re-run any of these
```bash
cp -R input-tasks/optimize-primes-h001 <harness>/Tasks_INPUT/
cd <harness>
./scripts/run-with-subscription.sh --path "$PWD/Tasks_INPUT/optimize-primes-h001" \
  --env docker --n-attempts 1 --judge-with -o Output --job-name primes-run
```
