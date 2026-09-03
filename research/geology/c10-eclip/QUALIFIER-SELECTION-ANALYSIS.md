# C10-eclip qualifier-selection analysis

**Status:** adversarial research; not a GoldAtom specification, extraction design, or security claim.

**Verdict:** **SURVIVES-BOUNDED**, with medium confidence. Exact zero elasticity is false. In the continuous uniform-PoW/common-target model, one qualifier omission has uniformly bounded *expected* influence, including when the next common target is selected adaptively before each epoch. Repeated fresh opportunities can nevertheless accumulate linearly on a target path that sustains crossing intensity. At the observed live state the opportunity is rare; the largest preselected realistic-minority result was `+0.27499` expected deposits over 100 years at 30% hash share in an expressly non-forecast, indefinitely growing-difficulty scenario (`0.2970%` elasticity, 95% CI `[0.26479, 0.28520]`).

The strongest disconfirming results are: (1) the previously quoted live `lambda ~= 0.01357` is not C10-eclip but the **unclipped C10 control**; correctly clipped C10-eclip is at `lambda = 0.024277...`, almost 1.79 times larger; and (2) the strongest realistic creation policy increased global deposits while *reducing* attacker-associated deposit blocks. In the confirmed 30% case the global change was `+0.27499`, but the block-producer-association change was `-0.13536` (95% CI `[-0.14183,-0.12890]`). The familiar order-2 influence bound of 2 also does not survive clipping: the fixed-target rare-limit supremum is about `2.582`, and the target-uniform continuous-model bound is `5.3003`.

## Scope and terminology

The experiment treats every difficulty epoch as 2,016 accepted canonical Bitcoin blocks. A qualifying header is a Bitcoin-valid header below the epoch's live pre-transition `G2`. A deposit is the epoch-level Boolean fact `m_j < G2_before`; it is not an ownership assignment or an extracted GoldAtom.

The primary attack modeled here is **creation through qualifier selection**: an epoch already contains one accepted qualifier, and an attacker later finds a lower Bitcoin-valid header. Omitting that lower header preserves the current epoch's one deposit while leaving a looser future state. The ordinary model does not let the attacker omit an honest miner's header.

## Finding GA-C10-001 — the integer-clipped state machine preserves its invariant

- **Mechanism:** initialization, unique-min, new-second, and neither transitions were reconstructed independently.
- **Prerequisites:** the clip is applied both at initialization and on every unique-min transition.
- **Classification:** state-machine correctness; not an attack.
- **Quantitative effect:** every reachable state satisfies `G1 <= G2` and `G2/G1 <= e`.
- **Severity:** critical if omitted; informational when applied correctly.
- **Confidence:** high. The transition is exact integer arithmetic and the full historical replay was independently reproduced row-for-row.
- **Threatens C10-eclip:** no, but initialization clipping is load-bearing.
- **Unresolved:** a future encoding would still have to normatively define `ceil(G2/e)`; this research code is not that encoding.

Let `ceil_e(x) = ceil(x/e)`. The research implementation computes it using a rigorous 180-term rational enclosure of `e`; no binary floating-point value controls a transition.

Initialization from the first two minima `a,b` is:

```text
G2 = max(a,b)
q  = min(a,b)
G1 = max(q, ceil_e(G2))
```

For a unique minimum `m < G1`:

```text
G2' = G1
G1' = max(m, ceil_e(G2'))
```

For a new second `G1 <= m < G2`, `(G1',G2')=(G1,m)`. Otherwise the state is unchanged. Deposit status is evaluated against the **pre-transition** `G2`.

The invariant is inductive. Initialization and unique-min impose `G1 >= ceil(G2/e)` directly. A new-second has `m/G1 <= G2/G1 <= e`; neither changes nothing. The historical first pair has raw ratio `5.754307867...`; clipping reduces it to `e` within displayed precision. Unclipped historical C10 later reached `55.927474929...`, whereas exact certificate checks accept every clipped historical state.

## Finding GA-C10-002 — correctly initialized clipping eliminates new-second A0 creation

- **Mechanism:** suppress a current new-second deposit, retain a higher `G2`, then collect future loose-only deposits before the tighter process catches up.
- **Prerequisites:** a live ratio `R=G2/G1`.
- **Classification:** attempted creation through suppression.
- **Quantitative effect:** future advantage is at most `ln R <= 1`; the suppressed current deposit costs one, so net creation is at most zero.
- **Severity:** none in every correctly reachable clipped state; catastrophic without the load-bearing clip.
- **Confidence:** high in the continuous model; finite-binomial concavity is no more favorable to the attacker.
- **Threatens C10-eclip:** no positive A0 creating set remains.
- **Unresolved:** exact finite-integer consensus formalization is outside this task.

