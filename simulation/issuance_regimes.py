#!/usr/bin/env python3
"""Generate deterministic adversarial comparisons of three issuance regimes."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
import math
from pathlib import Path
import sys
from typing import Any

# Direct execution sets sys.path[0] to ``simulation/`` rather than the
# repository root. Insert the root so the checked-out package is importable
# without requiring an editable install.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from goldatom.economics import (
    auction_censorship_share,
    effective_producers,
    gate_stats,
    gini,
    hhi,
    one_retry_withholding_threshold,
    producer_shares,
    simulate_auction_top_producer,
    target_granularity,
    variant_gate_probability,
)

SEED = 0x474F4C44  # ASCII-ish "GOLD"
PRODUCERS = 100
ADVANTAGES = (1, 2, 10, 100, 10_000)
AUCTION_EPOCHS = 20_000
WINNERS_PER_EPOCH = 64
BASE_GATE_PROBABILITY = 1 / 4096


def build_results() -> dict[str, Any]:
    concentration: list[dict[str, Any]] = []
    auction: list[dict[str, Any]] = []
    for index, advantage in enumerate(ADVANTAGES):
        shares = producer_shares(PRODUCERS, advantage)
        top_share = shares[0]
        concentration.append(
            {
                "hardware_advantage": advantage,
                "top_expected_share": top_share,
                "hhi": hhi(shares),
                "effective_producers": effective_producers(shares),
                "gini": gini(shares),
            }
        )
        simulation = simulate_auction_top_producer(
            top_share=top_share,
            epochs=AUCTION_EPOCHS,
            winners_per_epoch=WINNERS_PER_EPOCH,
            seed=SEED + index,
        )
        auction.append(
            {
                "hardware_advantage": advantage,
                **asdict(simulation),
            }
        )

    hash_budget = 2**40
    granularity = [
        asdict(target_granularity(hash_budget=hash_budget, expected_work_per_atom=2**power))
        for power in (16, 24, 32, 40)
    ]

    elasticity = [
        {
            "efficiency_multiplier": multiplier,
            "relative_atom_or_bullion_output": float(multiplier),
        }
        for multiplier in (1, 2, 10, 100)
    ]

    unsuccessful_attempt_fraction = 1.0 - WINNERS_PER_EPOCH / 2**30
    censorship = [
        {
            "native_share": 0.20,
            "checkpoint_share": 0.20,
            "censored_rival_fraction": fraction,
            "adversarial_share_bound": auction_censorship_share(
                native_share=0.20,
                checkpoint_share=0.20,
                censored_rival_fraction=fraction,
            ),
        }
        for fraction in (0.0, 0.25, 0.50, 1.0)
    ]

    gate_windows = [asdict(gate_stats(epochs=epochs, probability=BASE_GATE_PROBABILITY)) for epochs in (10_000, 1_000_000)]
    variant_amplification = []
    for variants in (1, 10, 100, 1_000, 10_000):
        effective = variant_gate_probability(BASE_GATE_PROBABILITY, variants)
        variant_amplification.append(
            {
                "variants": variants,
                "effective_probability": effective,
                "amplification": effective / BASE_GATE_PROBABILITY,
            }
        )

    block_candidate_grinding = []
    for candidates in (1, 2, 16, 256, 4096):
        effective = variant_gate_probability(BASE_GATE_PROBABILITY, candidates)
        block_candidate_grinding.append(
            {
                "candidate_headers": candidates,
                "effective_probability": effective,
                "amplification": effective / BASE_GATE_PROBABILITY,
            }
        )

    withholding = [
        {
            "miner_share": share,
            "gate_prize_threshold_in_block_rewards": one_retry_withholding_threshold(
                miner_share=share,
                gate_probability=BASE_GATE_PROBABILITY,
            ),
        }
        for share in (0.05, 0.20, 0.50)
    ]

    return {
        "schema": "goldatom-issuance-stress-0",
        "generated_on": str(date(2026, 9, 2)),
        "deterministic_seed": SEED,
        "assumptions": {
            "producers": PRODUCERS,
            "equal_resource_budget_except_hardware_advantage": True,
            "auction_epochs": AUCTION_EPOCHS,
            "winners_per_epoch": WINNERS_PER_EPOCH,
            "auction_large_search_space_iid_label_approximation": True,
            "base_gate_probability": BASE_GATE_PROBABILITY,
            "variant_trials_assumed_independent": True,
            "price_prediction": False,
        },
        "work_weighted_bullion": {
            "concentration": concentration,
            "fixed_target_supply_elasticity": elasticity,
            "target_granularity": granularity,
        },
        "sealed_epoch_auction": {
            "concentration": auction,
            "fixed_winners_per_epoch": WINNERS_PER_EPOCH,
            "example_attempts_per_epoch": 2**30,
            "attempts_not_represented_by_winning_atoms_fraction": unsuccessful_attempt_fraction,
            "checkpoint_censorship_stress_bound": censorship,
        },
        "proof_intersection_gating": {
            "gate_windows": gate_windows,
            "claim_variant_amplification": variant_amplification,
            "source_block_candidate_grinding": block_candidate_grinding,
            "one_retry_withholding_thresholds": withholding,
        },
        "verdict": {
            "control_branch": "work-weighted bullion",
            "experimental_branch": "canonical vein auction",
            "rejected_as_standalone": "proof-intersection gating",
            "reason": (
                "Canonical intersections can schedule scarce opportunities, but they do not by themselves "
                "create exclusive ownership or atom-specific cost. Claim-dependent gates are Sybil-grindable; "
                "claim-independent gates still require a separate allocation mechanism."
            ),
        },
    }


def pct(value: float, places: int = 3) -> str:
    return f"{100.0 * value:.{places}f}%"


def num(value: float, places: int = 4) -> str:
    if abs(value) >= 1000:
        return f"{value:,.{places}f}"
    return f"{value:.{places}f}"


def markdown(results: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    add("# GoldAtom Issuance Stress Test 0")
    add("")
    add("**Generated:** 2026-09-02  ")
    add(f"**Deterministic seed:** `{results['deterministic_seed']}`  ")
    add("**Status:** economic toy models; not consensus rules, market forecasts, or security proofs")
    add("")
    add("## Executive result")
    add("")
    add("The three candidate regimes solve different problems, and none supplies all of GoldAtom's desired properties by itself:")
    add("")
    add("1. **Work-weighted bullion** gives every atom exclusive, independently assayable local work, but aggregate supply remains linearly elastic to available hashing efficiency and resource expenditure.")
    add("2. **A sealed epoch auction** fixes atom count, but long-run ownership remains proportional to effective hashpower and the design converges toward ordinary competitive proof of work, with added deadline and censorship surfaces.")
    add("3. **Proof-intersection gating** best resembles digital geology, but a canonical intersection only schedules an opportunity. It does not choose an owner or create per-atom exclusive cost. If claimant-controlled variants enter the gate, the scarcity can be ground away.")
    add("")
    add("> **Recommendation:** retain work-weighted bullion as the control branch and investigate a **canonical vein auction** as the experimental branch: claim-independent external proofs open a rare epoch; separately committed local work allocates exactly one title. Do not treat proof-intersection gating as a standalone minting rule.")
    add("")

    add("## Model boundaries")
    add("")
    add("These are deliberately minimal stress models. Producers have equal resource budgets except for one hardware-efficiency multiplier; auction winner labels are sampled in the large-search-space limit; candidate gates are independent Bernoulli trials; network topology, fee dynamics, strategic coalitions, price reflexivity, and cross-chain correlations are omitted unless explicitly modeled. The omission makes the figures diagnostic, not predictive.")
    add("")

    add("## 1. Work-weighted bullion")
    add("")
    add("With equal resource budgets, one producer's expected output share is `A / (A + N - 1)`, where `A` is its hardware advantage and `N = 100` producers. Standardizing nuggets into bars does not change this distribution.")
    add("")
    add("| Hardware advantage | Top expected share | HHI | Effective producers | Gini |")
    add("|---:|---:|---:|---:|---:|")
    for row in results["work_weighted_bullion"]["concentration"]:
        add(
            f"| {row['hardware_advantage']:,}× | {pct(row['top_expected_share'])} | "
            f"{row['hhi']:.5f} | {row['effective_producers']:.2f} | {row['gini']:.4f} |"
        )
    add("")
    add("**Disconfirming result:** the assay layer cannot neutralize hardware asymmetry. At 100× efficiency, one equal-budget producer controls just over half of expected output; at 10,000×, it controls about 99%.")
    add("")
    add("### Fixed-target supply elasticity")
    add("")
    add("If target policy is unchanged and the same resource budget produces more hashes, expected output scales one-for-one with the efficiency improvement.")
    add("")
    add("| Hash-efficiency multiplier | Relative expected output |")
    add("|---:|---:|")
    for row in results["work_weighted_bullion"]["fixed_target_supply_elasticity"]:
        add(f"| {row['efficiency_multiplier']}× | {row['relative_atom_or_bullion_output']:.0f}× |")
    add("")
    add("This is genuine unforgeable costliness, but not a finite ore body. A retarget or quota can stabilize issuance only by adding monetary policy.")
    add("")
    add("### Atom granularity versus chain load and variance")
    add("")
    add("For a period containing `2^40` local hash attempts, the table treats each atom as a Poisson success worth its target-implied expected work. The transaction count is the unbatched GoldAtom/0 claim-plus-mint lifecycle.")
    add("")
    add("| Expected work/atom | Expected atoms | Relative SD of credited work | Unbatched claim+mint txs |")
    add("|---:|---:|---:|---:|")
    for row in results["work_weighted_bullion"]["target_granularity"]:
        power = int(round(math.log2(row["expected_work_per_atom"])))
        add(
            f"| 2^{power} | {row['expected_atoms']:,.3f} | "
            f"{pct(row['credited_work_relative_stddev'], 4)} | "
            f"{row['unbatched_lifecycle_transactions']:,.3f} |"
        )
    add("")
    add("Very small nuggets reduce assay variance but explode title and publication overhead. Very large nuggets reduce chain footprint but make issuance lumpy and favor entities that can finance long dry spells.")
    add("")

    add("## 2. Sealed epoch auction")
    add("")
    add(f"The model issues exactly {WINNERS_PER_EPOCH} atoms per epoch. It simulates {AUCTION_EPOCHS:,} epochs and compares the result with the exact hash-share expectation.")
    add("")
    add("| Hardware advantage | Expected top share | Simulated top share | P(top gets ≥ half of epoch) exact | Simulated |")
    add("|---:|---:|---:|---:|---:|")
    for row in results["sealed_epoch_auction"]["concentration"]:
        add(
            f"| {row['hardware_advantage']:,}× | {pct(row['top_share_expected'])} | "
            f"{pct(row['top_share_simulated'])} | {pct(row['majority_probability_exact'], 4)} | "
            f"{pct(row['majority_probability_simulated'], 4)} |"
        )
    add("")
    unrepresented = results["sealed_epoch_auction"]["attempts_not_represented_by_winning_atoms_fraction"]
    add(f"At `2^30` attempts competing for {WINNERS_PER_EPOCH} winning positions, **{pct(unrepresented, 6)}** of attempts are not represented by a winning atom. They are not cryptographically meaningless—the order statistics depend on them—but their producer receives no title.")
    add("")
    add("### Checkpoint-censorship stress bound")
    add("")
    add("This deliberately hostile bound gives an attacker 20% native winning share and 20% probability of controlling the checkpoint. Whenever it controls the checkpoint, it censors a fraction of rival slots and is assumed able to fill every censored slot with a reserve proof.")
    add("")
    add("| Rival slots censored when checkpoint controlled | Attacker share bound |")
    add("|---:|---:|")
    for row in results["sealed_epoch_auction"]["checkpoint_censorship_stress_bound"]:
        add(f"| {pct(row['censored_rival_fraction'])} | {pct(row['adversarial_share_bound'])} |")
    add("")
    add("This is an upper-bound scenario, not an equilibrium prediction. It shows why proofs must be committed before the final reveal and why a single hard-deadline block should not decide admissibility.")
    add("")
    add("**Disconfirming result:** a quota fixes quantity, not decentralization. Long-run title share still follows effective hashpower, while the auction adds strategic reveal and inclusion machinery.")
    add("")

    add("## 3. Proof-intersection gating")
    add("")
    add("The base toy gate opens with probability `1/4096` per canonical epoch.")
    add("")
    add("| Epoch window | Expected gates | Standard deviation | Coefficient of variation |")
    add("|---:|---:|---:|---:|")
    for row in results["proof_intersection_gating"]["gate_windows"]:
        add(
            f"| {row['epochs']:,} | {row['expected_gates']:.3f} | "
            f"{row['standard_deviation']:.3f} | {pct(row['coefficient_of_variation'])} |"
        )
    add("")
    add("The long-run rate can be statistically stable while short windows remain extremely lumpy. That resembles mineral discovery, but it does not yet solve ownership.")
    add("")
    add("### Claim-variant amplification")
    add("")
    add("If a claimant can try `M` independent claim identifiers against the same epoch, the effective probability becomes `1 - (1-p)^M`.")
    add("")
    add("| Claim variants | Effective gate probability | Amplification over one claim |")
    add("|---:|---:|---:|")
    for row in results["proof_intersection_gating"]["claim_variant_amplification"]:
        add(
            f"| {row['variants']:,} | {pct(row['effective_probability'], 5)} | "
            f"{row['amplification']:,.2f}× |"
        )
    add("")
    add("**Protocol consequence:** the existence relation must be independent of claimant-controlled keys, transaction IDs, salts, ordering, or cheap source-chain variants. Otherwise claim flooding is simply mining under another name.")
    add("")
    add("### Source-block candidate grinding")
    add("")
    add("A last revealer able to inspect or generate multiple valid candidate headers gets the same mathematical amplification:")
    add("")
    add("| Candidate headers | Effective gate probability | Amplification |")
    add("|---:|---:|---:|")
    for row in results["proof_intersection_gating"]["source_block_candidate_grinding"]:
        add(
            f"| {row['candidate_headers']:,} | {pct(row['effective_probability'], 5)} | "
            f"{row['amplification']:,.2f}× |"
        )
    add("")
    add("### One-extra-block withholding threshold")
    add("")
    add("In a deliberately simplified one-retry model, grinding becomes positive-expectation when the gate prize exceeds `(1-α)/(αp)` source-chain block rewards. This omits repeated retries, orphan risk, fee revenue, hedging, and market impact.")
    add("")
    add("| Source-chain miner share α | Gate prize threshold |")
    add("|---:|---:|")
    for row in results["proof_intersection_gating"]["one_retry_withholding_thresholds"]:
        add(
            f"| {pct(row['miner_share'], 0)} | "
            f"{row['gate_prize_threshold_in_block_rewards']:,.0f} block rewards |"
        )
    add("")
    add("A highly secure source chain can make this expensive in absolute terms; a cheap auxiliary chain can make nominal proof diversity dangerously inexpensive.")
    add("")
    add("### The ownership gap")
    add("")
    add("A claim-independent canonical intersection is observable by everyone at essentially the same time. Therefore:")
    add("")
    add("- first-to-publish becomes a latency and censorship race;")
    add("- claimant-key selection becomes Sybil grinding;")
    add("- random selection from claims requires a costly anti-Sybil admission rule;")
    add("- a local-work competition restores exclusive cost but reintroduces a work auction.")
    add("")
    add("There is also a geological limit to the metaphor: past cryptographic strata are fully enumerable. A simple vein relation can be exhaustively scanned and its historical reserve count learned. Making discovery itself computationally difficult merely turns the scan into another proof-of-work problem.")
    add("")

    add("## Comparative verdict")
    add("")
    add("| Criterion | Work-weighted bullion | Sealed epoch auction | Proof-intersection gate alone | Canonical vein auction hybrid |")
    add("|---|---|---|---|---|")
    add("| Exclusive atom-specific cost | **Yes** | **Yes** for winners | **No** | **Yes** via separate local work |")
    add("| Predictable atom count | No | **Yes** | Statistical only | Statistical or capped per open gate |")
    add("| Claim-Sybil resistance | Work-priced | Work-priced | **Fails if claim enters gate** | Work-priced after claim-independent gate |")
    add("| Gold-like unknown reserves | Weak | No | Superficially strongest, but enumerable | Moderate metaphor |")
    add("| Hardware concentration | High | High | Allocation undefined | High unless allocation changes |")
    add("| Novelty | Moderate | Low | High | **High** |")
    add("| Current readiness | **Control implementation** | Research model | Reject standalone | **Experimental specification target** |")
    add("")
    add("## GoldAtom/1 research direction")
    add("")
    add("Specify two branches rather than prematurely collapsing them:")
    add("")
    add("1. **Bullion/1:** preserve heterogeneous, transferable proofs of exclusive local work; solve batching, larger nonce space, and bar standardization. Treat its supply as compute-elastic and say so plainly.")
    add("2. **Vein/1:** derive a claimant-independent gate from deeply finalized canonical proof histories; allow at most one title per gate; allocate that title through a prior-commitment local-work contest whose submissions cannot be censored by one decisive block.")
    add("")
    add("The experimental branch is worth pursuing only if it survives four falsification tests: no claimant-controlled gate variants, bounded source-miner influence, an exclusive non-latency-based title rule, and no double-counting of shared external chainwork as atom substance.")
    add("")
    add("## Reproduce")
    add("")
    add("```bash")
    add("python3 simulation/issuance_regimes.py \\")
    add("  --json-output simulation/results/issuance-regimes.json \\")
    add("  --markdown-output ISSUANCE-SIMULATION-0.md")
    add("```")
    add("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=Path("simulation/results/issuance-regimes.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("ISSUANCE-SIMULATION-0.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = build_results()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(results), encoding="utf-8")
    print(f"Wrote {args.json_output}")
    print(f"Wrote {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
