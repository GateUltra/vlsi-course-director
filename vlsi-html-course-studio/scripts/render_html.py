"""Render deterministic HTML/SVG scenes to H.264, or inspect selected PNG frames.

Page contract: window.ready === true and window.renderAt(seconds) render a
complete random-access state. Start a local static server separately.
"""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import tempfile
import time
from pathlib import Path
from validate_media import load_json, validate_clock, matching_clocks


def check_page_clock(page_clock, clock):
    """Catch a URL selecting another voice while --clock names this voice."""
    matching_clocks(page_clock, clock)
    if abs(page_clock["duration"] - clock["duration"]) > 1e-7:
        raise ValueError("Page clock differs from --clock: duration")
    for actual, expected in zip(page_clock["segments"], clock["segments"]):
        for field in ("start", "end", "sceneEnd"):
            if abs(actual[field] - expected[field]) > 1e-7:
                raise ValueError(f"Page clock differs from --clock: {actual['id']}.{field}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--clock", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Silent MP4; omitted when only making previews")
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--preview-times", default="", help="Comma-separated seconds; defaults to each cue's midpoint")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--browser", help="Optional Chromium/Chrome executable; otherwise Playwright's installed Chromium")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if not args.output and not args.preview_dir:
        parser.error("Choose --output and/or --preview-dir")
    if args.fps <= 0 or min(args.width, args.height) <= 0 or args.width % 2 or args.height % 2:
        parser.error("Positive fps and even positive dimensions are required")
    if args.output and args.output.suffix.lower() != ".mp4":
        parser.error("--output must end in .mp4")
    if args.output and args.output.exists() and not args.overwrite:
        parser.error("Output exists; choose a new path or pass --overwrite")
    clock = validate_clock(load_json(args.clock))
    frames = math.ceil(clock["duration"] * args.fps)
    from playwright.sync_api import sync_playwright
    errors = []
    with sync_playwright() as pw:
        launch = {"headless": True, "args": ["--disable-background-timer-throttling", "--hide-scrollbars"]}
        if args.browser:
            launch["executable_path"] = args.browser
        browser = pw.chromium.launch(**launch)
        try:
            page = browser.new_page(viewport={"width": args.width, "height": args.height}, device_scale_factor=1)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda response: errors.append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
            page.goto(args.url, wait_until="domcontentloaded")
            page.wait_for_function("window.ready === true && typeof window.renderAt === 'function'")
            page_clock = page.evaluate("() => window.clock ?? null")
            if page_clock is not None:
                check_page_clock(page_clock, clock)
            page.evaluate("() => document.fonts.ready")
            page.evaluate("() => Promise.all([...document.images].map(im => im.decode()))")
            if args.preview_dir:
                args.preview_dir.mkdir(parents=True, exist_ok=True)
                times = [float(t) for t in args.preview_times.split(",")] if args.preview_times else [(s["start"] + s["sceneEnd"]) / 2 for s in clock["segments"]]
                for i, second in enumerate(times):
                    if not math.isfinite(second) or not 0 <= second <= clock["duration"]:
                        raise ValueError(f"Preview time outside clock: {second}")
                    page.evaluate("t => window.renderAt(t)", second)
                    page.screenshot(path=str(args.preview_dir / f"{i:03d}-{second:.3f}s.png"))
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                started = time.monotonic()
                # A failed encode leaves any existing final output untouched.
                with tempfile.TemporaryDirectory(prefix="html-render-", dir=args.output.parent) as temp:
                    temporary = Path(temp) / "picture.mp4"
                    log_path = Path(temp) / "ffmpeg.log"
                    command = [args.ffmpeg, "-v", "error", "-y", "-f", "image2pipe", "-vcodec", "mjpeg", "-framerate", str(args.fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", str(args.crf), "-pix_fmt", "yuv420p", "-g", str(args.fps), "-movflags", "+faststart", str(temporary)]
                    with log_path.open("wb") as log:
                        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
                        try:
                            for frame in range(frames):
                                page.evaluate("t => window.renderAt(t)", frame / args.fps)
                                process.stdin.write(page.screenshot(type="jpeg", quality=95))
                                if frame % max(1, args.fps * 20) == 0:
                                    print(f"Rendered {frame}/{frames} frames", flush=True)
                            process.stdin.close()
                            if process.wait() != 0:
                                raise RuntimeError("FFmpeg encode failed")
                            if errors:
                                raise RuntimeError("Page errors: " + "; ".join(errors))
                        except BaseException:
                            process.kill()
                            process.wait()
                            if process.stdin and not process.stdin.closed:
                                process.stdin.close()
                            log.flush()
                            print(log_path.read_text(encoding="utf8", errors="replace"), flush=True)
                            raise
                    temporary.replace(args.output)
                record = {"frames": frames, "fps": args.fps, "clockDuration": clock["duration"], "pageClockChecked": page_clock is not None, "dimensions": [args.width, args.height], "wallSeconds": round(time.monotonic() - started, 3), "pageErrors": errors}
                args.output.with_suffix(".render.json").write_text(json.dumps(record, indent=2), encoding="utf8")
                print(json.dumps(record))
            elif errors:
                raise RuntimeError("Page errors: " + "; ".join(errors))
        finally:
            browser.close()


if __name__ == "__main__":
    main()
