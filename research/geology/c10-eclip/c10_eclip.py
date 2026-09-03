#!/usr/bin/env python3
"""Historical C10-eclip replay and exact finite-binomial diagnostics.

This is research tooling, not consensus code.  Bitcoin proof-of-work hashes are
unsigned integers in Bitcoin display order, as implemented by the parent
record-geology scanner.  The e-clip uses an exact rational enclosure of e to
certify every integer ceil(G2/e); no binary floating-point value determines a
historical transition.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from pathlib import Path


GEOLOGY_DIR = Path(__file__).resolve().parents[1]
if str(GEOLOGY_DIR) not in sys.path:
    sys.path.insert(0, str(GEOLOGY_DIR))

import goldatom_ledger as bitcoin


W = 2016
E_SERIES_TERMS = 180


@lru_cache(maxsize=1)
def e_bounds() -> tuple[Fraction, Fraction]:
    """Return rigorous rational lower/upper bounds around Euler's number.

    The lower bound is sum(1/k!, k=0..n).  For n>=1 the omitted positive tail
    is less than 1/(n*n!), which supplies the upper bound.
    """
    factorial = 1
    lower = Fraction(1, 1)
    for k in range(1, E_SERIES_TERMS + 1):
        factorial *= k
        lower += Fraction(1, factorial)
    upper = lower + Fraction(1, E_SERIES_TERMS * factorial)
    return lower, upper


def ceil_div_e(value: int) -> int:
    """Compute ceil(value/e) as an integer and certify it with e bounds."""
    if value < 0:
        raise ValueError("frontiers must be nonnegative")
    if value == 0:
        return 0
    lower, upper = e_bounds()
    candidate = (value * lower.denominator + lower.numerator - 1) // lower.numerator
    if lower * candidate < value:
        raise AssertionError("lower-bound clip certificate failed")
    if upper * (candidate - 1) >= value:
        raise ArithmeticError("e enclosure cannot distinguish adjacent integers")
    return candidate


def ratio_at_most_e(g1: int, g2: int) -> bool:
    if not 0 <= g1 <= g2:
        return False
    lower, upper = e_bounds()
    if lower * g1 >= g2:
        return True
    if upper * g1 < g2:
        return False
    raise ArithmeticError("e enclosure is too narrow to classify ratio")


@dataclass(frozen=True)
class State:
    g1: int
    g2: int

    def __post_init__(self) -> None:
        if not 0 <= self.g1 <= self.g2:
            raise ValueError("state requires 0 <= G1 <= G2")
        if not ratio_at_most_e(self.g1, self.g2):
            raise ValueError("state violates G2/G1 <= e")


@dataclass(frozen=True)
class Transition:
    before: State
    observation: int
    deposit: bool
    kind: str
    after: State


def initialize(a: int, b: int) -> State:
    g2 = max(a, b)
    q = min(a, b)
    return State(max(q, ceil_div_e(g2)), g2)


def transition(state: State, observation: int) -> Transition:
    """Apply the clipped order-2 transition; deposit uses pre-state G2."""
    if observation < 0:
        raise ValueError("observation must be unsigned")
    deposit = observation < state.g2
    if observation < state.g1:
        next_g2 = state.g1
        after = State(max(observation, ceil_div_e(next_g2)), next_g2)
        kind = "unique-min"
    elif observation < state.g2:
        after = State(state.g1, observation)
        kind = "new-second"
    else:
        after = state
        kind = "neither"
    return Transition(state, observation, deposit, kind, after)


def natural_initialize(a: int, b: int) -> tuple[int, int]:
    return min(a, b), max(a, b)


def natural_transition(state: tuple[int, int], observation: int) -> tuple[int, int]:
    g1, g2 = state
    if observation < g1:
        return observation, g1
    if observation < g2:
        return g1, observation
    return state


@dataclass(frozen=True)
class Block:
    height: int
    timestamp: int
    hash_int: int
    block_hash: str
    target: int
    bits: int


def utc(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def load_blocks(headers_path: Path) -> list[Block]:
    headers = bitcoin.read_headers(headers_path)
    bitcoin.validate_chain(headers)
    blocks: list[Block] = []
    for height, raw in enumerate(headers):
        _, _, _, timestamp, bits, _ = bitcoin.header_fields(raw)
        blocks.append(Block(
            height=height,
            timestamp=timestamp,
            hash_int=bitcoin.hash_int(raw),
            block_hash=bitcoin.display_hash(raw),
            target=bitcoin.decode_compact(bits),
            bits=bits,
        ))
    return blocks


def exact_crossing_probability(g2: int, target: int) -> float:
    """P(H < G2 | H is uniform over the valid integers 0..T)."""
    return min(g2, target + 1) / (target + 1)


def binomial_crossing_stats(p: float, trials: int = W) -> dict[str, float]:
    if p <= 0.0:
        p0, p1, at_least_one, at_least_two = 1.0, 0.0, 0.0, 0.0
    elif p >= 1.0:
        p0, p1, at_least_one = 0.0, float(trials == 1), 1.0
        at_least_two = float(trials >= 2)
    else:
        log_q = math.log1p(-p)
        p0 = math.exp(trials * log_q)
        p1 = trials * p * math.exp((trials - 1) * log_q)
        at_least_one = -math.expm1(trials * log_q)
        at_least_two = max(0.0, at_least_one - p1)
    return {
        "p": p,
        "trials": trials,
        "lambda": trials * p,
        "p_k_ge_1": at_least_one,
        "p_k_ge_2": at_least_two,
        "p_k_ge_2_given_k_ge_1": at_least_two / at_least_one if at_least_one else 0.0,
    }


def poisson_crossing_stats(lam: float) -> dict[str, float]:
    p0 = math.exp(-lam)
    p1 = lam * p0
    at_least_one = -math.expm1(-lam)
    at_least_two = max(0.0, at_least_one - p1)
    return {
        "lambda": lam,
        "p_k_ge_1": at_least_one,
        "p_k_ge_2": at_least_two,
        "p_k_ge_2_given_k_ge_1": at_least_two / at_least_one if at_least_one else 0.0,
    }


def exact_decimal_binomial_stats(g2: int, target: int, trials: int = W) -> dict[str, str]:
    """High-precision evaluation of the exact discrete finite-binomial model."""
    with localcontext() as context:
        context.prec = 90
        p = Decimal(min(g2, target + 1)) / Decimal(target + 1)
        q = Decimal(1) - p
        p0 = q ** trials
        p1 = Decimal(trials) * p * (q ** (trials - 1))
        ge1 = Decimal(1) - p0
        ge2 = ge1 - p1
        conditional = ge2 / ge1 if ge1 else Decimal(0)
        return {
            "p": str(p),
            "lambda": str(Decimal(trials) * p),
            "p_k_ge_1": str(ge1),
            "p_k_ge_2": str(ge2),
            "p_k_ge_2_given_k_ge_1": str(conditional),
        }


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile of empty sample")
    index = (len(ordered) - 1) * probability
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    weight = index - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def state_dict(state: State | None) -> dict | None:
    if state is None:
        return None
    return {
        "g1": str(state.g1),
        "g2": str(state.g2),
        "g1_hex": f"{state.g1:064x}",
        "g2_hex": f"{state.g2:064x}",
        "g2_over_g1": state.g2 / state.g1 if state.g1 else None,
    }


def replay(headers_path: Path) -> tuple[dict, list[dict], list[dict]]:
    blocks = load_blocks(headers_path)
    source_metadata_path = GEOLOGY_DIR / "source.json"
    source_metadata = (
        json.loads(source_metadata_path.read_text(encoding="utf-8"))
        if source_metadata_path.exists() else None
    )
    complete_epochs = len(blocks) // W
    epochs = [blocks[i * W:(i + 1) * W] for i in range(complete_epochs)]
    minima = [min(epoch, key=lambda block: block.hash_int) for epoch in epochs]
    rows: list[dict] = []
    crossings_out: list[dict] = []

    state: State | None = None
    natural: tuple[int, int] | None = None
    ratios: list[float] = []
    lambdas: list[float] = []
    deposits = 0
    historical_selective_epochs = 0
    worst: dict | None = None
    worst_potential: dict | None = None
    max_natural_ratio = 0.0

    for index, (epoch, minimum) in enumerate(zip(epochs, minima)):
        target = epoch[0].target
        if index == 0:
            rows.append({
                "epoch": index,
                "start_height": epoch[0].height,
                "end_height": epoch[-1].height,
                "target": str(target),
                "target_hex": f"{target:064x}",
                "epoch_minimum": str(minimum.hash_int),
                "epoch_minimum_hex": f"{minimum.hash_int:064x}",
                "epoch_minimum_height": minimum.height,
                "pre_g1": "",
                "pre_g2": "",
                "pre_g2_over_g1": "",
                "lambda": "",
                "deposit": "",
                "transition_class": "initialization-input-1",
                "crossing_count": "",
                "selective_opportunity": "",
                "deeper_records_after_first_crossing": "",
                "max_shallow_over_deep": "",
                "post_g1": "",
                "post_g2": "",
            })
            continue
        if index == 1:
            state = initialize(minima[0].hash_int, minima[1].hash_int)
            natural = natural_initialize(minima[0].hash_int, minima[1].hash_int)
            max_natural_ratio = natural[1] / natural[0]
            rows.append({
                "epoch": index,
                "start_height": epoch[0].height,
                "end_height": epoch[-1].height,
                "target": str(target),
                "target_hex": f"{target:064x}",
                "epoch_minimum": str(minimum.hash_int),
                "epoch_minimum_hex": f"{minimum.hash_int:064x}",
                "epoch_minimum_height": minimum.height,
                "pre_g1": "",
                "pre_g2": "",
                "pre_g2_over_g1": "",
                "lambda": "",
                "deposit": "",
                "transition_class": "initialize-clipped",
                "crossing_count": "",
                "selective_opportunity": "",
                "deeper_records_after_first_crossing": "",
                "max_shallow_over_deep": "",
                "post_g1": str(state.g1),
                "post_g2": str(state.g2),
            })
            continue

        assert state is not None and natural is not None
        before = state
        ratio = before.g2 / before.g1
        ratios.append(ratio)
        p = exact_crossing_probability(before.g2, target)
        lam = W * p
        lambdas.append(lam)
        crossings = [block for block in epoch if block.hash_int < before.g2]
        running = None
        first_crossing = crossings[0] if crossings else None
        deeper_records: list[Block] = []
        effective_deeper_records: list[Block] = []
        max_shallow_over_deep = 1.0
        for order, block in enumerate(crossings, 1):
            is_deeper = running is not None and block.hash_int < running.hash_int
            effective_if_first_preserved = False
            if is_deeper:
                deeper_records.append(block)
                shallow_state = transition(before, first_crossing.hash_int).after
                deep_state = transition(before, block.hash_int).after
                effective_if_first_preserved = shallow_state != deep_state
                if effective_if_first_preserved:
                    effective_deeper_records.append(block)
                    max_shallow_over_deep = max(
                        max_shallow_over_deep,
                        first_crossing.hash_int / block.hash_int if block.hash_int else math.inf,
                    )
            if running is None or block.hash_int < running.hash_int:
                running = block
            crossings_out.append({
                "epoch": index,
                "crossing_order": order,
                "height": block.height,
                "epoch_position": block.height % W,
                "utc": utc(block.timestamp),
                "block_hash": block.block_hash,
                "hash_integer": str(block.hash_int),
                "hash_integer_hex": f"{block.hash_int:064x}",
                "pre_g1": str(before.g1),
                "pre_g2": str(before.g2),
                "crosses_pre_g1": block.hash_int < before.g1,
                "hash_over_pre_g2": block.hash_int / before.g2,
                "depth_bits_below_g2": (
                    math.log2(before.g2 / block.hash_int) if block.hash_int else math.inf
                ),
                "lower_record_after_first_crossing": is_deeper,
                "state_effective_if_first_qualifier_preserved": effective_if_first_preserved,
            })
        selective = bool(effective_deeper_records)
        historical_selective_epochs += int(selective)
        if selective:
            candidate = {
                "epoch": index,
                "first_crossing_height": first_crossing.height,
                "first_crossing_hash": first_crossing.block_hash,
                "deepest_later_height": min(effective_deeper_records, key=lambda b: b.hash_int).height,
                "deepest_later_hash": min(effective_deeper_records, key=lambda b: b.hash_int).block_hash,
                "shallow_over_deep": max_shallow_over_deep,
                "crossing_count": len(crossings),
            }
            if worst is None or candidate["shallow_over_deep"] > worst["shallow_over_deep"]:
                worst = candidate
            shallow_state = transition(before, first_crossing.hash_int).after
            deepest = min(effective_deeper_records, key=lambda b: b.hash_int)
            deep_state = transition(before, deepest.hash_int).after
            weight = math.e / (math.e - 1.0)
            potential_gap = (
                -weight * math.log(deep_state.g1) - math.log(deep_state.g2)
                + weight * math.log(shallow_state.g1) + math.log(shallow_state.g2)
            )
            potential_candidate = {
                **candidate,
                "rare_limit_constant_target_potential_gap": potential_gap,
            }
            if (worst_potential is None
                    or potential_gap > worst_potential["rare_limit_constant_target_potential_gap"]):
                worst_potential = potential_candidate

        event = transition(before, minimum.hash_int)
        state = event.after
        deposits += int(event.deposit)
        natural = natural_transition(natural, minimum.hash_int)
        max_natural_ratio = max(max_natural_ratio, natural[1] / natural[0])
        rows.append({
            "epoch": index,
            "start_height": epoch[0].height,
            "end_height": epoch[-1].height,
            "target": str(target),
            "target_hex": f"{target:064x}",
            "epoch_minimum": str(minimum.hash_int),
            "epoch_minimum_hex": f"{minimum.hash_int:064x}",
            "epoch_minimum_height": minimum.height,
            "pre_g1": str(before.g1),
            "pre_g2": str(before.g2),
            "pre_g2_over_g1": ratio,
            "lambda": lam,
            "deposit": event.deposit,
            "transition_class": event.kind,
            "crossing_count": len(crossings),
            "selective_opportunity": selective,
            "deeper_records_after_first_crossing": len(deeper_records),
            "max_shallow_over_deep": max_shallow_over_deep if selective else "",
            "post_g1": str(state.g1),
            "post_g2": str(state.g2),
        })

    assert state is not None and natural is not None
    tip = blocks[-1]
    current_target = tip.target
    partial_epoch = blocks[complete_epochs * W:]
    partial_crossings = [block for block in partial_epoch if block.hash_int < state.g2]
    live_p = exact_crossing_probability(state.g2, current_target)
    natural_live_p = exact_crossing_probability(natural[1], current_target)
    evaluated = rows[2:]
    k_ge_1 = sum(int(row["crossing_count"]) >= 1 for row in evaluated)
    k_ge_2 = sum(int(row["crossing_count"]) >= 2 for row in evaluated)
    k_distribution = {
        str(k): sum(int(row["crossing_count"]) == k for row in evaluated)
        for k in sorted({int(row["crossing_count"]) for row in evaluated})
    }
    transition_counts = {
        kind: sum(row["transition_class"] == kind for row in evaluated)
        for kind in ("unique-min", "new-second", "neither")
    }
    model_rows = [
        binomial_crossing_stats(
            exact_crossing_probability(int(row["pre_g2"]), int(row["target"]))
        )
        for row in evaluated
    ]
    live_finite = binomial_crossing_stats(live_p)
    natural_finite = binomial_crossing_stats(natural_live_p)
    ownership_rows = []
    for alpha in (0.01, 0.10, 0.20, 0.30, 0.50, 1.00):
        grouped = {}
        for crossing in crossings_out:
            grouped.setdefault(crossing["epoch"], []).append(crossing)
        first_attacker = multiple_attacker = public_effective = owned_effective = 0.0
        effective_unique = mixed = 0.0
        for epoch_crossings in grouped.values():
            count = len(epoch_crossings)
            first_attacker += alpha
            multiple_attacker += (
                1.0 - (1.0 - alpha) ** count
                - count * alpha * (1.0 - alpha) ** (count - 1)
            )
            effective_count = sum(
                row["state_effective_if_first_qualifier_preserved"]
                for row in epoch_crossings
            )
            unique_count = sum(
                row["state_effective_if_first_qualifier_preserved"]
                and row["crosses_pre_g1"] for row in epoch_crossings
            )
            public_effective += 1.0 - (1.0 - alpha) ** effective_count
            owned_effective += alpha * (1.0 - (1.0 - alpha) ** effective_count)
            effective_unique += 1.0 - (1.0 - alpha) ** unique_count
            mixed += 1.0 - alpha ** count - (1.0 - alpha) ** count
        ownership_rows.append({
            "alpha": alpha,
            "expected_first_qualifier_attacker_epochs": first_attacker,
            "expected_epochs_with_at_least_two_attacker_qualifiers": multiple_attacker,
            "expected_state_effective_public_lock_opportunities": public_effective,
            "expected_attacker_first_then_effective_later_attacker_opportunities": owned_effective,
            "expected_state_effective_later_attacker_unique_min_opportunities": effective_unique,
            "expected_mixed_owner_qualifier_epochs": mixed,
        })
    summary = {
        "schema": "goldatom-c10-eclip-historical-v1",
        "status": "adversarial research; not a specification",
        "source": {
            "headers_file": headers_path.name,
            "headers_sha256": hashlib.sha256(headers_path.read_bytes()).hexdigest(),
            "headers_bytes": headers_path.stat().st_size,
            "header_count": len(blocks),
            "tip_height": tip.height,
            "tip_hash": tip.block_hash,
            "complete_difficulty_epochs": complete_epochs,
            "evaluated_post_initialization_epochs": len(evaluated),
            "partial_epoch": {
                "epoch": complete_epochs,
                "blocks_observed": len(partial_epoch),
                "blocks_remaining": W - len(partial_epoch),
                "first_height": partial_epoch[0].height if partial_epoch else None,
                "tip_position_zero_based": tip.height % W,
                "crossings_of_live_pre_epoch_g2_observed": len(partial_crossings),
                "warning": (
                    "Future simulations restart at a complete epoch boundary and "
                    "do not condition on this partial epoch."
                ),
            },
            "dataset_provenance": source_metadata,
        },
        "initialization": {
            "epoch_0_minimum": str(minima[0].hash_int),
            "epoch_1_minimum": str(minima[1].hash_int),
            "unclipped_g2_over_g1": max(minima[0].hash_int, minima[1].hash_int)
                                      / min(minima[0].hash_int, minima[1].hash_int),
            "clipped_state": state_dict(initialize(minima[0].hash_int, minima[1].hash_int)),
        },
        "invariant": {
            "e_series_terms": E_SERIES_TERMS,
            "all_reachable_historical_states_g2_over_g1_at_most_e": all(
                ratio_at_most_e(int(row["pre_g1"]), int(row["pre_g2"]))
                for row in evaluated
            ),
            "maximum_historical_clipped_g2_over_g1": max(ratios),
            "maximum_historical_unclipped_g2_over_g1": max_natural_ratio,
            "new_second_a0_max_ln_ratio_minus_one": max(
                0.0, max(math.log(value) - 1.0 for value in ratios)
            ),
        },
        "historical": {
            "deposits": deposits,
            "transition_counts": transition_counts,
            "lambda": {
                "minimum": min(lambdas),
                "median": statistics.median(lambdas),
                "mean": statistics.fmean(lambdas),
                "p90": percentile(lambdas, 0.90),
                "p95": percentile(lambdas, 0.95),
                "p99": percentile(lambdas, 0.99),
                "maximum": max(lambdas),
            },
            "epochs_k_ge_1": k_ge_1,
            "crossing_count_distribution": k_distribution,
            "fraction_epochs_k_ge_1": k_ge_1 / len(evaluated),
            "epochs_k_ge_2": k_ge_2,
            "fraction_epochs_k_ge_2": k_ge_2 / len(evaluated),
            "empirical_p_k_ge_2_given_k_ge_1": k_ge_2 / k_ge_1 if k_ge_1 else 0.0,
            "finite_binomial_expected_epochs_k_ge_1": sum(
                row["p_k_ge_1"] for row in model_rows
            ),
            "finite_binomial_expected_epochs_k_ge_2": sum(
                row["p_k_ge_2"] for row in model_rows
            ),
            "finite_binomial_aggregate_p_k_ge_2_given_k_ge_1": (
                sum(row["p_k_ge_2"] for row in model_rows)
                / sum(row["p_k_ge_1"] for row in model_rows)
            ),
            "epochs_with_monopoly_qualifier_selection_opportunity": historical_selective_epochs,
            "worst_historical_opportunity_by_hash_depth_ratio": worst,
            "worst_historical_opportunity_by_rare_limit_potential": worst_potential,
            "random_owner_label_model": {
                "warning": (
                    "Actual historical miner ownership was not inferred. Values randomly "
                    "label fixed observed headers Bernoulli(alpha); they are not attacked histories."
                ),
                "rows": ownership_rows,
            },
        },
        "live_c10_eclip": {
            "state": state_dict(state),
            "target": str(current_target),
            "target_hex": f"{current_target:064x}",
            "p_per_valid_block": live_p,
            "lambda_prompt_W_G2_over_T": W * state.g2 / current_target,
            "lambda_exact_discrete_W_G2_over_T_plus_1": W * live_p,
            "finite_binomial": live_finite,
            "finite_binomial_exact_decimal": exact_decimal_binomial_stats(
                state.g2, current_target
            ),
            "poisson_cross_check": poisson_crossing_stats(W * live_p),
        },
        "live_unclipped_c10_control": {
            "state": {"g1": str(natural[0]), "g2": str(natural[1]),
                      "g2_over_g1": natural[1] / natural[0]},
            "p_per_valid_block": natural_live_p,
            "lambda_prompt_W_G2_over_T": W * natural[1] / current_target,
            "lambda_exact_discrete_W_G2_over_T_plus_1": W * natural_live_p,
            "finite_binomial": natural_finite,
            "finite_binomial_exact_decimal": exact_decimal_binomial_stats(
                natural[1], current_target
            ),
            "poisson_cross_check": poisson_crossing_stats(W * natural_live_p),
        },
    }
    return summary, rows, crossings_out


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headers", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    summary, rows, crossings = replay(args.headers)
    args.outdir.mkdir(parents=True, exist_ok=True)
    (args.outdir / "historical-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(args.outdir / "historical-replay.csv", rows)
    write_csv(args.outdir / "historical-crossings.csv", crossings)
    print(json.dumps({
        "tip": summary["source"]["tip_height"],
        "live_lambda": summary["live_c10_eclip"]["lambda_prompt_W_G2_over_T"],
        "historical": summary["historical"],
    }, indent=2))


if __name__ == "__main__":
    main()
