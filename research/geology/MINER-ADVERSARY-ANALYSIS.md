# GoldAtom/1 Bitcoin raw-record geology: miner-adversary analysis

**Status:** adversarial research result; not a specification
**Base experiment:** `d991207a6720898a60e2adb110d3f432fc69ee61`
**Scope:** deposit existence in canonical Bitcoin history only
**Out of scope:** extraction, ownership, title, activation selection, and GoldAtom/0

## Executive verdict

No nonce, version, timestamp, merkle-root, template, Stratum, or ASICBoost technique found a GoldAtom-specific shortcut to a low hash. A raw-record candidate is obtained by exactly the same SHA-256d trials as an ordinary Bitcoin block candidate. Conditioned on Bitcoin validity, the continuous approximation is:

\[
p=\min(1,F/T).
\]

The exact integer probability for Bitcoin's `H <= T` validity rule and GoldAtom's `H < F` record rule is `min(1, F/(T+1))`. At the measured tip, the approximation is `2.489175366907752e-6`, about one record per 401,739 accepted blocks.

That result does **not** save the candidate under the stated falsification criterion. Raw-record geology is stateful. A producer that happens to find an exceptionally deep record can withhold it, preserve the higher old frontier, and thereby allow multiple later intermediate hashes to become canonical records. Under a constant-target model, withholding a found hash `x < F/e` eventually increases expected canonical deposit count relative to publishing it. The marginal strategic act forfeits the subsidy and risks some or all fees from one valid block; it does not require the attacker to perform the corresponding extra hash trials, because later ordinary network mining supplies the intermediate hashes.

**Conclusion:** raw-record geology does not cleanly survive the literal criterion `Delta expected canonical deposits > 0 at materially lower marginal cost than producing corresponding extra ordinary trials`. This is creation-through-suppression, not cheap manufacture of low hashes. It is rare, delayed, globally distributed, and target-path dependent, but it is a real count-manipulation mechanism.

## Model and classification

An 80-byte Bitcoin header is hashed twice with SHA-256. The digest bytes are interpreted as a little-endian unsigned integer for proof of work; reversing those digest bytes and printing hex gives Bitcoin's familiar displayed hash, whose ordinary base-16 value is the same integer. Let `T` be the contemporaneous target and `F` the minimum canonical hash before the candidate block.

Assumptions used for closed-form calculations:

- SHA-256d outputs are independent uniform integers absent a cryptanalytic shortcut.
- A Bitcoin-valid block has `H <= T`; a raw record has `H < F`.
- Valid-solution arrivals are Poisson races proportional to hash share.
- Unless stated otherwise, propagation and tie-breaking are abstracted away.
- Constant-target order-statistic results are mechanism proofs, not long-term Bitcoin forecasts.

Finding-level confidence percentages below are subjective analyst judgments. Only intervals explicitly labeled as simulation confidence intervals are statistical intervals.

Classifications are deliberately separate:

- **Creation:** increases expected canonical deposit count.
- **Suppression:** removes, delays, or reduces canonical deposits.
- **Redistribution:** changes which producer or branch obtains a naturally found deposit without increasing count.
- **Liveness:** slows canonical progress or makes deposit status unstable.

## Quantitative baseline: continuing after a non-record solution

Let attacker share be `alpha`, and let it discard every Bitcoin-valid non-record it finds while honest miners publish all valid blocks. Ignoring a fallback release, the next published block is selected from honest blocks at rate `1-alpha` and attacker record blocks at rate `alpha*p`. With `D=1-alpha+alpha*p`:

\[
P(\text{attacker record before honest block})=\frac{\alpha p}{D}
\]

\[
P(\text{canonical record at this height})=\frac{p}{D}
\]

\[
E[\text{discarded attacker blocks per canonical block}]=\frac{\alpha(1-p)}{D}.
\]

At the empirical `p`:

