#!/usr/bin/env python3
"""Deterministic Monte Carlo models for raw-record publication strategies.

Hashes are represented as uniform real values conditional on Bitcoin validity:
0 <= x < 1.  The normalized raw frontier f is F/T.  Each draw is one ordinary
Bitcoin-valid proof-of-work solution; withholding never creates a free draw.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

CURRENT_P = 2.489175366907752e-06
ALPHAS = (0.01, 0.10, 0.20, 0.30, 0.50)


def analytic_continue(alpha: float, p: float) -> dict[str, float]:
    """Attacker discards every non-record solution until honest wins or it records."""
    denominator = 1.0 - alpha + alpha * p
    attacker_record = alpha * p / denominator
    canonical_record = p / denominator
    forfeited = alpha * (1.0 - p) / denominator
    return {
        "alpha": alpha,
        "attacker_record_before_honest": attacker_record,
        "canonical_deposit_probability": canonical_record,
        "delta_vs_honest": canonical_record - p,
        "expected_forfeited_bitcoin_blocks_per_canonical_block": forfeited,
        "break_even_V_GA_over_R_for_attacker_control": ((1.0 - alpha) / (alpha * p)
                                                          if alpha else None),
    }


def deep_withholding_break_even(frontier: float, improvement_factor: float,
                                limit: int = 10_000_000) -> dict[str, float]:
    """Compare withholding a found x=frontier/factor with publishing it.

    At the same final chain height, publishing gives 1+E_n(x), while
    withholding replaces the candidate height and gives E_(n+1)(frontier).
    """
    x = frontier / improvement_factor
    qa = 1.0 - frontier
    qb = 1.0
    expected_a = frontier
    expected_b = 0.0
    delta = expected_a - 1.0
    first_positive = None
    for n in range(1, limit + 1):
        qa *= 1.0 - frontier
        qb *= 1.0 - x
        expected_a += (1.0 - qa) / (n + 1)
        expected_b += (1.0 - qb) / n
        delta = expected_a - 1.0 - expected_b
        if delta > 0.0:
            first_positive = n
            break
    return {
        "found_hash_improvement_factor_F_over_x": improvement_factor,
        "found_hash_improvement_bits": math.log2(improvement_factor),
        "asymptotic_net_additional_deposits": math.log(improvement_factor) - 1.0,
        "first_positive_horizon_canonical_blocks": first_positive,
    }


def deep_cutoff_policy(alpha: float, p: float, cutoff: float) -> dict[str, float]:
    """Asymptotic constant-target effect of censoring attacker records x<cF."""
    mean_log_improvement = (1.0 - alpha * cutoff * (1.0 - math.log(cutoff))) / (1.0 - alpha * cutoff)
    coefficient = 1.0 / mean_log_improvement
    return {
        "alpha": alpha,
        "cutoff_c": cutoff,
        "censorship_opportunity_probability_per_valid_solution": alpha * cutoff * p,
        "mean_log_frontier_improvement_per_accepted_record": mean_log_improvement,
        "asymptotic_record_count_coefficient_vs_honest": coefficient,
        "relative_count_increase": coefficient - 1.0,
        "expected_net_extra_records_per_censored_opportunity": -math.log(cutoff),
        "break_even_V_GA_over_R_if_all_global_count_value_is_captured": 1.0 / -math.log(cutoff),
    }


def one_run(strategy: str, alpha: float, blocks: int, initial_frontier: float,
            seed: int, deep_cutoff: float = 0.1, gamma: float = 0.5) -> dict[str, float]:
    rng = random.Random(seed)
    frontier = initial_frontier
    deposits = forfeited = solutions = attacker_deposits = orphaned = canonical = 0
    while canonical < blocks:
        withheld_once = False
        while True:
            solutions += 1
            attacker = rng.random() < alpha
            value = rng.random()
            record = value < frontier
            if strategy == "private_fork_search" and attacker and not record:
                # One-block private lead, truncated selfish-mining model.  The
                # attacker seeks a second block; an honest find creates a tie.
                solutions += 1
                second_attacker = rng.random() < alpha
                second_value = rng.random()
                if second_attacker:
                    canonical += 1  # private non-record parent
                    if canonical < blocks:
                        canonical += 1
                        if second_value < frontier:
                            deposits += 1
                            attacker_deposits += 1
                            frontier = second_value
                else:
                    orphaned += 1
                    if rng.random() < gamma:
                        canonical += 1  # attacker's non-record wins the tie
                    else:
                        forfeited += 1
                        canonical += 1
                        if second_value < frontier:
                            deposits += 1
                            frontier = second_value
                break
            discard = False
            if strategy in ("withhold_nonrecord", "selective_publication"):
                discard = attacker and not record
            elif strategy == "withhold_record":
                discard = attacker and record
            elif strategy == "withhold_deep_record":
                discard = attacker and value < deep_cutoff * frontier
            elif strategy not in ("honest", "private_fork_search"):
                raise ValueError(strategy)
            if discard:
                forfeited += 1
                withheld_once = True
                continue
            if record:
                deposits += 1
                attacker_deposits += int(attacker)
                frontier = value
            canonical += 1
            break
    return {
        "deposits": deposits,
        "attacker_deposits": attacker_deposits,
        "forfeited_blocks": forfeited,
        "ordinary_pow_solutions": solutions,
        "orphaned_blocks": orphaned,
        "terminal_frontier": frontier,
    }


def run_rows(strategy: str, alpha: float, blocks: int, initial_frontier: float,
             repetitions: int, seed: int):
    return [one_run(strategy, alpha, blocks, initial_frontier,
                    seed + 1_000_003 * i) for i in range(repetitions)]


def summarize(strategy: str, alpha: float, rows, baseline_rows) -> dict[str, float]:
    repetitions = len(rows)
    avg = lambda key: sum(r[key] for r in rows) / repetitions
    deltas = [r["deposits"] - b["deposits"] for r, b in zip(rows, baseline_rows)]
    delta = sum(deltas) / repetitions
    variance = sum((x - delta) ** 2 for x in deltas) / (repetitions - 1)
    half_width = 1.96 * math.sqrt(variance / repetitions)
    return {
        "strategy": strategy,
        "alpha": alpha,
        "mean_canonical_deposits": avg("deposits"),
        "mean_attacker_deposits": avg("attacker_deposits"),
        "mean_forfeited_bitcoin_blocks": avg("forfeited_blocks"),
        "mean_ordinary_pow_solutions": avg("ordinary_pow_solutions"),
        "mean_orphaned_blocks": avg("orphaned_blocks"),
        "mean_terminal_frontier": avg("terminal_frontier"),
        "delta_mean_canonical_deposits_vs_honest": delta,
        "delta_95_percent_interval": [delta - half_width, delta + half_width],
    }


def build_results(blocks=20_000, repetitions=250, seed=0x474131,
                  initial_frontier=0.01):
    strategies = ("honest", "withhold_nonrecord", "withhold_record",
                  "withhold_deep_record", "private_fork_search",
                  "selective_publication")
    stress = []
    for alpha in ALPHAS:
        baseline_rows = run_rows("honest", alpha, blocks, initial_frontier,
                                 repetitions, seed)
        for strategy in strategies:
            rows = baseline_rows if strategy == "honest" else run_rows(
                strategy, alpha, blocks, initial_frontier, repetitions, seed)
            row = summarize(strategy, alpha, rows, baseline_rows)
            stress.append(row)
    return {
        "schema": "goldatom-raw-record-miner-adversary-v1",
        "current_frontier_fixed_state_analytic": [analytic_continue(a, CURRENT_P) for a in ALPHAS],
        "deep_record_withholding_exact": {
            "comparison": "withhold found record x versus publish it, compared at the same final canonical height",
            "criterion": "Asymptotically net-positive iff F/x > e.",
            "current_frontier_over_target": CURRENT_P,
            "rows": [deep_withholding_break_even(CURRENT_P, factor)
                     for factor in (3, 5, 10, 100, 1_000_000)],
        },
        "deep_cutoff_policy_exact": {
            "constant_target_cutoff_c": 0.1,
            "rows": [deep_cutoff_policy(a, CURRENT_P, 0.1) for a in ALPHAS],
        },
        "monte_carlo_stress_test": {
            "note": "Elevated initial F/T makes strategy differences measurable; this is not a forecast of Bitcoin deposits.",
            "strategy_aliases": {"selective_publication": "withhold_nonrecord"},
            "seed": seed,
            "repetitions": repetitions,
            "canonical_blocks_per_repetition": blocks,
            "initial_frontier_over_target": initial_frontier,
            "deep_record_cutoff_fraction_of_frontier": 0.1,
            "results": stress,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--blocks", type=int, default=20_000)
    ap.add_argument("--repetitions", type=int, default=250)
    ap.add_argument("--seed", type=int, default=0x474131)
    args = ap.parse_args()
    result = build_results(args.blocks, args.repetitions, args.seed)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
