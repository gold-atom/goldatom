import importlib.util
import unittest
from pathlib import Path

P = Path(__file__).with_name("simulate.py")
S = importlib.util.spec_from_file_location("adversary_sim", P)
M = importlib.util.module_from_spec(S)
S.loader.exec_module(M)


class AdversarySimulationTests(unittest.TestCase):
    def test_honest_baseline(self):
        r = M.analytic_continue(0.0, 0.125)
        self.assertEqual(r["canonical_deposit_probability"], 0.125)
        self.assertEqual(r["delta_vs_honest"], 0.0)

    def test_continue_search_formula(self):
        r = M.analytic_continue(0.5, 0.25)
        self.assertAlmostEqual(r["attacker_record_before_honest"], 0.2)
        self.assertAlmostEqual(r["canonical_deposit_probability"], 0.4)
        self.assertAlmostEqual(r["expected_forfeited_bitcoin_blocks_per_canonical_block"], 0.6)

    def test_no_free_hash_trials(self):
        for strategy in ("honest", "withhold_nonrecord", "withhold_record",
                         "withhold_deep_record"):
            r = M.one_run(strategy, 0.3, 1000, 0.01, 12345)
            self.assertEqual(r["ordinary_pow_solutions"], 1000 + r["forfeited_blocks"])

    def test_deterministic_seed(self):
        a = M.one_run("withhold_deep_record", 0.3, 2000, 0.02, 7)
        b = M.one_run("withhold_deep_record", 0.3, 2000, 0.02, 7)
        self.assertEqual(a, b)

    def test_deep_withholding_asymptotic_threshold(self):
        below = M.deep_withholding_break_even(0.01, 2.0, 100_000)
        above = M.deep_withholding_break_even(0.01, 3.0, 100_000)
        self.assertLess(below["asymptotic_net_additional_deposits"], 0)
        self.assertIsNone(below["first_positive_horizon_canonical_blocks"])
        self.assertGreater(above["asymptotic_net_additional_deposits"], 0)
        self.assertIsNotNone(above["first_positive_horizon_canonical_blocks"])

    def test_deep_cutoff_policy_increases_count_coefficient(self):
        r = M.deep_cutoff_policy(0.5, M.CURRENT_P, 0.1)
        self.assertGreater(r["asymptotic_record_count_coefficient_vs_honest"], 1.0)
        self.assertAlmostEqual(r["expected_net_extra_records_per_censored_opportunity"],
                               __import__("math").log(10))


if __name__ == "__main__":
    unittest.main()
