"""Portable v2 preview: explicit module/caption/media MIME types plus byte ranges."""
from __future__ import annotations
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from serve_site import PreviewHandler


class StudioHandler(PreviewHandler):
    # Windows registry mappings may otherwise serve .mjs as text/plain.
    extensions_map = {**PreviewHandler.extensions_map,
                      '.mjs': 'text/javascript', '.js': 'text/javascript',
                      '.json': 'application/json', '.vtt': 'text/vtt',
                      '.mp4': 'video/mp4', '.webm': 'video/webm', '.mp3': 'audio/mpeg',
                      '.svg': 'image/svg+xml', '.css': 'text/css'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8780)
    args = parser.parse_args()
    root = args.directory.resolve(strict=True)
    if not root.is_dir():
        parser.error('Preview directory must be a directory')
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(StudioHandler, directory=str(root))) as server:
        print(f'Studio preview: http://127.0.0.1:{server.server_port}/', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
