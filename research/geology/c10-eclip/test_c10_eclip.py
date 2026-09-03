import importlib.util
import json
import math
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np


HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = load("c10_eclip_tested", "c10_eclip.py")
S = load("c10_eclip_sim_tested", "simulate.py")
B = load("c10_eclip_bounds_tested", "bounds.py")


class EClipTransitionTests(unittest.TestCase):
    def test_integer_e_clip_certificates(self):
        expected = {
            0: 0,
            1: 1,
            2: 1,
            3: 2,
            10: 4,
            100: 37,
            2**256 - 1: 42597529080697662913911602080600932014987715856510989744817822076425378192110,
        }
        lower, upper = C.e_bounds()
        for value, clipped in expected.items():
            self.assertEqual(C.ceil_div_e(value), clipped)
            self.assertGreaterEqual(lower * clipped, value)
            if value:
                self.assertLess(upper * (clipped - 1), value)

    def test_historical_initialization_clips_load_bearing_ratio(self):
        a = 3857338712755543345253973973591186299193617950513887497584803401
        b = 22196314501187840792218844525263652093585624848119336967297003374
        state = C.initialize(a, b)
        self.assertEqual(state, C.initialize(b, a))
        self.assertEqual(state.g1, 8165567774762564395586499251453268775359881340032553143329137868)
        self.assertEqual(state.g2, b)
        self.assertGreater(b / a, math.e)
        self.assertTrue(C.ratio_at_most_e(state.g1, state.g2))

    def test_deposit_uses_pre_transition_second_frontier(self):
        state = C.State(40, 100)
        cases = {
            39: (True, "unique-min", C.State(39, 40)),
            40: (True, "new-second", C.State(40, 40)),
            99: (True, "new-second", C.State(40, 99)),
            100: (False, "neither", state),
        }
        for observation, expected in cases.items():
            event = C.transition(state, observation)
            self.assertEqual((event.deposit, event.kind, event.after), expected)

    def test_invariant_is_inductive_on_small_integer_space(self):
        for a in range(1, 31):
            for b in range(1, 31):
                state = C.initialize(a, b)
                self.assertTrue(C.ratio_at_most_e(state.g1, state.g2))
                for observation in range(61):
                    after = C.transition(state, observation).after
                    self.assertTrue(C.ratio_at_most_e(after.g1, after.g2))

    def test_new_second_a0_creating_set_is_empty(self):
        lower_e, upper_e = C.e_bounds()
        largest_tested_ratio = 1.0
        for g1 in range(1, 513):
            # Certify the exact greatest integer G2 admitted by G2/G1 <= e.
            # Equality of these floors means the rational enclosure, rather
            # than binary floating point, determines the boundary.
            lower_floor = (lower_e.numerator * g1) // lower_e.denominator
            upper_floor = (upper_e.numerator * g1) // upper_e.denominator
            self.assertEqual(lower_floor, upper_floor)
            max_g2 = lower_floor

            self.assertTrue(C.ratio_at_most_e(g1, max_g2))
            self.assertFalse(C.ratio_at_most_e(g1, max_g2 + 1))
            largest_tested_ratio = max(largest_tested_ratio, max_g2 / g1)

            # Exercise every integer state in the complete admitted interval.
            # lower_e * G1 >= G2 is an exact certificate that G2/G1 < e,
            # hence the new-second A0 term ln(G2/G1) - 1 cannot be positive.
            for g2 in range(g1, max_g2 + 1):
                self.assertTrue(C.ratio_at_most_e(g1, g2))
                self.assertGreaterEqual(lower_e * g1, g2)

        self.assertGreater(largest_tested_ratio, math.e - 0.002)

    def test_discrete_crossing_strict_inequality(self):
        self.assertEqual(C.exact_crossing_probability(0, 3), 0)
        self.assertEqual(C.exact_crossing_probability(1, 3), 0.25)
        self.assertEqual(C.exact_crossing_probability(4, 3), 1)

    def test_stable_finite_binomial(self):
        result = C.binomial_crossing_stats(0.25, 2)
        self.assertAlmostEqual(result["p_k_ge_1"], 7 / 16)
        self.assertAlmostEqual(result["p_k_ge_2"], 1 / 16)
        self.assertAlmostEqual(result["p_k_ge_2_given_k_ge_1"], 1 / 7)


