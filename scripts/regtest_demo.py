#!/usr/bin/env python3
"""Create a real GoldAtom/0 lifecycle on a running Bitcoin Core regtest node.

This script never permits mainnet or public test networks. It creates:
  claim transaction -> future challenge block -> local work -> mint transaction
  -> one burial block -> portable proof bundle -> independent verifier pass.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from goldatom.core_rpc import CoreBitcoinView, JsonRpcClient, RpcError
from goldatom.encoding import marker_payload, marker_script
from goldatom.models import ClaimRecord, GoldAtomBundle, MintRecord, Outpoint, WorkRecord
from goldatom.profiles import ALGORITHM_SHA256D_80_V0, get_profile
from goldatom.protocol import claim_commitment, derive_challenge, mine_work, mint_commitment
from goldatom.verify import verify_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default="http://127.0.0.1:18443")
    parser.add_argument("--rpc-user")
    parser.add_argument("--rpc-password")
    parser.add_argument("--cookie-file")
    parser.add_argument("--wallet", default="goldatom-demo")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "examples" / "regtest.goldatom.json",
    )
    return parser.parse_args()


def ensure_wallet(base: JsonRpcClient, name: str) -> JsonRpcClient:
    loaded = set(base.call("listwallets"))
    if name not in loaded:
        available = {item["name"] for item in base.call("listwalletdir")["wallets"]}
        if name in available:
            base.call("loadwallet", name)
        else:
            base.call("createwallet", name)
    return base.child(f"wallet/{quote(name, safe='')}")


def mine_blocks(wallet: JsonRpcClient, count: int) -> list[str]:
    address = wallet.call("getnewaddress", "goldatom-mining", "bech32m")
    return wallet.call("generatetoaddress", count, address)


def assert_output(decoded: dict, index: int, script_hex: str, role: str) -> None:
    try:
        actual = decoded["vout"][index]["scriptPubKey"]["hex"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"{role} output {index} missing after transaction construction") from exc
    if actual != script_hex:
        raise RuntimeError(f"{role} output order changed: expected {script_hex}, got {actual}")


def main() -> int:
    args = parse_args()
    if args.cookie_file and (args.rpc_user or args.rpc_password):
        raise SystemExit("Use cookie authentication or username/password, not both.")
    base = JsonRpcClient(
        args.rpc_url,
        username=args.rpc_user,
        password=args.rpc_password,
        cookie_file=args.cookie_file,
    )
    chain_info = base.call("getblockchaininfo")
    if chain_info["chain"] != "regtest":
        raise SystemExit(
            f"Refusing to run: expected regtest, Bitcoin Core reports {chain_info['chain']!r}."
        )

    wallet = ensure_wallet(base, args.wallet)
    if Decimal(str(wallet.call("getbalance"))) < Decimal("0.01"):
        print("Mining 101 regtest blocks to create mature wallet funds...", file=sys.stderr)
        mine_blocks(wallet, 101)

    profile = get_profile("goldatom-regtest-v0")
    target_hex = profile.maximum_target_hex

    # ----- Claim -----
    claim_address = wallet.call("getnewaddress", "goldatom-claim", "bech32m")
    claim_seal_script = wallet.call("getaddressinfo", claim_address)["scriptPubKey"]
    claim_digest = claim_commitment(
        profile,
        seal_vout=0,
        seal_script_hex=claim_seal_script,
        algorithm=ALGORITHM_SHA256D_80_V0,
        target_hex=target_hex,
    )
    claim_marker_script = marker_script("claim", claim_digest).hex()
    unsigned_claim = wallet.call(
        "createrawtransaction",
        [],
        [
            {claim_address: "0.00100000"},
            {"data": marker_payload("claim", claim_digest).hex()},
        ],
    )
    funded_claim = wallet.call(
        "fundrawtransaction",
        unsigned_claim,
        {"changePosition": 2, "fee_rate": "1.0"},
    )
    signed_claim = wallet.call("signrawtransactionwithwallet", funded_claim["hex"])
    if signed_claim.get("complete") is not True:
        raise RuntimeError("wallet did not completely sign the claim transaction")
    decoded_claim = wallet.call("decoderawtransaction", signed_claim["hex"])
    assert_output(decoded_claim, 0, claim_seal_script, "claim seal")
    assert_output(decoded_claim, 1, claim_marker_script, "claim marker")
    claim_txid = wallet.call("sendrawtransaction", signed_claim["hex"])
    mine_blocks(wallet, 1)
    claim_wallet_tx = wallet.call("gettransaction", claim_txid)
    claim_block_hash = claim_wallet_tx["blockhash"]
    claim_header = base.call("getblockheader", claim_block_hash, True)
    claim_height = int(claim_header["height"])
    claim_outpoint = Outpoint(claim_txid, 0)
    claim_proof = base.call("gettxoutproof", [claim_txid], claim_block_hash)
    print(f"Claim confirmed at height {claim_height}: {claim_outpoint}", file=sys.stderr)

    # ----- Future Bitcoin challenge -----
    expected_challenge_height = claim_height + profile.challenge_delay
    current_height = int(base.call("getblockcount"))
    if current_height < expected_challenge_height:
        mine_blocks(wallet, expected_challenge_height - current_height)
    challenge_block_hash = base.call("getblockhash", expected_challenge_height)
    challenge_digest = derive_challenge(
        profile,
        claim_outpoint=claim_outpoint,
        claim_block_hash=claim_block_hash,
        claim_commitment_digest=claim_digest,
        challenge_block_hash=challenge_block_hash,
    )
    print(
        f"Challenge fixed by block {expected_challenge_height}: {challenge_block_hash}",
        file=sys.stderr,
    )

    # ----- Local Bit-Gold-style work -----
    mined = mine_work(
        challenge_digest=challenge_digest,
        claim_commitment_digest=claim_digest,
        target=profile.maximum_target,
        max_attempts=1_000_000,
    )
    print(
        f"Local proof found after {mined.attempts} attempts: {mined.work_hash.hex()}",
        file=sys.stderr,
    )

    # ----- Mint and title seal -----
    title_address = wallet.call("getnewaddress", "goldatom-title", "bech32m")
    title_script = wallet.call("getaddressinfo", title_address)["scriptPubKey"]
    mint_digest = mint_commitment(
        profile,
        claim_outpoint=claim_outpoint,
        challenge_digest=challenge_digest,
        extra_nonce=mined.extra_nonce,
        nonce=mined.nonce,
        work_hash=mined.work_hash,
        title_vout=0,
        title_script_hex=title_script,
    )
    mint_marker_script = marker_script("mint", mint_digest).hex()
    unsigned_mint = wallet.call(
        "createrawtransaction",
        [{"txid": claim_txid, "vout": 0}],
        [
            {title_address: "0.00098000"},
            {"data": marker_payload("mint", mint_digest).hex()},
        ],
    )
    signed_mint = wallet.call("signrawtransactionwithwallet", unsigned_mint)
    if signed_mint.get("complete") is not True:
        raise RuntimeError("wallet did not completely sign the mint transaction")
    decoded_mint = wallet.call("decoderawtransaction", signed_mint["hex"])
    assert_output(decoded_mint, 0, title_script, "title")
    assert_output(decoded_mint, 1, mint_marker_script, "mint marker")
    acceptance = base.call("testmempoolaccept", [signed_mint["hex"]])
    if not acceptance or acceptance[0].get("allowed") is not True:
        raise RuntimeError(f"Bitcoin Core rejected mint transaction: {acceptance}")
    mint_txid = wallet.call("sendrawtransaction", signed_mint["hex"])
    mine_blocks(wallet, 1)
    mint_wallet_tx = wallet.call("gettransaction", mint_txid)
    mint_block_hash = mint_wallet_tx["blockhash"]
    mint_header = base.call("getblockheader", mint_block_hash, True)
    mint_height = int(mint_header["height"])
    mint_proof = base.call("gettxoutproof", [mint_txid], mint_block_hash)

    # One block of post-mint burial is required by the regtest profile.
    mine_blocks(wallet, profile.minimum_burial_blocks)

    bundle = GoldAtomBundle(
        profile=profile.id,
        claim=ClaimRecord(
            outpoint=claim_outpoint,
            block_hash=claim_block_hash,
            height=claim_height,
            seal_script_hex=claim_seal_script,
            algorithm=ALGORITHM_SHA256D_80_V0,
            target_hex=target_hex,
            commitment_hex=claim_digest.hex(),
            txout_proof=claim_proof,
        ),
        work=WorkRecord(
            challenge_height=expected_challenge_height,
            challenge_block_hash=challenge_block_hash,
            challenge_digest_hex=challenge_digest.hex(),
            extra_nonce=mined.extra_nonce,
            nonce=mined.nonce,
            work_hash_hex=mined.work_hash.hex(),
        ),
        mint=MintRecord(
            txid=mint_txid,
            block_hash=mint_block_hash,
            height=mint_height,
            txout_proof=mint_proof,
            title_vout=0,
            title_script_hex=title_script,
            commitment_hex=mint_digest.hex(),
        ),
    )
    bundle.write(args.output)
    report = verify_bundle(bundle, CoreBitcoinView(base))
    print(report.pretty())
    print(f"\nProof bundle written to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RpcError, OSError, ConnectionError, RuntimeError, ValueError) as exc:
        print(f"regtest demo failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
