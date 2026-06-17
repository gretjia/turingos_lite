"""Minimal JSON-RPC 2.0 framing over unix socket (line-delimited JSON). No extra deps."""
import json
from typing import Any


class RPCError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"RPCError {code}: {message}")


def make_request(method: str, params: dict | None = None, req_id: Any = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params or {},
    }


def make_response(result: Any, req_id: Any = 1) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(error: RPCError, req_id: Any = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": error.code, "message": error.message, "data": error.data},
    }


def serialize(obj: dict) -> bytes:
    return (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")


def deserialize(data: bytes | str) -> dict:
    text = data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data
    return json.loads(text.strip())


def send_message(sock, obj: dict) -> None:
    sock.sendall(serialize(obj))


def recv_message(sock, bufsize: int = 65536) -> dict:
    data = sock.recv(bufsize)
    if not data:
        raise RPCError(-32603, "empty response")
    return deserialize(data)
