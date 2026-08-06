# Hard Tasks — generated bundles + harness runs

The two hardest tasks the generation kit produces, with their **input bundles**
and the **harness run outputs** (real `claude-code` / `claude-opus-4-8` agent +
`claude-sonnet-4-6` LLM judge).

## Layout
```
HARD_TASKS/
├── input-tasks/                         # the generated task bundles (what the harness runs)
│   ├── optimize-rangedistinct-h001/
│   └── recover-codec-h001/
└── harness-output/                      # the run results for each
    ├── rangedistinct-check/  <trial>/   # report.json, agent/trajectory.json, judge_response.txt, verifier/*
    └── recover-codec-check/  <trial>/
```

## Results (measured on the harness, opus-4-8)

| task | domain | test% | rubric% | final | is it hard? |
|---|---|---|---|---|---|
| **optimize-rangedistinct-h001** | Software / Algorithms | 100 | 57.14 | **78.57** | **Yes — genuinely hard** |
| recover-codec-h001 | Security / Reverse-eng | 100 | 100 | 100 | hard for weaker solvers; opus solved it |

## Why `optimize-rangedistinct` is the genuinely hard one
It is a **performance-gated** task, not a spec-transcription task:
- The shipped `solve(array, queries)` (count distinct values in a range) is **correct
  but O(n·q)**. The verifier runs the agent's program on **150k–200k** held-out inputs
  under a **hard wall-clock budget** (subprocess timeout). A slow solution **times out
  and fails** — correctness alone is not enough.
- Measured: a **correct-but-naive** solution scores **0.333** (fails both perf tests);
  the reference (offline Fenwick-tree / Mo's algorithm) scores **1.0**.
- Even **opus** landed at **final 78.57** — it wrote a correct fast algorithm (test 100%)
  but the judge docked the rubric to 57% for *claiming it was fast without testing on a
  large input* and *not verifying complexity* (the negative process rubric items).

This is the reliable difficulty lever: **a hard time budget makes "correct" insufficient**
and forces the right algorithm, while the process-rubric catches unverified work.

## Why the other tasks (and `recover-codec`) aren't hard for opus
The 9 "moderate" families and `recover-codec` all get **test = 100%** from opus:
they either fully specify the algorithm (opus transcribes it) or, for reverse-engineering,
opus is strong enough to infer the scheme. On the harness's *own* hardest task
(`qtm-format-recovery`) opus also scores 100% × 3. Making the **deterministic** score fail
opus is a capability wall; the two things that move it are **performance gates** and
**process rubrics**.

## To re-run either
```bash
cp -R input-tasks/optimize-rangedistinct-h001 <harness>/Tasks_INPUT/
cd <harness>
./scripts/run-with-subscription.sh --path "$PWD/Tasks_INPUT/optimize-rangedistinct-h001" \
  --env docker --n-attempts 1 --judge-with -o Output --job-name rangedistinct-run
```
