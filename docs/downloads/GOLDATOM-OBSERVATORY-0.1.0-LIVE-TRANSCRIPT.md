# GoldAtom Observatory 0.1.0 — Live Lab Transcript

Captured: 2026-09-02 UTC  
Mode: isolated Bitcoin Core regtest lab, started and observed through the site API.

## Final state

```text
Atom ID             : 6444e4843b5c8c4af3bdfb2a763e7e3fd41542fd890a4572d4c9c89057fe109d
Verdict             : VALID GOLDATOM / 0
Profile             : goldatom-regtest-v0
Node height         : 107
Claim height        : 102
Challenge height    : 105
Mint height         : 106
Local attempts      : 15
Expected hashes     : 16
Burial blocks       : 1
Burial chainwork    : 2
Current title       : c2d97bf3c716154e55d9e096fb85827d8c92f3561dd8ffb7be690865148bb8ae:0
Title confirmations : 2
Verifier gates      : 16/16
Lifecycle exit      : 0
```

## Structured event stream

### 2026-09-02T07:05:42.442037Z [NODE] — Fresh GoldAtom lifecycle started

**Kind:** `lifecycle.started` · **Severity:** `signal`

Connecting to an isolated Bitcoin Core regtest node.

### 2026-09-02T07:05:42.450087Z [NODE] — Bitcoin Core connected

**Kind:** `node.connected` · **Severity:** `success`

Regtest best height is 0.

```json
{
  "height": 0,
  "tip_hash": "0f9188f13cb7b2c71f2a335e3a4fc328bf5beb436012afca590b1a11466e2206"
}
```

### 2026-09-02T07:05:42.837088Z [NODE] — Maturing regtest funds

**Kind:** `funds.mining` · **Severity:** `info`

Mining 101 blocks so the wallet can spend a coinbase output.

```json
{
  "blocks": 101
}
```

### 2026-09-02T07:05:42.885088Z [NODE] — Wallet funds matured

**Kind:** `funds.ready` · **Severity:** `success`

The private regtest chain reached height 101.

```json
{
  "height": 101
}
```

### 2026-09-02T07:05:42.915358Z [CLAIM] — Constructing claim seal

**Kind:** `claim.constructing` · **Severity:** `info`

Committing the algorithm, target, challenge delay, and spendable P2TR seal.

```json
{
  "algorithm": "sha256d-80-v0",
  "target": "0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
}
```

### 2026-09-02T07:05:42.925760Z [CLAIM] — Claim broadcast

**Kind:** `claim.broadcast` · **Severity:** `signal`

The precommitment is in the mempool and cannot be revised without changing its txid.

```json
{
  "commitment": "a4a28159780338332101981c6164256b65825205994ae8c1e2d06cc45957e62c",
  "txid": "1937f8af6306b55d65e0a4ad2d098ba7cc9af0482f5728db7766efe333a719c4"
}
```

### 2026-09-02T07:05:42.983093Z [CLAIM] — Claim seal confirmed

**Kind:** `claim.confirmed` · **Severity:** `success`

Bitcoin fixed the claim at height 102 before its future challenge existed.

```json
{
  "block_hash": "7eafc8e59f735813ae3aac8f4ee0d8f83dd883e48b00bb49431e9f85c6989fba",
  "height": 102,
  "outpoint": "1937f8af6306b55d65e0a4ad2d098ba7cc9af0482f5728db7766efe333a719c4:0"
}
```

### 2026-09-02T07:05:43.014103Z [CHALLENGE] — Waiting for unknowable future history

**Kind:** `challenge.waiting` · **Severity:** `info`

The challenge will be fixed at height 105.

```json
{
  "challenge_height": 105,
  "current_height": 102
}
```

### 2026-09-02T07:05:43.015684Z [CHALLENGE] — Regtest block 103 connected

**Kind:** `block.connected` · **Severity:** `info`

Future chain history advanced by one block.

```json
{
  "block_hash": "281f55c6e9a16f777cd8e52b684ef7bbfe1d61a4bfd3563b46c0c1d6bb3b7f59",
  "height": 103
}
```

### 2026-09-02T07:05:43.047658Z [CHALLENGE] — Regtest block 104 connected

**Kind:** `block.connected` · **Severity:** `info`

