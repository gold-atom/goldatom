# GoldAtom/0 Threat Model

**Scope:** simulation and Bitcoin regtest prototype  
**Date:** 2026-09-02

GoldAtom/0 should be evaluated as three coupled systems:

1. an atom-specific local proof-of-work;
2. a client-validated history anchored into Bitcoin;
3. a UTXO-based title chain.

A failure in any one can invalidate the object even if the other two remain sound.

## 1. Security properties under test

### 1.1 Proof non-transplantability

A valid local proof for claim outpoint `A` must not verify for claim outpoint `B`.

The challenge commits to:

- the profile;
- claim outpoint;
- claim block hash;
- claim commitment;
- future challenge block hash.

Changing any one changes the work header.

### 1.2 Claim single use

One claim seal should authorize no more than one recognized atom mint.

The mint must spend the claim UTXO. Bitcoin prevents spending that outpoint in two canonical transactions. GoldAtom additionally requires the mint transaction to contain exactly one `GA0M` marker, preventing one spend from being interpreted as several protocol mints.

### 1.3 Bounded work vintage

A claimant should not be able to create a low-difficulty claim, preserve it indefinitely, then solve it years later with far more capable hardware while presenting it as contemporaneously costly.

The mint window bounds the interval between challenge and canonical mint confirmation. This mitigates but does not eliminate hardware asymmetry.

### 1.4 Canonical public history

The claim, challenge, mint, and transfer chain should follow the active most-work Bitcoin history reported by a fully validating node.

### 1.5 Unique current title

The recognized owner state should resolve to one live terminal UTXO. A transfer must consume the preceding title and commit to one designated successor.

### 1.6 Honest assay dimensions

The protocol must not claim that shared Bitcoin chainwork is exclusive atom substance. Local expected work and Bitcoin burial remain separate dimensions.

## 2. Protected assets

- Integrity of the claim parameters.
- Integrity and uniqueness of the atom-specific work proof.
- Integrity of the mint interval.
- Integrity of the AtomID.
- Continuity and uniqueness of title.
- Accuracy of the displayed assay.
- Availability of the proof bundle and historical Bitcoin data needed to verify it.

## 3. Trust assumptions

GoldAtom/0 assumes:

- a correct SHA-256 implementation;
- no practical collision or preimage break against SHA-256;
- a fully validating Bitcoin Core node or equivalent Bitcoin view;
- an uneclipsed view of Bitcoin’s active most-work chain;
- honest local software when generating owner keys;
- secure storage of title-spending keys;
- continued availability of historical blocks, transactions, and inclusion proofs.

The prototype does not attempt to remove these assumptions.

## 4. Adversaries

### 4.1 Copying observer

Observes claims, work proofs, and pending mint transactions and attempts to copy or front-run them.

### 4.2 Malicious claimant

Chooses parameters strategically, creates many claims, withholds work, attempts multiple mints, or constructs ambiguous transactions.

### 4.3 Specialized miner

Has hidden SHA-256d optimizations, ASIC access, or a large performance advantage not reflected in public benchmark assumptions.

### 4.4 Bitcoin block producer

Can select transactions, manipulate candidate block headers within Bitcoin consensus, withhold blocks, or censor GoldAtom transactions.

### 4.5 Bitcoin reorganization attacker

Attempts to replace the claim, challenge, mint, or transfer history.

### 4.6 Title thief

Obtains a title private key or induces the owner to sign a transaction that spends the title without a valid successor commitment.

### 4.7 Verifier-view attacker

Controls or eclipses the Bitcoin node used by a recipient, causing it to report a false best chain or stale UTXO state.

## 5. Attack analysis

| Attack | Version-zero defense | Residual risk |
|---|---|---|
| Copy a work proof onto another claim | Challenge binds the exact claim outpoint and block history | None absent hash break or verifier bug |
| Front-run a visible mint | Mint must spend claimant’s claim UTXO; title script is committed | Key compromise or exotic signing-policy failure |
| Spend one claim in two blocks | Bitcoin UTXO rules select at most one spend in canonical history | Temporary competing forks until settled |
| Put two atoms in one mint transaction | Exactly one `GA0M` marker is allowed | A client ignoring this rule can be fooled |
| Change target after seeing challenge | Target is fixed by the pre-challenge claim commitment | Mass creation of alternative claims remains possible |
| Reuse an old easy challenge years later | Mint must confirm inside a bounded window | Hardware asymmetry within the window remains |
| Falsify transaction inclusion | Core validates `gettxoutproof` material and exact active-chain block | Eclipsed or malicious Bitcoin view |
| Reorganize challenge block | Old challenge and work become invalid | Deep reorg destroys apparent atom continuity |
| Duplicate title by copying proof bundle | Current UTXO state reveals which title remains live | Offline recipients can see stale state |
| Split title into two successors | Only the output named by the unique `GA0T` commitment is recognized | Other outputs can resemble titles socially but are protocol-invalid |
| Spend title without transfer marker | Atom becomes burned or bundle becomes incomplete | No recovery path in v0 |
| Use a malformed or unsupported title template | Verifier permits only native P2WPKH, P2WSH, or P2TR byte templates | Template validity does not prove key possession, a valid P2TR point, or a satisfiable P2WSH witness |
| Claim shared Bitcoin work per atom | Assay reports burial separately from local work | External promoters may still misrepresent it |
| Create unlimited trivial atoms | Profile maximum target imposes a floor | Regtest floor is intentionally trivial; production issuance unresolved |
| Censor claim or mint | Users can fee-bump or retry before confirmation | Mint window can expire under censorship |
| Manipulate future-block challenge | Bitcoin hash is costly to select, and claim predates it | A block producer may grind/withhold among candidate valid blocks |
| Secret ASIC advantage | Fixed work header is benchmarkable | Distribution may centralize dramatically |
| Proof-bundle deletion | Bitcoin preserves commitments, not all reconstruction metadata | Owners need redundant bundle backups |

