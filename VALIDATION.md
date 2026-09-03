# GoldAtom/0 Validation Record

**Release:** `0.0.3`  
**Validation date:** 2026-09-02  
**Executed environment:** Linux x86_64; CPython 3.13.5; Node.js 22.16.0  
**Scope:** simulation and disposable Bitcoin Core `regtest` only

## Result

The complete lifecycle was executed successfully against a fresh, isolated Bitcoin Core regtest node with inbound P2P listening disabled and zero observed peers:

```text
claim → future canonical challenge → local SHA-256d work
      → mint → Bitcoin burial → Core-backed verification
      → semantic tamper rejection → reversible reorganization
```

Release `0.0.3` also recomputed the portable cryptographic layer in an independent Node.js implementation that imports no Python code.

The final isolated validation atom is preserved at `examples/live-core-final-2026-09-02.goldatom.json`.

```text
Atom ID:          1f703b02a851b5ab42e5dcfb561799b7eca6ddd52246ddace14cd4d0845f6fa6
Claim outpoint:   9e308c3550b7d68192cbf699a3635fed54368a0a8b5cb2443800594c06265587:0
Claim height:     102
Challenge height: 105
Mint height:      106
Assay tip:        107
Work attempts:    18
Work hash:        0546ac5ac82d731e83b0a91465127e7bef5713cfa3ea6b04ceabf0fd006d46f4
Current title:    6cbcc67ad14557336d7d8b8ae45a9d453d004879bda5692c4bd70791ab9a4ba6:0
Bundle SHA-256:   c68dcdd8a9ad1e86ae72042a75eece97c14e72bb666f94e3c91696344f1b36ad
```

The full release command/output record is in `FINAL-VALIDATION-TRANSCRIPT.md`. Machine-readable evidence is under `validation/live-core-final/`.

## Bitcoin Core provenance

The live run used:

```text
Bitcoin Core daemon version v31.99.0-031175197f1b bitcoind
Source revision prefix: 031175197f1b
Full recorded source commit: 031175197f1b7f90397b838a381f0892a74ca62a
Binary SHA-256: 8e3afd78738ebc6d59787fc232c4f0025b6a3dd1e2c59cee4fd1b5ed1ba3dba4
```

This is a Bitcoin Core master/pre-release build, not the signed deterministic Bitcoin Core 31.1 release package. The official archive could not be downloaded into this environment. The run therefore establishes compatibility with the identified source revision and observed RPC behavior, but does **not** close the separate requirement to reproduce against the official 31.1 binary.

The earlier preserved live run remains under `validation/live-regtest/` and produced a different valid regtest atom, as expected from fresh wallet keys and future block hashes.

## Final live positive checks

- Started a fresh temporary regtest datadir with inbound P2P listening disabled, zero observed peers, and `txindex=1`.
- Created a descriptor wallet and mined 101 blocks for mature disposable funds.
- Published the claim transaction and confirmed it at height 102.
- Fixed the challenge from the canonical block at height 105.
- Found valid local work after 18 SHA-256d attempts under the deliberately trivial regtest target.
- Spent the claim seal into one P2TR title output and one matching `GA0M` commitment at height 106.
- Mined one post-mint burial block, producing a tip at height 107.
- Verified claim and mint inclusion using Bitcoin Core `verifytxoutproof`.
- Confirmed the terminal title through `gettxout`: P2TR, `0.00098000` BTC, two confirmations.
- Re-read the serialized proof bundle in a separate Python CLI process and returned `valid: true`.
- Recomputed claim, challenge, 80-byte work header, work hash, mint commitment, AtomID, and terminal title outpoint in independent Node.js code and obtained the same AtomID.
- Stopped the temporary node and deleted the disposable datadir.

## Final live negative checks

All checks used the real Core-backed verifier.

