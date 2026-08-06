# Generation Kit — convenience runner.
# Usage examples:
#   make list
#   make generate FAMILY=fix-makefile TIER=medium N=1
#   make validate
#   make oracle TASK=fix-makefile-m001
#   make nop    TASK=fix-makefile-m001
#   make all-tiers FAMILY=fix-nginx-config
#   make clean

PY      ?= python3.12
OUT     ?= output
FAMILY  ?= fix-nginx-config
TIER    ?= medium
N       ?= 1
SEED    ?= 1
TASK    ?=

.PHONY: help list list-families list-tiers list-categories plan \
        generate all-tiers validate oracle nop clean

help:
	@echo "Targets:"
	@echo "  list                 list families, tiers, categories"
	@echo "  generate             FAMILY=<f> TIER=<t> N=<k> SEED=<s>"
	@echo "  all-tiers            FAMILY=<f>  (generate medium/hard/expert)"
	@echo "  validate             run the 27 gates over $(OUT)/tasks/"
	@echo "  oracle / nop         TASK=<task-id>  (run on harbor)"
	@echo "  clean                remove generated output"

list: list-families list-tiers list-categories

list-families:
	@$(PY) kit.py list-families

list-tiers:
	@$(PY) kit.py list-tiers

list-categories:
	@$(PY) kit.py list-categories

plan:
	@$(PY) kit.py plan --n $(N)

generate:
	@$(PY) kit.py generate --family $(FAMILY) --tier $(TIER) --n $(N) --seed-start $(SEED) --out $(OUT) --overwrite

all-tiers:
	@for t in medium hard expert; do \
		$(PY) kit.py generate --family $(FAMILY) --tier $$t --n 1 --seed-start 1 --out $(OUT) --overwrite; \
	done

validate:
	@$(PY) kit.py validate $(OUT)/tasks/

oracle:
	@test -n "$(TASK)" || { echo "set TASK=<task-id>"; exit 2; }
	harbor run -p $(OUT)/tasks/$(TASK) --agent oracle -n 1

nop:
	@test -n "$(TASK)" || { echo "set TASK=<task-id>"; exit 2; }
	harbor run -p $(OUT)/tasks/$(TASK) --agent nop -n 1

clean:
	@rm -rf $(OUT)/tasks/* jobs/2* trials/2* 2>/dev/null; \
	find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null; \
	echo "cleaned"
