# GoldAtom/1 variable-difficulty impossibility pass

Status: adversarial theorem and counterexample research. This document does not
specify a GoldAtom protocol, propose a replacement geology, or alter any prior
empirical result.

The broad proposition tested here is false as written. Header-only and
claimant-independent do not, by themselves, force non-summable creation
elasticity. A concrete absorbing process below satisfies the four premises of
`GA-IMP-DIFF-1` but permits at most one deposit over its entire lifetime, so its
creation elasticity is bounded pathwise by one under every target path and
every publication strategy. This is a theorem counterexample, not a useful
GoldAtom construction.

A narrower result does survive. Exact count zero-elasticity forces equal total
value across miner-co-selectable outcomes. Persistent frontier and finite-order
geologies violate that condition whenever equally depositing header outcomes
lead to different continuation values. If a Bitcoin-valid target policy also
keeps such a vulnerable normalized state recurrent, with non-vanishing
selection probability and non-vanishing uncompensated count gain, cumulative
elasticity is linear. Those added premises describe the failure mode of raw
records, C10, and C10-eclip much better than “header-only discovered supply.”

## Definitions

### Canonical observations and probability space

At observation index `n`:

* `T_n` is the decoded Bitcoin proof-of-work target applying to the canonical
  block or epoch;
* `X_n` is the relevant canonical proof-of-work observation, such as one block
  hash or a completed 2016-block epoch minimum;
* `S_n` is geology state reconstructed deterministically from the canonical
  Bitcoin header prefix;
* `D_n` is the non-negative integer deposit count caused at that observation;
* `N_H = sum_{n <= H} D_n`.

For one honestly published, magnitude-unfiltered accepted candidate at integer
target `T`, the random-oracle model used here is

```text
X | accepted, T  ~  Uniform({0, 1, ..., T}).
```

Strategic canonical publication can filter this law and make the eventual
canonical hash nonuniform. Before such filtering, for a non-negative strict
integer bar `b`,

```text
Pr[X < b | accepted, T] = min(b, T + 1) / (T + 1).
```

The familiar `b/T` expression is a continuous, large-target approximation.
This distinction matters near the smallest targets and for equality at zero.

An expectation is always relative to a stated stochastic law for PoW discovery,
ownership, network races, and any target policy. A deterministic “target/hash
trajectory” has no remaining probability space on which an expected
manipulation can be defined. This report therefore keeps two experiments
separate:

1. fix a target path or a non-anticipating target policy and compare publication
   strategies on coupled PoW randomness; or
2. compare pathwise counts on a fixed coupled realization, without calling the
   result an expectation.

### Header-only and claimant-independent

**Header-only.** State, deposits, and verification are deterministic functions
of canonical Bitcoin headers, Bitcoin consensus data, and fixed rules. No
off-chain database or GoldAtom consensus service is required.

**Claimant-independent.** GoldAtom identities, keys, claims, salts, transaction
variants, tickets, or claimant work cannot change `D_n`.

Neither property makes canonical headers exogenous. Bitcoin miners can
sometimes choose whether to publish a header they found.

### Miner-selectable publication

A realistic publication option is narrower than arbitrary substitution:

1. a miner performs ordinary PoW and finds a Bitcoin-valid candidate;
2. the candidate belongs to that miner, not to an honest miner;
3. the miner may publish it or discard/withhold it;
4. discarding normally forfeits its chance at the Bitcoin block reward and fees
   and permits an honest or later attacker block to fill the canonical height;
5. private forks add race and orphan risk rather than free choice;
6. a miner cannot select an honest network's unpublished hash.

Two models are used in theorem statements:

* **actual rejection:** an attacker may discard only its own candidate and pays
  the associated Bitcoin opportunity cost;
* **full substitutability upper bound:** after seeing one accepted outcome, the
  attacker may reject it and receive a fresh same-context draw. This deliberately
  overstates ordinary miner power and isolates the optionality theorem.

The phrase “miners sometimes have a publication choice” only asserts a
positive-probability option. It does not assert costless choice, control of
honest blocks, or an ability to prescribe a chosen hash.

`R` denotes the block subsidy plus fees the miner would receive if an otherwise
canonical Bitcoin block were published successfully.

