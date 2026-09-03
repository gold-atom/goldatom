# GoldAtom Design Notes

These notes separate the implemented **object layer** from speculative **monetary layers**. None of the branches below is part of GoldAtom/0 validity.

## 1. The conceptual decomposition

“Proof of proof” can mean several different things:

1. **Proof about a proof-bearing history** — demonstrate facts about a PoW chain.
2. **Proof buried by another proof system** — publish one object under the accumulated work of Bitcoin.
3. **Proof whose inputs are prior proofs** — construct a higher-order scarce relation from several independent work artifacts.
4. **Proof that an exclusive costly event occurred** — Szabo’s unforgeable-costliness objective.

GoldAtom/0 implements primarily (2) and (4): a fresh atom-specific proof is created and then buried by Bitcoin. It leaves (3), the more alien “digital geology” concept, as a research branch.

## 2. Why Bitcoin burial is not the atom

A Bitcoin block can commit to thousands or millions of externally aggregated facts. If each fact claimed the full block’s work as its own exclusive substance, arbitrary replication would manufacture apparent mass without additional cost.

Therefore:

```text
local work = exclusive statistical production signal
Bitcoin work = shared ordering and revision-resistance
```

This is the most important accounting rule in the prototype.

## 3. Why use a UTXO title seal

A commitment alone establishes existence, not exclusive current ownership. A Bitcoin UTXO supplies a native single-use state transition:

```text
unspent = live title
spent into valid successor = transferred title
spent without valid successor = burned title
```

The proof object remains off-chain/client-validated; Bitcoin enforces only the input authorization and single-spend property.

## 4. Why an 80-byte local work header

The local header deliberately has the same byte length and double-SHA-256 primitive as a Bitcoin header while using a distinct magic and field layout.

Advantages:

- simple independent implementation;
- mature hashing libraries;
- transparent benchmarking;
- potential adaptation of mining tooling;
- no need to invent a fashionable “ASIC-resistant” claim that later collapses.

Disadvantages:

- likely centralization around existing SHA-256 expertise or hardware;
- work may compete economically with Bitcoin mining;
- adapting fixed-function ASIC interfaces may require a Stratum bridge;
- version zero has only 64 variable counter bits per fixed claim;
- the social meaning risks collapsing into “another SHA-256 token.”

The control implementation should remain SHA-256d. Alternative work functions should compete against it under measured adversarial benchmarks.

## 5. Why the challenge is future Bitcoin history

A claimant must commit before knowing the search seed. Otherwise a large stockpile of precomputed work could be attached opportunistically to whichever claim becomes valuable.

A future block gives:

- public chronology;
- globally inspectable seed material;
- no new committee;
- direct reorganization semantics.

It does not give perfect randomness. The block producer has some grinding and withholding discretion. A production design needs a quantified model of that discretion rather than the slogan “Bitcoin hash is random.”

## 6. Why the mint window matters

Without expiry, a claimant can preserve a challenge indefinitely. Hardware improvements then sever the relationship between the target’s nominal expected work and contemporary cost.

A bounded window creates a rough vintage:

```text
claim parameters fixed
future challenge arrives
work must be found and published before expiry
```

The window also creates a censorship vulnerability. A producer can complete work yet fail to mint if Bitcoin inclusion is delayed. Production policy must balance hardware-vintage integrity against fee-market and censorship risk.

## 7. Candidate monetary layers

### 7.1 Work-weighted bullion

Every valid atom has a heterogeneous target. A bar consumes title seals whose summed expected local work exceeds a standard threshold:

```text
sum(expected_local_hashes(atom_i)) >= bar_threshold
```

Pros:

- faithful to Szabo’s heterogeneous nuggets and standardized bundles;
- simple assay;
- no need to call every atom equal.

Cons:

- aggregate issuance still responds elastically to available hardware;
- expected work is not literal work;
- hidden optimizations distort production cost.

### 7.2 Epoch quota with deterministic difficulty

Claims in epoch `e` share one target derived from previous observed mint rate. The next target adjusts by a fully specified formula.

Pros:

- familiar supply stabilization;
- easy economic modeling.

Cons:

- converges toward an ordinary PoW currency;
- oscillation and timestamp/withholding games;
- the “digital substance” premise becomes mostly metaphor.

### 7.3 Sealed work auction

An epoch allows a fixed number of atoms. Claimants commit bids denominated in work target, and the hardest valid proofs win after reveal.

Pros:

- fixed issuance without guessing total hashpower;
- cost discovery by competition.

Cons:

- auction complexity and strategic withholding;
- failed work is destroyed;
- challenge-beacon manipulation can become highly valuable.

### 7.4 Fossil Gold

No fresh local mining determines existence. Rare deterministic relations among finalized Bitcoin, Litecoin, Monero, or other independent PoW artifacts define naturally occurring “veins.” A claimant proves discovery and secures title.

Pros:

- known physics, unknown reserves;
- truly higher-order proof inputs;
- existing computational history becomes geological substrate.

Cons:

