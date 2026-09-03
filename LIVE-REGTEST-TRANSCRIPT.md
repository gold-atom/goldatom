# GoldAtom/0 Live Regtest Transcript

**Execution date:** 2026-09-02  
**Protocol release after validation:** `0.0.2`  
**Scope:** disposable local Bitcoin Core `regtest`; no public network and no real funds  
**Transcript status:** terminal output below is copied from preserved stdout/stderr and node evidence; RPC credentials are omitted

## 0. Outcome

The unmodified GoldAtom/0 lifecycle driver completed successfully on its first live run:

```text
claim at 102 → challenge at 105 → local proof → mint at 106 → burial at 107 → valid title
```

The serialized bundle was then verified by a separate CLI process against the same fully validating node. Two semantic mutations were rejected. Invalidating the challenge block rolled the node back to height 104 and invalidated the atom; reconsidering the block restored the exact chain and atom.

The preserved atom is:

```text
Atom ID:        9dcf1564738e803d3ac036d4f609a123e4efee9ade19101a6e2750cfd1f9b031
Bundle:         examples/live-regtest-2026-09-02.goldatom.json
Bundle SHA-256: b218d596d85f9c85591fa7509cf2e43486f1f6365d81ecdc9bebb578557a7cef
Current title:  f1624bb71a62c1c661d940739429a5a3a8f0415cb8390f4f6386a09a9a83506c:0
```

## 1. Binary acquisition and provenance

The sandbox could not retrieve the deterministic Bitcoin Core 31.1 release archive directly:

```text
https://bitcoincore.org/bin/bitcoin-core-31.1/bitcoin-31.1-x86_64-linux-gnu.tar.gz
ERROR: download failed
```

No successful 31.1 execution is claimed. The run instead used a fresh, non-expired `bitcoind` artifact built by Bitcoin Core's HWI continuous-integration workflow from Bitcoin Core master.

```text
HWI repository:       bitcoin-core/HWI
HWI workflow run:     32899502994 (successful)
HWI commit:           e63a0af2bf5c7c60b8cc71d99aba59068e8be0f0
Artifact ID/name:     9584237798 / bitcoind
Recorded artifact SHA-256:
7120a949b516e692d0dd197a3820308b704c89d97163f0f2b99e133aadef61cc
Downloaded artifact SHA-256:
7120a949b516e692d0dd197a3820308b704c89d97163f0f2b99e133aadef61cc
```

The HWI build action clones `bitcoin/bitcoin`, builds `bitcoind`, archives it, and uploads that archive. The binary identifies its exact source revision:

```console
$ bitcoind --version
Bitcoin Core daemon version v31.99.0-031175197f1b bitcoind
Copyright (C) 2009-2026 The Bitcoin Core developers
```

```text
Bitcoin source commit:
031175197f1b7f90397b838a381f0892a74ca62a

Extracted bitcoind SHA-256:
8e3afd78738ebc6d59787fc232c4f0025b6a3dd1e2c59cee4fd1b5ed1ba3dba4
```

**Provenance boundary:** GitHub's matching artifact digest establishes that the retrieved artifact equals the artifact recorded for that CI run. This is still weaker provenance than a deterministic, signed Bitcoin Core release package. The exact 31.1 release run remains open.

## 2. Environment

```text
OS:      Linux 6.18.35 x86_64, glibc 2.41
Python:  CPython 3.13.5, GCC 14.2.0
Core:    /Satoshi:31.99.0/
Network: regtest
Pruned:  false
Peers:   0
Wallet:  descriptor wallet "goldatom-demo"
```

The node was launched locally with inbound P2P listening disabled; the captured run reported zero peers:

```console
$ bitcoind \
    -regtest \
    -datadir=/mnt/data/goldatom-regtest-node \
    -server=1 \
    -txindex=1 \
    -fallbackfee=0.0002 \
    -listen=0 \
    -daemonwait=1
Bitcoin Core starting
```

The actual local RPC credential was supplied out of band and is intentionally omitted here.

## 3. Complete lifecycle run

Command, shown with authentication redacted:

```console
$ python3 scripts/regtest_demo.py \
    --rpc-user '<local-regtest-user>' \
    --rpc-password '<redacted>' \
    --output examples/regtest.goldatom.json
```

