"""Abstract Bitcoin view consumed by the verifier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import Outpoint


@dataclass(frozen=True, slots=True)
class TxInput:
    previous_outpoint: Outpoint


@dataclass(frozen=True, slots=True)
class TxOutput:
    value_sats: int
    script_pubkey_hex: str


@dataclass(frozen=True, slots=True)
class BitcoinTransaction:
    txid: str
    block_hash: str
    height: int
    inputs: tuple[TxInput, ...]
    outputs: tuple[TxOutput, ...]


@dataclass(frozen=True, slots=True)
class BlockHeader:
    hash: str
    height: int
    confirmations: int
    chainwork: int
    time: int


@dataclass(frozen=True, slots=True)
class UTXO:
    outpoint: Outpoint
    value_sats: int
    script_pubkey_hex: str
    confirmations: int


class BitcoinView(Protocol):
    def network(self) -> str: ...

    def get_transaction(self, txid: str, block_hash: str) -> BitcoinTransaction: ...

    def verify_inclusion(self, txid: str, proof_hex: str, block_hash: str) -> bool: ...

    def get_header(self, block_hash: str) -> BlockHeader: ...

    def get_header_by_height(self, height: int) -> BlockHeader: ...

    def get_tip(self) -> BlockHeader: ...

    def get_utxo(self, outpoint: Outpoint) -> UTXO | None: ...