| `alpha` | Attacker record before honest | Canonical record probability | `Delta` per canonical height | Discarded valid blocks per canonical block |
|---:|---:|---:|---:|---:|
| 0.01 | 2.51432e-8 | 2.51432e-6 | 2.51431e-8 | 0.010101 |
| 0.10 | 2.76575e-7 | 2.76575e-6 | 2.76574e-7 | 0.111111 |
| 0.20 | 6.22293e-7 | 3.11147e-6 | 6.22292e-7 | 0.249999 |
| 0.30 | 1.06679e-6 | 3.55596e-6 | 1.06679e-6 | 0.428570 |
| 0.50 | 2.48917e-6 | 4.97834e-6 | 2.48916e-6 | 0.999995 |

The positive per-height delta is not free creation. The canonical-block rate falls from `lambda` to `D*lambda`, so the record rate per wall-clock time is `(p/D)(D*lambda)=p*lambda`, unchanged. The attacker merely removes its non-record blocks from the denominator. Publishing the non-record and immediately mining the next height preserves the same frontier, keeps reward `R`, and exposes the miner to the same record hazard per unit time.

## The stateful adverse result

The formulas in this section are original derivations in this analysis, independently checked algebraically and numerically. Prior work supplies the order-statistic and selective-withholding foundations, not this specific `F/e` result.

For constant target, normalize `a=F/T`. Expected records in the next `n` independent accepted blocks are:

\[
E_n(a)=\sum_{k=1}^{n}\frac{1-(1-a)^k}{k}.
\]

Suppose a producer finds `x<F`. At the same final chain height, publishing produces the present record plus future expectation `1+E_n(x/T)`. Withholding forces a replacement at the current height and preserves `F`, producing expectation `E_(n+1)(F/T)`. Thus:

\[
\Delta_n=E_{n+1}(F/T)-1-E_n(x/T).
\]

As the horizon grows:

\[
\Delta_\infty=\ln(F/x)-1.
\]

It becomes positive iff `F/x > e`, or the withheld record improves the frontier by more than `log2(e) = 1.442695` bits. Exact constant-target break-even horizons at the current `F/T` are:

| `F/x` | Improvement bits | First net-positive horizon | Asymptotic net extra records |
|---:|---:|---:|---:|
| 3 | 1.584963 | 1,802,163 blocks | 0.098612 |
| 5 | 2.321928 | 872,473 blocks | 0.609438 |
| 10 | 3.321928 | 663,068 blocks | 1.302585 |
| 100 | 6.643856 | 550,371 blocks | 3.605170 |
| 1,000,000 | 19.931569 | 540,346 blocks | 12.815511 |

These are long horizons and assume constant target. They nevertheless demonstrate the mechanism.

A standing policy makes the result stronger. If a coalition with share `alpha` withholds only its records below `cF`, accepted record hashes have a shallower distribution. The expected log-frontier improvement per accepted record is:

\[
\mu=\frac{1-\alpha c(1-\ln c)}{1-\alpha c}<1,
\]

so the asymptotic record-count coefficient is:

\[
C=\frac{1}{\mu}=\frac{1-\alpha c}{1-\alpha c(1-\ln c)}>1.
\]

For `c=0.1`, `C-1` ranges from 0.231% at 1% hash share to 13.790% at 50% hash share. Each censorship opportunity is extremely rare—rate `alpha*c*p` per network valid solution—but is encountered during ordinary mining. At current `p`, the expected interval is about 8.03 million network blocks (153 years at ten-minute cadence) even for `alpha=0.5`; at the least-deep asymptotically effective cutoff `c=1/e`, it is about 2.18 million blocks (41.5 years). Conditional on having encountered and censored such an opportunity, the asymptotic expected extra record count is `ln(1/c)`; the sunk sacrificed-reward cost per eventual extra expected record is therefore `R/ln(1/c)`, or about `0.434R` for `c=0.1`. This is not the all-in ex-ante cost of encountering the rare hash. The benefit is delayed and may accrue to other miners or claimants, so private economic incentive is uncertain; technical capability is not.

## Findings

### Finding GA-MINER-001 — Ordinary PoW is the only low-hash search found