The loose and tight states share `G1` and differ only in `G2`. The first later observation below the tighter `G2` coalesces them. Before coalescence, loose-only events are descending records in the band between the bars. Their rare/uniform worst-case expected count is `ln(G2_loose/G2_tight) <= ln(e)=1`. Since suppression removed one present deposit, `ln(R)-1 <= 0`. Initialization clipping is essential: the historical initial ratio was already 5.75, and unclipped C10 reached 55.93.

## Finding GA-C10-003 — the live crossing intensity was previously attributed to the wrong control

- **Mechanism:** multiple sub-`G2` accepted headers create the raw material for qualifier choice.
- **Prerequisites:** live state, contemporaneous target, uniform valid-hash model.
- **Classification:** opportunity frequency.
- **Quantitative effect:** clipped live `lambda=0.024277063141...`; finite-binomial conditional multiple rate `1.208354%`.
- **Severity:** medium correction; it roughly doubles the conditional multiple rate relative to the quoted unclipped figure.
- **Confidence:** high.
- **Threatens C10-eclip:** increases measured exposure but does not change the boundedness class.
- **Unresolved:** none for the reported snapshot.

For exact discrete valid hashes `H in {0,...,T}`:

```text
p = min(G2,T+1)/(T+1)
K ~ Binomial(2016,p)
```

The prompt's `lambda = W*G2/T` is also reported. At Bitcoin-sized targets it differs from the exact-discrete `W*G2/(T+1)` by only about `1.13e-55`.

| Quantity | C10-eclip | Unclipped C10 |
|---|---:|---:|
| `G2/G1` | 1.1445523747 | 2.7046013271 |
| `lambda` | 0.0242770631411 | 0.0135721696336 |
| finite `P(K>=1)` | 0.0239848882288 | 0.0134805280734 |
| finite `P(K>=2)` | 0.000289822393128 | 0.0000912283136915 |
| finite `P(K>=2 | K>=1)` | 0.0120835415351 | 0.00676741394661 |
| Poisson conditional | 0.0120894174034 | 0.00677073454824 |

For C10-eclip the Poisson conditional exceeds the exact finite-binomial result by `5.8758683e-6`, or about `0.04863%` relatively. For unclipped C10 the corresponding discrepancy is `3.3206016e-6`, about `0.0491%`. Thus the earlier `~0.007` claim is reproducible—but only for unclipped C10.

## Finding GA-C10-004 — history contains multiple qualifiers, but not attributable attacks

- **Mechanism:** replay every completed Bitcoin difficulty epoch using its actual target and all 2,016 header hashes.
- **Prerequisites:** verified canonical header snapshot through height 965,246.
- **Classification:** empirical opportunity evidence, ownership-agnostic.
- **Quantitative effect:** 82 deposits; 23 epochs with `K>=2`; 10 chronological, state-changing monopoly selection opportunities.
- **Severity:** medium as evidence that the residual mechanism is real.
- **Confidence:** high for hashes/state; no claim about historical miner identity.
- **Threatens C10-eclip:** confirms nonzero elasticity, not exploitation.
- **Unresolved:** which historical headers, if any, shared a miner or pool.

The 77,219,760-byte header snapshot has SHA-256 `6d5775640085f29bae0882e4ec3c99f752ad4546f7589650adb9be1d4fd392af`. It contains 965,247 linked, PoW-valid headers, ending at height 965,246 and hash `00000000000000000000b96ab4c27a88f0394225bce8d8f8f92027f28563be1b`. There are 478 completed epochs; epochs 0 and 1 initialize the machine, leaving 476 evaluated transitions.

| Historical statistic | Result |
|---|---:|
| deposits / epochs with `K>=1` | 82 / 476 (17.2269%) |
| transition classes | 53 unique-min; 29 new-second; 394 neither |
| epochs with `K>=2` | 23 / 476 (4.8319%) |
| empirical `P(K>=2 | K>=1)` | 23/82 = 28.0488% |
| `K` distribution | 394 zero; 59 one; 15 two; 5 three; 3 four |
| finite-binomial expected `K>=1` epochs | 89.32248 |
| finite-binomial expected `K>=2` epochs | 23.78079 |
| aggregate modeled conditional | 26.6235% |
| monopoly chronological state-changing opportunities | 10 |

| Historical `lambda` | min | median | mean | p90 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| value | 0.0123705 | 0.120416 | 0.260522 | 0.764814 | 1.071714 | 1.675672 | 2.873979 |