Future chain history advanced by one block.

```json
{
  "block_hash": "5f42dc303a5c321215ca4a47ae452147319776d6164a3afb7f895d0efcd97d1e",
  "height": 104
}
```

### 2026-09-02T07:05:43.079790Z [CHALLENGE] — Regtest block 105 connected

**Kind:** `block.connected` · **Severity:** `info`

Future chain history advanced by one block.

```json
{
  "block_hash": "6eca8e75bd1681467f8f49696d45bd4b0f7277bf1a6c1ae7506e16c6e7b2a66d",
  "height": 105
}
```

### 2026-09-02T07:05:43.110771Z [CHALLENGE] — Challenge locked by Bitcoin

**Kind:** `challenge.locked` · **Severity:** `signal`

The work problem now contains a canonical future block the claimant could not know at claim time.

```json
{
  "block_hash": "6eca8e75bd1681467f8f49696d45bd4b0f7277bf1a6c1ae7506e16c6e7b2a66d",
  "digest": "2e3acf23f37db18e6c7d964a083565446d436f2fb369b47f51bfc25e50c40c76",
  "height": 105
}
```

### 2026-09-02T07:05:43.140954Z [WORK] — Local extraction started

**Kind:** `work.started` · **Severity:** `warning`

Searching the fixed 80-byte SHA-256d header below the committed target.

```json
{
  "expected_hashes": 16,
  "target": "0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
}
```

### 2026-09-02T07:05:43.171270Z [WORK] — Exclusive local proof found

**Kind:** `work.found` · **Severity:** `success`

Attempt 15 satisfied the precommitted target.

```json
{
  "attempts": 15,
  "extra_nonce": 0,
  "nonce": 14,
  "work_hash": "04bf1bcc593ffe0b0eea77a01421aff2a85546face4c45c2c4b1dd81e8c87bb8"
}
```

### 2026-09-02T07:05:43.201511Z [MINT] — Constructing mint and title seal

**Kind:** `mint.constructing` · **Severity:** `info`

The claim outpoint will be consumed exactly once into a new P2TR title output.

### 2026-09-02T07:05:43.206572Z [MINT] — Mint accepted into mempool

**Kind:** `mint.broadcast` · **Severity:** `signal`

The transaction spends the single-use claim seal and designates one title output.

```json
{
  "commitment": "ce508d36060507853669e294304970aee6f1f46c3d755a4b0e0a4a0a3a1df50d",
  "txid": "c2d97bf3c716154e55d9e096fb85827d8c92f3561dd8ffb7be690865148bb8ae"
}
```

### 2026-09-02T07:05:43.240143Z [MINT] — Atom minted

**Kind:** `mint.confirmed` · **Severity:** `success`

The mint and title seal were confirmed at height 106.

```json
{
  "block_hash": "5ef0a02d94abb75c1060070640c3d9ab37ab4a598610fa76130682f176612f9e",
  "height": 106,
  "title_outpoint": "c2d97bf3c716154e55d9e096fb85827d8c92f3561dd8ffb7be690865148bb8ae:0",
  "txid": "c2d97bf3c716154e55d9e096fb85827d8c92f3561dd8ffb7be690865148bb8ae"
}
```

### 2026-09-02T07:05:43.270321Z [BURIAL] — Accumulating post-mint chainwork

**Kind:** `burial.started` · **Severity:** `info`

The goldatom-regtest-v0 profile requires 1 subsequent block.

```json
{
  "required_blocks": 1
}
```

### 2026-09-02T07:05:43.273056Z [BURIAL] — Proof burial complete

**Kind:** `burial.complete` · **Severity:** `success`

Bitcoin advanced to height 107; the mint now has required burial.

```json
{
  "block_hash": "095700bb4bf9d03f9b79b771e4f890c8662d742137b5509a4ba18024a45a8fe8",
  "tip_height": 107
}
```

### 2026-09-02T07:05:43.303587Z [TITLE] — Portable proof bundle written

**Kind:** `bundle.written` · **Severity:** `info`

/mnt/data/goldatom-observatory-release-validation/lab-20260902T070541Z/atom-0001.goldatom.json

