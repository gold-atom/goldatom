"""Bitcoin Core 31-compatible JSON-RPC adapter for GoldAtom/0."""

from __future__ import annotations

import base64
import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib import error, request

from .models import Outpoint
from .view import BitcoinTransaction, BlockHeader, TxInput, TxOutput, UTXO


class RpcError(RuntimeError):
    def __init__(self, code: int | None, message: str):
        self.code = code
        super().__init__(f"Bitcoin Core RPC error {code}: {message}")


class JsonRpcClient:
    def __init__(
        self,
        url: str,
        *,
        username: str | None = None,
        password: str | None = None,
        cookie_file: str | Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        if cookie_file is not None:
            cookie = Path(cookie_file).expanduser().read_text(encoding="utf-8").strip()
            if ":" not in cookie:
                raise ValueError("Bitcoin Core cookie must contain username:password")
            username, password = cookie.split(":", 1)
        self.username = username
        self.password = password
        if (username is None) != (password is None):
            raise ValueError("RPC username and password must be supplied together")
        self._next_id = 1

    def child(self, path: str) -> "JsonRpcClient":
        return JsonRpcClient(
            f"{self.url}/{path.lstrip('/')}",
            username=self.username,
            password=self.password,
            timeout=self.timeout,
        )

    @staticmethod
    def _decode_response(payload: bytes, *, expected_id: int, http_status: int | None = None) -> Any:
        try:
            decoded = json.loads(payload, parse_float=Decimal)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            prefix = f"HTTP {http_status}: " if http_status is not None else ""
            detail = payload.decode("utf-8", errors="replace")[:500]
            raise RpcError(http_status, f"{prefix}malformed JSON-RPC response: {detail}") from exc
        if not isinstance(decoded, dict):
            raise RpcError(http_status, "JSON-RPC response must be an object")
        if decoded.get("id") != expected_id:
            raise RpcError(
                http_status,
                f"JSON-RPC response id mismatch: expected {expected_id}, got {decoded.get('id')!r}",
            )
        rpc_error = decoded.get("error")
        if rpc_error is not None:
            if not isinstance(rpc_error, dict):
                raise RpcError(http_status, "malformed JSON-RPC error object")
            code = rpc_error.get("code")
            if not isinstance(code, int):
                code = http_status
            message = rpc_error.get("message")
            if not isinstance(message, str) or not message:
                message = "unknown Bitcoin Core RPC error"
            raise RpcError(code, message)
        if "result" not in decoded:
            raise RpcError(http_status, "JSON-RPC response is missing result")
        return decoded["result"]

    def call(self, method: str, *params: Any) -> Any:
        rpc_id = self._next_id
        self._next_id += 1
        body = json.dumps(
            {"jsonrpc": "2.0", "id": rpc_id, "method": method, "params": list(params)},
            separators=(",", ":"),
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.username is not None and self.password is not None:
            token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        req = request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                payload = response.read()
        except error.HTTPError as exc:
            payload = exc.read()
            try:
                return self._decode_response(
                    payload,
                    expected_id=rpc_id,
                    http_status=exc.code,
                )
            except RpcError:
                raise
            except Exception as parse_error:  # defensive fallback for non-Core HTTP bodies
                detail = payload.decode("utf-8", errors="replace")[:500]
                raise RpcError(exc.code, detail) from parse_error
        except error.URLError as exc:
            raise ConnectionError(f"could not connect to Bitcoin Core RPC at {self.url}: {exc}") from exc
        return self._decode_response(payload, expected_id=rpc_id)


class CoreBitcoinView:
    """A verifier view backed by a fully validating Bitcoin Core node."""

    def __init__(self, rpc: JsonRpcClient):
        self.rpc = rpc
        self._network: str | None = None

    def network(self) -> str:
        if self._network is None:
            self._network = str(self.rpc.call("getblockchaininfo")["chain"])
        return self._network

    def get_transaction(self, txid: str, block_hash: str) -> BitcoinTransaction:
        result = self.rpc.call("getrawtransaction", txid, 1, block_hash)
        if result.get("in_active_chain") is not True:
            raise ValueError(f"transaction {txid} is not in the active chain block {block_hash}")
        header = self.get_header(block_hash)
        inputs: list[TxInput] = []
        for item in result["vin"]:
            if "coinbase" in item:
                continue
            inputs.append(TxInput(Outpoint(txid=item["txid"], vout=int(item["vout"]))))
        outputs: list[TxOutput] = []
        for item in result["vout"]:
            value = item["value"]
            value_decimal = value if isinstance(value, Decimal) else Decimal(str(value))
            sats = int(value_decimal * Decimal(100_000_000))
            outputs.append(
                TxOutput(
                    value_sats=sats,
                    script_pubkey_hex=item["scriptPubKey"]["hex"],
                )
            )
        return BitcoinTransaction(
            txid=result["txid"],
            block_hash=block_hash,
            height=header.height,
            inputs=tuple(inputs),
            outputs=tuple(outputs),
        )

    def verify_inclusion(self, txid: str, proof_hex: str, block_hash: str) -> bool:
        committed_txids = self.rpc.call("verifytxoutproof", proof_hex)
        if txid not in committed_txids:
            return False
        # Supplying block_hash forces Core to check the exact claimed block and report
        # whether that block remains in the active chain.
        result = self.rpc.call("getrawtransaction", txid, 1, block_hash)
        return result.get("in_active_chain") is True and result.get("blockhash") == block_hash

    def get_header(self, block_hash: str) -> BlockHeader:
        result = self.rpc.call("getblockheader", block_hash, True)
        return BlockHeader(
            hash=result["hash"],
            height=int(result["height"]),
            confirmations=int(result["confirmations"]),
            chainwork=int(result["chainwork"], 16),
            time=int(result["time"]),
        )

    def get_header_by_height(self, height: int) -> BlockHeader:
        block_hash = self.rpc.call("getblockhash", height)
        return self.get_header(block_hash)

    def get_tip(self) -> BlockHeader:
        return self.get_header(self.rpc.call("getbestblockhash"))

    def get_utxo(self, outpoint: Outpoint) -> UTXO | None:
        result = self.rpc.call("gettxout", outpoint.txid, outpoint.vout, True)
        if result is None:
            return None
        value = result["value"]
        value_decimal = value if isinstance(value, Decimal) else Decimal(str(value))
        return UTXO(
            outpoint=outpoint,
            value_sats=int(value_decimal * Decimal(100_000_000)),
            script_pubkey_hex=result["scriptPubKey"]["hex"],
            confirmations=int(result["confirmations"]),
        )