Preserved combined output:

```text
Mining 101 regtest blocks to create mature wallet funds...
Claim confirmed at height 102: 4ccc55c2fa683116c609b7dd7097e0cdc948652889d90a4bd7f6f774911fdc95:0
Challenge fixed by block 105: 52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216
Local proof found after 25 attempts: 0dd572dc76c8d3ab561c38156ff53a5147baca218311bcdea07271173312f5d7
VALID GOLDATOM/0

Profile:                    goldatom-regtest-v0
Atom ID:                    9dcf1564738e803d3ac036d4f609a123e4efee9ade19101a6e2750cfd1f9b031
Expected local hashes:      16
Expected local work:        2^4.0000
Claim height:               102
Challenge height:           105
Mint height:                106
Bitcoin burial blocks:      1
Bitcoin burial chainwork:   2
Title transfers:            0
Current title:              f1624bb71a62c1c661d940739429a5a3a8f0415cb8390f4f6386a09a9a83506c:0
Assayed at tip:             107 (21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950)

Proof bundle written to examples/regtest.goldatom.json
EXIT_STATUS=0
```

The output bundle was frozen under the dated filename:

```console
$ cp examples/regtest.goldatom.json \
    examples/live-regtest-2026-09-02.goldatom.json

$ sha256sum examples/live-regtest-2026-09-02.goldatom.json
b218d596d85f9c85591fa7509cf2e43486f1f6365d81ecdc9bebb578557a7cef  examples/live-regtest-2026-09-02.goldatom.json
```

## 4. Independent serialized-bundle verification

This was a new Python process reading the JSON bundle from disk and resolving Bitcoin state through `CoreBitcoinView`:

```console
$ python3 -m goldatom verify \
    examples/live-regtest-2026-09-02.goldatom.json \
    --json
{
  "as_of_tip_hash": "21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950",
  "as_of_tip_height": 107,
  "atom_id": "9dcf1564738e803d3ac036d4f609a123e4efee9ade19101a6e2750cfd1f9b031",
  "burial_blocks": 1,
  "burial_chainwork": "2",
  "challenge_height": 105,
  "claim_height": 102,
  "current_title_outpoint": {
    "txid": "f1624bb71a62c1c661d940739429a5a3a8f0415cb8390f4f6386a09a9a83506c",
    "vout": 0
  },
  "expected_local_hashes": 16,
  "expected_local_work_log2": 4.0,
  "mint_height": 106,
  "profile": "goldatom-regtest-v0",
  "target_hex": "0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
  "title_transfers": 0,
  "valid": true
}
EXIT_STATUS=0
```

## 5. Live semantic-tamper rejection

### 5.1 Altered local-work hash

The final hexadecimal nibble of `work.work_hash_hex` was changed while keeping the bundle structurally valid.

```console
$ python3 -m goldatom verify \
    validation/live-negative/tampered-work-hash.goldatom.json \
    --json
INVALID: BAD_WORK_HASH: local-work hash does not recompute
EXIT_STATUS=2
```

### 5.2 Altered challenge digest

The final hexadecimal nibble of `work.challenge_digest_hex` was changed while keeping the canonical challenge block unchanged.

```console
$ python3 -m goldatom verify \
    validation/live-negative/tampered-challenge-digest.goldatom.json \
    --json
INVALID: BAD_CHALLENGE: challenge digest does not recompute from canonical history
EXIT_STATUS=2
```

## 6. Live reversible reorganization test

### 6.1 Before invalidation

```json
{
  "bestblockhash": "21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950",
  "blocks": 107
}
```

### 6.2 Invalidate the canonical challenge block

```console
$ bitcoin-rpc invalidateblock \
    52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216
```

The challenge, mint, and burial blocks were disconnected:

```json
{
  "bestblockhash": "5bede6868322fc88c6c686131012b22b4a9cf02198b46f5982f8ae96763a97c9",
  "blocks": 104
}
```

Verification while the challenge height was outside the active chain:

