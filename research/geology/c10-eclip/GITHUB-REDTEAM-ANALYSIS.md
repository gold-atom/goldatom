# C10-eclip independent GitHub REDTEAM analysis

Status: **Final; Phase B comparison appended after remote Phase A blind lock**
Branch: `research/c10-eclip-github-redteam`
Preregistration: `9aca39cd7d06a9cd7444024dd518a58d011bbfb0`
Remote Phase A lock: `1da71b2493a4cba752aa02ebdc0698f500d842ee`

This is an independent deposit-count analysis. It neither proposes a repair nor
changes the candidate. Phase A was derived and saved without opening the three
excluded assay notes. The post-lock disagreement audit is isolated at the end.

## Executive result

The fixed-target result is substantially better than the variable-target
result, but one advertised fixed-target constant does not survive red-team
testing.

* The initialization and every transition preserve `G1 <= G2` and `G2/G1 <= e`.
  No certified `ceil(x/e)` call was ambiguous.
* Static canonical qualifier selection needs two observations under the live
  bar. That is necessary, not sufficient, for a minority miner. In Model A the
  selectively suppressed discovery is noncanonical, so an attacked chain can
  expose only `K=1`; `K>=2` is a diagnostic on the honest counterfactual or on
  an historical deletion experiment, not an ownership proof.
* Under a constant target the usual pre-endpoint `G2/T = Theta(1/E)` scaling is
  supported by local drift and simulation.  Conditional on that scaling,
  `P(K>=2)=Theta(1/E^2)`.  A rigorous attacked-process moment bound sufficient
  to sum the unconditional event probabilities was not established here, so
  the Borel--Cantelli conclusion is conditional rather than a proved theorem.
* The claimed one-unit *live-bar charge* is supportable. It is an expectation
  statement for one deletion at fixed target, not a pathwise ceiling.
* The claimed two-unit bound for the **complete clipped state is statistically
  contradicted as a uniform bound**. A limiting sequence of reachable
  interventions produced mean future influence `2.5818605` in 2,000,000
  event-coupled trials, standard error `0.0012384`, normal 95% interval
  `[2.5794332,2.5842878]`. The largest observed path was `+18`. This is strong
  numerical evidence, not certified quadrature or a finite-integer proof.
* Some continuously shrinking-target relaxations can keep `W G2/T` away from
  zero, giving positive-density selection and simulated linear pre-floor count
  influence. The `0.25` clamp extreme is an important exception: its `K>=2`
  opportunities become ubiquitous, but the transition becomes qualifier-
  independent and marginal count influence becomes zero after a finite
  transient. Bursts, target increases, and bounded `0.25,4` alternation revert
  to the fixed-target class.
* Exact Bitcoin integers add a real endpoint qualification: target and state
  cannot decrease forever. At the compact/integer floor, ties and the clipped
  fixed point make effective deeper selection degenerate even though the task's
  stipulated `q=G2/T` formula continues to call `K>=2` nonsummable. Results below
  therefore report the stipulated continuous asymptotic and the literal
  finite-state endpoint separately.

The **provisional empirical verdict** is **SURVIVES-FIXED-TARGET-ONLY** for the
stipulated continuous qualifier relaxation, with moderate confidence and the
proof gaps stated below. It is not `SURVIVES-BOUNDED` because D-0.75/D-0.95 and
adaptive-H supply evidence against boundedness: they show simulated linear
pre-floor behavior when their floating target schedules are continued without
an integer endpoint. This is not a proof of their asymptotic count-influence
rate, and it is not a literal infinite Bitcoin-consensus construction: compact
quantization, timestamps, and the finite target/state floor prevent that
stronger statement. One intervention is not catastrophic, and Model A burns
at least one Bitcoin reward per omitted otherwise-valid block.

## 1. Independent implementation and raw-header verification

The independent code is under `github-redteam/`; it imports none of the older
C10-eclip code or result files. The empirical input was the already-local
`bitcoin-mainnet-headers.bin` used by the research tree:

| check | independent result |
|---|---:|
| bytes | 77,219,760 |
| SHA-256 | `6d5775640085f29bae0882e4ec3c99f752ad4546f7589650adb9be1d4fd392af` |
| headers | 965,247 |
| tip height | 965,246 |
| tip hash | `00000000000000000000b96ab4c27a88f0394225bce8d8f8f92027f28563be1b` |
| completed 2,016-header epochs | 478 |
| incomplete epoch-478 headers | 1,599 |
| retargets recomputed | 478 |

