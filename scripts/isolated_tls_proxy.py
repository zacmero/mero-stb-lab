#!/usr/bin/env python3
"""Bounded TLS pass-through for the isolated receiver's authentic service."""

import argparse
import json
import select
import socket
import threading
import time
from pathlib import Path


def relay(client: socket.socket, args: argparse.Namespace) -> None:
    started = time.monotonic()
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "client": client.getpeername()[0],
        "upstream": f"{args.upstream}:{args.upstream_port}",
        "client_bytes": 0,
        "server_bytes": 0,
        "result": "started",
    }
    upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        upstream.setsockopt(
            socket.SOL_SOCKET, socket.SO_BINDTODEVICE, args.control_interface.encode() + b"\0"
        )
        upstream.settimeout(5)
        upstream.connect((args.upstream, args.upstream_port))
        upstream.setblocking(False)
        client.setblocking(False)
        deadline = started + args.max_seconds
        sockets = (client, upstream)
        while time.monotonic() < deadline:
            readable, _, _ = select.select(sockets, (), (), 0.5)
            if not readable:
                continue
            for source in readable:
                data = source.recv(65536)
                if not data:
                    record["result"] = "closed"
                    return
                if source is client:
                    record["client_bytes"] += len(data)
                    destination = upstream
                    total = record["client_bytes"]
                else:
                    record["server_bytes"] += len(data)
                    destination = client
                    total = record["server_bytes"]
                if total > args.max_bytes:
                    record["result"] = "byte-cap"
                    return
                destination.sendall(data)
        record["result"] = "time-cap"
    except Exception as error:  # Recorded for protocol discovery.
        record["result"] = f"error:{type(error).__name__}:{error}"
    finally:
        record["duration_ms"] = round((time.monotonic() - started) * 1000)
        upstream.close()
        client.close()
        with args.log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", default="10.74.0.1")
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--receiver-interface", required=True)
    parser.add_argument("--control-interface", required=True)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--upstream-port", type=int, default=443)
    parser.add_argument("--max-seconds", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=1_048_576)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.setsockopt(
        socket.SOL_SOCKET, socket.SO_BINDTODEVICE, args.receiver_interface.encode() + b"\0"
    )
    listener.bind((args.listen, args.port))
    listener.listen(4)
    print(
        f"TLS proxy {args.receiver_interface} {args.listen}:{args.port} -> "
        f"{args.upstream}:{args.upstream_port} via {args.control_interface}",
        flush=True,
    )
    while True:
        client, address = listener.accept()
        if address[0] != "10.74.0.10":
            client.close()
            continue
        threading.Thread(target=relay, args=(client, args), daemon=True).start()


if __name__ == "__main__":
    main()
