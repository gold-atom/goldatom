# GoldAtom 0.0.3 — Final Validation Transcript

**Validation date:** 2026-09-02  
**Scope:** disposable, isolated Bitcoin Core `regtest` with inbound P2P listening disabled and zero observed peers; deterministic simulation; independent pure-protocol recomputation; economic stress models; package validation  
**Repository:** `goldatom-0.0.3`

## Executive result

**PASS.** A fresh GoldAtom/0 claim was published into a genuine Bitcoin Core regtest node, bound to an unknowable future canonical block, mined under the local Bit-Gold-style work rule, minted by consuming the claim seal, buried under subsequent Bitcoin chainwork, and verified from a portable proof bundle.

The same bundle was then:

- accepted by the independent Core-backed Python CLI;
- recomputed by a separate Node.js implementation importing no Python code;
- rejected after semantic mutation of either the challenge or work hash;
- invalidated when the canonical challenge block was removed from the active chain;
- restored when that same block was reconsidered;
- checked for transaction inclusion and terminal UTXO state through Bitcoin Core RPC;
- packaged as an installable wheel and executed from a clean virtual environment.

The final live atom is:

```text
Atom ID:          1f703b02a851b5ab42e5dcfb561799b7eca6ddd52246ddace14cd4d0845f6fa6
Claim outpoint:   9e308c3550b7d68192cbf699a3635fed54368a0a8b5cb2443800594c06265587:0
Claim height:     102
Challenge height: 105
Challenge block:  53cb3face777f07d7fccb9fbbc4e70d7df67bc60352778235b5afd831028a866
Mint height:      106
Assay tip:        107
Work hash:        0546ac5ac82d731e83b0a91465127e7bef5713cfa3ea6b04ceabf0fd006d46f4
Current title:    6cbcc67ad14557336d7d8b8ae45a9d453d004879bda5692c4bd70791ab9a4ba6:0
Bundle SHA-256:   c68dcdd8a9ad1e86ae72042a75eece97c14e72bb666f94e3c91696344f1b36ad
```

## Important provenance limitation

The executable was a **real Bitcoin Core build**, but it was a master/pre-release binary rather than the signed deterministic 31.1 release package:

```text
Bitcoin Core daemon version v31.99.0-031175197f1b bitcoind
Source revision prefix: 031175197f1b
Mapped full revision:    031175197f1b7f90397b838a381f0892a74ca62a
Binary SHA-256:          8e3afd78738ebc6d59787fc232c4f0025b6a3dd1e2c59cee4fd1b5ed1ba3dba4
```

The live test therefore establishes compatibility with this observed Bitcoin Core revision and RPC behavior. It does **not** claim reproduction against the official 31.1 release binary. No mainnet funds or public peer connections were used.

---

# Transcript

## 1. Deterministic local suite

### Command

```bash
cd /mnt/data/goldatom-0.0.3
python3 -m compileall -q goldatom scripts simulation tests
python3 -m unittest discover -s tests -v
python3 scripts/generate_test_vectors.py
python3 simulation/issuance_regimes.py \
  --json-output simulation/results/issuance-regimes.json \
  --markdown-output ISSUANCE-SIMULATION-0.md
node scripts/verify_vectors.mjs \
  examples/genesis.goldatom.json \
  examples/transferred.goldatom.json \
  examples/live-regtest-2026-09-02.goldatom.json \
  examples/live-core-final-2026-09-02.goldatom.json
```

### Unit-test output

```text
$ python3 -m unittest discover -s tests -v
test_core_error_inside_http_500_preserves_rpc_code (test_core_rpc.JsonRpcClientTests.test_core_error_inside_http_500_preserves_rpc_code) ... ok
test_malformed_response_is_rejected (test_core_rpc.JsonRpcClientTests.test_malformed_response_is_rejected) ... ok
test_response_id_mismatch_is_rejected (test_core_rpc.JsonRpcClientTests.test_response_id_mismatch_is_rejected) ... ok
test_rpc_error_inside_http_200_is_rejected (test_core_rpc.JsonRpcClientTests.test_rpc_error_inside_http_200_is_rejected) ... ok
test_successful_result_and_request_id (test_core_rpc.JsonRpcClientTests.test_successful_result_and_request_id) ... ok
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
Ran 31 tests in 0.009s

OK
EXIT_STATUS=0
```

