"""turingd: Unix socket JSON-RPC server (Phase 10).
Listens, handles via commands (predicate + wtool always). Clean shutdown.
Socket path derived from TURINGOS_DATA_DIR or default. Per-charter: daemon + unix JSON-RPC.
Surgical: no TUI writes, no mixing tapes. Run via `python -m turingos.daemon.server`.
"""
import argparse
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any

from .rpc import (
    RPCError,
    make_response,
    make_error,
    deserialize,
    serialize,
    send_message,
)
from .commands import dispatch


DEFAULT_DATA = Path.home() / ".local" / "share" / "turingos"
SOCK_NAME = "turingd.sock"


def get_socket_path(data_dir: Path | None = None) -> Path:
    if data_dir is None:
        env = os.environ.get("TURINGOS_DATA_DIR")
        data_dir = Path(env) if env else DEFAULT_DATA
    run_dir = data_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir / SOCK_NAME


def handle_client(conn: socket.socket, addr: Any) -> None:
    try:
        raw = conn.recv(65536)
        if not raw:
            return
        req = deserialize(raw)
        method = req.get("method")
        params = req.get("params", {}) or {}
        rid = req.get("id", 1)
        try:
            result = dispatch(method, params)
            resp = make_response(result, rid)
        except Exception as e:
            err = RPCError(-32000, str(e)[:200])
            resp = make_error(err, rid)
        send_message(conn, resp)
    except Exception as e:
        try:
            err = RPCError(-32603, f"server error: {e}"[:200])
            send_message(conn, make_error(err, req.get("id", 1) if "req" in locals() else 1))
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_server(sock_path: Path | None = None, stop_event: threading.Event | None = None) -> None:
    sp = sock_path or get_socket_path()
    # cleanup stale
    try:
        if sp.exists():
            sp.unlink()
    except Exception:
        pass

    server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(str(sp))
    server_sock.listen(8)
    server_sock.settimeout(1.0)

    def _shutdown(sig=None, frame=None):
        if stop_event:
            stop_event.set()
        try:
            server_sock.close()
        except Exception:
            pass
        try:
            if sp.exists():
                sp.unlink()
        except Exception:
            pass
        # do not sys.exit in thread

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    print(f"turingd listening on {sp}", file=sys.stderr)
    try:
        while not (stop_event and stop_event.is_set()):
            try:
                conn, _ = server_sock.accept()
                t = threading.Thread(target=handle_client, args=(conn, None), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                if stop_event and stop_event.is_set():
                    break
                raise
    finally:
        try:
            server_sock.close()
        except Exception:
            pass
        try:
            if sp.exists():
                sp.unlink()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="TuringOS Lite turingd (Phase 10 daemon)")
    ap.add_argument("--sock", type=str, default=None, help="explicit unix socket path")
    args = ap.parse_args(argv or sys.argv[1:])
    sp = Path(args.sock) if args.sock else None
    stop = threading.Event()
    run_server(sp, stop)


if __name__ == "__main__":
    main()