## 6. Critical unresolved attacks

### 6.1 Challenge-beacon manipulation

A Bitcoin block hash is not an ideal unbiased random beacon. A block producer already searches a large candidate space and can discard or withhold a valid block if a particular GoldAtom challenge outcome is sufficiently valuable.

The current profile uses one future block because it is falsifiable and simple. Production candidates include:

- a commitment over several consecutive future block hashes;
- a delayed accumulator whose final block is not known when earlier contributions are fixed;
- a VDF applied after the Bitcoin seed;
- a commit/reveal set from independent parties, with penalties for non-reveal;
- a threshold randomness beacon anchored into Bitcoin.

Every alternative introduces additional assumptions. A multi-block construction reduces control concentration but does not remove the last-revealer problem.

### 6.2 Aggregate issuance

The object layer prevents reuse of one claim, but it does not determine how many claims may exist or how much aggregate proof can be produced.

A production monetary system needs an invariant stronger than “each atom is individually valid.” Candidate policies include:

- fixed target plus market-priced claim fees;
- globally adaptive target based on a deterministic observation window;
- periodic sealed-bid work auctions;
- standardized bars requiring a fixed sum of local expected work;
- rare proof intersections that gate which valid work can become monetary matter;
- issuance tied to dead or unrewarded proof from another system.

Each changes the political and economic character of the asset.

### 6.3 Work-function centralization

An 80-byte SHA-256d header deliberately exposes GoldAtom to existing knowledge and possibly existing hardware. This makes cost benchmarking less imaginary, but it may hand issuance to a small number of ASIC operators.

A memory-hard or sequential function could widen participation but would introduce its own hidden-optimization and verification tradeoffs. There is no neutral work function.

### 6.4 Finite per-claim search space

The version-zero work header exposes two 32-bit counters, for `2^64` candidate headers per fixed claim and challenge. This is ample for the non-economic profiles but is not a credible production search space for targets whose mean trial count is substantially larger. Creating many claims extends the aggregate space but adds Bitcoin fees, UTXO pressure, and claim-flooding incentives. A production profile needs a new work-header version or a rigorously specified rolling commitment mechanism.

### 6.5 Data availability

An `OP_RETURN` digest proves that a commitment existed; it does not reconstruct the entire proof bundle. If the owner loses claim parameters, nonce data, transaction proofs, and title history, the atom may remain visible but unverifiable as a complete object.

Production options include:

- redundant content-addressed archives;
- bundle commitments published through multiple channels;
- deterministic reconstruction from Bitcoin plus a minimal witness;
- erasure-coded owner backups;
- optional data-availability networks that do not control validity.

### 6.6 Title key loss and accidental burn

UTXO title is intentionally unforgiving. That resembles bearer gold, but ordinary wallet software can accidentally spend, consolidate, or fee-bump the title output without preserving the GoldAtom transfer commitment.

Production title scripts likely require:

- dedicated wallets;
- output labeling and coin control;
- policy descriptors that refuse uncommitted spends;
- possibly recovery branches with long timelocks;
- explicit distinction between transfer and destruction.

Recovery weakens pure bearer finality and must be designed transparently.

## 7. Verification failures that must be fatal

The reference verifier treats each as atom invalidity at the current chain tip:

- unknown profile or wrong Bitcoin network;
- unsupported work algorithm;
- malformed lengths or noncanonical hexadecimal;
- target above profile maximum;
- noncanonical claim, challenge, mint, or transfer block;
- invalid transaction inclusion proof;
- claim commitment mismatch;
- absent or duplicate matching claim marker;
- challenge mismatch;
- local work mismatch or insufficient threshold;
- mint outside the allowed interval;
- claim not spent exactly once by the mint;
- zero or multiple mint markers;
- title output mismatch or unspendability;
- broken title-transition ancestry;
- noncontiguous transition indices;
- absent or duplicate transfer marker;
- terminal title UTXO missing, unconfirmed, or inconsistent with its originating output;
- insufficient burial.

No “mostly valid” state exists.

## 8. Falsification criteria

The current architecture should be rejected or materially redesigned if any of the following is demonstrated:

1. A single canonical claim spend can create two independently valid GoldAtom/0 AtomIDs under the normative rules.
2. A valid work proof can be transplanted to a different claim without equivalent new work.
3. A title can be split into two terminal UTXOs that both verify under the same AtomID and chain tip.
4. Shared Bitcoin burial can be double-counted in a way the normative assay treats as exclusive atom production.
5. A practical challenge-grinding strategy gives one Bitcoin block producer near-deterministic control over valuable atom outcomes at negligible cost.
6. A production issuance rule cannot be specified without discretionary off-chain governance over who may mint.
7. Verifiers cannot reconstruct or retain enough data for long-horizon independent validation.

The protocol should survive adversarial simulation before any public economic value is attached.