- **Mechanism:** Each header trial produces a uniform 256-bit SHA-256d value. Conditioned on `H <= T`, the record probability is approximately `min(1,F/T)`; per raw hash trial it is `F/2^256` while `F <= T`.
- **Prerequisites:** Standard random-oracle-style assumptions for SHA-256d and a canonical Bitcoin target.
- **Classification:** Baseline.
- **Quantitative effect:** Current `p = 2.489175366907752e-6` per accepted block.
- **Severity:** None.
- **Confidence:** 99% conditional on SHA-256 assumptions.
- **Threatens geology itself:** No.
- **Unresolved questions:** A genuine SHA-256 cryptanalytic shortcut would affect Bitcoin mining itself and this conclusion.

### Finding GA-MINER-002 — Header-space techniques add ordinary trials, not special trials

- **Mechanism:** Nonce rolling, BIP323 nVersion rolling (superseding draft BIP320), extranonce/coinbase changes, merkle-root changes, nTime rolling, transaction/template variation, and Stratum job partitioning all generate fresh headers. Overt or covert ASICBoost amortizes SHA-256 work across work items; under the stated uniform-output assumption, it does not bias the low tail toward `F` rather than `T`.
- **Prerequisites:** Miner or pool control of the corresponding mutable fields and valid consensus/template construction.
- **Classification:** Baseline efficiency / possible mining-power redistribution.
- **Quantitative effect:** One additional independent header remains one ordinary hash trial. ASICBoost's published speedup applies to Bitcoin PoW generally, not specifically to records.
- **Severity:** Low.
- **Confidence:** 98%.
- **Threatens geology itself:** No GoldAtom-specific shortcut found.
- **Unresolved questions:** Proprietary optimizations can alter effective hash share, but any output-distribution bias would require separate evidence.

### Finding GA-MINER-003 — Discarding non-record blocks inflates records per height but not per hash or time

- **Mechanism:** A miner withholds Bitcoin-valid non-records and continues searching the same parent until it finds a record or honest miners advance the chain.
- **Prerequisites:** Ability to identify and suppress one's own full solutions; a height-specific objective; no profitable fallback assumed in the table.
- **Classification:** Liveness plus per-height selection; not efficient creation.
- **Quantitative effect:** At `alpha=0.5`, canonical per-height probability nearly doubles to `4.97834e-6`, but about one valid Bitcoin block is discarded per published block and deposit rate per hash/time is unchanged.
- **Severity:** Medium for Bitcoin liveness/economics; low for the falsification criterion.
- **Confidence:** 98% for the model.
- **Threatens geology itself:** Not by itself. The extra per-height count is purchased with corresponding ordinary trials and delay.
- **Unresolved questions:** Tie-release probability, propagation advantage, fee variance, and finite deadlines alter reward cost, not the absence of a hash shortcut.

### Finding GA-MINER-004 — Deep-record withholding creates later records by preserving the frontier

- **Mechanism:** Suppress a naturally found record deeper than `F/e`; later hashes between that suppressed value and the preserved frontier can qualify as multiple canonical records.
- **Prerequisites:** The producer must naturally find the deep hash, recognize it, forfeit publication, and value a long-horizon increase in global deposit count.
- **Classification:** Immediate suppression followed by prospective creation; frontier-state manipulation.
- **Quantitative effect:** `Delta_infinity = ln(F/x)-1`. A 10-fold-deeper record becomes net count-increasing after about 663,068 blocks in the constant-target model. The seeded stress simulation measured `+0.672` deposits per 20,000-block run at `alpha=0.5` (95% paired interval `[0.500,0.844]`) while censoring `0.384` blocks on average. At current parameters, qualifying opportunities are measured in decades or centuries even for large miners.
- **Severity:** High.
- **Confidence:** 95% for constant-target order statistics; 85% for long-run economic relevance under changing targets.
- **Threatens geology itself:** **Yes. This meets the literal falsification criterion in the model.**
- **Unresolved questions:** Target trajectories, discounting, who captures later value, reorg/finality policy, and whether the criterion should count canonical events or physical low-hash discoveries.

