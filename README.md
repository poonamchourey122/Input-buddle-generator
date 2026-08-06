# Generation Kit

A task factory: `recipe (family) + difficulty (tier) + seed → a finished, validated
Harbor task` that runs on `Terminal_2.0_Harbor_Harness`.

Full documentation: see **[GENERATION_KIT_GUIDE.md](GENERATION_KIT_GUIDE.md)**.

## Quickstart
```bash
cd generation-kit
python3.12 kit.py list-families                                  # 8 recipes across 7 domains
python3.12 kit.py generate --family repair-cipher --tier hard --n 5
python3.12 kit.py validate output/tasks/repair-cipher-h001
```

Finished tasks land in `output/tasks/<task-id>/`. Copy one into the harness
`Tasks_INPUT/` and run `./run_task.sh Tasks_INPUT/<task-id> oracle` (expect reward 1.0).

## Bulk generation
`--n N` emits N seeded variants in one call (each a different held-out instance):
```bash
python3.12 kit.py generate --family repair-solver --tier hard --n 500 --seed-start 1
```
