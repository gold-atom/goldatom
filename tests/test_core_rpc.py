from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch
from urllib import error

from goldatom.core_rpc import JsonRpcClient, RpcError


class _Response:
    def __init__(self, payload: object):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self.payload


class JsonRpcClientTests(unittest.TestCase):
    def test_successful_result_and_request_id(self) -> None:
        client = JsonRpcClient("http://127.0.0.1:1", username="alice", password="secret")
        with patch("goldatom.core_rpc.request.urlopen", return_value=_Response({
            "jsonrpc": "2.0", "id": 1, "result": {"chain": "regtest"}, "error": None
        })) as mocked:
            self.assertEqual(client.call("getblockchaininfo"), {"chain": "regtest"})
        request_object = mocked.call_args.args[0]
        request_body = json.loads(request_object.data)
        self.assertEqual(request_body["id"], 1)
        self.assertEqual(request_body["method"], "getblockchaininfo")
        self.assertTrue(request_object.headers["Authorization"].startswith("Basic "))

    def test_core_error_inside_http_500_preserves_rpc_code(self) -> None:
        client = JsonRpcClient("http://127.0.0.1:1")
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": None,
            "error": {"code": -8, "message": "Block height out of range"},
        }).encode("utf-8")
        http_error = error.HTTPError(
            client.url,
            500,
            "Internal Server Error",
            hdrs=None,
            fp=io.BytesIO(payload),
        )
        with patch("goldatom.core_rpc.request.urlopen", side_effect=http_error):
            with self.assertRaisesRegex(RpcError, r"RPC error -8: Block height out of range") as caught:
                client.call("getblockhash", 999)
        self.assertEqual(caught.exception.code, -8)

    def test_rpc_error_inside_http_200_is_rejected(self) -> None:
        client = JsonRpcClient("http://127.0.0.1:1")
        response = _Response({
            "jsonrpc": "2.0",
            "id": 1,
            "result": None,
            "error": {"code": -5, "message": "Block not found"},
        })
        with patch("goldatom.core_rpc.request.urlopen", return_value=response):
            with self.assertRaisesRegex(RpcError, r"RPC error -5: Block not found"):
                client.call("getblockheader", "00" * 32)

    def test_response_id_mismatch_is_rejected(self) -> None:
        client = JsonRpcClient("http://127.0.0.1:1")
        response = _Response({"jsonrpc": "2.0", "id": 2, "result": 7, "error": None})
        with patch("goldatom.core_rpc.request.urlopen", return_value=response):
            with self.assertRaisesRegex(RpcError, "response id mismatch"):
                client.call("getblockcount")

    def test_malformed_response_is_rejected(self) -> None:
        client = JsonRpcClient("http://127.0.0.1:1")
        response = _Response([1, 2, 3])
        with patch("goldatom.core_rpc.request.urlopen", return_value=response):
            with self.assertRaisesRegex(RpcError, "response must be an object"):
                client.call("getblockcount")


if __name__ == "__main__":
    unittest.main()