The worst observed opportunity by depth was epoch 134. The first qualifier at height 270,387 had hash `000000000000000001480bf37765db8beb84651395cc36e76e2c4e36fbb51026`; a later header at 271,381 had hash `0000000000000000002ad5e428b2c6bcf8056213c27361b222122f492b3176ed`, 7.6583 times deeper. Preserving the first rather than the latter gives a fixed-target rare-limit future-count potential gap of 2.2864. This is a monopoly counterfactual, not evidence one miner controlled both.

Randomly applying independent owner labels to the *fixed observed history* produces 3.0 expected public-lock opportunity epochs at `alpha=0.30`, 5.0 at `alpha=0.50`, and 10 at monopoly. It is a label model, not an attacked canonical-history replay.

## Finding GA-C10-005 — public-lock is the strongest realistic count-maximizing policy in the model

- **Mechanism:** after any accepted public qualifier secures the epoch's deposit, omit a later attacker-owned record-low header only if accepting it would strictly tighten the clipped post-state.
- **Prerequisites:** the attacker actually finds the later valid header; honest headers remain unavoidable.
- **Classification:** creation; also liveness delay and Bitcoin-reward loss.
- **Quantitative effect:** at live state, an effective opportunity occurs per epoch with probability from `1.3053e-6` at 1% share to `6.5192e-5` at 50%.
- **Severity:** low at the live state; persistent under target paths maintaining larger `lambda`.
- **Confidence:** high on policy ordering, medium on long-range economic realism.
- **Threatens C10-eclip:** establishes nonzero creation elasticity.
- **Unresolved:** propagation, pool payout, and target-feedback behavior outside the simplified race model.

The simulation treats each Bitcoin-valid discovery as a sequential race. Owner is attacker with probability `alpha`; valid hash is uniform under the target. If an attacker omits a block, the canonical height does not advance and another valid discovery races for that same height. No honest hash is selectable.

| `alpha` | first qualifier attacker | attacker gets >=2 qualifiers | attacker-first then deeper attacker | public qualifier then effective deeper attacker | effective later attacker unique-min | mixed honest/attacker qualifiers |
|---:|---:|---:|---:|---:|---:|---:|
| 1% | 2.3985e-4 | 2.9449e-8 | 1.4569e-8 | 1.3053e-6 | 1.2822e-6 | 5.7618e-6 |
| 10% | 2.3985e-3 | 2.9407e-6 | 1.4565e-6 | 1.3050e-5 | 1.2819e-5 | 5.2380e-5 |
| 20% | 4.7970e-3 | 1.1744e-5 | 5.8246e-6 | 2.6095e-5 | 2.5633e-5 | 9.3119e-5 |
| 30% | 7.1955e-3 | 2.6381e-5 | 1.3102e-5 | 3.9133e-5 | 3.8441e-5 | 1.2222e-4 |
| 50% | 1.1992e-2 | 7.3043e-5 | 3.6374e-5 | 6.5192e-5 | 6.4040e-5 | 1.4550e-4 |
| 100% | 2.3985e-2 | 2.8982e-4 | 1.4530e-4 | 1.3024e-4 | 1.2794e-4 | 0 |

The named **shallow-lock** policy requires an attacker-owned accepted qualifier to have established the running shallow lock; it need not be the first qualifier if an honest qualifier preceded it. It is weaker than **public-lock**: an honest published qualifier already fixes the current deposit count at one, after which a later attacker header can be omitted without controlling the honest hash. **Threshold** omits only if `alpha*(V/R)*B > 1`, using `V/R=100` as a declared illustration and the constant-target infinite-horizon potential `B`; it is a myopic economic proxy, not a solved finite-horizon optimum or a price assumption.

The simulated **all-discoveries-public-lock** stress gives the selector every later qualifier, including honest discoveries, for zero private reward cost, but still accepts the first public lock and has no foresight. It is deliberately impossible and is **not** called a hard omniscient bound. Suppressed discoveries still require replacement network work; machine rows count those solution intervals separately from the artificial zero charge. The genuine omniscient count ceiling is simply one deposit per epoch: for any `H`-epoch horizon, `N_attack <= H` and `Delta_N <= H-E[N_honest]`. Machine rows report that loose ceiling for every share/scenario/horizon; it grants arbitrary foresight, control, delay, and zero cost and is not an executable strategy.

Public-lock is count-maximizing within the ownership-respecting, no-foresight model when Bitcoin cost is ignored: rejecting a state-effective attacker-owned deeper qualifier leaves a componentwise looser state, while accepting it cannot increase future deposit count under the same exogenous target path. No claim of dynamically optimal economic behavior is made.

## Finding GA-C10-006 — finite-horizon elasticity is small in every predeclared scenario

