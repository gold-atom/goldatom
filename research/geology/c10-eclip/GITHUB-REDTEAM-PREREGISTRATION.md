# C10-eclip independent GitHub REDTEAM preregistration

Status: **Phase A blind lock**  
Branch: `research/c10-eclip-github-redteam`  
Preregistered on: 2026-09-03 UTC

This document is written before opening or relying on any existing C10-eclip
conclusion, result table, simulation output, or agent summary. In particular,
the three excluded assay notes named in the task have not been read. The
predictions below are therefore commitments to tests, not restatements of prior
results.

## 1. Exact state and attack model

An epoch is the canonical Bitcoin main-chain height interval
`[2016*j, 2016*j + 2015]`. Only complete intervals are eligible. For each
eligible epoch, `m_j` is the minimum unsigned, big-endian, displayed Bitcoin
proof-of-work hash integer among its 2,016 accepted headers.

The candidate state is two integers `G1 <= G2`. The first two eligible epoch
minima `a,b` initialize it exactly as follows, without a transient un-clipped
state:

```text
G2 = max(a,b)
q  = min(a,b)
G1 = max(q, ceil(G2/e))
```

For each later epoch, the deposit predicate is evaluated first against the
pre-transition `G2`: one deposit iff `m_j < G2`. The transition then is:

```text
m_j < G1:        (G1,G2) <- (max(m_j,ceil(G1/e)), G1)
G1 <= m_j < G2:  (G1,G2) <- (G1,m_j)
m_j >= G2:       no change
```

Normative state calculations use integer arithmetic and certified decimal or
rational bounds for `e`; binary floating point is not accepted at integer
ceilings. I will prove the transition invariant `G2/G1 <= e`, including the
initial state.

The residual intervention is an observation-deletion coupling. In one epoch
whose pre-state is fixed, a shallower published qualifier `s < G2` preserves
the current deposit while an attacker-owned later valid candidate `d < s`
would, under normal publication, become the epoch minimum. The attacked branch
omits `d`; the honest counterfactual publishes it. Subsequent randomness is
coupled. I measure future deposits after the intervention separately from the
unchanged current deposit.

`K_j` always means the count of *canonical accepted* hashes below the live
pre-transition bar `G2`. `K_j >= 2` is only a network-level selection
opportunity. It does not assign ownership and does not itself establish that a
minority miner could withhold the deeper observation.

## 2. Canonical observations and verification

A canonical observation is a Bitcoin header that is:

1. in the verified main-chain header sequence at the fixed empirical tip;
2. linked to its predecessor by the header hash;
3. valid under the decoded compact target and the Bitcoin proof-of-work
   comparison; and
4. counted once at its canonical height.

The replay will independently hash serialized 80-byte headers (double SHA-256),
interpret the displayed hash as an unsigned integer, decode `nBits`, verify
parent linkage and proof of work, and check difficulty-target constancy inside
each completed retarget epoch. Ownership of historical blocks remains
unspecified. A canonical `K>=2` finding is evidence of observations, not latent
withheld blocks and not miner exploitability.

For the exact simple model requested by the task, conditional accepted hashes
are treated as independent uniform draws with
`q_j=min(1,G2_j/T_j)` and `K_j~Binomial(2016,q_j)`. I will use the task's stated
continuous-ratio convention for these probabilities and separately identify
the one-integer endpoint convention if material.

## 3. Attacker capabilities and costs

### Model A: canonical-block suppression

Hash discoveries are marked attacker with probability `alpha` and honest with
probability `1-alpha`. The attacker can suppress only its own otherwise-valid
block. A suppressed block never becomes canonical; mining continues until a
publishable block fills that height. Every suppressed valid block costs one
Bitcoin block reward plus fees (`1 R`). Replacement discoveries, ownership,
hashes, and all suppressed events are recorded. The attacker cannot suppress
an honest qualifier, retroactively erase a published block, or keep the reward
for a withheld losing candidate. Private-fork, latency, and orphan costs are
reported separately and default to zero only as a favorable lower bound on
cost.