### Finding GA-MINER-005 — Publishing an exceptionally deep record suppresses future supply

- **Mechanism:** An unusually low published hash becomes the new frontier and makes every later deposit harder until Bitcoin's target changes enough to offset it.
- **Prerequisites:** Naturally finding the deep hash; ordinary publication.
- **Classification:** One present creation plus future suppression; “frontier squatting” effect.
- **Quantitative effect:** A lower absolute `F` permanently lowers `P(H<F)=F/2^256` until an even lower record replaces it. Difficulty changes alter conditional per-block probability and cadence but cannot undo the lower frontier. Obtaining depth `x` still costs ordinary probability `x/2^256` per raw trial.
- **Severity:** Medium to high for cadence predictability.
- **Confidence:** 98%.
- **Threatens geology itself:** Yes as a path-dependence/supply-control property, but not as cheap record manufacture.
- **Unresolved questions:** Whether an external suppression payoff could exceed future costs borne by others.

### Finding GA-MINER-006 — Withholding a record normally suppresses it; one height cannot contain two canonical deposits

- **Mechanism:** A producer discards a record solution instead of broadcasting it.
- **Prerequisites:** Producer sees the full solution before publication.
- **Classification:** Suppression and liveness; GA-MINER-004 is the long-horizon exception for net count.
- **Quantitative effect:** If a share-`alpha` miner withholds every one of its records, the canonical per-height probability becomes `(1-alpha)*p/(1-alpha*p)` and the record rate per wall time falls from `p*lambda` to `(1-alpha)*p*lambda`. Each censorship event costs one block reward but occurs only at rate `alpha*p`. The withheld header contributes zero; competing branch candidates are not additive unless separately canonical at different heights.
- **Severity:** Medium.
- **Confidence:** 99%.
- **Threatens geology itself:** It threatens availability and, for deep hashes, count integrity.
- **Unresolved questions:** Detectability and pool contractual treatment.

### Finding GA-MINER-007 — Private forks create option value over canonical history, not cheap hashes

- **Mechanism:** Selfish miners retain private leads, generate multiple valid candidates, and release branches selectively. They can choose among already-computed histories and waste honest work.
- **Prerequisites:** Meaningful hash share, propagation/tie advantage, and willingness to risk orphaned rewards.
- **Classification:** Redistribution, suppression, temporary creation, liveness, and—through frontier selection—possible long-run creation.
- **Quantitative effect:** Every favorable candidate still requires ordinary PoW. The truncated private-lead stress model's `alpha=0.5` delta was `+0.136` per 20,000 blocks with a 95% interval spanning zero; it is not evidence of a robust direct creation gain. Established selfish-mining models do establish canonicalization power and reward redistribution.
- **Severity:** High when hash share and network advantage are high.
- **Confidence:** 95% qualitatively; 60% for the deliberately simplified simulator magnitude.
- **Threatens geology itself:** Yes, because the geology delegates existence to whichever Bitcoin branch becomes canonical.
- **Unresolved questions:** A full propagation-aware MDP with the frontier in state is needed to optimize selective policies.

### Finding GA-MINER-008 — Reorganizations recompute the geology; branch records are never additive

- **Mechanism:** A higher-chainwork branch removes one or more canonical headers and replaces them.
- **Prerequisites:** Sufficient competing chainwork; depth determines practical cost, not conceptual behavior.
- **Classification:** Suppression, replacement, and temporary deposits.
- **Quantitative effect:** Removing a record restores the last surviving prior frontier. A replacement is a record iff its hash is below that restored frontier. It may set a different frontier or no record. All descendant classifications must be recomputed on the winning branch.
- **Severity:** Medium for shallow provisional history; critical under deep hostile reorgs.
- **Confidence:** 99%.
- **Threatens geology itself:** It is an inherent dependency rather than an implementation bug.
- **Unresolved questions:** This task intentionally does not choose finality or extraction rollback rules.

