"""Hybrid taxonomy: frontier-bench 7 domains + Anubis 3 sub-types + language axis.

The emitted bundle format follows frontier-bench conventions (task.toml,
environment/Dockerfile, tests/Dockerfile separate verifier, cheat/) but runs
on anubis-harness (terminal-bench-canary, WORKDIR /workspace).

Categories = frontier-bench's 7 domains (`docs/TAXONOMY.md`).
Sub-types  = Anubis's 3 closed-set task surfaces (`TAXONOMY.md`).
Languages  = per Anubis `requirements/project.md` \u00a72.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Domain:
    name: str
    description: str
    subcategories: tuple[str, ...]
    example_tasks: tuple[str, ...] = field(default_factory=tuple)


DOMAINS: dict[str, Domain] = {
    "Science": Domain(
        name="Science",
        description="Natural sciences, mathematics, and engineering science.",
        subcategories=("Biology", "Chemistry", "Physics", "Earth", "Robotics", "Math", "Linguistics"),
        example_tasks=("atrx-vep-crispr", "lean-midpoint-proof", "sound-change-cascade"),
    ),
    "Software": Domain(
        name="Software",
        description="Software engineering where the domain *is* software.",
        subcategories=("Algorithms", "Systems", "Databases", "Data engineering", "Frontend", "Languages"),
        example_tasks=("data-anonymization", "session-window-debug", "wal-recovery-ordering"),
    ),
    "ML": Domain(
        name="ML",
        description="Machine-learning training, serving, evaluation, infrastructure.",
        subcategories=("Training", "Inference", "Evaluation", "Kernels"),
        example_tasks=("batched-eval-parity", "vllm-deepseek-streaming", "fp8-rmsnorm-gemm"),
    ),
    "Operations": Domain(
        name="Operations",
        description="Business, financial, and operational domain reasoning.",
        subcategories=("Finance", "Logistics", "Supply chain", "Claims", "Compliance", "Marketing"),
        example_tasks=("fin-saccr-rwa", "cargo-flight-dispatch", "erp-procurement-planning"),
    ),
    "Security": Domain(
        name="Security",
        description="Offensive and defensive security.",
        subcategories=("Cryptography", "Reverse engineering", "Forensics", "AppSec"),
        example_tasks=("interleaved-vigenere", "uefi-bootkit", "memcached-backdoor"),
    ),
    "Hardware": Domain(
        name="Hardware",
        description="Physical and digital hardware design.",
        subcategories=("CAD", "RTL"),
        example_tasks=("freecad-impeller", "freecad-spring-clip", "retro-console-soc"),
    ),
    "Media": Domain(
        name="Media",
        description="Creative and design work.",
        subcategories=("Music", "Design"),
        example_tasks=("music-harmony", "satb-audio-transcription", "layout-config-recreation"),
    ),
}

VALID_CATEGORIES: tuple[str, ...] = tuple(DOMAINS)


@dataclass(frozen=True)
class SubType:
    slug: str
    name: str
    description: str


SUB_TYPES: dict[str, SubType] = {
    "cli": SubType(
        slug="cli",
        name="CLI",
        description="Command-line tool usage, shell scripting, package management, system administration.",
    ),
    "build-ci-cd": SubType(
        slug="build-ci-cd",
        name="Build / CI/CD",
        description="Compiler invocation, Makefiles, CMake, Bazel, GitHub Actions, Jenkins, GitLab CI.",
    ),
    "container-setup": SubType(
        slug="container-setup",
        name="Container Setup",
        description="Docker, Docker Compose, Podman, container networking, volume management.",
    ),
}

VALID_SUB_TYPES: tuple[str, ...] = tuple(SUB_TYPES)


LANGUAGES: dict[str, float] = {
    "python":     0.30,
    "typescript": 0.125,
    "javascript": 0.125,
    "go":         0.15,
    "java":       0.15,
    "rust":       0.10,
    "other":      0.05,
}

VALID_LANGUAGES: tuple[str, ...] = tuple(LANGUAGES)


def validate_category(name: str) -> Domain:
    if name not in DOMAINS:
        raise ValueError(
            f"unknown category {name!r}; must be one of the 7 domains: "
            f"{', '.join(VALID_CATEGORIES)}."
        )
    return DOMAINS[name]


def validate_subcategory(category: str, subcategory: str) -> list[str]:
    """Empty subcategory is a hard fail; unknown-but-non-empty is a warning."""
    if not subcategory or not subcategory.strip():
        raise ValueError(
            f"subcategory is required and must be non-empty for {category!r}."
        )
    known = set(DOMAINS[category].subcategories) if category in DOMAINS else set()
    if subcategory in known:
        return []
    return [
        f"subcategory {subcategory!r} not in the known list for {category!r} "
        f"({sorted(known)}). Allowed, but flag for taxonomy review."
    ]


def validate_sub_type(sub_type: str) -> SubType:
    if sub_type not in SUB_TYPES:
        raise ValueError(
            f"unknown sub_type {sub_type!r}; must be one of the 3 Anubis sub-types: "
            f"{', '.join(VALID_SUB_TYPES)}."
        )
    return SUB_TYPES[sub_type]


def validate_language(lang: str) -> str:
    if lang not in LANGUAGES:
        raise ValueError(
            f"unknown language {lang!r}; must be one of: {', '.join(VALID_LANGUAGES)}."
        )
    return lang


SUB_TYPE_MIX_TARGET: dict[str, float] = {
    "cli":             0.35,
    "build-ci-cd":     0.35,
    "container-setup": 0.30,
}

DOMAIN_CONCENTRATION_SOFT_CAP = 0.25


def plan_sub_type_distribution(total: int) -> dict[str, int]:
    plan = {st: round(total * pct) for st, pct in SUB_TYPE_MIX_TARGET.items()}
    diff = total - sum(plan.values())
    if diff != 0:
        plan["cli"] += diff
    return plan


def check_domain_concentration(counts: dict[str, int]) -> list[str]:
    total = sum(counts.values())
    if total == 0:
        return []
    warnings = []
    for cat, n in counts.items():
        share = n / total
        if share > DOMAIN_CONCENTRATION_SOFT_CAP:
            warnings.append(
                f"domain {cat!r} is {share:.1%} of the batch ({n}/{total}); "
                f"soft cap is {DOMAIN_CONCENTRATION_SOFT_CAP:.0%}."
            )
    return warnings
