#!/usr/bin/env python3
"""High-repetition confirmations for the finite-horizon decision rows."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_simulator():
    spec = importlib.util.spec_from_file_location("c10_eclip_sim_confirm", HERE / "simulate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "targeted-confirmations.json")
    parser.add_argument("--repetitions", type=int, default=65_536)
    args = parser.parse_args()
    sim = load_simulator()
    historical = json.loads(sim.HISTORICAL_SUMMARY.read_text())
    raw = json.loads(sim.RAW_SUMMARY.read_text())
    replay = list(csv.DictReader(sim.HISTORICAL_REPLAY.open()))
    rate = sim.historical_like_multiplier(replay)
    start = sim.initial_states(historical, raw)["c10-eclip"]
    current_target = int(historical["live_c10_eclip"]["target"])
    maximum_epochs = sim.HORIZONS[100]
    cases = (
        ("B-historical-like-growth", 0.30),
        ("B-historical-like-growth", 0.50),
        ("E-consensus-retarget-sawtooth", 0.50),
    )
    rows = []
    for index, (scenario, alpha) in enumerate(cases):
        targets = sim.target_path(
            scenario, maximum_epochs, rate["target_multiplier_per_epoch"],
            sim.POW_LIMIT / current_target, start_target=current_target,
        )
        seed = sim.SEED + 700_000_000 + index * 1_000_000
        honest = sim.simulate_path(
            start, targets, alpha, "honest", args.repetitions, seed
        )[100]
        attack = sim.simulate_path(
            start, targets, alpha, "public-lock", args.repetitions, seed
        )[100]
        row = sim.paired_row(
            scenario, "c10-eclip", alpha, "public-lock", 100,
            attack, honest, args.repetitions,
        )
        row["purpose"] = "preselected high-repetition confirmation; not maximum fishing"
        rows.append(row)
    result = {
        "schema": "goldatom-c10-eclip-targeted-confirmations-v1",
        "seed_base": sim.SEED + 700_000_000,
        "repetitions": args.repetitions,
        "preselected_cases": [
            "B/100y/alpha=.30 (largest strict-minority decision row)",
            "B/100y/alpha=.50 (boundary share)",
            "E/100y/alpha=.50 (retarget-bound stress)",
        ],
        "rows": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
