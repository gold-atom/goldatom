#!/usr/bin/env python3
"""Ownership-aware C10-eclip qualifier-selection experiments.

This is research code, not consensus code.  The historical scanner performs
integer-certified e clipping.  This Monte Carlo model deliberately uses
floating-point normalized hashes so that many long future paths can be
sampled; no value produced here is suitable for a consensus transition.

Each accepted Bitcoin height is a race for a Bitcoin-valid header.  A header
hash is uniform on [0, target], and its discoverer is attacker-controlled with
probability alpha.  When a valid header is suppressed, that height remains
open and another independently distributed valid header must be found.  Thus
the model never gives a free trial to the attacker and never lets the attacker
select an honest miner's hash, except in the explicitly impossible
all-discoveries stress control.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


HERE = Path(__file__).resolve().parent
HISTORICAL_SUMMARY = HERE / "historical-summary.json"
HISTORICAL_REPLAY = HERE / "historical-replay.csv"
RAW_SUMMARY = HERE.parent / "ledger" / "summary.json"

W = 2016
E = math.e
E_WEIGHT = E / (E - 1.0)
ALPHAS = (0.01, 0.10, 0.20, 0.30, 0.50, 1.00)
YEARS = (1, 4, 10, 25, 50, 100)
HORIZONS = {year: round(year * 365.25 / 14.0) for year in YEARS}
SEED = 0xC10EC11F
DEFAULT_REPETITIONS = 4_096
THRESHOLD_VALUE_OVER_R = 100.0
POW_LIMIT = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
TARGET_TIMESPAN = 14 * 24 * 60 * 60
MATCHED_GROSS_BUDGET_R = 1


@dataclass(frozen=True)
class InitialState:
    geology: str
    g1: float
    g2: float


def horizon_epochs(years: int) -> int:
    return round(years * 365.25 / 14.0)


def historical_like_multiplier(rows: list[dict], lookback_years: int = 8) -> dict:
    """Derive a declared stress rate from the final ~8 years of complete epochs."""
    lookback = horizon_epochs(lookback_years)
    last = len(rows) - 1
    first = last - lookback
    current = int(rows[last]["target"])
    prior = int(rows[first]["target"])
    multiplier = (current / prior) ** (1.0 / lookback)
    return {
        "lookback_years": lookback_years,
        "lookback_epochs": lookback,
        "first_epoch": int(rows[first]["epoch"]),
        "last_epoch": int(rows[last]["epoch"]),
        "target_ratio": current / prior,
        "target_multiplier_per_epoch": multiplier,
        "implied_difficulty_growth_per_year": multiplier ** (-365.25 / 14.0) - 1.0,
    }


def encode_compact_target(target: int) -> int:
    """Bitcoin Core-compatible positive target compression."""
    if target <= 0:
        raise ValueError("target must be positive")
    size = (target.bit_length() + 7) // 8
    compact = (target << (8 * (3 - size)) if size <= 3
               else target >> (8 * (size - 3)))
    if compact & 0x00800000:
        compact >>= 8
        size += 1
    return compact | (size << 24)


def decode_compact_target(bits: int) -> int:
    size = bits >> 24
    word = bits & 0x007FFFFF
    if bits & 0x00800000:
        raise ValueError("negative compact target")
    return (word >> (8 * (3 - size)) if size <= 3
            else word << (8 * (size - 3)))


def retarget_target(previous: int, actual_timespan: int) -> int:
    """Exact integer/compact arithmetic for a Bitcoin retarget boundary."""
    span = min(max(actual_timespan, TARGET_TIMESPAN // 4), TARGET_TIMESPAN * 4)
    candidate = min(POW_LIMIT, previous * span // TARGET_TIMESPAN)
    return decode_compact_target(encode_compact_target(candidate))


def target_path(name: str, epochs: int, growth_multiplier: float,
                pow_limit_ratio: float, start_target: int | None = None) -> np.ndarray:
    """Return target/T0 for a non-forecast scenario.

    The target for simulated epoch zero is the observed tip target.  Changes
    apply from epoch one onward.  Scenario E uses exact Bitcoin integer and
    compact-target arithmetic at alternating clamp endpoints.  It is an
    intentionally hostile consensus-admissible target path, not a forecast.
    """
    out = np.ones(epochs, dtype=np.float64)
    plateau_after = horizon_epochs(4)
    scenario_e_target = start_target
    for i in range(1, epochs):
        if name == "A-constant-target":
            out[i] = 1.0
        elif name == "B-historical-like-growth":
            out[i] = out[i - 1] * growth_multiplier
        elif name == "C-four-year-growth-then-plateau":
            out[i] = (out[i - 1] * growth_multiplier
                      if i < plateau_after else out[i - 1])
        elif name == "D-difficulty-decline":
            out[i] = min(pow_limit_ratio, out[i - 1] / growth_multiplier)
        elif name == "E-consensus-retarget-sawtooth":
            if start_target is None or scenario_e_target is None:
                raise ValueError("Scenario E requires an integer start_target")
            span = TARGET_TIMESPAN // 4 if i % 2 else TARGET_TIMESPAN * 4
            scenario_e_target = retarget_target(scenario_e_target, span)
            out[i] = scenario_e_target / start_target
        else:
            raise ValueError(name)
    return out


def clipped_transition_arrays(g1: np.ndarray, g2: np.ndarray,
                              observations: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    deposits = observations < g2
    unique = observations < g1
    second = (~unique) & deposits
    next_g1 = g1.copy()
    next_g2 = g2.copy()
    next_g2[unique] = g1[unique]
    next_g1[unique] = np.maximum(observations[unique], next_g2[unique] / E)
    next_g2[second] = observations[second]
    return next_g1, next_g2, deposits


def natural_transition_arrays(g1: np.ndarray, g2: np.ndarray,
                              observations: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    deposits = observations < g2
    unique = observations < g1
    second = (~unique) & deposits
    next_g1 = g1.copy()
    next_g2 = g2.copy()
    next_g2[unique] = g1[unique]
    next_g1[unique] = observations[unique]
    next_g2[second] = observations[second]
    return next_g1, next_g2, deposits


def raw_transition_arrays(g1: np.ndarray, g2: np.ndarray,
                          observations: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    deposits = observations < g2
    frontier = np.minimum(g2, observations)
    return frontier.copy(), frontier, deposits


def transition_arrays(geology: str, g1: np.ndarray, g2: np.ndarray,
                      observations: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if geology == "c10-eclip":
        return clipped_transition_arrays(g1, g2, observations)
    if geology == "c10-unclipped":
        return natural_transition_arrays(g1, g2, observations)
    if geology == "raw-record":
        return raw_transition_arrays(g1, g2, observations)
    raise ValueError(geology)


def eclip_potential(g1: np.ndarray, g2: np.ndarray) -> np.ndarray:
    return -E_WEIGHT * np.log(g1) - np.log(g2)


def potential_tightening(g1: np.ndarray, g2: np.ndarray,
                         shallow: np.ndarray, deep: np.ndarray) -> np.ndarray:
    """Rare-event, constant-target future count value of accepting deep vs shallow."""
    loose_g1, loose_g2, _ = clipped_transition_arrays(g1, g2, shallow)
    tight_g1, tight_g2, _ = clipped_transition_arrays(g1, g2, deep)
    return np.maximum(0.0, eclip_potential(tight_g1, tight_g2)
                      - eclip_potential(loose_g1, loose_g2))


def effective_tightening(geology: str, g1: np.ndarray, g2: np.ndarray,
                         shallow: np.ndarray, deep: np.ndarray) -> np.ndarray:
    loose_g1, loose_g2, _ = transition_arrays(geology, g1, g2, shallow)
    tight_g1, tight_g2, _ = transition_arrays(geology, g1, g2, deep)
    return (tight_g1 < loose_g1) | (tight_g2 < loose_g2)


def honest_epoch_minimum(rng: np.random.Generator, target: float,
                         repetitions: int, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    # Stable inverse CDF for the minimum of W independent U(0,T) values.
    u = rng.random(repetitions)
    minimum = target * (-np.expm1(np.log(u) / W))
    owner = rng.random(repetitions) < alpha
    return minimum, owner


def strategic_epoch_minimum(
    rng: np.random.Generator,
    target: float,
    g1: np.ndarray,
    g2: np.ndarray,
    alpha: float,
    policy: str,
    geology: str = "c10-eclip",
    threshold_value_over_r: float = THRESHOLD_VALUE_OVER_R,
    remaining_budget: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Simulate W accepted heights, resampling every suppressed valid header.

    Record-low skipping is distributionally exact: non-record candidates are
    accepted immediately and skipped with a geometric waiting time.  Every
    record-low candidate has an independently sampled owner and conditional
    U(0,current_min) value.
    """
    n = len(g1)
    accepted = np.zeros(n, dtype=np.int32)
    # Start at the qualifying bar, not T.  Geometric skipping jumps directly
    # over accepted non-qualifiers.  If no candidate crosses this bar the
    # returned value equals G2, which correctly encodes a `neither` transition.
    current = np.minimum(g2, target)
    current_owner = np.zeros(n, dtype=np.bool_)
    attacker_locked = np.zeros(n, dtype=np.bool_)
    eligible = np.zeros(n, dtype=np.int32)
    suppressed = np.zeros(n, dtype=np.int32)
    controlled_omissions = np.zeros(n, dtype=np.int32)
    raw_deposits = np.zeros(n, dtype=np.int32)
    raw_attacker_deposits = np.zeros(n, dtype=np.int32)

    while True:
        active = accepted < W
        if not np.any(active):
            break
        indexes = np.flatnonzero(active)
        cur = current[indexes]
        probability = np.clip(cur / target, 0.0, 1.0)
        # Draw full-length arrays so replication i receives the same variates
        # under every policy at record-event index j.  Epoch-level RNG reset in
        # simulate_path prevents a longer attacked epoch from shifting all
        # later epochs, providing a low-variance common-random coupling.
        u_wait = rng.random(n)[indexes]
        waits = np.empty(len(indexes), dtype=np.int64)
        certain = probability >= 1.0
        impossible = probability <= 0.0
        waits[certain] = 1
        waits[impossible] = W + 1
        ordinary = ~(certain | impossible)
        remaining = W - accepted[indexes]
        log_survival = np.zeros(len(indexes), dtype=np.float64)
        log_survival[ordinary] = np.log1p(-probability[ordinary])
        event_probability = np.zeros(len(indexes), dtype=np.float64)
        event_probability[certain] = 1.0
        event_probability[ordinary] = -np.expm1(
            remaining[ordinary] * log_survival[ordinary]
        )
        event = u_wait < event_probability
        sampled = event & ordinary
        waits[sampled] = (
            np.floor(np.log1p(-u_wait[sampled]) / log_survival[sampled])
            .astype(np.int64) + 1
        )
        waits[sampled] = np.clip(waits[sampled], 1, remaining[sampled])
        no_event_indexes = indexes[~event]
        accepted[no_event_indexes] = W
        if not np.any(event):
            continue

        event_indexes = indexes[event]
        accepted[event_indexes] += waits[event] - 1
        value_draw = rng.random(n)[event_indexes]
        owner_draw = rng.random(n)[event_indexes]
        deep = current[event_indexes] * value_draw
        attacker = owner_draw < alpha
        public_locked = current[event_indexes] < g2[event_indexes]
        effective = effective_tightening(
            geology, g1[event_indexes], g2[event_indexes],
            current[event_indexes], deep,
        )
        if policy == "raw-net-creation":
            # Raw records count every accepted new frontier.  Omitting one loses
            # that current deposit, so the fixed-target asymptotic net-creation
            # threshold is ln(shallow/deep)>1, i.e. deep<shallow/e.
            base_eligible = attacker & effective & (deep < current[event_indexes] / E)
        else:
            base_eligible = public_locked & attacker & effective

        if policy == "record-honest":
            opportunity = np.zeros(len(event_indexes), dtype=np.bool_)
            omit = np.zeros(len(event_indexes), dtype=np.bool_)
        elif policy == "raw-net-creation":
            opportunity = base_eligible
            omit = opportunity
        elif policy == "shallow-lock":
            opportunity = base_eligible & attacker_locked[event_indexes]
            omit = opportunity
        elif policy == "public-lock":
            opportunity = base_eligible
            omit = opportunity
        elif policy == "threshold":
            opportunity = base_eligible
            benefit = potential_tightening(
                g1[event_indexes], g2[event_indexes],
                current[event_indexes], deep,
            )
            # The attacker captures alpha of later incremental events under the
            # stated persistent-share value model.  A forgone canonical block
            # costs one R.
            omit = opportunity & (
                alpha * threshold_value_over_r * benefit > 1.0
            )
        elif policy == "all-discoveries-public-lock":
            # Explicitly impossible ownership stress: control every later
            # qualifier, including honest discoveries, at zero reward cost.
            # This is narrower than the separate omniscient hard ceiling.
            opportunity = public_locked & effective
            omit = public_locked & effective
            controlled_omissions[event_indexes] += omit
        else:
            raise ValueError(policy)

        eligible[event_indexes] += opportunity
        if remaining_budget is not None and policy != "all-discoveries-public-lock":
            omit &= remaining_budget[event_indexes] > 0

        omit_indexes = event_indexes[omit]
        if policy != "all-discoveries-public-lock":
            suppressed[omit_indexes] += 1
            if remaining_budget is not None:
                remaining_budget[omit_indexes] -= 1
        accept_mask = ~omit
        accept_indexes = event_indexes[accept_mask]
        accepted[accept_indexes] += 1
        current[accept_indexes] = deep[accept_mask]
        current_owner[accept_indexes] = attacker[accept_mask]
        accepted_raw_record = deep[accept_mask] < g2[accept_indexes]
        raw_deposits[accept_indexes] += accepted_raw_record
        raw_attacker_deposits[accept_indexes] += (
            accepted_raw_record & attacker[accept_mask]
        )
        new_attacker_qualifier = attacker[accept_mask] & (
            deep[accept_mask] < g2[accept_indexes]
        )
        attacker_locked[accept_indexes] |= new_attacker_qualifier

    return {
        "minimum": current,
        "minimum_owner_attacker": current_owner,
        "eligible_attacker_events": eligible,
        "forfeited_blocks": suppressed,
        "omniscient_controlled_omissions": controlled_omissions,
        "raw_deposit_count": raw_deposits,
        "raw_attacker_deposit_count": raw_attacker_deposits,
    }


