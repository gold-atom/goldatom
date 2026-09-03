# Raw-record miner-adversary simulator

This simulator tests publication strategies; it does not implement GoldAtom extraction or ownership.

`simulate.py` represents each Bitcoin-valid hash as a uniform value in `[0,1)` and counts every draw as an ordinary PoW solution. A withheld solution is never recycled into free work. It provides:

- exact fixed-frontier results at the empirical `F/T` value;
- seeded Monte Carlo stress tests with an intentionally elevated frontier so path-dependent effects are measurable;
- honest publication, non-record withholding, record withholding, deep-record withholding, a one-lead truncated private-fork search, and selective-publication cases.

`selective_publication` is an explicit alias for the publish-only-records (`withhold_nonrecord`) policy in this model. Depth-selective publication is the separate `withhold_deep_record` strategy.

Run:

```sh
python3 research/geology/adversary/simulate.py \
  --output research/geology/adversary/results.json
python3 -m unittest discover -s research/geology/adversary -v
```

The stress test is a mechanism check, not a forecast. Its simplified private-search case does not replace a network simulator for selfish mining, propagation, retargets, or multi-block reorganizations. Analytical bounds and those limitations are reported in `../MINER-ADVERSARY-ANALYSIS.md`.
