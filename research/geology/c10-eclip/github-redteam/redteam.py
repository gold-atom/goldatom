#!/usr/bin/env python3
"""Independent C10-eclip red-team primitives and historical replay.

This module deliberately does not import the pre-existing C10-eclip research
implementation or any of its result files.  It consumes raw 80-byte Bitcoin
headers and implements the transition given in the red-team brief directly.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import struct
from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Iterable, Iterator, Sequence


W = 2016
POW_LIMIT = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

# Consecutive decimal rationals known to bracket e.  The interval width is
# 1e-191, substantially narrower than needed to certify 256-bit ceilings.
_E_DIGITS = (
    "271828182845904523536028747135266249775724709369995957496696762772407663035354759"
    "457138217852516642742746639193200305992181741359662904357290033429526059563073813"
    "232862794349076323382988075319"
)
E_DEN = 10 ** (len(_E_DIGITS) - 1)
E_LO_NUM = int(_E_DIGITS)
E_HI_NUM = E_LO_NUM + 1


def ceil_div(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


def ceil_div_e(value: int) -> int:
    """Return ceil(value/e), certified by a rational interval around e."""

    lo_candidate = ceil_div(value * E_DEN, E_HI_NUM)
    hi_candidate = ceil_div(value * E_DEN, E_LO_NUM)
    if lo_candidate != hi_candidate:
        raise ArithmeticError(
            f"ceil(value/e) ambiguous in the registered e interval: {value}"
        )
    return lo_candidate


def init_state(a: int, b: int) -> tuple[int, int]:
    g2 = max(a, b)
    q = min(a, b)
    g1 = max(q, ceil_div_e(g2))
    assert 0 <= g1 <= g2
    assert g2 * E_DEN <= g1 * E_HI_NUM
    return g1, g2


def transition(state: tuple[int, int], epoch_minimum: int) -> tuple[bool, str, tuple[int, int]]:
    """Apply the deposit-first C10-eclip transition."""

    g1, g2 = state
    assert 0 <= g1 <= g2
    assert g2 * E_DEN <= g1 * E_HI_NUM
    deposit = epoch_minimum < g2
    if epoch_minimum < g1:
        post = (max(epoch_minimum, ceil_div_e(g1)), g1)
        kind = "unique-min"
    elif epoch_minimum < g2:
        post = (g1, epoch_minimum)
        kind = "new-second"
    else:
        post = state
        kind = "neither"
    assert deposit == (kind != "neither")
    assert 0 <= post[0] <= post[1]
    assert post[1] * E_DEN <= post[0] * E_HI_NUM
    return deposit, kind, post


def decode_compact(bits: int) -> int:
    exponent = bits >> 24
    mantissa = bits & 0x007FFFFF
    if bits & 0x00800000:
        raise ValueError(f"negative compact target: {bits:08x}")
    if exponent <= 3:
        return mantissa >> (8 * (3 - exponent))
    return mantissa << (8 * (exponent - 3))


def encode_compact(target: int) -> int:
    if target <= 0:
        return 0
    size = (target.bit_length() + 7) // 8
    if size <= 3:
        compact = target << (8 * (3 - size))
    else:
        compact = target >> (8 * (size - 3))
    if compact & 0x00800000:
        compact >>= 8
        size += 1
    return compact | (size << 24)


def sha256d(header: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(header).digest()).digest()


@dataclass(frozen=True)
class Header:
    height: int
    raw: bytes
    digest: bytes
    hash_int: int
    hash_hex: str
    prev_digest: bytes
    timestamp: int
    bits: int
    target: int


@dataclass(frozen=True)
class Epoch:
    index: int
    target: int
    bits: int
    minimum: int
    minimum_height: int
    hashes: tuple[int, ...]
    hash_hexes: tuple[str, ...]


def iter_verified_headers(path: Path) -> Iterator[Header]:
    previous_digest: bytes | None = None
    with path.open("rb") as stream:
        height = 0
        while raw := stream.read(80):
            if len(raw) != 80:
                raise ValueError(f"truncated header at height {height}: {len(raw)} bytes")
            version, prev_digest, merkle, timestamp, bits, nonce = struct.unpack(
                "<I32s32sIII", raw
            )
            del version, merkle, nonce
            digest = sha256d(raw)
            hash_int = int.from_bytes(digest, "little", signed=False)
            target = decode_compact(bits)
            if height == 0:
                if prev_digest != bytes(32):
                    raise ValueError("genesis predecessor is not zero")
            elif prev_digest != previous_digest:
                raise ValueError(f"predecessor mismatch at height {height}")
            if not (0 < target <= POW_LIMIT):
                raise ValueError(f"target out of range at height {height}")
            if hash_int > target:
                raise ValueError(f"invalid proof of work at height {height}")
            yield Header(
                height=height,
                raw=raw,
                digest=digest,
                hash_int=hash_int,
                hash_hex=digest[::-1].hex(),
                prev_digest=prev_digest,
                timestamp=timestamp,
                bits=bits,
                target=target,
            )
            previous_digest = digest
            height += 1
        if stream.read(1):
            raise AssertionError("unreachable trailing data check")


def load_and_verify(path: Path) -> tuple[list[Header], list[Epoch], dict[str, object]]:
    headers = list(iter_verified_headers(path))
    if not headers:
        raise ValueError("empty header file")

    # Verify constant nBits inside every period (including the incomplete tail).
    for start in range(0, len(headers), W):
        period = headers[start : min(start + W, len(headers))]
        expected_bits = period[0].bits
        if any(header.bits != expected_bits for header in period):
            raise ValueError(f"nBits changes inside period {start // W}")

    # Verify every available mainnet retarget from the raw timestamps and the
    # preceding compact target, including compact-format rounding.
    retargets_checked = 0
    for start in range(W, len(headers), W):
        previous_first = headers[start - W]
        previous_last = headers[start - 1]
        elapsed = previous_last.timestamp - previous_first.timestamp
        elapsed = max(14 * 24 * 60 * 60 // 4, min(elapsed, 14 * 24 * 60 * 60 * 4))
        next_target = min(POW_LIMIT, previous_last.target * elapsed // (14 * 24 * 60 * 60))
        expected_bits = encode_compact(next_target)
        if headers[start].bits != expected_bits:
            raise ValueError(
                f"retarget mismatch at height {start}: "
                f"{headers[start].bits:08x} != {expected_bits:08x}"
            )
        retargets_checked += 1

    completed = len(headers) // W
    epochs: list[Epoch] = []
    for index in range(completed):
        period = headers[index * W : (index + 1) * W]
        minimum_header = min(period, key=lambda item: item.hash_int)
        epochs.append(
            Epoch(
                index=index,
                target=period[0].target,
                bits=period[0].bits,
                minimum=minimum_header.hash_int,
                minimum_height=minimum_header.height,
                hashes=tuple(header.hash_int for header in period),
                hash_hexes=tuple(header.hash_hex for header in period),
            )
        )

    metadata = {
        "input": str(path),
        "input_bytes": path.stat().st_size,
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "header_count": len(headers),
        "tip_height": headers[-1].height,
        "tip_hash": headers[-1].hash_hex,
        "completed_epochs": completed,
        "incomplete_epoch": len(headers) // W,
        "incomplete_epoch_headers": len(headers) % W,
        "retargets_checked": retargets_checked,
    }
    return headers, epochs, metadata


def exact_probabilities(g2: int, target: int) -> dict[str, str | int]:
    """Task-specified continuous-ratio binomial probabilities, at high precision."""

    with localcontext() as context:
        # A 256-bit endpoint can make P(K>=2) about 1e-148.  Directly
        # subtracting P(K=0) and P(K=1) from one at ordinary decimal precision
        # can therefore produce a negative answer.  Sum the binomial tail by a
        # stable recurrence and retain ample guard precision for the Poisson
        # cross-checks as well.
        context.prec = 300
        q = min(Decimal(1), Decimal(g2) / Decimal(target))
        one_minus_q = Decimal(1) - q
        if q == 1:
            p_ge_1 = Decimal(1)
            p_ge_2 = Decimal(1)
        else:
            # 1-(1-q)^W = q * sum_{i=0}^{W-1}(1-q)^i.
            geometric = Decimal(0)
            power = Decimal(1)
            for _ in range(W):
                geometric += power
                power *= one_minus_q
            p_ge_1 = q * geometric

            # Start at P(K=2), then advance P(K=k) by its exact ratio.
            term = Decimal(W * (W - 1) // 2) * q * q * (one_minus_q ** (W - 2))
            p_ge_2 = term
            for k in range(2, W):
                term *= Decimal(W - k) * q
                term /= Decimal(k + 1) * one_minus_q
                p_ge_2 += term
        conditional = p_ge_2 / p_ge_1 if p_ge_1 else Decimal(0)
        poisson_ge_1 = Decimal(1) - (-Decimal(W) * q).exp()
        poisson_ge_2 = Decimal(1) - (-Decimal(W) * q).exp() * (Decimal(1) + Decimal(W) * q)
        endpoint_q = min(Decimal(1), Decimal(g2) / Decimal(target + 1))
        return {
            "q": format(q, ".80g"),
            "lambda": format(Decimal(W) * q, ".80g"),
            "p_k_ge_1": format(p_ge_1, ".80g"),
            "p_k_ge_2": format(p_ge_2, ".80g"),
            "p_k_ge_2_given_ge_1": format(conditional, ".80g"),
            "poisson_p_k_ge_1": format(poisson_ge_1, ".80g"),
            "poisson_p_k_ge_2": format(poisson_ge_2, ".80g"),
            "integer_endpoint_q": format(endpoint_q, ".80g"),
            "integer_endpoint_convention": "H uniform on integers 0..T; deposit H<G2",
        }


def replay(epochs: Sequence[Epoch], next_target: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    if len(epochs) < 2:
        raise ValueError("at least two completed epochs are required")
    rows: list[dict[str, object]] = []
    pending = [epochs[0].minimum]
    rows.append(
        {
            "epoch": 0,
            "target": str(epochs[0].target),
            "epoch_minimum": str(epochs[0].minimum),
            "epoch_minimum_height": epochs[0].minimum_height,
            "pre_g1": None,
            "pre_g2": None,
            "post_g1": None,
            "post_g2": None,
            "transition": "initialize-a",
            "deposit": None,
            "ratio_g2_g1": None,
            "q": None,
            "lambda": None,
            "canonical_k": None,
            "qualifier_hashes": [],
            "qualifier_heights": [],
            "ownership": "unspecified",
            "network_selection_opportunity": None,
        }
    )
    state = init_state(pending[0], epochs[1].minimum)
    initial_state = state
    rows.append(
        {
            "epoch": 1,
            "target": str(epochs[1].target),
            "epoch_minimum": str(epochs[1].minimum),
            "epoch_minimum_height": epochs[1].minimum_height,
            "pre_g1": None,
            "pre_g2": None,
            "post_g1": str(state[0]),
            "post_g2": str(state[1]),
            "transition": "initialize-b-clipped",
            "deposit": None,
            "ratio_g2_g1": format(Decimal(state[1]) / Decimal(state[0]), ".40g"),
            "q": None,
            "lambda": None,
            "canonical_k": None,
            "qualifier_hashes": [],
            "qualifier_heights": [],
            "ownership": "unspecified",
            "network_selection_opportunity": None,
        }
    )

    counts = {"k0": 0, "k1": 0, "k_ge_2": 0}
    lambdas: list[float] = []
    last_k_ge_2: int | None = None
    for epoch in epochs[2:]:
        g1, g2 = state
        qualifiers = [
            (value, epoch.index * W + offset, epoch.hash_hexes[offset])
            for offset, value in enumerate(epoch.hashes)
            if value < g2
        ]
        qualifiers.sort()
        k = len(qualifiers)
        counts["k0" if k == 0 else "k1" if k == 1 else "k_ge_2"] += 1
        if k >= 2:
            last_k_ge_2 = epoch.index
        deposit, kind, post = transition(state, epoch.minimum)
        q = min(1.0, g2 / epoch.target)
        lam = W * q
        lambdas.append(lam)
        rows.append(
            {
                "epoch": epoch.index,
                "target": str(epoch.target),
                "epoch_minimum": str(epoch.minimum),
                "epoch_minimum_height": epoch.minimum_height,
                "pre_g1": str(g1),
                "pre_g2": str(g2),
                "post_g1": str(post[0]),
                "post_g2": str(post[1]),
                "transition": kind,
                "deposit": deposit,
                "ratio_g2_g1": format(Decimal(post[1]) / Decimal(post[0]), ".40g"),
                "q": format(Decimal(g2) / Decimal(epoch.target), ".40g"),
                "lambda": format(Decimal(W) * Decimal(g2) / Decimal(epoch.target), ".40g"),
                "canonical_k": k,
                "qualifier_hashes": [item[2] for item in qualifiers],
                "qualifier_heights": [item[1] for item in qualifiers],
                "ownership": "unspecified",
                "network_selection_opportunity": k >= 2,
            }
        )
        state = post

    sorted_lambdas = sorted(lambdas)

    def quantile(probability: float) -> float:
        if not sorted_lambdas:
            return math.nan
        position = (len(sorted_lambdas) - 1) * probability
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return sorted_lambdas[lower]
        weight = position - lower
        return sorted_lambdas[lower] * (1 - weight) + sorted_lambdas[upper] * weight

    live = exact_probabilities(state[1], next_target)
    summary: dict[str, object] = {
        "simulation_initial_g1": str(initial_state[0]),
        "simulation_initial_g2": str(initial_state[1]),
        "simulation_first_target": str(epochs[2].target),
        "live_g1": str(state[0]),
        "live_g2": str(state[1]),
        "live_target": str(next_target),
        "live_probabilities": live,
        "historical_lambda": {
            "median": quantile(0.50),
            "p90": quantile(0.90),
            "p95": quantile(0.95),
            "p99": quantile(0.99),
            "maximum": max(lambdas),
            "sample_count": len(lambdas),
        },
        "qualifier_epoch_counts": counts,
        "last_k_ge_2_epoch": last_k_ge_2,
    }
    return rows, summary


def historical_prefer_second_forks(
    epochs: Sequence[Epoch], rows: Sequence[dict[str, object]]
) -> list[dict[str, object]]:
    """Delete the canonical epoch minimum, retain the second minimum, and replay."""

    forks: list[dict[str, object]] = []
    for row in rows[2:]:
        if not row["network_selection_opportunity"]:
            continue
        index = int(row["epoch"])
        pre = (int(row["pre_g1"]), int(row["pre_g2"]))
        epoch = epochs[index]
        qualifiers = sorted(value for value in epoch.hashes if value < pre[1])
        honest_min = qualifiers[0]
        attacked_min = qualifiers[1]
        honest_deposit, _, honest_state = transition(pre, honest_min)
        attacked_deposit, _, attacked_state = transition(pre, attacked_min)
        assert honest_deposit and attacked_deposit
        honest_post = honest_state
        attacked_post = attacked_state
        cumulative_delta = 0
        maximum_delta = 0
        minimum_delta = 0
        divergence_epochs = 0
        reconverged_at: int | None = index if honest_state == attacked_state else None
        for future in epochs[index + 1 :]:
            honest_dep, _, honest_state = transition(honest_state, future.minimum)
            attacked_dep, _, attacked_state = transition(attacked_state, future.minimum)
            cumulative_delta += int(attacked_dep) - int(honest_dep)
            maximum_delta = max(maximum_delta, cumulative_delta)
            minimum_delta = min(minimum_delta, cumulative_delta)
            if honest_state != attacked_state:
                divergence_epochs += 1
            elif reconverged_at is None:
                reconverged_at = future.index
        forks.append(
            {
                "epoch": index,
                "target": str(epoch.target),
                "pre_g1": str(pre[0]),
                "pre_g2": str(pre[1]),
                "honest_minimum": str(honest_min),
                "attacked_second_minimum": str(attacked_min),
                "honest_post_g1": str(honest_post[0]),
                "honest_post_g2": str(honest_post[1]),
                "attacked_post_g1": str(attacked_post[0]),
                "attacked_post_g2": str(attacked_post[1]),
                "future_deposit_delta": cumulative_delta,
                "maximum_prefix_delta": maximum_delta,
                "minimum_prefix_delta": minimum_delta,
                "divergence_epochs": divergence_epochs,
                "reconverged_at_epoch": reconverged_at,
                "reconvergence_time": None if reconverged_at is None else reconverged_at - index,
                "same_terminal_state": honest_state == attacked_state,
                "honest_terminal_g1": str(honest_state[0]),
                "honest_terminal_g2": str(honest_state[1]),
                "attacked_terminal_g1": str(attacked_state[0]),
                "attacked_terminal_g2": str(attacked_state[1]),
            }
        )
    return forks


def replay_control(epochs: Sequence[Epoch], kind: str, next_target: int) -> dict[str, object]:
    """Replay raw-record or ordinary (unclipped) two-record control geology."""

    if kind == "raw-record":
        state: int | tuple[int, int] = epochs[0].minimum
        start = 1
    elif kind == "vanilla-c10":
        state = tuple(sorted((epochs[0].minimum, epochs[1].minimum)))
        start = 2
    else:
        raise ValueError(kind)
    deposits = 0
    transition_counts = {"unique-min": 0, "new-second": 0, "neither": 0}
    lambda_history: list[float] = []
    for epoch in epochs[start:]:
        if kind == "raw-record":
            assert isinstance(state, int)
            lambda_history.append(W * min(1.0, state / epoch.target))
            if epoch.minimum < state:
                deposits += 1
                state = epoch.minimum
                transition_counts["unique-min"] += 1
            else:
                transition_counts["neither"] += 1
        else:
            assert isinstance(state, tuple)
            g1, g2 = state
            lambda_history.append(W * min(1.0, g2 / epoch.target))
            if epoch.minimum < g1:
                deposits += 1
                state = (epoch.minimum, g1)
                transition_counts["unique-min"] += 1
            elif epoch.minimum < g2:
                deposits += 1
                state = (g1, epoch.minimum)
                transition_counts["new-second"] += 1
            else:
                transition_counts["neither"] += 1
    if kind == "raw-record":
        assert isinstance(state, int)
        live_g1: str | None = None
        live_g2 = str(state)
    else:
        assert isinstance(state, tuple)
        live_g1 = str(state[0])
        live_g2 = str(state[1])
    live_lambda = W * int(live_g2) / next_target
    return {
        "kind": kind,
        "deposits_after_initialization": deposits,
        "live_g1": live_g1,
        "live_g2": live_g2,
        "live_target": str(next_target),
        "live_lambda": live_lambda,
        "historical_lambda_maximum": max(lambda_history),
        "transition_counts": transition_counts,
    }


def write_replay_csv(path: Path, rows: Sequence[dict[str, object]]) -> None:
    fields = [
        "epoch",
        "target",
        "epoch_minimum",
        "epoch_minimum_height",
        "pre_g1",
        "pre_g2",
        "post_g1",
        "post_g2",
        "transition",
        "deposit",
        "ratio_g2_g1",
        "q",
        "lambda",
        "canonical_k",
        "qualifier_hashes",
        "qualifier_heights",
        "ownership",
        "network_selection_opportunity",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            output = dict(row)
            output["qualifier_hashes"] = ";".join(output["qualifier_hashes"])
            output["qualifier_heights"] = ";".join(map(str, output["qualifier_heights"]))
            writer.writerow(output)


def historical_command(args: argparse.Namespace) -> None:
    input_path = Path(args.headers).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    headers, epochs, verification = load_and_verify(input_path)
    next_target = headers[len(epochs) * W].target if len(headers) > len(epochs) * W else epochs[-1].target
    rows, summary = replay(epochs, next_target)
    forks = historical_prefer_second_forks(epochs, rows)
    summary["verification"] = verification
    summary["historical_prefer_second_forks"] = forks
    summary["controls"] = {
        "raw-record": replay_control(epochs, "raw-record", next_target),
        "vanilla-c10": replay_control(epochs, "vanilla-c10", next_target),
    }
    (output_dir / "historical-targets.json").write_text(
        json.dumps(
            {
                "targets": [str(epoch.target) for epoch in epochs],
                "bits": [f"{epoch.bits:08x}" for epoch in epochs],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_replay_csv(output_dir / "historical-replay.csv", rows)
    (output_dir / "historical-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    historical = subparsers.add_parser("historical", help="verify headers and replay C10-eclip")
    historical.add_argument("--headers", required=True)
    historical.add_argument("--output", required=True)
    historical.set_defaults(function=historical_command)
    return result


def main() -> None:
    args = parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
