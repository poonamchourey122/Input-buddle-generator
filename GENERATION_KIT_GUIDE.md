# Generation Kit — Simple Guide

This kit is a **task factory**. You give it a *recipe* + a *difficulty* + a *number*,
and it prints out finished, ready-to-run benchmark tasks that plug straight into the
Harbor harness.

```
recipe (family)  +  difficulty (tier)  +  seed number   ─►   one finished task folder
```

---

## 1. Why "families"? (the key idea)

A **family is a recipe for a whole *class* of tasks, not a single task.**

We don't hand-write thousands of tasks one by one. Instead we author **one family**
(e.g. "repair a broken event-time sessionizer") that knows how to stamp out **many
concrete variants**. Each variant is produced from a **seed number**:

- Same family + seed `1` → variant `...-h001` (53 sample events)
- Same family + seed `2` → variant `...-h002` (49 different sample events)
- Same family + seed `3` → variant `...-h003` (57 different sample events)

Every variant tests the **same skill** with the **same tests and rubric**, but the
**data is different each time**. That matters for two reasons:

1. **Scale** — one authored recipe → hundreds of calibrated tasks.
2. **Anti-cheat** — because each variant's grading data is freshly seeded and the
   answer is *held out* (never shown to the agent), an agent can't pass by memorising
   or hardcoding a sample answer. It must implement the *general* rule.

> **Family = the thing you author. Task = the thing you run.** One family makes many tasks.

The 13 families shipped today span **all 7 domains** (every one is a deterministic,
`python:3.12-slim`, held-out-graded repair task with a `cheat/` adversarial oracle;
verified on the harness at oracle=1.0 / cheat<0):

| Family | Domain / Subcategory | What the agent must fix |
|---|---|---|
| `fix-nginx-config` | Software / Systems | broken `nginx.conf` so nginx boots + serves 200 |
| `fix-makefile` | Software / Systems | broken `Makefile` so `make` builds + runs |
| `sessionize-repair` | Software / Systems | broken event-time stream sessionizer (hard) |
| `repair-cipher` | Security / Cryptography | broken interleaved multi-key Vigenère decoder |
| `repair-solver` | Science / Math | broken Gaussian-elimination linear solver |
| `repair-grader` | ML / Evaluation | broken math-answer grader (fraction/decimal normalization) |
| `repair-adjudicator` | Operations / Claims | broken insurance payout rules engine |
| `repair-alu` | Hardware / RTL | broken fixed-width ALU (mod-2^width wrap) |
| `repair-harmony` | Media / Music | broken chord-spelling engine (pitch-class mod 12) |
| `recover-codec` | Security / Reverse engineering | **HARD** — reverse-engineer an undocumented codec from examples (held-out graded) |
| `optimize-rangedistinct` | Software / Algorithms | **HARD** — make a correct-but-quadratic query function pass large inputs under a hard time budget |
| `optimize-primes` | Science / Math | **HARD** — correct-but-trial-division prime counting; must use a sieve to pass millions-scale inputs |
| `optimize-dijkstra` | Operations / Logistics | **HARD** — correct-but-Bellman-Ford shortest paths; must use Dijkstra to pass large graphs |

---

## 2. The pieces of the kit (what does what)

```
generation-kit/
├── kit.py            ← THE ENGINE (the command you run)
├── categories.py     ← the ALLOWED VOCABULARY (domains, sub-types, languages)
├── knobs.py          ← the DIFFICULTY DIALS (5 tiers + their timeouts/targets)
├── validators.py     ← the QUALITY GATES (28 checks; a task must pass all)
├── families/         ← the RECIPES (one file per task class, one per domain)
│   ├── fix_nginx_config.py     (Software/Systems)
│   ├── fix_makefile.py         (Software/Systems)
│   ├── sessionize_repair.py    (Software/Systems)
│   ├── repair_cipher.py        (Security/Cryptography)
│   ├── repair_solver.py        (Science/Math)
│   ├── repair_grader.py        (ML/Evaluation)
│   ├── repair_adjudicator.py   (Operations/Claims)
│   ├── repair_alu.py           (Hardware/RTL)
│   └── repair_harmony.py       (Media/Music)
└── output/tasks/     ← where finished tasks land
```

> The emitted tasks match the harness's own sample tasks (`qtm-format-recovery`,
> `governing-coefficient-recovery`): harbor `schema_version = "1.1"`, workdir `/app`,
> a `weighted_graded` `[reward]` block, and a `cheat/` adversarial oracle on every task.

### `kit.py` — the engine
The only thing you run. It:
1. loads a **family** (recipe) and a **tier** (difficulty),
2. asks the family to build a **bundle** (a plain Python dict describing the task),
3. writes that bundle out as real files (task.toml, instruction.md, Dockerfiles,
   solution, tests…),