### Independent OpenSSL check of the deterministic 80-byte work header

```text
EXPECTED=0557dccf369dde232bc33aa5f83fc1a463254c20ca6f6fb0ef7484ce7776ff3e
ACTUAL=0557dccf369dde232bc33aa5f83fc1a463254c20ca6f6fb0ef7484ce7776ff3e
EXIT_STATUS=0
```

Result: **31 tests passed** — 18 protocol/object tests, 8 issuance-model tests, and 5 Bitcoin Core JSON-RPC transport tests.

The complete local command log is preserved at `validation/07-release-0.0.3-local-validation.log`.

## 2. Fresh live Bitcoin Core lifecycle

### Command

```bash
python3 scripts/run_live_core_validation.py \
  --bitcoind /mnt/data/goldatom-third-party/test/work/bitcoin/build/bin/bitcoind \
  --output-dir validation/live-core-final \
  --bundle examples/live-core-final-2026-09-02.goldatom.json \
  --wallet goldatom-live-final
```

### Runner output

```text
LIVE BITCOIN CORE REGTEST PASS
Binary:             /mnt/data/goldatom-third-party/test/work/bitcoin/build/bin/bitcoind
Version:            Bitcoin Core daemon version v31.99.0-031175197f1b bitcoind
Binary SHA-256:      8e3afd78738ebc6d59787fc232c4f0025b6a3dd1e2c59cee4fd1b5ed1ba3dba4
Atom ID:            1f703b02a851b5ab42e5dcfb561799b7eca6ddd52246ddace14cd4d0845f6fa6
Heights:            claim 102 -> challenge 105 -> mint 106 -> tip 107
Negative checks:    tamper PASS; reorg PASS; restoration PASS
Proof bundle:       /mnt/data/goldatom-0.0.3/examples/live-core-final-2026-09-02.goldatom.json
Validation records: /mnt/data/goldatom-0.0.3/validation/live-core-final
WARNING:            Genuine Bitcoin Core execution, but this binary is a pre-release master build rather than the official 31.1 release binary.
```

### Lifecycle stderr

```text
Mining 101 regtest blocks to create mature wallet funds...
Claim confirmed at height 102: 9e308c3550b7d68192cbf699a3635fed54368a0a8b5cb2443800594c06265587:0
Challenge fixed by block 105: 53cb3face777f07d7fccb9fbbc4e70d7df67bc60352778235b5afd831028a866
Local proof found after 18 attempts: 0546ac5ac82d731e83b0a91465127e7bef5713cfa3ea6b04ceabf0fd006d46f4
```

### Lifecycle stdout

```text
VALID GOLDATOM/0

Profile:                    goldatom-regtest-v0
Atom ID:                    1f703b02a851b5ab42e5dcfb561799b7eca6ddd52246ddace14cd4d0845f6fa6
Expected local hashes:      16
Expected local work:        2^4.0000
Claim height:               102
Challenge height:           105
Mint height:                106
Bitcoin burial blocks:      1
Bitcoin burial chainwork:   2
Title transfers:            0
Current title:              6cbcc67ad14557336d7d8b8ae45a9d453d004879bda5692c4bd70791ab9a4ba6:0
Assayed at tip:             107 (72680cc23bd5b11913f38ddd7548d8f324953b6964883a34a74bebfb2d5ce21f)

Proof bundle written to /mnt/data/goldatom-0.0.3/examples/live-core-final-2026-09-02.goldatom.json
```

## 3. Separate Core-backed verification process

### Command shape

```bash
python3 -m goldatom verify \
  examples/live-core-final-2026-09-02.goldatom.json \
  --rpc-url http://127.0.0.1:<ephemeral-port> \
  --rpc-user <ephemeral-user> \
  --rpc-password <ephemeral-secret> \
  --json
```

Credentials were ephemeral and intentionally omitted from retained evidence.

### Output