```console
$ python3 -m goldatom verify \
    examples/live-regtest-2026-09-02.goldatom.json \
    --json
INVALID: HEADER_LOOKUP: could not load challenge header: Bitcoin Core RPC error -8: Block height out of range
EXIT_STATUS=2
```

### 6.3 Reconsider the challenge block

```console
$ bitcoin-rpc reconsiderblock \
    52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216
```

The original best chain returned:

```json
{
  "bestblockhash": "21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950",
  "blocks": 107
}
```

Verification after restoration:

```console
$ python3 -m goldatom verify \
    examples/live-regtest-2026-09-02.goldatom.json \
    --json
{
  "as_of_tip_hash": "21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950",
  "as_of_tip_height": 107,
  "atom_id": "9dcf1564738e803d3ac036d4f609a123e4efee9ade19101a6e2750cfd1f9b031",
  "burial_blocks": 1,
  "burial_chainwork": "2",
  "challenge_height": 105,
  "claim_height": 102,
  "current_title_outpoint": {
    "txid": "f1624bb71a62c1c661d940739429a5a3a8f0415cb8390f4f6386a09a9a83506c",
    "vout": 0
  },
  "expected_local_hashes": 16,
  "expected_local_work_log2": 4.0,
  "mint_height": 106,
  "profile": "goldatom-regtest-v0",
  "target_hex": "0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
  "title_transfers": 0,
  "valid": true
}
EXIT_STATUS=0
```

## 7. Relevant Bitcoin Core debug-log evidence