- **Mechanism:** deterministic Monte Carlo over future epoch minima and replacement races.
- **Prerequisites:** one of five non-forecast target paths and a persistent hash share.
- **Classification:** creation plus liveness/cost.
- **Quantitative effect:** strict-minority maximum confirmed at `Delta_N=0.27499`, `Lambda=0.2970%` over 100 years for `alpha=0.30` in Scenario B.
- **Severity:** low finite-horizon supply elasticity; measurable rather than zero.
- **Confidence:** medium-high for the model, low as a forecast.
- **Threatens C10-eclip:** the measured minority effect is small in these scenarios; `FAIL-MATERIAL` remains a qualitative economic judgment rather than a post-hoc numerical cutoff.
- **Unresolved:** future target process, Bitcoin fee/reward path, and strategic feedback.

Nominal horizons use 14-day epochs: 1/4/10/25/50/100 years are 26/104/261/652/1,304/2,609 epochs, or 52,416/209,664/526,176/1,314,432/2,628,864/5,259,744 accepted blocks. These are boundary-normalized experiments: the snapshot tip is position 1,598 (zero based) in epoch 478, with 1,599 blocks observed, no live-bar crossing, and 417 blocks remaining. Simulations deliberately restart from the completed-epoch-477 state at a fresh full epoch; they are not literal tip-forward forecasts conditioned on that partial epoch.

The target scenarios are not forecasts:

- **A:** constant observed tip target.
- **B:** continue the geometric target multiplier observed across the final 209 completed epochs (eight nominal years): `0.98622348` per epoch, implying 43.61% annual difficulty growth indefinitely.
- **C:** Scenario B for 104 epochs, then plateau.
- **D:** reciprocal path (difficulty decline), capped at Bitcoin's pow limit.
- **E:** alternate minimum/maximum clamped actual-timespan inputs. The code uses Bitcoin integer multiplication/division and compact-target rounding at every boundary, producing a consensus-admissible target sawtooth. It is hostile and not a forecast or a constructed header chain.

The broad sweep used 4,096 paths for every combination. The decision rows below were preselected and rerun at 65,536 paths; confidence intervals are paired common-random Monte Carlo intervals.

| Scenario / share / horizon | honest deposits | attack deposits | `Delta_N` (95% CI) | `Lambda` | effective omissions | gross `R` / extra deposit |
|---|---:|---:|---:|---:|---:|---:|
| B / 30% / 100y | 92.57625 | 92.85124 | 0.27499 [0.26479, 0.28520] | 0.2970% | 0.31621 | 1.1499 |
| B / 50% / 100y | 92.53331 | 92.96925 | 0.43594 [0.42336, 0.44852] | 0.4711% | 0.52716 | 1.2092 |
| E / 50% / 100y | 11.64369 | 11.67404 | 0.03035 [0.02828, 0.03242] | 0.2607% | 0.03813 | 1.2564 |

For the strongest realistic policy, 100-year broad-sweep point estimates are:

| Scenario | 1% `Delta/Lambda` | 10% | 20% | 30% | 50% | monopoly |
|---|---:|---:|---:|---:|---:|---:|
| A constant | 0 / 0% | .0022 / .024% | .0032 / .034% | .0076 / .081% | .0063 / .068% | .0220 / .236% |
| B continued growth | .0110 / .012% | .0894 / .097% | .1804 / .195% | .2705 / .292% | .4380 / .472% | .9438 / 1.023% |
| C growth then plateau | .0002 / .002% | .0032 / .024% | .0061 / .047% | .0203 / .157% | .0256 / .197% | .0420 / .325% |
| D decline | 0 / 0% | .0002 / .016% | .0002 / .016% | 0 / 0% | 0 / 0% | .0007 / .048% |
| E sawtooth | .0020 / .017% | .0076 / .065% | .0078 / .067% | .0161 / .139% | .0337 / .290% | .0603 / .519% |

Small 4,096-path cells can round to zero or fluctuate; they are not evidence of exact zero. `simulation-results.csv` contains all 1,800 geology/policy/share/scenario/horizon rows, including honest/attack means, `Delta_N`, 95% interval, `Lambda`, direct attacker-associated changes, opportunity count, gross and net reward cost, efficiency, matched-budget rows, the impossible all-discoveries stress, and the trivial omniscient ceiling. `simulation-results.json` preserves the scenario/model metadata, row count, CSV filename, and complete field manifest without duplicating the 1,800-row table.

To compare controls under the same budget, a separate sweep gives every path the same ex-ante hard cap of **one omitted valid block (`1 R`)**. Each online policy takes its first eligible omission and then publishes normally; this is a matched hard budget, not a claim that the policy allocates that budget optimally. Realized spend differs because some paths never see an opportunity.

