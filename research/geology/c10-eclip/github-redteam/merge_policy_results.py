#!/usr/bin/env python3
"""Validate and merge deterministic scenario shards from policy_sim.py."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Sequence


SCENARIOS = (
    "A-constant",
    "B-historical-ratios-then-plateau",
    "C-post-tip-plateau",
    "D-growth-0.95",
    "D-growth-0.75",
    "D-growth-0.25",
    "E-decline-1.05",
    "E-decline-1.25",
    "E-decline-4.0",
    "F-eight-epoch-growth-burst",
    "G-alternating-clamps",
    "H-adaptive-lambda-half",
)
ALPHAS = (0.01, 0.10, 0.20, 0.30, 0.50, 1.00)
HORIZONS = (100, 476, 800, 2_000, 10_000, 100_000)
MODEL_POLICIES = (
    ("A", "honest-publication"),
    ("A", "prefer-shallow"),
    ("A", "publish-minimum"),
    ("A", "state-aware"),
    ("B", "honest-publication"),
    ("B", "prefer-shallow"),
    ("B", "publish-minimum"),
    ("B", "state-aware"),
    ("upper", "omniscient"),
)
EXPECTED_MASTER_SEED = 1269070838

REQUIRED_METADATA_FIELDS = frozenset(
    {
        "master_seed",
        "master_seed_hex",
        "continuous_simulation",
        "normative_integer_replay_file",
        "historical_summary_sha256",
        "historical_targets_sha256",
        "policy_sim_sha256",
        "live_initial_state",
        "historical_initial_state",
        "historical_initial_target",
        "trial_schedule",
        "effective_trials_by_checkpoint",
        "value_over_reward",
        "discount",
        "sha_trial_conversion",
        "exact_binomial_fields",
        "selection_success_semantics",
        "event_trace_retention",
        "state_aware_gain_proxy",
        "model_A",
        "model_B",
        "omniscient",
    }
)

# This is deliberately exact. A partial rerun or a simulator/schema change
# must not silently merge with results produced by another code version.
ROW_FIELDS = (
    "geology",
    "scenario",
    "alpha",
    "model",
    "policy",
    "horizon",
    "trials",
    "honest_deposits_mean",
    "attack_deposits_mean",
    "delta_mean",
    "elasticity",
    "delta_median",
    "delta_p90",
    "delta_p95",
    "delta_p99",
    "delta_maximum",
    "maximum_prefix_delta_observed",
    "probability_any_state_raising_selection",
    "registered_conditional_success_probability",
    "honest_k0_epochs_mean",
    "honest_k1_epochs_mean",
    "honest_k_ge_2_epochs_mean",
    "honest_exact_p_k0_epochs_mean",
    "honest_exact_p_k1_epochs_mean",
    "honest_exact_p_k_ge_2_epochs_mean",
    "attacked_counterfactual_k0_epochs_mean",
    "attacked_counterfactual_k1_epochs_mean",
    "attacked_counterfactual_k_ge_2_epochs_mean",
    "attacked_counterfactual_exact_p_k0_epochs_mean",
    "attacked_counterfactual_exact_p_k1_epochs_mean",
    "attacked_counterfactual_exact_p_k_ge_2_epochs_mean",
    "actual_attacked_k0_epochs_mean",
    "actual_attacked_k1_epochs_mean",
    "actual_attacked_k_ge_2_epochs_mean",
    "selectable_epochs_mean",
    "selection_attempt_epochs_mean",
    "state_raising_selection_epochs_mean",
    "harmful_selection_epochs_mean",
    "discarded_valid_candidates_mean",
    "replacement_discoveries_mean",
    "attacker_replacements_mean",
    "honest_replacements_mean",
    "withheld_bitcoin_blocks_mean",
    "bitcoin_reward_cost_mean_R",
    "extra_sha_trials_mean",
    "R_per_expected_global_marginal_deposit",
    "attacker_captured_marginal_deposits_retain_share",
    "R_per_expected_attacker_captured_deposit",
    "divergence_duration_mean",
    "probability_reconvergence_given_divergence",
    "reconvergence_time_mean_given_observed",
    "probability_terminal_state_diverged",
    "terminal_g1_relative_difference_mean",
    "terminal_g2_relative_difference_mean",
    "private_fork_or_orphan_cost_R",
    "latency_cost_R",
)

HASH_RE = re.compile(r"[0-9a-f]{64}")
TEXT_ROW_FIELDS = frozenset({"geology", "scenario", "model", "policy"})
INTEGER_ROW_FIELDS = frozenset({"horizon", "trials"})
NULLABLE_NUMERIC_ROW_FIELDS = frozenset(
    {
        "elasticity",
        "registered_conditional_success_probability",
        "actual_attacked_k0_epochs_mean",
        "actual_attacked_k1_epochs_mean",
        "actual_attacked_k_ge_2_epochs_mean",
        "R_per_expected_global_marginal_deposit",
        "attacker_captured_marginal_deposits_retain_share",
        "R_per_expected_attacker_captured_deposit",
        "probability_reconvergence_given_divergence",
        "reconvergence_time_mean_given_observed",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite, got {value!r}")
    return result


def _require_close(
    left: object,
    right: object,
    label: str,
    *,
    rel_tol: float = 1e-12,
) -> None:
    left_number = _require_number(left, f"{label} left side")
    right_number = _require_number(right, f"{label} right side")
    if not math.isclose(left_number, right_number, rel_tol=rel_tol, abs_tol=1e-9):
        raise ValueError(f"{label}: {left_number!r} != {right_number!r}")


def _validate_hash(value: object, label: str) -> None:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


def _require_probability(value: object, label: str) -> float:
    result = _require_number(value, label)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must lie in [0,1], got {result!r}")
    return result


def _metadata(document: dict[str, Any], shard_index: int) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError(f"shard {shard_index} is not an object")
    if not isinstance(document.get("rows"), list):
        raise ValueError(f"shard {shard_index} has no rows list")
    metadata = {key: value for key, value in document.items() if key != "rows"}
    missing = sorted(REQUIRED_METADATA_FIELDS - metadata.keys())
    if missing:
        raise ValueError(f"shard {shard_index} missing metadata fields: {missing}")
    for field in (
        "historical_summary_sha256",
        "historical_targets_sha256",
        "policy_sim_sha256",
    ):
        _validate_hash(metadata[field], f"shard {shard_index} {field}")
    if metadata["continuous_simulation"] is not True:
        raise ValueError(f"shard {shard_index} must declare continuous_simulation=true")
    seed = metadata["master_seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(f"shard {shard_index} master_seed must be an integer")
    if seed != EXPECTED_MASTER_SEED:
        raise ValueError(
            f"shard {shard_index} master_seed={seed}, expected {EXPECTED_MASTER_SEED}"
        )
    if metadata["master_seed_hex"] != hex(seed):
        raise ValueError(f"shard {shard_index} master_seed_hex does not match master_seed")
    return metadata


def _validate_trial_metadata(metadata: dict[str, Any]) -> dict[str, int]:
    schedule = metadata["trial_schedule"]
    effective = metadata["effective_trials_by_checkpoint"]
    if not isinstance(schedule, dict) or not isinstance(effective, dict):
        raise ValueError("trial schedule and effective-trial metadata must be objects")
    if set(effective) != {str(horizon) for horizon in HORIZONS}:
        raise ValueError(
            "effective_trials_by_checkpoint keys do not match the exact checkpoint grid"
        )
    parsed_schedule: dict[int, int] = {}
    for horizon_text, count in schedule.items():
        try:
            horizon = int(horizon_text)
        except (TypeError, ValueError) as error:
            raise ValueError(f"invalid trial-schedule horizon: {horizon_text!r}") from error
        if str(horizon) != horizon_text or isinstance(count, bool) or not isinstance(count, int):
            raise ValueError(f"invalid trial-schedule entry: {horizon_text!r}: {count!r}")
        if horizon <= 0 or count <= 0 or horizon not in HORIZONS:
            raise ValueError(f"out-of-grid trial-schedule entry: {horizon}: {count}")
        parsed_schedule[horizon] = count
    if not parsed_schedule:
        raise ValueError("trial_schedule must not be empty")

    parsed_effective: dict[str, int] = {}
    for checkpoint in HORIZONS:
        key = str(checkpoint)
        count = effective[key]
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise ValueError(f"invalid effective trial count at {checkpoint}: {count!r}")
        derived = sum(
            batch_count
            for batch_horizon, batch_count in parsed_schedule.items()
            if batch_horizon >= checkpoint
        )
        if count != derived:
            raise ValueError(
                f"effective trial count at {checkpoint} is {count}, schedule implies {derived}"
            )
        parsed_effective[key] = count
    return parsed_effective


def _validate_partition(
    row: dict[str, Any],
    fields: tuple[str, str, str],
    label: str,
    *,
    rel_tol: float = 1e-12,
) -> None:
    values = [_require_number(row[field], f"{label} {field}") for field in fields]
    if any(value < 0 for value in values):
        raise ValueError(f"{label} contains a negative K category")
    _require_close(
        sum(values),
        row["horizon"],
        f"{label} K0+K1+K>=2 partition",
        rel_tol=rel_tol,
    )


def _validate_row(row: object, effective: dict[str, int], row_index: int) -> None:
    if not isinstance(row, dict):
        raise ValueError(f"row {row_index} is not an object")
    actual_fields = set(row)
    expected_fields = set(ROW_FIELDS)
    if actual_fields != expected_fields:
        raise ValueError(
            f"row {row_index} schema mismatch: missing={sorted(expected_fields - actual_fields)}, "
            f"unexpected={sorted(actual_fields - expected_fields)}"
        )
    for field in ROW_FIELDS:
        value = row[field]
        if field in TEXT_ROW_FIELDS or field in INTEGER_ROW_FIELDS:
            continue
        if value is None:
            if field not in NULLABLE_NUMERIC_ROW_FIELDS:
                raise ValueError(f"row {row_index} {field} must not be null")
        else:
            _require_number(value, f"row {row_index} {field}")
    if row["geology"] != "c10-eclip":
        raise ValueError(f"row {row_index} geology is not c10-eclip: {row['geology']!r}")
    if row["alpha"] not in ALPHAS:
        raise ValueError(f"row {row_index} has invalid alpha: {row['alpha']!r}")
    if (row["model"], row["policy"]) not in MODEL_POLICIES:
        raise ValueError(
            f"row {row_index} has invalid model/policy: "
            f"{(row['model'], row['policy'])!r}"
        )
    horizon = row["horizon"]
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon not in HORIZONS:
        raise ValueError(f"row {row_index} has invalid horizon: {horizon!r}")
    trials = row["trials"]
    if isinstance(trials, bool) or not isinstance(trials, int):
        raise ValueError(f"row {row_index} has non-integer trials: {trials!r}")
    if trials != effective[str(horizon)]:
        raise ValueError(
            f"row {row_index} trials={trials}, expected {effective[str(horizon)]} at {horizon}"
        )

    _validate_partition(
        row,
        ("honest_k0_epochs_mean", "honest_k1_epochs_mean", "honest_k_ge_2_epochs_mean"),
        f"row {row_index} honest sampled",
    )
    _validate_partition(
        row,
        (
            "honest_exact_p_k0_epochs_mean",
            "honest_exact_p_k1_epochs_mean",
            "honest_exact_p_k_ge_2_epochs_mean",
        ),
        f"row {row_index} honest exact-probability",
        rel_tol=5e-12,
    )
    _validate_partition(
        row,
        (
            "attacked_counterfactual_k0_epochs_mean",
            "attacked_counterfactual_k1_epochs_mean",
            "attacked_counterfactual_k_ge_2_epochs_mean",
        ),
        f"row {row_index} attacked counterfactual sampled",
    )
    _validate_partition(
        row,
        (
            "attacked_counterfactual_exact_p_k0_epochs_mean",
            "attacked_counterfactual_exact_p_k1_epochs_mean",
            "attacked_counterfactual_exact_p_k_ge_2_epochs_mean",
        ),
        f"row {row_index} attacked counterfactual exact-probability",
        rel_tol=5e-12,
    )
    actual_attacked_fields = (
        "actual_attacked_k0_epochs_mean",
        "actual_attacked_k1_epochs_mean",
        "actual_attacked_k_ge_2_epochs_mean",
    )
    if row["model"] == "upper":
        if any(row[field] is not None for field in actual_attacked_fields):
            raise ValueError(f"row {row_index} omniscient actual-attacked K fields must all be null")
    else:
        if any(row[field] is None for field in actual_attacked_fields):
            raise ValueError(f"row {row_index} actual-attacked K fields must all be numeric")
        _validate_partition(row, actual_attacked_fields, f"row {row_index} actual attacked")
    _require_close(
        row["selectable_epochs_mean"],
        row["attacked_counterfactual_k_ge_2_epochs_mean"],
        f"row {row_index} selectable/counterfactual-K>=2 identity",
    )

    delta = _require_number(row["delta_mean"], f"row {row_index} delta")
    honest_deposits = _require_number(
        row["honest_deposits_mean"], f"row {row_index} honest deposits"
    )
    attacked_deposits = _require_number(
        row["attack_deposits_mean"], f"row {row_index} attacked deposits"
    )
    if not 0.0 <= honest_deposits <= horizon or not 0.0 <= attacked_deposits <= horizon:
        raise ValueError(f"row {row_index} mean deposits must lie in [0,horizon]")
    _require_close(
        attacked_deposits,
        honest_deposits + delta,
        f"row {row_index} deposit difference",
    )
    if honest_deposits:
        _require_close(
            row["elasticity"], delta / honest_deposits, f"row {row_index} elasticity"
        )
    elif row["elasticity"] is not None:
        raise ValueError(f"row {row_index} zero-denominator elasticity must be null")

    ordered_delta_fields = (
        "delta_median",
        "delta_p90",
        "delta_p95",
        "delta_p99",
        "delta_maximum",
    )
    ordered_delta_values = [
        _require_number(row[field], f"row {row_index} {field}")
        for field in ordered_delta_fields
    ]
    if ordered_delta_values != sorted(ordered_delta_values):
        raise ValueError(f"row {row_index} delta quantiles/maximum are not ordered")
    maximum_prefix = _require_number(
        row["maximum_prefix_delta_observed"], f"row {row_index} maximum prefix delta"
    )
    if maximum_prefix + 1e-9 < ordered_delta_values[-1]:
        raise ValueError(f"row {row_index} maximum prefix is below terminal delta maximum")
    discarded = _require_number(
        row["discarded_valid_candidates_mean"], f"row {row_index} discarded candidates"
    )
    replacements = _require_number(
        row["replacement_discoveries_mean"], f"row {row_index} replacements"
    )
    attacker_replacements = _require_number(
        row["attacker_replacements_mean"], f"row {row_index} attacker replacements"
    )
    honest_replacements = _require_number(
        row["honest_replacements_mean"], f"row {row_index} honest replacements"
    )
    if min(discarded, replacements, attacker_replacements, honest_replacements) < 0:
        raise ValueError(f"row {row_index} contains negative replacement/cost counts")
    _require_close(
        replacements,
        attacker_replacements + honest_replacements,
        f"row {row_index} replacement ownership partition",
    )
    model = row["model"]
    if model in ("A", "B"):
        _require_close(discarded, replacements, f"row {row_index} discard/replacement identity")
    elif model == "upper":
        _require_close(replacements, 0.0, f"row {row_index} omniscient replacements")
    else:
        raise ValueError(f"row {row_index} has unknown model: {model!r}")

    withheld = row["withheld_bitcoin_blocks_mean"]
    reward_cost = row["bitcoin_reward_cost_mean_R"]
    if model == "A":
        _require_close(withheld, discarded, f"row {row_index} withheld/discarded identity")
        _require_close(reward_cost, discarded, f"row {row_index} reward/discard identity")
    else:
        _require_close(withheld, 0.0, f"row {row_index} non-A Bitcoin withholding")
        _require_close(reward_cost, 0.0, f"row {row_index} non-A reward cost")
    if model == "B":
        _require_close(honest_replacements, 0.0, f"row {row_index} model-B honest replacements")
        _require_close(
            attacker_replacements,
            replacements,
            f"row {row_index} model-B attacker replacements",
        )
    extra_sha = _require_number(
        row["extra_sha_trials_mean"], f"row {row_index} extra SHA trials"
    )
    if extra_sha < 0:
        raise ValueError(f"row {row_index} contains negative extra SHA trials")
    if model == "upper":
        _require_close(extra_sha, 0.0, f"row {row_index} omniscient extra SHA trials")

    global_ratio = row["R_per_expected_global_marginal_deposit"]
    captured = row["attacker_captured_marginal_deposits_retain_share"]
    captured_ratio = row["R_per_expected_attacker_captured_deposit"]
    alpha = _require_number(row["alpha"], f"row {row_index} alpha")
    if model == "upper":
        if captured is not None or captured_ratio is not None or global_ratio is not None:
            raise ValueError(f"row {row_index} omniscient cost/capture fields must be null")
    else:
        _require_close(captured, alpha * delta, f"row {row_index} retained-share capture")
        if model == "A" and delta > 0:
            _require_close(
                global_ratio,
                _require_number(reward_cost, f"row {row_index} reward cost") / delta,
                f"row {row_index} global marginal-deposit cost ratio",
            )
            _require_close(
                captured_ratio,
                _require_number(reward_cost, f"row {row_index} reward cost")
                / (alpha * delta),
                f"row {row_index} participant-captured-deposit cost ratio",
            )
        elif global_ratio is not None or captured_ratio is not None:
            raise ValueError(f"row {row_index} inapplicable cost ratios must be null")

    for field in ("private_fork_or_orphan_cost_R", "latency_cost_R"):
        _require_close(row[field], 0.0, f"row {row_index} {field}")
    if row["policy"] in ("honest-publication", "publish-minimum"):
        _require_close(discarded, 0.0, f"row {row_index} non-selecting policy discards")

    attempts = _require_number(
        row["selection_attempt_epochs_mean"], f"row {row_index} selection attempts"
    )
    state_raising = _require_number(
        row["state_raising_selection_epochs_mean"], f"row {row_index} state-raising selections"
    )
    harmful = _require_number(
        row["harmful_selection_epochs_mean"], f"row {row_index} harmful selections"
    )
    if row["registered_conditional_success_probability"] is not None:
        raise ValueError(
            f"row {row_index} registered conditional-future success probability must be null"
        )
    any_state_raising = _require_probability(
        row["probability_any_state_raising_selection"],
        f"row {row_index} state-raising-selection probability",
    )
    if (
        min(attempts, state_raising, harmful) < 0
        or state_raising + harmful > attempts + 1e-9
    ):
        raise ValueError(f"row {row_index} has inconsistent selection-event counts")
    if attempts > discarded + 1e-9:
        raise ValueError(f"row {row_index} has more selection-attempt epochs than discards")
    if any(value > horizon + 1e-9 for value in (attempts, state_raising, harmful)):
        raise ValueError(f"row {row_index} selection-event means exceed the horizon")
    divergence_duration = _require_number(
        row["divergence_duration_mean"], f"row {row_index} divergence duration"
    )
    if not 0.0 <= divergence_duration <= horizon:
        raise ValueError(f"row {row_index} divergence duration lies outside [0,horizon]")
    _require_probability(
        row["probability_terminal_state_diverged"],
        f"row {row_index} terminal-divergence probability",
    )
    if row["probability_reconvergence_given_divergence"] is not None:
        _require_probability(
            row["probability_reconvergence_given_divergence"],
            f"row {row_index} reconvergence probability",
        )
    if row["reconvergence_time_mean_given_observed"] is not None:
        reconvergence_time = _require_number(
            row["reconvergence_time_mean_given_observed"],
            f"row {row_index} reconvergence time",
        )
        if not 0.0 <= reconvergence_time <= horizon:
            raise ValueError(f"row {row_index} reconvergence time lies outside [0,horizon]")


def validate_and_merge_documents(
    documents: Sequence[dict[str, Any]],
    source_shards_sha256: Sequence[str],
    *,
    expected_policy_sim_sha256: str | None = None,
    merge_policy_results_sha256: str | None = None,
) -> dict[str, Any]:
    """Return one validated merged document, or raise ``ValueError``.

    This pure-data entry point is intentionally public so tests can mutate a
    valid fixture and assert that each integrity check fails closed.
    """

    if len(documents) != 6:
        raise ValueError(f"expected six shards, got {len(documents)}")
    if len(source_shards_sha256) != 6:
        raise ValueError(f"expected six shard hashes, got {len(source_shards_sha256)}")
    for index, digest in enumerate(source_shards_sha256):
        _validate_hash(digest, f"source shard {index}")
    if len(set(source_shards_sha256)) != 6:
        raise ValueError("source shard hashes must be distinct")

    metadata_items = [_metadata(document, index) for index, document in enumerate(documents)]
    metadata = metadata_items[0]
    for index, comparison in enumerate(metadata_items[1:], start=1):
        if comparison != metadata:
            differing = sorted(set(comparison) | set(metadata))
            differing = [key for key in differing if comparison.get(key) != metadata.get(key)]
            raise ValueError(f"metadata mismatch in shard {index}: {differing}")
    if expected_policy_sim_sha256 is not None:
        _validate_hash(expected_policy_sim_sha256, "expected policy_sim.py hash")
        if metadata["policy_sim_sha256"] != expected_policy_sim_sha256:
            raise ValueError(
                "declared policy_sim_sha256 does not match the merger-adjacent policy_sim.py"
            )
    if merge_policy_results_sha256 is not None:
        _validate_hash(merge_policy_results_sha256, "merge_policy_results.py hash")
    effective = _validate_trial_metadata(metadata)

    shard_scenario_sets: list[frozenset[str]] = []
    rows: list[dict[str, Any]] = []
    seen_scenarios: set[str] = set()
    for index, document in enumerate(documents):
        shard_rows = document["rows"]
        shard_scenarios = frozenset(
            row.get("scenario") for row in shard_rows if isinstance(row, dict)
        )
        if len(shard_scenarios) != 2:
            raise ValueError(
                f"shard {index} must contain exactly two scenarios, "
                f"got {sorted(map(str, shard_scenarios))}"
            )
        overlap = seen_scenarios.intersection(shard_scenarios)
        if overlap:
            raise ValueError(f"shard {index} overlaps earlier scenarios: {sorted(overlap)}")
        if not shard_scenarios.issubset(SCENARIOS):
            raise ValueError(f"shard {index} contains unknown scenarios: {sorted(shard_scenarios)}")
        seen_scenarios.update(shard_scenarios)
        shard_scenario_sets.append(shard_scenarios)
        for row in shard_rows:
            _validate_row(row, effective, len(rows))
            rows.append(row)
    if seen_scenarios != set(SCENARIOS):
        raise ValueError(
            f"scenario coverage mismatch: missing={sorted(set(SCENARIOS) - seen_scenarios)}, "
            f"unexpected={sorted(seen_scenarios - set(SCENARIOS))}"
        )

    keys = [
        (row["scenario"], row["alpha"], row["model"], row["policy"], row["horizon"])
        for row in rows
    ]
    if len(set(keys)) != len(rows):
        raise ValueError("duplicate policy rows")
    expected = {
        (scenario, alpha, model, policy, horizon)
        for scenario in SCENARIOS
        for alpha in ALPHAS
        for model, policy in MODEL_POLICIES
        for horizon in HORIZONS
    }
    actual = set(keys)
    if actual != expected:
        raise ValueError(
            f"policy grid mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    rows.sort(
        key=lambda row: (
            SCENARIOS.index(row["scenario"]),
            float(row["alpha"]),
            MODEL_POLICIES.index((row["model"], row["policy"])),
            int(row["horizon"]),
        )
    )
    shard_provenance = sorted(
        (
            {"scenarios": sorted(scenarios), "sha256": digest}
            for scenarios, digest in zip(shard_scenario_sets, source_shards_sha256)
        ),
        key=lambda item: item["scenarios"],
    )
    merged = dict(metadata)
    merged["execution"] = "six validated, disjoint deterministic two-scenario shards"
    if merge_policy_results_sha256 is not None:
        merged["merge_policy_results_sha256"] = merge_policy_results_sha256
    merged["source_shards"] = shard_provenance
    merged["source_shards_sha256"] = [item["sha256"] for item in shard_provenance]
    merged["rows"] = rows
    return merged


def load_validate_and_merge(input_paths: Sequence[Path]) -> dict[str, Any]:
    """Load six paths and validate them against the local simulator source."""

    if len(input_paths) != 6:
        raise ValueError(f"expected six shards, got {len(input_paths)}")
    resolved = [path.resolve() for path in input_paths]
    if len(set(resolved)) != 6:
        raise ValueError("input shard paths must be distinct")
    # Parse and hash the same immutable byte snapshots, so the provenance
    # cannot race a concurrent replacement of a shard file.
    payloads = [path.read_bytes() for path in input_paths]
    documents = [json.loads(payload.decode("utf-8")) for payload in payloads]
    hashes = [hashlib.sha256(payload).hexdigest() for payload in payloads]
    policy_path = Path(__file__).with_name("policy_sim.py")
    merger_path = Path(__file__)
    return validate_and_merge_documents(
        documents,
        hashes,
        expected_policy_sim_sha256=_sha256(policy_path),
        merge_policy_results_sha256=_sha256(merger_path),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()
    merged = load_validate_and_merge([Path(item) for item in args.inputs])

    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = merged["rows"]
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ROW_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "scenarios": list(SCENARIOS)}, sort_keys=True))


if __name__ == "__main__":
    main()
