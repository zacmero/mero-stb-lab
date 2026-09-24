#!/usr/bin/env python3
"""Serve selected local videos to the isolated receiver laptop."""

import argparse
import hashlib
import http.server
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
    ".ts": "video/mp2t",
}
VIDEO_ID = re.compile(r"[0-9a-f]{16}\Z")
BYTE_RANGE = re.compile(r"bytes=(\d*)-(\d*)\Z")


def library(root: Path) -> dict[str, Path]:
    videos = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in MEDIA_TYPES:
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            continue
        relative = resolved.relative_to(root).as_posix()
        videos[hashlib.sha256(relative.encode()).hexdigest()[:16]] = resolved
    return videos


def select_range(header: str | None, size: int) -> tuple[int, int, bool]:
    if not header:
        return 0, size - 1, False
    match = BYTE_RANGE.fullmatch(header.strip())
    if not match or size == 0 or not any(match.groups()):
        raise ValueError("invalid byte range")
    first, last = match.groups()
    if first:
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
    else:
        suffix = int(last)
        if suffix == 0:
            raise ValueError("invalid suffix")
        start, end = max(size - suffix, 0), size - 1
    if start >= size or start > end:
        raise ValueError("unsatisfiable byte range")
    return start, end, True


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self) -> None:
        self.handle_video(send_body=False)

    def do_GET(self) -> None:
        self.handle_video(send_body=True)

    def handle_video(self, send_body: bool) -> None:
        if self.client_address[0] not in (self.server.allowed_client, "127.0.0.1"):  # type: ignore[attr-defined]
            self.send_error(403)
            return
        path = urlsplit(self.path).path
        videos = library(self.server.root)  # type: ignore[attr-defined]
        if path in ("/api/videos", "/video019/list"):
            entries = [
                {"id": video_id, "title": str(file.relative_to(self.server.root)), "bytes": file.stat().st_size}  # type: ignore[attr-defined]
                for video_id, file in sorted(videos.items(), key=lambda item: str(item[1]).lower())
            ]
            body = json.dumps(entries, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if send_body:
                self.wfile.write(body)
            return
        video_id = (path.removeprefix("/video/") if path.startswith("/video/") else
                    path.removeprefix("/video019/media/") if path.startswith("/video019/media/") else "")
        if not VIDEO_ID.fullmatch(video_id) or video_id not in videos:
            self.send_error(404)
            return
        file = videos[video_id]
        size = file.stat().st_size
        try:
            start, end, partial = select_range(self.headers.get("Range"), size)
        except ValueError:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        length = max(end - start + 1, 0)
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", MEDIA_TYPES[file.suffix.lower()])
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if not send_body:
            return
        with file.open("rb") as stream:
            stream.seek(start)
            remaining = length
            while remaining:
                chunk = stream.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/home/zacmero/Videos"))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=39019)
    parser.add_argument("--allow-client", default="127.0.0.1")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    if not root.is_dir():
        parser.error("video root must be a directory")
    server = http.server.ThreadingHTTPServer((args.bind, args.port), Handler)
    server.root = root
    server.allowed_client = args.allow_client
    print(f"Video library ready: {root} on {args.bind}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
