"""In-memory Bitcoin view used by deterministic protocol tests."""

from __future__ import annotations

from dataclasses import replace

from .models import Outpoint
from .view import BitcoinTransaction, BlockHeader, UTXO


class FakeBitcoinView:
    def __init__(self, network: str = "simnet") -> None:
        self._network = network
        self.transactions: dict[tuple[str, str], BitcoinTransaction] = {}
        self.headers_by_hash: dict[str, BlockHeader] = {}
        self.headers_by_height: dict[int, BlockHeader] = {}
        self.proofs: dict[str, tuple[str, str]] = {}
        self.utxos: dict[Outpoint, UTXO] = {}
        self.tip_hash: str | None = None

    def network(self) -> str:
        return self._network

    def add_header(self, header: BlockHeader, *, tip: bool = False) -> None:
        self.headers_by_hash[header.hash] = header
        self.headers_by_height[header.height] = header
        if tip or self.tip_hash is None:
            self.tip_hash = header.hash

    def add_transaction(self, tx: BitcoinTransaction, proof_hex: str) -> None:
        self.transactions[(tx.txid, tx.block_hash)] = tx
        self.proofs[proof_hex] = (tx.txid, tx.block_hash)

    def add_utxo(self, utxo: UTXO) -> None:
        self.utxos[utxo.outpoint] = utxo

    def spend_utxo(self, outpoint: Outpoint) -> None:
        self.utxos.pop(outpoint, None)

    def get_transaction(self, txid: str, block_hash: str) -> BitcoinTransaction:
        try:
            return self.transactions[(txid, block_hash)]
        except KeyError as exc:
            raise ValueError(f"fake transaction not found: {txid} in {block_hash}") from exc

    def verify_inclusion(self, txid: str, proof_hex: str, block_hash: str) -> bool:
        return self.proofs.get(proof_hex) == (txid, block_hash)

    def get_header(self, block_hash: str) -> BlockHeader:
        try:
            return self.headers_by_hash[block_hash]
        except KeyError as exc:
            raise ValueError(f"fake header not found: {block_hash}") from exc

    def get_header_by_height(self, height: int) -> BlockHeader:
        try:
            return self.headers_by_height[height]
        except KeyError as exc:
            raise ValueError(f"fake header height not found: {height}") from exc

    def get_tip(self) -> BlockHeader:
        if self.tip_hash is None:
            raise ValueError("fake chain has no tip")
        return self.get_header(self.tip_hash)

    def get_utxo(self, outpoint: Outpoint) -> UTXO | None:
        return self.utxos.get(outpoint)

    def replace_header(self, height: int, new_hash: str) -> None:
        old = self.get_header_by_height(height)
        new = replace(old, hash=new_hash)
        self.headers_by_hash.pop(old.hash, None)
        self.headers_by_hash[new.hash] = new
        self.headers_by_height[height] = new
        if self.tip_hash == old.hash:
            self.tip_hash = new.hash
