# GoldAtom/0: Proof-Buried Work

**Status:** Experimental protocol draft 0  
**Profiles:** simulation and Bitcoin regtest only  
**Author:** Jcb  
**Date:** 2026-09-02

## Abstract

GoldAtom/0 defines a client-validated digital object composed of:

1. a precommitted, atom-specific proof-of-work challenge;
2. a future Bitcoin block that fixes the challenge after the claim is confirmed;
3. a successful local SHA-256d work header;
4. a mint transaction that consumes the claim and creates one title UTXO;
5. subsequent Bitcoin chainwork that buries the mint; and
6. an optional chain of single-use title transfers.

The protocol uses Bitcoin as a publication, ordering, reorganization-resistance, and title substrate. It does not create a new consensus chain. Bitcoin chainwork is treated as shared historical security; it is never counted as exclusive production work inside each atom. The local proof is the atom-specific costly signal.

GoldAtom/0 is an object-layer experiment. It does not specify a production issuance schedule or claim to constitute money.

## 1. Normative language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

An implementation conforms to GoldAtom/0 only for a named profile. No mainnet profile is defined by this document.

## 2. Goals

A conforming verifier should establish all of the following:

- **Prior claim:** protocol parameters and a spendable claim seal existed in canonical Bitcoin history before the challenge was known.
- **Challenge unpredictability:** the challenge depends on a later canonical Bitcoin block.
- **Proof binding:** a local proof valid for one claim is invalid for every different claim outpoint or canonical history.
- **Single mint:** the claim seal is spent once in a transaction containing exactly one GoldAtom mint marker.
- **Bounded latency:** the mint confirms inside a fixed profile-defined window after the challenge.
- **Public burial:** the mint remains in Bitcoin’s active best chain beneath profile-required subsequent work.
- **Unique title:** the terminal title outpoint is unspent and descends through an unbroken commitment chain from the mint.
- **Portable evidence:** all non-UTXO evidence needed by the verifier can be serialized as one proof bundle.

## 3. Non-goals

GoldAtom/0 does not establish:

- a maximum aggregate supply;
- a socially fair distribution;
- stable purchasing power;
- literal joules consumed by a producer;
- privacy of claimant or owner;
- finality independent of Bitcoin;
- resistance to all Bitcoin miner manipulation of a future-block beacon;
- fungibility among heterogeneous work proofs;
- a production-ready work function;
- a recovery mechanism for accidentally spent or lost title seals.

## 4. Security model

The verifier assumes:

- SHA-256 collision and preimage resistance;
- SHA-256d output behaves sufficiently like a uniform 256-bit value for work-threshold purposes;
- the Bitcoin view fully validates Bitcoin consensus and reports the active most-work chain;
- the verifier is not eclipsed onto an adversarial chain view;
- a Bitcoin transaction accepted into the active chain validly authorizes each input spend;
- owner keys remain uncompromised.

The protocol does not trust a claimant-supplied statement that a transaction or block exists. It asks the Bitcoin view to verify the exact transaction, block, height, inclusion proof, chain membership, and terminal UTXO state.

## 5. Data conventions

### 5.1 Hash notation

`SHA256(x)` is one SHA-256 invocation.

`SHA256d(x)` is:

```text
SHA256(SHA256(x))
```

`TaggedHash(tag, message)` is the BIP340-style construction:

```text
tag_hash = SHA256(UTF8(tag))
TaggedHash = SHA256(tag_hash || tag_hash || message)
```

Tagged hashes are used for commitments. SHA-256d is used for the local work function.

### 5.2 Integer notation

- `u32be(x)`: unsigned 32-bit big-endian integer.
- `u32le(x)`: unsigned 32-bit little-endian integer.
- `varbytes(x)`: `u32be(len(x)) || x`.
- `varstr(x)`: `varbytes(UTF8(x))`.

Integers MUST be in range. No alternate-width or non-minimal encoding is permitted.

### 5.3 Hexadecimal notation

