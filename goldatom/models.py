"""Serializable GoldAtom/0 proof-bundle models."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .encoding import require_hex


def _require_nonnegative(value: int, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _require_fields(data: dict[str, Any], *, required: set[str], optional: set[str] | None = None) -> None:
    if not isinstance(data, dict):
        raise ValueError("record must be a JSON object")
    optional = optional or set()
    unknown = set(data) - required - optional
    missing = required - set(data)
    if unknown:
        raise ValueError(f"unknown fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing fields: {sorted(missing)}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class Outpoint:
    txid: str
    vout: int

    def __post_init__(self) -> None:
        require_hex(self.txid, length=32, name="txid")
        _require_nonnegative(self.vout, "vout")
        if self.vout > 0xFFFFFFFF:
            raise ValueError("vout exceeds u32")

    def to_dict(self) -> dict[str, Any]:
        return {"txid": self.txid, "vout": self.vout}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Outpoint":
        _require_fields(data, required={"txid", "vout"})
        return cls(txid=data["txid"], vout=data["vout"])

    def __str__(self) -> str:
        return f"{self.txid}:{self.vout}"


@dataclass(frozen=True, slots=True)
class ClaimRecord:
    outpoint: Outpoint
    block_hash: str
    height: int
    seal_script_hex: str
    algorithm: str
    target_hex: str
    commitment_hex: str
    txout_proof: str

    def __post_init__(self) -> None:
        require_hex(self.block_hash, length=32, name="claim block hash")
        seal_script = require_hex(self.seal_script_hex, name="claim seal script")
        if not seal_script:
            raise ValueError("claim seal script must not be empty")
        require_hex(self.target_hex, length=32, name="target")
        require_hex(self.commitment_hex, length=32, name="claim commitment")
        proof = require_hex(self.txout_proof, name="claim txout proof")
        if not proof:
            raise ValueError("claim txout proof must not be empty")
        _require_nonnegative(self.height, "claim height")
        if not isinstance(self.algorithm, str) or not self.algorithm:
            raise ValueError("algorithm must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["outpoint"] = self.outpoint.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClaimRecord":
        _require_fields(data, required={
            "outpoint", "block_hash", "height", "seal_script_hex", "algorithm",
            "target_hex", "commitment_hex", "txout_proof"
        })
        return cls(
            outpoint=Outpoint.from_dict(data["outpoint"]),
            block_hash=data["block_hash"],
            height=data["height"],
            seal_script_hex=data["seal_script_hex"],
            algorithm=data["algorithm"],
            target_hex=data["target_hex"],
            commitment_hex=data["commitment_hex"],
            txout_proof=data["txout_proof"],
        )


@dataclass(frozen=True, slots=True)
class WorkRecord:
    challenge_height: int
    challenge_block_hash: str
    challenge_digest_hex: str
    extra_nonce: int
    nonce: int
    work_hash_hex: str

    def __post_init__(self) -> None:
        _require_nonnegative(self.challenge_height, "challenge height")
        require_hex(self.challenge_block_hash, length=32, name="challenge block hash")
        require_hex(self.challenge_digest_hex, length=32, name="challenge digest")
        require_hex(self.work_hash_hex, length=32, name="work hash")
        _require_nonnegative(self.extra_nonce, "extra_nonce")
        _require_nonnegative(self.nonce, "nonce")
        if self.extra_nonce > 0xFFFFFFFF or self.nonce > 0xFFFFFFFF:
            raise ValueError("work counters must fit u32")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkRecord":
        _require_fields(data, required={
            "challenge_height", "challenge_block_hash", "challenge_digest_hex",
            "extra_nonce", "nonce", "work_hash_hex"
        })
        return cls(**data)


@dataclass(frozen=True, slots=True)
class MintRecord:
    txid: str
    block_hash: str
    height: int
    txout_proof: str
    title_vout: int
    title_script_hex: str
    commitment_hex: str

    def __post_init__(self) -> None:
        require_hex(self.txid, length=32, name="mint txid")
        require_hex(self.block_hash, length=32, name="mint block hash")
        proof = require_hex(self.txout_proof, name="mint txout proof")
        if not proof:
            raise ValueError("mint txout proof must not be empty")
        title_script = require_hex(self.title_script_hex, name="title script")
        if not title_script:
            raise ValueError("title script must not be empty")
        require_hex(self.commitment_hex, length=32, name="mint commitment")
        _require_nonnegative(self.height, "mint height")
        _require_nonnegative(self.title_vout, "title_vout")
        if self.title_vout > 0xFFFFFFFF:
            raise ValueError("title_vout exceeds u32")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MintRecord":
        _require_fields(data, required={
            "txid", "block_hash", "height", "txout_proof", "title_vout",
            "title_script_hex", "commitment_hex"
        })
        return cls(**data)


@dataclass(frozen=True, slots=True)
class TitleTransition:
    index: int
    previous_outpoint: Outpoint
    txid: str
    block_hash: str
    height: int
    txout_proof: str
    successor_vout: int
    successor_script_hex: str
    commitment_hex: str

    def __post_init__(self) -> None:
        _require_nonnegative(self.index, "transition index")
        require_hex(self.txid, length=32, name="transfer txid")
        require_hex(self.block_hash, length=32, name="transfer block hash")
        proof = require_hex(self.txout_proof, name="transfer txout proof")
        if not proof:
            raise ValueError("transfer txout proof must not be empty")
        successor_script = require_hex(self.successor_script_hex, name="successor script")
        if not successor_script:
            raise ValueError("successor script must not be empty")
        require_hex(self.commitment_hex, length=32, name="transfer commitment")
        _require_nonnegative(self.height, "transfer height")
        _require_nonnegative(self.successor_vout, "successor_vout")
        if self.successor_vout > 0xFFFFFFFF:
            raise ValueError("successor_vout exceeds u32")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["previous_outpoint"] = self.previous_outpoint.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TitleTransition":
        _require_fields(data, required={
            "index", "previous_outpoint", "txid", "block_hash", "height",
            "txout_proof", "successor_vout", "successor_script_hex", "commitment_hex"
        })
        return cls(
            index=data["index"],
            previous_outpoint=Outpoint.from_dict(data["previous_outpoint"]),
            txid=data["txid"],
            block_hash=data["block_hash"],
            height=data["height"],
            txout_proof=data["txout_proof"],
            successor_vout=data["successor_vout"],
            successor_script_hex=data["successor_script_hex"],
            commitment_hex=data["commitment_hex"],
        )


@dataclass(frozen=True, slots=True)
class GoldAtomBundle:
    profile: str
    claim: ClaimRecord
    work: WorkRecord
    mint: MintRecord
    transfers: tuple[TitleTransition, ...] = field(default_factory=tuple)
    format: str = "goldatom-proof"
    version: int = 0

    def __post_init__(self) -> None:
        if self.format != "goldatom-proof":
            raise ValueError("unsupported proof-bundle format")
        if type(self.version) is not int or self.version != 0:
            raise ValueError("unsupported GoldAtom proof-bundle version")
        if not isinstance(self.profile, str) or not self.profile:
            raise ValueError("profile must be a non-empty string")
        if not isinstance(self.transfers, tuple) or not all(
            isinstance(item, TitleTransition) for item in self.transfers
        ):
            raise ValueError("transfers must be a tuple of TitleTransition records")

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "version": self.version,
            "profile": self.profile,
            "claim": self.claim.to_dict(),
            "work": self.work.to_dict(),
            "mint": self.mint.to_dict(),
            "transfers": [transition.to_dict() for transition in self.transfers],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"

    def write(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json(), encoding="utf-8")
        return output

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoldAtomBundle":
        _require_fields(
            data,
            required={"profile", "claim", "work", "mint"},
            optional={"format", "version", "transfers"},
        )
        transfers = data.get("transfers", [])
        if not isinstance(transfers, list):
            raise ValueError("transfers must be a JSON array")
        for name in ("claim", "work", "mint"):
            if not isinstance(data[name], dict):
                raise ValueError(f"{name} must be a JSON object")
        if not all(isinstance(item, dict) for item in transfers):
            raise ValueError("each transfer must be a JSON object")
        return cls(
            format=data.get("format", "goldatom-proof"),
            version=data.get("version", 0),
            profile=data["profile"],
            claim=ClaimRecord.from_dict(data["claim"]),
            work=WorkRecord.from_dict(data["work"]),
            mint=MintRecord.from_dict(data["mint"]),
            transfers=tuple(TitleTransition.from_dict(item) for item in transfers),
        )

    @classmethod
    def from_json(cls, text: str) -> "GoldAtomBundle":
        parsed = json.loads(text, object_pairs_hook=_strict_object)
        if not isinstance(parsed, dict):
            raise ValueError("GoldAtom bundle JSON must be an object")
        return cls.from_dict(parsed)

    @classmethod
    def read(cls, path: str | Path) -> "GoldAtomBundle":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))