| 1-R cap, B / 30% / 100y | honest deposits | attack deposits | `Delta_N` | `Lambda` | realized `R` | utilization | `R` / extra |
|---|---:|---:|---:|---:|---:|---:|---:|
| raw record / net-creation cutoff | 35.8162 | 36.6895 | 0.8733 | 2.4383% | 0.9846 | 98.46% | 1.1275 |
| C10 unclipped / public-lock | 70.7554 | 70.9238 | 0.1685 | 0.2381% | 0.1934 | 19.34% | 1.1478 |
| C10-eclip / public-lock | 92.6128 | 92.8425 | 0.2297 | 0.2481% | 0.2668 | 26.68% | 1.1615 |

The machine rows apply this same cap for every requested share, target scenario, and horizon. The unbounded-policy table later in this report is retained as an opportunity-limited efficiency comparison and is explicitly not budget matched.

The earlier `+2.8 deposits / 800 epochs / ~4 hashes` setup could not be recovered: the referenced `/workspace/goldatom-assay/c10-clip-attack.md`, its code, and seeds were absent. An untuned replacement started from the actual maximum-lambda historical pre-state (epoch 37), held target constant, used monopoly public-lock, and ran 800 epochs. Across 32,768 paths it produced 15.7649 honest versus 17.1988 attacked deposits: `Delta_N=1.43390` (95% CI `[1.41445,1.45335]`) at 2.5061 omitted headers. This is the same mechanism but does not reproduce the unavailable number.

## Finding GA-C10-007 — one omission is expected-value bounded, not pathwise bounded

- **Mechanism:** compare the loose post-selection state with the tighter honest state under common future observations.
- **Prerequisites:** uniform Bitcoin-valid PoW hashes; target chosen before the epoch observation.
- **Classification:** single-event creation influence: **A, uniformly bounded in expectation** in the continuous model.
- **Quantitative effect:** exact fixed-target rare-limit supremum `2.5819767`; target-uniform continuous-model bound `5.3002586`.
- **Severity:** bounded but nonzero.
- **Confidence:** medium-high for the continuous proof; exact finite-integer lifting remains open.
- **Threatens C10-eclip:** no raw-record-style depth singularity remains.
- **Unresolved:** a formal discrete `T+1`/integer proof and tightness of the 5.3003 bound.

Use log state `(A,B)=(-ln G2,-ln G1)`, so `A<=B<=A+1`. On observation `Z=-ln m`:

```text
Z <= A       : (A,B)
A < Z <= B   : (Z,B)
Z > B        : (B,min(Z,B+1))
```

A selector omission produces ordered loose/tight states whose corresponding log-coordinate gaps `a,b` are each in `[0,1]`. The transition is monotone and non-expansive, so this remains true under common observations.

For constant target in the rare-crossing limit, define

```text
A_e = e/(e-1)
phi(G1,G2) = -A_e ln(G1) - ln(G2).
```

Conditional on a deposit, direct integration over the clipped transition regions gives expected `Delta phi = 1` for every internal ratio. The relative future-count value of loose versus tight state is therefore

```text
A_e ln(G1_loose/G1_tight) + ln(G2_loose/G2_tight),
```

whose selector-reachable supremum is

```text
(2e-1)/(e-1) = 2.5819767068693265.
```

One million deterministic Monte Carlo paths from the maximal pair measured 2.57937 (SE 0.00175; 95% CI `[2.57594,2.58279]`), consistent with the analytic value. This is disconfirming relative to the unclipped bound of 2: the clip eliminates an unbounded tail but increases the finite worst-case coefficient.

For changing targets, condition on crossing the loose bar. The continuous epoch-min log-depth density satisfies

```text
f_p(q+t)/f_p(q) >= exp(-t)
```

for every target placement `p`; the rare-crossing exponential limit is therefore the most favorable shallow-versus-erasing-tail ratio available to the attacker. Let `c=e^-1-e^-2` and

```text
C = 1 + 1/c = 5.3002585353
Psi = C*b + max(a-b,0).
```

A transition-region case split gives the conditional supermartingale inequality

```text
E[loose-only deposit + Psi_next | history] <= Psi_now.
```

It remains valid when a **common counterfactual target** is chosen adaptively from prior joint history, before the next epoch minimum. Summing and taking monotone limits bounds the expected count attributable to one omission by `Psi_initial <= C`. The lemma does not compare worlds whose Bitcoin timestamps make their later targets diverge; that is a coupled difficulty-manipulation channel, not isolated qualifier-state influence.

There is **no deterministic pathwise bound**. Positive-probability sequences of a loose-only event followed by a common deep clipped reset can repeat arbitrarily many times. The task's catastrophic criterion is expected count, not maximum sample path. The exact discrete hash grid is not covered by the density proof; at Bitcoin targets the numerical correction is negligible, but that is still an explicit proof obligation.

