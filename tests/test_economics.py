from __future__ import annotations

import math
import unittest

from goldatom.economics import (
    auction_censorship_share,
    effective_producers,
    gate_stats,
    gini,
    hhi,
    one_retry_withholding_threshold,
    producer_shares,
    target_granularity,
    variant_gate_probability,
)


class EconomicsTests(unittest.TestCase):
    def test_equal_producers(self) -> None:
        shares = producer_shares(100, 1)
        self.assertAlmostEqual(shares[0], 0.01)
        self.assertAlmostEqual(sum(shares), 1.0)
        self.assertAlmostEqual(hhi(shares), 0.01)
        self.assertAlmostEqual(effective_producers(shares), 100.0)
        self.assertAlmostEqual(gini(shares), 0.0)

    def test_hardware_advantage_share(self) -> None:
        shares = producer_shares(100, 100)
        self.assertAlmostEqual(shares[0], 100 / 199)
        self.assertGreater(shares[0], 0.5)

    def test_variant_amplification(self) -> None:
        p = 1 / 4096
        self.assertAlmostEqual(variant_gate_probability(p, 1), p)
        self.assertGreater(variant_gate_probability(p, 10_000), 0.9)

    def test_gate_stats(self) -> None:
        stats = gate_stats(epochs=4096, probability=1 / 4096)
        self.assertAlmostEqual(stats.expected_gates, 1.0)
        self.assertAlmostEqual(stats.standard_deviation, math.sqrt(1 - 1 / 4096))

    def test_censorship_bound(self) -> None:
        self.assertAlmostEqual(
            auction_censorship_share(
                native_share=0.2,
                checkpoint_share=0.2,
                censored_rival_fraction=1.0,
            ),
            0.36,
        )

    def test_withholding_threshold(self) -> None:
        self.assertAlmostEqual(
            one_retry_withholding_threshold(miner_share=0.2, gate_probability=1 / 4096),
            16_384,
        )

    def test_target_granularity(self) -> None:
        result = target_granularity(hash_budget=2**40, expected_work_per_atom=2**32)
        self.assertEqual(result.expected_atoms, 256)
        self.assertEqual(result.unbatched_lifecycle_transactions, 512)
        self.assertAlmostEqual(result.credited_work_relative_stddev, 1 / 16)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            producer_shares(1, 1)
        with self.assertRaises(ValueError):
            variant_gate_probability(0, 1)
        with self.assertRaises(ValueError):
            one_retry_withholding_threshold(miner_share=1, gate_probability=0.5)


if __name__ == "__main__":
    unittest.main()