```text
2026-09-02T05:55:44Z Bitcoin Core version v31.99.0-031175197f1b (release build)
2026-09-02T05:55:44Z Using data directory /mnt/data/goldatom-regtest-node/regtest
2026-09-02T05:55:44Z Using at most 200 automatic connections (16384 file descriptors available)
2026-09-02T05:55:55Z [goldatom-demo] AddToWallet 4ccc55c2fa683116c609b7dd7097e0cdc948652889d90a4bd7f6f774911fdc95 new InMempool
2026-09-02T05:55:55Z UpdateTip: new best=7e6c0e91c4ebf58501532f07d7cc7a26bff2ddd59da0127728f9609aefd4cafe height=102 version=0x20000000 log2_work=7.686501 tx=104 date='2026-09-02T05:56:13Z' progress=1.000000 cache=0.3MiB(104txo)
2026-09-02T05:55:55Z [goldatom-demo] AddToWallet 4ccc55c2fa683116c609b7dd7097e0cdc948652889d90a4bd7f6f774911fdc95 update Confirmed (block=7e6c0e91c4ebf58501532f07d7cc7a26bff2ddd59da0127728f9609aefd4cafe, height=102, index=1)
2026-09-02T05:55:55Z UpdateTip: new best=19efd37e2db2c03e082c162d9e18904830f39e0d5ac12b0b3e26bbc5aca6eda1 height=103 version=0x20000000 log2_work=7.700440 tx=105 date='2026-09-02T05:56:13Z' progress=1.000000 cache=0.3MiB(105txo)
2026-09-02T05:55:55Z UpdateTip: new best=5bede6868322fc88c6c686131012b22b4a9cf02198b46f5982f8ae96763a97c9 height=104 version=0x20000000 log2_work=7.714246 tx=106 date='2026-09-02T05:56:14Z' progress=1.000000 cache=0.3MiB(106txo)
2026-09-02T05:55:55Z UpdateTip: new best=52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216 height=105 version=0x20000000 log2_work=7.727920 tx=107 date='2026-09-02T05:56:14Z' progress=1.000000 cache=0.3MiB(107txo)
2026-09-02T05:55:55Z [goldatom-demo] AddToWallet f1624bb71a62c1c661d940739429a5a3a8f0415cb8390f4f6386a09a9a83506c new InMempool
2026-09-02T05:55:55Z UpdateTip: new best=364fe86cd01edd84e4171d9dd041179ee2f7287cf9ecbe9dca489cd5f722da46 height=106 version=0x20000000 log2_work=7.741467 tx=109 date='2026-09-02T05:56:14Z' progress=1.000000 cache=0.3MiB(108txo)
2026-09-02T05:55:55Z [goldatom-demo] AddToWallet f1624bb71a62c1c661d940739429a5a3a8f0415cb8390f4f6386a09a9a83506c update Confirmed (block=364fe86cd01edd84e4171d9dd041179ee2f7287cf9ecbe9dca489cd5f722da46, height=106, index=1)
2026-09-02T05:55:55Z UpdateTip: new best=21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950 height=107 version=0x20000000 log2_work=7.754888 tx=110 date='2026-09-02T05:56:14Z' progress=1.000000 cache=0.3MiB(109txo)
2026-09-02T06:03:05Z Bitcoin Core version v31.99.0-031175197f1b (release build)
2026-09-02T06:03:05Z Using data directory /mnt/data/goldatom-regtest-node/regtest
2026-09-02T06:03:05Z Using at most 200 automatic connections (16384 file descriptors available)
2026-09-02T06:03:33Z UpdateTip: new best=364fe86cd01edd84e4171d9dd041179ee2f7287cf9ecbe9dca489cd5f722da46 height=106 version=0x20000000 log2_work=7.741467 tx=109 date='2026-09-02T05:56:14Z' progress=0.994526 cache=0.3MiB(2txo)
2026-09-02T06:03:33Z UpdateTip: new best=52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216 height=105 version=0x20000000 log2_work=7.727920 tx=107 date='2026-09-02T05:56:14Z' progress=0.994424 cache=0.3MiB(4txo)
2026-09-02T06:03:33Z UpdateTip: new best=5bede6868322fc88c6c686131012b22b4a9cf02198b46f5982f8ae96763a97c9 height=104 version=0x20000000 log2_work=7.714246 tx=106 date='2026-09-02T05:56:14Z' progress=0.994371 cache=0.3MiB(5txo)
2026-09-02T06:03:33Z InvalidChainFound: invalid block=52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216 height=105 log2_work=7.727920 date=2026-09-02T05:56:14Z
2026-09-02T06:03:33Z InvalidChainFound: current best=5bede6868322fc88c6c686131012b22b4a9cf02198b46f5982f8ae96763a97c9 height=104 log2_work=7.714246 date=2026-09-02T05:56:14Z
2026-09-02T06:03:34Z UpdateTip: new best=52a4334064cf581c8af3f10cf496b8bcac6db638e294c107916041d60fc24216 height=105 version=0x20000000 log2_work=7.727920 tx=107 date='2026-09-02T05:56:14Z' progress=0.988909 cache=0.3MiB(5txo)
2026-09-02T06:03:34Z UpdateTip: new best=364fe86cd01edd84e4171d9dd041179ee2f7287cf9ecbe9dca489cd5f722da46 height=106 version=0x20000000 log2_work=7.741467 tx=109 date='2026-09-02T05:56:14Z' progress=0.994526 cache=0.3MiB(4txo)
2026-09-02T06:03:34Z UpdateTip: new best=21629b8af14352991e77d3d7fcaecbab528f03b26667e593daa88b0776b70950 height=107 version=0x20000000 log2_work=7.754888 tx=110 date='2026-09-02T05:56:14Z' progress=1.000000 cache=0.3MiB(4txo)
```

## 8. Deterministic local validation and issuance runner