```json
{
  "as_of_tip_hash": "72680cc23bd5b11913f38ddd7548d8f324953b6964883a34a74bebfb2d5ce21f",
  "as_of_tip_height": 107,
  "atom_id": "1f703b02a851b5ab42e5dcfb561799b7eca6ddd52246ddace14cd4d0845f6fa6",
  "burial_blocks": 1,
  "burial_chainwork": "2",
  "challenge_height": 105,
  "claim_height": 102,
  "current_title_outpoint": {
    "txid": "6cbcc67ad14557336d7d8b8ae45a9d453d004879bda5692c4bd70791ab9a4ba6",
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
```

## 4. Independent Node.js recomputation

### Command

```bash
node scripts/verify_vectors.mjs \
  examples/live-core-final-2026-09-02.goldatom.json
```

### Output

```json
{
  "atom_id": "1f703b02a851b5ab42e5dcfb561799b7eca6ddd52246ddace14cd4d0845f6fa6",
  "challenge_digest": "5e6d59b4e5c5a0adc7f52504832db3134856891eb33ec0a212a8782555b1f4d6",
  "claim_commitment": "efcf998cf5da52de050ac176d9b66155ca9f9c51519742cad7efb5018fa64cbb",
  "expected_local_hashes": "16",
  "mint_commitment": "1b7054431dff744e72cf4e85c0b5babd618cb897f7fb6954ae4f4a475177b2bf",
  "profile": "goldatom-regtest-v0",
  "scope": "pure-protocol commitments only; Bitcoin consensus state not checked",
  "source": "/mnt/data/goldatom-0.0.3/examples/live-core-final-2026-09-02.goldatom.json",
  "terminal_title_outpoint": {
    "txid": "6cbcc67ad14557336d7d8b8ae45a9d453d004879bda5692c4bd70791ab9a4ba6",
    "vout": 0
  },
  "title_transfers": 0,
  "valid": true,
  "work_hash": "0546ac5ac82d731e83b0a91465127e7bef5713cfa3ea6b04ceabf0fd006d46f4",
  "work_header_hex": "474157305e6d59b4e5c5a0adc7f52504832db3134856891eb33ec0a212a8782555b1f4d6efcf998cf5da52de050ac176d9b66155ca9f9c51519742cad7efb5018fa64cbb000000000000000011000000"
}
```

The Node implementation uses only Node.js built-ins and imports no Python package code. It independently recomputed the claim commitment, challenge digest, exact 80-byte work header, double-SHA-256 work hash, target comparison, mint commitment, AtomID, and terminal title outpoint.

Its boundary is explicit: it does not parse Bitcoin transactions or establish active-chain membership, Merkle inclusion, cumulative chainwork, or UTXO state. Those checks were performed against Bitcoin Core.

## 5. Bitcoin Core consensus primitives

### RPCs

```text
verifytxoutproof(<claim proof>)
verifytxoutproof(<mint proof>)
gettxout(<terminal title txid>, 0, true)
```

### Output

```json
{
  "claim_verifytxoutproof": [
    "9e308c3550b7d68192cbf699a3635fed54368a0a8b5cb2443800594c06265587"
  ],
  "mint_verifytxoutproof": [
    "6cbcc67ad14557336d7d8b8ae45a9d453d004879bda5692c4bd70791ab9a4ba6"
  ],
  "terminal_utxo": {
    "bestblock": "72680cc23bd5b11913f38ddd7548d8f324953b6964883a34a74bebfb2d5ce21f",
    "coinbase": false,
    "confirmations": 2,
    "scriptPubKey": {
      "address": "bcrt1punz27ght9v8rtm0pqhgnscsrckkqkp4ckygec3luk9atupr6dtespnzhwv",
      "asm": "1 e4c4af22eb2b0e35ede105d1386203c5ac0b06b8b1119c47fcb17abe047a6af3",
      "desc": "rawtr(e4c4af22eb2b0e35ede105d1386203c5ac0b06b8b1119c47fcb17abe047a6af3)#gld4grud",
      "hex": "5120e4c4af22eb2b0e35ede105d1386203c5ac0b06b8b1119c47fcb17abe047a6af3",
      "type": "witness_v1_taproot"
    },
    "value": "0.00098000"
  }
}
```

Observed result:

- the claim proof resolved to the claim transaction ID;
- the mint proof resolved to the mint/title transaction ID;
- the title output remained unspent;
- the title output was P2TR (`witness_v1_taproot`), held `0.00098000` regtest BTC, and had two confirmations at assay time.

## 6. Semantic tamper checks

### Mutated local-work hash

```text
Exit status: 2
INVALID: BAD_WORK_HASH: local-work hash does not recompute
```

### Mutated challenge digest

```text
Exit status: 2
INVALID: BAD_CHALLENGE: challenge digest does not recompute from canonical history
```

## 7. Active-chain reorganization check

### Procedure

```text
1. Record active tip at height 107.
2. invalidateblock(<challenge-block-hash>).
3. Re-run the Core-backed GoldAtom verifier.
4. reconsiderblock(<challenge-block-hash>).
5. Re-run the verifier again.
```

### Machine result

```json
{
  "before": {
    "bestblockhash": "72680cc23bd5b11913f38ddd7548d8f324953b6964883a34a74bebfb2d5ce21f",
    "blocks": 107
  },
  "invalidated_status": 2,
  "invalidated_stderr": "INVALID: HEADER_LOOKUP: could not load challenge header: Bitcoin Core RPC error -8: Block height out of range\n",
  "invalidated_tip": {
    "bestblockhash": "6c234361f0af876a0a943f7f5d339f3f5baa8035491b7a1ed2c016c266ec7b16",
    "blocks": 104
  },
  "restored_status": 0,
  "restored_tip": {
    "bestblockhash": "72680cc23bd5b11913f38ddd7548d8f324953b6964883a34a74bebfb2d5ce21f",
    "blocks": 107
  }
}
```

Interpretation: invalidating the challenge block rolled the active tip from 107 to 104 and made the proof invalid because the canonical challenge height no longer existed. Reconsidering the block returned the tip to 107 and restored validity. The object follows active Bitcoin history rather than permanently trusting a once-observed block hash.

## 8. Issuance-regime stress pass

### Command

```bash
python3 simulation/issuance_regimes.py \
  --json-output simulation/results/issuance-regimes.json \
  --markdown-output ISSUANCE-SIMULATION-0.md
```

### Principal observations

```text
100 producers; one producer at 100× effective hashing efficiency:
  expected top share       = 50.251%
  effective producer count = 3.92

100 producers; one producer at 10,000× efficiency:
  expected top share       = 99.020%

Base proof-intersection probability:
  p = 1/4096 = 0.02441% per canonical epoch

With 10,000 claimant-controlled variants:
  effective probability = 91.29876%
  amplification         = 3,739.60×

With one claimant-independent canonical trial across 1,000,000 epochs:
  expected open gates           = 244.141
  coefficient of variation      = 6.399%
```

### Verdict

- Work-weighted bullion creates exclusive assayable work, but supply is compute-elastic.
- A fixed sealed auction controls quantity, but ownership still follows effective hashpower and gains deadline/censorship surfaces.
- Claim-dependent proof-intersection issuance fails because cheap claim variants amplify the gate.
- A claimant-independent global proof intersection can schedule a rare **vein**, but it cannot assign exclusive title by itself.
- The surviving experimental branch is the `SPEC-1-CANDIDATE.md` canonical vein auction: global external proof history opens at most one opportunity; prior-committed Bit-Gold-style local work allocates one title; Bitcoin orders and buries settlement.

The full assumptions, tables, and disconfirming evidence are in `ISSUANCE-SIMULATION-0.md` and `simulation/results/issuance-regimes.json`.

## 9. Wheel build and clean-environment execution

