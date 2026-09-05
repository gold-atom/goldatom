# Reproduction log

## Source establishment

- Repository: `gold-atom/goldatom`
- Starting branch: `copilot/research-audit-variable-difficulty`
- Starting commit: `fc75ea3c75cabd87d45fe037d9c886ab9987cf1e`
- Pinned source branch: `research/variable-difficulty-impossibility`
- Pinned commit: `187874d11c3432d2fa41eb22febb0ef452f4bc4f`
- Exact report path in pinned commit: `research/geology/VARIABLE-DIFFICULTY-IMPOSSIBILITY.md`
- Report SHA-256: `f4789ab3281bb14e8d9482ba347a54a3faf0d91793d83b0372678d04feb456aa`
- Review-directory export: `research/reviews/copilot-first-pass/VARIABLE-DIFFICULTY-IMPOSSIBILITY.pinned-187874d11c3432d2fa41eb22febb0ef452f4bc4f.md`
- Located later errata: none

## Environment

- Clean worktree path: `/tmp/goldatom-pinned-audit`
- Python: `Python 3.12.3`
- Node.js: `v22.23.2`

## Commands actually run

| Step | Working directory | Command | Exit |
|---|---|---|---:|
| Fetch pinned branch | `/home/runner/work/goldatom/goldatom` | `git fetch origin research/variable-difficulty-impossibility` | 0 |
| Confirm pinned commit | `/home/runner/work/goldatom/goldatom` | `git rev-parse FETCH_HEAD` | 0 |
| Locate report path | `/home/runner/work/goldatom/goldatom` | `git ls-tree -r --name-only 187874d11c3432d2fa41eb22febb0ef452f4bc4f \| grep 'VARIABLE-DIFFICULTY-IMPOSSIBILITY\.md'` | 0 |
| Clean checkout | `/home/runner/work/goldatom/goldatom` | `git worktree add --detach /tmp/goldatom-pinned-audit 187874d11c3432d2fa41eb22febb0ef452f4bc4f` | 0 |
| Root documented suite | `/tmp/goldatom-pinned-audit` | `python3 -m unittest discover -s tests -v` | 0 |
| Adversary documented suite | `/tmp/goldatom-pinned-audit` | `python3 -m unittest discover -s research/geology/adversary -v` | 0 |
| C10-eclip suite before deps | `/tmp/goldatom-pinned-audit` | `python3 -m unittest discover -s research/geology/c10-eclip -p 'test_*.py' -v` | 1 |
| Install declared research dependency | `/tmp/goldatom-pinned-audit` | `python3 -m pip install -r research/geology/c10-eclip/requirements.txt` | 0 |
| C10-eclip suite after deps | `/tmp/goldatom-pinned-audit` | `python3 -m unittest discover -s research/geology/c10-eclip -p 'test_*.py' -v` | 0 |
| Independent synthetic witness checks | `/home/runner/work/goldatom/goldatom` | `python3 -m unittest discover -s research/reviews/copilot-first-pass -p 'test_*.py' -v` | 0 |

## Test results

### Root documented suite

Command: `python3 -m unittest discover -s tests -v`

- Result: **31 passed, 0 failed, 0 skipped**

### `research/geology/adversary`

Command: `python3 -m unittest discover -s research/geology/adversary -v`

- Result: **6 passed, 0 failed, 0 skipped**

### `research/geology/c10-eclip`

First run, before installing the declared dependency:

- Result: **import error**
- Reason: `ModuleNotFoundError: No module named 'numpy'`

Second run, after `python3 -m pip install -r research/geology/c10-eclip/requirements.txt`:

- Result: **18 passed, 0 failed, 1 skipped**
- Skip reason: `external header snapshot not configured`

## Independent review scope

The new synthetic harness is intentionally synthetic. It checks only the logic of `GA-CE-1` as stated in the pinned report:

- initialization;
- strict target/hash comparisons and equality edge cases;
- target-decrease versus no-decrease behavior;
- absorption after the first deposit;
- at-most-one lifetime issuance; and
- ordinary versus selectively published synthetic sequences.

Command result: **6 passed, 0 failed, 0 skipped**.

It is not presented as a Bitcoin mainnet replay and is not a substitute for the report's general argument.
