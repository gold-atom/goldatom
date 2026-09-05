# Referee review: variable-difficulty counterexample

## Source under review

- Starting branch: `copilot/research-audit-variable-difficulty` at `fc75ea3c75cabd87d45fe037d9c886ab9987cf1e`.
- Pinned source branch/commit: `research/variable-difficulty-impossibility` at `187874d11c3432d2fa41eb22febb0ef452f4bc4f`.
- Exact report path in that commit: `research/geology/VARIABLE-DIFFICULTY-IMPOSSIBILITY.md`.
- Byte-for-byte checksum: `f4789ab3281bb14e8d9482ba347a54a3faf0d91793d83b0372678d04feb456aa`.
- Located later errata: none.

## Exact claim extracted

The report's tested conjecture is universal: for **every** header-only, claimant-independent deposit process satisfying four premises, there **exists** a Bitcoin-consensus-valid target/hash environment and attacker strategy with non-summable positive manipulation (`research/geology/VARIABLE-DIFFICULTY-IMPOSSIBILITY.md@187874d11c3432d2fa41eb22febb0ef452f4bc4f:259-277`).

The four premises are:

1. future expected supply depends nontrivially on the Bitcoin target trajectory;
2. supply is not equivalent to a fixed schedule plus independent sampling noise;
3. miners sometimes have a publication choice among Bitcoin-valid outcomes inducing different future geology states; and
4. those state differences affect future deposit hazard (`...:262-267`).

The report defines:

- **scheduled supply** as an issuance law that, after conditioning on height or a predetermined Bitcoin-native partition, is fixed independently of realized PoW magnitudes and the future target trajectory apart from target-independent sampling noise (`...:137-149`);
- **genuinely discovered supply** as remaining expected issuance being materially changed by realized PoW magnitudes and/or the future target trajectory (`...:137-156`);
- three distinct target environments: exogenous target paths, non-anticipating target policies, and attacker-induced target paths (`...:118-134`);
- miner publication power as publish/discard control only over the miner's own found Bitcoin-valid candidates, not honest-network unpublished hashes (`...:82-113`);
- the honest/attacked comparison as a coupled expected deposit-count gap `Delta_H(sigma) = E[N_H | sigma] - E[N_H | honest]` (`...:158-181`);
- **creation elasticity** through the same `Delta_H(sigma)` family, with exact-zero, finite-total, sublinear, and linear cases distinguished explicitly (`...:158-181`).

The report also keeps equal hash attempts, equal canonical heights, and equal elapsed time separate. I found no place where the decisive `GA-CE-1` argument needs those notions to be swapped mid-proof.

## Audit of `GA-CE-1`

`GA-CE-1` defines state `(A_n, Y_n)` with armed bit `A_n` and previous accepted hash `Y_n`, initializes `A_1 = 1` and `Y_1 = X_0`, and sets

```text
D_n = A_n * 1{T_n < T_(n-1) and X_n < Y_n}
A_(n+1) = A_n * (1 - D_n)
Y_(n+1) = X_n
```

(`...:575-586`).

### Initialization

The witness is fully initialized from canonical data only: one armed bit plus the previous canonical hash (`...:578-586`). No claimant-controlled field appears.

### Deposit predicate

The deposit predicate uses two strict inequalities:

- strict target decrease `T_n < T_(n-1)`;
- strict accepted-hash decrease `X_n < Y_n`.

Equality in either place blocks a deposit. That matters because the report relies on exact integer-target/hash semantics rather than continuous approximations (`...:583-590`).

### State transitions and absorbing state

After the first deposit, `A_(n+1)=0`, so the process is permanently absorbing and no later path can issue again (`...:584-589`, `...:634-648`).

### Actual target/hash dependence

The witness is genuinely target-path-sensitive as written. At a boundary with no target decrease, issuance probability is zero; with `T_1 < T_0`, the one-boundary issuance probability becomes `(T_0 - T_1/2)/(T_0+1) > 0` under the accepted-hash model (`...:592-617`). So the report's "not merely scheduled" premise is satisfied by the exact definition it adopts.

### Miner-selectable successor states

The report's miner-choice premise is also met literally. If a miner owns two same-context old-target siblings `x < y`, then choosing which one becomes canonical stores a different `Y`, and therefore changes the next-step hazard by

```text
[min(y,T+1) - min(x,T+1)] / (T+1)
```

(`...:619-632`). This is a same-height publication choice, not a free honest-hash substitution.

### Lifetime issuance bound

The fatal point is pathwise, not asymptotic: for every target path, hash path, ownership pattern, timestamp policy, and publication strategy,

```text
sum_n D_n <= 1
```

(`...:634-648`). Therefore `sup_H Delta_H(sigma) <= 1`, and even the stronger positive-part series is bounded by `1`. That directly contradicts the conjecture's promised non-summability.

## Disposition of the broad conjecture

I independently confirm that `GA-CE-1` satisfies each premise of `GA-IMP-DIFF-1` **as written** yet defeats its conclusion. On that narrow question, the report's top-level disposition is correct: the broad conjecture is false.

This does **not** establish any stronger downstream claim:

- **A. Broad conjecture false:** yes, by `GA-CE-1`.
- **B. Restricted impossibility survives:** plausibly yes only with stronger premises such as the exact-zero-elasticity boundary and explicit recurrence/uncompensated-count assumptions (`...:702-719`, `...:1068-1088`).
- **C. Continuing discovered supply is achievable with acceptable manipulation:** not shown.
- **D. C10-eclip is secure or repaired:** not shown.

The companion `GA-CE-2` and `GA-CE-3` examples matter for that separation. They show that even unbounded **total** supply can hide the same bounded discovered component, and that changed future hazard need not imply changed total continuation count (`...:667-700`).

## Proof gaps that remain open

The report does not close the C10-eclip or variable-target program generally. The main unresolved obligations I found are:

1. `OPEN GA-PRIOR-006` remains open: a fixed-target C10-eclip second-moment bound is still unproved (`...:251-255`).
2. `GA-C10-DRIFT-1` is only a theorem sketch and explicitly lacks the uniform attacked-state moment bound needed to convert local drift into a global summability class (`...:797-818`).
3. Any replacement impossibility theorem still has to prove recurrence, attacker attainability, uncompensated count gain, and exact target/hash/timestamp endpoint handling (`...:702-719`, `...:1102-1105`).
4. The report correctly warns that an `O_P(1/n)`-style typical rate does not by itself prove summability of expectations; the open quantity is an attacked-process expectation/moment bound, not merely a pointwise or in-probability rate (`...:248-255`, `...:794-818`).

## Usefulness for GoldAtom geology

This result is useful as a boundary-cleaning review result, not as a protocol green light. It defeats an overly broad universal impossibility theorem against all header-only, claimant-independent discovered-supply mechanisms. It does **not** authorize monetary implementation, validate C10-eclip, or identify an acceptable GoldAtom/1 geology.

## Conclusion

**VALID UNDER STATED ASSUMPTIONS**

The pinned report successfully refutes `GA-IMP-DIFF-1` as written by exhibiting `GA-CE-1`, an absorbing target/hash latch that can issue at most one deposit while still satisfying the conjecture's four premises.