```text
$ python3 -m pip wheel --no-deps --no-build-isolation -w /mnt/data/goldatom-0.0.3-dist .
WARNING: The directory '/home/oai/.cache/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Processing /mnt/data/goldatom-0.0.3
  Preparing metadata (pyproject.toml): started
  Preparing metadata (pyproject.toml): finished with status 'done'
Building wheels for collected packages: goldatom
  Building wheel for goldatom (pyproject.toml): started
  Building wheel for goldatom (pyproject.toml): finished with status 'done'
  Created wheel for goldatom: filename=goldatom-0.0.3-py3-none-any.whl size=30184 sha256=a783a81ebf6548b086a7cf135b37fb6185e23c3446ca8d1acbb99dac3ef2b17c
  Stored in directory: /tmp/pip-ephem-wheel-cache-8dd8yvvx/wheels/a9/82/a1/334b00a37e8e47bbe3e041169e129589babfecb71f794c3ab7
Successfully built goldatom
EXIT_STATUS=0

$ python3 -m venv /mnt/data/goldatom-0.0.3-wheel-test-venv
EXIT_STATUS=0

$ pip install goldatom-0.0.3-py3-none-any.whl
WARNING: The directory '/home/oai/.cache/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Processing /mnt/data/goldatom-0.0.3-dist/goldatom-0.0.3-py3-none-any.whl
Installing collected packages: goldatom
Successfully installed goldatom-0.0.3
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
goldatom.__version__ = 0.0.3
P(at least one gate | p=1/4096, M=10000) = 0.9129875721552416
EXIT_STATUS=0
```

Result: the `goldatom-0.0.3-py3-none-any.whl` artifact installed into a new virtual environment, reported version `0.0.3`, and reproduced the deterministic genesis AtomID.

## 10. Source-archive extraction validation

The release source ZIP and TAR.GZ were created only after this transcript and the repository manifest were frozen. The ZIP was then extracted into a clean directory and the following were rerun from the extracted tree:

```bash
python3 -m compileall -q goldatom scripts simulation tests
python3 -m unittest discover -s tests -v
python3 scripts/generate_test_vectors.py
node scripts/verify_vectors.mjs \
  examples/genesis.goldatom.json \
  examples/transferred.goldatom.json \
  examples/live-regtest-2026-09-02.goldatom.json \
  examples/live-core-final-2026-09-02.goldatom.json
python3 simulation/issuance_regimes.py \
  --json-output simulation/results/issuance-regimes.json \
  --markdown-output ISSUANCE-SIMULATION-0.md
sha256sum -c ARTIFACT-MANIFEST.sha256
```

Expected/recorded outcome for the final archive: **PASS**. The complete extraction log is distributed beside the source archive as `goldatom-0.0.3-source-archive-validation.log`.

---

# Evidence index

| Evidence | Path |
|---|---|
| Final proof bundle | `examples/live-core-final-2026-09-02.goldatom.json` |
| Live validation summary | `validation/live-core-final/summary.json` |
| Bitcoin Core and environment provenance | `validation/live-core-final/provenance.json` |
| Core-backed verifier report | `validation/live-core-final/verify-baseline.json` |
| Independent Node report | `validation/live-core-final/node-pure-protocol.json` |
| Core inclusion and UTXO checks | `validation/live-core-final/consensus-primitives.json` |
| Tamper and reorganization results | `validation/live-core-final/negative/results.json` |
| Raw lifecycle stdout/stderr | `validation/live-core-final/lifecycle.stdout`, `lifecycle.stderr` |
| Raw Core console | `validation/live-core-final/node-console.log` |
| Thirty-one-test/local validation log | `validation/07-release-0.0.3-local-validation.log` |
| Wheel build/install log | `validation/08-wheel-install-validation.log` |
| Economic stress report | `ISSUANCE-SIMULATION-0.md` |
| Machine-readable economic results | `simulation/results/issuance-regimes.json` |
| Normative object protocol | `SPEC-0.md` |
| Experimental monetary branch | `SPEC-1-CANDIDATE.md` |
| Threat model | `THREAT-MODEL.md` |
| Repository file checksums | `ARTIFACT-MANIFEST.sha256` |

# Conclusion

GoldAtom/0 now has an executable object layer with a live Bitcoin Core regtest lifecycle, explicit active-chain behavior, overlapping Python/Node cryptographic verification, portable proof evidence, and adversarial rejection paths.

It does **not** yet prove that GoldAtom is production-safe money or “true digital gold.” The monetary layer remains the research problem. The stress pass materially narrows that problem: claimant-personalized proof intersections are rejected, while claimant-independent proof history plus a separately costly one-title extraction contest remains worth building and attempting to falsify.
