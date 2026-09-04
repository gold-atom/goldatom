#!/usr/bin/env python3
"""Focused raw-record / vanilla-C10 / C10-eclip control comparison."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("policy_sim.py")
POLICY_SIM_BYTES = MODULE_PATH.read_bytes()
POLICY_SIM_SHA256 = hashlib.sha256(POLICY_SIM_BYTES).hexdigest()
CONTROL_SIM_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
SPEC = importlib.util.spec_from_file_location("policy_sim_independent", MODULE_PATH)
assert SPEC and SPEC.loader
sim = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sim
exec(compile(POLICY_SIM_BYTES, str(MODULE_PATH), "exec"), sim.__dict__)


CONTROL_BATCHES = ((10_000, 32), (2_000, 96), (800, 128))
VALUE_OVER_REWARD = 1.0
DISCOUNT = 0.99


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-summary", required=True)
    parser.add_argument("--historical-targets", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()

    historical_summary_path = Path(args.historical_summary)
    historical_targets_path = Path(args.historical_targets)
    historical_summary_bytes = historical_summary_path.read_bytes()
    historical_targets_bytes = historical_targets_path.read_bytes()
    historical = json.loads(historical_summary_bytes.decode("utf-8"))
    targets = [
        int(item)
        for item in json.loads(historical_targets_bytes.decode("utf-8"))["targets"]
    ]
    live_target = int(historical["live_target"])
    min_target = 1.0 / live_target
    max_target = sim.POW_LIMIT / live_target if hasattr(sim, "POW_LIMIT") else int(
        "00000000ffff0000000000000000000000000000000000000000000000000000", 16
    ) / live_target
    historical_ratios = [targets[i + 1] / targets[i] for i in range(len(targets) - 1)]

    control = historical["controls"]
    absolute_states: dict[str, int | tuple[int, int]] = {
        "raw-record": int(control["raw-record"]["live_g2"]),
        "vanilla-c10": (
            int(control["vanilla-c10"]["live_g1"]),
            int(control["vanilla-c10"]["live_g2"]),
        ),
        "c10-eclip": (
            int(historical["live_g1"]),
            int(historical["live_g2"]),
        ),
    }
    states: dict[str, sim.State] = {
        kind: (
            tuple(value / live_target for value in state)
            if isinstance(state, tuple)
            else state / live_target
        )
        for kind, state in absolute_states.items()
    }

    sim.BATCHES = CONTROL_BATCHES
    scenarios = ("A-constant", "D-growth-0.75", "H-adaptive-lambda-half")
    alphas = (0.10, 0.30, 0.50)
    rows: list[dict[str, object]] = []
    for kind, initial_state in states.items():
        for scenario in scenarios:
            for alpha in alphas:
                for model in ("A", "B"):
                    rows.extend(
                        sim.run_configuration(
                            kind=kind,
                            initial_state=initial_state,
                            scenario=scenario,
                            alpha=alpha,
                            model=model,
                            policy="prefer-shallow",
                            initial_target=1.0,
                            min_target=min_target,
                            max_target=max_target,
                            historical_ratios=historical_ratios,
                            value_over_reward=VALUE_OVER_REWARD,
                            discount=DISCOUNT,
                        )
                    )

    sha_scale = (2**256) / live_target
    for row in rows:
        row["extra_sha_trials_mean"] = float(row["extra_sha_trials_mean"]) * sha_scale
    output = {
        "master_seed": sim.MASTER_SEED,
        "master_seed_hex": hex(sim.MASTER_SEED),
        "purpose": "focused same-framework control comparison",
        "continuous_simulation": True,
        "historical_summary_sha256": hashlib.sha256(historical_summary_bytes).hexdigest(),
        "historical_targets_sha256": hashlib.sha256(historical_targets_bytes).hexdigest(),
        "control_sim_sha256": CONTROL_SIM_SHA256,
        "policy_sim_sha256": POLICY_SIM_SHA256,
        "absolute_live_target": live_target,
        "absolute_initial_states": {
            kind: list(state) if isinstance(state, tuple) else state
            for kind, state in absolute_states.items()
        },
        "normalized_initial_target": 1.0,
        "normalized_min_target": min_target,
        "normalized_max_target": max_target,
        "normalized_initial_states": {
            kind: list(state) if isinstance(state, tuple) else state
            for kind, state in states.items()
        },
        "scenarios": list(scenarios),
        "alphas": list(alphas),
        "models": ["A", "B"],
        "policy": "prefer-shallow",
        "trial_schedule": {str(horizon): count for horizon, count in CONTROL_BATCHES},
        "effective_trials_by_checkpoint": {
            str(checkpoint): effective
            for checkpoint in sim.CHECKPOINTS
            if (effective := sum(
                count for horizon, count in sim.BATCHES if horizon >= checkpoint
            ))
        },
        "value_over_reward": VALUE_OVER_REWARD,
        "discount": DISCOUNT,
        "sha_trial_conversion": (
            "for each suppressed candidate simulation accumulates "
            "1/(normalized_target + 1/live_target), then multiplies by "
            "2^256/live_target, exactly yielding 2^256/(absolute_target+1) "
            "expected double-SHA trials"
        ),
        "rows": rows,
    }
    output_path = Path(args.output_json)
    output_csv_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with output_csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "output": str(output_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
