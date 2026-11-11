"""Copy the original silent HTML/SVG starter to a new directory. Never overwrites."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True, help='New, nonexistent project directory.')
    parser.add_argument('--title', default='The Wirelength Studio', help='Display title; no HTML interpolation.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / 'assets' / 'starter'
    destination = args.destination.expanduser().resolve()
    if destination.exists():
        parser.error(f'Destination already exists; choose a new directory: {destination}')
    if not (source / 'content' / 'script.json').is_file():
        parser.error(f'Starter assets are incomplete: {source}')
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    script_path = destination / 'content' / 'script.json'
    data = json.loads(script_path.read_text(encoding='utf-8'))
    data['title'] = args.title
    script_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    server = root / 'scripts' / 'serve_site.py'
    if server.is_file():
        shutil.copy2(server, destination / 'serve_site.py')
    print(f'Created silent storyboard starter: {destination}')
    print('No speech service or network was called. Demo timing is provisional.')
    print(f'Change directory to the project, then run: python {"serve_site.py" if server.is_file() else "-m http.server"} {"--directory . --port 8780" if server.is_file() else "8780 --bind 127.0.0.1"}')
    print('Open http://127.0.0.1:8780/ ; run node check.mjs for model checks.')


if __name__ == '__main__':
    main()
