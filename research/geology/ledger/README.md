# Bitcoin record-geology ledger

This directory contains empirical results from canonical Bitcoin mainnet headers through the fixed tip below. Historical raw records are **deposits/specimens, not GoldAtoms**. Nothing here assigns ownership or retroactively mints anything.

## Empirical observations

- Tip: height **965,246**, `00000000000000000000b96ab4c27a88f0394225bce8d8f8f92027f28563be1b`, 2026-09-03T02:05:17Z.
- Raw deposits: **30**; normalized records: **8**.
- Current raw frontier: `0000000000000000000000005d6f06154c8685146aa7bc3dc9843876c9cefd0f`.
- Current target: `000000000000000000023cc10000000000000000000000000000000000000000`.
- Current gap: **18.615901 bits**.
- Conditional next-block raw-deposit probability: **2.48917536691e-06**, approximately **1 in 401,739**.
- Shortest completed raw interval: **1,028 blocks** (6.29 days by the corresponding timestamp interval).
- Longest completed raw interval: **107,193 blocks** (738.43 days).
- Median completed raw interval: **12,717 blocks**.
- Current incomplete interval: **208,295 blocks** since height 756,951.

### Deposits by year

- 2009: 3
- 2010: 7
- 2011: 3
- 2012: 1
- 2013: 4
- 2014: 4
- 2015: 1
- 2017: 2
- 2018: 1
- 2019: 1
- 2020: 1
- 2022: 2

### Deposits by halving era

- halving-0 (0-209999): 14
- halving-1 (210000-419999): 9
- halving-2 (420000-629999): 4
- halving-3 (630000-839999): 3

### Difficulty eras containing deposits

- retarget-0 (0-2015): 2
- retarget-5 (10080-12095): 1
- retarget-21 (42336-44351): 1
- retarget-27 (54432-56447): 1
- retarget-29 (58464-60479): 1
- retarget-30 (60480-62495): 1
- retarget-36 (72576-74591): 1
- retarget-44 (88704-90719): 1
- retarget-45 (90720-92735): 1
- retarget-50 (100800-102815): 1
- retarget-56 (112896-114911): 1
- retarget-62 (124992-127007): 1
- retarget-102 (205632-207647): 1
- retarget-118 (237888-239903): 1
- retarget-121 (243936-245951): 1
- retarget-128 (258048-260063): 1
- retarget-132 (266112-268127): 1
- retarget-155 (312480-314495): 1
- retarget-161 (324576-326591): 1
- retarget-164 (330624-332639): 1
- retarget-165 (332640-334655): 1
- retarget-182 (366912-368927): 1
- retarget-227 (457632-459647): 1
- retarget-248 (499968-501983): 1
- retarget-255 (514080-516095): 1
- retarget-290 (584640-586655): 1
- retarget-314 (633024-635039): 1
- retarget-368 (741888-743903): 1
- retarget-375 (756000-758015): 1

### Difficulty retarget observations

Near/after a retarget means position 0–12 in its 2,016-block period. Qualifying raw records: 0 (genesis is position 0).
Adjacent raw records (zero or one intervening block): none.
Retargets where the new target was already below the entering raw frontier, which would make the first valid block an automatic record: none.
Raw records occurring in a period whose difficulty fell at its boundary: 334261, 634842, 742035, 756951.

## Data and independent verification

The archival prefix is `bitcoincc/headers` commit `b53315ec4991e0ca06eabae0d17774afea7bf4b5` through height 926039; the suffix is captured from `https://mempool.space/api/v1/blocks/{height}` through the fixed tip. Every displayed hash was recomputed from the 80-byte header, and the whole chain was checked for genesis, linkage, proof of work, intra-period bits, and retarget rules.

Manual hash cross-checks against both mempool.space and Blockstream at heights 0, 125552, 313338, 585774, 756951, 965246 matched exactly. `goldatom_ledger.mjs` independently agreed with Python on every raw-record height and hash, the count, and terminal frontier.

## Files

- `raw-records.csv`: all raw-record specimens and requested per-record fields.
- `normalized-records.csv`: all difficulty-normalized records.
- `summary.json`: machine-readable counts, groupings, frontier, target, probabilities, and verification metadata.

## Reproduction

1. Clone `https://github.com/bitcoincc/headers` at the commit recorded above.
2. Build the fixed snapshot: `python3 research/geology/goldatom_ledger.py bitcoincc-mempool-sync --bitcoincc-dir <clone> --tip-height 965246 --out bitcoin-mainnet-headers.bin`.
3. Run `python3 research/geology/run_experiment.py bitcoin-mainnet-headers.bin`.

The 77 MB input snapshot is reproducible and intentionally not committed.

## Interpretation boundary

Everything above reports measurements. Interpretive conclusions and disconfirming evidence are separated into `../ANALYSIS.md`.

## Activation candidate (documented, not executed)

A future GoldAtom/1 profile could become active through a Bitcoin transaction containing a commitment equivalent to `GA1P || SHA256(frozen_profile)`. The canonical Bitcoin block containing that commitment would establish activation. Deposits at or below activation would remain permanently non-extractable historical specimens. Deposits above activation could become eligible only under a future extraction specification. This experiment selects no activation height and performs no activation.
