"""Deterministic simulated GoldAtom used as an executable test vector."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass

from .encoding import marker_script, tagged_hash
from .models import ClaimRecord, GoldAtomBundle, MintRecord, Outpoint, TitleTransition, WorkRecord
from .profiles import ALGORITHM_SHA256D_80_V0, get_profile
from .protocol import (
    atom_id,
    claim_commitment,
    derive_challenge,
    mine_work,
    mint_commitment,
    transfer_commitment,
)
from .testing import FakeBitcoinView
from .view import BitcoinTransaction, BlockHeader, TxInput, TxOutput, UTXO


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _fake_txid(label: str, inputs: tuple[TxInput, ...], outputs: tuple[TxOutput, ...]) -> str:
    data = {
        "label": label,
        "inputs": [str(item.previous_outpoint) for item in inputs],
        "outputs": [
            {"value_sats": output.value_sats, "script": output.script_pubkey_hex}
            for output in outputs
        ],
    }
    return tagged_hash(
        "GoldAtom/simulated-txid/v0",
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hex()


def _p2tr_script(label: str) -> str:
    # OP_1 PUSH32 <deterministic x-only key-shaped bytes>.
    return (b"\x51\x20" + hashlib.sha256(label.encode("utf-8")).digest()).hex()


@dataclass(slots=True)
class SimulatedFixture:
    bundle: GoldAtomBundle
    view: FakeBitcoinView

    def clone(self) -> "SimulatedFixture":
        return copy.deepcopy(self)


def build_simulated_fixture(*, with_transfer: bool = False) -> SimulatedFixture:
    profile = get_profile("goldatom-sim-v0")
    target_hex = profile.maximum_target_hex
    claim_height = 100
    challenge_height = claim_height + profile.challenge_delay
    mint_height = challenge_height + 1
    transfer_height = mint_height + 1
    tip_height = transfer_height + 1 if with_transfer else mint_height + 1

    view = FakeBitcoinView(network=profile.network)
    headers: dict[int, BlockHeader] = {}
    for height in range(claim_height, tip_height + 1):
        header = BlockHeader(
            hash=_hash(f"sim-block-{height}"),
            height=height,
            confirmations=tip_height - height + 1,
            chainwork=1_000_000 + (height - claim_height + 1) * 10_000,
            time=1_800_000_000 + height * 600,
        )
        headers[height] = header
        view.add_header(header, tip=height == tip_height)

    claim_seal_script = _p2tr_script("claim-seal")
    claim_digest = claim_commitment(
        profile,
        seal_vout=0,
        seal_script_hex=claim_seal_script,
        algorithm=ALGORITHM_SHA256D_80_V0,
        target_hex=target_hex,
    )
    claim_outputs = (
        TxOutput(100_000, claim_seal_script),
        TxOutput(0, marker_script("claim", claim_digest).hex()),
    )
    claim_txid = _fake_txid("claim", (), claim_outputs)
    claim_outpoint = Outpoint(claim_txid, 0)
    claim_proof = _hash("claim-proof")
    claim_tx = BitcoinTransaction(
        txid=claim_txid,
        block_hash=headers[claim_height].hash,
        height=claim_height,
        inputs=(),
        outputs=claim_outputs,
    )
    view.add_transaction(claim_tx, claim_proof)

    challenge_digest = derive_challenge(
        profile,
        claim_outpoint=claim_outpoint,
        claim_block_hash=headers[claim_height].hash,
        claim_commitment_digest=claim_digest,
        challenge_block_hash=headers[challenge_height].hash,
    )
    mined = mine_work(
        challenge_digest=challenge_digest,
        claim_commitment_digest=claim_digest,
        target=profile.maximum_target,
        max_attempts=1_000_000,
    )

    title_script = _p2tr_script("title-owner-0")
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
    mint_inputs = (TxInput(claim_outpoint),)
    mint_outputs = (
        TxOutput(98_000, title_script),
        TxOutput(0, marker_script("mint", mint_digest).hex()),
    )
    mint_txid = _fake_txid("mint", mint_inputs, mint_outputs)
    mint_proof = _hash("mint-proof")
    mint_tx = BitcoinTransaction(
        txid=mint_txid,
        block_hash=headers[mint_height].hash,
        height=mint_height,
        inputs=mint_inputs,
        outputs=mint_outputs,
    )
    view.add_transaction(mint_tx, mint_proof)

    claim_record = ClaimRecord(
        outpoint=claim_outpoint,
        block_hash=headers[claim_height].hash,
        height=claim_height,
        seal_script_hex=claim_seal_script,
        algorithm=ALGORITHM_SHA256D_80_V0,
        target_hex=target_hex,
        commitment_hex=claim_digest.hex(),
        txout_proof=claim_proof,
    )
    work_record = WorkRecord(
        challenge_height=challenge_height,
        challenge_block_hash=headers[challenge_height].hash,
        challenge_digest_hex=challenge_digest.hex(),
        extra_nonce=mined.extra_nonce,
        nonce=mined.nonce,
        work_hash_hex=mined.work_hash.hex(),
    )
    mint_record = MintRecord(
        txid=mint_txid,
        block_hash=headers[mint_height].hash,
        height=mint_height,
        txout_proof=mint_proof,
        title_vout=0,
        title_script_hex=title_script,
        commitment_hex=mint_digest.hex(),
    )

    transfers: tuple[TitleTransition, ...] = ()
    current_outpoint = Outpoint(mint_txid, 0)
    current_script = title_script

    if with_transfer:
        atom_digest = atom_id(
            mint_txid=mint_txid,
            title_vout=0,
            mint_commitment_digest=mint_digest,
        )
        successor_script = _p2tr_script("title-owner-1")
        transition_digest = transfer_commitment(
            profile,
            atom_id_digest=atom_digest,
            transition_index=0,
            previous_outpoint=current_outpoint,
            successor_vout=0,
            successor_script_hex=successor_script,
        )
        transfer_inputs = (TxInput(current_outpoint),)
        transfer_outputs = (
            TxOutput(96_000, successor_script),
            TxOutput(0, marker_script("transfer", transition_digest).hex()),
        )
        transfer_txid = _fake_txid("transfer-0", transfer_inputs, transfer_outputs)
        transfer_proof = _hash("transfer-proof-0")
        transfer_tx = BitcoinTransaction(
            txid=transfer_txid,
            block_hash=headers[transfer_height].hash,
            height=transfer_height,
            inputs=transfer_inputs,
            outputs=transfer_outputs,
        )
        view.add_transaction(transfer_tx, transfer_proof)
        transfers = (
            TitleTransition(
                index=0,
                previous_outpoint=current_outpoint,
                txid=transfer_txid,
                block_hash=headers[transfer_height].hash,
                height=transfer_height,
                txout_proof=transfer_proof,
                successor_vout=0,
                successor_script_hex=successor_script,
                commitment_hex=transition_digest.hex(),
            ),
        )
        current_outpoint = Outpoint(transfer_txid, 0)
        current_script = successor_script

    view.add_utxo(
        UTXO(
            outpoint=current_outpoint,
            value_sats=96_000 if with_transfer else 98_000,
            script_pubkey_hex=current_script,
            confirmations=tip_height - (transfer_height if with_transfer else mint_height) + 1,
        )
    )

    bundle = GoldAtomBundle(
        profile=profile.id,
        claim=claim_record,
        work=work_record,
        mint=mint_record,
        transfers=transfers,
    )
    return SimulatedFixture(bundle=bundle, view=view)