For every header the verifier parsed the serialized 80 bytes, recomputed double
SHA-256, interpreted the digest in Bitcoin's unsigned integer order, checked
the predecessor field, decoded `nBits`, checked proof of work, and enforced one
target within a period. At each boundary it recomputed the clamped retarget and
compact encoding from raw timestamps. It trusted neither an advertised hash nor
an older epoch-minimum table.

## 2. Exact transition and invariant

Let `c(x)=ceil(x/e)`, computed with consecutive rational bounds separated by
`10^-191` around `e`. For initialization,

```
G2 = max(a,b)
G1 = max(min(a,b), c(G2)).
```

Both terms in the maximum are at most `G2`, while `G1>=G2/e`. Therefore
`G1<=G2` and `G2/G1<=e` immediately; there is no transient un-clipped state.

For a unique minimum, new `G2=old G1` and
`new G1=max(m,c(old G1))`. Both inputs are at most the new `G2`, and the ceiling
gives the ratio bound. For a new second, `new G1=old G1` and `new G2=m<old G2`,
so the old ratio bound only tightens. Neither leaves the state unchanged. The
deposit comparison is made against old `G2` in all cases.

This also removes a reachable new-second `A0`: every new-second satisfies
`G1<=m<G2_before`, and hence necessarily carries the one current deposit. A
state created by the specified initialization never lacks the clip needed by
that argument.

The multiplicative ratio statement assumes positive state. The exact but
astronomically unlikely initialization `(a,b)=(0,0)` instead produces the
absorbing state `(0,0)`; the implementation handles it separately, and the
cross-multiplied invariant remains true although `G2/G1` is undefined.

## 3. Qualifier counts and exact live values

Under the brief's continuous convention, with `q=min(1,G2/T)`:

```
P(K>=1)             = 1 - (1-q)^2016
P(K>=2)             = 1 - (1-q)^2016 - 2016 q (1-q)^2015
P(K>=2 | K>=1)      = P(K>=2) / P(K>=1).
```

The Poisson cross-check is `1-exp(-lambda)` and
`1-exp(-lambda)(1+lambda)`, where `lambda=2016q`. The exact integer-endpoint
probability for accepted hashes uniformly distributed on `0,...,T` and the
strict predicate `H<G2` would instead use `G2/(T+1)`. That distinction is
negligible live but load-bearing at a target of order one.

Independent live replay gives:

| quantity | value |
|---|---:|
| `G1` | 2,254,640,379,176,521,218,445,219,994,660,972,651,329,674,190,988 |
| `G2` | 2,580,554,000,060,355,442,454,944,565,354,521,997,722,846,080,764 |
| current target | 214,292,677,573,643,640,381,615,288,597,024,997,757,051,109,113,856,000 |
| `q` | 0.00001204219401838182005430211249782237828865 |
| `lambda` | 0.02427706314105774922947305879560991463 |
| `P(K>=1)` | 0.02398488822880385674411912467774177448 |
| `P(K>=2)` | 0.00028982239312791996835342367116774104 |
| `P(K>=2 | K>=1)` | 0.01208354153511824036829425715258014614 |
| Poisson `P(K>=2)` | 0.00028996160037823009474017190571626795 |

This state is clipped C10-eclip state. No vanilla-C10 bar was imported.

## 4. Historical replay and deletion forks

The replay CSV has one row for every completed epoch, including initialization
rows with explicitly null pre-state fields. For every ordinary row it records
the target, minimum, exact pre/post state, transition, deposit, ratio, `q`,
`lambda`, `K`, every qualifier hash and height, unspecified ownership, and the
network-level `K>=2` flag.

| historical statistic | result |
|---|---:|
| lambda median | 0.1204155849 |
| lambda p90 | 0.7648144300 |
| lambda p95 | 1.0717135479 |
| lambda p99 | 1.6756720942 |
| lambda maximum | 2.8739787871 |
| `K=0` epochs | 394 |
| `K=1` epochs | 59 |
| `K>=2` epochs | 23 |
| last `K>=2` epoch | 200 |
| eclip deposits after initialization | 82 |

For each of the 23 opportunities I deleted only the canonical minimum, retained
the second-lowest qualifier, and replayed the same later epoch minima. The
largest terminal-prefix count difference was epoch 45 at `+5`. All 23 forks
reconverged and all 23 ended at the honest terminal state. The longest observed
state divergence was 57 later epochs (58 epochs from intervention to first
reconvergence). This is a canonical deletion counterfactual; no historical
ownership is inferred.

## 5. Necessity, sufficiency, and policy ordering

