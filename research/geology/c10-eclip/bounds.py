#!/usr/bin/env python3
"""Deterministic envelope and rare-crossing Monte Carlo for one C10-eclip omission.

The calculations use continuous log/hash coordinates and are research models,
not consensus arithmetic.  The output deliberately retains a falsified 4.300
boundary calculation beside the corrected 5.300 Lyapunov model bound so the
failed bound is not silently erased.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
E = math.e
SEED = 0xC10B0A7D
ADAPTIVE_SEED = 20260903


def clipped_step(g1: np.ndarray, g2: np.ndarray,
                 m: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    deposit = m < g2
    unique = m < g1
    second = (~unique) & deposit
    n1 = g1.copy()
    n2 = g2.copy()
    n2[unique] = g1[unique]
    n1[unique] = np.maximum(m[unique], n2[unique] / E)
    n2[second] = m[second]
    return n1, n2, deposit


def rare_limit_max_pair(repetitions: int, seed: int) -> dict:
    """Couple maximal e-separated tight/loose states until coalescence."""
    rng = np.random.default_rng(seed)
    loose1 = np.full(repetitions, 1.0 / E)
    loose2 = np.ones(repetitions)
    tight1 = np.full(repetitions, 1.0 / (E * E))
    tight2 = np.full(repetitions, 1.0 / E)
    advantage = np.zeros(repetitions, dtype=np.int32)
    active = np.ones(repetitions, dtype=np.bool_)
    iterations = 0
    while np.any(active):
        iterations += 1
        if iterations > 10_000:
            raise RuntimeError("rare-limit coupling did not coalesce")
        idx = np.flatnonzero(active)
        # Condition on the next observation that crosses the loose G2.  In the
        # rare-event uniform-hash limit, its ratio to loose G2 is U(0,1).
        m = loose2[idx] * rng.random(len(idx))
        l1, l2, ld = clipped_step(loose1[idx], loose2[idx], m)
        t1, t2, td = clipped_step(tight1[idx], tight2[idx], m)
        advantage[idx] += ld.astype(np.int32) - td.astype(np.int32)
        loose1[idx], loose2[idx] = l1, l2
        tight1[idx], tight2[idx] = t1, t2
        active[idx] = ~((l1 == t1) & (l2 == t2))
    mean = float(np.mean(advantage))
    se = float(np.std(advantage, ddof=1) / math.sqrt(repetitions))
    return {
        "model": "rare-crossing fixed-target maximal e-separated state pair",
        "initial_loose_g1_g2": [1.0 / E, 1.0],
        "initial_tight_g1_g2": [1.0 / (E * E), 1.0 / E],
        "repetitions": repetitions,
        "seed": seed,
        "mean_extra_future_deposits": mean,
        "standard_error": se,
        "ci95": [mean - 1.96 * se, mean + 1.96 * se],
        "maximum_sample": int(np.max(advantage)),
        "maximum_embedded_crossings_until_all_coalesced": iterations,
    }


def log_step(a: np.ndarray, b: np.ndarray,
             z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    new_a = a.copy()
    new_b = b.copy()
    second = (z > a) & (z <= b)
    unique = z > b
    new_a[second] = z[second]
    new_a[unique] = b[unique]
    new_b[unique] = np.minimum(z[unique], b[unique] + 1.0)
    return new_a, new_b


def adaptive_reset_stress(repetitions: int, seed: int = ADAPTIVE_SEED) -> dict:
    """Reproduce a state-adaptive rare-tail/deep-reset stress policy.

    The controller observes only current paired state.  A rare action samples
    the limiting Exp(1) log depth conditional on a loose crossing.  A deep
    action places support beyond both clip boundaries and uses a representative
    value.  This is an ideal target-control stress, not a Bitcoin forecast.
    """
    rng = np.random.default_rng(seed)
    la = np.zeros(repetitions)
    lb = np.ones(repetitions)
    ha = np.ones(repetitions)
    hb = np.full(repetitions, 2.0)
    extra = np.zeros(repetitions, dtype=np.int32)
    active = np.ones(repetitions, dtype=np.bool_)
    iterations = 0
    while np.any(active):
        iterations += 1
        if iterations > 10_000:
            raise RuntimeError("adaptive stress did not coalesce")
        idx = np.flatnonzero(active)
        da = ha[idx] - la[idx]
        db = hb[idx] - lb[idx]
        translated = (
            (np.abs((lb[idx] - la[idx]) - 1.0) < 1e-12)
            & (np.abs((hb[idx] - ha[idx]) - 1.0) < 1e-12)
            & (np.abs(da - db) < 1e-12)
        )
        force_deep = (db >= da - 1e-14) & ~translated
        z = la[idx] + rng.exponential(size=len(idx))
        z[force_deep] = np.maximum(lb[idx][force_deep] + 1.0,
                                   hb[idx][force_deep] + 1.0) + 100.0
        extra[idx] += ((z > la[idx]) & (z <= ha[idx])).astype(np.int32)
        nla, nlb = log_step(la[idx], lb[idx], z)
        nha, nhb = log_step(ha[idx], hb[idx], z)
        shift = nla
        la[idx] = 0.0
        lb[idx] = nlb - shift
        ha[idx] = nha - shift
        hb[idx] = nhb - shift
        active[idx] = ~(
            (np.abs(la[idx] - ha[idx]) < 1e-12)
            & (np.abs(lb[idx] - hb[idx]) < 1e-12)
        )
    mean = float(np.mean(extra))
    se = float(np.std(extra, ddof=1) / math.sqrt(repetitions))
    return {
        "model": "state-adaptive rare-tail/deep-reset embedded-event stress",
        "repetitions": repetitions,
        "seed": seed,
        "mean_extra_future_deposits": mean,
        "standard_error": se,
        "ci95": [mean - 1.96 * se, mean + 1.96 * se],
        "maximum_sample": int(np.max(extra)),
        "maximum_policy_steps_until_all_coalesced": iterations,
    }


def envelope_value(delta: float, steps: int = 200_000) -> dict:
    """Solve the attacker-favorable Volterra envelope by RK4 quadrature.

    With A(d)=int_0^d exp(r)V(r)dr and B(d)=int_0^d exp(-r)V(r)dr,
    A'=exp(d)V and B'=exp(-d)V.  V is recovered algebraically from the
    envelope equation at each Runge--Kutta stage.
    """
    if not 0.0 <= delta <= 1.0:
        raise ValueError("delta must lie in [0,1]")

    def value(d: float, a: float, b: float) -> float:
        denominator = math.exp(-1.0) - math.exp(-2.0 - d)
        numerator = (1.0 - math.exp(-d)
                     + math.exp(-1.0 - d) * a + math.exp(-2.0) * b)
        return numerator / denominator

    def derivative(d: float, a: float, b: float) -> tuple[float, float]:
        v = value(d, a, b)
        return math.exp(d) * v, math.exp(-d) * v

    h = delta / steps if steps else 0.0
    d = a = b = 0.0
    for _ in range(steps):
        k1a, k1b = derivative(d, a, b)
        k2a, k2b = derivative(d + h / 2, a + h * k1a / 2, b + h * k1b / 2)
        k3a, k3b = derivative(d + h / 2, a + h * k2a / 2, b + h * k2b / 2)
        k4a, k4b = derivative(d + h, a + h * k3a, b + h * k3b)
        a += h * (k1a + 2 * k2a + 2 * k3a + k4a) / 6
        b += h * (k1b + 2 * k2b + 2 * k3b + k4b) / 6
        d += h
    return {
        "delta": delta,
        "steps": steps,
        "V_delta": value(delta, a, b),
        "equation": (
            "(e^-1-e^(-2-d))V(d)=1-e^-d+integral_0^d"
            "[e^(r-1-d)+e^(-2-r)]V(r)dr"
        ),
        "interpretation": (
            "Conservative model-bound after enlarging to boundary states and "
            "granting costless deep resets; not a realistic attack estimate."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "boundedness-results.json")
    parser.add_argument("--repetitions", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    result = {
        "schema": "goldatom-c10-eclip-single-omission-bounds-v1",
        "status": "adversarial research; continuous approximation, not consensus code",
        "log_coordinate_nonexpansion": {
            "maximum_initial_coordinate_separation_nats": 1.0,
            "statement": (
                "A qualifier-selection outcome differs by at most one nat in each "
                "frontier coordinate, and common clipped transitions do not enlarge it."
            ),
        },
        "direct_maximal_pair_monte_carlo": rare_limit_max_pair(
            args.repetitions, args.seed
        ),
        "fixed_target_rare_limit_analytic": {
            "potential_weight_e_over_e_minus_1": E / (E - 1.0),
            "single_omission_supremum_expected_extra_deposits": (
                (2.0 * E - 1.0) / (E - 1.0)
            ),
            "scope": "continuous rare-crossing, constant-target limit",
        },
        "refuted_4_300_boundary_calculation": {
            **envelope_value(1.0),
            "interpretation": (
                "Refuted boundary-state calculation retained for provenance; "
                "it is neither an upper bound nor a realistic attack estimate."
            ),
            "valid_upper_bound": False,
            "reason": (
                "Boundary-state reset does not dominate every interior paired state; "
                "the calculation is retained as falsified evidence, not used in verdict."
            ),
            "counterexample_log_states": {
                "loose": [0.0, 0.6249070258],
                "tight": [0.4431755803, 0.8199775082],
                "observation_relative_log_depth": 1.3677044043,
            },
        },
        "target_uniform_continuous_model_bound": {
            "middle_band_probability_e_minus_1_minus_e_minus_2": (
                math.exp(-1.0) - math.exp(-2.0)
            ),
            "lyapunov_coefficient": (
                1.0 + 1.0 / (math.exp(-1.0) - math.exp(-2.0))
            ),
            "single_omission_expected_extra_deposit_bound": (
                1.0 + 1.0 / (math.exp(-1.0) - math.exp(-2.0))
            ),
            "lyapunov": (
                "C*delta_G1_log + max(delta_G2_log-delta_G1_log,0)"
            ),
            "scope": (
                "continuous uniform-PoW epoch-min model, including a common target "
                "chosen adaptively before each epoch; divergent counterfactual target "
                "paths and exact integer/discrete lift remain open"
            ),
            "proof_method": (
                "piecewise-affine transition case split plus conditional log-depth "
                "density ratio f_p(q+t)/f_p(q)>=exp(-t)"
            ),
        },
        "adaptive_policy_stress": adaptive_reset_stress(args.repetitions),
        "pathwise_bound": {
            "exists": False,
            "note": (
                "Arbitrarily long positive-probability reward/reset paths exist; the "
                "finite bound is in expectation, matching the task's criterion."
            ),
        },
        "control_classification": {
            "raw-record": "D-unbounded-from-one-event",
            "c10-unclipped": "D-unbounded-from-one-event",
            "c10-eclip": "A-uniformly-bounded-single-event-model",
        },
        "long_run_classification": {
            "constant_or_eventual_plateau": (
                "asymptotic order-statistic model: lambda=O(1/n), multiple-qualifier "
                "opportunities O(1/n^2) and summable; simulations are finite-horizon"
            ),
            "target_path_sustaining_positive_crossing_intensity": (
                "B-per-opportunity-bounded-but-cumulatively-linear"
            ),
        },
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