Serialized JSON uses lowercase hexadecimal without a `0x` prefix.

All transaction IDs and block hashes are encoded as their conventional display-order 32-byte hexadecimal sequence. GoldAtom does not reverse those bytes when hashing its own protocol messages.

Targets are exactly 32 bytes and are interpreted as unsigned big-endian integers.

### 5.4 Outpoint encoding

For outpoint `u = (txid, vout)`:

```text
EncodeOutpoint(u) = bytes(txid) || u32be(vout)
```

## 6. Named profiles

### 6.1 `goldatom-sim-v0`

```text
Bitcoin-view network:          simnet
challenge_delay:               3 blocks
mint_window:                   12 blocks
maximum_target:                0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
minimum_burial_blocks:         1
minimum_burial_chainwork:      1
work algorithm:                sha256d-80-v0
```

### 6.2 `goldatom-regtest-v0`

The constants are identical except that the Bitcoin-view network MUST be `regtest`.

These targets imply approximately 16 expected hashes at the easiest permitted setting. This is intentionally non-economic.

### 6.3 No production profile

A verifier MUST reject an unknown profile. In particular, implementations MUST NOT silently reinterpret either version-zero profile as mainnet, testnet, testnet4, or signet. Profile identifiers are immutable: changing any constant or interpretation requires a new profile identifier.

## 7. Bitcoin marker scripts

GoldAtom/0 uses one canonical small direct-push `OP_RETURN` encoding:

```text
OP_RETURN || PUSHBYTES_36 || marker || digest
```

Byte form:

```text
6a 24 <4-byte marker> <32-byte digest>
```

Markers:

```text
GA0C    claim
GA0M    mint
GA0T    title transfer
```

A noncanonical push encoding, trailing byte, wrong payload length, or alternate marker is not a GoldAtom/0 marker.

Claim-seal and title outputs MUST use one of these native SegWit script templates:

```text
P2WPKH   00 14 <20 bytes>
P2WSH    00 20 <32 bytes>
P2TR     51 20 <32 bytes>
```

This is only a script-template restriction. It does not prove key possession, that a P2TR x-coordinate lifts to a curve point, or that a P2WSH witness is satisfiable. Key possession is evidenced operationally when a seal is later spent through Bitcoin consensus; deliberate key destruction remains indistinguishable from key loss.

## 8. Claim

### 8.1 Claim parameters

A claim specifies:

```text
profile_id
profile network
claim_seal_vout
claim_seal_script
algorithm
32-byte target
challenge_delay
mint_window
```

### 8.2 Claim commitment

```text
claim_message =
    varstr(profile_id) ||
    varstr(network) ||
    u32be(claim_seal_vout) ||
    varbytes(claim_seal_script) ||
    varstr(algorithm) ||
    target ||
    u32be(challenge_delay) ||
    u32be(mint_window)

claim_commitment = TaggedHash("GoldAtom/claim/v0", claim_message)
```

### 8.3 Claim transaction

A valid claim transaction MUST:

1. be confirmed in a canonical Bitcoin block at height `h_claim`;
2. have transaction ID equal to the claim outpoint’s `txid`;
3. contain the designated claim-seal output at `claim_seal_vout`;
4. have a claim-seal script exactly equal to the committed script and matching an allowed native SegWit template; and
5. contain exactly one claim marker whose digest equals `claim_commitment`.

A transaction MAY contain commitments for other claims. For the evaluated claim, the matching digest must occur exactly once.

The claim outpoint is:

```text
claim_outpoint = (claim_txid, claim_seal_vout)
```

## 9. Future-block challenge

The profile fixes:

```text
h_challenge = h_claim + challenge_delay
```

The challenge block MUST be the canonical active-chain block at that exact height.

```text
challenge_message =
    varstr(profile_id) ||
    EncodeOutpoint(claim_outpoint) ||
    bytes(claim_block_hash) ||
    claim_commitment ||
    bytes(challenge_block_hash)

challenge_digest = TaggedHash("GoldAtom/challenge/v0", challenge_message)
```

