"""Smoke-test portable helpers without contacting online services.

Default: clocks, caption bounds and localhost HTTP ranges (stdlib only).
--integration additionally encodes/retimes/decodes a tiny deterministic HTML
movie using Playwright, Chromium and FFmpeg. Artifacts use a temporary folder.
"""
from __future__ import annotations
import argparse
import copy
import json
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from retime_video import cuts_for
from render_html import check_page_clock
from serve_site import PreviewHandler
from validate_media import check_vtt, local_asset, matching_clocks, validate_clock, validate_site


def expect_error(operation):
    try:
        operation()
    except (ValueError, KeyError):
        return
    raise AssertionError("Expected a bad input to be rejected")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integration", action="store_true")
    parser.add_argument("--browser")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    source = {"duration": 1.8, "segments": [{"id": "measure", "start": .2, "end": .7, "sceneEnd": .8}, {"id": "move", "start": .8, "end": 1.4, "sceneEnd": 1.6}]}
    target = {"duration": 2.2, "segments": [{"id": "measure", "start": .2, "end": .9, "sceneEnd": 1.0}, {"id": "move", "start": 1.0, "end": 1.8, "sceneEnd": 2.0}]}
    matching_clocks(source, target, contiguous=True)
    check_page_clock(source, source)
    expect_error(lambda: check_page_clock(source, target))
    wrong_interval = copy.deepcopy(source)
    wrong_interval["segments"][0]["end"] = .6
    expect_error(lambda: check_page_clock(wrong_interval, source))
    assert sum(c["endFrame"] - c["startFrame"] for c in cuts_for(source, target, 10)) == 22
    no_tail = {"duration": 1.03, "segments": [{"id": "only", "start": 0, "end": .8, "sceneEnd": 1.03}]}
    assert cuts_for(no_tail, no_tail, 30)[-1]["endFrame"] == 31
    bad = copy.deepcopy(target); bad["segments"][1]["id"] = "different"
    expect_error(lambda: matching_clocks(source, bad))
    bad = copy.deepcopy(target); bad["segments"].pop()
    expect_error(lambda: matching_clocks(source, bad))
    bad = copy.deepcopy(target); bad["segments"][1]["start"] += .1
    expect_error(lambda: cuts_for(source, bad, 30))
    bad = copy.deepcopy(target); bad["segments"][1]["start"] = .5
    expect_error(lambda: validate_clock(bad))
    bad = copy.deepcopy(target); bad["duration"] = float("nan")
    expect_error(lambda: validate_clock(bad))
    bad = copy.deepcopy(target); bad["segments"][1]["id"] = "measure"
    expect_error(lambda: validate_clock(bad))
    with tempfile.TemporaryDirectory(prefix="course-tooling-check-") as temp:
        root = Path(temp)
        (root / "bytes.bin").write_bytes(b"0123456789")
        (root / "caption.vtt").write_text("WEBVTT\n\n00:00:00.200 --> 00:00:00.900\n48.1 remains one number.\n\n00:00:01.000 --> 00:00:01.800\nMove the point.\n", encoding="utf8")
        assert check_vtt(root / "caption.vtt", 2.2) == 2
        expect_error(lambda: check_vtt(root / "caption.vtt", .7))
        expect_error(lambda: local_asset(root, "../escape.mp4"))
        expect_error(lambda: local_asset(root, "https://example.com/clip.mp4"))
        expect_error(lambda: local_asset(root, "missing.mp4"))
        class QuietHandler(PreviewHandler):
            def log_message(self, *values):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/"
        try:
            with urllib.request.urlopen(urllib.request.Request(url + "bytes.bin", headers={"Range": "bytes=2-5"})) as result:
                assert result.status == 206 and result.read() == b"2345"
                assert result.headers["Content-Range"] == "bytes 2-5/10"
            with urllib.request.urlopen(urllib.request.Request(url + "bytes.bin", headers={"Range": "bytes=-3"}, method="HEAD")) as result:
                assert result.status == 206 and result.headers["Content-Length"] == "3" and result.read() == b""
            try:
                urllib.request.urlopen(urllib.request.Request(url + "bytes.bin", headers={"Range": "bytes=12-13"}))
                raise AssertionError("Invalid range must fail")
            except urllib.error.HTTPError as error:
                assert error.code == 416
            if args.integration:
                (root / "source.json").write_text(json.dumps(source), encoding="utf8")
                (root / "target.json").write_text(json.dumps(target), encoding="utf8")
                (root / "render.html").write_text('''<!doctype html><html><head><link rel="icon" href="data:,"><style>body{margin:0;background:#fff9ec}svg{display:block}</style></head><body><svg width="320" height="180"><circle id="point" cx="30" cy="90" r="24" fill="#397f75"/><text id="time-label" x="20" y="30">0</text></svg><script type="module">window.clock=await (await fetch('source.json')).json();window.renderAt=t=>{document.querySelector('#point').setAttribute('cx',30+120*t);document.querySelector('#time-label').textContent=t.toFixed(3)};window.ready=true;</script></body></html>''', encoding="utf8")
                render = [sys.executable, str(scripts / "render_html.py"), "--url", url + "render.html", "--clock", str(root / "source.json"), "--output", str(root / "picture.mp4"), "--preview-dir", str(root / "frames"), "--fps", "10", "--width", "320", "--height", "180", "--ffmpeg", args.ffmpeg]
                if args.browser:
                    render += ["--browser", args.browser]
                subprocess.run(render, check=True)
                mismatch = render.copy()
                mismatch[mismatch.index("--clock") + 1] = str(root / "target.json")
                mismatch[mismatch.index("--output") + 1] = str(root / "preserved.mp4")
                mismatch[mismatch.index("--preview-dir") + 1] = str(root / "wrong-frames")
                (root / "preserved.mp4").write_bytes(b"previous output remains intact")
                mismatch += ["--overwrite"]
                failure = subprocess.run(mismatch, capture_output=True, text=True)
                assert failure.returncode != 0 and "Page clock differs from --clock" in failure.stderr
                assert (root / "preserved.mp4").read_bytes() == b"previous output remains intact"
                assert not (root / "wrong-frames").exists()
                subprocess.run([args.ffmpeg, "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2.2", "-ar", "48000", str(root / "audio.wav")], check=True)
                subprocess.run([sys.executable, str(scripts / "retime_video.py"), "--source", str(root / "picture.mp4"), "--source-clock", str(root / "source.json"), "--target-clock", str(root / "target.json"), "--audio", str(root / "audio.wav"), "--output", str(root / "lesson.mp4"), "--fps", "10", "--ffmpeg", args.ffmpeg, "--ffprobe", args.ffprobe], check=True)
                manifest = {"defaultVoice": "test", "captionLanguages": ["en"], "tracks": [{"id": "test", "video": "lesson.mp4", "timing": "target.json", "captions": {"en": "caption.vtt"}}]}
                (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf8")
                record = validate_site(root, root / "manifest.json", ffmpeg=args.ffmpeg, ffprobe=args.ffprobe, decode=True)
                assert record["tracks"][0]["fps"] == 10
                assert abs(record["tracks"][0]["duration"] - 2.2) < .01
                assert len(list((root / "frames").glob("*.png"))) == 2
                provisional = copy.deepcopy(target); provisional["provisional"] = True
                (root / "target.json").write_text(json.dumps(provisional), encoding="utf8")
                expect_error(lambda: validate_site(root, root / "manifest.json", ffprobe=args.ffprobe))
                (root / "target.json").write_text(json.dumps(target), encoding="utf8")
                subprocess.run([args.ffmpeg, "-v", "error", "-y", "-i", str(root / "lesson.mp4"), "-f", "lavfi", "-i", "sine=frequency=440:duration=0.2", "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", str(root / "short-audio.mp4")], check=True)
                subprocess.run([args.ffmpeg, "-v", "error", "-y", "-i", str(root / "picture.mp4"), "-i", str(root / "audio.wav"), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", str(root / "short-video.mp4")], check=True)
                for invalid in ("short-audio.mp4", "short-video.mp4"):
                    manifest["tracks"][0]["video"] = invalid
                    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf8")
                    expect_error(lambda: validate_site(root, root / "manifest.json", ffprobe=args.ffprobe))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    print(json.dumps({"result": "PASS", "clockAndCaptionChecks": True, "httpRangeChecks": True, "htmlRenderRetimeMuxDecode": args.integration, "wrongPageClockRejectedAndOutputPreserved": args.integration, "provisionalAndTruncatedStreamsRejected": args.integration}))


if __name__ == "__main__":
    main()
