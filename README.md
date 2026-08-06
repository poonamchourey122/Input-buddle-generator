# Input Bundle Generator (Generation Kit)

A **task factory** for the Harbor / Terminal-Bench harness. You give it a
*recipe (family)* + a *difficulty (tier)* + a *seed*, and it emits a finished,
**validated**, harness-runnable task bundle:

```
recipe (family)  +  tier  +  seed   ─►   output/tasks/<task-id>/   (28/28 gates passed)
```

Every generated task is **harbor-native** — the same shape as the harness's own
sample tasks (`qtm-format-recovery`, `governing-coefficient-recovery`):
`schema_version = "1.1"`, workdir `/app`, a `weighted_graded` `[reward]` block,
a `solution/` positive oracle, a `cheat/` adversarial oracle, and a separate
verifier that writes `/logs/verifier/reward.json`.

> Full documentation: **[GENERATION_KIT_GUIDE.md](GENERATION_KIT_GUIDE.md)**.

---

## The 13 families

**Moderate repair tasks — one per domain (all 7 domains):**

| Family | Domain / Subcategory | The broken artifact the agent must fix |
|---|---|---|
| `fix-nginx-config` | Software / Systems | a broken `nginx.conf` so nginx boots + serves HTTP 200 |
| `fix-makefile` | Software / Systems | a broken `Makefile` so `make` builds + runs |
| `sessionize-repair` | Software / Systems | a broken event-time stream sessionizer (watermark, lateness, bridge, dedup, max-duration) |
| `repair-cipher` | Security / Cryptography | a broken interleaved multi-key Vigenère decoder |
| `repair-solver` | Science / Math | a broken Gaussian-elimination linear solver |
| `repair-grader` | ML / Evaluation | a broken math-answer grader (fraction/decimal normalization) |
| `repair-adjudicator` | Operations / Claims | a broken insurance payout rules engine |
| `repair-alu` | Hardware / RTL | a broken fixed-width ALU (mod-2^width wrap) |
| `repair-harmony` | Media / Music | a broken chord-spelling engine (pitch-class mod 12) |

**Hard tasks (genuinely challenge frontier agents):**