For a successful residual selection in this model there must already be a
published shallower epoch qualifier; the attacker must later own a deeper valid
candidate; suppressing it must prevent it from entering the canonical epoch;
the shallow qualifier must remain the observed minimum; and the resulting
state must have strictly larger conditional expected future deposit count than
the honest-publication state.

### Model B: favorable selection upper bound

Each canonical slot is ownership-marked, but an attacker-owned tightening
candidate may be discarded and replaced while the attacker unrealistically
retains the slot and its Bitcoin reward. This grants cost-free valid-header
selection and is an upper bound, not ordinary mining. A separate omniscient
ceiling may select the shallowest deposit-preserving epoch minimum with future
knowledge, regardless of normal information timing; it will never be labeled
realistic.

No honest observation is assigned to the attacker in either model.

## 4. Policies

I will compare normal publication; publish-minimum (publish every owned deeper
qualifier); prefer-shallow (after a published qualifier, suppress an owned
candidate only when it would lower the epoch minimum); a state-aware threshold
policy (suppress only if discounted, attacker-captured expected GoldAtom value
exceeds Bitcoin cost); and an omniscient upper bound.

The primary policy claim to test is that, conditional on keeping one current
deposit, the highest feasible observed epoch minimum (the shallowest published
qualifier) maximizes expected future deposit count. This will be checked by
dynamic programming on small exact state spaces and paired Monte Carlo on the
full model; no monotonicity claim will be assumed merely from coordinatewise
larger state.

## 5. Quantities and bound semantics

The analysis keeps distinct:

- conditional expected single-intervention influence
  `E[Delta | state, intervention]` over a stated remaining horizon;
- realized pathwise influence `Delta(omega)` on one coupled future header
  sequence;
- worst-state expected influence, with the target class and horizon explicit;
- repeated-policy cumulative influence
  `E[N_attack(N)-N_honest(N)]`.

For every claimed constant bound I will state whether it applies to the live
`G2` bar alone or the complete `(G1,G2)` state; one deletion or a repeated
policy; fixed or variable targets; finite or arbitrary horizons; and typical or
all reachable states. Expected bounds will not be described as deterministic
ceilings.

The primary output variables are total deposits, intervention count, successful
selection probability, `K` categories, duration and probability of state
divergence/reconvergence, terminal state divergence, exact binomial qualifier
probabilities, Bitcoin blocks/rewards forfeited, marginal global deposits,
attacker-captured marginal deposits, `Delta_N`, and elasticity
`Lambda=Delta_N/E[N_honest]`.

## 6. Preregistered target paths

I will evaluate:

- A: constant target;
- B: the historical verified target sequence;
- C: a permanent plateau after the empirical tip;
- D: sustained difficulty growth, using target multipliers per epoch including
  `0.95`, `0.75`, and the Bitcoin clamp extreme `0.25`;
- E: sustained difficulty decline, using target multipliers `1.05`, `1.25`, and
  the clamp extreme `4`, capped at the proof-of-work limit where appropriate;
- F: growth bursts followed by plateaus;
- G: alternating `0.25` and `4` clamp-scale target changes;
- H: a searched consensus-valid adversarial sequence, with every retarget ratio
  inside `[0.25,4]` and the proof-of-work limit enforced.

The classification vocabulary is finite total, logarithmic, other sublinear,
linear, superlinear, or unresolved. Artificial clamp paths will be separated
from economically plausible paths.

## 7. Simulation lock

Master seed: `1269070838` (hex mnemonic `0x4BA6E536`). Independent streams are
derived by SHA-256 of the master seed plus model, target path, alpha, policy,
horizon, and trial index. Paired honest/attacked paths consume the same base
uniform variates; replacement draws caused by suppression use a separate keyed
stream so policy-dependent draw counts cannot desynchronize the base stream.

Horizon/trial budget:

| epochs | paired trials |
|---:|---:|
| 100 | 20,000 |
| 476 | 20,000 |
| 800 | 20,000 |
| 2,000 | 10,000 |
| 10,000 | 2,000 |
| 100,000 | 256 |