An earlier boundary/reset calculation yielded 4.30026. Adversarial review found an interior-state counterexample; an unconstrained, instantaneous rare-tail/deep-reset stress policy measured 4.82114 expected extra deposits (SE 0.00377) across one million paths, exceeding it. That policy is not a factor-four Bitcoin retarget trajectory. The 4.300 value is retained in `boundedness-results.json` as **refuted evidence**, not used as a bound. Its missing unit was the possible loose-only salvage in the one-coordinate-gap branch.

## Finding GA-C10-008 — repeated opportunities are per-event bounded but can be cumulatively linear

- **Mechanism:** maintain nonvanishing crossing intensity so fresh multiple-qualifier opportunities continue arriving.
- **Prerequisites:** persistent strategic mining and a target path coupled to the changing scale of `G2`.
- **Classification:** **B, per-event bounded but cumulatively linear** in the nondegenerate asymptotic model.
- **Quantitative effect:** `Delta_N=Theta(number of epochs)` is possible; it does not arise from one omitted hash.
- **Severity:** medium long-horizon protocol elasticity.
- **Confidence:** high for the asymptotic construction, low as a Bitcoin forecast.
- **Threatens C10-eclip:** prevents a stronger “total influence is bounded” claim.
- **Unresolved:** feasibility/economics of steering Bitcoin difficulty to such a path.

An adaptive path can set `T_j = W*G2_j/lambda_0`. Because every clipped transition has `G2_(j+1)/G2_j in [1/e,1]`, the required target ratio is also in `[1/e,1]`, within Bitcoin's factor-four retarget bounds. This keeps `lambda_0>0`; every persistent `alpha>0` then has a positive rate of owned later-deeper opportunities. Renewal/reward reasoning gives linear accumulation from repeated fresh omissions.

By contrast, under constant target or an eventual plateau, order-statistic scaling gives `lambda=O(1/n)` and multiple-qualifier probability `O(1/n^2)`, making opportunities asymptotically summable in the idealized model. Literal infinite Bitcoin history also has a finite integer target space; the classification concerns the usual nondegenerate asymptotic model.

Mapped to the finite scenarios: A is constant and C eventually plateaus, so both enter the summable regime; D raises target toward `powLimit`, reducing crossings; E oscillates between two nearby target scales while the frontier continues falling, so it also trends toward the summable regime. B continually lowers target and is the predeclared path that most nearly sustains crossing intensity. The linear class is established by the adaptive `T_j=W*G2_j/lambda_0` construction, not claimed as the infinite-horizon behavior of every A-E path.

## Finding GA-C10-009 — the ordinary attack costs a Bitcoin block; value capture weakens it further

- **Mechanism:** omit an otherwise publishable later-height Bitcoin-valid header.
- **Prerequisites:** attacker finds a state-effective deeper qualifier after a public qualifier.
- **Classification:** creation plus liveness and reward opportunity cost.
- **Quantitative effect:** about one gross `R` per omission; 1.1499 gross `R` per global extra deposit, while direct attacker-associated deposits change by `-0.13536` in the confirmed 30%/Scenario-B/100y case.
- **Severity:** economically conditional, not free.
- **Confidence:** high for symbolic threshold, medium for illustrative path.
- **Threatens C10-eclip:** a global-supply motive can overcome cost; private block-association value does not in the confirmed minority cases.
- **Unresolved:** `V`, discounting, fees, pool contract, and any future title mechanism.

Let `F` be expected omitted valid headers, `Delta_N` the global increment, `c` the fraction of that increment the attacker expects to capture, `d` a discount factor, and `R` the Bitcoin reward plus fees. Gross break-even is

```text
V/R > F / (c*d*Delta_N).
```

At fixed canonical height a replacement may also be attacker-won with probability `alpha`, so the net accepted-reward shortfall proxy is `(1-alpha)F*R`; the conservative gross opportunity cost remains `F*R`. The attacker performs no GoldAtom-specific shortcut hashing. Each omission forces roughly one additional network valid-solution interval; the attacker bears its hash-share portion during the delay.

For the confirmed 30% Scenario-B case, `F=0.31621`, `Delta_N=0.27499`. Gross cost is 1.1499 `R` per global extra deposit; the fixed-height net shortfall proxy is 0.8049 `R` per global extra. If one counts only *future loose-only extra events* and assumes their block producers are sampled at persistent share `alpha`, then the optimistic capture proxy `c=0.30` gives 3.8329 gross `R` per captured extra event (2.6830 net). That calculation deliberately ignores displacement of the attacker-owned block that was omitted, and therefore is not a net value-capture estimate. Delayed benefits raise every threshold.

