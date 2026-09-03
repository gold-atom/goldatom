# GoldAtom independent rerun — 2026-09-02

A fresh isolated Bitcoin Core regtest lifecycle was executed from the GoldAtom 0.0.3 repository during the review prompted by the user's question, rather than relying on the preserved validation transcript.

Result: PASS.

- Bitcoin binary identification: Bitcoin Core daemon version v31.99.0-031175197f1b bitcoind
- Binary SHA-256: 8e3afd78738ebc6d59787fc232c4f0025b6a3dd1e2c59cee4fd1b5ed1ba3dba4
- Atom ID: 71f9d931f3627162725ae5823ff600a581fbfddc46f50cceacdc6915db21c970
- Heights: claim 102 → challenge 105 → mint 106 → assay tip 107
- Tampered work: rejected
- Tampered challenge: rejected
- Challenge-block invalidation: atom rejected
- Block reconsideration: validity restored

Caveat: the executable identifies itself as a Bitcoin Core pre-release/master build, not a signed stable release binary. This rerun validates the prototype lifecycle against that executable; it is not an external security audit, a formal proof, or a production-readiness certification.