```text
$ python3 -m compileall -q goldatom scripts simulation tests
EXIT_STATUS=0

$ python3 -m unittest discover -s tests -v
test_censorship_bound (test_economics.EconomicsTests.test_censorship_bound) ... ok
test_equal_producers (test_economics.EconomicsTests.test_equal_producers) ... ok
test_gate_stats (test_economics.EconomicsTests.test_gate_stats) ... ok
test_hardware_advantage_share (test_economics.EconomicsTests.test_hardware_advantage_share) ... ok
test_invalid_inputs (test_economics.EconomicsTests.test_invalid_inputs) ... ok
test_target_granularity (test_economics.EconomicsTests.test_target_granularity) ... ok
test_variant_amplification (test_economics.EconomicsTests.test_variant_amplification) ... ok
test_withholding_threshold (test_economics.EconomicsTests.test_withholding_threshold) ... ok
test_broken_transfer_ancestry_is_rejected (test_protocol.GoldAtomProtocolTests.test_broken_transfer_ancestry_is_rejected) ... ok
test_challenge_reorg_is_rejected (test_protocol.GoldAtomProtocolTests.test_challenge_reorg_is_rejected) ... ok
test_claim_proof_cannot_be_relabelled (test_protocol.GoldAtomProtocolTests.test_claim_proof_cannot_be_relabelled) ... ok
test_current_title_value_mismatch_is_rejected (test_protocol.GoldAtomProtocolTests.test_current_title_value_mismatch_is_rejected) ... ok
test_duplicate_json_key_is_rejected (test_protocol.GoldAtomProtocolTests.test_duplicate_json_key_is_rejected) ... ok
test_eighty_byte_work_header_and_vector (test_protocol.GoldAtomProtocolTests.test_eighty_byte_work_header_and_vector) ... ok
test_genesis_vector_is_valid (test_protocol.GoldAtomProtocolTests.test_genesis_vector_is_valid) ... ok
test_mint_outside_window_is_rejected (test_protocol.GoldAtomProtocolTests.test_mint_outside_window_is_rejected) ... ok
test_missing_current_title_is_rejected (test_protocol.GoldAtomProtocolTests.test_missing_current_title_is_rejected) ... ok
test_nested_record_must_be_json_object (test_protocol.GoldAtomProtocolTests.test_nested_record_must_be_json_object) ... ok
test_noncanonical_hex_whitespace_is_rejected (test_protocol.GoldAtomProtocolTests.test_noncanonical_hex_whitespace_is_rejected) ... ok
test_second_mint_marker_is_rejected (test_protocol.GoldAtomProtocolTests.test_second_mint_marker_is_rejected) ... ok
test_tampered_nonce_is_rejected (test_protocol.GoldAtomProtocolTests.test_tampered_nonce_is_rejected) ... ok
test_tampered_work_hash_is_rejected (test_protocol.GoldAtomProtocolTests.test_tampered_work_hash_is_rejected) ... ok
test_target_above_profile_maximum_is_rejected_first (test_protocol.GoldAtomProtocolTests.test_target_above_profile_maximum_is_rejected_first) ... ok
test_unconfirmed_current_title_is_rejected (test_protocol.GoldAtomProtocolTests.test_unconfirmed_current_title_is_rejected) ... ok
test_unsupported_title_script_is_rejected (test_protocol.GoldAtomProtocolTests.test_unsupported_title_script_is_rejected) ... ok
test_valid_title_transfer (test_protocol.GoldAtomProtocolTests.test_valid_title_transfer) ... ok

----------------------------------------------------------------------
Ran 26 tests in 0.004s

OK
EXIT_STATUS=0

$ python3 scripts/generate_test_vectors.py
Regenerated examples/genesis.goldatom.json
Regenerated examples/transferred.goldatom.json
Regenerated TEST-VECTORS.md
EXIT_STATUS=0

$ python3 simulation/issuance_regimes.py
Wrote simulation/results/issuance-regimes.json
Wrote ISSUANCE-SIMULATION-0.md
EXIT_STATUS=0
```

## 9. Wheel build and clean-environment installation