For a single maximally influential fixed-target rare-limit omission, the optimistic bound gives `V/R > 0.3873/(c*d)`; actual omissions usually have much less than the 2.582 maximum. The broader 5.3003 target-uniform envelope is even more attacker-favorable and not a typical event.

Value capture is not geology ownership. If the attacker exits after the current epoch, its expected share of future marginal event blocks is zero. If it maintains independent share `alpha`, `alpha` is a neutral proxy only for the producer of a future loose-only extra event; 50% gives about one half and monopoly gives one. It is **not** the net effect of the strategy on attacker-associated deposits.

The simulator directly reports the signed change in deposits whose final epoch-minimum block producer is the attacker. At 30%, Scenario B, 100 years, attack minus honest is **`-0.13536`** (95% CI `[-0.14183,-0.12890]`) even while global deposits rise by `+0.27499`; the signed ratio is `-0.4922`, not a capture probability. At 50% the corresponding change is `-0.04312` (95% CI `[-0.05268,-0.03356]`) against global `+0.43594`. A useful approximation is

```text
net attacker-associated change ~= alpha*Delta_N - (1-alpha)*F.
```

Future extra events contribute roughly `alpha*Delta_N`, but omitting an attacker-owned would-be minimum tends to hand the existing epoch association to a prior or replacement producer, costing roughly `(1-alpha)F`. Under this block-producer-association value model, no positive `V` makes the confirmed 30% policy privately break even: it pays Bitcoin cost and reduces its associated deposits. A miner that values **global** supply creation can set `c=1` in the symbolic inequality; any future extraction/title rule could give a different capture function, but it is outside this task. Assuming the attacker captures all `Delta_N` merely because it caused the state divergence is unsupported.

A same-height buffered choice has a successful branch with no *second* canonical reward forgone, but it is not free ex ante. After holding a shallow candidate `q=x_s/(T+1)`, probability of finding a deeper attacker candidate before an honest block is

```text
alpha*q / (1-alpha+alpha*q).
```

For a typical live qualifier `q~=p/2`, this is only `2.58e-6` at 30% share and `6.02e-6` at 50%. Failure orphans the already-found shallow reward with near-unit probability, before propagation penalties. This belongs near the omniscient upper bound, not the ordinary low-cost model.

## Finding GA-C10-010 — the clip removes catastrophic single-event depth elasticity, not all issuance elasticity

- **Mechanism:** compare the same target/share/horizon framework with raw records and unclipped C10 controls.
- **Prerequisites:** control-specific publication rule; raw records are evaluated block-by-block, C10 variants by epoch minima.
- **Classification:** creation/suppression controls.
- **Quantitative effect:** clipped C10 changes the single-event class from D to A in the continuous model; repeated C10-eclip opportunities remain class B.
- **Severity:** major improvement over both controls, incomplete protection.
- **Confidence:** high on qualitative classes; medium on finite-horizon magnitudes.
- **Threatens C10-eclip:** residual is real but does not meet the stated catastrophic/material thresholds in tested finite horizons.
- **Unresolved:** exact discrete target-uniform proof and real Bitcoin target feedback.

Raw all-time records remain **D, unbounded from one event**: omitting `x` below frontier `F` has influence growing like `ln(F/x)` as `x->0`. Unclipped C10 is also D because its coordinate ratio is unbounded. C10-eclip caps selector-created coordinate separations to one nat each and yields the expected-value bound above.

The finite simulations apply block-grain record counting to raw geology and epoch-grain counting to both C10 controls. Raw uses its fixed-target net-creation cutoff (`deep < current/e`), because suppressing a raw record loses that present record; both C10 variants preserve the already-secured one-per-epoch deposit under qualifier selection.

At `alpha=0.30`, Scenario B, 100 years (4,096-path broad sweep), the following **opportunity-limited strategies use unequal realized budgets**. Use the matched 1-R table above for the same-cap comparison:

| Control / strategy | honest deposits | attack deposits | `Delta_N` | `Lambda` | gross omitted `R` | `R` / extra | single event | sustained long run |
|---|---:|---:|---:|---:|---:|---:|---|---|
| raw record / deep `< current/e` cutoff | 35.8162 | 40.4333 | 4.6172 | 12.891% | 5.0237 | 1.0880 | D: unbounded | linear cutoff policy plus unbounded event tail |
| C10 unclipped / public-lock | 70.7554 | 70.9448 | 0.1895 | 0.2678% | 0.2207 | 1.1649 | D: unbounded | B: cumulative linear if intensity persists |
| C10-eclip / public-lock | 92.6128 | 92.8833 | 0.2705 | 0.2921% | 0.3105 | 1.1480 | A: expected bound <=5.3003 | B: cumulative linear if intensity persists |

