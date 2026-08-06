"""Difficulty knobs, tier profiles, and per-tier [reward]-block defaults.

All 5 tiers ship to anubis-harness (Anubis wants a full pyramid, per
``anubis-local/requirements/project.md`` \u00a75.1). The tier lattice sets
design defaults; the observed pass_rate from calibration pilots is what
actually pins a tier per \u00a75.3.6's stratified schedule (Expert/Hard 8 trials,
Medium 4, Easy/Trivial 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Precision = Literal["low", "medium", "high"]
Strictness = Literal["loose", "medium", "strict"]
StartState = Literal["clean", "partial", "polluted"]
Discovery = Literal["none", "low", "medium", "high"]
Tier = Literal["trivial", "easy", "medium", "hard", "expert"]


@dataclass(frozen=True)
class KnobValues:
    instruction_precision: Precision
    distractors: int
    coupled_subgoals: int
    step_budget: int
    test_strictness: Strictness
    starting_state: StartState
    env_discovery_cost: Discovery
    time_limit_sec: int
    verifier_timeout_sec: int
    calibration_trials: int
    expert_time_str: str
    junior_time_str: str
    turns_expected: int
    tokens_expected: int
    pass_at_8_band: tuple[float, float]
    deterministic_alpha: float

    def to_dict(self) -> dict:
        return {
            "instruction_precision": self.instruction_precision,
            "distractors": self.distractors,
            "coupled_subgoals": self.coupled_subgoals,
            "step_budget": self.step_budget,
            "test_strictness": self.test_strictness,
            "starting_state": self.starting_state,
            "env_discovery_cost": self.env_discovery_cost,
            "time_limit_sec": self.time_limit_sec,
            "verifier_timeout_sec": self.verifier_timeout_sec,
            "calibration_trials": self.calibration_trials,
            "expert_time_str": self.expert_time_str,
            "junior_time_str": self.junior_time_str,
            "turns_expected": self.turns_expected,
            "tokens_expected": self.tokens_expected,
            "pass_at_8_band": list(self.pass_at_8_band),
            "deterministic_alpha": self.deterministic_alpha,
        }


TIER_PROFILES: dict[Tier, KnobValues] = {
    "trivial": KnobValues(
        instruction_precision="high",
        distractors=0,
        coupled_subgoals=1,
        step_budget=100,
        test_strictness="loose",
        starting_state="clean",
        env_discovery_cost="none",
        time_limit_sec=600,
        verifier_timeout_sec=300,
        calibration_trials=2,
        expert_time_str="<15 minutes",
        junior_time_str="<30 minutes",
        turns_expected=2,
        tokens_expected=8000,
        pass_at_8_band=(0.875, 1.0),
        deterministic_alpha=1.0,
    ),
    "easy": KnobValues(
        instruction_precision="high",
        distractors=1,
        coupled_subgoals=1,
        step_budget=80,
        test_strictness="loose",
        starting_state="clean",
        env_discovery_cost="low",
        time_limit_sec=900,
        verifier_timeout_sec=300,
        calibration_trials=2,
        expert_time_str="<30 minutes",
        junior_time_str="30 minutes - 2 hours",
        turns_expected=3,
        tokens_expected=12000,
        pass_at_8_band=(0.50, 0.875),
        deterministic_alpha=1.0,
    ),
    "medium": KnobValues(
        instruction_precision="medium",
        distractors=2,
        coupled_subgoals=2,
        step_budget=60,
        test_strictness="medium",
        starting_state="partial",
        env_discovery_cost="medium",
        time_limit_sec=1800,
        verifier_timeout_sec=600,
        calibration_trials=4,
        expert_time_str="30 minutes - 1 hour",
        junior_time_str="2 - 4 hours",
        turns_expected=7,
        tokens_expected=28000,
        pass_at_8_band=(0.375, 0.50),
        deterministic_alpha=0.8,
    ),
    "hard": KnobValues(
        instruction_precision="low",
        distractors=3,
        coupled_subgoals=3,
        step_budget=40,
        test_strictness="strict",
        starting_state="partial",
        env_discovery_cost="high",
        time_limit_sec=7200,
        verifier_timeout_sec=900,
        calibration_trials=8,
        expert_time_str="1 - 2 hours",
        junior_time_str="4 - 8 hours",
        turns_expected=15,
        tokens_expected=55000,
        pass_at_8_band=(0.25, 0.375),
        deterministic_alpha=0.7,
    ),
    "expert": KnobValues(
        instruction_precision="low",
        distractors=4,
        coupled_subgoals=4,
        step_budget=30,
        test_strictness="strict",
        starting_state="polluted",
        env_discovery_cost="high",
        time_limit_sec=7200,
        verifier_timeout_sec=1800,
        calibration_trials=8,
        expert_time_str="2 - 4 hours",
        junior_time_str="1 - 2 days",
        turns_expected=25,
        tokens_expected=100000,
        pass_at_8_band=(0.0, 0.25),
        deterministic_alpha=0.6,
    ),
}


TIER_MIX_TARGET: dict[Tier, float] = {
    "trivial": 0.05,
    "easy":    0.20,
    "medium":  0.40,
    "hard":    0.25,
    "expert":  0.10,
}

TIER_COUNT_TARGET: dict[Tier, int] = {
    "trivial":   500,
    "easy":    2_000,
    "medium":  4_000,
    "hard":    2_500,
    "expert":  1_000,
}


HARD_TIME_LIMIT_CAP_SEC = 18000
FAMILY_SIZE_CAP = 12


def load_tier(tier: str) -> KnobValues:
    if tier not in TIER_PROFILES:
        raise ValueError(
            f"unknown tier {tier!r}; must be one of: {list(TIER_PROFILES)}"
        )
    return TIER_PROFILES[tier]


def plan_tier_distribution(total: int) -> dict[Tier, int]:
    plan = {t: round(total * pct) for t, pct in TIER_MIX_TARGET.items()}
    diff = total - sum(plan.values())
    if diff != 0:
        plan["medium"] += diff
    return plan
