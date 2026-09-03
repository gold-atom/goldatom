# Changelog

## 0.0.3 — 2026-09-02

- Added a one-command isolated Bitcoin Core live-validation runner.
- Repeated the complete claim→challenge→work→mint→burial lifecycle in a fresh temporary regtest datadir.
- Added independent Node.js recomputation of claim, challenge, work-header, work hash, mint, AtomID, and transfer commitments.
- Added five JSON-RPC transport tests and preserved native Bitcoin Core error codes returned inside HTTP 500 responses.
- Added a final machine-readable live proof bundle, consensus-primitives record, semantic-tamper results, and reversible reorganization evidence.
- Added `SPEC-1-CANDIDATE.md`, a non-normative claimant-independent canonical vein auction.
- Raised the deterministic unit-test count from 26 to 31.
- Added a complete final validation transcript and rebuilt reproducible source/wheel artifacts.

## 0.0.2 — 2026-09-02

- Executed the complete lifecycle against a live Bitcoin Core regtest node.
- Preserved the live proof bundle, independent verification report, node provenance, and full transcript.
- Added real-node tamper rejection and reversible challenge-block reorganization tests.
- Added assumption-explicit economic helpers and eight tests.
- Added deterministic comparisons of work-weighted bullion, sealed epoch auctions, and proof-intersection gating.
- Identified claimant-dependent proof intersections as Sybil-grindable and claimant-independent intersections as ownership-incomplete.
- Added the canonical vein auction as the experimental GoldAtom/1 research branch.
- Fixed direct execution of `simulation/issuance_regimes.py` by inserting the repository root into `sys.path`.
- Raised the deterministic test count from 18 to 26.

## 0.0.1 — 2026-09-02

- Initial verifier-first GoldAtom/0 protocol, simulated proof vectors, Core RPC adapter, regtest lifecycle driver, and source release.