With one canonical qualifier there is no distinct deposit-preserving minimum to
select. Thus `K=1` has zero static canonical selection advantage, and `K>=2` is
necessary for a canonical deletion experiment. It is not sufficient for a
minority miner. A feasible event additionally needs chronological order (the
shallower observation must already be public), attacker ownership of a later
deeper discovery, actual suppression ability, an eventual replacement block,
and an attacked post-state strictly above the same-prestate no-suppression
counterfactual. The simulator records attempts, beneficial state changes, and
harmful replacements separately.

Conversely, Model A's suppressed discovery never becomes canonical. The final
attacked epoch can have `K=1` even though a latent attacker-owned deeper valid
block was burned. It is therefore incorrect to use attacked-chain `K>=2` as a
necessary observable signature.

For two valid states ordered coordinatewise, direct case analysis of the three
transitions shows that a common next minimum preserves that order. The higher
state deposits whenever the lower state deposits. Replacing an epoch minimum
`d` with a shallower qualifier `s>d` also gives a coordinatewise no-lower post
state in all transition-class combinations. Consequently, when discards are
free and liveness is supplied, retaining the shallowest feasible qualifier is
pathwise count-maximizing. This establishes prefer-shallow for Model B and the
omniscient count ceiling.

In Model A a discard triggers an ownership-marked replacement race that
continues until a block is publishable, so one path can get a still-deeper
honest replacement. Prefer-shallow stochastically raises the accepted minimum
but is not pathwise dominant on every replacement draw. For an economic
objective, count ordering is not enough: reward loss, participant capture,
discounting, target path, and remaining horizon all matter. The simulated
`state-aware` row uses a disclosed fixed-target log-gap heuristic; it is not an
optimal dynamic program or a D/H continuation-value calculation.

## 6. What the one-event bounds actually mean

### Live-bar charge

For a one-coordinate record threshold under fixed target, transform epoch
minima by their CDF `F`. The expected number of extra future record crossings
from thresholds `l<h` is `log(F(h)/F(l))`. Since the minimum-of-2016 CDF is
concave and vanishes at zero,

```
log(F(h)/F(l)) <= log(h/l).
```

The clip limits the relevant one-coordinate ratio to `e`, giving a charge of at
most one. Its semantics are: conditional expectation, one intervention,
fixed target, one live-bar lineage, arbitrary remaining horizon. It is not a
deterministic ceiling and is not by itself a theorem for the coupled two-token
state.

### Complete-state statistical counterexample to two

Take a reachable pre-state approaching `(G1,G2)=(e^-1,1)` after normalization.
Let the honest published minimum approach zero and the retained shallow
qualifier approach one. The post states approach

```
honest   = (e^-2, e^-1)
attacked = (e^-1, 1).
```

The event-driven coupling skips null epochs and draws the next relevant epoch
minimum uniformly under the larger bar, which is exact as `G2/T -> 0`. Across
2,000,000 registered-seed trials:

| statistic | future delta |
|---|---:|
| mean | 2.5818605 |
| standard error | 0.0012384 |
| median | 2 |
| p90 | 5 |
| p95 | 6 |
| p99 | 8 |
| maximum | 18 |
| mean relevant events to reconvergence | 8.331838 |
| maximum relevant events to reconvergence | 44 |

The interval excludes two by hundreds of estimated standard errors. This is a
strong registered-seed statistical rejection in the continuous scale limit,
not certified quadrature or a finite-integer lower bound. The flaw in the
two-unit argument is additive charging: interaction between the clipped tokens
creates additional deposit crossings, so two separate one-token charges cannot
simply be summed. Among the 23 empirical fork states, the largest constant-
target mean was epoch 136 at `1.95493` (100,000 trials, standard error
`0.004936`). Thus the old constant can appear adequate on historical states
while failing numerically as a worst-reachable-state claim.

No deterministic pathwise constant exists in the continuous model. A future
sequence can put arbitrarily many descending minima in the gap before it crosses
the lower state. The historical `+5` and simulated `+18` are examples, not
estimates of a deterministic maximum.

## 7. Constant-target asymptotics

Write `g=G2/T` and `r=G1/G2 in [1/e,1]`. For small `g`, an epoch minimum has
density `2016/T + O(G2/T^2)` below the state. The live second coordinate's
one-epoch drift, holding `r` fixed for the local calculation, is

```
E[G2-G2' | state]
  = (2016/(2T)) (G2^2-G1^2) + O(G2^3/T^2).
```

When `r` is near one the first coordinate moves before the second; a two-step
calculation supplies the missing local drift. The clip keeps `r` in a compact
set, and the calculation plus simulations support the usual pre-endpoint
`G2/T=Theta(1/E)` scaling. They do not by themselves prove the uniform moment
bound `E[(G2/T)^2]=O(E^-2)` under an adaptive attacked policy.

