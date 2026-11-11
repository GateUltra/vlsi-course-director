"""Optional real-browser check. Requires Playwright; serves this folder temporarily."""
from __future__ import annotations
import argparse
import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', help='Optional executable path for a local Chromium browser.')
    parser.add_argument('--screenshots', type=Path, help='Optional new directory for review screenshots.')
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parent
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/'
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, **({'executable_path': args.browser} if args.browser else {}))
            page = browser.new_page(viewport={'width': 1440, 'height': 1050})
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(url)
            page.wait_for_function('window.ready')
            assert page.locator('.status').is_visible()
            page.evaluate('starter.seek(24.5)')
            before = page.evaluate('starter.getFilmState()')
            page.click('#transfer')
            after = page.evaluate('starter.getLabState()')
            assert before['positions'] == after['positions'] and before['progress'] == after['progress']
            page.locator('#lab-board [data-pin="B"]').focus()
            x = after['positions']['B']['x']
            page.keyboard.press('ArrowLeft')
            after = page.evaluate('starter.getLabState()')
            assert abs(after['positions']['B']['x'] - (x - .5)) < 1e-9
            assert page.locator('#lab-board [data-pin="B"]').evaluate('(e)=>e===document.activeElement')
            assert after['positions']['A'] == {'x': 2, 'y': 2}
            pin = page.locator('#lab-board [data-pin="B"]').bounding_box()
            page.mouse.move(pin['x'] + pin['width'] / 2, pin['y'] + pin['height'] / 2)
            page.mouse.down()
            page.mouse.move(pin['x'] + pin['width'] / 2 + 40, pin['y'] + pin['height'] / 2 - 20, steps=4)
            page.mouse.up()
            dragged = page.evaluate('starter.getLabState()')
            assert dragged['positions']['B'] != after['positions']['B']
            assert dragged['positions']['A'] == {'x': 2, 'y': 2}
            for point in [{'x': 5, 'y': 4}, {'x': 2, 'y': 7}]:
                page.evaluate('(p)=>starter.setB(p)', point)
                page.click('#check')
                assert page.locator('#feedback').inner_text().startswith('Yes')
            page.evaluate('starter.setB({x:8,y:7})')
            page.click('#check')
            assert 'above the 6-unit maximum' in page.locator('#feedback').inner_text()
            for point, expected in [({'x': 5.03, 'y': 5}, 'above the 6-unit maximum'), ({'x': 4.99, 'y': 2}, 'below the 3-unit minimum')]:
                page.evaluate('(p)=>starter.setB(p)', point)
                page.click('#check')
                assert expected in page.locator('#feedback').inner_text()
                assert 'rounded' in page.locator('#score').inner_text()
            for point in [{'x': 5, 'y': 2}, {'x': 8, 'y': 2}]:
                page.evaluate('(p)=>starter.setB(p)', point)
                page.click('#check')
                assert page.locator('#feedback').inner_text().startswith('Yes')
            page.click('#reset')
            page.locator('#lab-board [data-pin="B"]').focus()
            for _ in range(50):
                page.keyboard.press('Shift+ArrowDown')
            keyboard_state = page.evaluate('starter.getLabState()')
            assert abs(keyboard_state['positions']['B']['y'] - 2) < 1e-12
            page.click('#check')
            assert page.locator('#feedback').inner_text().startswith('Yes')
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            for selector in ['#film-readout', '#lab-readout']:
                assert page.locator(selector).is_visible()
                assert page.locator(selector + ' dd').count() == 4
                sizes = page.locator(selector + ' dt, ' + selector + ' dd').evaluate_all('(nodes)=>nodes.map(n=>parseFloat(getComputedStyle(n).fontSize))')
                assert min(sizes) >= 14, sizes
            assert page.locator('#lab-readout').inner_text().find('(8.00, 2.00)') >= 0
            for selector in ['#spoken-text', '.model-definition', '.small']:
                assert page.locator(selector).evaluate('(n)=>parseFloat(getComputedStyle(n).fontSize)') >= 14
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / 'mobile.png'), full_page=True)
            page.set_viewport_size({'width': 1920, 'height': 1080})
            page.goto(url + 'render.html')
            page.wait_for_function('window.ready')
            first = page.evaluate('renderAt(25)')
            page.evaluate('renderAt(1)')
            assert first == page.evaluate('renderAt(25)')
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / 'render.png'))
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps({'ok': True, 'checks': ['exact transfer', 'keyboard and focus', 'fixed A', 'pointer drag', 'two valid exercise answers', 'failed answer', 'unrounded boundary feedback and inclusive endpoints', '50 small keyboard moves retain valid endpoint', '390px no overflow and 14px+ HTML measurements and definitions', 'random access renderer'], 'errors': errors}, indent=2))


if __name__ == '__main__':
    main()
