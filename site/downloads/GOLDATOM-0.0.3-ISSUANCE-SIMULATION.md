# GoldAtom Issuance Stress Test 0

**Generated:** 2026-09-02  
**Deterministic seed:** `1196379204`  
**Status:** economic toy models; not consensus rules, market forecasts, or security proofs

## Executive result

The three candidate regimes solve different problems, and none supplies all of GoldAtom's desired properties by itself:

1. **Work-weighted bullion** gives every atom exclusive, independently assayable local work, but aggregate supply remains linearly elastic to available hashing efficiency and resource expenditure.
2. **A sealed epoch auction** fixes atom count, but long-run ownership remains proportional to effective hashpower and the design converges toward ordinary competitive proof of work, with added deadline and censorship surfaces.
3. **Proof-intersection gating** best resembles digital geology, but a canonical intersection only schedules an opportunity. It does not choose an owner or create per-atom exclusive cost. If claimant-controlled variants enter the gate, the scarcity can be ground away.

> **Recommendation:** retain work-weighted bullion as the control branch and investigate a **canonical vein auction** as the experimental branch: claim-independent external proofs open a rare epoch; separately committed local work allocates exactly one title. Do not treat proof-intersection gating as a standalone minting rule.

## Model boundaries

These are deliberately minimal stress models. Producers have equal resource budgets except for one hardware-efficiency multiplier; auction winner labels are sampled in the large-search-space limit; candidate gates are independent Bernoulli trials; network topology, fee dynamics, strategic coalitions, price reflexivity, and cross-chain correlations are omitted unless explicitly modeled. The omission makes the figures diagnostic, not predictive.

## 1. Work-weighted bullion

With equal resource budgets, one producer's expected output share is `A / (A + N - 1)`, where `A` is its hardware advantage and `N = 100` producers. Standardizing nuggets into bars does not change this distribution.

| Hardware advantage | Top expected share | HHI | Effective producers | Gini |
|---:|---:|---:|---:|---:|
| 1× | 1.000% | 0.01000 | 100.00 | 0.0000 |
| 2× | 1.980% | 0.01010 | 99.04 | 0.0098 |
| 10× | 9.174% | 0.01675 | 59.70 | 0.0817 |
| 100× | 50.251% | 0.25502 | 3.92 | 0.4925 |
| 10,000× | 99.020% | 0.98049 | 1.02 | 0.9802 |

**Disconfirming result:** the assay layer cannot neutralize hardware asymmetry. At 100× efficiency, one equal-budget producer controls just over half of expected output; at 10,000×, it controls about 99%.

### Fixed-target supply elasticity

If target policy is unchanged and the same resource budget produces more hashes, expected output scales one-for-one with the efficiency improvement.

| Hash-efficiency multiplier | Relative expected output |
|---:|---:|
| 1× | 1× |
| 2× | 2× |
| 10× | 10× |
| 100× | 100× |

This is genuine unforgeable costliness, but not a finite ore body. A retarget or quota can stabilize issuance only by adding monetary policy.

### Atom granularity versus chain load and variance

For a period containing `2^40` local hash attempts, the table treats each atom as a Poisson success worth its target-implied expected work. The transaction count is the unbatched GoldAtom/0 claim-plus-mint lifecycle.

| Expected work/atom | Expected atoms | Relative SD of credited work | Unbatched claim+mint txs |
|---:|---:|---:|---:|
| 2^16 | 16,777,216.000 | 0.0244% | 33,554,432.000 |
| 2^24 | 65,536.000 | 0.3906% | 131,072.000 |
| 2^32 | 256.000 | 6.2500% | 512.000 |
| 2^40 | 1.000 | 100.0000% | 2.000 |

Very small nuggets reduce assay variance but explode title and publication overhead. Very large nuggets reduce chain footprint but make issuance lumpy and favor entities that can finance long dry spells.

## 2. Sealed epoch auction

The model issues exactly 64 atoms per epoch. It simulates 20,000 epochs and compares the result with the exact hash-share expectation.

| Hardware advantage | Expected top share | Simulated top share | P(top gets ≥ half of epoch) exact | Simulated |
|---:|---:|---:|---:|---:|
| 1× | 1.000% | 1.001% | 0.0000% | 0.0000% |
| 2× | 1.980% | 1.990% | 0.0000% | 0.0000% |
| 10× | 9.174% | 9.129% | 0.0000% | 0.0000% |
| 100× | 50.251% | 50.197% | 56.5604% | 56.3500% |
| 10,000× | 99.020% | 99.009% | 100.0000% | 100.0000% |

At `2^30` attempts competing for 64 winning positions, **99.999994%** of attempts are not represented by a winning atom. They are not cryptographically meaningless—the order statistics depend on them—but their producer receives no title.

### Checkpoint-censorship stress bound

This deliberately hostile bound gives an attacker 20% native winning share and 20% probability of controlling the checkpoint. Whenever it controls the checkpoint, it censors a fraction of rival slots and is assumed able to fill every censored slot with a reserve proof.