The clipped candidate has slightly more *typical* finite selector activity than unclipped C10 in this row because it maintains a higher live bar and a higher honest event count. The clip's security gain is removal of the arbitrarily deep single-event tail, not a monotone reduction in every finite point estimate. Raw's large result uses a different necessary strategy: because each raw record is itself a deposit, it omits only improvements deeper than `e`, where the asymptotic expected future gain exceeds the lost current record.

The clip therefore bought the property this task was testing: no single arbitrarily deep selected qualifier can create an arbitrarily large expected tail. It did **not** buy zero miner elasticity, a deterministic pathwise bound, or a total bound against indefinitely repeated fresh opportunities.

## Verdict and falsification thresholds

**Verdict: SURVIVES-BOUNDED.**

- **Not FAIL-CATASTROPHIC:** the continuous model gives a finite target-uniform expected single-event bound of 5.3003. Raw-record-style influence growing without limit in qualifier depth is gone.
- **Not classified FAIL-MATERIAL in the finite scenarios:** a 30% persistent miner's largest confirmed result was 0.275 extra deposits over 100 years, 0.297% of honest expected supply, at about 1.15 gross Bitcoin rewards per global expected extra deposit. “Material” is an explicit qualitative judgment here; no numerical threshold was chosen after observing the result.
- **Not SURVIVES-ECONOMIC:** exploitation is not obviously irrational under all possible valuations. Costs and weak value capture matter, but `V`, future capture/title, discounting, and pool contracts are unknown.
- **Important limitation:** repeated fresh omissions can accumulate linearly when a target path sustains crossing intensity. “Bounded” here means bounded expected influence per omitted qualifier, not bounded lifetime influence of a persistent miner.

## Reproduction

From the repository root, with the verified 80-byte header snapshot available:

```sh
python3 research/geology/c10-eclip/c10_eclip.py \
  --headers /path/to/bitcoin-mainnet-headers.bin \
  --outdir research/geology/c10-eclip
python3 -m pip install -r research/geology/c10-eclip/requirements.txt
python3 research/geology/c10-eclip/simulate.py
python3 research/geology/c10-eclip/confirm.py
python3 research/geology/c10-eclip/bounds.py
python3 -m unittest discover -s research/geology/c10-eclip -p 'test_*.py' -v
```

Artifacts:

- `c10_eclip.py`: integer-certified transition and historical replay.
- `historical-replay.csv`: every completed epoch and pre/post state.
- `historical-crossings.csv`: all 116 reconstructed crossing headers in chronological order.
- `historical-summary.json`: empirical distributions, exact-decimal live probabilities, and owner-label model.
- `simulate.py`, `simulation-results.json`, `simulation-results.csv`: deterministic ownership-aware policy sweep.
- `confirm.py`, `targeted-confirmations.json`: high-repetition decision rows.
- `bounds.py`, `boundedness-results.json`: analytic/Monte Carlo influence evidence, including the refuted 4.300 calculation.
- `test_c10_eclip.py`: deterministic unit, invariant, ownership, simulation, and optional full-snapshot tests.
- `requirements.txt`: declared NumPy 2.x dependency for simulation and tests; the empirical scanner itself remains stdlib-only.

## Remaining assumptions

1. The target-uniform bound is proved for continuous uniform valid hashes. A rigorous lift to exact integer support and rounding is not completed.
2. Targets are selected before observing an epoch minimum and are common to the attacked/counterfactual worlds. If omitted/replacement timestamps make later difficulty paths diverge, the target-uniform state lemma no longer isolates the effect; that coupled Bitcoin difficulty-manipulation channel remains unresolved.
3. Published valid headers are treated as canonical; propagation/orphan risk is omitted, favoring the attacker.
4. Miner ownership is independent Bernoulli share. Pool correlation, changing share, and payout rules are not inferred from historical headers.
5. Scenario B intentionally extrapolates eight-year difficulty growth for a century and is not a forecast. Scenario E uses exact consensus retarget/compact arithmetic at the clamp endpoints but is not a forecast, economic-feasibility claim, or mined header-chain construction.
6. The threshold policy uses a declared illustrative `V/R=100` and an infinite-horizon fixed-target potential; it is not a solved finite-horizon dynamic optimum. No GoldAtom price, extraction right, or ownership rule is assumed.
7. Future-extra-event share `alpha`, signed block-producer association, and any eventual extraction/title value are different quantities. Only the first two are modeled here; geology itself assigns no owner.
8. Budget-matched controls share a one-`R` ex-ante cap but not identical realized spend, because opportunity rates differ; their online first-eligible policies are not proven budget-optimal.
9. Forecasts are normalized to a fresh epoch boundary and do not condition on the 417 blocks remaining in partial epoch 478.
