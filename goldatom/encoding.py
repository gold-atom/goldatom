"""Canonical encodings and domain-separated hashes for GoldAtom/0."""

from __future__ import annotations

import hashlib
import re
import struct
from typing import Iterable


class EncodingError(ValueError):
    """Raised when a protocol value is not canonically encoded."""


def require_hex(value: str, *, length: int | None = None, name: str = "hex") -> bytes:
    if not isinstance(value, str):
        raise EncodingError(f"{name} must be a hexadecimal string")
    if len(value) % 2:
        raise EncodingError(f"{name} must contain an even number of hexadecimal characters")
    if re.fullmatch(r"[0-9a-f]*", value) is None:
        raise EncodingError(f"{name} must use canonical lowercase hexadecimal without whitespace")
    raw = bytes.fromhex(value)
    if length is not None and len(raw) != length:
        raise EncodingError(f"{name} must be exactly {length} bytes")
    if value != value.lower():
        raise EncodingError(f"{name} must use lowercase hexadecimal")
    return raw


def u32be(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise EncodingError("u32 value out of range")
    return struct.pack(">I", value)


def u32le(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise EncodingError("u32 value out of range")
    return struct.pack("<I", value)


def u64be(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
        raise EncodingError("u64 value out of range")
    return struct.pack(">Q", value)


def varbytes(value: bytes) -> bytes:
    return u32be(len(value)) + value


def varstr(value: str) -> bytes:
    return varbytes(value.encode("utf-8"))


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256d(data: bytes) -> bytes:
    return sha256(sha256(data))


def tagged_hash(tag: str, message: bytes) -> bytes:
    """BIP340-style tagged SHA-256 used only for protocol commitments."""
    tag_hash = sha256(tag.encode("utf-8"))
    return sha256(tag_hash + tag_hash + message)


MARKERS: dict[str, bytes] = {
    "claim": b"GA0C",
    "mint": b"GA0M",
    "transfer": b"GA0T",
}


def marker_payload(kind: str, digest: bytes) -> bytes:
    try:
        prefix = MARKERS[kind]
    except KeyError as exc:
        raise EncodingError(f"unknown marker kind: {kind}") from exc
    if len(digest) != 32:
        raise EncodingError("marker digest must be 32 bytes")
    return prefix + digest


def op_return_script(payload: bytes) -> bytes:
    """Encode one canonical small direct-push OP_RETURN script.

    GoldAtom/0 markers are exactly 36 bytes, so no PUSHDATA opcode is needed.
    """
    if not 1 <= len(payload) <= 75:
        raise EncodingError("GoldAtom/0 OP_RETURN payload must be 1..75 bytes")
    return b"\x6a" + bytes([len(payload)]) + payload


def marker_script(kind: str, digest: bytes) -> bytes:
    return op_return_script(marker_payload(kind, digest))


def decode_op_return(script: bytes) -> bytes | None:
    if len(script) < 2 or script[0] != 0x6A:
        return None
    length = script[1]
    if not 1 <= length <= 75:
        return None
    if len(script) != 2 + length:
        return None
    return script[2:]


def decode_marker(script_hex: str) -> tuple[str, bytes] | None:
    script = require_hex(script_hex, name="script_pubkey")
    payload = decode_op_return(script)
    if payload is None or len(payload) != 36:
        return None
    prefix, digest = payload[:4], payload[4:]
    for kind, expected in MARKERS.items():
        if prefix == expected:
            return kind, digest
    return None


def collect_markers(script_hexes: Iterable[str], kind: str) -> list[bytes]:
    found: list[bytes] = []
    for script_hex in script_hexes:
        decoded = decode_marker(script_hex)
        if decoded is not None and decoded[0] == kind:
            found.append(decoded[1])
    return found


def is_supported_seal_script(script_hex: str) -> bool:
    """Return whether a v0 title/claim seal uses an allowed native SegWit template.

    This is only a template check. It does not prove key possession, that a P2TR
    x-coordinate lifts to a curve point, or that a P2WSH witness is satisfiable.
    """
    script = require_hex(script_hex, name="seal script")
    return (
        (len(script) == 22 and script[:2] == b"\x00\x14")  # P2WPKH
        or (len(script) == 34 and script[:2] == b"\x00\x20")  # P2WSH
        or (len(script) == 34 and script[:2] == b"\x51\x20")  # P2TR
    )