| Rival slots censored when checkpoint controlled | Attacker share bound |
|---:|---:|
| 0.000% | 20.000% |
| 25.000% | 24.000% |
| 50.000% | 28.000% |
| 100.000% | 36.000% |

This is an upper-bound scenario, not an equilibrium prediction. It shows why proofs must be committed before the final reveal and why a single hard-deadline block should not decide admissibility.

**Disconfirming result:** a quota fixes quantity, not decentralization. Long-run title share still follows effective hashpower, while the auction adds strategic reveal and inclusion machinery.

## 3. Proof-intersection gating

The base toy gate opens with probability `1/4096` per canonical epoch.

| Epoch window | Expected gates | Standard deviation | Coefficient of variation |
|---:|---:|---:|---:|
| 10,000 | 2.441 | 1.562 | 63.992% |
| 1,000,000 | 244.141 | 15.623 | 6.399% |

The long-run rate can be statistically stable while short windows remain extremely lumpy. That resembles mineral discovery, but it does not yet solve ownership.

### Claim-variant amplification

If a claimant can try `M` independent claim identifiers against the same epoch, the effective probability becomes `1 - (1-p)^M`.

| Claim variants | Effective gate probability | Amplification over one claim |
|---:|---:|---:|
| 1 | 0.02441% | 1.00× |
| 10 | 0.24387% | 9.99× |
| 100 | 2.41214% | 98.80× |
| 1,000 | 21.66459% | 887.38× |
| 10,000 | 91.29876% | 3,739.60× |

**Protocol consequence:** the existence relation must be independent of claimant-controlled keys, transaction IDs, salts, ordering, or cheap source-chain variants. Otherwise claim flooding is simply mining under another name.

### Source-block candidate grinding

A last revealer able to inspect or generate multiple valid candidate headers gets the same mathematical amplification:

| Candidate headers | Effective gate probability | Amplification |
|---:|---:|---:|
| 1 | 0.02441% | 1.00× |
| 2 | 0.04882% | 2.00× |
| 16 | 0.38991% | 15.97× |
| 256 | 6.05941% | 248.19× |
| 4,096 | 63.21655% | 2,589.35× |

### One-extra-block withholding threshold

In a deliberately simplified one-retry model, grinding becomes positive-expectation when the gate prize exceeds `(1-α)/(αp)` source-chain block rewards. This omits repeated retries, orphan risk, fee revenue, hedging, and market impact.

| Source-chain miner share α | Gate prize threshold |
|---:|---:|
| 5% | 77,824 block rewards |
| 20% | 16,384 block rewards |
| 50% | 4,096 block rewards |

A highly secure source chain can make this expensive in absolute terms; a cheap auxiliary chain can make nominal proof diversity dangerously inexpensive.

### The ownership gap

A claim-independent canonical intersection is observable by everyone at essentially the same time. Therefore:

- first-to-publish becomes a latency and censorship race;
- claimant-key selection becomes Sybil grinding;
- random selection from claims requires a costly anti-Sybil admission rule;
- a local-work competition restores exclusive cost but reintroduces a work auction.

There is also a geological limit to the metaphor: past cryptographic strata are fully enumerable. A simple vein relation can be exhaustively scanned and its historical reserve count learned. Making discovery itself computationally difficult merely turns the scan into another proof-of-work problem.

## Comparative verdict

| Criterion | Work-weighted bullion | Sealed epoch auction | Proof-intersection gate alone | Canonical vein auction hybrid |
|---|---|---|---|---|
| Exclusive atom-specific cost | **Yes** | **Yes** for winners | **No** | **Yes** via separate local work |
| Predictable atom count | No | **Yes** | Statistical only | Statistical or capped per open gate |
| Claim-Sybil resistance | Work-priced | Work-priced | **Fails if claim enters gate** | Work-priced after claim-independent gate |
| Gold-like unknown reserves | Weak | No | Superficially strongest, but enumerable | Moderate metaphor |
| Hardware concentration | High | High | Allocation undefined | High unless allocation changes |
| Novelty | Moderate | Low | High | **High** |
| Current readiness | **Control implementation** | Research model | Reject standalone | **Experimental specification target** |

## GoldAtom/1 research direction

Specify two branches rather than prematurely collapsing them:

1. **Bullion/1:** preserve heterogeneous, transferable proofs of exclusive local work; solve batching, larger nonce space, and bar standardization. Treat its supply as compute-elastic and say so plainly.
2. **Vein/1:** derive a claimant-independent gate from deeply finalized canonical proof histories; allow at most one title per gate; allocate that title through a prior-commitment local-work contest whose submissions cannot be censored by one decisive block.

The experimental branch is worth pursuing only if it survives four falsification tests: no claimant-controlled gate variants, bounded source-miner influence, an exclusive non-latency-based title rule, and no double-counting of shared external chainwork as atom substance.

## Reproduce

```bash
python3 simulation/issuance_regimes.py \
  --json-output simulation/results/issuance-regimes.json \
  --markdown-output ISSUANCE-SIMULATION-0.md
```
