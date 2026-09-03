# GoldAtom Project Context

**Status:** research transition from GoldAtom/0 to GoldAtom/1  
**Canonical boundary:** release tag `v0.0.3`

## Canonical statement

> **GoldAtom/0 demonstrates object-level non-reuse and independently verifiable provenance. GoldAtom/1 investigates whether those objects can be governed by a claimant-independent scarcity law.**

This distinction is non-negotiable. An individual proof object can be unique, non-reusable, transferable, and independently assayable while the system that produces such objects remains capable of issuing arbitrarily many of them.

GoldAtom/0 therefore establishes a verified object layer, not monetary scarcity.

## Research progression

```text
GoldAtom/0
object-level non-reuse and independently verifiable provenance
        ↓
Proof-Cast Tickets
costly allocation of prior claims
        ↓
GoldAtom/1 geology
claimant-independent existence
        ↓
issuance-attack resistance
        ↓
monetary scarcity candidate
```

Each arrow is a research claim to be tested, not a conclusion inherited from the layer above it.

## Preserved boundary

The `v0.0.3` tag freezes the first complete GoldAtom/0 implementation, including its protocol, tests, simulations, examples, validation evidence, transcripts, and home page.

Historical validation artifacts MUST remain unchanged. Later work may cite, extend, or supersede them, but must not rewrite them. Failed designs and negative results are part of the project's provenance.

## Current research question

> Can canonical proof histories define rare supply opportunities that no claimant can multiply, while Proof-Cast Tickets allocate each opportunity through independently verifiable costly work?

The immediate task is to compare candidate geologies under a shared adversarial harness. Candidate families include:

- Bitcoin single-block constructions;
- Bitcoin multi-block windows;
- Bitcoin–Monero constructions;
- Bitcoin–Monero–Ethereum constructions.

These names identify test subjects, not endorsements.

## Method

GoldAtom/1 uses a falsification-first workflow:

```text
generate → attack → compare → kill → revise
```

All geology candidates must face the same attack model and declared assumptions. The project should actively seek evidence against its preferred construction.

Implementation of the Proof-Cast epoch miner/indexer is deferred until a geology survives comparative attack analysis. This prevents implementation effort from turning path dependence into protocol legitimacy.

## Claims not yet earned

GoldAtom does not yet claim:

- a fixed or defensible monetary supply;
- manipulation-resistant issuance;
- fair or egalitarian distribution;
- a production-ready work function;
- mainnet safety;
- economic value;
- “true digital gold.”

Those claims remain contingent on adversarial results, independent reproduction, and explicit protocol governance.


