"""Pure GoldAtom/0 protocol calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .encoding import (
    require_hex,
    sha256d,
    tagged_hash,
    u32be,
    u32le,
    varbytes,
    varstr,
)
from .models import Outpoint
from .profiles import ALGORITHM_SHA256D_80_V0, ProtocolProfile


WORK_HEADER_MAGIC = b"GAW0"
WORK_HEADER_RESERVED = b"\x00\x00\x00\x00"


def encode_outpoint(outpoint: Outpoint) -> bytes:
    # txids use the conventional display-order hexadecimal byte sequence.
    return require_hex(outpoint.txid, length=32, name="txid") + u32be(outpoint.vout)


def target_to_int(target_hex: str) -> int:
    return int.from_bytes(require_hex(target_hex, length=32, name="target"), "big")


def claim_commitment(
    profile: ProtocolProfile,
    *,
    seal_vout: int,
    seal_script_hex: str,
    algorithm: str,
    target_hex: str,
) -> bytes:
    script = require_hex(seal_script_hex, name="claim seal script")
    target = require_hex(target_hex, length=32, name="target")
    message = b"".join(
        [
            varstr(profile.id),
            varstr(profile.network),
            u32be(seal_vout),
            varbytes(script),
            varstr(algorithm),
            target,
            u32be(profile.challenge_delay),
            u32be(profile.mint_window),
        ]
    )
    return tagged_hash("GoldAtom/claim/v0", message)


def derive_challenge(
    profile: ProtocolProfile,
    *,
    claim_outpoint: Outpoint,
    claim_block_hash: str,
    claim_commitment_digest: bytes,
    challenge_block_hash: str,
) -> bytes:
    if len(claim_commitment_digest) != 32:
        raise ValueError("claim commitment digest must be 32 bytes")
    message = b"".join(
        [
            varstr(profile.id),
            encode_outpoint(claim_outpoint),
            require_hex(claim_block_hash, length=32, name="claim block hash"),
            claim_commitment_digest,
            require_hex(challenge_block_hash, length=32, name="challenge block hash"),
        ]
    )
    return tagged_hash("GoldAtom/challenge/v0", message)


def build_work_header(
    *,
    challenge_digest: bytes,
    claim_commitment_digest: bytes,
    extra_nonce: int,
    nonce: int,
) -> bytes:
    """Construct the fixed 80-byte local-work header.

    Layout:
      4 bytes  magic = ASCII "GAW0"
     32 bytes  challenge digest
     32 bytes  claim commitment digest
      4 bytes  extra_nonce, little-endian
      4 bytes  reserved zero
      4 bytes  nonce, little-endian
    """
    if len(challenge_digest) != 32 or len(claim_commitment_digest) != 32:
        raise ValueError("work header digests must be 32 bytes")
    header = b"".join(
        [
            WORK_HEADER_MAGIC,
            challenge_digest,
            claim_commitment_digest,
            u32le(extra_nonce),
            WORK_HEADER_RESERVED,
            u32le(nonce),
        ]
    )
    if len(header) != 80:
        raise AssertionError("GoldAtom work header must be exactly 80 bytes")
    return header


def calculate_work_hash(
    *,
    challenge_digest: bytes,
    claim_commitment_digest: bytes,
    extra_nonce: int,
    nonce: int,
) -> bytes:
    return sha256d(
        build_work_header(
            challenge_digest=challenge_digest,
            claim_commitment_digest=claim_commitment_digest,
            extra_nonce=extra_nonce,
            nonce=nonce,
        )
    )


@dataclass(frozen=True, slots=True)
class MinedWork:
    extra_nonce: int
    nonce: int
    work_hash: bytes
    attempts: int


def mine_work(
    *,
    challenge_digest: bytes,
    claim_commitment_digest: bytes,
    target: int,
    start_extra_nonce: int = 0,
    start_nonce: int = 0,
    max_attempts: int | None = None,
) -> MinedWork:
    if not 0 <= target < (1 << 256):
        raise ValueError("target must be a 256-bit unsigned integer")
    attempts = 0
    extra_nonce = start_extra_nonce
    nonce = start_nonce
    while extra_nonce <= 0xFFFFFFFF:
        while nonce <= 0xFFFFFFFF:
            digest = calculate_work_hash(
                challenge_digest=challenge_digest,
                claim_commitment_digest=claim_commitment_digest,
                extra_nonce=extra_nonce,
                nonce=nonce,
            )
            attempts += 1
            if int.from_bytes(digest, "big") <= target:
                return MinedWork(extra_nonce, nonce, digest, attempts)
            if max_attempts is not None and attempts >= max_attempts:
                raise RuntimeError(f"no valid work found in {attempts} attempts")
            nonce += 1
        extra_nonce += 1
        nonce = 0
    raise RuntimeError("GoldAtom work-counter space exhausted")


def mint_commitment(
    profile: ProtocolProfile,
    *,
    claim_outpoint: Outpoint,
    challenge_digest: bytes,
    extra_nonce: int,
    nonce: int,
    work_hash: bytes,
    title_vout: int,
    title_script_hex: str,
) -> bytes:
    if len(challenge_digest) != 32 or len(work_hash) != 32:
        raise ValueError("mint digests must be 32 bytes")
    message = b"".join(
        [
            varstr(profile.id),
            encode_outpoint(claim_outpoint),
            challenge_digest,
            u32be(extra_nonce),
            u32be(nonce),
            work_hash,
            u32be(title_vout),
            varbytes(require_hex(title_script_hex, name="title script")),
        ]
    )
    return tagged_hash("GoldAtom/mint/v0", message)


def atom_id(*, mint_txid: str, title_vout: int, mint_commitment_digest: bytes) -> bytes:
    if len(mint_commitment_digest) != 32:
        raise ValueError("mint commitment digest must be 32 bytes")
    message = b"".join(
        [
            require_hex(mint_txid, length=32, name="mint txid"),
            u32be(title_vout),
            mint_commitment_digest,
        ]
    )
    return tagged_hash("GoldAtom/id/v0", message)


def transfer_commitment(
    profile: ProtocolProfile,
    *,
    atom_id_digest: bytes,
    transition_index: int,
    previous_outpoint: Outpoint,
    successor_vout: int,
    successor_script_hex: str,
) -> bytes:
    if len(atom_id_digest) != 32:
        raise ValueError("atom id must be 32 bytes")
    message = b"".join(
        [
            varstr(profile.id),
            atom_id_digest,
            u32be(transition_index),
            encode_outpoint(previous_outpoint),
            u32be(successor_vout),
            varbytes(require_hex(successor_script_hex, name="successor script")),
        ]
    )
    return tagged_hash("GoldAtom/transfer/v0", message)


def expected_hashes(target: int) -> int:
    """Ceiling of the geometric expectation 2^256 / (target + 1)."""
    if not 0 <= target < (1 << 256):
        raise ValueError("target must be a 256-bit unsigned integer")
    denominator = target + 1
    return ((1 << 256) + denominator - 1) // denominator


def expected_work_log2(target: int) -> float:
    if not 0 <= target < (1 << 256):
        raise ValueError("target must be a 256-bit unsigned integer")
    return 256.0 - math.log2(target + 1)


def assert_supported_algorithm(algorithm: str) -> None:
    if algorithm != ALGORITHM_SHA256D_80_V0:
        raise ValueError(f"unsupported local-work algorithm: {algorithm}")
