#!/usr/bin/env python3
"""Paired finite-horizon qualifier-selection simulations.

The simulation is offline and continuous-ratio.  Each epoch generates exactly
the low canonical hashes needed by either coupled branch; Model A replacement
discoveries use a separately keyed stream.  Normative historical state remains
the certified-integer implementation in redteam.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


W = 2016
MASTER_SEED = 1269070838
ALPHAS = (0.01, 0.10, 0.20, 0.30, 0.50, 1.00)
CHECKPOINTS = (100, 476, 800, 2_000, 10_000, 100_000)
E = math.e


State = float | tuple[float, float]


def stream_seed(*parts: object) -> int:
    label = ":".join(map(str, (MASTER_SEED,) + parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(label).digest()[:16], "big")


def bar(state: State) -> float:
    return state if isinstance(state, float) else state[1]


def coords(state: State) -> tuple[float, float]:
    return (state, state) if isinstance(state, float) else state


def accepted_low_support(upper: float, target: float) -> tuple[float, float]:
    """Return the materialized accepted-hash support and its probability."""

    support = min(upper, target)
    return support, support / target


def exact_binomial_category_probabilities(q: float) -> tuple[float, float, float]:
    """Return stable Binomial(W,q) probabilities for K=0, K=1, and K>=2.

    These are exact for the task's continuous-ratio IID model up to binary64
    evaluation error.  The recurrence avoids cancellation in the rare tail.
    """

    if q <= 0.0:
        return 1.0, 0.0, 0.0
    if q >= 1.0:
        return 0.0, 0.0, 1.0
    log_p0 = W * math.log1p(-q)
    p0 = math.exp(log_p0)
    odds = q / (1.0 - q)
    p1 = p0 * W * odds
    if q >= 1e-6:
        p_ge_2 = max(0.0, -math.expm1(log_p0) - p1)
    else:
        term = p0 * (W * (W - 1) / 2.0) * odds * odds
        p_ge_2 = term
        k = 2
        while k < W and term > max(1e-323, abs(p_ge_2) * 1e-16):
            term *= ((W - k) / (k + 1.0)) * odds
            p_ge_2 += term
            k += 1
    return p0, p1, min(1.0, p_ge_2)


def step(kind: str, state: State, value: float, state_floor: float) -> tuple[State, int]:
    if kind == "raw-record":
        assert isinstance(state, float)
        if value < state:
            return max(state_floor, value), 1
        return state, 0
    assert isinstance(state, tuple)
    g1, g2 = state
    if value < g1:
        if kind == "vanilla-c10":
            return (max(state_floor, value), g1), 1
        if kind == "c10-eclip":
            return (max(state_floor, value, g1 / E), g1), 1
        raise ValueError(kind)
    if value < g2:
        return (g1, value), 1
    return state, 0


def state_strictly_lower(left: State, right: State) -> bool:
    """Whether left is coordinatewise no higher and differs from right."""

    left_coords = coords(left)
    right_coords = coords(right)
    return (
        left_coords[0] <= right_coords[0]
        and left_coords[1] <= right_coords[1]
        and left_coords != right_coords
    )


def expected_gain_proxy(kind: str, lower: State, higher: State) -> float:
    """Fixed-target heuristic used only by the illustrative threshold policy.

    For eclip, 1.291 times the sum of coordinate log gaps interpolates the
    independently simulated limiting result (2.582 for two unit log gaps).
    This is not a continuation-value theorem, particularly for nonstationary
    target paths; the economic report gives the symbolic break-even rule and
    labels these policy rows as heuristic.
    """

    low = coords(lower)
    high = coords(higher)
    log_gap = sum(math.log(max(1.0, high[i] / max(low[i], 1e-320))) for i in (0, 1))
    if kind == "c10-eclip":
        return 1.291 * log_gap
    return log_gap


@dataclass
class TrialState:
    honest_state: State
    attacked_state: State
    honest_deposits: int = 0
    attacked_deposits: int = 0
    honest_k0_epochs: int = 0
    honest_k1_epochs: int = 0
    honest_selectable_epochs: int = 0
    attacked_k0_epochs: int = 0
    attacked_k1_epochs: int = 0
    selectable_epochs: int = 0
    actual_attacked_k0_epochs: int = 0
    actual_attacked_k1_epochs: int = 0
    actual_attacked_selectable_epochs: int = 0
    honest_exact_p_k0_epochs: float = 0.0
    honest_exact_p_k1_epochs: float = 0.0
    honest_exact_p_k_ge_2_epochs: float = 0.0
    attacked_counterfactual_exact_p_k0_epochs: float = 0.0
    attacked_counterfactual_exact_p_k1_epochs: float = 0.0
    attacked_counterfactual_exact_p_k_ge_2_epochs: float = 0.0
    selection_attempt_epochs: int = 0
    state_raising_selection_epochs: int = 0
    harmful_selection_epochs: int = 0
    withheld_blocks: int = 0
    replacement_discoveries: int = 0
    attacker_replacements: int = 0
    honest_replacements: int = 0
    extra_sha_trials: float = 0.0
    divergence_duration: int = 0
    ever_diverged: bool = False
    reconverged: bool = False
    first_divergence_epoch: int | None = None
    first_reconvergence_time: int | None = None
    maximum_prefix_delta: int = 0


def should_suppress(
    kind: str,
    policy: str,
    model: str,
    alpha: float,
    current_state: State,
    retained: float,
    deeper: float,
    state_floor: float,
    value_over_reward: float,
    discount: float,
) -> bool:
    retained_post, _ = step(kind, current_state, retained, state_floor)
    deeper_post, _ = step(kind, current_state, deeper, state_floor)
    if not state_strictly_lower(deeper_post, retained_post):
        return False
    if policy in ("prefer-shallow", "omniscient"):
        return True
    if policy != "state-aware":
        return False
    if model == "B":
        return True
    gain = expected_gain_proxy(kind, deeper_post, retained_post)
    captured_fraction = alpha
    return discount * value_over_reward * captured_fraction * gain > 1.0


def attacked_epoch_minimum(
    *,
    kind: str,
    state: State,
    threshold: float,
    base_values: list[float],
    base_owners: list[bool],
    alpha: float,
    model: str,
    policy: str,
    target: float,
    state_floor: float,
    replacement_rng: random.Random,
    value_over_reward: float,
    discount: float,
) -> tuple[float | None, int, float, int, int, int]:
    retained: float | None = None
    withheld = 0
    extra_sha = 0.0
    attacker_replacements = 0
    honest_replacements = 0
    canonical_k = 0
    # With target expressed in live-target units, conversion by
    # 2^256/live_target gives exactly 2^256/(absolute_target+1).
    expected_trials_per_valid = 1.0 / (target + state_floor)

    for base_value, base_attacker in zip(base_values, base_owners):
        if base_value >= threshold:
            continue
        if retained is None:
            retained = base_value
            canonical_k += 1
            continue
        candidate = base_value
        candidate_attacker = base_attacker
        while (
            candidate < retained
            and candidate_attacker
            and should_suppress(
                kind,
                policy,
                model,
                alpha,
                state,
                retained,
                candidate,
                state_floor,
                value_over_reward,
                discount,
            )
        ):
            # Each omitted otherwise-valid discovery costs one reward in A.
            # Mining then continues until a candidate is actually publishable.
            # In B, the attacker unrealistically keeps both slot and reward, so
            # replacement ownership remains attacker-controlled.
            withheld += 1
            extra_sha += expected_trials_per_valid
            candidate = replacement_rng.random() * target
            candidate_attacker = (
                True if model == "B" else replacement_rng.random() < alpha
            )
            attacker_replacements += int(candidate_attacker)
            honest_replacements += int(not candidate_attacker)
        canonical_k += int(candidate < threshold)
        retained = min(retained, candidate)
    return (
        retained,
        withheld,
        extra_sha,
        attacker_replacements,
        honest_replacements,
        canonical_k,
    )


def target_after_epoch(
    scenario: str,
    epoch: int,
    target: float,
    honest_state: State,
    min_target: float,
    max_target: float,
    historical_ratios: list[float],
) -> float:
    if scenario in ("A-constant", "C-post-tip-plateau"):
        ratio = 1.0
    elif scenario == "B-historical-ratios-then-plateau":
        ratio = historical_ratios[epoch] if epoch < len(historical_ratios) else 1.0
    elif scenario.startswith("D-growth-"):
        ratio = float(scenario.rsplit("-", 1)[1])
    elif scenario.startswith("E-decline-"):
        ratio = float(scenario.rsplit("-", 1)[1])
    elif scenario == "F-eight-epoch-growth-burst":
        ratio = 0.75 if epoch < 8 else 1.0
    elif scenario == "G-alternating-clamps":
        ratio = 0.25 if epoch % 2 == 0 else 4.0
    elif scenario == "H-adaptive-lambda-half":
        desired = W * bar(honest_state) / 0.5
        ratio = min(4.0, max(0.25, desired / target))
    else:
        raise ValueError(scenario)
    candidate = target * ratio
    # At the representable lower endpoint, a Bitcoin-valid construction can
    # switch to ratio 1 rather than request a zero compact target.
    return min(max_target, max(min_target, candidate))


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


def simulate_trial(
    *,
    kind: str,
    initial_state: State,
    scenario: str,
    alpha: float,
    model: str,
    policy: str,
    horizon: int,
    seed: int,
    initial_target: float,
    min_target: float,
    max_target: float,
    historical_ratios: list[float],
    value_over_reward: float,
    discount: float,
) -> dict[int, dict[str, object]]:
    base_rng = random.Random(seed)
    replacement_rng = random.Random(stream_seed(seed, "replacement"))
    trial = TrialState(initial_state, initial_state)
    target = initial_target
    outputs: dict[int, dict[str, object]] = {}
    checkpoints = set(item for item in CHECKPOINTS if item <= horizon)

    for epoch in range(1, horizon + 1):
        upper = max(bar(trial.honest_state), bar(trial.attacked_state))
        # Accepted proof-of-work hashes have support [0,T), even when a live
        # geology bar is above T.  Only values below both the larger bar and T
        # need to be materialized for the coupled branches.
        support, q_upper = accepted_low_support(upper, target)
        k_upper = base_rng.binomialvariate(n=W, p=q_upper)
        _, honest_q = accepted_low_support(bar(trial.honest_state), target)
        _, attacked_q = accepted_low_support(bar(trial.attacked_state), target)
        honest_probabilities = exact_binomial_category_probabilities(honest_q)
        attacked_probabilities = exact_binomial_category_probabilities(attacked_q)
        trial.honest_exact_p_k0_epochs += honest_probabilities[0]
        trial.honest_exact_p_k1_epochs += honest_probabilities[1]
        trial.honest_exact_p_k_ge_2_epochs += honest_probabilities[2]
        trial.attacked_counterfactual_exact_p_k0_epochs += attacked_probabilities[0]
        trial.attacked_counterfactual_exact_p_k1_epochs += attacked_probabilities[1]
        trial.attacked_counterfactual_exact_p_k_ge_2_epochs += attacked_probabilities[2]
        at_absorbing_floor = (
            trial.honest_state == trial.attacked_state
            and all(value == min_target for value in coords(trial.honest_state))
        )
        clip_dominated = False
        if (
            kind == "c10-eclip"
            and isinstance(trial.honest_state, tuple)
            and isinstance(trial.attacked_state, tuple)
        ):
            def deterministic_branch(state: tuple[float, float]) -> bool:
                return target <= state[0] / E or (
                    state[0] == min_target and target <= min_target
                )

            clip_dominated = deterministic_branch(trial.honest_state) and deterministic_branch(
                trial.attacked_state
            )
        if clip_dominated:
            # Every possible continuous hash is below both clip floors.  Both
            # transitions are deterministic and selection cannot affect them.
            trial.honest_selectable_epochs += 1
            trial.selectable_epochs += 1
            trial.actual_attacked_selectable_epochs += 1
            trial.honest_deposits += 1
            trial.attacked_deposits += 1
            honest_g1, _ = trial.honest_state
            attacked_g1, _ = trial.attacked_state
            trial.honest_state = (max(min_target, honest_g1 / E), honest_g1)
            trial.attacked_state = (max(min_target, attacked_g1 / E), attacked_g1)
        elif at_absorbing_floor:
            # No observation can move either state below the integer floor, so
            # qualifier selection has zero issuance effect.  K and deposits
            # still receive continuous-convention binomial draws without
            # materializing hashes.
            trial.honest_selectable_epochs += int(k_upper >= 2)
            trial.selectable_epochs += int(k_upper >= 2)
            trial.honest_k0_epochs += int(k_upper == 0)
            trial.honest_k1_epochs += int(k_upper == 1)
            trial.attacked_k0_epochs += int(k_upper == 0)
            trial.attacked_k1_epochs += int(k_upper == 1)
            trial.actual_attacked_k0_epochs += int(k_upper == 0)
            trial.actual_attacked_k1_epochs += int(k_upper == 1)
            trial.actual_attacked_selectable_epochs += int(k_upper >= 2)
            trial.honest_deposits += int(k_upper >= 1)
            trial.attacked_deposits += int(k_upper >= 1)
        elif k_upper:
            base_values = [base_rng.random() * support for _ in range(k_upper)]
            base_owners = [base_rng.random() < alpha for _ in range(k_upper)]
            honest_minimum = min(base_values)
            honest_k = sum(value < bar(trial.honest_state) for value in base_values)
            attacked_k = sum(value < bar(trial.attacked_state) for value in base_values)
            trial.honest_k0_epochs += int(honest_k == 0)
            trial.honest_k1_epochs += int(honest_k == 1)
            trial.honest_selectable_epochs += int(honest_k >= 2)
            trial.attacked_k0_epochs += int(attacked_k == 0)
            trial.attacked_k1_epochs += int(attacked_k == 1)
            trial.selectable_epochs += int(attacked_k >= 2)
            honest_post, honest_deposit = step(
                kind, trial.honest_state, honest_minimum, min_target
            )

            no_suppression_post, _ = step(
                kind, trial.attacked_state, honest_minimum, min_target
            )

            if policy == "omniscient":
                qualifiers = [value for value in base_values if value < bar(trial.attacked_state)]
                attacked_minimum = max(qualifiers) if qualifiers else None
                withheld = max(0, len(qualifiers) - 1)
                extra_sha = 0.0
                attacker_replacements = 0
                honest_replacements = 0
                actual_attacked_k = attacked_k
            elif policy in ("prefer-shallow", "state-aware"):
                (
                    attacked_minimum,
                    withheld,
                    extra_sha,
                    attacker_replacements,
                    honest_replacements,
                    actual_attacked_k,
                ) = attacked_epoch_minimum(
                    kind=kind,
                    state=trial.attacked_state,
                    threshold=bar(trial.attacked_state),
                    base_values=base_values,
                    base_owners=base_owners,
                    alpha=alpha,
                    model=model,
                    policy=policy,
                    target=target,
                    state_floor=min_target,
                    replacement_rng=replacement_rng,
                    value_over_reward=value_over_reward,
                    discount=discount,
                )
            else:
                attacked_minimum = honest_minimum
                withheld = 0
                extra_sha = 0.0
                attacker_replacements = 0
                honest_replacements = 0
                actual_attacked_k = attacked_k

            if attacked_minimum is None:
                attacked_post, attacked_deposit = trial.attacked_state, 0
            else:
                attacked_post, attacked_deposit = step(
                    kind, trial.attacked_state, attacked_minimum, min_target
                )
            trial.selection_attempt_epochs += int(withheld > 0)
            if withheld and state_strictly_lower(no_suppression_post, attacked_post):
                trial.state_raising_selection_epochs += 1
            elif withheld and state_strictly_lower(attacked_post, no_suppression_post):
                trial.harmful_selection_epochs += 1
            trial.actual_attacked_k0_epochs += int(actual_attacked_k == 0)
            trial.actual_attacked_k1_epochs += int(actual_attacked_k == 1)
            trial.actual_attacked_selectable_epochs += int(actual_attacked_k >= 2)
            trial.withheld_blocks += withheld
            trial.replacement_discoveries += attacker_replacements + honest_replacements
            trial.attacker_replacements += attacker_replacements
            trial.honest_replacements += honest_replacements
            trial.extra_sha_trials += extra_sha
            trial.honest_state = honest_post
            trial.attacked_state = attacked_post
            trial.honest_deposits += honest_deposit
            trial.attacked_deposits += attacked_deposit
        else:
            trial.honest_k0_epochs += 1
            trial.attacked_k0_epochs += 1
            trial.actual_attacked_k0_epochs += 1

        different = trial.honest_state != trial.attacked_state
        if different:
            trial.divergence_duration += 1
            if not trial.ever_diverged:
                trial.ever_diverged = True
                trial.first_divergence_epoch = epoch
        elif trial.ever_diverged and not trial.reconverged:
            trial.reconverged = True
            assert trial.first_divergence_epoch is not None
            trial.first_reconvergence_time = epoch - trial.first_divergence_epoch
        trial.maximum_prefix_delta = max(
            trial.maximum_prefix_delta,
            trial.attacked_deposits - trial.honest_deposits,
        )
        target = target_after_epoch(
            scenario,
            epoch - 1,
            target,
            trial.honest_state,
            min_target,
            max_target,
            historical_ratios,
        )

        if epoch in checkpoints:
            honest_coords = coords(trial.honest_state)
            attacked_coords = coords(trial.attacked_state)
            outputs[epoch] = {
                "honest_deposits": trial.honest_deposits,
                "attacked_deposits": trial.attacked_deposits,
                "delta": trial.attacked_deposits - trial.honest_deposits,
                "maximum_prefix_delta": trial.maximum_prefix_delta,
                "honest_k0_epochs": trial.honest_k0_epochs,
                "honest_k1_epochs": trial.honest_k1_epochs,
                "honest_k_ge_2_epochs": trial.honest_selectable_epochs,
                "attacked_counterfactual_k0_epochs": trial.attacked_k0_epochs,
                "attacked_counterfactual_k1_epochs": trial.attacked_k1_epochs,
                "attacked_counterfactual_k_ge_2_epochs": trial.selectable_epochs,
                "actual_attacked_k0_epochs": trial.actual_attacked_k0_epochs,
                "actual_attacked_k1_epochs": trial.actual_attacked_k1_epochs,
                "actual_attacked_k_ge_2_epochs": trial.actual_attacked_selectable_epochs,
                "honest_exact_p_k0_epochs": trial.honest_exact_p_k0_epochs,
                "honest_exact_p_k1_epochs": trial.honest_exact_p_k1_epochs,
                "honest_exact_p_k_ge_2_epochs": trial.honest_exact_p_k_ge_2_epochs,
                "attacked_counterfactual_exact_p_k0_epochs": trial.attacked_counterfactual_exact_p_k0_epochs,
                "attacked_counterfactual_exact_p_k1_epochs": trial.attacked_counterfactual_exact_p_k1_epochs,
                "attacked_counterfactual_exact_p_k_ge_2_epochs": trial.attacked_counterfactual_exact_p_k_ge_2_epochs,
                "selectable_epochs": trial.selectable_epochs,
                "selection_attempt_epochs": trial.selection_attempt_epochs,
                "state_raising_selection_epochs": trial.state_raising_selection_epochs,
                "harmful_selection_epochs": trial.harmful_selection_epochs,
                "any_state_raising_selection": trial.state_raising_selection_epochs > 0,
                "withheld_blocks": trial.withheld_blocks,
                "replacement_discoveries": trial.replacement_discoveries,
                "attacker_replacements": trial.attacker_replacements,
                "honest_replacements": trial.honest_replacements,
                "extra_sha_trials": trial.extra_sha_trials,
                "divergence_duration": trial.divergence_duration,
                "ever_diverged": trial.ever_diverged,
                "reconverged": trial.reconverged,
                "first_reconvergence_time": trial.first_reconvergence_time,
                "terminal_g1_relative_difference": attacked_coords[0] - honest_coords[0],
                "terminal_g2_relative_difference": attacked_coords[1] - honest_coords[1],
                "terminal_state_diverged": trial.attacked_state != trial.honest_state,
            }
    return outputs


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(probability * len(ordered)) - 1))]


def summarize(
    samples: list[dict[str, object]],
    *,
    kind: str,
    scenario: str,
    alpha: float,
    model: str,
    policy: str,
    horizon: int,
) -> dict[str, object]:
    deltas = [float(item["delta"]) for item in samples]
    honest = [float(item["honest_deposits"]) for item in samples]
    withheld = [float(item["withheld_blocks"]) for item in samples]
    mean_delta = sum(deltas) / len(deltas)
    mean_honest = sum(honest) / len(honest)
    mean_withheld = sum(withheld) / len(withheld)
    diverged_samples = [item for item in samples if item["ever_diverged"]]
    reconverged_samples = [item for item in diverged_samples if item["reconverged"]]
    reconvergence_times = [
        float(item["first_reconvergence_time"])
        for item in reconverged_samples
        if item["first_reconvergence_time"] is not None
    ]
    return {
        "geology": kind,
        "scenario": scenario,
        "alpha": alpha,
        "model": model,
        "policy": policy,
        "horizon": horizon,
        "trials": len(samples),
        "honest_deposits_mean": mean_honest,
        "attack_deposits_mean": sum(float(item["attacked_deposits"]) for item in samples) / len(samples),
        "delta_mean": mean_delta,
        "elasticity": mean_delta / mean_honest if mean_honest else None,
        "delta_median": quantile(deltas, 0.50),
        "delta_p90": quantile(deltas, 0.90),
        "delta_p95": quantile(deltas, 0.95),
        "delta_p99": quantile(deltas, 0.99),
        "delta_maximum": max(deltas),
        "maximum_prefix_delta_observed": max(float(item["maximum_prefix_delta"]) for item in samples),
        "probability_any_state_raising_selection": sum(
            bool(item["any_state_raising_selection"]) for item in samples
        ) / len(samples),
        "registered_conditional_success_probability": None,
        "honest_k0_epochs_mean": sum(float(item["honest_k0_epochs"]) for item in samples) / len(samples),
        "honest_k1_epochs_mean": sum(float(item["honest_k1_epochs"]) for item in samples) / len(samples),
        "honest_k_ge_2_epochs_mean": sum(float(item["honest_k_ge_2_epochs"]) for item in samples) / len(samples),
        "attacked_counterfactual_k0_epochs_mean": sum(
            float(item["attacked_counterfactual_k0_epochs"]) for item in samples
        ) / len(samples),
        "attacked_counterfactual_k1_epochs_mean": sum(
            float(item["attacked_counterfactual_k1_epochs"]) for item in samples
        ) / len(samples),
        "attacked_counterfactual_k_ge_2_epochs_mean": sum(
            float(item["attacked_counterfactual_k_ge_2_epochs"]) for item in samples
        ) / len(samples),
        "actual_attacked_k0_epochs_mean": (
            None if model == "upper" else
            sum(float(item["actual_attacked_k0_epochs"]) for item in samples) / len(samples)
        ),
        "actual_attacked_k1_epochs_mean": (
            None if model == "upper" else
            sum(float(item["actual_attacked_k1_epochs"]) for item in samples) / len(samples)
        ),
        "actual_attacked_k_ge_2_epochs_mean": (
            None if model == "upper" else
            sum(float(item["actual_attacked_k_ge_2_epochs"]) for item in samples) / len(samples)
        ),
        "honest_exact_p_k0_epochs_mean": sum(
            float(item["honest_exact_p_k0_epochs"]) for item in samples
        ) / len(samples),
        "honest_exact_p_k1_epochs_mean": sum(
            float(item["honest_exact_p_k1_epochs"]) for item in samples
        ) / len(samples),
        "honest_exact_p_k_ge_2_epochs_mean": sum(
            float(item["honest_exact_p_k_ge_2_epochs"]) for item in samples
        ) / len(samples),
        "attacked_counterfactual_exact_p_k0_epochs_mean": sum(
            float(item["attacked_counterfactual_exact_p_k0_epochs"]) for item in samples
        ) / len(samples),
        "attacked_counterfactual_exact_p_k1_epochs_mean": sum(
            float(item["attacked_counterfactual_exact_p_k1_epochs"]) for item in samples
        ) / len(samples),
        "attacked_counterfactual_exact_p_k_ge_2_epochs_mean": sum(
            float(item["attacked_counterfactual_exact_p_k_ge_2_epochs"]) for item in samples
        ) / len(samples),
        "selectable_epochs_mean": sum(float(item["selectable_epochs"]) for item in samples) / len(samples),
        "selection_attempt_epochs_mean": sum(float(item["selection_attempt_epochs"]) for item in samples) / len(samples),
        "state_raising_selection_epochs_mean": sum(
            float(item["state_raising_selection_epochs"]) for item in samples
        ) / len(samples),
        "harmful_selection_epochs_mean": sum(float(item["harmful_selection_epochs"]) for item in samples) / len(samples),
        "discarded_valid_candidates_mean": mean_withheld,
        "replacement_discoveries_mean": sum(float(item["replacement_discoveries"]) for item in samples) / len(samples),
        "attacker_replacements_mean": sum(float(item["attacker_replacements"]) for item in samples) / len(samples),
        "honest_replacements_mean": sum(float(item["honest_replacements"]) for item in samples) / len(samples),
        "withheld_bitcoin_blocks_mean": mean_withheld if model == "A" else 0.0,
        "bitcoin_reward_cost_mean_R": mean_withheld if model == "A" else 0.0,
        "extra_sha_trials_mean": sum(float(item["extra_sha_trials"]) for item in samples) / len(samples),
        "R_per_expected_global_marginal_deposit": (
            mean_withheld / mean_delta if model == "A" and mean_delta > 0 else None
        ),
        "attacker_captured_marginal_deposits_retain_share": alpha * mean_delta,
        "R_per_expected_attacker_captured_deposit": (
            mean_withheld / (alpha * mean_delta)
            if model == "A" and alpha * mean_delta > 0
            else None
        ),
        "divergence_duration_mean": sum(float(item["divergence_duration"]) for item in samples) / len(samples),
        "probability_reconvergence_given_divergence": (
            len(reconverged_samples) / len(diverged_samples) if diverged_samples else None
        ),
        "reconvergence_time_mean_given_observed": (
            sum(reconvergence_times) / len(reconvergence_times) if reconvergence_times else None
        ),
        "probability_terminal_state_diverged": sum(bool(item["terminal_state_diverged"]) for item in samples) / len(samples),
        "terminal_g1_relative_difference_mean": sum(float(item["terminal_g1_relative_difference"]) for item in samples) / len(samples),
        "terminal_g2_relative_difference_mean": sum(float(item["terminal_g2_relative_difference"]) for item in samples) / len(samples),
        "private_fork_or_orphan_cost_R": 0.0,
        "latency_cost_R": 0.0,
    }


BATCHES = (
    (100_000, 4),
    (10_000, 28),
    (2_000, 96),
    (800, 128),
    (100, 256),
)


def run_configuration(
    *,
    kind: str,
    initial_state: State,
    scenario: str,
    alpha: float,
    model: str,
    policy: str,
    initial_target: float,
    min_target: float,
    max_target: float,
    historical_ratios: list[float],
    value_over_reward: float,
    discount: float,
) -> list[dict[str, object]]:
    collected: dict[int, list[dict[str, object]]] = {checkpoint: [] for checkpoint in CHECKPOINTS}
    trial_index = 0
    for batch_horizon, count in BATCHES:
        for _ in range(count):
            seed = stream_seed(kind, scenario, alpha, model, policy, batch_horizon, trial_index)
            outputs = simulate_trial(
                kind=kind,
                initial_state=initial_state,
                scenario=scenario,
                alpha=alpha,
                model=model,
                policy=policy,
                horizon=batch_horizon,
                seed=seed,
                initial_target=initial_target,
                min_target=min_target,
                max_target=max_target,
                historical_ratios=historical_ratios,
                value_over_reward=value_over_reward,
                discount=discount,
            )
            for checkpoint, sample in outputs.items():
                collected[checkpoint].append(sample)
            trial_index += 1
    return [
        summarize(
            samples,
            kind=kind,
            scenario=scenario,
            alpha=alpha,
            model=model,
            policy=policy,
            horizon=horizon,
        )
        for horizon, samples in collected.items()
        if samples
    ]


def zero_policy_rows(source_rows: Iterable[dict[str, object]], policy: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in source_rows:
        row = dict(source)
        row["policy"] = policy
        row["attack_deposits_mean"] = row["honest_deposits_mean"]
        row["attacked_counterfactual_k0_epochs_mean"] = row["honest_k0_epochs_mean"]
        row["attacked_counterfactual_k1_epochs_mean"] = row["honest_k1_epochs_mean"]
        row["attacked_counterfactual_k_ge_2_epochs_mean"] = row["honest_k_ge_2_epochs_mean"]
        row["actual_attacked_k0_epochs_mean"] = row["honest_k0_epochs_mean"]
        row["actual_attacked_k1_epochs_mean"] = row["honest_k1_epochs_mean"]
        row["actual_attacked_k_ge_2_epochs_mean"] = row["honest_k_ge_2_epochs_mean"]
        row["attacked_counterfactual_exact_p_k0_epochs_mean"] = row[
            "honest_exact_p_k0_epochs_mean"
        ]
        row["attacked_counterfactual_exact_p_k1_epochs_mean"] = row[
            "honest_exact_p_k1_epochs_mean"
        ]
        row["attacked_counterfactual_exact_p_k_ge_2_epochs_mean"] = row[
            "honest_exact_p_k_ge_2_epochs_mean"
        ]
        row["selectable_epochs_mean"] = row["honest_k_ge_2_epochs_mean"]
        row["registered_conditional_success_probability"] = None
        for field in (
            "delta_mean",
            "delta_median",
            "delta_p90",
            "delta_p95",
            "delta_p99",
            "delta_maximum",
            "maximum_prefix_delta_observed",
            "probability_any_state_raising_selection",
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
            "attacker_captured_marginal_deposits_retain_share",
            "divergence_duration_mean",
            "probability_terminal_state_diverged",
            "terminal_g1_relative_difference_mean",
            "terminal_g2_relative_difference_mean",
            "private_fork_or_orphan_cost_R",
            "latency_cost_R",
        ):
            row[field] = 0.0
        row["elasticity"] = 0.0 if row["honest_deposits_mean"] else None
        row["R_per_expected_global_marginal_deposit"] = None
        row["R_per_expected_attacker_captured_deposit"] = None
        row["probability_reconvergence_given_divergence"] = None
        row["reconvergence_time_mean_given_observed"] = None
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-summary", required=True)
    parser.add_argument("--historical-targets", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument(
        "--scenario",
        action="append",
        choices=SCENARIOS,
        help="run only this scenario (repeatable); default is the complete grid",
    )
    parser.add_argument("--quick", action="store_true", help="one trial per 100/800 checkpoint for tests")
    parser.add_argument("--value-over-reward", type=float, default=1.0)
    parser.add_argument("--discount", type=float, default=0.99)
    args = parser.parse_args()

    historical = json.loads(Path(args.historical_summary).read_text(encoding="utf-8"))
    targets = [int(item) for item in json.loads(Path(args.historical_targets).read_text(encoding="utf-8"))["targets"]]
    live_target = int(historical["live_target"])
    min_target = 1.0 / live_target
    max_target = int("00000000ffff0000000000000000000000000000000000000000000000000000", 16) / live_target
    # Epochs zero and one create the empirical clipped initial state.  Scenario
    # B begins its stochastic policy replay at epoch two, consumes the verified
    # targets through epoch 477, and then holds the final target constant.
    historical_ratios = [
        targets[index + 1] / targets[index]
        for index in range(2, len(targets) - 1)
    ]
    live_state: State = (
        int(historical["live_g1"]) / live_target,
        int(historical["live_g2"]) / live_target,
    )
    historical_initial_state: State = (
        int(historical["simulation_initial_g1"]) / live_target,
        int(historical["simulation_initial_g2"]) / live_target,
    )
    historical_initial_target = int(historical["simulation_first_target"]) / live_target

    global BATCHES
    scenarios = tuple(args.scenario) if args.scenario else SCENARIOS
    alphas = ALPHAS
    if args.quick:
        BATCHES = ((800, 1),)
        scenarios = ("A-constant", "H-adaptive-lambda-half")
        alphas = (0.30,)

    rows: list[dict[str, object]] = []
    for scenario in scenarios:
        initial_state = (
            historical_initial_state
            if scenario == "B-historical-ratios-then-plateau"
            else live_state
        )
        initial_target = (
            historical_initial_target
            if scenario == "B-historical-ratios-then-plateau"
            else 1.0
        )
        for alpha in alphas:
            for model in ("A", "B"):
                prefer = run_configuration(
                    kind="c10-eclip",
                    initial_state=initial_state,
                    scenario=scenario,
                    alpha=alpha,
                    model=model,
                    policy="prefer-shallow",
                    initial_target=initial_target,
                    min_target=min_target,
                    max_target=max_target,
                    historical_ratios=historical_ratios,
                    value_over_reward=args.value_over_reward,
                    discount=args.discount,
                )
                rows.extend(prefer)
                rows.extend(zero_policy_rows(prefer, "honest-publication"))
                rows.extend(zero_policy_rows(prefer, "publish-minimum"))

                # With cost-free replacement, the threshold policy is exactly
                # prefer-shallow.  Model A is simulated separately at every
                # share; no result row is synthesized from a presumed bound.
                if model == "B":
                    state_aware = [dict(item, policy="state-aware") for item in prefer]
                else:
                    state_aware = run_configuration(
                        kind="c10-eclip",
                        initial_state=initial_state,
                        scenario=scenario,
                        alpha=alpha,
                        model=model,
                        policy="state-aware",
                        initial_target=initial_target,
                        min_target=min_target,
                        max_target=max_target,
                        historical_ratios=historical_ratios,
                        value_over_reward=args.value_over_reward,
                        discount=args.discount,
                    )
                rows.extend(state_aware)

        # Omniscient results do not depend on alpha; duplicate a single run so
        # the machine grid is complete while retaining the upper-bound label.
        upper = run_configuration(
            kind="c10-eclip",
            initial_state=initial_state,
            scenario=scenario,
            alpha=1.0,
            model="upper",
            policy="omniscient",
            initial_target=initial_target,
            min_target=min_target,
            max_target=max_target,
            historical_ratios=historical_ratios,
            value_over_reward=args.value_over_reward,
            discount=args.discount,
        )
        for alpha in alphas:
            for item in upper:
                clone = dict(item, alpha=alpha)
                # The omniscient ceiling has no miner ownership or participant
                # capture semantics; alpha exists only to complete the grid.
                clone["attacker_captured_marginal_deposits_retain_share"] = None
                clone["R_per_expected_attacker_captured_deposit"] = None
                rows.append(clone)

    # During simulation target is expressed in units of the empirical live
    # target.  Convert inverse-target work to expected double-SHA trials per
    # valid discovery using the discrete T+1 endpoint normalization.
    sha_scale = (2**256) / live_target
    for row in rows:
        row["extra_sha_trials_mean"] = float(row["extra_sha_trials_mean"]) * sha_scale

    output = {
        "master_seed": MASTER_SEED,
        "master_seed_hex": hex(MASTER_SEED),
        "policy_sim_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "continuous_simulation": True,
        "normative_integer_replay_file": str(Path(args.historical_summary)),
        "historical_summary_sha256": hashlib.sha256(
            Path(args.historical_summary).read_bytes()
        ).hexdigest(),
        "historical_targets_sha256": hashlib.sha256(
            Path(args.historical_targets).read_bytes()
        ).hexdigest(),
        "live_initial_state": list(live_state),
        "historical_initial_state": list(historical_initial_state),
        "historical_initial_target": historical_initial_target,
        "trial_schedule": {str(horizon): count for horizon, count in BATCHES},
        "effective_trials_by_checkpoint": {
            str(checkpoint): sum(count for horizon, count in BATCHES if horizon >= checkpoint)
            for checkpoint in CHECKPOINTS
        },
        "value_over_reward": args.value_over_reward,
        "discount": args.discount,
        "sha_trial_conversion": "discarded candidates * 2^256 / (absolute target + 1)",
        "exact_binomial_fields": "per-trial sums of continuous-ratio Binomial(2016,min(1,G2/T)) category probabilities, averaged across trials",
        "selection_success_semantics": "state-raising fields compare immediate same-prestate post-states; registered conditional-future success probability is null because continuation value was not solved",
        "event_trace_retention": "aggregate ownership/replacement/suppression counts only; individual replacement hashes and suppressed-event traces not retained (preregistration deviation)",
        "state_aware_gain_proxy": "fixed-target heuristic: 1.291 * sum coordinate log gaps; not a variable-target continuation value",
        "model_A": "attacker-owned otherwise-valid discoveries suppressed; ownership-marked replacement race continues until publication; 1 R per suppression",
        "model_B": "attacker redraws until policy accepts while retaining slot ownership and Bitcoin reward; favorable upper bound",
        "omniscient": "retains maximum deposit-preserving qualifier regardless of ownership or timing",
        "rows": rows,
    }
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_path = Path(args.output_csv)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "output": str(output_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