```json
{
  "path": "/mnt/data/goldatom-observatory-release-validation/lab-20260902T070541Z/atom-0001.goldatom.json"
}
```

### 2026-09-02T07:05:43.333738Z [TITLE] — Independent assay started

**Kind:** `verification.started` · **Severity:** `info`

The proof bundle is being checked against the active Core view.

### 2026-09-02T07:05:43.342380Z [TITLE] — VALID GOLDATOM / 0

**Kind:** `verification.pass` · **Severity:** `success`

Every normative verifier gate passed against the active Bitcoin chain.

```json
{
  "atom_id": "6444e4843b5c8c4af3bdfb2a763e7e3fd41542fd890a4572d4c9c89057fe109d",
  "burial_blocks": 1,
  "burial_chainwork": "2",
  "current_title": "c2d97bf3c716154e55d9e096fb85827d8c92f3561dd8ffb7be690865148bb8ae:0"
}
```

### 2026-09-02T07:05:43.342442Z [TITLE] — Adversarial validation started

**Kind:** `adversarial.started` · **Severity:** `warning`

Mutations and a reversible challenge-block reorganization will now attack the atom.

```json
{
  "atom_id": "6444e4843b5c8c4af3bdfb2a763e7e3fd41542fd890a4572d4c9c89057fe109d"
}
```

### 2026-09-02T07:05:43.377621Z [WORK] — Mutated work hash rejected

**Kind:** `tamper.work.rejected` · **Severity:** `success`

The verifier stopped with BAD_WORK_HASH.

```json
{
  "code": "BAD_WORK_HASH"
}
```

### 2026-09-02T07:05:43.412791Z [CHALLENGE] — Mutated challenge rejected

**Kind:** `tamper.challenge.rejected` · **Severity:** `success`

The verifier stopped with BAD_CHALLENGE.

```json
{
  "code": "BAD_CHALLENGE"
}
```

### 2026-09-02T07:05:43.443614Z [CHALLENGE] — Withdrawing the challenge block

**Kind:** `reorg.started` · **Severity:** `error`

Bitcoin Core will invalidate the challenge and every dependent descendant.

```json
{
  "challenge_block": "6eca8e75bd1681467f8f49696d45bd4b0f7277bf1a6c1ae7506e16c6e7b2a66d",
  "tip_height": 107
}
```

### 2026-09-02T07:05:44.651208Z [CHALLENGE] — Noncanonical atom rejected

**Kind:** `reorg.rejected` · **Severity:** `success`

Removing the challenge history invalidated the atom with HEADER_LOOKUP.

```json
{
  "code": "HEADER_LOOKUP",
  "new_tip_height": 104
}
```

### 2026-09-02T07:05:44.681414Z [CHALLENGE] — Restoring canonical history

**Kind:** `reorg.restoring` · **Severity:** `signal`

Reconsidering the challenge block and its descendants.

```json
{
  "challenge_block": "6eca8e75bd1681467f8f49696d45bd4b0f7277bf1a6c1ae7506e16c6e7b2a66d"
}
```

### 2026-09-02T07:05:45.890868Z [TITLE] — Atom validity restored

**Kind:** `reorg.restored` · **Severity:** `success`

The unchanged proof verifies again because its committed history is canonical again.

```json
{
  "atom_id": "6444e4843b5c8c4af3bdfb2a763e7e3fd41542fd890a4572d4c9c89057fe109d",
  "tip_height": 107
}
```

### 2026-09-02T07:05:45.890961Z [TITLE] — Fresh digital matter created and attacked

**Kind:** `lifecycle.complete` · **Severity:** `signal`

The node remains available for continuous reassay in the Observatory.

```json
{
  "atom_id": "6444e4843b5c8c4af3bdfb2a763e7e3fd41542fd890a4572d4c9c89057fe109d",
  "bundle": "/mnt/data/goldatom-observatory-release-validation/lab-20260902T070541Z/atom-0001.goldatom.json"
}
```

## Adversarial outcome

- `tampered_work_rejected`: **PASS**
- `tampered_challenge_rejected`: **PASS**
- `challenge_reorg_rejected`: **PASS**
- `reconsider_restored_validity`: **PASS**

The transcript contains the lifecycle journal only. The release deliberately omits the private Core datadir, RPC cookie, and wallet database.
