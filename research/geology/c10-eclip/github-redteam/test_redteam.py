#!/usr/bin/env python3
"""Independent deterministic tests for the GitHub red-team implementation."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import random
import sys
import unittest
from decimal import Decimal, localcontext
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("redteam.py")
SPEC = importlib.util.spec_from_file_location("github_redteam", MODULE_PATH)
assert SPEC and SPEC.loader
redteam = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = redteam
SPEC.loader.exec_module(redteam)

POLICY_PATH = Path(__file__).with_name("policy_sim.py")
POLICY_SPEC = importlib.util.spec_from_file_location("github_redteam_policy", POLICY_PATH)
assert POLICY_SPEC and POLICY_SPEC.loader
policy = importlib.util.module_from_spec(POLICY_SPEC)
sys.modules[POLICY_SPEC.name] = policy
POLICY_SPEC.loader.exec_module(policy)

BOUNDS_PATH = Path(__file__).with_name("bounds_mc.py")
BOUNDS_SPEC = importlib.util.spec_from_file_location("github_redteam_bounds", BOUNDS_PATH)
assert BOUNDS_SPEC and BOUNDS_SPEC.loader
bounds = importlib.util.module_from_spec(BOUNDS_SPEC)
sys.modules[BOUNDS_SPEC.name] = bounds
BOUNDS_SPEC.loader.exec_module(bounds)

MERGE_PATH = Path(__file__).with_name("merge_policy_results.py")
MERGE_SPEC = importlib.util.spec_from_file_location("github_redteam_merge", MERGE_PATH)
assert MERGE_SPEC and MERGE_SPEC.loader
merge = importlib.util.module_from_spec(MERGE_SPEC)
sys.modules[MERGE_SPEC.name] = merge
MERGE_SPEC.loader.exec_module(merge)


class StubRandom:
    def __init__(self, values: list[float]) -> None:
        self.values = iter(values)

    def random(self) -> float:
        return next(self.values)


class ArithmeticTests(unittest.TestCase):
    def test_certified_ceil_matches_high_precision_fixtures(self) -> None:
        fixtures = {
            1: 1,
            2: 1,
            3: 2,
            10: 4,
            2**256 - 1: 42597529080697662913911602080600932014987715856510989744817822076425378192110,
        }
        for value, expected in fixtures.items():
            self.assertEqual(redteam.ceil_div_e(value), expected)

    def test_initialization_is_clipped(self) -> None:
        g1, g2 = redteam.init_state(1, 10)
        self.assertEqual((g1, g2), (4, 10))

    def test_all_zero_initialization_is_absorbing(self) -> None:
        self.assertEqual(redteam.init_state(0, 0), (0, 0))
        self.assertEqual(redteam.transition((0, 0), 0), (False, "neither", (0, 0)))

    def test_extreme_q_probability_tail_is_positive_and_stable(self) -> None:
        result = redteam.exact_probabilities(1, 2**256 - 1)
        actual = Decimal(result["p_k_ge_2"])
        with localcontext() as context:
            context.prec = 200
            q = Decimal(1) / Decimal(2**256 - 1)
            leading = Decimal(redteam.W * (redteam.W - 1) // 2) * q * q
            self.assertGreater(actual, 0)
            self.assertLess(abs(actual / leading - 1), Decimal("1e-70"))

    def test_invariant_randomized_integer_states(self) -> None:
        rng = random.Random(1269070838)
        for _ in range(10_000):
            g2 = rng.randrange(1, 2**256)
            lower = redteam.ceil_div_e(g2)
            g1 = rng.randrange(lower, g2 + 1)
            epoch_minimum = rng.randrange(0, 2**256)
            _, _, post = redteam.transition((g1, g2), epoch_minimum)
            self.assertLessEqual(post[0], post[1])
            self.assertLessEqual(post[1] * redteam.E_DEN, post[0] * redteam.E_HI_NUM)


class CompactTests(unittest.TestCase):
    def test_genesis_target(self) -> None:
        self.assertEqual(redteam.decode_compact(0x1D00FFFF), redteam.POW_LIMIT)
        self.assertEqual(redteam.encode_compact(redteam.POW_LIMIT), 0x1D00FFFF)

    def test_known_compact_roundtrips(self) -> None:
        for bits in (0x1D00FFFF, 0x1B0404CB, 0x1701E2A0):
            self.assertEqual(redteam.encode_compact(redteam.decode_compact(bits)), bits)


class TransitionTests(unittest.TestCase):
    def test_deposit_uses_pre_transition_second(self) -> None:
        deposit, kind, post = redteam.transition((40, 100), 39)
        self.assertTrue(deposit)
        self.assertEqual(kind, "unique-min")
        self.assertEqual(post, (39, 40))

    def test_new_second_always_deposits(self) -> None:
        deposit, kind, post = redteam.transition((40, 100), 80)
        self.assertTrue(deposit)
        self.assertEqual(kind, "new-second")
        self.assertEqual(post, (40, 80))

    def test_k_one_has_no_suppressible_later_qualifier(self) -> None:
        result = policy.attacked_epoch_minimum(
            kind="c10-eclip",
            state=(0.2, 0.5),
            threshold=0.5,
            base_values=[0.4],
            base_owners=[True],
            alpha=1.0,
            model="A",
            policy="prefer-shallow",
            target=1.0,
            state_floor=0.01,
            replacement_rng=StubRandom([]),
            value_over_reward=1.0,
            discount=0.99,
        )
        retained, withheld, _, _, _, actual_k = result
        self.assertEqual((retained, withheld, actual_k), (0.4, 0, 1))

    def test_clip_dominated_fast_path_matches_scalar_transition(self) -> None:
        floor = 1e-60
        rng = random.Random(policy.MASTER_SEED)
        for _ in range(10_000):
            honest_g2 = 10 ** rng.uniform(-40, -1)
            attacked_g2 = 10 ** rng.uniform(-40, -1)
            honest = (rng.uniform(honest_g2 / policy.E, honest_g2), honest_g2)
            attacked = (rng.uniform(attacked_g2 / policy.E, attacked_g2), attacked_g2)
            target = min(honest[0], attacked[0]) / (2 * policy.E)
            value = rng.random() * target
            scalar_honest, deposit_honest = policy.step("c10-eclip", honest, value, floor)
            scalar_attacked, deposit_attacked = policy.step("c10-eclip", attacked, value, floor)
            fast_honest = (max(floor, honest[0] / policy.E), honest[0])
            fast_attacked = (max(floor, attacked[0] / policy.E), attacked[0])
            self.assertEqual((scalar_honest, deposit_honest), (fast_honest, 1))
            self.assertEqual((scalar_attacked, deposit_attacked), (fast_attacked, 1))

    def test_quarter_target_regime_becomes_qualifier_independent(self) -> None:
        state = (0.4, 1.0)
        target = 0.1
        self.assertLessEqual(target, state[0] / policy.E)
        low = policy.step("c10-eclip", state, 0.01, 1e-100)
        high = policy.step("c10-eclip", state, 0.09, 1e-100)
        self.assertEqual(low, high)


class PolicySimulationTests(unittest.TestCase):
    def test_accepted_hash_support_is_capped_at_target(self) -> None:
        self.assertEqual(policy.accepted_low_support(0.25, 1.0), (0.25, 0.25))
        self.assertEqual(policy.accepted_low_support(2.0, 1.0), (1.0, 1.0))

    def test_model_a_replacements_retain_ownership_and_continue(self) -> None:
        result = policy.attacked_epoch_minimum(
            kind="c10-eclip",
            state=(0.2, 0.5),
            threshold=0.5,
            base_values=[0.4, 0.1],
            base_owners=[False, True],
            alpha=0.5,
            model="A",
            policy="prefer-shallow",
            target=1.0,
            state_floor=0.01,
            replacement_rng=StubRandom([0.05, 0.1, 0.45, 0.9]),
            value_over_reward=1.0,
            discount=0.99,
        )
        retained, withheld, work, attacker_replacements, honest_replacements, actual_k = result
        self.assertEqual(retained, 0.4)
        self.assertEqual(withheld, 2)
        self.assertAlmostEqual(work, 2 / 1.01)
        self.assertEqual((attacker_replacements, honest_replacements), (1, 1))
        self.assertEqual(actual_k, 2)

    def test_replacement_above_bar_reduces_actual_canonical_k(self) -> None:
        result = policy.attacked_epoch_minimum(
            kind="c10-eclip",
            state=(0.2, 0.5),
            threshold=0.5,
            base_values=[0.4, 0.1],
            base_owners=[False, True],
            alpha=0.5,
            model="A",
            policy="prefer-shallow",
            target=1.0,
            state_floor=0.01,
            replacement_rng=StubRandom([0.8, 0.9]),
            value_over_reward=1.0,
            discount=0.99,
        )
        retained, withheld, _, attacker_replacements, honest_replacements, actual_k = result
        self.assertEqual(retained, 0.4)
        self.assertEqual((withheld, attacker_replacements, honest_replacements), (1, 0, 1))
        self.assertEqual(actual_k, 1)

    def test_model_b_repeated_redraws_remain_attacker_owned(self) -> None:
        result = policy.attacked_epoch_minimum(
            kind="c10-eclip",
            state=(0.2, 0.5),
            threshold=0.5,
            base_values=[0.4, 0.1],
            base_owners=[False, True],
            alpha=0.5,
            model="B",
            policy="prefer-shallow",
            target=1.0,
            state_floor=0.01,
            replacement_rng=StubRandom([0.05, 0.8]),
            value_over_reward=1.0,
            discount=0.99,
        )
        retained, withheld, _, attacker_replacements, honest_replacements, actual_k = result
        self.assertEqual(retained, 0.4)
        self.assertEqual((withheld, attacker_replacements, honest_replacements), (2, 2, 0))
        self.assertEqual(actual_k, 1)

    def test_exact_binomial_categories_are_stable_and_partition_one(self) -> None:
        for q in (0.0, 1e-20, 1e-9, 1e-5, 0.1, 1.0):
            p0, p1, p_ge_2 = policy.exact_binomial_category_probabilities(q)
            self.assertGreaterEqual(p_ge_2, 0.0)
            self.assertAlmostEqual(p0 + p1 + p_ge_2, 1.0, places=13)
        rare_q = 1e-20
        rare_tail = policy.exact_binomial_category_probabilities(rare_q)[2]
        leading = policy.W * (policy.W - 1) * rare_q * rare_q / 2
        self.assertGreater(rare_tail, 0.0)
        self.assertAlmostEqual(rare_tail / leading, 1.0, places=12)

    def test_omniscient_summary_nulls_undefined_actual_k_and_old_success_names(self) -> None:
        outputs = policy.simulate_trial(
            kind="c10-eclip",
            initial_state=(0.2, 0.5),
            scenario="A-constant",
            alpha=1.0,
            model="upper",
            policy="omniscient",
            horizon=100,
            seed=policy.MASTER_SEED,
            initial_target=1.0,
            min_target=1e-20,
            max_target=1.0,
            historical_ratios=[],
            value_over_reward=1.0,
            discount=0.99,
        )
        row = policy.summarize(
            [outputs[100]],
            kind="c10-eclip",
            scenario="A-constant",
            alpha=1.0,
            model="upper",
            policy="omniscient",
            horizon=100,
        )
        self.assertTrue(
            all(
                row[field] is None
                for field in (
                    "actual_attacked_k0_epochs_mean",
                    "actual_attacked_k1_epochs_mean",
                    "actual_attacked_k_ge_2_epochs_mean",
                )
            )
        )
        self.assertIsNone(row["registered_conditional_success_probability"])
        self.assertNotIn("successful_selection_epochs_mean", row)
        self.assertNotIn("probability_any_successful_selection", row)

    def test_zero_policy_preserves_network_opportunities_and_null_elasticity(self) -> None:
        source = {
            "policy": "prefer-shallow",
            "honest_deposits_mean": 0.0,
            "attack_deposits_mean": 1.0,
            "honest_k0_epochs_mean": 8.0,
            "honest_k1_epochs_mean": 1.0,
            "honest_k_ge_2_epochs_mean": 1.0,
            "attacked_counterfactual_k0_epochs_mean": 7.0,
            "attacked_counterfactual_k1_epochs_mean": 1.0,
            "attacked_counterfactual_k_ge_2_epochs_mean": 2.0,
            "honest_exact_p_k0_epochs_mean": 7.5,
            "honest_exact_p_k1_epochs_mean": 1.5,
            "honest_exact_p_k_ge_2_epochs_mean": 1.0,
        }
        numeric = (
            "delta_mean", "elasticity", "delta_median", "delta_p90", "delta_p95",
            "delta_p99", "delta_maximum", "maximum_prefix_delta_observed",
            "probability_any_state_raising_selection", "selectable_epochs_mean",
            "selection_attempt_epochs_mean", "state_raising_selection_epochs_mean",
            "harmful_selection_epochs_mean", "discarded_valid_candidates_mean",
            "replacement_discoveries_mean", "attacker_replacements_mean",
            "honest_replacements_mean", "withheld_bitcoin_blocks_mean",
            "bitcoin_reward_cost_mean_R", "extra_sha_trials_mean",
            "attacker_captured_marginal_deposits_retain_share", "divergence_duration_mean",
            "probability_terminal_state_diverged", "terminal_g1_relative_difference_mean",
            "terminal_g2_relative_difference_mean", "private_fork_or_orphan_cost_R",
            "latency_cost_R",
        )
        source.update({key: 1.0 for key in numeric})
        source.update(
            {
                "R_per_expected_global_marginal_deposit": 1.0,
                "R_per_expected_attacker_captured_deposit": 1.0,
                "probability_reconvergence_given_divergence": 1.0,
                "reconvergence_time_mean_given_observed": 1.0,
            }
        )
        row = policy.zero_policy_rows([source], "honest-publication")[0]
        self.assertEqual(row["selectable_epochs_mean"], 1.0)
        self.assertEqual(row["actual_attacked_k_ge_2_epochs_mean"], 1.0)
        self.assertIsNone(row["registered_conditional_success_probability"])
        self.assertIsNone(row["elasticity"])

    def test_registered_decimal_seed_is_authoritative(self) -> None:
        self.assertEqual(policy.MASTER_SEED, 1269070838)
        self.assertEqual(hex(policy.MASTER_SEED), "0x4ba47bf6")


class BoundsTests(unittest.TestCase):
    def test_exact_conditional_sampler_accepts_unit_upper_bound(self) -> None:
        value = bounds.conditional_epoch_minimum(random.Random(1), 1.0, exact=True)
        self.assertGreaterEqual(value, 0.0)
        self.assertLess(value, 1.0)


class ArtifactValidationTests(unittest.TestCase):
    def test_merged_artifact_revalidates_as_six_disjoint_shards(self) -> None:
        result_path = Path(__file__).with_name("results") / "policy-simulation.json"
        document = json.loads(result_path.read_text(encoding="utf-8"))
        metadata = {key: value for key, value in document.items() if key != "rows"}
        documents = []
        for index in range(0, len(merge.SCENARIOS), 2):
            selected = set(merge.SCENARIOS[index : index + 2])
            documents.append(
                metadata
                | {"rows": [row for row in document["rows"] if row["scenario"] in selected]}
            )
        source_hashes = [f"{index + 1:064x}" for index in range(6)]
        policy_hash = hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
        validated = merge.validate_and_merge_documents(
            documents,
            source_hashes,
            expected_policy_sim_sha256=policy_hash,
        )
        self.assertEqual(len(validated["rows"]), 3888)

    def test_historical_scenario_starts_at_verified_epoch_two(self) -> None:
        results = Path(__file__).with_name("results")
        summary = json.loads((results / "historical-summary.json").read_text(encoding="utf-8"))
        targets = json.loads((results / "historical-targets.json").read_text(encoding="utf-8"))
        matrix = json.loads((results / "policy-simulation.json").read_text(encoding="utf-8"))
        live_target = int(summary["live_target"])
        self.assertEqual(int(summary["simulation_first_target"]), int(targets["targets"][2]))
        self.assertEqual(
            matrix["historical_initial_target"],
            int(targets["targets"][2]) / live_target,
        )
        self.assertEqual(
            matrix["historical_initial_state"],
            [
                int(summary["simulation_initial_g1"]) / live_target,
                int(summary["simulation_initial_g2"]) / live_target,
            ],
        )


if __name__ == "__main__":
    unittest.main()
