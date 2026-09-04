#!/usr/bin/env python3
"""Independent coupled Monte Carlo for one-intervention influence.

The event-driven sampler is exact in the registered small-q scale limit: after
discarding epochs whose minimum is above both live bars, the next relevant
epoch minimum is uniform on the larger bar.  A second sampler uses the exact
minimum-of-2016 conditional CDF at each historical target ratio.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Callable


W = 2016
MASTER_SEED = 1269070838


def stream_seed(label: str) -> int:
    payload = f"{MASTER_SEED}:{label}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")


def step(state: tuple[float, float], value: float) -> tuple[tuple[float, float], int]:
    g1, g2 = state
    if value < g1:
        return (max(value, g1 / math.e), g1), 1
    if value < g2:
        return (g1, value), 1
    return state, 0


def conditional_epoch_minimum(rng: random.Random, upper: float, exact: bool) -> float:
    if not exact:
        return rng.random() * upper
    # F(x)=1-(1-x)^W for the minimum of W uniforms on [0,1].
    f_upper = 1.0 if upper == 1.0 else -math.expm1(W * math.log1p(-upper))
    f_value = rng.random() * f_upper
    return -math.expm1(math.log1p(-f_value) / W)


def coupled_trial(
    rng: random.Random,
    honest: tuple[float, float],
    attacked: tuple[float, float],
    exact: bool,
    event_cap: int = 10_000,
) -> tuple[int, int]:
    delta = 0
    for event_count in range(event_cap + 1):
        if honest == attacked:
            return delta, event_count
        upper = max(honest[1], attacked[1])
        value = conditional_epoch_minimum(rng, upper, exact)
        honest, honest_deposit = step(honest, value)
        attacked, attacked_deposit = step(attacked, value)
        delta += attacked_deposit - honest_deposit
    raise RuntimeError("coupling did not reconverge before event cap")


def summarize_samples(samples: list[int], event_counts: list[int]) -> dict[str, object]:
    ordered = sorted(samples)
    n = len(samples)

    def empirical(probability: float) -> int:
        return ordered[max(0, min(n - 1, math.ceil(probability * n) - 1))]

    mean = sum(samples) / n
    second = sum(item * item for item in samples) / n
    standard_error = math.sqrt(max(0.0, second - mean * mean) / n)
    return {
        "trials": n,
        "mean": mean,
        "standard_error": standard_error,
        "ci95_normal": [mean - 1.96 * standard_error, mean + 1.96 * standard_error],
        "median": empirical(0.50),
        "p90": empirical(0.90),
        "p95": empirical(0.95),
        "p99": empirical(0.99),
        "maximum": max(samples),
        "mean_relevant_events_to_reconvergence": sum(event_counts) / n,
        "maximum_relevant_events_to_reconvergence": max(event_counts),
    }


def run_pair(
    label: str,
    honest: tuple[float, float],
    attacked: tuple[float, float],
    trials: int,
    exact: bool,
) -> dict[str, object]:
    if not (
        0 < honest[0] <= honest[1] <= attacked[1] <= 1
        and honest[0] <= attacked[0]
        and attacked[0] <= attacked[1]
    ):
        raise ValueError((honest, attacked))
    rng = random.Random(stream_seed(label))
    samples: list[int] = []
    events: list[int] = []
    for _ in range(trials):
        delta, event_count = coupled_trial(rng, honest, attacked, exact)
        samples.append(delta)
        events.append(event_count)
    result = summarize_samples(samples, events)
    result.update(
        {
            "label": label,
            "honest_state": list(honest),
            "attacked_state": list(attacked),
            "conditional_sampler": "exact minimum-of-2016 CDF" if exact else "small-q scale limit",
            "seed": stream_seed(label),
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--scale-limit-trials", type=int, default=2_000_000)
    parser.add_argument("--historical-trials", type=int, default=100_000)
    args = parser.parse_args()

    # Limiting post-intervention states reached from a valid pre-state with
    # G1/G2=1/e, an arbitrarily deep published honest minimum, and a retained
    # shallow observation arbitrarily close to G2.
    limiting = run_pair(
        "limiting-extreme",
        (math.exp(-2), math.exp(-1)),
        (math.exp(-1), 1.0),
        args.scale_limit_trials,
        exact=False,
    )

    source = json.loads(Path(args.historical_summary).read_text(encoding="utf-8"))
    historical: list[dict[str, object]] = []
    for fork in source["historical_prefer_second_forks"]:
        target = int(fork["target"])
        honest = (
            int(fork["honest_post_g1"]) / target,
            int(fork["honest_post_g2"]) / target,
        )
        attacked = (
            int(fork["attacked_post_g1"]) / target,
            int(fork["attacked_post_g2"]) / target,
        )
        historical.append(
            run_pair(
                f"historical-epoch-{fork['epoch']}",
                honest,
                attacked,
                args.historical_trials,
                exact=True,
            )
            | {"epoch": fork["epoch"]}
        )

    output = {
        "master_seed": MASTER_SEED,
        "semantics": {
            "delta": "future attacked deposits minus future honest deposits; current epoch excluded",
            "scale_limit": "T=1 and G2->0, so a relevant epoch minimum is uniform below the larger live bar",
            "exact_historical": "T=1 normalization with F(x)=1-(1-x)^2016",
            "bar_only_bound": "log(attacked_G2/honest_G2) <= 1 when the bar ratio is <= e",
            "complete_state_claim_tested": "the claimed <=2 bound for both coordinates",
        },
        "limiting_extreme": limiting,
        "historical": historical,
        "largest_historical_mean": max(historical, key=lambda item: item["mean"]),
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