The claim block hash is included so that a claim transaction re-mined into a different history does not inherit the old challenge.

If either the claim block or challenge block is reorganized out of the active chain, the old proof bundle is invalid under the new canonical history.

## 10. Local work

### 10.1 Algorithm identifier

Version zero supports only:

```text
sha256d-80-v0
```

### 10.2 Work-header layout

The local work header is exactly 80 bytes:

| Offset | Length | Field | Encoding |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `GAW0` |
| 4 | 32 | challenge digest | raw bytes |
| 36 | 32 | claim commitment | raw bytes |
| 68 | 4 | extra nonce | `u32le` |
| 72 | 4 | reserved | four zero bytes |
| 76 | 4 | nonce | `u32le` |

```text
work_header =
    "GAW0" ||
    challenge_digest ||
    claim_commitment ||
    u32le(extra_nonce) ||
    00000000 ||
    u32le(nonce)

work_hash = SHA256d(work_header)
```

The 80-byte shape is deliberate: it is easy to benchmark against mature SHA-256d tooling while remaining a distinct domain from a Bitcoin block header. Version zero exposes 64 variable counter bits (`extra_nonce || nonce`) per claim. Targets whose mean trial count materially exceeds `2^64` therefore require many independent claims and are outside the intended operating range of this prototype. A production algorithm must either widen the rolling search space or specify a new work-header version.

### 10.3 Threshold rule

Interpret `work_hash` directly as a big-endian unsigned integer. It is valid exactly when:

```text
int(work_hash) <= int(target)
```

For a uniformly distributed 256-bit digest, the geometric mean trial count implied by target `T` is `2^256 / (T + 1)`. The integer assay field is its ceiling:

```text
expected_hashes_ceiling = ceil(2^256 / (T + 1))
expected_work_log2 = 256 - log2(T + 1)
```

This is a statistical expectation, not an observation of actual hashes performed. A successful proof may be found earlier or later. The protocol MUST NOT report the successful nonce value as a count of work performed.

## 11. Mint

### 11.1 Mint interval

A mint MUST confirm at height `h_mint` satisfying:

```text
h_challenge + 1 <= h_mint <= h_challenge + mint_window
```

The bounded interval reduces indefinite warehousing of old challenges for future hardware.

### 11.2 Mint commitment

```text
mint_message =
    varstr(profile_id) ||
    EncodeOutpoint(claim_outpoint) ||
    challenge_digest ||
    u32be(extra_nonce) ||
    u32be(nonce) ||
    work_hash ||
    u32be(title_vout) ||
    varbytes(title_script)

mint_commitment = TaggedHash("GoldAtom/mint/v0", mint_message)
```

### 11.3 Mint transaction

A valid mint transaction MUST:

1. confirm inside the mint interval;
2. spend the claim outpoint exactly once;
3. contain the designated title output at `title_vout`;
4. have a title script exactly equal to the committed script and matching an allowed native SegWit template;
5. contain exactly one GoldAtom mint marker in the entire transaction; and
6. have that marker’s digest equal `mint_commitment`.

The exactly-one-marker rule prevents one claim spend from being interpreted as multiple atom mints in the same transaction.

### 11.4 Atom identifier

```text
atom_id_message =
    bytes(mint_txid) ||
    u32be(title_vout) ||
    mint_commitment

AtomID = TaggedHash("GoldAtom/id/v0", atom_id_message)
```

The initial title outpoint is:

```text
(mint_txid, title_vout)
```

## 12. Title transfer

A title transfer closes the current title seal by spending its outpoint and designates one successor output.

For transition index `i`:

```text
transfer_message =
    varstr(profile_id) ||
    AtomID ||
    u32be(i) ||
    EncodeOutpoint(previous_title_outpoint) ||
    u32be(successor_vout) ||
    varbytes(successor_script)

transfer_commitment = TaggedHash("GoldAtom/transfer/v0", transfer_message)
```

A valid transition MUST:

1. have a contiguous zero-based index;
2. name the current title outpoint as `previous_title_outpoint`;
3. confirm no earlier than the transaction that created the previous title;
4. spend the previous title outpoint exactly once;
5. contain the designated successor output using an allowed native SegWit template;
6. contain exactly one GoldAtom transfer marker in the entire transaction; and
7. have that marker equal the recomputed transfer commitment.

After applying every included transition, the terminal title outpoint MUST exist as a confirmed output in the active-chain UTXO set. Its script and value MUST equal the originating transaction output. If it is absent, the atom is treated as spent, burned, in-flight, or represented by an incomplete bundle.

GoldAtom/0 does not attempt title recovery. Spending a title UTXO without a valid successor commitment burns or strands the client-validated object.

## 13. Bitcoin inclusion and canonicality

For the claim, mint, and every transfer, a verifier MUST establish:

- the supplied transaction inclusion proof commits to the claimed transaction;
- the claimed block is in the active best chain;
- the block hash is canonical at the claimed height;
- the decoded transaction matches the supplied transaction ID and block metadata.

The reference implementation delegates these checks to a fully validating Bitcoin Core node using `verifytxoutproof`, `getrawtransaction` with an explicit block hash, `getblockheader`, and `getblockhash`.

The proof-bundle format contains serialized Bitcoin transaction inclusion proofs but does not yet contain a standalone Bitcoin header-chain verifier. Future versions may add compact chain proofs; version zero intentionally uses a full node.

## 14. Burial

At verification time:

```text
burial_blocks = tip_height - mint_height
burial_chainwork = tip_chainwork - mint_block_chainwork
```

Both values MUST meet the selected profile’s minimums.

Burial is dynamic: the same atom acquires greater historical depth as Bitcoin advances. A verifier’s report MUST identify the tip at which the assay was calculated.

Bitcoin burial chainwork MUST remain a separate assay dimension. It MUST NOT be added to or multiplied into local expected work as though the same Bitcoin work were exclusively consumed by each atom.

## 15. Portable proof bundle

The JSON object has the following top-level form:

```json
{
  "format": "goldatom-proof",
  "version": 0,
  "profile": "goldatom-regtest-v0",
  "claim": {},
  "work": {},
  "mint": {},
  "transfers": []
}
```

Unknown fields at every bundle level and duplicate JSON keys are rejected by the reference parser. JSON key order and whitespace are not consensus-relevant; all cryptographic commitments are calculated from the canonical binary encodings in this document, not from serialized JSON.

### 15.1 Claim record

```json
{
  "outpoint": {"txid": "32-byte hex", "vout": 0},
  "block_hash": "32-byte hex",
  "height": 0,
  "seal_script_hex": "hex",
  "algorithm": "sha256d-80-v0",
  "target_hex": "32-byte hex",
  "commitment_hex": "32-byte hex",
  "txout_proof": "hex"
}
```

### 15.2 Work record

```json
{
  "challenge_height": 0,
  "challenge_block_hash": "32-byte hex",
  "challenge_digest_hex": "32-byte hex",
  "extra_nonce": 0,
  "nonce": 0,
  "work_hash_hex": "32-byte hex"
}
```

### 15.3 Mint record

```json
{
  "txid": "32-byte hex",
  "block_hash": "32-byte hex",
  "height": 0,
  "txout_proof": "hex",
  "title_vout": 0,
  "title_script_hex": "hex",
  "commitment_hex": "32-byte hex"
}
```

### 15.4 Transfer record

```json
{
  "index": 0,
  "previous_outpoint": {"txid": "32-byte hex", "vout": 0},
  "txid": "32-byte hex",
  "block_hash": "32-byte hex",
  "height": 0,
  "txout_proof": "hex",
  "successor_vout": 0,
  "successor_script_hex": "hex",
  "commitment_hex": "32-byte hex"
}
```

## 16. Verification order

The reference verifier uses fail-closed validation in this order:

