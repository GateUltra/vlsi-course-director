"""Serve a local static site with single-range requests for video scrubbing.

Run: python serve_site.py --directory PATH --port 8765
The server listens on 127.0.0.1 only; Ctrl+C stops it.
"""
from __future__ import annotations

import argparse
import re
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class PreviewHandler(SimpleHTTPRequestHandler):
    """Serve GET and HEAD; reject symlinks that escape the preview root."""

    def __init__(self, *args, directory: str, **kwargs):
        self.preview_root = Path(directory).resolve(strict=True)
        super().__init__(*args, directory=str(self.preview_root), **kwargs)

    def inside_root(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.preview_root)
            return True
        except (ValueError, OSError, RuntimeError):
            return False

    def range_error(self, size: int):
        self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
        self.send_header("Content-Range", f"bytes */{size}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return None

    def send_head(self):
        self.byte_range = None
        filename = Path(self.translate_path(self.path))
        if not self.inside_root(filename):
            self.send_error(HTTPStatus.FORBIDDEN, "Path outside preview directory")
            return None
        # SimpleHTTPRequestHandler also resolves directory indexes; ensure an
        # index symlink cannot bypass the regular file check above.
        if filename.is_dir():
            for index in (filename / "index.html", filename / "index.htm"):
                if index.is_file() and not self.inside_root(index):
                    self.send_error(HTTPStatus.FORBIDDEN, "Path outside preview directory")
                    return None
                if index.is_file():
                    break
        header = self.headers.get("Range")
        if not header or not filename.is_file():
            return super().send_head()

        try:
            size = filename.stat().st_size
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
            if not match or (not match.group(1) and not match.group(2)) or size == 0:
                return self.range_error(size)
            if match.group(1):
                start = int(match.group(1))
                end = min(int(match.group(2)), size - 1) if match.group(2) else size - 1
            else:
                start = max(0, size - int(match.group(2)))
                end = size - 1
            if start >= size or start > end:
                return self.range_error(size)
            stream = filename.open("rb")
            stream.seek(start)
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File unavailable")
            return None

        self.byte_range = (start, end)
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(str(filename)))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Last-Modified", self.date_time_string(filename.stat().st_mtime))
        self.end_headers()
        return stream

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        remaining = self.byte_range[1] - self.byte_range[0] + 1
        while remaining:
            chunk = source.read(min(65536, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=".", help="Static site directory (default: current directory)")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")
    if not 0 <= args.port <= 65535:
        parser.error("Port must be in 0–65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(PreviewHandler, directory=str(root)))
    print(f"Serving {root} at http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