| Family | Domain / Subcategory | Challenge |
|---|---|---|
| `recover-codec` | Security / Reverse engineering | **reverse-engineer** an undocumented codec (varint + zig-zag + resetting predictor) from worked examples; graded on held-out |
| `optimize-rangedistinct` | Software / Algorithms | **perf**: correct-but-O(n·q) range-distinct-count → must be near-linearithmic (Fenwick/Mo's) to pass 150k–200k inputs under a hard time budget |
| `optimize-primes` | Science / Math | **perf**: correct-but-trial-division prime counting → must use a sieve + prefix sums to pass millions-scale inputs |
| `optimize-dijkstra` | Operations / Logistics | **perf**: correct-but-O(V·E) Bellman-Ford shortest paths → must use heap-based Dijkstra to pass 40k–60k-node graphs |

Each family is a deterministic, pure-Python, `python:3.12-slim` task with a held-out
reference verifier, negative-weight cheat-traps, and a 6-item LLM rubric. The perf-gated
hard families are the reliable difficulty lever: a **correct-but-slow** solution **fails**
the time budget (measured: naive scores ~0.33, reference 1.0), forcing the right
algorithm — so correctness alone is not enough.

---

## Prerequisites
- **Python 3.12+** (the kit uses `tomllib`; run everything with `python3.12`).
- No third-party deps for generation (stdlib only). To *run* generated tasks you
  need the Harbor harness + Docker.

---

## Usage

Run everything from the kit directory:
```bash
cd generation-kit
```

**Discover**
```bash
python3.12 kit.py list-families      # the 9 recipes
python3.12 kit.py list-tiers         # the 5 difficulty tiers + timeouts
python3.12 kit.py list-categories    # 7 domains + sub-types + languages
```

**Generate**
```bash
python3.12 kit.py generate --family <family> --tier <tier> --n <count> --seed-start <n>
```
| flag | meaning |
|---|---|
| `--family` | which recipe (→ which domain) |
| `--tier` | `trivial \| easy \| medium \| hard \| expert` (sets agent/verifier timeouts) |
| `--n` | number of variants (each seed = a different puzzle/data) |
| `--seed-start` | first seed (default 1); ids get `-h001`, `-h002`, … |
| `--out` | output dir (default `./output`) |
| `--overwrite` | regenerate over an existing task dir |

Generation **auto-validates** each task (prints `[ok] <id> (28/28 gates)`), writing to
`output/tasks/<task-id>/`.

**Validate** an existing task against all 28 gates:
```bash
python3.12 kit.py validate output/tasks/repair-cipher-h001
```

---

## Bulk generation
`--n N` emits N seeded, non-identical variants in a single call:
```bash
python3.12 kit.py generate --family repair-solver --tier hard --n 500 --seed-start 1
```
To generate across all families and tiers:
```bash
for fam in fix-nginx-config fix-makefile sessionize-repair repair-cipher \
           repair-solver repair-grader repair-adjudicator repair-alu repair-harmony; do
  for tier in easy medium hard; do
    python3.12 kit.py generate --family $fam --tier $tier --n 130 --seed-start 1
  done
done
```

---

## A finished task folder
```
<task-id>/
├── task.toml                 # harbor schema 1.1: [task]/[metadata]/[verifier]/[agent]/[environment]/[reward]
├── instruction.md            # what the agent reads
├── README.md                 # human summary
├── environment/
│   ├── Dockerfile            # agent container (WORKDIR /app, pinned image)
│   └── data/                 # the BROKEN starting file(s) + sample input
├── solution/                 # positive oracle
│   ├── solve.sh              #   cp /solution/<file> /app/<file>   (must score 1.0)
│   └── <artifact>            #   the correct reference file
├── cheat/
│   └── solve.sh              # adversarial oracle: a reward-hack (must score < 0)
└── tests/
    ├── Dockerfile            # isolated verifier container
    ├── test.sh               # self-contained reward runner -> /logs/verifier/reward.json
    ├── test_output.py        # deterministic checks (held-out, reference-compared)
    ├── test_weights.json     # weight per test (+ negative cheat-traps)
    └── rubric.json           # LLM-judge criteria (4 positive + 2 negative)
```

---

## Running a generated task on the harness
```bash
# stage it
cp -R output/tasks/repair-cipher-h001 <harness>/Tasks_INPUT/

# quick deterministic check (verifier only)
cd <harness>
./run_task.sh Tasks_INPUT/repair-cipher-h001 oracle   # reference fix -> reward 1.0
./run_task.sh Tasks_INPUT/repair-cipher-h001 nop      # do-nothing    -> reward ~0

# full agent + LLM judge (report.json + trajectory + pass_summary)
./scripts/run-with-subscription.sh \
  --path "$PWD/Tasks_INPUT/repair-cipher-h001" \
  --env docker --n-attempts 1 --judge-with -o Output --job-name cipher-run
```

---

## The contract every task satisfies (28 gates)
- `solution/solve.sh` (positive oracle) → reward **1.0** (the task is genuinely solvable).
- `cheat/solve.sh` (adversarial oracle) → reward **< 0** (a real reward-hack that trips a
  negative-weight trap — fabricated binary, stripped config, degenerate/hardcoded output).
- a do-nothing agent → **~0** (honest bugs are never punished as cheating).
- plus schema/canary/Dockerfile/weights-bijection/rubric-format/no-fixture-tests checks.

---

## Repository layout
```
kit.py            # the engine (generate / validate / list-* / plan)
categories.py     # closed taxonomy: 7 domains, sub-types, languages
knobs.py          # 5 difficulty tiers + timeouts/targets
validators.py     # the 28 acceptance gates
families/         # the 9 recipes (one file per task class)
GENERATION_KIT_GUIDE.md   # full guide
```

## Notes
- `--tier` sets **timeouts**, not intrinsic difficulty. True difficulty should be
  established by **calibration** (running agents and measuring pass@k), not the label.
- Variety comes from seeded **bug-variants** (each family ships several) × seeded data;
  add more families/subcategories for broader coverage.