1. Parse strict bundle types and lengths.
2. Load the named profile.
3. Match the Bitcoin-view network.
4. Accept only the profile’s work algorithm.
5. Reject a target easier than the profile maximum.
6. Validate claim block, inclusion, seal output, commitment, and marker.
7. Derive and validate the canonical future-block challenge.
8. Rebuild the 80-byte work header and enforce the threshold.
9. Enforce the mint interval.
10. Validate mint block, inclusion, claim spend, title output, and unique mint marker.
11. Derive the AtomID.
12. Validate each title transition in sequence.
13. Require the terminal title outpoint to be confirmed and unspent, with matching script and value.
14. Measure burial against the current canonical tip.
15. Return a multidimensional assay report.

An implementation MUST NOT return a partially valid atom after any failure.

## 17. Reorganization behavior

GoldAtom/0 has no independent fork-choice rule. Canonicality follows the verifier’s Bitcoin view.

- If the claim block is reorganized, the claim’s height or block hash may change; the old challenge is invalid.
- If the challenge block is reorganized, the challenge digest changes; the old work is invalid.
- If the mint block is reorganized but the mint later reconfirms, its transaction ID may remain the same but its block metadata and burial change. A refreshed bundle is required.
- If a title transition is reorganized, the terminal title chain reverts to the last transition still canonical and unspent.

This is intentional. The atom’s public history is not independent of Bitcoin’s canonical history.

## 18. Assay report

A conforming report SHOULD expose a vector rather than collapse the object into one “fineness” number:

```text
AtomID
algorithm
target
expected local hashes
expected local work log2
claim height
challenge height
mint height
burial blocks
burial chainwork
number of title transfers
current title outpoint
assay tip hash and height
```

Any later standardization layer that bundles heterogeneous atoms into fungible bars MUST consume their title seals so the same atom cannot back multiple bars.

## 19. Unresolved production questions

A production profile requires, at minimum, decisions about:

- aggregate issuance and difficulty adjustment;
- whether target choice is fixed, auctioned, adaptive, or market-assayed;
- resistance to Bitcoin miner manipulation of the challenge beacon;
- whether the local work function should invite existing SHA-256 ASICs or force a different resource regime;
- how a production work-header version supplies sufficient rolling nonce space beyond the 64 variable bits in `sha256d-80-v0`;
- claim fees and anti-spam policy;
- proof-bundle compression and independent header validation;
- title privacy and transfer recovery;
- economic standardization of heterogeneous proofs;
- governance of profile changes without creating discretionary monetary policy.

These are not implementation details. They determine whether GoldAtom becomes scarce matter, an expensive timestamp collectible, or a trivial token factory.

## 20. Reference implementation correspondence

| Spec concept | Reference module |
|---|---|
| canonical encodings and markers | `goldatom/encoding.py` |
| profiles | `goldatom/profiles.py` |
| commitment and work calculations | `goldatom/protocol.py` |
| proof-bundle schema | `goldatom/models.py` |
| Bitcoin Core view | `goldatom/core_rpc.py` |
| deterministic verification | `goldatom/verify.py` |
| simulation vector | `goldatom/demo.py` |
| adversarial suite | `tests/test_protocol.py` |
| real regtest lifecycle | `scripts/regtest_demo.py` |

## 21. References

- Nick Szabo, “Bit Gold”: https://nakamotoinstitute.org/library/bit-gold/
- Bitcoin block-chain reference: https://developer.bitcoin.org/reference/block_chain.html
- Bitcoin Core 31 `getblockheader`: https://bitcoincore.org/en/doc/31.0.0/rpc/blockchain/getblockheader/
- Bitcoin Core 31 `gettxoutproof`: https://bitcoincore.org/en/doc/31.0.0/rpc/blockchain/gettxoutproof/
- Bitcoin Core 31 `verifytxoutproof`: https://bitcoincore.org/en/doc/31.0.0/rpc/blockchain/verifytxoutproof/
- Bitcoin Core 31 `gettxout`: https://bitcoincore.org/en/doc/31.0.0/rpc/blockchain/gettxout/
