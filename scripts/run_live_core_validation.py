#!/usr/bin/env python3
"""Execute GoldAtom/0 against a fresh, real Bitcoin Core regtest node.

The script discovers or accepts a ``bitcoind`` binary, starts it in the
foreground with an isolated temporary datadir and inbound P2P listening disabled,
runs the unchanged lifecycle,
performs positive and negative verification checks, captures provenance, and
stops the node. The datadir is deleted; the proof bundle and validation logs are
retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from goldatom.core_rpc import JsonRpcClient
from goldatom.models import GoldAtomBundle


KNOWN_LOCAL_BINARIES = (
    Path("/mnt/data/goldatom-third-party/test/work/bitcoin/build/bin/bitcoind"),
    Path("/mnt/data/hwi-bitcoind-extracted/test/work/bitcoin/build/bin/bitcoind"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bitcoind", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "validation" / "live-core",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=ROOT / "examples" / "live-core.goldatom.json",
    )
    parser.add_argument("--wallet", default="goldatom-live-validation")
    return parser.parse_args()


def discover_bitcoind(explicit: Path | None) -> Path | None:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit.expanduser())
    env_binary = os.environ.get("BITCOIND")
    if env_binary:
        candidates.append(Path(env_binary).expanduser())
    in_path = shutil.which("bitcoind")
    if in_path:
        candidates.append(Path(in_path))
    candidates.extend(KNOWN_LOCAL_BINARIES)
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


def free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run(
    command: list[str],
    *,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    timeout: float = 60.0,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if stdout_path is not None:
        stdout_path.write_text(completed.stdout, encoding="utf-8")
    if stderr_path is not None:
        stderr_path.write_text(completed.stderr, encoding="utf-8")
    return completed


def wait_for_rpc(rpc: JsonRpcClient, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"bitcoind exited during startup with status {process.returncode}")
        try:
            rpc.call("getblockchaininfo")
            return
        except Exception as exc:  # startup races are expected
            last_error = exc
            time.sleep(0.05)
    raise RuntimeError(f"Bitcoin Core RPC did not become ready: {last_error}")


def mutate_final_nibble(hex_value: str) -> str:
    return hex_value[:-1] + ("0" if hex_value[-1] != "0" else "1")


def verify_command(
    bundle: Path,
    rpc_url: str,
    rpc_user: str,
    rpc_password: str,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "goldatom",
        "verify",
        str(bundle),
        "--rpc-url",
        rpc_url,
        "--rpc-user",
        rpc_user,
        "--rpc-password",
        rpc_password,
        "--json",
    ]


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    binary = discover_bitcoind(args.bitcoind)
    if binary is None:
        print("LIVE BITCOIN CORE SKIP: no executable bitcoind found")
        return 3

    output_dir = args.output_dir.resolve()
    bundle_path = args.bundle.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    bundle_path.parent.mkdir(parents=True, exist_ok=True)

    version = run([str(binary), "--version"])
    if version.returncode != 0:
        raise RuntimeError(f"bitcoind --version failed: {version.stderr}")
    (output_dir / "version.txt").write_text(version.stdout, encoding="utf-8")

    rpc_port = free_tcp_port()
    rpc_url = f"http://127.0.0.1:{rpc_port}"
    rpc_user = "goldatom-live"
    rpc_password = hashlib.sha256(f"{time.time_ns()}:{rpc_port}".encode()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="goldatom-live-core-") as temporary:
        datadir = Path(temporary) / "node"
        datadir.mkdir()
        node_stdout_path = output_dir / "node-console.log"
        node_stderr_path = output_dir / "node-stderr.log"
        with node_stdout_path.open("w", encoding="utf-8") as node_stdout, node_stderr_path.open(
            "w", encoding="utf-8"
        ) as node_stderr:
            node_command = [
                str(binary),
                "-regtest",
                f"-datadir={datadir}",
                "-server=1",
                "-txindex=1",
                "-fallbackfee=0.0002",
                f"-rpcuser={rpc_user}",
                f"-rpcpassword={rpc_password}",
                f"-rpcport={rpc_port}",
                "-listen=0",
                "-printtoconsole=1",
            ]
            process = subprocess.Popen(
                node_command,
                cwd=ROOT,
                text=True,
                stdout=node_stdout,
                stderr=node_stderr,
            )
            rpc = JsonRpcClient(
                rpc_url,
                username=rpc_user,
                password=rpc_password,
                timeout=10.0,
            )
            try:
                wait_for_rpc(rpc, process)

                lifecycle_command = [
                    sys.executable,
                    str(ROOT / "scripts" / "regtest_demo.py"),
                    "--rpc-url",
                    rpc_url,
                    "--rpc-user",
                    rpc_user,
                    "--rpc-password",
                    rpc_password,
                    "--wallet",
                    args.wallet,
                    "--output",
                    str(bundle_path),
                ]
                lifecycle = run(
                    lifecycle_command,
                    stdout_path=output_dir / "lifecycle.stdout",
                    stderr_path=output_dir / "lifecycle.stderr",
                    timeout=60.0,
                )
                if lifecycle.returncode != 0:
                    raise RuntimeError(
                        f"live lifecycle failed ({lifecycle.returncode}): {lifecycle.stderr}"
                    )

                baseline = run(
                    verify_command(bundle_path, rpc_url, rpc_user, rpc_password),
                    stdout_path=output_dir / "verify-baseline.json",
                    stderr_path=output_dir / "verify-baseline.stderr",
                )
                if baseline.returncode != 0:
                    raise RuntimeError(f"baseline verification failed: {baseline.stderr}")
                baseline_report = json.loads(baseline.stdout)

                node_verification = run(
                    ["node", str(ROOT / "scripts" / "verify_vectors.mjs"), str(bundle_path)],
                    stdout_path=output_dir / "node-pure-protocol.json",
                    stderr_path=output_dir / "node-pure-protocol.stderr",
                )
                if node_verification.returncode != 0:
                    raise RuntimeError(
                        f"Node.js protocol verification failed: {node_verification.stderr}"
                    )

                bundle = GoldAtomBundle.read(bundle_path)
                negative_dir = output_dir / "negative"
                negative_dir.mkdir()

                work_tamper = bundle.to_dict()
                work_tamper["work"]["work_hash_hex"] = mutate_final_nibble(
                    work_tamper["work"]["work_hash_hex"]
                )
                work_tamper_path = negative_dir / "tampered-work-hash.goldatom.json"
                json_write(work_tamper_path, work_tamper)

                challenge_tamper = bundle.to_dict()
                challenge_tamper["work"]["challenge_digest_hex"] = mutate_final_nibble(
                    challenge_tamper["work"]["challenge_digest_hex"]
                )
                challenge_tamper_path = negative_dir / "tampered-challenge.goldatom.json"
                json_write(challenge_tamper_path, challenge_tamper)

                negative_results: dict[str, Any] = {}
                for name, path, expected_fragment in (
                    ("tampered_work", work_tamper_path, "BAD_WORK_HASH"),
                    ("tampered_challenge", challenge_tamper_path, "BAD_CHALLENGE"),
                ):
                    result = run(verify_command(path, rpc_url, rpc_user, rpc_password))
                    negative_results[name] = {
                        "status": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                    if result.returncode != 2 or expected_fragment not in result.stderr:
                        raise RuntimeError(f"negative test {name} did not fail as expected")

                reorg_before = {
                    "blocks": rpc.call("getblockcount"),
                    "bestblockhash": rpc.call("getbestblockhash"),
                }
                rpc.call("invalidateblock", bundle.work.challenge_block_hash)
                reorg_invalidated = {
                    "blocks": rpc.call("getblockcount"),
                    "bestblockhash": rpc.call("getbestblockhash"),
                }
                invalidated_verify = run(
                    verify_command(bundle_path, rpc_url, rpc_user, rpc_password)
                )
                if invalidated_verify.returncode != 2 or "HEADER_LOOKUP" not in invalidated_verify.stderr:
                    raise RuntimeError("reorg invalidation did not invalidate the atom")
                rpc.call("reconsiderblock", bundle.work.challenge_block_hash)
                reorg_restored = {
                    "blocks": rpc.call("getblockcount"),
                    "bestblockhash": rpc.call("getbestblockhash"),
                }
                restored_verify = run(
                    verify_command(bundle_path, rpc_url, rpc_user, rpc_password)
                )
                if restored_verify.returncode != 0:
                    raise RuntimeError("reconsidering the challenge block did not restore validity")

                negative_results["reorg"] = {
                    "before": reorg_before,
                    "invalidated_tip": reorg_invalidated,
                    "invalidated_status": invalidated_verify.returncode,
                    "invalidated_stderr": invalidated_verify.stderr,
                    "restored_tip": reorg_restored,
                    "restored_status": restored_verify.returncode,
                }
                json_write(negative_dir / "results.json", negative_results)

                consensus_primitives = {
                    "claim_verifytxoutproof": rpc.call(
                        "verifytxoutproof", bundle.claim.txout_proof
                    ),
                    "mint_verifytxoutproof": rpc.call(
                        "verifytxoutproof", bundle.mint.txout_proof
                    ),
                    "terminal_utxo": rpc.call(
                        "gettxout", bundle.mint.txid, bundle.mint.title_vout, True
                    ),
                }
                json_write(output_dir / "consensus-primitives.json", consensus_primitives)

                tip_hash = rpc.call("getbestblockhash")
                headers = {
                    "claim": rpc.call("getblockheader", bundle.claim.block_hash, True),
                    "challenge": rpc.call(
                        "getblockheader", bundle.work.challenge_block_hash, True
                    ),
                    "mint": rpc.call("getblockheader", bundle.mint.block_hash, True),
                    "tip": rpc.call("getblockheader", tip_hash, True),
                }
                network_info = rpc.call("getnetworkinfo")
                blockchain_info = rpc.call("getblockchaininfo")
                wallet_info = rpc.child(f"wallet/{args.wallet}").call("getwalletinfo")

                short_commit_match = re.search(r"-([0-9a-f]{12})\b", version.stdout)
                provenance = {
                    "validation_date_utc": time.strftime("%Y-%m-%d", time.gmtime()),
                    "environment": {
                        "platform": platform.platform(),
                        "python": sys.version,
                        "node": shutil.which("node"),
                    },
                    "bitcoin_core": {
                        "binary_path_used": str(binary),
                        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                        "version_output": version.stdout.splitlines(),
                        "source_commit_prefix": (
                            short_commit_match.group(1) if short_commit_match else None
                        ),
                        "release_status": (
                            "pre-release build"
                            if "pre-release" in json.dumps(blockchain_info, default=str).lower()
                            or ".99." in version.stdout
                            else "release build"
                        ),
                    },
                    "node": {
                        "blockchain_info": blockchain_info,
                        "network_info": network_info,
                        "wallet_info": wallet_info,
                    },
                    "atom": {
                        "bundle_path": str(bundle_path.relative_to(ROOT)),
                        "bundle_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest(),
                        "report": baseline_report,
                        "claim_outpoint": str(bundle.claim.outpoint),
                        "work_hash": bundle.work.work_hash_hex,
                        "block_headers": headers,
                    },
                    "negative_checks": {
                        "tampered_work_rejected": True,
                        "tampered_challenge_rejected": True,
                        "challenge_reorg_rejected": True,
                        "reconsider_restored_validity": True,
                    },
                }
                json_write(output_dir / "provenance.json", provenance)

                summary = {
                    "kind": "live-bitcoin-core-regtest",
                    "status": "pass",
                    "binary": str(binary),
                    "version_first_line": version.stdout.splitlines()[0],
                    "binary_sha256": provenance["bitcoin_core"]["binary_sha256"],
                    "atom_id": baseline_report["atom_id"],
                    "claim_height": baseline_report["claim_height"],
                    "challenge_height": baseline_report["challenge_height"],
                    "mint_height": baseline_report["mint_height"],
                    "tip_height": baseline_report["as_of_tip_height"],
                    "bundle": str(bundle_path),
                    "output_dir": str(output_dir),
                    "negative_checks": provenance["negative_checks"],
                    "warning": (
                        "Genuine Bitcoin Core execution, but this binary is a pre-release "
                        "master build rather than the official 31.1 release binary."
                    ),
                }
                json_write(output_dir / "summary.json", summary)

            finally:
                try:
                    rpc.call("stop")
                except Exception:
                    process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

    summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    print("LIVE BITCOIN CORE REGTEST PASS")
    print(f"Binary:             {summary['binary']}")
    print(f"Version:            {summary['version_first_line']}")
    print(f"Binary SHA-256:      {summary['binary_sha256']}")
    print(f"Atom ID:            {summary['atom_id']}")
    print(f"Heights:            claim {summary['claim_height']} -> challenge {summary['challenge_height']} -> mint {summary['mint_height']} -> tip {summary['tip_height']}")
    print("Negative checks:    tamper PASS; reorg PASS; restoration PASS")
    print(f"Proof bundle:       {summary['bundle']}")
    print(f"Validation records: {summary['output_dir']}")
    print(f"WARNING:            {summary['warning']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"live Core validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
