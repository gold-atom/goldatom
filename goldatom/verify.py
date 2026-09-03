"""Deterministic verifier for GoldAtom/0 proof bundles."""

from __future__ import annotations

from dataclasses import dataclass

from .encoding import collect_markers, is_supported_seal_script, require_hex
from .models import GoldAtomBundle, Outpoint
from .profiles import ALGORITHM_SHA256D_80_V0, ProtocolProfile, get_profile
from .protocol import (
    atom_id,
    calculate_work_hash,
    claim_commitment,
    derive_challenge,
    expected_hashes,
    expected_work_log2,
    mint_commitment,
    target_to_int,
    transfer_commitment,
)
from .view import BitcoinTransaction, BitcoinView, BlockHeader


class VerificationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise VerificationError(code, message)


def _require_canonical_header(
    view: BitcoinView,
    *,
    block_hash: str,
    height: int,
    role: str,
) -> BlockHeader:
    try:
        header = view.get_header(block_hash)
        at_height = view.get_header_by_height(height)
    except Exception as exc:
        _fail("HEADER_LOOKUP", f"could not load {role} header: {exc}")
    if header.hash != block_hash or header.height != height:
        _fail("HEADER_MISMATCH", f"{role} header does not match claimed hash and height")
    if header.confirmations < 1:
        _fail("NONCANONICAL_BLOCK", f"{role} block is not in the active best chain")
    if at_height.hash != block_hash:
        _fail("REORGED_BLOCK", f"{role} block is not canonical at height {height}")
    return header


def _load_confirmed_transaction(
    view: BitcoinView,
    *,
    txid: str,
    block_hash: str,
    height: int,
    proof_hex: str,
    role: str,
) -> tuple[BitcoinTransaction, BlockHeader]:
    header = _require_canonical_header(view, block_hash=block_hash, height=height, role=role)
    try:
        if not view.verify_inclusion(txid, proof_hex, block_hash):
            _fail("BAD_INCLUSION_PROOF", f"{role} transaction inclusion proof is invalid")
        tx = view.get_transaction(txid, block_hash)
    except VerificationError:
        raise
    except Exception as exc:
        _fail("TRANSACTION_LOOKUP", f"could not load {role} transaction: {exc}")
    if tx.txid != txid or tx.block_hash != block_hash or tx.height != height:
        _fail("TRANSACTION_MISMATCH", f"{role} transaction metadata does not match bundle")
    return tx, header


def _input_count(tx: BitcoinTransaction, outpoint: Outpoint) -> int:
    return sum(item.previous_outpoint == outpoint for item in tx.inputs)


def _script_at(tx: BitcoinTransaction, vout: int, role: str) -> str:
    if not 0 <= vout < len(tx.outputs):
        _fail("MISSING_OUTPUT", f"{role} output index {vout} does not exist")
    return tx.outputs[vout].script_pubkey_hex


@dataclass(frozen=True, slots=True)
class VerificationReport:
    profile: str
    atom_id: str
    expected_local_hashes: int
    expected_local_work_log2: float
    target_hex: str
    claim_height: int
    challenge_height: int
    mint_height: int
    burial_blocks: int
    burial_chainwork: int
    current_title_outpoint: Outpoint
    title_transfers: int
    as_of_tip_hash: str
    as_of_tip_height: int

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": True,
            "profile": self.profile,
            "atom_id": self.atom_id,
            "expected_local_hashes": self.expected_local_hashes,
            "expected_local_work_log2": self.expected_local_work_log2,
            "target_hex": self.target_hex,
            "claim_height": self.claim_height,
            "challenge_height": self.challenge_height,
            "mint_height": self.mint_height,
            "burial_blocks": self.burial_blocks,
            "burial_chainwork": str(self.burial_chainwork),
            "current_title_outpoint": self.current_title_outpoint.to_dict(),
            "title_transfers": self.title_transfers,
            "as_of_tip_hash": self.as_of_tip_hash,
            "as_of_tip_height": self.as_of_tip_height,
        }

    def pretty(self) -> str:
        return "\n".join(
            [
                "VALID GOLDATOM/0",
                "",
                f"Profile:                    {self.profile}",
                f"Atom ID:                    {self.atom_id}",
                f"Expected local hashes:      {self.expected_local_hashes:,}",
                f"Expected local work:        2^{self.expected_local_work_log2:.4f}",
                f"Claim height:               {self.claim_height}",
                f"Challenge height:           {self.challenge_height}",
                f"Mint height:                {self.mint_height}",
                f"Bitcoin burial blocks:      {self.burial_blocks}",
                f"Bitcoin burial chainwork:   {self.burial_chainwork}",
                f"Title transfers:            {self.title_transfers}",
                f"Current title:              {self.current_title_outpoint}",
                f"Assayed at tip:             {self.as_of_tip_height} ({self.as_of_tip_hash})",
            ]
        )