### Finding GA-MINER-009 — Pools centralize observation and publication but do not obtain a low-hash oracle

- **Mechanism:** Pools construct jobs, observe submitted shares, recognize network-valid and record-valid solutions, and often control broadcast. Workers or operators may withhold full solutions. Job Declaration can shift template choice back toward miners.
- **Prerequisites:** Pool protocol position or a withholding worker.
- **Classification:** Suppression, redistribution, and centralization.
- **Quantitative effect:** Because current `F<T`, every record is already a full Bitcoin solution. A merely “unusually low” partial share above `T` cannot become a deposit. Seeing shares does not predict independent future hashes.
- **Severity:** Medium; higher for concentrated pools.
- **Confidence:** 97%.
- **Threatens geology itself:** Pools make GA-MINER-004 and GA-MINER-006 easier to coordinate, but provide no creation shortcut.
- **Unresolved questions:** Pool payout rules could reward or penalize record publication if GoldAtom-linked external value ever existed.

### Finding GA-MINER-010 — Difficulty manipulation changes per-block probability, not raw-hash probability

- **Mechanism:** Hashrate and retargets change `T`; timestamps influence the 2,016-block adjustment, and a sufficiently powerful coalition may exploit Bitcoin's timewarp weakness if not prevented by active consensus rules.
- **Prerequisites:** Sustained material control over timestamps/hashrate, becoming extreme for deliberate consensus-scale manipulation.
- **Classification:** Liveness, cadence manipulation, and possible enhancement of frontier-selection attacks.
- **Quantitative effect:** Raising difficulty lowers `T` and raises `F/T` per accepted block while slowing blocks; lowering difficulty does the reverse. Per raw trial, `P(H<F)=F/2^256` is unchanged. If `T<F`, every valid block is initially a record, but each accepted record lowers `F`.
- **Severity:** Low as an isolated GoldAtom shortcut; critical when coupled to majority control of Bitcoin history.
- **Confidence:** 96%.
- **Threatens geology itself:** It threatens cadence and predictability, not SHA work per qualifying hash.
- **Unresolved questions:** Future activation of consensus-cleanup proposals and realistic target paths over the long withholding horizon.

### Finding GA-MINER-011 — Transaction censorship cannot prevent deposit existence

- **Mechanism:** Exclude GoldAtom-related transactions or alter the transaction set.
- **Prerequisites:** Template control.
- **Classification:** Outside geology; template variation is ordinary header search.
- **Quantitative effect:** Deposits require no GoldAtom transaction, so censoring such transactions cannot systematically change deposit probability. Altering any transaction changes the merkle root and therefore the realized header hash, but that is only another ordinary unbiased header trial—not a GoldAtom-specific advantage.
- **Severity:** None for geology; potentially material for a future extraction/title layer.
- **Confidence:** 99%.
- **Threatens geology itself:** No.
- **Unresolved questions:** Extraction censorship is deliberately outside this task.

### Finding GA-MINER-012 — A majority miner can govern the canonical specimen history, subject to PoW

- **Mechanism:** Sustain private chains, remove records, replace them, refuse selected headers, preserve or crush the frontier, and make minority-observed deposits disappear.
- **Prerequisites:** Majority hashpower sustained long enough for the desired reorg/selection policy; some extreme record-only policies require far more than bare 51% because rejected work slows the private chain.
- **Classification:** Creation-through-selection, suppression, redistribution, and liveness.
- **Quantitative effect:** A bare majority still cannot output `H<F` with probability exceeding `F/2^256` per hash. It can, however, decide which of its and displaced miners' valid candidates survive, apply the deep-withholding policy, and repeatedly reorganize provisional geology. As an instantaneous first-block bound at current `p`, publishing only record blocks cannot outrun honest miners unless roughly `alpha*p > 1-alpha`, requiring hash share near 99.99975%, not 51%; each accepted record then lowers `F`, making a continuing record-only chain harder still.
- **Severity:** Critical.
- **Confidence:** 96%.
- **Threatens geology itself:** Yes. Claimant independence does not imply block-producer independence.
- **Unresolved questions:** Optimized majority policies with changing target and finite reorg horizons.

