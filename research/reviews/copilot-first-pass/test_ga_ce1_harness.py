from dataclasses import dataclass
from fractions import Fraction
import unittest


@dataclass(frozen=True)
class State:
    armed: int
    previous_hash: int


def initialize(previous_hash: int) -> State:
    return State(armed=1, previous_hash=previous_hash)


def step(previous_target: int, current_target: int, current_hash: int, state: State):
    deposit = int(
        state.armed == 1
        and current_target < previous_target
        and current_hash < state.previous_hash
    )
    return deposit, State(armed=state.armed * (1 - deposit), previous_hash=current_hash)


def run_synthetic_sequence(targets, hashes):
    if len(targets) != len(hashes):
        raise ValueError("targets and hashes must have equal length")
    if len(targets) < 2:
        raise ValueError("synthetic sequence must span at least two observations")
    state = initialize(hashes[0])
    deposits = []
    for index in range(1, len(targets)):
        deposit, state = step(targets[index - 1], targets[index], hashes[index], state)
        deposits.append(deposit)
    return deposits


def exact_deposit_probability(previous_target: int, current_target: int) -> Fraction:
    if current_target >= previous_target:
        return Fraction(0, 1)
    return Fraction(
        2 * previous_target - current_target,
        2 * (previous_target + 1),
    )


class GACE1SyntheticTests(unittest.TestCase):
    def test_synthetic_initialization_arms_latch(self):
        self.assertEqual(initialize(9), State(armed=1, previous_hash=9))

    def test_synthetic_strict_comparisons_reject_equalities(self):
        state = initialize(4)
        self.assertEqual(step(8, 8, 3, state)[0], 0)
        self.assertEqual(step(8, 5, 4, state)[0], 0)
        self.assertEqual(step(8, 5, 3, state)[0], 1)

    def test_synthetic_target_decrease_changes_probability(self):
        self.assertEqual(exact_deposit_probability(8, 8), 0)
        self.assertEqual(exact_deposit_probability(8, 2), Fraction(7, 9))
        self.assertEqual(exact_deposit_probability(8, 2), Fraction(2 * 8 - 2, 2 * (8 + 1)))

    def test_synthetic_first_deposit_absorbs_forever(self):
        self.assertEqual(run_synthetic_sequence([9, 5, 4, 3], [4, 3, 0, 0]), [1, 0, 0])

    def test_synthetic_lifetime_issuance_is_at_most_one(self):
        deposits = run_synthetic_sequence([12, 8, 6, 4, 2], [6, 5, 1, 0, 0])
        self.assertLessEqual(sum(deposits), 1)

    def test_synthetic_selective_publication_changes_next_outcome(self):
        shallow_choice = initialize(3)
        deep_choice = initialize(5)
        self.assertEqual(step(10, 6, 4, shallow_choice)[0], 0)
        self.assertEqual(step(10, 6, 4, deep_choice)[0], 1)


if __name__ == "__main__":
    unittest.main()