class SimulationTests(unittest.TestCase):
    def test_state_neutral_deeper_hash_is_not_eligible(self):
        g1 = np.array([0.5])
        g2 = np.array([1.0])
        shallow = np.array([0.10])
        deep = np.array([0.01])
        self.assertFalse(S.effective_tightening("c10-eclip", g1, g2, shallow, deep)[0])

    def test_target_paths_respect_declared_retarget_bound(self):
        start_target = S.decode_compact_target(0x1701E63A)
        for name in (
            "A-constant-target", "B-historical-like-growth",
            "C-four-year-growth-then-plateau", "D-difficulty-decline",
            "E-consensus-retarget-sawtooth",
        ):
            path = S.target_path(
                name, 300, 0.986, S.POW_LIMIT / start_target,
                start_target=start_target,
            )
            ratios = path[1:] / path[:-1]
            # Compact target truncation can put the encoded /4 endpoint a few
            # ulps below the unencoded rational bound.
            self.assertTrue(np.all(ratios >= 0.24999))
            self.assertTrue(np.all(ratios <= 4.0 + 1e-15))

    def test_scenario_e_uses_exact_bitcoin_retarget_arithmetic(self):
        start = S.decode_compact_target(0x1701E63A)
        path = S.target_path(
            "E-consensus-retarget-sawtooth", 5, 0.986,
            S.POW_LIMIT / start, start_target=start,
        )
        expected = [start]
        for index in range(1, 5):
            span = S.TARGET_TIMESPAN // 4 if index % 2 else S.TARGET_TIMESPAN * 4
            expected.append(S.retarget_target(expected[-1], span))
        np.testing.assert_array_equal(path, np.array([target / start for target in expected]))
        for target in expected:
            self.assertEqual(
                S.decode_compact_target(S.encode_compact_target(target)), target
            )

    def test_hard_budget_caps_each_path(self):
        initial = S.InitialState("c10-eclip", 0.01 / math.e, 0.01)
        result = S.simulate_path(
            initial, np.ones(50), 1.0, "public-lock", 256, 91,
            gross_budget_cap_R=1,
        )
        endpoint = result[1]
        self.assertTrue(np.all(endpoint["forfeited_blocks"] <= 1))

    def test_epoch_simulation_is_seed_deterministic(self):
        g1 = np.full(64, 0.001 / math.e)
        g2 = np.full(64, 0.001)
        a = S.strategic_epoch_minimum(
            np.random.default_rng(7), 1.0, g1, g2, 0.3, "public-lock"
        )
        b = S.strategic_epoch_minimum(
            np.random.default_rng(7), 1.0, g1, g2, 0.3, "public-lock"
        )
        for key in a:
            np.testing.assert_array_equal(a[key], b[key])

    def test_record_low_skip_matches_small_w_order_statistic(self):
        repetitions = 50_000
        g1 = np.full(repetitions, 0.5)
        g2 = np.full(repetitions, 1.0)
        with mock.patch.object(S, "W", 20):
            result = S.strategic_epoch_minimum(
                np.random.default_rng(771), 1.0, g1, g2, 0.3,
                "record-honest",
            )
        # Minimum of 20 independent U(0,1) values has mean 1/21.
        self.assertLess(abs(float(np.mean(result["minimum"])) - 1 / 21), 0.001)

    def test_zero_hash_share_cannot_select(self):
        g1 = np.full(512, 0.01 / math.e)
        g2 = np.full(512, 0.01)
        result = S.strategic_epoch_minimum(
            np.random.default_rng(8), 1.0, g1, g2, 0.0, "public-lock"
        )
        self.assertEqual(int(result["eligible_attacker_events"].sum()), 0)
        self.assertEqual(int(result["forfeited_blocks"].sum()), 0)

    def test_live_ownership_effective_subset(self):
        history = json.loads((HERE / "historical-summary.json").read_text())
        state = history["live_c10_eclip"]["state"]
        ratio = int(state["g1"]) / int(state["g2"])
        result = S.ownership_metrics(
            history["live_c10_eclip"]["p_per_valid_block"], 0.3, ratio
        )
        self.assertLess(
            result["p_state_effective_public_qualifier_then_later_deeper_attacker"],
            result["p_public_qualifier_then_later_deeper_attacker"],
        )
        self.assertLessEqual(
            result["p_strategically_suppressible_state_effective_later_attacker_unique_min"],
            result["p_state_effective_public_qualifier_then_later_deeper_attacker"],
        )

    def test_fixed_target_bound_monte_carlo_tracks_analytic_value(self):
        result = B.rare_limit_max_pair(100_000, B.SEED)
        analytic = (2 * math.e - 1) / (math.e - 1)
        self.assertLess(abs(result["mean_extra_future_deposits"] - analytic), 0.03)

    def test_adaptive_stress_refutes_old_bound_but_stays_below_new_bound(self):
        result = B.adaptive_reset_stress(100_000)
        corrected = 1 + 1 / (math.exp(-1) - math.exp(-2))
        self.assertGreater(result["mean_extra_future_deposits"], 4.30)
        self.assertLess(result["mean_extra_future_deposits"], corrected)


class GeneratedEvidenceTests(unittest.TestCase):
    def test_historical_golden_summary(self):
        summary = json.loads((HERE / "historical-summary.json").read_text())
        self.assertEqual(summary["source"]["tip_height"], 965246)
        self.assertEqual(summary["historical"]["deposits"], 82)
        self.assertEqual(summary["historical"]["epochs_k_ge_2"], 23)
        self.assertEqual(summary["source"]["partial_epoch"]["blocks_observed"], 1599)
        self.assertEqual(summary["source"]["partial_epoch"]["blocks_remaining"], 417)
        self.assertEqual(
            summary["source"]["partial_epoch"]["crossings_of_live_pre_epoch_g2_observed"],
            0,
        )
        self.assertEqual(
            summary["historical"]["epochs_with_monopoly_qualifier_selection_opportunity"], 10
        )
        self.assertTrue(
            summary["invariant"]["all_reachable_historical_states_g2_over_g1_at_most_e"]
        )

    @unittest.skipUnless(os.environ.get("BITCOIN_HEADERS_FILE"), "external header snapshot not configured")
    def test_full_header_replay_matches_golden_counts(self):
        summary, rows, crossings = C.replay(Path(os.environ["BITCOIN_HEADERS_FILE"]))
        self.assertEqual(summary["source"]["headers_sha256"],
                         "6d5775640085f29bae0882e4ec3c99f752ad4546f7589650adb9be1d4fd392af")
        self.assertEqual(len(rows), 478)
        self.assertEqual(len(crossings), 116)
        self.assertEqual(summary["historical"]["deposits"], 82)


if __name__ == "__main__":
    unittest.main()