4. writes a fixed, self-contained `tests/test.sh` reward runner,
5. runs `validators.py` and refuses to ship a task that fails any gate.

### `categories.py` — the vocabulary
The closed list of allowed **domains** (Science, Software, ML, Operations, Security,
Hardware, Media), their sub-categories, the 3 **sub-types**, and the **languages**.
A family can't invent an off-list category — the kit rejects it. This keeps the whole
benchmark consistently labelled.

### `knobs.py` — the difficulty dials
Defines the 5 **tiers** — `trivial, easy, medium, hard, expert` — and, for each, a
profile: agent timeout, verifier timeout, expected turns/tokens, and the target
pass@8 band. Picking `--tier hard` is how the same recipe gets a 1-hour agent
timeout and strict settings vs. an easy 10-minute one.

### `validators.py` — the quality gates (28 checks)
This is what makes a task **correct, not just correctly-shaped**. Examples of gates:
- every required file exists; `task.toml` parses and has the right schema;
- the anti-training **canary** lines are present in every file;
- `test_weights.json` keys are a **bijection** with the `test_` functions;
- there is **at least one positive weight** (so reward has a denominator);
- `rubric.json` is a **list** in the harness judge format;
- every `test_` function takes **no arguments** (the harness calls `fn()` directly,
  so pytest fixtures would silently break — this gate catches that);
- `test.sh` actually writes `reward.json`; `solve.sh` has a shebang; Dockerfiles
  don't pin `:latest` or leak the solution, etc.

### `families/…` — the recipes
Each family is one Python file exposing:
- constants: `CATEGORY, SUBCATEGORY, SUB_TYPE, LANGUAGE, FAMILY_ID`
- `build_task_id(tier, seed)` → the task's name (e.g. `sessionize-repair-h001`)
- `generate(knobs, seed)` → the **bundle** dict:
  - `instruction` (what the agent reads)
  - `metadata` (author, difficulty/solution/verification explanations, tags…)
  - `agent` (base image + the **broken** starting files the agent must fix)
  - `solution` (`solve_sh` = `cp /solution/<file> /app/<file>` + the reference artifact; must score 1.0)
  - `cheat` (`solve_sh` — an adversarial reward-hack; must score < 0)
  - `verifier` (base image for the isolated grading container)
  - `tests` → `test_output.py` (the checks), `test_weights` (points per check),
    `rubric` (LLM-judge criteria)

---

## 3. How a task is graded (tests **and** rubric)

Two independent layers, on purpose — they must **complement**, not overlap:

**A. Deterministic tests** (`test_output.py` + `test_weights.json`)
`test.sh` imports each `test_` function, runs it, and does:

```
reward = (sum of weights of tests that PASS) / (sum of all POSITIVE weights)
```

- **Positive weights** = points for correct behaviour (e.g. `held_out_streams: +5`).
- **Negative weights** = *cheat traps*. They only "pass" (and subtract) when the
  forbidden behaviour is detected — e.g. `hardcoded_sample: -5` fires only if the
  sample matches but no held-out stream does. An honest bug is **not** punished.

**B. LLM rubric** (`rubric.json`, scored by the harness judge)
A list of criteria the deterministic tests *can't* see — about **method and process**:
event-time reasoning, verifying-before-finishing, and negative criteria that penalise
over-claiming or hardcoding. Positive items add their score; negative items subtract
**only when the judge detects the bad behaviour**.