- relation searching can become ordinary grind in disguise;
- source chains are correlated and differently secure;
- last-revealer and ownership races are severe;
- cheap chains can counterfeit “diversity”;
- no obvious exclusive production cost per discovered object.

A viable Fossil Gold function must make the valid relation scarce without allowing a searcher to create arbitrary variants of the inputs.

### 7.5 Dead-Work Gold

The ore consists of demonstrable SHA-256 shares, stale blocks, or orphan work that did not receive Bitcoin’s canonical block reward.

Pros:

- monetizes otherwise dead computation;
- could create a secondary market in verifiable work receipts;
- unusually close to “recovered digital metal.”

Cons:

- pool shares are often private and weakly standardized;
- miners can deliberately manufacture stale work;
- data availability is poor;
- rewarding dead work may degrade Bitcoin mining incentives or propagation behavior.

### 7.6 Proof intersection plus local assay

A hybrid: external PoW histories gate the moments at which a fresh GoldAtom claim may become eligible, while local work determines the atom’s grade.

This may preserve both geological rarity and exclusive cost, but it compounds attack surfaces.

## 8. Candidate challenge beacons

### Single future block

Implemented control. Minimal assumptions, maximal measurable miner influence.

### Multi-block hash accumulator

```text
seed = H(B[h+1] || ... || B[h+k])
```

Control must be quantified. The final miner can condition on earlier fixed blocks.

### XOR is not enough

XOR of block hashes sounds symmetric but still gives the final revealer selective-withholding power. A cryptographic hash of the sequence is clearer but does not remove that power.

### VDF-delayed beacon

Apply a publicly verifiable sequential function to the future Bitcoin seed. This may prevent instant exploitation and reduce the value of withholding, but introduces VDF assumptions and specialized implementation risk.

### Threshold beacon

Independent participants contribute randomness with slashing or Bitcoin-bonded penalties. This can improve bias resistance but replaces Bitcoin-only elegance with membership, liveness, and penalty governance.

## 9. Candidate proof compression

Version zero asks a full node to validate ordinary transaction inclusion and chain state. Long-term transferability may need:

- a header chain plus Merkle branches;
- NIPoPoW/FlyClient-style succinct chain proofs;
- Utreexo-style accumulator proofs for title state;
- periodic bundle refreshes at standardized checkpoints;
- redundant watchtowers that preserve transfer witnesses.

Compression must not turn an independently verifiable object into trust in one indexer.

## 10. Candidate title models

### Plain P2TR/P2WPKH title

Simple bearer ownership. Easy to lose or accidentally spend.

### Policy descriptor title

Wallet refuses spends lacking the required `GA0T` commitment. Better operational safety without changing Bitcoin consensus.

### Timelocked recovery branch

Owner can recover after a long inactivity period. Reduces permanent loss but complicates the definition of final ownership.

### MuSig or threshold title

Improves custody and institutional transfer. Increases coordination requirements.

### Confidential client-side title

Hide more transfer metadata while retaining a Bitcoin single-use seal. This moves toward RGB-like complexity and should not enter the control protocol prematurely.

## 11. Simulation agenda

Before selecting a monetary layer, run independent models for:

1. **Hashpower concentration:** distribution of atoms under hardware advantages of 2×, 10×, 100×, and 10,000×.
2. **Target dynamics:** oscillation under fixed, retargeted, and auctioned issuance.
3. **Challenge grinding:** expected value of Bitcoin block withholding for various atom prize distributions.
4. **Claim flooding:** fee costs and UTXO impact of mass precommitment.
5. **Censorship:** probability of mint-window expiry under fee shocks and targeted exclusion.
6. **Reorganizations:** atom invalidation and title rollback at different confirmation policies.
7. **Lost title:** monetary supply attrition under realistic key loss and accidental wallet consolidation.
8. **Bundling:** attack strategies against standardized bars and assay thresholds.

The best workflow is candidate → independent simulation → adversarial critique → revised candidate. Monetary rhetoric should follow, not precede, the measurements.

## 12. Near-term engineering sequence

1. Freeze GoldAtom/0 encodings and publish the test vector.
2. Execute the regtest driver against Bitcoin Core 31.1 on macOS and Linux.
3. Replace the version-zero 64-bit counter ceiling with a separately versioned rolling-work design before considering economic targets.
4. Add raw Bitcoin transaction parsing so the verifier depends on fewer decoded-RPC conventions.
5. Implement standalone Merkle-block proof parsing.
6. Add a descriptor-based title wallet that refuses accidental burns.
7. Write a Stratum bridge or benchmark proving whether existing SHA-256 hardware can process the `GAW0` header efficiently.
8. Build issuance simulations before proposing any mainnet constants.
9. Red-team challenge manipulation with explicit miner economics.
10. Only then draft GoldAtom/1.

## 13. The decisive research question

The object layer is now technically coherent enough to attack. The monetary question remains:

> Can atom-specific expected work be transformed into a scarce, standardized digital substance without either double-counting Bitcoin’s shared work or recreating an ordinary discretionary altcoin issuance schedule?

That is the project.