```text
$ python3 -m pip wheel --no-deps --no-build-isolation -w /mnt/data/goldatom-release-0.0.2 .
WARNING: The directory '/home/oai/.cache/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Processing /mnt/data/goldatom-0
  Preparing metadata (pyproject.toml): started
  Preparing metadata (pyproject.toml): finished with status 'done'
Building wheels for collected packages: goldatom
  Building wheel for goldatom (pyproject.toml): started
  Building wheel for goldatom (pyproject.toml): finished with status 'done'
  Created wheel for goldatom: filename=goldatom-0.0.2-py3-none-any.whl size=29023 sha256=e3e914989fd98b87cf7e5e5b25b643b91a7668c9959b641b4e1dcd1e4928ba9e
  Stored in directory: /tmp/pip-ephem-wheel-cache-spxxko0n/wheels/57/ab/40/7fdfdc02cd19b35e9552b94ff8d254f0d742c9874d6b00aa42
Successfully built goldatom
EXIT_STATUS=0

$ python3 -m venv /mnt/data/goldatom-wheel-test-venv
EXIT_STATUS=0

$ pip install goldatom-0.0.2-py3-none-any.whl
WARNING: The directory '/home/oai/.cache/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Processing /mnt/data/goldatom-release-0.0.2/goldatom-0.0.2-py3-none-any.whl
Installing collected packages: goldatom
Successfully installed goldatom-0.0.2
EXIT_STATUS=0

$ goldatom simulate --json
{
  "as_of_tip_hash": "df1ed9dc41a0c72dad35cf3f7ae999e7244a6a90326d218c97c82f37b977c504",
  "as_of_tip_height": 105,
  "atom_id": "164b8c2fd964c6a5deed2f16264bedfe2e20ee777c677c250d3f0673a5957417",
  "burial_blocks": 1,
  "burial_chainwork": "10000",
  "challenge_height": 103,
  "claim_height": 100,
  "current_title_outpoint": {
    "txid": "0c2dc53fb853bd864b8b1617ee5da1644b213a64955d16dae38102c6fc71d886",
    "vout": 0
  },
  "expected_local_hashes": 16,
  "expected_local_work_log2": 4.0,
  "mint_height": 104,
  "profile": "goldatom-sim-v0",
  "target_hex": "0fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
  "title_transfers": 0,
  "valid": true
}
EXIT_STATUS=0

$ python -c import version/economics
goldatom.__version__ = 0.0.2
P(at least one gate | p=1/4096, M=10000) = 0.9129875721552416
EXIT_STATUS=0
```

## 10. Issuance stress-test result

The economic runner compared work-weighted bullion, a 64-winner sealed epoch auction, and proof-intersection gating at base probability `1/4096`.

Key measured/model-derived outputs:

```text
100 producers, one 100× hardware advantage:
  advantaged expected share       50.251%
  effective producer count         3.92

100 producers, one 10,000× advantage:
  advantaged expected share       99.020%

10,000 claimant-controlled gate variants:
  base probability                 0.02441%
  effective probability           91.29876%
  amplification                    3,739.60×

1,000,000 canonical epochs at p=1/4096:
  expected open gates             244.141
  coefficient of variation         6.399%
```

The adverse conclusion is not that proof intersections are useless. It is narrower and more important:

> A canonical proof intersection can schedule a scarce opportunity, but cannot by itself establish exclusive ownership or atom-specific cost. If claimant-controlled variants enter the relation, the gate becomes a grind.

The next experimental branch is therefore a **canonical vein auction**:

```text
claim-independent external proof relation opens a rare epoch
                          +
prior-committed local work allocates exactly one title
                          +
Bitcoin publishes and buries the title
```

Work-weighted bullion remains the control branch because it is the cleanest implementation of exclusive assayable work, despite its compute-elastic supply.

## 11. Clean shutdown

```text
Bitcoin Core stopping
RPC unavailable after stop: yes
```

## 12. What this run proves—and what it does not

### Established under the recorded conditions

- GoldAtom/0's claim, challenge, local proof, mint, burial, serialization, and current-title checks execute together against a real Bitcoin Core node.
- A copied or altered proof does not survive deterministic recomputation.
- Atom validity follows the active Bitcoin chain and reverses with a reorganization.
- The object-layer implementation did not require a new consensus chain.

### Not established

- Compatibility with the signed Bitcoin Core 31.1 release binary or with macOS.
- Security at economic work targets; the regtest profile intentionally expects only 16 hashes.
- Mainnet safety, monetary value, price support, fair launch, privacy, or legal status.
- Resistance to ASIC concentration or hidden work-function optimization.
- A sound aggregate issuance rule.
- Independent cryptographic or economic audit.

## 13. Evidence index

```text
examples/live-regtest-2026-09-02.goldatom.json
validation/live-regtest/00-provenance.json
validation/live-regtest/01-regtest-demo.log
validation/live-regtest/02-independent-verify.json
validation/live-regtest/03-node-chain-info.json
validation/live-regtest/04-node-network-info.json
validation/live-regtest/05-node-debug-excerpt.log
validation/live-regtest/06-node-stop.log
validation/live-negative/
validation/05-final-local-validation.log
ISSUANCE-SIMULATION-0.md
simulation/results/issuance-regimes.json
```