### Finding GA-MINER-013 — Economic incentives differ sharply by strategy

- **Mechanism:** Compare foregone Bitcoin reward `R` with external value `V_GA` attached to causing or controlling a deposit. Here `R=subsidy+fees` is a conservative upper-bound loss: transactions and some fees may remain available for a later block. Let `L<=R` denote the actual expected loss; a simple model may resemble `subsidy + (1-alpha)*fees`.
- **Prerequisites:** External GoldAtom-linked value; none is assumed to exist.
- **Classification:** Incentive threshold.
- **Quantitative effect:** Using full `R` as the loss upper bound, after already finding a non-record and assuming only an attacker-found replacement record yields `V_GA`, continuing rather than publishing requires `V_GA/R > (1-alpha)/(alpha*p)`: approximately 39.77 million, 3.616 million, 1.607 million, 937,392, and 401,739 for the five tested shares. Replace `R` by actual `L` for a fee-recapture model. In an ongoing no-deadline model, publishing dominates because the miner can keep the reward and mine the next height at the same record hazard. For a deep record with net long-horizon count gain `Delta_n`, a pure supply-inflation actor breaks even when `V_GA*Delta_n > L`; attribution of that benefit is unresolved.
- **Severity:** Low likelihood at current parameters for non-record grinding; potentially important for deep withholding if an external sabotage or supply payoff exists.
- **Confidence:** 95% for algebra; 75% for economic applicability.
- **Threatens geology itself:** Capability exists independently of whether present incentives fund it.
- **Unresolved questions:** Discount rate, reward/fee volatility, pool contracts, value capture, and the meaning of `V_GA` without extraction.

## Reproducible simulation

`adversary/simulate.py` uses deterministic seed `0x474131`. It reports exact current-frontier formulas and a Monte Carlo mechanism stress test with initial `F/T=0.01`, 250 paired repetitions, and 20,000 canonical blocks per repetition. The elevated frontier makes differences observable and is not a Bitcoin forecast.

In this simplified simulator, `selective_publication` is intentionally an explicit alias for the “publish only records” / withhold-non-record policy so its equivalence is visible. Depth-selective publication is modeled separately as `withhold_deep_record`.

At `alpha=0.5`:

| Strategy | Mean delta vs honest | 95% paired interval | Mean attacker blocks forfeited | Interpretation |
|---|---:|---:|---:|---|
| Withhold non-record | +0.696 | [0.594, 0.798] | 19,986.128 | Per-height filtering bought with vast ordinary work |
| Withhold all records | -0.492 | [-0.755, -0.229] | 5.404 | Direct suppression |
| Withhold deepest 10% of records | +0.672 | [0.500, 0.844] | 0.384 | Stateful creation-through-suppression |
| Truncated private-fork search | +0.136 | [-0.177, 0.449] | 1,998.996 | Inconclusive simplified network model |

The maximum measured stress-test delta was `+0.696` deposits per 20,000 accepted blocks for non-record filtering, but that consumed nearly 20,000 extra valid solutions. The strongest efficient adverse result was `+0.672` for deep-record withholding. In the exact conditional table, a millionfold-deep record has asymptotic net delta `+12.815511`, at the cost of suppressing its one Bitcoin block; the opportunity to find such a header is correspondingly extraordinary.

## Falsification decision

Two possible criteria produce different answers:

1. **Can a miner generate hashes below `F` with fewer SHA-256 trials?** No method found. Raw-hash discovery remains ordinary Bitcoin PoW.
2. **Can a miner cheaply change the expected number of canonical events classified as deposits?** Yes. Selective deep-record withholding changes the future frontier path and eventually increases canonical record count.

The task's stated criterion uses the second framing. **Raw-record geology therefore fails that criterion in the constant-target model.** This does not show arbitrary issuance, immediate inflation, claimant control, or a practical present-day profit. It shows that “claimant-independent” is insufficient: canonical record count is strategically influenced by producers who can censor unusually deep state transitions.

