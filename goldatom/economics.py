"""Pure economic stress-model helpers for GoldAtom research.

These functions are deliberately small and assumption-explicit. They are not
consensus code and do not make price or profitability predictions.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable


def producer_shares(producers: int, advantage: float) -> tuple[float, ...]:
    """Return normalized production shares for one advantaged producer.

    ``advantage`` is the advantaged producer's hashes per unit resource divided
    by every other producer's hashes per unit resource. All producers are
    assumed to commit the same resource budget.
    """
    if type(producers) is not int or producers < 2:
        raise ValueError("producers must be an integer >= 2")
    if not math.isfinite(advantage) or advantage <= 0:
        raise ValueError("advantage must be finite and > 0")
    denominator = advantage + producers - 1
    return (advantage / denominator,) + tuple(1.0 / denominator for _ in range(producers - 1))


def hhi(shares: Iterable[float]) -> float:
    values = tuple(shares)
    _validate_shares(values)
    return sum(value * value for value in values)


def effective_producers(shares: Iterable[float]) -> float:
    return 1.0 / hhi(shares)


def gini(shares: Iterable[float]) -> float:
    values = tuple(sorted(shares))
    _validate_shares(values)
    n = len(values)
    total = sum(values)
    weighted = sum((2 * index - n - 1) * value for index, value in enumerate(values, start=1))
    return weighted / (n * total)


def _validate_shares(values: tuple[float, ...]) -> None:
    if not values or any((not math.isfinite(value) or value < 0) for value in values):
        raise ValueError("shares must be finite and nonnegative")
    if sum(values) <= 0:
        raise ValueError("shares must have positive mass")


def binomial_tail(trials: int, probability: float, minimum_successes: int) -> float:
    """Exact P[X >= minimum_successes] for a Binomial(trials, probability)."""
    if type(trials) is not int or trials < 0:
        raise ValueError("trials must be a nonnegative integer")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be in [0, 1]")
    if type(minimum_successes) is not int:
        raise ValueError("minimum_successes must be an integer")
    if minimum_successes <= 0:
        return 1.0
    if minimum_successes > trials:
        return 0.0
    return sum(
        math.comb(trials, k)
        * probability**k
        * (1.0 - probability) ** (trials - k)
        for k in range(minimum_successes, trials + 1)
    )


@dataclass(frozen=True, slots=True)
class AuctionSimulation:
    epochs: int
    winners_per_epoch: int
    top_share_expected: float
    top_share_simulated: float
    majority_probability_exact: float
    majority_probability_simulated: float


def simulate_auction_top_producer(
    *,
    top_share: float,
    epochs: int,
    winners_per_epoch: int,
    seed: int,
) -> AuctionSimulation:
    """Monte Carlo check for a top producer in a sealed top-work auction.

    Each winning position is modeled as an independent draw proportional to
    hash share. This is the large-search-space limit for labels on the global
    order statistics. It does not model network latency or censorship.
    """
    if not 0.0 <= top_share <= 1.0:
        raise ValueError("top_share must be in [0, 1]")
    if type(epochs) is not int or epochs <= 0:
        raise ValueError("epochs must be a positive integer")
    if type(winners_per_epoch) is not int or winners_per_epoch <= 0:
        raise ValueError("winners_per_epoch must be a positive integer")

    rng = random.Random(seed)
    total_wins = 0
    majority_epochs = 0
    majority_threshold = math.ceil(winners_per_epoch / 2)
    for _ in range(epochs):
        wins = sum(rng.random() < top_share for _ in range(winners_per_epoch))
        total_wins += wins
        majority_epochs += wins >= majority_threshold

    return AuctionSimulation(
        epochs=epochs,
        winners_per_epoch=winners_per_epoch,
        top_share_expected=top_share,
        top_share_simulated=total_wins / (epochs * winners_per_epoch),
        majority_probability_exact=binomial_tail(
            winners_per_epoch,
            top_share,
            majority_threshold,
        ),
        majority_probability_simulated=majority_epochs / epochs,
    )


def variant_gate_probability(base_probability: float, variants: int) -> float:
    """Probability that at least one of ``variants`` independent trials gates."""
    if not 0.0 < base_probability < 1.0:
        raise ValueError("base_probability must be in (0, 1)")
    if type(variants) is not int or variants <= 0:
        raise ValueError("variants must be a positive integer")
    # Numerically stable form of 1 - (1 - p)**variants.
    return -math.expm1(variants * math.log1p(-base_probability))


@dataclass(frozen=True, slots=True)
class GateStats:
    epochs: int
    probability: float
    expected_gates: float
    standard_deviation: float
    coefficient_of_variation: float


def gate_stats(*, epochs: int, probability: float) -> GateStats:
    if type(epochs) is not int or epochs <= 0:
        raise ValueError("epochs must be a positive integer")
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must be in (0, 1)")
    mean = epochs * probability
    standard_deviation = math.sqrt(epochs * probability * (1.0 - probability))
    return GateStats(
        epochs=epochs,
        probability=probability,
        expected_gates=mean,
        standard_deviation=standard_deviation,
        coefficient_of_variation=standard_deviation / mean,
    )


def auction_censorship_share(*, native_share: float, checkpoint_share: float, censored_rival_fraction: float) -> float:
    """Stylized upper-bound share under checkpoint censorship and substitution.

    Assumes the attacker can replace every censored rival slot with a reserve
    proof. This is an adversarial bound, not a prediction.
    """
    for name, value in (
        ("native_share", native_share),
        ("checkpoint_share", checkpoint_share),
        ("censored_rival_fraction", censored_rival_fraction),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")
    return min(1.0, native_share + checkpoint_share * censored_rival_fraction * (1.0 - native_share))


def one_retry_withholding_threshold(
    *,
    miner_share: float,
    gate_probability: float,
    block_reward_units: float = 1.0,
) -> float:
    """Gate prize threshold for a stylized one-extra-block grinding attempt.

    The toy model compares incremental expected gate prize ``alpha*p*G`` with
    expected forfeited block reward ``(1-alpha)*B``. Real mining strategy is a
    dynamic game and must not be inferred from this threshold alone.
    """
    if not 0.0 < miner_share < 1.0:
        raise ValueError("miner_share must be in (0, 1)")
    if not 0.0 < gate_probability < 1.0:
        raise ValueError("gate_probability must be in (0, 1)")
    if not math.isfinite(block_reward_units) or block_reward_units <= 0:
        raise ValueError("block_reward_units must be finite and > 0")
    return block_reward_units * (1.0 - miner_share) / (miner_share * gate_probability)


@dataclass(frozen=True, slots=True)
class TargetGranularity:
    hash_budget: int
    expected_work_per_atom: int
    expected_atoms: float
    credited_work_relative_stddev: float
    unbatched_lifecycle_transactions: float


def target_granularity(*, hash_budget: int, expected_work_per_atom: int) -> TargetGranularity:
    if type(hash_budget) is not int or hash_budget <= 0:
        raise ValueError("hash_budget must be a positive integer")
    if type(expected_work_per_atom) is not int or expected_work_per_atom <= 0:
        raise ValueError("expected_work_per_atom must be a positive integer")
    expected_atoms = hash_budget / expected_work_per_atom
    return TargetGranularity(
        hash_budget=hash_budget,
        expected_work_per_atom=expected_work_per_atom,
        expected_atoms=expected_atoms,
        credited_work_relative_stddev=math.sqrt(expected_work_per_atom / hash_budget),
        unbatched_lifecycle_transactions=2.0 * expected_atoms,
    )