The exact binomial expansions are

```
P(K>=1) = 2016 g - C(2016,2) g^2 + O(g^3)
P(K>=2) = C(2016,2) g^2 + O(g^3).
```

The local expansion says normal state evolution has an `O(G^2)` expected
decrement when `T` is the scaling unit. Qualifier selection needs the second low
observation, `O(G^2)`, and changes a coordinate by `O(G)`, suggesting an
`O(G^3)` state-drift perturbation. This supports, but does not prove uniformly,
that a fixed-share policy changes a lower-order coefficient rather than the
leading `1/E` decay.

If the *actual attacked-process* event probability is bounded by `C/E^2`, its
sum is finite. Borel--Cantelli I, which does not require independence, then says
only finitely many such events occur almost surely. It would be invalid to sum
honest-state probabilities while allowing the attacked state to follow a
higher schedule. Establishing the requisite attacked-process moment bound is
therefore an explicit unresolved proof obligation, not something the local
third-order calculation silently supplies.

## 8. Variable-target classification

The target is an independent scaling variable. Absolute `G1,G2` never increase,
but reducing `T` can increase `G2/T`. Thus the constant-target proof is not
uniform over target schedules.

| path | registered definition | continuous pre-floor `K>=2` opportunity class | cumulative count-influence class in continuous relaxation | exact endpoint note |
|---|---|---|---|---|
| A | constant target | finite total, conditional on state moment bound | finite total, same condition | raw tied-zero `K>=2` recurs at `(1,1)`, but effective selection leverage absorbs |
| B | verified historical targets, then plateau | finite prefix plus A | finite prefix plus A | same |
| C | permanent plateau at empirical tip | same as A | same as A | same |
| D-0.95 | target multiplied by 0.95 | linear (supported) | linear pre-floor (simulated; not proved) | floor eventually intervenes |
| D-0.75 | target multiplied by 0.75 | linear (supported) | linear pre-floor (simulated; not proved) | aggressive; floor sooner |
| D-0.25 | clamp-scale difficulty growth | linear; ultimately every epoch | **finite transient; eventual zero leverage** | qualifier-independent before/following floor |
| E-1.05 | target multiplied by 1.05, capped | finite total, conditional as A after cap | finite total, same condition | proof-of-work limit then A |
| E-1.25 | target multiplied by 1.25, capped | finite total, conditional as A after cap | finite total, same condition | proof-of-work limit then A |
| E-4 | clamp-scale difficulty decline, capped | finite total, conditional as A after cap | finite total, same condition | artificial extreme |
| F | eight 0.75 growth epochs, then plateau | finite total, conditional as A after burst | finite total, same condition | potentially larger finite prefix |
| G | alternating 0.25 and 4 | finite total, conditional on analogous bounded-periodic moment control | finite total, same condition | bounded periodic scaling |
| H | adapt floating target toward `lambda=0.5` | linear (supported) | linear pre-floor (simulated; not proved) | continuous-ratio relaxation only |

On D-0.95, D-0.75, and H, normalized state can occupy a nonzero pre-floor
regime: target reduction offsets absolute state decay and `P(K>=2)` stays
positive. For H at `lambda=0.5`, the Poisson cross-check is
`1-exp(-0.5)(1+0.5)=0.090204...` per epoch. The implementation enforces the
ratio clamp and proof-of-work bounds, but does not construct compact-encoded
targets plus a consistent timestamp history; H is therefore a continuous-ratio
consensus relaxation, not a proved Bitcoin header path or an economic forecast.

For D-0.25, once `T<=G1/e`, every accepted minimum lies below the clip floor
and both branches deterministically map `(G1,G2)` to `(G1/e,G1)` in the
continuous model. Every epoch deposits on both branches, so selection leverage
is zero even though `K>=2` has probability one. This directly shows why a
nonsummable diagnostic opportunity count is not sufficient for divergent
issuance influence.

Literal compact targets and integer clipped states occupy finite spaces. Under
the IID accepted-hash model, zero-minimum epochs recur and eventually drive any
positive clipped state to `(1,1)`. Tied zero qualifiers can keep `K>=2`
nonsummable without a deeper distinct candidate or count advantage. Thus the
linear entries are properties of the stipulated continuous extension and its
pre-floor transient; any finite pre-floor prefix is, literally, summable, and
no claim is made that Bitcoin difficulty grows geometrically forever.

## 9. Miner models and finite-horizon simulations