Reference-style shape (matches the harness's own tasks): **6 rubric items = 4 positive
+ 2 negative**, plus negative-weight test traps.

---

## 4. How to generate (step by step)

**Always run from the kit directory with `python3.12`:**
```bash
cd terminal-tasks-pod/generation-kit
```

**Step 1 — see what you can make**
```bash
python3.12 kit.py list-families     # the 13 recipes (below)
python3.12 kit.py list-tiers        # the 5 difficulty tiers (below)
```

**Step 2 — generate** — pick a `--family` and a `--tier`:
```bash
python3.12 kit.py generate --family <family> --tier <tier> --n <count> --seed-start <n>
```
| flag | meaning |
|---|---|
| `--family` | which recipe → which domain (see table) |
| `--tier` | `trivial \| easy \| medium \| hard \| expert` (sets timeouts/difficulty) |
| `--n` | how many **variants** to make (each a different seed = different held-out data, same skill) |
| `--seed-start` | first seed number (default 1); task ids get `-h001`, `-h002`, … |
| `--out` | output dir (default `./output`) |
| `--overwrite` | regenerate over an existing task dir |

Generation **auto-validates** every task (prints `[ok] <id> (28/28 gates)`), landing in `output/tasks/<task-id>/`.

**The 13 families (one command each covers a whole domain):**
```bash
python3.12 kit.py generate --family fix-nginx-config   --tier hard --n 1   # Software/Systems
python3.12 kit.py generate --family fix-makefile        --tier hard --n 1   # Software/Systems
python3.12 kit.py generate --family sessionize-repair   --tier hard --n 1   # Software/Systems
python3.12 kit.py generate --family repair-cipher       --tier hard --n 1   # Security/Cryptography
python3.12 kit.py generate --family repair-solver       --tier hard --n 1   # Science/Math
python3.12 kit.py generate --family repair-grader       --tier hard --n 1   # ML/Evaluation
python3.12 kit.py generate --family repair-adjudicator  --tier hard --n 1   # Operations/Claims
python3.12 kit.py generate --family repair-alu          --tier hard --n 1   # Hardware/RTL
python3.12 kit.py generate --family repair-harmony      --tier hard --n 1   # Media/Music
python3.12 kit.py generate --family recover-codec       --tier hard --n 1   # Security/Reverse-eng (HARD)
python3.12 kit.py generate --family optimize-rangedistinct --tier hard --n 1 # Software/Algorithms (HARD)
```

**The 5 tiers** (chosen with `--tier`) change the agent/verifier timeouts:
| tier | id suffix | agent timeout | verifier timeout |
|---|---|---|---|
| trivial | `-t001` | 600s | 300s |
| easy | `-e001` | 900s | 300s |
| medium | `-m001` | 1800s | 600s |
| hard | `-h001` | 7200s | 900s |
| expert | `-x001` | 7200s | 1800s |

Every generated task also carries the harness reference profile (matches
`qtm-format-recovery`): `build_timeout_sec = 900`, `cpus = 2`, `memory_mb = 2048`,
`storage_mb = 10240`. The `hard` tier's agent timeout (7200s) matches qtm exactly.

**Step 3 — (optional) re-validate** an existing task against all 28 gates:
```bash
python3.12 kit.py validate output/tasks/repair-cipher-h001
```

**Step 4 — run it on the harness**
```bash
cp -R output/tasks/repair-cipher-h001 ../../Terminal_2.0_Harbor_Harness/Tasks_INPUT/
cd ../../Terminal_2.0_Harbor_Harness
./run_task.sh Tasks_INPUT/repair-cipher-h001 oracle   # reference fix -> reward 1.0
./run_task.sh Tasks_INPUT/repair-cipher-h001 nop      # do-nothing    -> reward ~0
# reward lands in Output/<job>/*/verifier/reward.json
```

---

## 5. What one finished task folder looks like

The kit emits the **harbor-native layout** used by the harness's own sample tasks
(`schema_version = "1.1"`, workdir `/app`, `weighted_graded` reward):

```
sessionize-repair-h001/
├── task.toml                 # harbor schema 1.1: [task]/[metadata]/[verifier]/[agent]/[environment]/[reward]
├── instruction.md            # what the agent reads
├── README.md                 # human summary
├── environment/
│   ├── Dockerfile            # the agent's container (WORKDIR /app)
│   └── data/                 # the BROKEN starting files (+ sample input)
├── solution/                # frontier-bench convention: reference artifact + cp installer
│   ├── solve.sh             # positive_oracle: cp /solution/<file> /app/<file> (must score 1.0)
│   └── <artifact>           # the correct reference file (sessionize.py / Makefile / nginx.conf)
├── cheat/
│   └── solve.sh              # adversarial_oracle: a reward-hack (must score < 0)
└── tests/
    ├── Dockerfile            # the isolated grading container
    ├── test.sh               # self-contained reward runner
    ├── test_output.py        # the checks (with baked, held-out answer key)
    ├── test_weights.json     # points per check (+ negative cheat-traps)
    └── rubric.json           # LLM-judge criteria (4 positive + 2 negative)
```

The `[reward]` block is `weighted_graded`, range `[-1, 1]`, and wires both oracles:

```toml
[reward]
type = "weighted_graded"
min = -1.0
max = 1.0
deterministic = "tests/test_output.py"
weights = "tests/test_weights.json"
rubric = "tests/rubric.json"
positive_oracle = "solution/solve.sh"      # must grade to  1.0
adversarial_oracle = "cheat/solve.sh"      # must grade to  < 0
```

**Golden rules the kit enforces (28 gates):**
- the `positive_oracle` (`solution/solve.sh`) must score **1.0**;
- the `adversarial_oracle` (`cheat/solve.sh`) must score **< 0** (a real reward-hack
  that trips a negative-weight trap — e.g. a fabricated binary, a stripped config, or
  a degenerate/hardcoded output);
- a do-nothing agent scores near **0** (honest bugs are never punished as cheating).