def summarize_samples(values: np.ndarray) -> dict[str, float]:
    n = len(values)
    mean = float(np.mean(values))
    standard_error = float(np.std(values, ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    return {
        "mean": mean,
        "standard_error": standard_error,
        "ci95": [mean - 1.96 * standard_error, mean + 1.96 * standard_error],
    }


def simulate_path(
    initial: InitialState,
    targets: np.ndarray,
    alpha: float,
    policy: str,
    repetitions: int,
    seed: int,
    threshold_value_over_r: float = THRESHOLD_VALUE_OVER_R,
    gross_budget_cap_R: int | None = None,
) -> dict[int, dict]:
    g1 = np.full(repetitions, initial.g1, dtype=np.float64)
    g2 = np.full(repetitions, initial.g2, dtype=np.float64)
    deposits = np.zeros(repetitions, dtype=np.int32)
    attacker_deposit_blocks = np.zeros(repetitions, dtype=np.int32)
    forfeited = np.zeros(repetitions, dtype=np.int32)
    eligible = np.zeros(repetitions, dtype=np.int32)
    controlled = np.zeros(repetitions, dtype=np.int32)
    remaining_budget = (None if gross_budget_cap_R is None else
                        np.full(repetitions, gross_budget_cap_R, dtype=np.int32))
    checkpoints = {epochs: years for years, epochs in HORIZONS.items()}
    output: dict[int, dict] = {}

    for epoch, target in enumerate(targets, 1):
        epoch_rng = np.random.default_rng(seed + epoch * 1_000_003)
        event = strategic_epoch_minimum(
            epoch_rng, float(target), g1, g2, alpha,
            "record-honest" if policy == "honest" else policy,
            geology=initial.geology,
            threshold_value_over_r=threshold_value_over_r,
            remaining_budget=remaining_budget,
        )
        minimum = event["minimum"]
        owner = event["minimum_owner_attacker"]
        eligible += event["eligible_attacker_events"]
        forfeited += event["forfeited_blocks"]
        controlled += event["omniscient_controlled_omissions"]
        g1, g2, epoch_deposits = transition_arrays(initial.geology, g1, g2, minimum)
        if initial.geology == "raw-record":
            deposits += event["raw_deposit_count"]
            attacker_deposit_blocks += event["raw_attacker_deposit_count"]
        else:
            deposits += epoch_deposits
            attacker_deposit_blocks += epoch_deposits & owner

        if epoch in checkpoints:
            output[checkpoints[epoch]] = {
                "deposits": deposits.copy(),
                "attacker_deposit_blocks": attacker_deposit_blocks.copy(),
                "forfeited_blocks": forfeited.copy(),
                "eligible_attacker_events": eligible.copy(),
                "omniscient_controlled_omissions": controlled.copy(),
                "terminal_g1": g1.copy(),
                "terminal_g2": g2.copy(),
                "gross_budget_cap_R": gross_budget_cap_R,
            }
    return output


def paired_row(scenario: str, geology: str, alpha: float, policy: str,
               years: int, attack: dict, honest: dict,
               repetitions: int) -> dict:
    # Epoch-indexed common variates couple honest and attacked replication i.
    # This is a variance-reduction coupling, not a claim that divergent Bitcoin
    # histories literally encounter identical future blocks.
    delta_samples = attack["deposits"].astype(np.float64) - honest["deposits"]
    attacker_delta_samples = (
        attack["attacker_deposit_blocks"].astype(np.float64)
        - honest["attacker_deposit_blocks"]
    )
    honest_summary = summarize_samples(honest["deposits"].astype(np.float64))
    attack_summary = summarize_samples(attack["deposits"].astype(np.float64))
    delta_summary = summarize_samples(delta_samples)
    attacker_delta_summary = summarize_samples(attacker_delta_samples)
    cost_summary = summarize_samples(attack["forfeited_blocks"].astype(np.float64))
    eligible_summary = summarize_samples(attack["eligible_attacker_events"].astype(np.float64))
    controlled_summary = summarize_samples(
        attack["omniscient_controlled_omissions"].astype(np.float64)
    )
    honest_mean = honest_summary["mean"]
    delta = delta_summary["mean"]
    cost = cost_summary["mean"]
    controlled = controlled_summary["mean"]
    return {
        "scenario": scenario,
        "geology": geology,
        "alpha": alpha,
        "policy": policy,
        "years": years,
        "epochs": HORIZONS[years],
        "repetitions": repetitions,
        "honest_expected_deposits": honest_mean,
        "attack_expected_deposits": attack_summary["mean"],
        "delta_N": delta,
        "delta_N_standard_error": delta_summary["standard_error"],
        "delta_N_ci95": delta_summary["ci95"],
        "relative_supply_elasticity": delta / honest_mean if honest_mean else None,
        "attacker_associated_delta_N": attacker_delta_summary["mean"],
        "attacker_associated_delta_N_standard_error": attacker_delta_summary["standard_error"],
        "attacker_associated_delta_N_ci95": attacker_delta_summary["ci95"],
        "net_attacker_associated_delta_over_global_delta": (
            attacker_delta_summary["mean"] / delta if delta > 0 else None
        ),
        "expected_eligible_attacker_events": eligible_summary["mean"],
        "expected_forfeited_bitcoin_rewards_R": cost,
        "expected_net_fixed_height_reward_shortfall_R": cost * (1.0 - alpha),
        "expected_additional_network_valid_solution_intervals": cost + controlled,
        "expected_attacker_share_of_additional_hash_intervals": (
            None if policy == "all-discoveries-public-lock" else alpha * cost
        ),
        "expected_zero_cost_all_discoveries_omissions": controlled,
        "R_per_expected_extra_deposit": cost / delta if delta > 0 else None,
        "value_capture_proxy_if_attacker_exits": 0.0,
        "value_capture_proxy_if_hash_share_maintained": alpha,
        "value_capture_upper_bound": 1.0,
        "gross_budget_cap_R": attack.get("gross_budget_cap_R"),
        "gross_budget_utilization": (
            cost / attack["gross_budget_cap_R"]
            if attack.get("gross_budget_cap_R") else None
        ),
    }


def omniscient_hard_ceiling_row(scenario: str, alpha: float, years: int,
                                honest: dict, repetitions: int) -> dict:
    """Trivial but genuine hard bound: at most one deposit per epoch."""
    epochs = HORIZONS[years]
    honest_values = honest["deposits"].astype(np.float64)
    honest_summary = summarize_samples(honest_values)
    delta_summary = summarize_samples(epochs - honest_values)
    honest_mean = honest_summary["mean"]
    delta = delta_summary["mean"]
    return {
        "scenario": scenario,
        "geology": "c10-eclip",
        "alpha": alpha,
        "policy": "omniscient-hard-ceiling",
        "years": years,
        "epochs": epochs,
        "repetitions": repetitions,
        "honest_expected_deposits": honest_mean,
        "attack_expected_deposits": float(epochs),
        "delta_N": delta,
        "delta_N_standard_error": delta_summary["standard_error"],
        "delta_N_ci95": delta_summary["ci95"],
        "relative_supply_elasticity": delta / honest_mean if honest_mean else None,
        "expected_eligible_attacker_events": None,
        "expected_forfeited_bitcoin_rewards_R": 0.0,
        "expected_net_fixed_height_reward_shortfall_R": 0.0,
        "expected_additional_network_valid_solution_intervals": None,
        "expected_attacker_share_of_additional_hash_intervals": None,
        "expected_zero_cost_all_discoveries_omissions": None,
        "R_per_expected_extra_deposit": None,
        "gross_budget_cap_R": None,
        "warning": (
            "Hard count ceiling only: grants arbitrary foresight, control, delay, "
            "and zero cost; it is not an executable strategy."
        ),
    }


def ownership_metrics(p: float, alpha: float, g1_over_g2: float,
                      trials: int = W) -> dict[str, float]:
    """Exact finite-binomial ownership metrics plus rank-symmetry sums."""
    p_any = -math.expm1(trials * math.log1p(-p))
    p_first_attacker = alpha * p_any
    p_attacker_multiple = 1.0 - (1.0 - alpha * p) ** trials \
        - trials * alpha * p * (1.0 - alpha * p) ** (trials - 1)
    p_mixed = 1.0 - (1.0 - alpha * p) ** trials \
        - (1.0 - (1.0 - alpha) * p) ** trials + (1.0 - p) ** trials
    p_owned_shallow_then_deeper = 0.0
    p_public_lock_later_attacker_record = 0.0
    p_effective_public_lock = 0.0
    p_later_attacker_unique_min = 0.0
    expected_public_lock_suppressions = 0.0
    expected_owned_lock_suppressions = 0.0
    clip_floor = g1_over_g2 / E

    # Deterministic quadrature for the intersection requested by the threat
    # model: a later attacker record crosses G1 while the prior running minimum
    # remains above the clip floor G1/e, so accepting it actually tightens the
    # state.  f_n(y) is the no-event probability for n remaining qualifier
    # values given current normalized minimum y.
    grid = np.linspace(0.0, 1.0, 500_001)
    step = grid[1]
    f = np.ones_like(grid)
    effective_unique_by_k = {1: 0.0}
    for k in range(2, 17):
        integral = np.empty_like(f)
        integral[0] = 0.0
        integral[1:] = np.cumsum((f[:-1] + f[1:]) * (step / 2.0))
        limited = np.interp(np.minimum(grid, g1_over_g2), grid, integral)
        next_f = (1.0 - grid) * f + integral
        next_f[grid > clip_floor] -= alpha * limited[grid > clip_floor]
        f = np.clip(next_f, 0.0, 1.0)
        survival = float(np.trapezoid(f, grid))
        effective_unique_by_k[k] = 1.0 - survival
    p_effective_later_attacker_unique = 0.0
    pk = (1.0 - p) ** trials
    for k in range(1, trials + 1):
        pk *= (trials - k + 1) / k * p / (1.0 - p)
        if pk == 0.0:
            break
        if k < 2:
            continue
        # Given k chronological qualifier values, qualifier j is a new running
        # minimum with probability 1/j.  Ownership is independent.
        public_none = 1.0
        owned_none = 1.0
        expected_public = 0.0
        expected_owned = 0.0
        for j in range(2, k + 1):
            public_none *= 1.0 - alpha / j
            expected_public += alpha / j
            # Required named shallow-lock: first qualifier attacker-owned, then
            # later attacker-owned running minimum.  This expression conditions
            # only on that sufficient first-lock case and is therefore a lower
            # bound on all attacker-lock chronologies.
            owned_none *= 1.0 - alpha / j
            expected_owned += alpha / j
        p_public_lock_later_attacker_record += pk * (1.0 - public_none)
        expected_public_lock_suppressions += pk * expected_public
        p_owned_shallow_then_deeper += pk * alpha * (1.0 - owned_none)
        expected_owned_lock_suppressions += pk * alpha * expected_owned
        product_to_k = 1.0
        effective_survival = clip_floor
        for ell in range(2, k + 1):
            product_before = product_to_k
            product_to_k *= 1.0 - alpha / ell
            effective_survival += (
                (1.0 - clip_floor) ** (ell - 1) * clip_floor
                * (1.0 - alpha) * product_before
            )
        effective_survival += (1.0 - clip_floor) ** k * product_to_k
        p_effective_public_lock += pk * (1.0 - effective_survival)

        # Exact continuous-order calculation for a later attacker-owned
        # running minimum that also crosses G1.  L is the number of the k
        # qualifier values below r=G1/G2.  The record-count probability
        # generating function is prod_i(1-alpha/i).
        no_unique = (1.0 - g1_over_g2) ** k
        for ell in range(1, k + 1):
            probability_l = (
                math.comb(k, ell) * g1_over_g2 ** ell
                * (1.0 - g1_over_g2) ** (k - ell)
            )
            pgf = 1.0
            for i in range(1, ell + 1):
                pgf *= 1.0 - alpha / i
            if alpha < 1.0:
                pgf_minus_one_record = pgf / (1.0 - alpha)
            else:
                pgf_minus_one_record = 1.0 / ell
            no_unique_given_l = (
                (ell / k) * pgf_minus_one_record
                + (1.0 - ell / k) * pgf
            )
            no_unique += probability_l * no_unique_given_l
        p_later_attacker_unique_min += pk * (1.0 - no_unique)
        if k in effective_unique_by_k:
            p_effective_later_attacker_unique += pk * effective_unique_by_k[k]
    return {
        "alpha": alpha,
        "p_first_qualifier_attacker": p_first_attacker,
        "p_at_least_two_attacker_qualifiers": p_attacker_multiple,
        "p_mixed_honest_and_attacker_qualifiers": p_mixed,
        "p_attacker_first_then_later_deeper_attacker": p_owned_shallow_then_deeper,
        "p_public_qualifier_then_later_deeper_attacker": p_public_lock_later_attacker_record,
        "p_state_effective_public_qualifier_then_later_deeper_attacker": p_effective_public_lock,
        "p_later_attacker_unique_min_including_clip_neutral": p_later_attacker_unique_min,
        "p_strategically_suppressible_state_effective_later_attacker_unique_min": (
            p_effective_later_attacker_unique
        ),
        "state_effective_unique_min_quadrature_grid_points": len(grid),
        "expected_public_lock_suppressions_per_epoch": expected_public_lock_suppressions,
        "expected_first-attacker-lock_suppressions_lower_bound_per_epoch": expected_owned_lock_suppressions,
        "ex_post_ownership_respecting_upper_bound": alpha * (
            1.0 - (1.0 - p) ** trials
            - trials * p * (1.0 - p) ** (trials - 1)
        ),
    }


def initial_states(historical: dict, raw: dict) -> dict[str, InitialState]:
    target = float(historical["live_c10_eclip"]["target"])
    clipped = historical["live_c10_eclip"]["state"]
    natural = historical["live_unclipped_c10_control"]["state"]
    frontier = int(raw["current_frontier"], 16)
    return {
        "c10-eclip": InitialState(
            "c10-eclip", int(clipped["g1"]) / target, int(clipped["g2"]) / target
        ),
        "c10-unclipped": InitialState(
            "c10-unclipped", int(natural["g1"]) / target, int(natural["g2"]) / target
        ),
        "raw-record": InitialState("raw-record", frontier / target, frontier / target),
    }


def build_results(repetitions: int = DEFAULT_REPETITIONS, seed: int = SEED) -> dict:
    historical = json.loads(HISTORICAL_SUMMARY.read_text())
    raw = json.loads(RAW_SUMMARY.read_text())
    replay_rows = list(csv.DictReader(HISTORICAL_REPLAY.open()))
    rate = historical_like_multiplier(replay_rows)
    starts = initial_states(historical, raw)
    current_target = int(historical["live_c10_eclip"]["target"])
    pow_limit_ratio = POW_LIMIT / current_target
    max_epochs = max(HORIZONS.values())
    scenarios = (
        "A-constant-target",
        "B-historical-like-growth",
        "C-four-year-growth-then-plateau",
        "D-difficulty-decline",
        "E-consensus-retarget-sawtooth",
    )
    eclip_policies = (
        "shallow-lock", "public-lock", "threshold",
        "all-discoveries-public-lock",
    )
    rows: list[dict] = []

    # NumPy's deterministic PCG64 stream is fixed by the stored seed.  Distinct
    # integer offsets isolate every scenario/geology/alpha/policy experiment.
    for scenario_index, scenario in enumerate(scenarios):
        targets = target_path(
            scenario, max_epochs, rate["target_multiplier_per_epoch"],
            pow_limit_ratio, start_target=current_target,
        )
        for geology_index, (geology, start) in enumerate(starts.items()):
            # Honest state evolution is alpha-independent, but ownership counts
            # are not, so retain one paired honest run for each alpha.
            for alpha_index, alpha in enumerate(ALPHAS):
                experiment_base = (
                    seed + 10_000_000 * scenario_index + 1_000_000 * geology_index
                    + 10_000 * alpha_index
                )
                honest = simulate_path(
                    start, targets, alpha, "honest", repetitions, experiment_base
                )
                if geology == "c10-eclip":
                    policies = eclip_policies
                elif geology == "raw-record":
                    policies = ("raw-net-creation",)
                else:
                    policies = ("public-lock",)
                for policy_index, policy in enumerate(policies, 1):
                    attack_alpha = (
                        1.0 if policy == "all-discoveries-public-lock" else alpha
                    )
                    attack = simulate_path(
                        start, targets, attack_alpha, policy, repetitions,
                        experiment_base,
                    )
                    for years in YEARS:
                        row = paired_row(
                            scenario, geology, alpha, policy, years,
                            attack[years], honest[years], repetitions,
                        )
                        if policy == "threshold":
                            row["threshold_value_over_R"] = THRESHOLD_VALUE_OVER_R
                            row["threshold_capture_fraction_assumption"] = alpha
                        if policy == "all-discoveries-public-lock":
                            for key in (
                                "attacker_associated_delta_N",
                                "attacker_associated_delta_N_standard_error",
                                "attacker_associated_delta_N_ci95",
                                "net_attacker_associated_delta_over_global_delta",
                            ):
                                row[key] = None
                            row["warning"] = (
                                "Impossible ownership stress: controls every discovery "
                                "after a public lock at zero cost, but lacks foresight; "
                                "it is not the omniscient hard ceiling."
                            )
                        rows.append(row)

                if geology == "c10-eclip":
                    for years in YEARS:
                        rows.append(omniscient_hard_ceiling_row(
                            scenario, alpha, years, honest[years], repetitions
                        ))

                # A common ex-ante hard budget: each path may omit at most one
                # publishable valid header over the full simulated horizon.
                budget_policy = (
                    "raw-net-creation" if geology == "raw-record" else "public-lock"
                )
                budget_attack = simulate_path(
                    start, targets, alpha, budget_policy, repetitions,
                    experiment_base, gross_budget_cap_R=MATCHED_GROSS_BUDGET_R,
                )
                for years in YEARS:
                    budget_row = paired_row(
                        scenario, geology, alpha,
                        f"{budget_policy}-budget-{MATCHED_GROSS_BUDGET_R}R",
                        years, budget_attack[years], honest[years], repetitions,
                    )
                    budget_row["matched_control_budget"] = True
                    rows.append(budget_row)

    live_p = historical["live_c10_eclip"]["p_per_valid_block"]
    live_ratio = (
        int(historical["live_c10_eclip"]["state"]["g1"])
        / int(historical["live_c10_eclip"]["state"]["g2"])
    )
    ownership = [ownership_metrics(live_p, alpha, live_ratio) for alpha in ALPHAS]

    # Untuned equivalent stress baseline: the actual maximum-lambda historical
    # pre-state (epoch 37), then a constant target for 800 epochs.  This was
    # fixed before running the result and does not attempt to reverse-engineer
    # the unavailable earlier setup.
    stress_row = max(
        (row for row in replay_rows[2:] if row["lambda"]),
        key=lambda row: float(row["lambda"]),
    )
    stress_target = float(stress_row["target"])
    stress_start = InitialState(
        "c10-eclip",
        int(stress_row["pre_g1"]) / stress_target,
        int(stress_row["pre_g2"]) / stress_target,
    )
    stress_targets = np.ones(800, dtype=np.float64)
    stress_repetitions = max(repetitions, 32_768)
    # simulate_path records only standard calendar checkpoints; use a dedicated
    # 800-epoch endpoint routine.
    stress_attack = simulate_endpoint(
        stress_start, stress_targets, 1.0, "public-lock", stress_repetitions,
        seed + 900_000_000,
    )
    stress_honest_end = simulate_endpoint(
        stress_start, stress_targets, 1.0, "honest", stress_repetitions,
        seed + 900_000_000,
    )
    stress_delta = (stress_attack["deposits"].astype(float)
                    - stress_honest_end["deposits"].astype(float))
    stress = {
        "prior_setup_recoverable": False,
        "reason": (
            "The referenced /workspace/goldatom-assay/c10-clip-attack.md and its "
            "code/seeds were absent from the repository and workspace."
        ),
        "equivalent_baseline": (
            "Actual historical maximum-lambda pre-state (epoch 37), constant target, "
            "alpha=1, public-lock policy, 800 epochs; selected before observing output."
        ),
        "initial_historical_epoch": int(stress_row["epoch"]),
        "initial_lambda": float(stress_row["lambda"]),
        "repetitions": stress_repetitions,
        "honest_expected_deposits": float(np.mean(stress_honest_end["deposits"])),
        "attack_expected_deposits": float(np.mean(stress_attack["deposits"])),
        "delta_N": summarize_samples(stress_delta),
        "extra_strategically_omitted_hashes": summarize_samples(
            stress_attack["forfeited_blocks"].astype(float)
        ),
    }

    return {
        "schema": "goldatom-c10-eclip-qualifier-selection-v1",
        "status": "adversarial research; not a specification or forecast",
        "seed": seed,
        "numpy_version": np.__version__,
        "repetitions": repetitions,
        "bitcoin_blocks_per_epoch": W,
        "calendar_conversion": "round(years * 365.25 / 14)",
        "horizons": HORIZONS,
        "alphas": ALPHAS,
        "threshold_policy": {
            "illustrative_V_over_R": THRESHOLD_VALUE_OVER_R,
            "captured_fraction": "alpha, maintained indefinitely",
            "rule": "omit iff alpha*(V/R)*rare-event potential tightening > 1",
            "warning": (
                "Myopic constant-target infinite-horizon proxy; not a solved "
                "finite-horizon dynamic economic optimum."
            ),
        },
        "matched_control_budget": {
            "gross_cap_R_per_path": MATCHED_GROSS_BUDGET_R,
            "meaning": (
                "Same ex-ante cap for raw, unclipped C10, and C10-eclip; "
                "realized spend differs when a strategy finds no opportunity."
            ),
        },
        "scenario_rate_calibration": rate,
        "scenario_definitions": {
            "A-constant-target": "tip target for every future epoch",
            "B-historical-like-growth": "8-year observed geometric target multiplier continued",
            "C-four-year-growth-then-plateau": "same multiplier for 104 epochs, then constant",
            "D-difficulty-decline": "reciprocal multiplier until Bitcoin powLimit",
            "E-consensus-retarget-sawtooth": (
                "alternate Bitcoin min/max clamped actual-timespan inputs using "
                "exact integer and compact-target rounding; hostile, not a forecast"
            ),
        },
        "model": {
            "unit": "one independently found Bitcoin-valid header",
            "hash": "continuous uniform on [0,target]",
            "ownership": "independent Bernoulli(alpha) for each found valid header",
            "canonicalization": (
                "suppressed valid header does not advance height; next valid discovery "
                "competes for the same height"
            ),
            "publication_races": (
                "published valid headers are treated as canonical; propagation/orphan risk "
                "is omitted, favoring the attacker"
            ),
            "forecast_epoch_boundary": (
                "future scenarios restart at a full 2016-block epoch boundary from "
                "the completed-epoch-477 state; they are not conditioned on the "
                "417 blocks remaining after snapshot height 965246"
            ),
        },
        "live_ownership_analytics": ownership,
        "unavailable-prior-stress-and-equivalent-baseline": stress,
        "rows": rows,
    }


def simulate_endpoint(initial: InitialState, targets: np.ndarray, alpha: float,
                      policy: str, repetitions: int, seed: int) -> dict[str, np.ndarray]:
    """Memory-light endpoint version used by the fixed 800-epoch stress test."""
    g1 = np.full(repetitions, initial.g1)
    g2 = np.full(repetitions, initial.g2)
    deposits = np.zeros(repetitions, dtype=np.int32)
    forfeited = np.zeros(repetitions, dtype=np.int32)
    for epoch, target in enumerate(targets, 1):
        epoch_rng = np.random.default_rng(seed + epoch * 1_000_003)
        event = strategic_epoch_minimum(
            epoch_rng, float(target), g1, g2, alpha,
            "record-honest" if policy == "honest" else policy,
            geology=initial.geology,
        )
        minimum = event["minimum"]
        forfeited += event["forfeited_blocks"]
        g1, g2, found = transition_arrays(initial.geology, g1, g2, minimum)
        deposits += found
    return {"deposits": deposits, "forfeited_blocks": forfeited,
            "terminal_g1": g1, "terminal_g2": g2}


def write_rows(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "simulation-results.json")
    parser.add_argument("--csv", type=Path, default=HERE / "simulation-results.csv")
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    result = build_results(args.repetitions, args.seed)
    rows = result["rows"]
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    summary = {key: value for key, value in result.items() if key != "rows"}
    summary["row_count"] = len(rows)
    summary["rows_file"] = args.csv.name
    summary["row_fields"] = fieldnames
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_rows(args.csv, rows)
    print(json.dumps({
        "rows": len(rows),
        "stress": result["unavailable-prior-stress-and-equivalent-baseline"],
    }, indent=2))


if __name__ == "__main__":
    main()