def verify_bundle(bundle: GoldAtomBundle, view: BitcoinView) -> VerificationReport:
    try:
        profile = get_profile(bundle.profile)
    except ValueError as exc:
        _fail("UNKNOWN_PROFILE", str(exc))

    if view.network() != profile.network:
        _fail(
            "WRONG_NETWORK",
            f"bundle profile requires {profile.network}, but Bitcoin view reports {view.network()}",
        )

    claim = bundle.claim
    if claim.algorithm != ALGORITHM_SHA256D_80_V0:
        _fail("UNSUPPORTED_ALGORITHM", f"unsupported algorithm {claim.algorithm!r}")

    target = target_to_int(claim.target_hex)
    if target > profile.maximum_target:
        _fail("TARGET_TOO_EASY", "claim target exceeds the profile maximum")

    claim_tx, _claim_header = _load_confirmed_transaction(
        view,
        txid=claim.outpoint.txid,
        block_hash=claim.block_hash,
        height=claim.height,
        proof_hex=claim.txout_proof,
        role="claim",
    )
    seal_script = _script_at(claim_tx, claim.outpoint.vout, "claim seal")
    if seal_script != claim.seal_script_hex:
        _fail("CLAIM_SEAL_MISMATCH", "claim seal script differs from committed script")
    if not is_supported_seal_script(seal_script):
        _fail(
            "UNSUPPORTED_CLAIM_SEAL",
            "claim seal must be canonical P2WPKH, P2WSH, or P2TR",
        )

    expected_claim_commitment = claim_commitment(
        profile,
        seal_vout=claim.outpoint.vout,
        seal_script_hex=claim.seal_script_hex,
        algorithm=claim.algorithm,
        target_hex=claim.target_hex,
    )
    supplied_claim_commitment = require_hex(
        claim.commitment_hex, length=32, name="claim commitment"
    )
    if expected_claim_commitment != supplied_claim_commitment:
        _fail("BAD_CLAIM_COMMITMENT", "claim commitment does not recompute")
    claim_markers = collect_markers(
        (output.script_pubkey_hex for output in claim_tx.outputs), "claim"
    )
    if claim_markers.count(expected_claim_commitment) != 1:
        _fail("CLAIM_MARKER_COUNT", "claim transaction must contain one matching claim marker")

    work = bundle.work
    expected_challenge_height = claim.height + profile.challenge_delay
    if work.challenge_height != expected_challenge_height:
        _fail("BAD_CHALLENGE_HEIGHT", "challenge height is not claim height plus profile delay")
    challenge_header = _require_canonical_header(
        view,
        block_hash=work.challenge_block_hash,
        height=work.challenge_height,
        role="challenge",
    )
    expected_challenge = derive_challenge(
        profile,
        claim_outpoint=claim.outpoint,
        claim_block_hash=claim.block_hash,
        claim_commitment_digest=expected_claim_commitment,
        challenge_block_hash=challenge_header.hash,
    )
    supplied_challenge = require_hex(
        work.challenge_digest_hex, length=32, name="challenge digest"
    )
    if expected_challenge != supplied_challenge:
        _fail("BAD_CHALLENGE", "challenge digest does not recompute from canonical history")

    expected_work_hash = calculate_work_hash(
        challenge_digest=expected_challenge,
        claim_commitment_digest=expected_claim_commitment,
        extra_nonce=work.extra_nonce,
        nonce=work.nonce,
    )
    supplied_work_hash = require_hex(work.work_hash_hex, length=32, name="work hash")
    if supplied_work_hash != expected_work_hash:
        _fail("BAD_WORK_HASH", "local-work hash does not recompute")
    if int.from_bytes(expected_work_hash, "big") > target:
        _fail("INSUFFICIENT_WORK", "local-work hash is above the committed target")

    mint = bundle.mint
    earliest_mint_height = work.challenge_height + 1
    latest_mint_height = work.challenge_height + profile.mint_window
    if not earliest_mint_height <= mint.height <= latest_mint_height:
        _fail(
            "MINT_OUTSIDE_WINDOW",
            f"mint height must be in [{earliest_mint_height}, {latest_mint_height}]",
        )
    mint_tx, mint_header = _load_confirmed_transaction(
        view,
        txid=mint.txid,
        block_hash=mint.block_hash,
        height=mint.height,
        proof_hex=mint.txout_proof,
        role="mint",
    )
    if _input_count(mint_tx, claim.outpoint) != 1:
        _fail("CLAIM_NOT_CONSUMED", "mint transaction must spend the claim seal exactly once")

    title_script = _script_at(mint_tx, mint.title_vout, "mint title")
    if title_script != mint.title_script_hex:
        _fail("TITLE_SCRIPT_MISMATCH", "mint title script differs from committed script")
    if not is_supported_seal_script(title_script):
        _fail(
            "UNSUPPORTED_TITLE_SCRIPT",
            "title output must be canonical P2WPKH, P2WSH, or P2TR",
        )

    expected_mint_commitment = mint_commitment(
        profile,
        claim_outpoint=claim.outpoint,
        challenge_digest=expected_challenge,
        extra_nonce=work.extra_nonce,
        nonce=work.nonce,
        work_hash=expected_work_hash,
        title_vout=mint.title_vout,
        title_script_hex=mint.title_script_hex,
    )
    supplied_mint_commitment = require_hex(
        mint.commitment_hex, length=32, name="mint commitment"
    )
    if expected_mint_commitment != supplied_mint_commitment:
        _fail("BAD_MINT_COMMITMENT", "mint commitment does not recompute")
    mint_markers = collect_markers(
        (output.script_pubkey_hex for output in mint_tx.outputs), "mint"
    )
    if mint_markers != [expected_mint_commitment]:
        _fail(
            "MINT_MARKER_COUNT",
            "mint transaction must contain exactly one GoldAtom mint marker, and it must match",
        )

    atom_digest = atom_id(
        mint_txid=mint.txid,
        title_vout=mint.title_vout,
        mint_commitment_digest=expected_mint_commitment,
    )
    current_outpoint = Outpoint(mint.txid, mint.title_vout)
    current_script = mint.title_script_hex
    current_value_sats = mint_tx.outputs[mint.title_vout].value_sats
    previous_height = mint.height

    for expected_index, transition in enumerate(bundle.transfers):
        if transition.index != expected_index:
            _fail("TRANSFER_INDEX", "title transition indices must be contiguous from zero")
        if transition.previous_outpoint != current_outpoint:
            _fail("BROKEN_TITLE_CHAIN", "transition does not spend the preceding title outpoint")
        if transition.height < previous_height:
            _fail("TRANSFER_ORDER", "title transition precedes the output it spends")
        tx, _header = _load_confirmed_transaction(
            view,
            txid=transition.txid,
            block_hash=transition.block_hash,
            height=transition.height,
            proof_hex=transition.txout_proof,
            role=f"title transition {expected_index}",
        )
        if _input_count(tx, current_outpoint) != 1:
            _fail("TITLE_NOT_CONSUMED", "title transition must spend the current title exactly once")
        successor_script = _script_at(tx, transition.successor_vout, "successor title")
        if successor_script != transition.successor_script_hex:
            _fail("SUCCESSOR_SCRIPT_MISMATCH", "successor title script differs from commitment")
        if not is_supported_seal_script(successor_script):
            _fail(
                "UNSUPPORTED_TITLE_SCRIPT",
                "successor title must be canonical P2WPKH, P2WSH, or P2TR",
            )
        expected_transfer_commitment = transfer_commitment(
            profile,
            atom_id_digest=atom_digest,
            transition_index=transition.index,
            previous_outpoint=current_outpoint,
            successor_vout=transition.successor_vout,
            successor_script_hex=transition.successor_script_hex,
        )
        supplied_transfer_commitment = require_hex(
            transition.commitment_hex, length=32, name="transfer commitment"
        )
        if supplied_transfer_commitment != expected_transfer_commitment:
            _fail("BAD_TRANSFER_COMMITMENT", "title transfer commitment does not recompute")
        transfer_markers = collect_markers(
            (output.script_pubkey_hex for output in tx.outputs), "transfer"
        )
        if transfer_markers != [expected_transfer_commitment]:
            _fail(
                "TRANSFER_MARKER_COUNT",
                "title transition must contain exactly one matching transfer marker",
            )
        current_outpoint = Outpoint(transition.txid, transition.successor_vout)
        current_script = transition.successor_script_hex
        current_value_sats = tx.outputs[transition.successor_vout].value_sats
        previous_height = transition.height

    current_utxo = view.get_utxo(current_outpoint)
    if current_utxo is None:
        _fail(
            "TITLE_SPENT_OR_MISSING",
            "current title is spent, in-flight in the mempool, burned, or the bundle omits a transfer",
        )
    if current_utxo.script_pubkey_hex != current_script:
        _fail("CURRENT_TITLE_MISMATCH", "UTXO script does not match the terminal title script")
    if current_utxo.value_sats != current_value_sats:
        _fail("CURRENT_TITLE_VALUE", "UTXO value does not match the terminal title output")
    if current_utxo.confirmations < 1:
        _fail("CURRENT_TITLE_UNCONFIRMED", "terminal title output is not confirmed")

    tip = view.get_tip()
    if tip.confirmations < 1:
        _fail("BAD_TIP", "Bitcoin view tip is not canonical")
    burial_blocks = tip.height - mint.height
    burial_chainwork = tip.chainwork - mint_header.chainwork
    if burial_blocks < profile.minimum_burial_blocks:
        _fail("INSUFFICIENT_BURIAL", "mint has too few subsequent canonical blocks")
    if burial_chainwork < profile.minimum_burial_chainwork:
        _fail("INSUFFICIENT_CHAINWORK", "mint has too little subsequent Bitcoin chainwork")

    return VerificationReport(
        profile=profile.id,
        atom_id=atom_digest.hex(),
        expected_local_hashes=expected_hashes(target),
        expected_local_work_log2=expected_work_log2(target),
        target_hex=claim.target_hex,
        claim_height=claim.height,
        challenge_height=work.challenge_height,
        mint_height=mint.height,
        burial_blocks=burial_blocks,
        burial_chainwork=burial_chainwork,
        current_title_outpoint=current_outpoint,
        title_transfers=len(bundle.transfers),
        as_of_tip_hash=tip.hash,
        as_of_tip_height=tip.height,
    )