“Canonical” also requires more than header PoW validity. Every block must satisfy
the applicable full Bitcoin consensus rules, and its branch must win Bitcoin's
cumulative-chainwork selection and propagation race. Bitcoin's per-block work
is `floor(2^256/(T+1))`: two same-parent candidates with the same `nBits` carry
equal chainwork even if one hash is much deeper. Raw hash depth does not buy
extra Bitcoin chainwork. The relevant implementation is `GetBlockProof` in
Bitcoin Core's
[`src/chain.cpp`](https://github.com/bitcoin/bitcoin/blob/master/src/chain.cpp)
and `nChainWork` in
[`src/chain.h`](https://github.com/bitcoin/bitcoin/blob/master/src/chain.h).
Any sibling-selection example below is conditional on the selected valid
sibling becoming canonical.

### Target environments

Three different notions must not be merged:

* **exogenous target path:** the same `T_1,T_2,...` is supplied to honest and
  attacked runs;
* **non-anticipating target policy:** future targets may depend on prior
  canonical headers and timestamps, under a stated consensus-valid rule;
* **attacker-induced target path:** the miner also uses hash rate, timestamps,
  or private chains to influence Bitcoin difficulty. This is a stronger attack
  model and its attainability depends on hash share and wall-clock constraints.

Existence of a consensus-valid sequence is much weaker than the ability of a
minority miner to cause it economically.

### Scheduled and discovered supply

For this pass, **scheduled supply** means that after conditioning on height or a
predetermined Bitcoin-native partition, its expected issuance law is fixed
independently of realized PoW magnitudes and the future target trajectory,
apart from sampling noise whose law is itself target-independent.

Under the question's literal definition, **genuinely discovered supply** means
that realized PoW magnitudes and/or the future target trajectory materially
change remaining expected issuance. This is weaker than each of the following:

* unbounded remaining issuance capacity;
* an asymptotically material non-scheduled component;
* persistent magnitude dependence;
* recurrent miner-selectable state;
* unbounded continuation-value oscillation.

That gap is decisive. A bounded one-shot random amount can be “discovered” in
the literal sense while making non-summable manipulation impossible.

Future hashrate can also make supply uncertain indirectly through Bitcoin's
retarget schedule. A rule that simply emits a target-indexed quota has unknown
calendar behavior, but economically it is an indirect difficulty-indexed
issuance schedule. This report labels that case rather than treating every
kind of uncertainty as geology.

### Elasticity notions

For attacker strategy `sigma`, compared on the same model with honest
publication,

```text
Delta_H(sigma) = E[N_H | sigma] - E[N_H | honest].
```

Because the attacker can always behave honestly, optimization includes a
zero-gain action. The following terms are used:

* **exact zero-elasticity:** `sup_sigma Delta_H(sigma) = 0` for every horizon and
  reachable history;
* **finite-total elasticity:** there is a finite `C`, independent of `H`, with
  `sup_sigma Delta_H(sigma) <= C`;
* **sublinear elasticity:** the optimized positive gain is unbounded but
  `o(H)`;
* **linear elasticity:** `limsup_H sup_sigma Delta_H(sigma)/H > 0`;
* **non-summable local positive influence:** for a fixed policy,
  `sum_n [E(D_n^sigma - D_n^honest)]_+` diverges.

The last quantity is stronger than divergence of an opportunity count and is
not identical to `Delta_H`: positive and negative count differences can cancel.
A proof of non-summable creation therefore needs the expected *count gain* per
opportunity, not only infinitely many selectable observations.

### Current-deposit and continuation values

For reachable canonical history `h`, let `P_h` be the honest law of the next
accepted observation in a fixed context. With `m` observations remaining, set

```text
V_m(h)    = E_h[sum of the next m deposits under honest publication]
Q_m(h,x)  = d(h,x) + V_{m-1}(h x)
mu_m(h)   = E_{X ~ P_h}[Q_m(h,X)] = V_m(h).
```

`Q_m` is the total finite-horizon count value of publishing outcome `x` now.
It is the correct object for publication selection. A change in next-epoch
hazard is not itself creation if a later compensating count change makes total
`Q_m` equal.

## Previously established results

The prior record-geology and C10-eclip artifacts are treated as reproducible
evidence, not axioms. Their calculations and deterministic tests were run on
the branch base before this document was written.

**EMPIRICAL GA-PRIOR-001 — raw records.** The verified mainnet replay through
height 965,246 found 30 historical raw record deposits. The running frontier
made a withheld sufficiently deep record capable of preserving a looser future
bar. The exact 256-bit process is finite, but its security-parameter/continuous
analogue has unbounded depth sensitivity.

**EMPIRICAL GA-PRIOR-002 — C10-eclip.** Initialization clipping enforces
`G2/G1 <= e` and removes the analyzed new-second `A0` creating set. It does not
make equal-deposit qualifier depths continuation-equivalent.

**SIMULATION GA-PRIOR-003 — complete-state qualifier influence.** The independent
REDTEAM coupled limiting sampler estimated a mean one-intervention influence of
`2.5818605` over 2,000,000 trials, with standard error `0.0012384`, 95% interval
`[2.5794332, 2.5842878]`, and largest realized path `+18`. This statistically
contradicts—and is strong numerical evidence against—the proposed complete-state
expected bound of two in that model; Monte Carlo alone is not a formal
refutation, proof of an infinite tail, or literal Bitcoin pathwise bound.

**SIMULATION GA-PRIOR-004 — variable targets.** Continuous-ratio simulations
with target multipliers `0.95` and `0.75`, and an adaptive target intended to
hold normalized crossing intensity away from zero, exhibited approximately
linear count differences before integer target saturation. The clamp-scale
`0.25` case did not: it entered a regime in which essentially every epoch
qualified and alternative depths induced the same transition, so selection
leverage disappeared. This is disconfirming evidence against the shortcut
“non-summable qualifiers imply non-summable creation.”

**SIMULATION GA-PRIOR-005 — minority cost and controls.** In the prior Model A
`alpha=0.30`, 800-epoch, 256-trial `0.75` target-multiplier slice, C10-eclip's
mean `Delta` was `9.9375`, elasticity was `0.01578046`, and the largest sampled
path was `+26`. It forfeited `2.35810 R` per expected global marginal deposit.
Under the same coupled setup, raw records and vanilla C10 had smaller mean
deltas (`3.09765625` and `8.1875`). These finite-prefix estimates do not prove
an asymptotic class, and the target path is not claimed to be minority-attainable.
The policies were opportunity-limited by each construction, so these means are
diagnostics under one coupled budget model, not an apples-to-apples security
ranking.

**OPEN GA-PRIOR-006 — fixed-target C10-eclip proof.** Fixed-target drift and
simulation support finite-total selection, but the required attacked-process
second-moment bound has not been proved. Typical or median `lambda_n ~ 1/n`
does not suffice; a rare loose state with probability `1/n` could make
`E[lambda_n^2]` harmonic.

These results motivate the theorem search. They do not establish a universal
impossibility.

## Conjecture

**CONJECTURE GA-IMP-DIFF-1 (as tested).** For every header-only,
claimant-independent deposit process satisfying all four conditions below:

1. future expected supply depends nontrivially on the Bitcoin target trajectory;
2. supply is not equivalent to a fixed schedule plus independent sampling
   noise;
3. miners sometimes have a publication choice among Bitcoin-valid outcomes
   inducing different future geology states; and
4. those state differences affect future deposit hazard;

there exists a Bitcoin-consensus-valid target/hash environment and attacker
strategy for which expected positive issuance manipulation is non-summable.

To make “expected” coherent, this report reads “environment” as a fixed target
path or non-anticipating target policy plus a stochastic PoW ownership/race law.
A completely fixed hash trajectory supports only a pathwise comparison.
Because “non-summable manipulation” is otherwise ambiguous, the conclusion is
tested under both plausible readings: unbounded `sup_H Delta_H(sigma)` and
divergence of `sum_n [E(D_n^sigma-D_n^honest)]_+`. The decisive counterexample
bounds both.

The universal quantifier fails. Conditions 1–4 say neither that count influence
can recur nor that a hazard difference is an uncompensated count difference.
The counterexample section gives a process satisfying them whose total deposits
are at most one.

## Theorems proved

Only results labeled **THEOREM** or **LEMMA** are claimed as proved under their
stated assumptions. Items labeled **THEOREM-SKETCH** remain conditional or
incomplete and are included to expose the precise proof obligation.

### Exact zero-elasticity boundary

**THEOREM GA-ZE-1 — one-resampling optionality.** Fix a reachable history `h`,
a finite remaining horizon `m`, and a same-context honest outcome law `P_h`.
Assume an attacker owns the candidate with probability `alpha > 0`, independently
of its value; after observing it, the attacker may reject it once, forfeit its
Bitcoin reward opportunity, and let an independent replacement `Y ~ P_h` fill
the stage without otherwise changing the context. Then the strategy

```text
reject X iff Q_m(h,X) < mu_m(h)
```

increases expected deposit count by exactly

```text
alpha * E[(mu_m(h) - Q_m(h,X))_+].
```

Therefore exact strong count zero-elasticity in this upper-bound model implies
`Q_m(h,X) = mu_m(h)` almost surely.

**Proof.** Publishing the first draw returns `Q_m(h,X)`. Conditional on rejection,
the fresh draw has mean `mu_m(h)`. The pointwise gain on the rejection set is
`mu_m(h) - Q_m(h,X)`. Multiplication by candidate ownership probability and
integration gives the formula. A non-constant integrable random variable has a
non-empty lower tail below its mean, so exact zero gain forces constancy. QED.

The theorem charges one rejected Bitcoin-valid candidate; it does not claim a
free attack. It establishes count optionality, not economic rationality. A more
general rejection kernel `K` yields `Q >= KQ` under zero-elasticity. If `P_h` is
`K`-invariant, integration gives equality; constancy then needs ergodicity or a
connected co-selectability class. Disconnected outcome classes may retain
different values.

**LEMMA GA-ZE-2 — self-financing sibling values.** Under full connected
substitutability and the assumptions of `GA-ZE-1`, exact zero-elasticity implies,
for `P_h x P_h`-almost every co-selectable pair `(x,y)`,

```text
V_{m-1}(h x) - V_{m-1}(h y) = d(h,y) - d(h,x)
```

For the finite discrete Bitcoin outcome space this includes every positive-mass
pair; a continuous pointwise version additionally needs continuity plus full
support. If `0 <= d <= M`, the essential continuation-value diameter among
those sibling successor states is at most `M`. Outcomes with the same current
deposit count must have equal continuation value almost surely.

This is a local sibling-state statement. It does not bound the value diameter
between arbitrary remote histories. If the attacker is only allowed to
substitute within a fixed current-deposit class, only the equal-deposit equality
follows; the cross-class `M` bound does not.

**THEOREM GA-ZE-3 — finite-horizon schedule collapse.** Let `Z` be a
standard-Borel random element collecting every non-resampled supply-relevant
variable (for example the target path, and any timestamp, version, or template
variables not included in `X`), and let `calE=sigma(Z)`. For `P_Z`-almost every
`z`, suppose a regular conditional law `P(.|Z=z)` exists; `GA-ZE-1` and exact
strong count zero-elasticity apply at almost every descendant history and every
finite remaining horizon under that law; the rejection policy may condition on
`z`; and the resampled coordinates exhaust all remaining supply-relevant
randomness. Then `N_H` is `calE`-measurable—equivalently, conditionally
almost-surely deterministic—for every finite `H`.

**Proof sketch.** At each prefix, exact zero-elasticity makes the terminal-count
Doob martingale's conditional value invariant across `P_h`-almost every next
outcome. Recursing to terminal histories, where the conditional value equals
the realized integer `N_H`, makes `N_H` constant almost surely over the
conditional support. Equivalently, backward induction makes every `Q_m`
constant almost surely. The result is per terminal
horizon; it need not fix deposit timing. For an infinite lifetime, integrability
is required—one cannot subtract two infinite supplies. QED.

The revealed-conditioning premise is essential. If `Z` is hidden from the
attacker, unconditional `Q` values can be equal even when conditional outcomes
are not. For example, with hidden fair bit `Z`, fair resampleable bit `X`, and
`N=1{X=Z}`, observing `X` alone always gives value `1/2`; rejection has no gain,
but `N` is not conditionally deterministic. A fixed future target path is
therefore a theorem environment, not a claim that a real miner knows it.

This is the strongest defensible form of the previously reported Q2 boundary:

> For `P_Z`-almost every fixed and revealed realization of all non-resampled
> supply-relevant variables, with the remaining header randomness fully
> co-selectable, exact strong zero-elasticity at almost every reachable history
> and finite horizon makes cumulative supply by height conditionally
> deterministic.

Under the weaker deposit-preserving notion, the justified result is narrower:
any geology requiring unequal continuation value among same-deposit,
co-selectable header magnitudes has nonzero elasticity. Neither statement is a
blanket theorem about header-only processes.

### Application to raw records and C10-eclip

**LEMMA GA-RAW-1 — raw-record continuation spread.** Normalize a fixed-target
continuous hash to `[0,1]` and let `f` be the current strict record frontier.
The expected number of records in the next `H` draws is

```text
V_H(f) = sum_{i=1}^H [1 - (1-f)^i] / i.
```

For `0 < x < y`,

```text
lim_{H -> infinity} [V_H(y) - V_H(x)] = log(y/x).
```

Two record outcomes `x < y < f` both create one current deposit but lead to
unequal continuation values. A miner able to preserve `y` instead of publishing
`x` has positive creation optionality, and the continuous spread grows without
bound as `x/y -> 0`.

**Proof.** The `i`-th future draw is a record below `f` exactly when it is the
minimum of the first `i` future draws and at least one is below `f`. Symmetry
gives `[1-(1-f)^i]/i`. Subtracting the two series and using
`sum_{i>=1} z^i/i = -log(1-z)` gives `log(y/x)`. QED.

Exact Bitcoin is not continuous and does not have infinite bit width. With
strict integer frontier `g`, the expected number of remaining descending
records is the harmonic number `H_g`; zero is absorbing. The maximum expected
remaining count is finite and, even using the loose full-256-bit bound, is less than
`log(2^256)+1`, approximately `178.45`. “Unbounded single-record influence” is
therefore an idealized/security-parameter statement; exact Bitcoin still permits
an enormous range of finite depth sensitivity.

**THEOREM-SKETCH GA-C10-1 — why clipping does not restore zero-elasticity.**
C10-eclip retains two persistent order statistics. A shallow and a deeper
qualifier both make the current epoch's deposit count one, but can induce
different `(G1,G2)` successors and different future hazards. Whenever their
finite-horizon continuation values differ and the attacker can reject the
worse outcome, `GA-ZE-1` gives positive elasticity. The clip bounds
`G2/G1`; it does not make `Q_m` constant. The measured complete-state mean above
two is evidence that separate coordinate charges cannot simply be added.

C10-eclip evades the raw-record calculation in three ways: it has two-dimensional
state, clips local ratios, and accepts nonzero elasticity. It retains the exact
premise that matters for local optionality: same-deposit co-selectable
magnitudes with unequal continuation values.

### Opportunity summability and recurrence

**LEMMA GA-SEL-1 — order of an `r`-qualifier selection opportunity.** Let a
completed epoch contain `W` accepted independent hashes at target `T`, and let
`q` be the exact probability that one accepted hash crosses a live bar. If
selection requires at least `r` crossings, with `1<=r<=W`, then

```text
Pr[K >= r]
  = 1 - sum_{k=0}^{r-1} C(W,k) q^k (1-q)^(W-k)
  = C(W,r) q^r + O(q^(r+1)).
```

Writing `lambda = Wq`, this is `Theta(lambda^r)` for fixed `W` in the
small-`lambda` regime. C10 qualifier selection has `r=2`. Requiring attacker
ownership and a favorable order changes constants—and may increase the event
order in a stricter race model—but does not by itself turn opportunity count
into count creation.

**LEMMA GA-SEL-2 — sufficient condition for finite total manipulation.** Suppose
under the *attacked* process:

1. selectable event `A_n` satisfies
   `Pr(A_n | F_{n-1}) <= C q_n^r`;
2. conditional on `(F_(n-1), A_n)`, the expected positive count influence
   chargeable to that intervention is at most `J`;
3. all created deposits can be charged without double-counting to such
   interventions; and
4. `sum_n E[q_n^r] < infinity`.

Then expected cumulative creation is at most
`C J sum_n E[q_n^r]`, hence finite. Moreover
`sum_n Pr(A_n) < infinity`, so Borel–Cantelli I implies only finitely many
selection events almost surely.

No independence between the `A_n` is needed for Borel–Cantelli I. The actual
attacked-state moments are needed; honest or median scaling cannot replace
them.

The converse does not follow from a divergent opportunity sum. It additionally
needs non-vanishing uncompensated count gain, recurrence or a charging argument,
and enough dependence control to prevent cancellations. In particular:

* `K >= 2` may recur while all qualifying depths induce the same saturated
  transition;
* per-event count influence may decay fast enough to be summable;
* state differences may be a bounded timing coboundary;
* one intervention may erase the leverage of another.

**THEOREM GA-REC-1 — recurrent-vulnerability linearity.** Consider a finite
unichain average-reward MDP whose state includes target phase, geology state,
candidate ownership, and any observed publication opportunity. Let honest
publication be stationary policy `pi_0`, with average count reward `g_0` and a
bounded bias function `h_0` satisfying its Poisson equation. For action `a` at
state `s`, define baseline advantage

```text
A_0(s,a) = r(s,a) - g_0 + E[h_0(S') | s,a] - h_0(s).
```

Let a feasible stationary attacker policy `pi` have invariant distribution
`mu_pi`. Suppose:

1. `A_0(s,pi(s)) >= 0` for every state in the stationary support;
2. a set `U` of attacker-owned selectable states has
   `mu_pi(U) >= rho*p > 0`; and
3. `A_0(s,pi(s)) >= a > 0` for every `s` in `U`.

Then

```text
g_pi - g_0 >= rho * p * a,
Delta_H(pi) >= rho * p * a * H - O(1).
```

**Proof.** The average-reward performance-difference identity gives

```text
g_pi-g_0 = sum_s mu_pi(s) A_0(s,pi(s)).
```

The non-negative advantages off `U`, the lower bound on `U`, and its invariant
mass give the first inequality. Finite-state unichain bias terms are bounded,
so finite-horizon reward differs from average reward times `H` by `O(1)`. QED.

This theorem is deliberately conditional. “Target tracking” alone does not
prove premise 3. The `0.25` C10-eclip simulation is a direct warning: crossing
events became ubiquitous while count advantage vanished.

**THEOREM GA-MDP-1 — bounded-or-linear finite-state dichotomy.** Consider a
finite-state, finite-action, time-homogeneous MDP with bounded deposit rewards
(including any finite periodic target phase in state). Assume there are a
scalar optimal average reward `g*` and bounded bias `h*` satisfying the
average-reward optimality equation

```text
g* + h*(s) = max_a [r(s,a) + E(h*(S') | s,a)],
```

and a scalar honest average reward `g0` and bounded bias `h0` satisfying the
Poisson equation for honest policy `pi0`. Then, from every state `s`,

```text
V_H^* - V_H^0 = (g* - g0) H + O(1).
```

Thus `g* > g0` gives linear elasticity; `g* = g0` permits only a bounded
transient advantage. Different successor states and different next-step hazards
do not imply `g* > g0`: a bounded potential can telescope.

**Proof.** The Bellman operator is monotone and translation-invariant. Iterating
the optimality equation and sandwiching terminal value zero between translates
of `h*` gives `V_H^*(s)=Hg*+O(span(h*))`. Telescoping the honest Poisson equation
gives `V_H^0(s)=Hg0+h0(s)-E_s[h0(S_H)]`, whose remainder is bounded by
`span(h0)`. Subtraction proves the display. QED.

**THEOREM GA-WINDOW-1 — bounded single intervention for an exogenous target
path.** If each `D_n` depends only on the last `L` abstract observations, each
observation creates at most `M` deposits, and one PoW magnitude is replaced
while the future target path and all later abstract observations are held fixed,
then at most `L` output positions change and the pathwise count difference is at
most `LM`.

Repeated replacements can still create `Theta(H)` total influence. The theorem
also fails if changing the header timestamp changes later Bitcoin targets, or
if literal descendant block hashes rather than coupled abstract PoW draws must
be held fixed.

### Results by requested family

| Family | Result established | What is not established |
|---|---|---|
| A — scalar frontier | Strictly monotone continuation value across same-deposit, co-selectable tight/loose successors implies nonzero local elasticity by `GA-ZE-1`. | Scalar state alone implies neither non-summability nor even meaningful memory restriction; one integer can encode arbitrary history. Absorbing and summably weighted scalar rules are counterexamples. |
| B — finite order statistic | Under fixed-target IID sampling, a fixed `k`th CDF-order statistic has second moment `k(k+1)/((n+1)(n+2)) = Theta(n^-2)`. An honest `r=2` opportunity series is therefore summable. Under `GA-REC-1`, a target policy sustaining a vulnerable normalized state produces linear elasticity. | The fixed-target statement is not an attacked-process moment proof. Variable target tracking is not sufficient without nonzero average count gain. |
| C — finite-memory state | A genuinely finite-state unichain model obeys `GA-MDP-1`. | Fixed finite dimension is not finite state and has no blanket implication; coordinates can encode unbounded history. |
| D — bounded window | One exogenous-path intervention has the `LM` pathwise bound in `GA-WINDOW-1`. | Repeated local opportunities may still give linear gain; target feedback can defeat the simple bound. |
| E — arbitrary reconstructable header-only | No nontrivial impossibility follows from header-only and claimant-independent alone. | Finite quotas, absorbing budgets, coboundaries, target-indexed schedules, summably attenuated effects, and record frontiers occupy different elasticity classes. |

## Counterexamples

### Decisive literal counterexample

**COUNTEREXAMPLE GA-CE-1 — absorbing target/hash latch.** This construction is
only a witness against the universal theorem. It is not proposed for GoldAtom.

For canonical block `n`, let `T_n` be its target and `X_n` its integer PoW hash.
Maintain state `(A_n,Y_n)`, where `A_n` is an armed bit and `Y_n` is the previous
canonical hash. For `n>=1`, initialize `A_1=1`, `Y_1=X_0`, and define

```text
D_n = A_n * 1{T_n < T_(n-1) and X_n < Y_n}.
A_(n+1) = A_n * (1-D_n),
Y_(n+1) = X_n.
```

After the first deposit, the recurrence sets `A=0` permanently. The rule uses
only strict comparisons of Bitcoin-native targets and hashes and no numerical
issuance threshold.

At a retarget boundary from `T_0` to `T_1<T_0`, conditional on the latch still
being armed, let `Y` be the last accepted old-target hash and `X` the first
accepted new-target hash. Under independent accepted uniform hashes,

```text
Pr[X < Y]
  = [T_1(T_1+1)/2 + (T_0-T_1)(T_1+1)]
      / [(T_0+1)(T_1+1)]
  = (T_0 - T_1/2) / (T_0+1).
```

The probability is zero on a path with no target decrease. At a near-clamp
decrease `T_1 approximately T_0/4`, it is approximately `7/8`. Supply therefore
depends materially on the target path and on realized PoW magnitudes.

More formally, take a finite horizon spanning one boundary while `A=1`. For a
context-valid target path `tau_0` with no decrease and a path `tau_1` with
`T_1<T_0`,

```text
Pr[N_H=1 | tau_0] = 0,
Pr[N_H=1 | tau_1] = (T_0-T_1/2)/(T_0+1) > 0.
```

Thus neither the conditional law nor the conditional expectation is
target-independent under the schedule definition fixed above.

Suppose an attacker finds two unsaturated valid candidates `x<y` for the last
old-target height, using the same timestamp and block template except for header
search variables, and the selected sibling wins canonicalization. This joint
event has positive probability under the PoW/race model, though it is costly and
may be very rare. Choosing which owned candidate to attempt to canonicalize
stores a different `Y`. At the next block, the hazard difference is

```text
[min(y,T+1) - min(x,T+1)] / (T+1),
```

which is positive in the unsaturated case. Thus the miner has a genuine,
costly publication choice inducing different future states and hazards. No
honest hash is granted to the attacker.

Nevertheless, for every target path, hash path, ownership pattern, timestamp
policy, and publication strategy,

```text
sum_n D_n <= 1
```

pathwise. Hence `Delta_H(sigma) <= 1` for every horizon. Even the stronger local
positive-part quantity satisfies

```text
sum_n [E(D_n^sigma)-E(D_n^honest)]_+
  <= sum_n E[D_n^sigma]
  <= 1.
```

The four premises of `GA-IMP-DIFF-1` are therefore insufficient for its
conclusion.

| Conjecture premise | Witness in `GA-CE-1` |
|---|---|
| Header-only and claimant-independent | `T_n`, `X_n`, `A_n`, and `Y_n` reconstruct from canonical headers; no claimant input exists. |
| Nontrivial target dependence | A no-decrease path has zero lifetime issuance; a decrease gives the target-ratio-dependent probability above. |
| Not fixed schedule plus target-independent noise | Both whether an opportunity exists and its law depend on the realized target path and stored PoW magnitude. |
| Miner-selectable successor states | Owned same-height candidates with different hashes store different `Y`. |
| Different future hazard | The next-decrease probability is monotone in stored `Y`. |
| Claimed non-summability | Impossible: the absorbing lifetime cap is one. |

The counterexample exploits a bounded absorbing supply component. If
“genuinely discovered” were intended to require unbounded continuation-value
variation, `GA-CE-1` would be excluded—but that premise is absent from the
conjecture.

### Why an unbounded total alone does not fix the conjecture

**COUNTEREXAMPLE GA-CE-2 — scheduled background plus bounded discovered
ornament.** Add one action-invariant deposit per epoch to `GA-CE-1`. Total supply
is then unbounded in the widened-time, unbounded-chain model, and it still
contains the same nontrivial target/hash-dependent component, but all creation
elasticity remains bounded by one. Under literal current timestamps, both the
chain and this total are finite. This is plainly an issuance schedule with a
bounded ornament and is not attractive geology. It shows that the
*non-scheduled component itself* must have unbounded or asymptotically material
remaining-count variation.

### Different hazard need not mean different total count

**COUNTEREXAMPLE GA-CE-3 — bounded potential/coboundary.** Suppose a bounded
state potential `Phi` and non-negative integer deposits can be arranged as

```text
D_n = B_n + Phi(S_n) - Phi(S_(n+1)),
```

where `B_n` is policy-invariant across the entire coupled comparison horizon.
Then

```text
N_H = sum_{n<=H} B_n + Phi(S_0) - Phi(S_(H+1)).
```

Publication can change state and every near-term hazard, yet cumulative
influence is bounded by the oscillation of `Phi`. A concrete paired version
lets a first header bit choose whether one target-indexed deposit occurs in the
first or second slot of a pair; the pair total is fixed. Such rules are best
called target-indexed quotas or timing schedules, but premise 4 only says
“future hazard” and does not exclude them.

### Stronger conditions actually needed

The counterexamples show that a defensible broader conjecture would need all of
the following, or comparably strong substitutes:

1. the non-scheduled component has unbounded remaining issuance capacity;
2. its target/hash dependence is asymptotically material, not a bounded
   ornament;
3. the miner-selectable state is causally responsible for that component;
4. effective selection opportunities recur under an attainable target policy;
5. their expected uncompensated count gains are not a bounded coboundary,
   timing shift, or mutually cancelling effect; and
6. the attacked process satisfies a lower bound strong enough to imply
   `sum_n p_n g_n = infinity`, where `p_n` is feasible opportunity probability
   and `g_n` is its conditional positive count gain.

Those conditions are close to the conclusion and must be justified per family.
Target dependence alone cannot supply them.

## Proof sketches: the variable-difficulty mechanism

### Frontier contraction versus target contraction

Let `G_n` be the characteristic absolute live bar of a scale-homogeneous
frontier process, before saturation, and set

```text
q_n      = min(1, G_n/(T_n+1)),
lambda_n = W q_n,
L_G(n)   = log(G_0/G_n),
L_D(n)   = log(T_0/T_n).
```

Ignoring the immaterial `+1` away from the integer endpoint,

```text
log(lambda_n/lambda_0) = L_D(n) - L_G(n).
```

Therefore:

* `lambda_n -> 0` when frontier log contraction outruns difficulty growth;
* `lambda_n -> c>0` when their difference converges to a finite constant; if
  the difference is merely bounded, `lambda_n` stays bounded above and below
  away from the saturation endpoint;
* `lambda_n` grows when difficulty growth outruns frontier contraction.

For an attack requiring `r` qualifiers, the small-bar opportunity diagnostic is

```text
sum_n exp[-r(L_G(n)-L_D(n))].
```

If `L_G-L_D ~ beta log n`, this series is finite when `r beta>1`, harmonic at
equality, and polynomially divergent when `r beta<1`. `lambda_n -> 0` alone is
not enough: for C10's `r=2`, `lambda_n ~ n^(-1/2)` is the harmonic boundary.

### Low-hash exposure clock for finite order statistics

For epoch minima, define approximate low-hash exposure

```text
a_n = W/(T_n+1),
A_n = sum_{i<=n} a_i.
```

Near zero, the epoch-minimum CDF is `a_n x + O(x^2/T_n^2)`. In the standard
Poissonized fixed-`k` order-statistic model, the `k`th frontier has characteristic
scale `Theta(1/A_(n-1))`, so

```text
lambda_n = Theta(a_n/A_(n-1)).
```

This ratio—current low-hash exposure divided by cumulative prior exposure—is
more precise than saying merely that “difficulty rises.” It gives:

| Difficulty exposure `a_n` | `a_n/A_(n-1)` | `r=2` opportunity class |
|---|---:|---|
| bounded above and below, `0<c<=a_n<=C` | `Theta(1/n)` | finite sum |
| regularly varying `n^p L(n)`, `p>=0` | `Theta(1/n)` | finite sum |
| `exp(c n^beta)`, `0<beta<1` | `Theta(n^(beta-1))` | finite if `beta<1/2`; logarithmic at `1/2`; polynomially divergent above `1/2` |
| geometric `a^n`, `a>1` | approaches a positive constant ratio | linear opportunity count before endpoints |
| current exposure dominates all history | may saturate `q` | opportunity count may be linear, but count leverage can become zero |

For ordinary fixed-target order statistics, applying the common CDF makes the
`k`th statistic `Beta(k,n-k+1)`, and

```text
E[Y_(k)^2] = k(k+1)/[(n+1)(n+2)] = Theta(n^-2).
```

That proves honest-process `r=2` opportunity summability. It does not prove the
same moment bound under a strategic C10-eclip state process.

### C10-eclip's local drift

**THEOREM-SKETCH GA-C10-DRIFT-1 — local C10-eclip drift.** In the continuous
small-bar approximation,
with `u=G1/G2` and characteristic scale `g:=G2`, the one-epoch second-bar
contraction satisfies

```text
E[G2-G2' | G1,G2]
  = W/(2T) * (G2^2-G1^2) + O(G2^3/T^2).
```

Thus honest absolute state drift is `O(g^2/T)`. A qualifier-selection event
requires two crossings, probability `O((g/T)^2)`, and changes state on scale
`O(g)`, producing an `O(g^3/T^2)` perturbation to local state drift. This
higher-order term explains why the strategic process plausibly preserves the
leading fixed-target `1/n` scale.

It is not a complete proof: at `G1=G2`, `G1` must move before `G2`, the two
coordinates interact, and a uniform attacked-state moment bound is still open.
The prior `2.58` complete-state result is precisely why coordinatewise charges
cannot be assumed additive.

### What sustained growth actually does

The essential C10-eclip mechanism is not simply “target decreases.” It is:

1. current target exposure remains a non-negligible share of cumulative
   low-hash exposure;
2. normalized state repeatedly enters a region where a minority miner can own
   the necessary later/deeper qualifier;
3. alternative publication choices induce distinct continuation *counts*, not
   only distinct hazards; and
4. the conditional count benefit stays bounded away from zero often enough.

Geometric difficulty growth in a continuous unbounded-difficulty idealization
can hold `lambda` in an interior band, satisfying condition 1. The previous
simulations support, but do not prove, conditions 2–4 for selected C10-eclip
paths. Growth faster than the frontier is not monotonically worse: it can force
`q` to one, where every observation qualifies and depth selection no longer
changes the transition. The `0.25` control exhibited this collapse of leverage.

## Assumption audit

### What the old Q2 boundary assumes

| Assumption | Why load-bearing |
|---|---|
| Full or connected substitutability | Converts unequal `Q` values into a realizable rejection option. Header-only alone does not grant it. |
| Strong count zero-elasticity | A memoryless Bernoulli gate can have no state carryover yet still be biased by rejecting non-hits; deposit-preserving zero-elasticity is weaker. |
| Almost every conditional history and finite horizon | One terminal condition or one typical state does not give recursive schedule collapse. |
| All supply-relevant header randomness covered | Exogenous or non-resampled variables can retain unscheduled supply. |
| Bounded current deposit count | Gives the local sibling continuation-span bound. |
| Fixed and revealed conditioning environment | The proof is pointwise in non-resampled variables and lets the rejection policy condition on them. Hidden future targets can retain uncertainty. If publication changes targets, target state must instead enter the controlled process. |

### Which assumptions C10-eclip retains or evades

| Property | C10-eclip status | Consequence |
|---|---|---|
| Header-only, claimant-independent | retained | Independently reconstructable, but not manipulation-free. |
| Same-deposit co-selectable magnitudes | retained | Qualifier depths can have unequal continuation values, activating `GA-ZE-1`. |
| Persistent magnitude state | retained | State divergence can outlive the selected epoch. |
| Scalar frontier | evaded | Two coordinates invalidate a scalar-only theorem. |
| Unbounded local ratio | evaded by clip | Removes the identified new-second `A0` mechanism and raw depth-ratio explosion. |
| Exact zero-elasticity | not claimed | Q2 schedule-collapse theorem does not directly condemn it; measured nonzero elasticity must be classified quantitatively. |
| Fixed target | not intrinsic | Variable targets can keep normalized vulnerability recurrent before endpoints. |
| Uniform complete-state influence bound | not established | The proposed bound of two is contradicted numerically. |

### Missing implications in the broad conjecture

None of the following arrows is valid without additional assumptions:

```text
target-dependent supply  -> recurrent selectable state
different future hazard  -> different total continuation count
non-summable K>=2        -> non-summable positive Delta
finite state             -> bounded attack advantage
finite dimension         -> finite state
canonical-path existence -> minority-attainable target path
finite target alphabet   -> target eventually constant
```

An exact target cycle is possible in arithmetic—for example `1 -> 2` with a
two-timespan retarget and `2 -> 1` with a half-timespan retarget, both inside the
clamp—although wall-clock, timestamp, and economic attainability remain separate
questions. This is a cycle of the retarget map, not an indefinitely canonical
unmodified-Core chain: cumulative-chainwork arithmetic can overflow almost
immediately at such hard targets. Thus target finiteness alone does not prove
convergence to a plateau, and a target cycle alone does not prove a canonical
attack path.

### Cheap bytes, costly history, and exogenous uncertainty

| Source of variation | Who controls it? | Cost/status | Theorem treatment |
|---|---|---|---|
| Claim keys, salts, transaction variants, or GoldAtom work | claimant | potentially cheap and indefinitely enumerable | Excluded by claimant independence; this pass proves nothing useful for rules that admit these inputs. |
| A Bitcoin-valid header found by a miner | finding miner | ordinary SHA-256 work already incurred; withholding normally risks or forfeits `R` plus race/orphan costs | The publication option in `GA-ZE-1`; nonzero count elasticity and economic exploitability remain separate. |
| An honest miner's header | honest network | unavailable to attacker before publication | Never placed in the attacker's selectable set. |
| Future global hashrate | miners and exogenous economics collectively | not a free input to one minority miner | Can make future targets and calendar timing unknown; that uncertainty may be only an indirect difficulty-indexed schedule. |
| Accepted PoW magnitude | random-oracle sampling, conditional on target | costly history, not a claimant byte | Drives genuine record/order-statistic uncertainty but becomes censorable when the finder owns the candidate. |
| Difficulty adjustment | deterministic from canonical history once timestamps/targets are fixed | consensus rule; strategic influence requires mining/timestamp power | Either condition on a common path or include target state and attack cost explicitly. |

This separation prevents two opposite errors: treating a Bitcoin hash as a free
salt, and treating costly publication as automatically unbiased. Cost affects
rationality; it does not turn a positive `Delta_H` into zero.

## Bitcoin-consensus qualification

### Exact retarget arithmetic

On current Bitcoin mainnet:

* target changes only every 2016 blocks;
* away from a retarget boundary, contextual validity requires the new header's
  `nBits` to equal the preceding required value;
* the nominal timespan is 1,209,600 seconds;
* Bitcoin Core measures the last block timestamp minus the first block timestamp
  of the period, spanning 2015 timestamp gaps;
* that measured timespan is clamped to one quarter through four times nominal;
* at a boundary, required `nBits` is exactly the compact encoding of the
  integer-multiplied/divided old target after the timespan clamp and raw
  `powLimit` cap—not merely any decoded target inside the factor-of-four range;
* compact encoding truncation makes reachable ratios discrete rather than
  arbitrary reals;
* negative, zero, overflowing, or above-`powLimit` targets are invalid; and
* a header is PoW-valid when its unsigned hash integer is no greater than the
  decoded target.

The normative implementation is Bitcoin Core's
[`src/pow.cpp`](https://github.com/bitcoin/bitcoin/blob/master/src/pow.cpp), with
mainnet parameters in
[`src/kernel/chainparams.cpp`](https://github.com/bitcoin/bitcoin/blob/master/src/kernel/chainparams.cpp).

Calling `powLimit` a “target floor” reverses the ordering: it is the configured
raw upper bound and therefore bounds minimum difficulty. On mainnet it is
`2^224-1`, but `GetCompact(powLimit)` decodes to the slightly smaller easiest
contextually attainable target `2^224-2^208`. The hard endpoint is the smallest
positive canonically encodable target, one. From `T=1`, another quartering
computes zero before compact encoding and cannot produce a valid next target;
an extendible path must plateau or ease instead.

At the empirical REDTEAM tip target

```text
214292677573643640381615288597024997757051109113856000,
```

a continuous geometric decrease would reach below one after approximately:

| target multiplier per epoch | maximum continuous pre-endpoint epochs | nominal years at 14 days/epoch |
|---:|---:|---:|
| `0.95` | 2,395 | 91.8 |
| `0.75` | 427 | 16.4 |
| `0.25` | 89 | 3.4 |

Exact compact rounding can make a prescribed hardening path non-extendible
sooner, including by mapping a target above one directly to zero. In addition,
Bitcoin Core stores cumulative `nChainWork` in a 256-bit arithmetic type;
extreme hardening can encounter chainwork accumulation/overflow behavior before
the target reaches one. A sufficient no-wrap condition for a claimed literal
Core prefix is

```text
C_start + sum_(blocks i) floor(2^256/(T_i+1)) < 2^256.
```

The table is therefore a continuous target-arithmetic scale estimate, not a
demonstrated Core-canonical chain duration. A 100,000-epoch geometrically
decreasing floating-target run is not a literal mainnet trajectory. It is an
unbounded-difficulty and unbounded-chainwork relaxation whose finite early
segment may still expose an economically material multi-decade risk.

### Timestamp constraints and literal infinity

Bitcoin block timestamps are unsigned 32-bit values. A new block must exceed
the median time past of the preceding 11 blocks, and node acceptance also
temporarily rejects a header more than two hours ahead of the node's local
system time. That future-time check is node-time-dependent rather than a fixed
historical target-path equation. Current mainnet does not apply
Testnet4's BIP94 first-block difficulty preservation. The implementation points
are Bitcoin Core's
[`src/chain.h`](https://github.com/bitcoin/bitcoin/blob/master/src/chain.h) and
[`src/validation.cpp`](https://github.com/bitcoin/bitcoin/blob/master/src/validation.cpp).

These facts produce three distinct mathematical settings:

1. **literal current consensus:** finite timestamp range means no actually
   infinite header chain under unchanged rules;
2. **long literal Bitcoin prefixes:** study concrete finite horizons available
   before the fixed timestamp ceiling; there is no literal `H -> infinity`
   family under unchanged rules;
3. **parameterized/unbounded-chain idealization:** widen the timestamp domain
   while retaining exact target/hash arithmetic, and, if separately stated,
   widen target/hash precision to study scale asymptotics.

Under setting 1, every cumulative count is technically finite. That trivial
finiteness is not a useful security result. Under setting 3, one must state
whether targets remain exact compact integers, cycle, or inhabit an unbounded
continuous scale. A sustained geometric hardening experiment in setting 3 gives
a finite-horizon adverse stress effect in the relaxation, not literal
asymptotic divergence; an exact compact and canonical replay is required before
calling the whole prefix a Bitcoin path.

### Finite hash space

Bitcoin hashes lie in `{0,...,2^256-1}`. Strict monotone integer frontiers can
hit zero and absorb; finite-order states can tie. Near `T=1`, continuous
order-statistic formulas cease to be accurate, and multiple zero qualifiers
offer no “deeper” alternative.

This materially changes the asymptotic statement for raw records and C10-like
monotone frontiers. It does not establish a theorem for arbitrary reconstructable
processes: such a process can use unbounded height/state, target cycles, or
recurrent finite-state publication games in an unbounded-time model.

### Six levels of a target-path claim

Every future analysis should label which claim it establishes:

1. **context-valid header path:** parent links, exact required `nBits`, MTP/time
   rules, and header PoW all satisfy the applicable checks;
2. **positive-probability PoW realization:** the required finite hash events can
   occur under the random-oracle discovery law;
3. **full-block-valid realization:** every corresponding block body also
   satisfies Bitcoin consensus;
4. **canonical/active-chain realization:** the branch wins cumulative chainwork
   and propagation, with no 256-bit chainwork wrap unless that arithmetic is
   explicitly idealized;
5. **physically/economically plausible:** wall time and global hash rate can
   sustain it; and
6. **attainable by the modeled miner:** an attacker with hash share `alpha` can
   cause it at the stated cost.

`GA-IMP-DIFF-1` asks for an existential “Bitcoin-consensus-valid” target/hash
path but then pairs it with an attacker strategy. Because deposits use canonical
history, the claim needs at least level 4. If the target path is not exogenous,
the attacker claim additionally needs level 6.

## Prior-art relationship

No located primary source proves the theorem posed here. The closest work
provides components of the decision model or probability tools; its conclusions
do not transfer automatically.

| Primary source | Same decision-class contribution | Missing for this theorem |
|---|---|---|
| Bonneau, Clark, Goldfeder, [“On Bitcoin as a public randomness source”](https://eprint.iacr.org/2015/1015) (2015) | Formalizes publicly verifiable Bitcoin randomness and prices beacon manipulation through mining cost. | Does not prove zero bias, cumulative deposit bounds, or non-summability for stateful variable-target geology. |
| Bentov, Gabizon, Zuckerman, [“Bitcoin Beacon”](https://arxiv.org/abs/1605.04559) (2016) | Models reset/discard power and proves deterministic-extractor bias for resettable sources; closest abstract negative result. | Treats a beacon output, not cumulative stateful deposits, canonical races, ownership, or exact retarget paths. Bias does not imply non-summable positive count elasticity. |
| Pierrot, Wesolowski, [“Malleability of the blockchain's entropy”](https://eprint.iacr.org/2016/370) (2016/2018) | Bitcoin-specific selective mining and financial/computational budgets for entropy manipulation. | Entropy loss and beacon bias are not the `Delta_H` objective. |
| Eyal, Sirer, [“Majority is not Enough”](https://arxiv.org/abs/1311.0243) (2013/2014) | Establishes strategic withholding and canonical publication games for minority miners. | Optimizes Bitcoin revenue, not PoW-magnitude-dependent downstream issuance. |
| Sapirshtein, Sompolinsky, Zohar, [“Optimal Selfish Mining Strategies in Bitcoin”](https://arxiv.org/abs/1507.06183) (2015/2016) | Supplies the MDP methodology for optimizing adaptive publication. | Its state and reward omit geology continuation value and target-dependent deposit count. |
| Garay, Kiayias, Leonardos, [“The Bitcoin Backbone Protocol with Chains of Variable Difficulty”](https://eprint.iacr.org/2016/1048) (2016/2017) | Closest formal active-adversary framework for changing mining population and target recalculation. | Proves ledger robustness under population assumptions, not a secondary-issuance impossibility over every header state machine. |
| Bahack, [“Theoretical Bitcoin Attacks with less than Half of the Computational Power”](https://eprint.iacr.org/2013/868) (2013) | Studies block discarding and attacks interacting with difficulty. | Particular Bitcoin attack objectives do not imply a theorem for arbitrary downstream issuance state. |
| Santha, Vazirani, [“Generating Quasi-Random Sequences from Slightly-Random Sources”](https://doi.org/10.1016/0022-0000(86)90044-9) (1986) | Foundational adaptive-source impossibility where each next symbol can be biased. | An SV adversary controls source distributions much more directly than a miner who owns only costly candidate headers. Extraction impossibility is not count non-summability. |
| Chandler, [“The Distribution and Frequency of Record Values”](https://doi.org/10.1111/j.2517-6161.1952.tb00115.x) (1952), and Rényi, [record theory](https://www.numdam.org/item/ASCFM_1962__8_2_7_0/) (1962) | Classical IID record frequencies and indicator structure. | Variable targets and adversarial canonical filtering destroy the IID/exchangeability premise unless separately normalized and justified. |
| Dziubdziela, Kopociński, [“Limiting properties of the k-th record values”](https://eudml.org/doc/263206) (1976) | Higher-order record limits relevant to fixed-`k` frontiers. | Has no censorable observations, target path, or cumulative attack comparison. |
| Wald, [“Some Generalizations of the Theory of Cumulative Sums of Random Variables”](https://doi.org/10.1214/aoms/1177731092) (1945) | Supplies stopping-time machinery once a valid martingale and integrability conditions exist. | Optional stopping is not a slogan that adaptivity cannot help; publication changes the transition law and deposit count is not automatically a martingale. |
| Kiayias, Miller, Zindros, [“Non-Interactive Proofs of Proof-of-Work”](https://eprint.iacr.org/2017/963) (2017/2020) | Header-only rare-hash levels and reconstructable superblock proofs. | Proves succinct proof security, not unknown supply or publication elasticity; superblock levels use explicit thresholds. |

The closest *same-decision-class* negative result is the resettable-source
analysis in **Bitcoin Beacon**, not a theorem about record statistics. The
closest Bitcoin-specific manipulation analysis is Pierrot–Wesolowski. The
closest variable-difficulty formalism is Garay–Kiayias–Leonardos. None has the
quantifiers or cumulative count objective of `GA-IMP-DIFF-1`.

Prophet and online-selection inequalities are similarly methodological, not
dispositive: an online selector normally chooses one payoff, while a Bitcoin
miner deletes only owned costly candidates, races honest miners, and changes a
persistent downstream state. Optional-stopping results apply only after the
relevant attacked-process martingale and hypotheses are proved.

## Consequence for GoldAtom/1

1. The observed and conditional variable-target failure mechanism in C10-eclip
   is **representative of scale-homogeneous persistent frontier and
   finite-order-statistic geologies** when target evolution keeps normalized
   vulnerability recurrent and selection retains positive count value. Raw
   records, C10, and C10-eclip all have same-deposit magnitude choices with
   unequal continuation values; recurrent linear gain still requires the stated
   MDP or charging premises.
2. It is **not representative of arbitrary header-only processes**. Bounded
   quotas, absorbing latches, bounded windows, target-indexed timing
   coboundaries, and summably attenuated effects refute a blanket theorem.
3. Exact zero-elasticity remains in strong tension with non-scheduled PoW
   magnitude discovery. Under full substitutability, recursive exact zero
   elasticity collapses finite-horizon total supply to a `calE`-conditioned
   schedule, where `calE=sigma(Z)` contains all fixed, revealed, non-resampled
   variables. It is target-conditioned only when `Z` is restricted to the
   target path.
   That is a narrower and defensible impossibility boundary.
4. Variable difficulty changes the relevant clock from epoch count to cumulative
   low-hash exposure. For finite-order candidates, the quantity to control is
   `a_n/A_(n-1)` and its attacked-state moments, not merely current difficulty.
5. Exact Bitcoin's finite target, hash, timestamp, and chainwork domains preclude
   treating literal indefinite geometric hardening as an unmodified-Core
   canonical path. For monotone-frontier mechanisms, the corresponding infinite
   relaxation can describe at most a finite adverse prefix, if that prefix is
   canonically realizable. This is mathematically material but not automatically
   economically reassuring: the continuous target-only `0.95` estimate from the
   measured tip is 91.8 nominal years before `T<1`, while exact compact rounding
   and finite chainwork can intervene earlier.
6. A theorem broad enough to eliminate every attractive GoldAtom/1 geology was
   not established. Nor did this pass produce evidence that C10-eclip's measured
   elasticity is harmless. The earlier candidate-specific adverse result remains
   the relevant disposition for that construction.
7. Any next theorem attempt must define persistent discovered supply and prove
   recurrence, attacker attainability, uncompensated count gain, and target/hash
   endpoint handling, including timestamp and chainwork limits. Without those
   premises, the counterexamples above remain fatal to the universal quantifier.

This pass deliberately offers no repair, extraction rule, production candidate,
or specification language.

## Disposition

CONJECTURE-FALSE
