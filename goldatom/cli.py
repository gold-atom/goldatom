"""Command-line interface for GoldAtom/0."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .core_rpc import CoreBitcoinView, JsonRpcClient
from .demo import build_simulated_fixture
from .models import GoldAtomBundle
from .verify import VerificationError, verify_bundle


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goldatom",
        description="Experimental verifier-first Proof-Buried Work prototype",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="create and verify a deterministic simulated atom")
    simulate.add_argument("--output", type=Path, help="write the proof bundle to this path")
    simulate.add_argument("--with-transfer", action="store_true", help="include one title transfer")
    simulate.add_argument("--json", action="store_true", help="print the report as JSON")

    verify = subparsers.add_parser("verify", help="verify a proof bundle against Bitcoin Core")
    verify.add_argument("bundle", type=Path)
    verify.add_argument(
        "--rpc-url",
        default=os.environ.get("BITCOIN_RPC_URL", "http://127.0.0.1:18443"),
    )
    verify.add_argument("--rpc-user", default=os.environ.get("BITCOIN_RPC_USER"))
    verify.add_argument("--rpc-password", default=os.environ.get("BITCOIN_RPC_PASSWORD"))
    verify.add_argument("--cookie-file", default=os.environ.get("BITCOIN_RPC_COOKIE"))
    verify.add_argument("--json", action="store_true", help="print the report as JSON")

    inspect = subparsers.add_parser("inspect", help="parse and print a proof bundle without validating it")
    inspect.add_argument("bundle", type=Path)

    return parser


def _print_report(report, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.pretty())


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "simulate":
            fixture = build_simulated_fixture(with_transfer=args.with_transfer)
            report = verify_bundle(fixture.bundle, fixture.view)
            if args.output:
                fixture.bundle.write(args.output)
                print(f"Wrote {args.output}", file=sys.stderr)
            _print_report(report, args.json)
            return 0

        if args.command == "inspect":
            bundle = GoldAtomBundle.read(args.bundle)
            print(bundle.to_json(), end="")
            return 0

        if args.command == "verify":
            if args.cookie_file and (args.rpc_user or args.rpc_password):
                parser.error("use either --cookie-file or --rpc-user/--rpc-password, not both")
            rpc = JsonRpcClient(
                args.rpc_url,
                username=args.rpc_user,
                password=args.rpc_password,
                cookie_file=args.cookie_file,
            )
            bundle = GoldAtomBundle.read(args.bundle)
            report = verify_bundle(bundle, CoreBitcoinView(rpc))
            _print_report(report, args.json)
            return 0
    except (VerificationError, ValueError, OSError, ConnectionError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    return 1