Model A assigns every discovery an owner. After a shallow canonical qualifier,
an attacker-owned later record can be omitted. It costs one otherwise-valid
Bitcoin block and exactly one `R` per omission. Replacement discoveries receive
fresh ownership marks, and the race continues until a candidate is publishable;
every suppressed replacement is also charged. Replacement draws use an
independently keyed stream so the shared base stream stays coupled.
Propagation, private-fork/orphan, and latency costs are set to zero as an
attacker-favorable lower bound, not asserted absent.

Model B assigns canonical slot ownership but grants attacker-controlled redraws
until the policy accepts while retaining the slot and Bitcoin reward. This is
not ordinary mining. The omniscient ceiling can retain the highest deposit-
preserving qualifier without ownership or timing constraints. Honest
publication and publish-minimum are identical controls.

The comprehensive matrix uses decimal master seed `1269070838`; streams are SHA-256
derived from geology, scenario, alpha, model, policy, horizon batch, and trial.
The preregistration's hexadecimal mnemonic is a transcription error:
`1269070838 == 0x4ba47bf6`, not `0x4ba6e536`; the committed decimal value is
authoritative and no simulation stream used the mistaken mnemonic.
Paired branches share base candidates. Effective trial counts are 512, 256, 256,
128, 32, and 4 at horizons 100, 476, 800, 2,000, 10,000, and 100,000. Long-tail
order statistics with 32 or four samples are shown as such and are not treated
as precise p99 estimates. This is a material preregistration deviation: counts
are below the locked ideal budget at every horizon, not only the two longest.
The full 12-path, six-share, five-policy grid was retained, but its Monte Carlo
confidence is correspondingly lower.

Before the Phase A result lock, code review rejected the first shard set: when a live bar
exceeded the target, candidates had been sampled on `[0,G2)` rather than
`[0,T)`, and Model A forced one implicit-honest replacement. Those artifacts
were discarded. The committed matrix was regenerated after capping accepted-
hash support at `min(G2,T)`, looping ownership-marked replacements until
publication, recording actual attacked-chain canonical `K`, and separating
attempts, state-raising same-prestate changes, and harmful replacements. The
merge validator checks the exact Cartesian grid, schema, trial counts, category
partitions, cost identities, and input/code hashes.

The machine fields deliberately say `state_raising_selection`, not
`successful_selection`: they count only coordinatewise state-raising
same-prestate replacements. The registered conditional-future success
probability is present as null because the required continuation value was not
solved. Exact binomial category expectations for the honest and attacked
no-suppression prestates are accumulated separately from empirical honest,
counterfactual, and actual attacked-chain `K` counts.

| matrix property | committed result |
|---|---:|
| rows | 3,888 |
| scenarios | 12 |
| hash shares | 6 |
| horizons | 6 |
| model-policy pairs per scenario/share/horizon | 9 |
| missing / duplicate grid cells | 0 / 0 |
| effective trials at `100/476/800/2k/10k/100k` | `512/256/256/128/32/4` |
| policy JSON SHA-256 | `f70a97c9bd1e3d723837a252d3e3a62900271abff7ab81f2c6d853c26b9eec72` |
| policy CSV SHA-256 | `1c877331065b0d5bb66cc3c11222f22c1692d13b7f4d4297bcb8c634ce171990` |

“Minority” below means strictly `alpha<0.50`; the primary result is Model A
prefer-shallow, not the ownership-free omniscient ceiling. Within that defined
miner slice, the maximum matrix mean was `Delta_N=13.25` at D-0.75,
`alpha=0.30`, `N=100,000`, but it has only four trials. Requiring at least 128
trials, the slice maximum was `9.984375` at D-0.75, `alpha=0.30`, `N=800` (256
trials). Its empirical delta order
statistics were median/p90/p95/p99/max `10/15/18/22/26`; reward loss was
`23.53125 R`, or `2.3568075 R` per expected global marginal deposit and
`7.8560250 R` per marginal deposit under the assumed `f=alpha=0.30` capture.

The maximum strict-minority elasticity was `Lambda=0.0385214296` at D-0.75,
`alpha=0.30`, `N=100` (512 trials), with mean delta `2.029296875` and empirical
p90/p95/p99/max `5/6/8/9`. Model B's sensitivity maxima were mean delta `9.328125`
at D-0.75, `alpha=0.30`, `N=2,000` (128 trials), and elasticity
`0.0401846722` at `N=100` (512 trials). Model B assigns zero reward loss by
construction and is not ordinary mining. At the separate `alpha=0.50` boundary,
Model A reached mean delta `21.5` only in the four-trial 100,000-epoch cell and
maximum elasticity `0.0693692699` at 100 epochs.

