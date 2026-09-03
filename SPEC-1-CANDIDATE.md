# GoldAtom/1 Candidate: Canonical Vein Auction

**Status:** non-normative research specification; not implemented; not safe for public funds  
**Object-layer dependency:** GoldAtom/0  
**Purpose:** preserve the strongest part of the proof-intersection idea without allowing claimant-controlled variants to manufacture supply

## Abstract

GoldAtom/0 proves that an individually owned, Bit-Gold-style work object can be precommitted, derived from future Bitcoin history, minted into a single-use title, and verified without launching a new consensus chain. It does not produce a defensible monetary issuance rule: fixed-target local work is compute-elastic, while an unconstrained proof-intersection rule is either non-exclusive or grindable.

GoldAtom/1 separates **existence** from **allocation**.

1. A claimant-independent relation among canonical proof-of-work histories determines whether a rare global opportunity—a **vein**—exists for epoch `e`.
2. A prior-commitment local-work contest allocates at most one title for that vein.
3. Bitcoin publishes the contest record, selects the canonical winner from a bounded window, and carries the resulting title.

The central invariant is:

> Claimants may compete to extract a vein, but claimant-controlled bytes must never determine whether the vein exists.

This is a candidate architecture, not a completed scarcity proof. It deliberately exposes the remaining source-miner manipulation, censorship, hardware concentration, and parameter-governance problems.

## 1. Design goals

A conforming GoldAtom/1 profile should attempt to provide:

- **Global supply bounded by canonical history:** at most one atom per open epoch, regardless of the number of claims, public keys, salts, or search processes.
- **Exclusive title:** exactly one canonical claimant can settle an open vein.
- **Prior commitment:** the winning identity and claim seal existed before the final source input became known.
- **Assayable local cost:** allocation depends on a separate below-target or minimum-order-statistic work proof tied to the claim and vein.
- **No double-counting:** external source-chain work schedules and secures the event but is not reported as exclusive atom-specific production work.
- **Deterministic client validation:** two verifiers with the same canonical source histories and Bitcoin blocks derive the same vein state and winner.
- **No new fork-choice rule:** Bitcoin remains the publication, ordering, and title substrate.

GoldAtom/1 does not claim to provide privacy, egalitarian mining, fixed purchasing power, legal commodity status, or immunity to source-chain capture.

## 2. Non-negotiable invariants

### 2.1 Claimant-independent existence

The vein predicate MUST NOT contain or be selectable through:

- claimant public keys;
- claim transaction IDs or output indices;
- user-provided salts;
- claimant-selected source heights;
- transaction ordering;
- a menu of equivalent encodings;
- cheap auxiliary-chain forks selected after observing other inputs.

Otherwise `M` cheap variants amplify a base gate probability `p` to:

```text
1 - (1 - p)^M
```

At `p = 1/4096`, 10,000 variants raise the effective probability from approximately `0.02441%` to approximately `91.30%`. That is ordinary grinding disguised as geology.

### 2.2 One canonical source tuple

For every profile and epoch, exactly one source tuple MUST be derivable from canonical history. A profile must specify:

- source-chain identifiers;
- exact source-height functions;
- header serialization;
- chain-selection and finalization rules;
- ordering of source records;
- behavior when a source chain stalls, reorganizes, or disappears.

### 2.3 One atom maximum per vein

An open vein has one stable `vein_id`. Regardless of claim count or work submissions, no more than one GoldAtom title may settle under that `vein_id`.

### 2.4 Separate accounting domains

A verifier reports at least three independent quantities:

1. gate rarity implied by the vein target;
2. winning local-work evidence;
3. Bitcoin burial and title depth.

They MUST NOT be added into a single “total work” value. Source history and Bitcoin burial are shared security; local work is the only exclusive extraction evidence.

## 3. Profile and epoch model

A GoldAtom/1 profile defines:

```text
profile_id
anchor_chain = bitcoin
source_chains[]
epoch_length_anchor_blocks
source_height_functions[]
source_finality_chainwork[]
vein_target
preclaim_deadline
extraction_window
commit_window
reveal_window
settlement_window
minimum_claim_bond
local_work_algorithm
work_header_version
```

The first executable profile SHOULD use Bitcoin alone, or Bitcoin plus one carefully specified auxiliary source, before attempting broad multi-chain diversity. Adding sources increases nominal independence but also adds weak-chain bribery, correlated failure, finality mismatch, and last-revealer attacks.

Let `e` be the epoch number derived only from Bitcoin height. For each source chain `S_j`, the profile deterministically selects one canonical source header:

```text
R_j(e) = chain_id_j || height_j(e) || canonical_header_j(e) || cumulative_chainwork_j(e)
```

After every source record satisfies the profile’s finalization rule, derive:

```text
vein_digest = TaggedHash(
    "GoldAtom/vein/v1",
    profile_id || epoch_u64 || R_0(e) || ... || R_k(e)
)
```

The epoch is open exactly when:

```text
uint256_be(vein_digest) <= vein_target
```

The unique vein identifier is:

```text
vein_id = TaggedHash(
    "GoldAtom/vein-id/v1",
    profile_id || epoch_u64 || vein_digest
)
```

No claimant data appears in either calculation.

## 4. Claim phase

Before the final source input is knowable, a prospector publishes a Bitcoin claim transaction containing:

- one spendable claim-seal UTXO;
- claimant title key or committed successor script;
- local-work algorithm and work-header version;
- optional bond amount;
- a `GA1C` commitment.

The claim commitment binds:

```text
profile_id
claim-seal outpoint and script
claimant key or successor script
work algorithm and version
eligible epoch or bounded epoch range
bond policy
```

A claim is eligible for epoch `e` only if it is canonical before the profile’s preclaim deadline. The deadline must precede revelation of the last source record by enough chainwork that a claimant cannot cheaply wait for the vein result and then reselect identity bytes.

Multiple claims do not create additional veins. They may create independent local-work domains, but any advantage must come from actual hashing, not from a finite per-claim nonce ceiling. Therefore GoldAtom/1 requires a separately versioned rolling work header with a practically unbounded domain.

## 5. Extraction contest

When a vein opens, each eligible claimant derives:

```text
extraction_challenge = TaggedHash(
    "GoldAtom/extract/v1",
    vein_id || claim_commitment
)
```

The claimant searches the profile’s local-work function. Each candidate binds at least:

```text
work_magic
extraction_challenge
claim_commitment
rolling_counter_or_merkleized_job_id
nonce
```

A claimant retains its lowest observed 256-bit work hash. A profile may impose an eligibility ceiling to limit spam, but the canonical ranking rule is lower numeric hash first, followed by deterministic tie-breakers that do not depend on transaction ordering.

### 5.1 Commit then reveal

To reduce copied-proof races and late adaptive submissions, the contest uses two publication phases:

1. **Commit phase:** publish `GA1W || H(work_proof || reveal_nonce)` during a bounded Bitcoin block window.
2. **Reveal phase:** publish the full work proof, reveal nonce, and claim reference during a later bounded window.

A valid reveal must:

- match a canonical prior `GA1W` commitment;
- reference an eligible preclaim;
- recompute under the vein and claim challenge;
- satisfy the profile’s work admissibility rule;
- be included before the reveal deadline.

Copying a reveal cannot steal the title because the proof is bound to the claimant’s pre-existing claim seal and title key.

## 6. Canonical winner selection

After the reveal window closes, every verifier scans the specified Bitcoin block interval and constructs the complete valid reveal set `Q_e`.

The canonical ordering is:

```text
(
  numeric_work_hash ascending,
  claim_commitment ascending,
  work_commitment_txid ascending,
  reveal_txid ascending
)
```

The first element is the provisional winner.

This is intentionally not “first transaction seen” and not “first reveal mined.” Inclusion ordering within one block must not alter the winner.

### 6.1 Settlement and fallback

The provisional winner receives a bounded settlement interval in which to spend its claim seal into:

- exactly one title UTXO;
- exactly one `GA1M` commitment binding `vein_id`, the winning proof, and the title output.

If the winner fails to settle, the right passes deterministically to the next ranked reveal in a later fixed slot. Once one valid settlement becomes canonical, all lower-ranked claims are permanently ineligible for that vein.

A production design must specify how losing claims reclaim bonds and how clients distinguish settlement, forfeiture, and deliberate atom burn.

## 7. Validation state machine

For each epoch, a client derives exactly one state:

```text
CLOSED
OPEN_UNCLAIMED
EXTRACTION
COMMIT_COMPLETE
REVEAL_COMPLETE
AWAITING_SETTLEMENT(rank)
SETTLED(atom_id)
EXHAUSTED
REORG_PENDING
```

A verifier rejects a purported GoldAtom/1 atom when any of the following holds:

- source tuple is noncanonical or insufficiently finalized;
- vein predicate is closed;
- claim missed the preclaim deadline;
- claimant-controlled data influenced the vein predicate;
- work commitment or reveal lies outside its window;
- revealed work does not match its commitment;
- local proof does not recompute;
- a lower-ranked valid reveal exists;
- settlement occurred outside the claimant’s slot;
- another canonical settlement already exists for the vein;
- mint transaction does not spend the winning claim seal exactly once;
- title output or `GA1M` marker is missing, duplicated, or inconsistent;
- current title ancestry is broken or terminal title is spent without a valid successor.

A source-chain or Bitcoin reorganization may move an epoch backward through this state machine. Finality is an assay property, not an exception to canonical validation.

## 8. Assay

A GoldAtom/1 atom is reported as a vector:

```text
vein profile and epoch
source tuple and finalization depths
vein target and implied base rarity
winning local-work hash and algorithm
number of canonical valid reveals
winner rank and settlement slot
Bitcoin mint height and cumulative burial chainwork
complete title provenance
```

The number of published reveals does not prove total hidden hashing. A low winning hash demonstrates statistical unforgeable costliness, not a literal meter reading of energy consumed.

## 9. Security analysis

### 9.1 Last-revealer manipulation

The producer of the final source block may test, withhold, or reorder candidate headers after seeing earlier source inputs. Multi-chain source tuples do not remove this; they move the privilege to the last revealer. Profiles must bound:

- candidate-header multiplicity;
- withholding cost;
- source-chain block reward and fee value;
- attack value of opening or suppressing one vein;
- correlated control across sources.

A cheap auxiliary chain can reduce, not increase, security.

### 9.2 Bitcoin inclusion censorship

A miner or coalition may censor preclaims, commitments, reveals, or settlement transactions. Multi-block windows reduce one-block discretion but do not eliminate sustained censorship. The protocol must not claim censorship neutrality without a quantified model.

### 9.3 Hardware concentration

The auction’s long-run allocation follows effective local hashpower. The gate controls the number of opportunities; it does not make the extraction contest egalitarian. Hidden optimizations may dominate distribution.

### 9.4 Claim flooding and validation cost

Even when extra claims do not amplify supply, they can increase block-space and verifier scan costs. Bitcoin fees, minimum bonds, bounded windows, and compact index commitments are possible controls. None is free of policy tradeoffs.

### 9.5 Reserve enumerability

Past cryptographic strata are public and enumerable. Once the vein relation is known, historical open epochs can be counted exactly. GoldAtom/1 therefore has unknown future realizations, not unknowable historical reserves. This limits the geological analogy and should be stated plainly.

### 9.6 Governance and parameter capture

The vein target, epoch duration, source set, and work algorithm determine scarcity and distribution. Changing them is monetary policy. A production system needs explicit versioning and opt-in validation, not an administrator who silently changes assay rules.

## 10. Falsification criteria

The canonical vein auction should be rejected or materially redesigned if any of the following is demonstrated:

1. Claimant-controlled variants can increase the number of open veins.
2. Two titles for the same `vein_id` can both validate at one canonical Bitcoin tip.
3. A source miner can open or suppress valuable veins at negligible marginal cost.
4. Winner selection depends on network latency or within-block transaction order.
5. Verifiers cannot deterministically enumerate the valid reveal set from canonical data.
6. Censorship of one decisive block reliably changes the winner.
7. Shared source-chain or burial work is represented as exclusive substance in each atom.
8. The work-header domain can be cheaply expanded through claims rather than computation.
9. The protocol requires discretionary off-chain judgment to choose the winner.
10. Data needed for long-horizon validation is not practically retainable.

## 11. Implementation sequence

GoldAtom/1 should be built in four falsifiable increments:

1. **Single-source simulator:** claimant-independent Bitcoin-derived gates; no economic value.
2. **Canonical contest indexer:** preclaims, work commitments, reveals, deterministic winner enumeration, and reversible reorg handling.
3. **Settlement prototype:** one-atom-per-vein title mint with ranked fallback and losing-claim recovery.
4. **Adversarial network model:** source grinding, sustained inclusion censorship, fee shocks, claim floods, hardware asymmetry, and data-availability failure.

Only after those passes should a second proof-of-work source be added. Multi-chain complexity should earn its place by measurably improving manipulation cost rather than by making the object sound more geological.

## 12. Current verdict

The candidate retains Szabo’s strongest contribution—individually assayable, transferable proofs of unforgeable costliness—while using proof intersections only where they survive adversarial analysis: as a claimant-independent schedule of rare global opportunities.

It does not yet establish “true digital gold.” It establishes the next testable proposition:

> Can canonical proof histories create a supply opportunity that no claimant can multiply, while a separate Bit-Gold-style contest assigns exactly one bearer title without reducing the result to a latency race or a new blockchain?