## Prior technical work

- Nakamoto, [Bitcoin: A Peer-to-Peer Electronic Cash System](https://bitcoin.org/bitcoin.pdf), sections 4–5 and 11: PoW chain selection and attacker catch-up.
- Bitcoin developer guide, [Mining](https://developer.bitcoin.org/devguide/mining.html): nonce exhaustion, extranonce/merkle-root work updates, target checking, and publication.
- Bitcoin Core, [`pow.cpp` at `b811aeab`](https://github.com/bitcoin/bitcoin/blob/b811aeabad94ef48cd0f0fb1d2fcc456594aeedb/src/pow.cpp): implemented PoW and retarget rules.
- Bonneau, Clark, and Goldfeder, [On Bitcoin as a public randomness source](https://eprint.iacr.org/2015/1015): withholding and selective-fork manipulation of header-derived randomness.
- Eyal and Sirer, [Majority is not Enough](https://arxiv.org/abs/1311.0243), and Sapirshtein, Sompolinsky, and Zohar, [Optimal Selfish Mining Strategies](https://arxiv.org/abs/1507.06183): private leads and selective publication.
- Rosenfeld, [Analysis of Bitcoin Pooled Mining Reward Systems](https://arxiv.org/abs/1112.4980), and Eyal, [The Miner's Dilemma](https://arxiv.org/abs/1411.7099): pooled mining and block-withholding incentives.
- Hanke, [AsicBoost — A Speedup for Bitcoin Mining](https://arxiv.org/abs/1604.00575): amortized Bitcoin hashing work across work items.
- [BIP22](https://github.com/bitcoin/bips/blob/7273e178e52f02de100950f569ae40f485099b58/bip-0022.mediawiki), [BIP23](https://github.com/bitcoin/bips/blob/7273e178e52f02de100950f569ae40f485099b58/bip-0023.mediawiki), [BIP310](https://github.com/bitcoin/bips/blob/7273e178e52f02de100950f569ae40f485099b58/bip-0310.mediawiki), [superseded BIP320](https://github.com/bitcoin/bips/blob/7273e178e52f02de100950f569ae40f485099b58/bip-0320.mediawiki), and replacement draft [BIP323](https://github.com/bitcoin/bips/blob/7273e178e52f02de100950f569ae40f485099b58/bip-0323.mediawiki): templates, pooled mining, version rolling, and expanded header search space. Draft status is not consensus activation.
- Stratum V2 [Mining Protocol](https://github.com/stratum-mining/sv2-spec/blob/0f38d51dcd569e8f76575bf03cdf12848f4a4bef/05-Mining-Protocol.md) and [Job Declaration Protocol](https://github.com/stratum-mining/sv2-spec/blob/0f38d51dcd569e8f76575bf03cdf12848f4a4bef/06-Job-Declaration-Protocol.md): job construction, defined hash-space fields, work allocation, solution submission, and template authority. Consensus permits template variation; current protocol constraints determine how that space is partitioned in SV2.
- Bissias and Levine, [Bobtail](https://arxiv.org/abs/1709.08750): Bitcoin proof-of-work order statistics.
- [BIP54 consensus cleanup](https://github.com/bitcoin/bips/blob/7273e178e52f02de100950f569ae40f485099b58/bip-0054.md): technical description and proposed repair of Bitcoin's timewarp weakness. This analysis does not assume activation.

## Remaining work before any profile decision

- Build a propagation-aware selfish-mining MDP whose state includes the raw frontier and competing-branch frontiers.
- Replay strategic publication policies over historical and multiple explicit future difficulty trajectories.
- Formalize whether scarcity means physical qualifying-hash discoveries or canonical classified events; raw-record geology equates them only under honest publication.
- Quantify discounted value and detectability of deep-record censorship under realistic pool arrangements.
- Define a human acceptance threshold for producer influence before any activation or extraction work.

No extraction design, activation height, ownership rule, or production specification is proposed here.