The Model-A fixed-target log-gap `state-aware` heuristic made no intervention
at `alpha<0.50`, `V/R=1`, and discount `0.99`; Model B's cost-free threshold
row is intentionally identical to prefer-shallow and does intervene. The
Model-A result is a property of that heuristic, not evidence that a correctly
solved variable-target economic policy is inactive. Honest-publication and
publish-minimum have zero delta while retaining their policy-independent `K`
category counts.

D-0.25 is the sharpest diagnostic/control separation: at `alpha=0.30`, its mean
delta was exactly zero at every checkpoint even while mean honest `K>=2` counts
rose to `99,996.75` of 100,000 epochs. D-0.75 and H instead showed approximately
linear growth only until the normalized integer floor, after which delta
plateaued and both branches deposited together. These finite simulations
support the pre-floor classifications; they do not create an infinite compact-
target Bitcoin history.

Reconvergence was strong but horizon-dependent. All 23 historical deletion
forks returned to the honest state (longest intervention-to-first-return 58
epochs), and all 2,000,000 limiting one-event trials returned within at most 44
relevant events. In the repeated-policy matrix, every strict-minority Model A
prefer-shallow row at horizons 10,000 and 100,000 ended with zero sampled
terminal divergence. Short horizons censor outstanding divergences—for example
D-0.75 at 100 epochs ended divergent in `0.263671875` of trials. The stored
reconvergence probability means *first observed return*; a later policy event
may diverge again.

## 10. Cost and value capture

For each Model A discard, the results separately record one withheld Bitcoin-
valid block, `1 R`, and expected replacement work `2^256/(T+1)` SHA-256 trials.
Calling it “one extra hash” would be wrong. The current GoldAtom epoch still has
one deposit, but the Bitcoin cost is nonzero.

Let `d` be expected global marginal deposits per discarded Bitcoin block,
`f` the attacker's captured fraction, `delta` a discount factor, and `V` value
captured per marginal GoldAtom deposit. Ignoring the separately zeroed lower-
bound externalities, break-even is

```
delta * f * V * d >= R,
or V/R >= 1/(delta f d).
```

Capture scenarios are: immediate exit `f=0`; retain hash share `f=alpha`;
increase later `f=beta` (must be supplied, not guessed); monopoly `f=1`. Global
issuance is never automatically attacker revenue, and this analysis does not
estimate title displacement or net participant capture. Using the largest
independently measured one-intervention mean `d=2.582` as an illustrative
attacker-favorable input—not a certified ceiling—and `delta=0.99`, retaining
share gives these optimistic break-even ratios:

| alpha | minimum `V/R` under the favorable 2.582 gain |
|---:|---:|
| 0.01 | 39.13 |
| 0.10 | 3.91 |
| 0.20 | 1.96 |
| 0.30 | 1.30 |
| 0.50 | 0.783 |
| 1.00 | 0.391 |

Policy-average `d` can be lower and can require multiple discarded blocks, so
matrix-derived costs are generally higher. Model B's zero reward cost is a
deliberately unrealistic upper bound and cannot establish economic feasibility.
For example, the 256-trial strict-minority maximum described above needs
`V/R >= 7.93538` after its `0.99` discount under the assumed 30% retain-share
capture. The matrix stores `alpha*Delta` as an assumed captured *amount*; it
does not estimate the capture fraction itself.

## 11. Controls

The same raw replay gives:

| geology | historical deposits after initialization | live lambda | worst historical lambda |
|---|---:|---:|---:|
| raw all-time record | 28 | 0.0050181775 | 0.9920106787 |
| vanilla C10 | 62 | 0.0135721696 | 1.9776400629 |
| C10-eclip | 82 | 0.0242770631 | 2.8739787871 |

The clip does not simply lower the live hazard; on this history it raises the
live bar relative to vanilla C10 and raises baseline deposits. What it changes
is the worst-state geometry: raw and vanilla state can contain an arbitrarily
large multiplicative gap, so a one-deletion expected influence has no analogous
uniform logarithmic bound. Eclip confines each immediate coordinate gap, sharply
restricting the one-coordinate log charge, although interaction invalidates the
proposed constant two and the focused live-state simulation below does not show
tail dominance.

All three controls have the usual fixed-target pre-floor `Theta(1/E)` record
scaling; summable two-qualifier opportunities follow if the corresponding
second-moment bounds hold. Target paths that track the falling state remove
that route. A Bitcoin block discard costs `1 R` in all three; eclip changes
gain/opportunity frequency, not the Bitcoin opportunity cost.

The focused paired control used the same corrected simulator at
`alpha=0.30`, Model A, prefer-shallow, horizon 800, and 256 trials:

| geology | D-0.75 mean `Delta` | D-0.75 `Lambda` | D-0.75 empirical max | D-0.75 `R/Delta` | H mean `Delta` | H `Lambda` |
|---|---:|---:|---:|---:|---:|---:|
| raw record | 3.09765625 | 0.00623178 | 25 | 1.59269 | 2.37500000 | 0.00774907 |
| vanilla C10 | 8.18750000 | 0.01416121 | 22 | 1.91317 | 5.38671875 | 0.01724526 |
| C10-eclip | 9.93750000 | 0.01578046 | 26 | 2.35810 | 6.32421875 | 0.02010506 |

Thus eclip did **not** dominate the other geologies on realized gain in this
live-state slice: its higher current bar created more deposits and more
opportunities, producing the largest mean and tail maximum here. Its benefit is
the immediate-state ratio restriction and associated worst-gap control, not a
universal reduction in empirical lambda or every finite-horizon delta. At
constant target the same slice observed zero raw/vanilla mean delta and one
rare eclip outcome (`0.0078125` mean, empirical max 2), far too sparse for a
ranking.

## 12. Limitations and preregistration deviations

* The full matrix retained every registered scenario/share/policy but used far
  fewer trials than locked at every horizon; four-trial 100,000-epoch rows are
  sensitivity checks, not precise maxima or tails.
* The fixed-target attacked-process second-moment bound is not proved. The
  local drift argument and simulations support it, but Borel--Cantelli remains
  conditional on that missing bound.
* `state-aware` is a fixed-target log-gap heuristic, not the promised exact
  continuation-value dynamic program. Its economic rows cannot certify an
  optimum on nonstationary target paths.
* For the same reason, the registered definition of “successful selection” as
  a strict conditional-future expected-count improvement was not evaluated.
  The matrix exposes the immediate same-prestate state-raising proxy under an
  unambiguous name and leaves the registered success probability null.
* H enforces floating retarget ratios and global bounds but does not emit a
  compact-encoded target/timestamp construction. It is a continuous consensus
  relaxation, not a fully verified Bitcoin header path.
* Replacement ownership and counts are aggregated with deterministic seeds;
  the matrix does not retain every replacement hash/event trace. Ownership of
  historical canonical blocks remains unknown. This is an explicit output-
  auditability deviation from the preregistration, not a hidden inference.
* Accepted hashes and ownership marks follow the brief's IID model. Network
  latency, private-fork/orphan costs, changing fees/rewards, title displacement,
  and participant capture beyond the stated `f` scenarios are not estimated.
* The decimal master seed is authoritative; the locked hexadecimal mnemonic is
  an explicitly disclosed transcription error.

The blind-lock gate ran 23 independent red-team tests, 31 package tests, seven
geology tests, six prior adversary tests, and 19 C10-eclip tests: 85 passed and
one pre-existing optional test was skipped. A quick policy CLI run and exact
3,888-row/270-row artifact-schema and category-sum checks also passed.

## 13. Reproduction commands

Run from the repository root, setting `BITCOIN_HEADERS` to the canonical local
header file:

```sh
PYTHONPATH=. python research/geology/c10-eclip/github-redteam/test_redteam.py
BITCOIN_HEADERS=/path/to/bitcoin-mainnet-headers.bin
python research/geology/c10-eclip/github-redteam/redteam.py historical \
  --headers "${BITCOIN_HEADERS}" \
  --output research/geology/c10-eclip/github-redteam/results
python research/geology/c10-eclip/github-redteam/bounds_mc.py \
  --historical-summary research/geology/c10-eclip/github-redteam/results/historical-summary.json \
  --output research/geology/c10-eclip/github-redteam/results/one-intervention.json \
  --scale-limit-trials 2000000 --historical-trials 100000
research/geology/c10-eclip/github-redteam/reproduce_policy.sh
python research/geology/c10-eclip/github-redteam/control_sim.py \
  --historical-summary research/geology/c10-eclip/github-redteam/results/historical-summary.json \
  --historical-targets research/geology/c10-eclip/github-redteam/results/historical-targets.json \
  --output-json research/geology/c10-eclip/github-redteam/results/control-simulation.json \
  --output-csv research/geology/c10-eclip/github-redteam/results/control-simulation.csv
```

## 14. Phase A claim disposition