Tail quantiles at small samples will be reported as empirical order statistics
with their sample sizes, not implied to be high-precision estimates. Exact or
dynamic-programming results will replace Monte Carlo where practical. All six
shares `0.01,0.10,0.20,0.30,0.50,1.00`, all target-path families, and all
policies will be covered, with a reduced but explicitly reported parameter grid
for the two longest horizons if resource limits require it.

## 8. Preregistered predictions

1. The stated transition and clipped initialization preserve `G1<=G2` and
   `G2/G1<=e`; integer ambiguity from `ceil(x/e)` will be absent when certified
   interval arithmetic is used.
2. The clipped state eliminates the previously conceivable zero-current-count
   new-second (`A0`) manipulation in every reachable state.
3. `K>=2` is necessary for canonical qualifier selection, and `K=1` gives zero
   selection advantage. It is not sufficient for a minority attacker: timing,
   ownership of a selectively suppressible deeper candidate, and an already
   retained shallow canonical qualifier are additionally necessary.
4. Among feasible deposit-preserving observations, publishing/retaining the
   shallowest qualifier will maximize expected future count in the IID
   fixed-target model. The statement may need qualification for arbitrary
   nonstationary target schedules or economic objectives.
5. For one intervention at fixed target, I predict an expected influence bound
   of at most one deposit through the live `G2` bar and at most two when the
   residual `G1` effect is included. I predict this is not a pathwise bound and
   that coupled rare paths can realize values above two.
6. I predict `G2_E/T=Theta(1/E)` under IID constant target, hence exact
   `P(K>=2)=Theta(1/E^2)` in the small-`q` regime, finite expected selectable
   opportunities, and only finitely many actual selectable epochs almost surely
   if summability is proved for event probabilities under the attacked policy.
7. I predict the normal `K>=1` state-evolution term is second order in the
   dimensionless live threshold while ownership-dependent `K>=2` selection is
   third order, so persistent fixed-share selection changes a constant or lower
   order term but not the leading `1/E` decay at fixed target.
8. I predict fixed-target finite-total conclusions are not uniform over all
   Bitcoin-valid target histories. Sustained target reduction (difficulty
   growth) can track or outrun the falling absolute state, keep `G2/T` and
   `lambda` bounded away from zero, make selectable probabilities
   nonsummable, and yield linear repeated opportunities. Plateau and sustained
   target increase should instead restore or strengthen summability. Alternating
   clamp paths may produce a nonzero-density subsequence of opportunities.
9. In realistic Model A, each successful deletion costs at least `1 R`, while
   the attacker captures only a discounted fraction of global marginal supply.
   I predict low-share mining is economically unattractive unless value `V` per
   captured marginal deposit is many Bitcoin rewards; Model B will materially
   overstate feasibility.
10. I predict raw record geology has longer pathwise memory and the weakest
    economic resistance, vanilla C10 improves opportunity decay but lacks the
    clip's state-ratio restriction, and C10-eclip reduces single-event expected
    influence/tails without curing adversarial variable-target nonsummability.

These predictions are deliberately falsifiable and will be retained verbatim in
the final branch.

## 9. Falsification criteria

The claim of bounded-total manipulation is falsified for a target-path class if
I exhibit either:

1. a valid path and reachable state for which the expected cumulative deposit
   advantage of an allowed repeated policy diverges with horizon; or
2. a valid path for which actual selectable-event probabilities under the
   attacked process are nonsummable and successful selection has a positive
   asymptotic rate (or otherwise produces divergent cumulative expected
   influence).

For a purported *uniform single-intervention* bound, a certified state/path with
conditional expected influence above the bound falsifies it. A realized
pathwise `Delta>2` does not by itself falsify an expectation bound. Conversely,
fixed-target summability cannot establish uniform boundedness over variable
Bitcoin-valid paths.

Phase A will save derivations, independent code, deterministic fixtures, and
machine-readable results before any excluded note is opened. Only then will a
separate disagreement audit begin.
