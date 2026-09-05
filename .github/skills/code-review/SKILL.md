---
name: code-review
description: Adversarial review of GoldAtom protocol code, cryptographic research, simulations, specifications, and empirical claims.
---

# GoldAtom adversarial code and research review

Use this skill when reviewing GoldAtom code, research branches, specifications,
simulations, mathematical claims, protocol changes, or pull requests.

## Review posture

Treat every important claim as unverified until supported by code, tests,
derivation, empirical evidence, or an explicitly stated assumption.

The goal is not to preserve GoldAtom.

The goal is to identify the smallest reproducible reason a claim, construction,
implementation, or experiment is wrong.

Prefer falsification over confirmation.

Do not describe a construction as secure merely because no attack was found.

## Project boundaries

GoldAtom/0 is the frozen object-layer prototype.

The demonstrated GoldAtom/0 claim is:

> object-level non-reuse demonstrated

Do not silently strengthen this to:

> monetary scarcity demonstrated

GoldAtom/1 is research.

Unless a task explicitly says otherwise:

- do not modify GoldAtom/0;
- do not implement extraction;
- do not create monetary issuance;
- do not write or freeze SPEC-1;
- do not merge research branches;
- do not deploy protocol changes;
- do not create mainnet transactions;
- do not introduce private keys or secrets.

## Evidence hierarchy

Keep these categories separate:

1. THEOREM
2. LEMMA
3. THEOREM-SKETCH
4. CONDITIONAL THEOREM
5. COUNTEREXAMPLE
6. EMPIRICAL RESULT
7. SIMULATION RESULT
8. CONJECTURE
9. INTERPRETATION
10. SPECULATION

Never promote one category into another without justification.

A passing simulation is not a theorem.

A failed counterexample search is not a proof.

A counterexample to a universal theorem does not automatically produce a useful
GoldAtom construction.

## Reproducibility

Before changing anything:

1. identify the exact branch;
2. record the starting commit SHA;
3. identify relevant source files;
4. run the existing tests;
5. record commands and results.

After changes:

1. rerun the same tests;
2. run any new tests;
3. inspect the diff;
4. confirm unrelated protocol files were not modified;
5. report exact files changed.

Do not rewrite historical empirical artifacts to fit a later theory.

## Mathematical review

For mathematical claims, explicitly identify:

- random variables;
- state variables;
- conditioning;
- probability space;
- horizon;
- attacker powers;
- target/difficulty assumptions;
- quantifiers;
- asymptotic regime.

Keep distinct:

- expectation versus pathwise realization;
- finite horizon versus infinite horizon;
- pointwise bounds versus uniform bounds;
- O(), o(), Theta(), O_P(), and almost-sure statements;
- net cumulative advantage versus sum of positive local advantages.

In particular:

`X_n = O_P(1/n)`

does not by itself establish:

`sum E[X_n] < infinity`

or summability of attack-event probabilities.

Require the appropriate moment, tail, domination, or direct summability argument.

## Bitcoin model

Distinguish:

- context-valid header path;
- positive-probability PoW realization;
- full-block-valid realization;
- canonical/active-chain realization;
- physically/economically plausible realization;
- realization attainable by the modeled miner.

Do not call a path "Bitcoin-valid" without saying which level is established.

For variable difficulty distinguish:

- actual integer Bitcoin targets;
- retarget constraints;
- 4x / 1/4x clamp;
- powLimit / target floor;
- continuous approximations;
- floorless mathematical idealizations.

Do not silently transfer conclusions between these models.

## Attack classification

Classify attacks as:

- CREATION
- SUPPRESSION
- REDISTRIBUTION
- TIMING
- LIVENESS

For monetary geology, creation is the primary concern.

Measure where possible:

`Delta = E[N_attack] - E[N_honest]`

and report attacker cost separately.

Do not confuse changing ownership probability with changing deposit count.

## Miner economics

When an attack involves withholding Bitcoin-valid blocks, distinguish:

- additional hashes;
- foregone block rewards;
- fees;
- orphan/private-fork risk;
- delayed benefit;
- fraction of marginal GoldAtom issuance captured by the attacker.

Never describe forfeiting a Bitcoin-valid block as merely "one extra hash."

## Counterexamples

When reviewing an impossibility theorem, actively search for counterexamples.

For each apparent counterexample ask:

- Does it satisfy every premise literally?
- Is supply actually discovered?
- Is there a hidden height schedule?
- Is there a designer threshold?
- Is there claimant-controlled entropy?
- Is there non-header state?
- Is the manipulation bound trivial because lifetime supply is capped?
- Does it refute the theorem without being useful as a protocol?

A valid but economically useless counterexample still refutes an overly broad
universal theorem.

Say both things.

## Prior art

Separate:

> same decision or attack class

from:

> same theorem or construction

Do not claim prior art subsumes GoldAtom unless assumptions and conclusions
actually match.

Known relevant families include:

- Bit Gold
- Hashcash
- RPOW
- single-use seals
- client-side validation
- k-record processes
- Bitcoin randomness beacons
- block withholding
- selfish mining
- variable-difficulty Bitcoin analysis

Prefer primary sources.

## Review output

Lead with the most serious finding.

Use severity when reviewing code:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- NOTE

For research claims, use:

- FALSIFIED
- UNPROVED
- CONDITIONAL
- SUPPORTED
- VERIFIED

Every substantive finding should contain:

1. exact claim or code location;
2. reason it may fail;
3. smallest reproducible example or derivation;
4. consequence;
5. confidence;
6. what evidence would resolve it.

## Final disposition

End research reviews with one precise disposition appropriate to the task, such
as:

- VALID UNDER STATED ASSUMPTIONS
- INVALID
- OPEN AT NAMED LEMMA
- COUNTEREXAMPLE
- CONJECTURE-FALSE
- RESTRICTED-IMPOSSIBILITY
- UNRESOLVED

Do not use vague conclusions such as "looks good" or "seems secure."

Do not select GoldAtom/1 unless the human explicitly asks for protocol selection.