| claim | independent result |
|---|---|
| reachable positive-state new-second A0 eliminated | proved; `(0,0)` is degenerate absorbing initialization |
| selection requires `K>=2` | yes for canonical deletion; qualify for latent Model A discovery |
| `K=1` zero advantage | yes for static canonical selection |
| shallowest qualifier count-maximizing | proved for free selection; economic optimum differs in A |
| live-bar expected influence `<=1` | supported under its one-token, fixed-target semantics |
| full-state expected influence `<=2` | **statistically contradicted**; mean 2.5818605 in the continuous limiting sampler |
| bound is not pathwise | continuous construction; observed +5 historical and +18 simulated |
| fixed-target `G2/T=Theta(1/E)` | supported pre-floor, not proved as a uniform attacked-process moment theorem |
| conditional fixed-target `P(K>=2)=O(1/E^2)` | exact binomial expansion given `G2/T=O(1/E)` |
| finite expected repeated opportunities | supported, conditional on the missing attacked-state second-moment bound |
| only finitely many almost surely | follows by Borel--Cantelli I if that unconditional summability premise is proved |
| strategy preserves leading `1/E` | suggested by local `O(G^2)` versus `O(G^3)` drift, not a global proof |
| survives arbitrary variable difficulty | **no in stipulated continuous relaxation** for D-0.75/D-0.95/H; literal endpoint qualified |

## 15. Phase B disagreement audit

Phase B began only after the blind result tree
`8a9924c736f2c9e7f4af93661cf5c2152162803d` was committed and remotely locked
at `1da71b2493a4cba752aa02ebdc0698f500d842ee`. The three specified full-note
paths—`/workspace/goldatom-assay/c10-clip-attack.md`,
`c10-eclip-qualifier-selection.md`, and `c10-gap-history.md`—were unavailable:
each returned `ENOENT`, and an exact-filename search under `/workspace` found
no substitute. Consequently, no full note file was read and no unseen note
content is inferred. This audit is limited to the eight verbatim reported
claims supplied in the task context.

| reported claim | independent agreement audit | scope / source of any difference |
|---|---|---|
| clipped live lambda is about `0.02428` | **Agree.** Independently derived `0.02427706314105775`. | Clipped clock and clipped initialization; do not substitute the vanilla state. |
| the older `0.01357` value belongs to vanilla C10 | **Agree.** Independent vanilla replay gives `0.0135721696`. | Clipped-versus-vanilla clock/state distinction, not a numerical discrepancy. |
| the historical epoch-45 `prefer_second` fork produced realized `Delta=+5` | **Agree.** The canonical deletion replay gives future delta and maximum prefix delta `+5`; it reconverges at epoch 66. | Realized pathwise, single canonical-history deletion; it does not prove latent withheld-block ownership. |
| several worst historical forks reconverged to the same terminal state | **Agree and strengthen.** All 23 canonical deletion forks reconverged and all reached the honest terminal state. | Canonical history and pathwise reconvergence, not a guarantee for a repeated minority-owned policy. |
| the last canonical historical `K>=2` epoch was epoch 200 | **Agree.** The 23-event independent replay has last event 200. | Canonical accepted hashes only; says nothing about unobserved suppressed discoveries or miner ownership. |
| one-intervention expected influence is at most one on the live bar and at most two including the `G1` residual | **Split.** Agree with the live-bar `<=1` expectation under the stated fixed-target, one-coordinate semantics. **Disagree** with `<=2` as a uniform complete-state expectation: the limiting coupled sampler estimates `2.5818605` (SE `0.0012384`, 95% interval `[2.5794332,2.5842878]`; max path `18`). | Expected is not pathwise; one intervention is not a repeated policy; fixed target is not variable target. The `>2` finding is strong numerical evidence, not a certified proof, and review found no implementation error explaining it. |
| repeated selection is finite-total under a constant target | **Qualified agreement, not independently proved.** Local drift, exact conditional binomial scaling, and simulations support finite total, conditional on an attacked-process second-moment bound that remains open. | Repeated policy under fixed target; the claim does not extend uniformly to variable-target relaxations. The qualification is a missing proof premise, not a state-initialization or arithmetic error. |
| only finitely many selectable epochs occur almost surely in that model | **Qualified / unresolved as a theorem.** Borel--Cantelli I gives this if the required unconditional attacked-process summability is proved; this audit did not prove that premise. | Fixed-target repeated process. Canonical historical finiteness is finite-sample evidence, not an almost-sure theorem; minority ownership only reduces feasible events but does not supply the missing bound. |

Thus the sole direct disagreement among the eight available claims is the
complete-state two-unit expectation. The two constant-target asymptotic claims
are supported but retain a proof qualification; the other five claims agree
with the independent results. A file-level agreement/disagreement assessment
beyond these eight claims remains blocked by the missing note files.

The post-comparison gate reran the same 23 red-team, 31 package, seven geology,
six adversary, and 19 C10-eclip tests: 85 passed and the same one optional test
was skipped.