| Test | Expected | Observed |
|---|---|---|
| Alter final nibble of `work_hash_hex` | Reject | Exit 2, `BAD_WORK_HASH` |
| Alter final nibble of `challenge_digest_hex` | Reject | Exit 2, `BAD_CHALLENGE` |
| Invalidate canonical challenge block | Reject atom | Tip rolled 107 → 104; exit 2, `HEADER_LOOKUP` with Core RPC code `-8` |
| Reconsider same challenge block | Restore atom | Tip returned 104 → 107; verifier returned valid |

This demonstrates that validity follows active Bitcoin history rather than merely accepting a once-observed block hash.

## Independent implementation boundary

`scripts/verify_vectors.mjs` is intentionally independent of the Python package and uses only Node.js built-ins. It verifies the **portable pure-protocol layer**:

- canonical profile constants;
- claim commitment;
- challenge derivation;
- exact 80-byte work-header layout;
- double-SHA-256 work hash and target comparison;
- mint commitment;
- AtomID;
- title-transfer commitment ancestry.

It cannot verify data that is not self-contained in the proof bundle: Bitcoin transaction decoding, transaction-marker counts, Merkle inclusion, active-chain membership, cumulative chainwork, or current UTXO state. Those remain Core-backed checks. The two implementations therefore overlap on the cryptographic boundary without falsely claiming two independent full-node implementations.

## Deterministic suite

Executed successfully:

- Python source compilation.
- Thirty-one unit tests:
  - eighteen object/protocol tests;
  - eight issuance-model tests;
  - five JSON-RPC transport/envelope tests.
- Deterministic genesis and one-transfer vector regeneration.
- Independent Node.js recomputation of the genesis, transfer, preserved live, and final live bundles.
- Independent OpenSSL double-SHA-256 verification of the fixed 80-byte genesis work header.
- Deterministic issuance stress runner.
- Wheel construction, installation into a fresh virtual environment, and installed-command execution.
- Source ZIP and TAR.GZ extraction followed by compile, test, vector, Node, and simulation reruns.

## Issuance stress pass

`simulation/issuance_regimes.py` compares:

1. work-weighted Bit-Gold-style bullion;
2. a 64-winner sealed epoch auction;
3. proof-intersection gating with base opportunity probability `1/4096`.

The principal disconfirming results are:

- fixed-target work issuance is linearly elastic to effective hashing;
- in the 100-producer toy model, one producer with a 100× efficiency advantage receives about 50.25% of expected output;
- a fixed auction controls quantity but not long-run hashpower concentration;
- 10,000 claimant-controlled gate variants raise a `1/4096` opportunity probability to about 91.30%;
- a claimant-independent intersection avoids that supply amplification but cannot by itself assign exclusive ownership.

Therefore proof intersection is rejected as a standalone minting rule. `SPEC-1-CANDIDATE.md` specifies the surviving research branch: a **canonical vein auction** in which claimant-independent proof histories open at most one opportunity, separate prior-committed local work allocates one title, and Bitcoin publishes and buries that title.

## Remaining validation gaps

- Reproduce the full lifecycle with the signed deterministic Bitcoin Core 31.1 Linux release binary.
- Run on macOS, preferably Apple Silicon.
- Execute under the declared Python floor, CPython 3.11, and also 3.12.
- Replace the fixed-claim 64-bit work-counter ceiling with a separately versioned rolling-work design before economic targets.
- Add an independent implementation that parses raw Bitcoin transactions and Merkle proofs rather than relying on decoded Core RPC responses.
- Obtain external cryptographic and protocol review.
- Benchmark the `GAW0` header on existing SHA-256 hardware.
- Model fee shocks, batching, censorship windows, claim floods, key loss, source-chain correlation, and source-miner grinding before choosing monetary constants.
- Implement and falsify the GoldAtom/1 canonical contest indexer and one-vein/one-title settlement state machine.

## Release boundary

This validation establishes that the GoldAtom/0 object layer is executable and internally consistent under the recorded regtest conditions, including reorganization behavior and overlapping Python/Node cryptographic recomputation. It does not establish production safety, mainnet readiness, economic scarcity, fair issuance, purchasing power, specialized-hardware resistance, legal status, or independent audit.
