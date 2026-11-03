#!/usr/bin/env python3
"""Validate a local educational site's media using the documented manifest contract.

Expected files are SITE/media/manifest.json and SITE/data/timings.json. The
manifest has tracks[{id, video, captions:{language:path}}], and the timing
file has languages[id] with duration and scenes[{id,start,end,cues:[...]}].
Paths are relative to SITE. This does not evaluate narration, translations,
visual synchronization, browser behavior, accessibility, or licensing.
Requires Python 3.9+ and ffprobe on PATH; no network access is used.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

TOLERANCE = 0.15  # Rendered videos can end slightly after the cue timeline.
STAMP = r"(?:(?P<{p}h>\d{{2,}}):)?(?P<{p}m>\d{{2}}):(?P<{p}s>\d{{2}})\.(?P<{p}ms>\d{{3}})"
TIMING = re.compile(r"^" + STAMP.format(p="a") + r"[ \t]+-->[ \t]+" + STAMP.format(p="b") + r"(?:[ \t]+.*)?$")


class Audit:
    def __init__(self, site: Path):
        self.site = site.resolve()
        self.errors: list[str] = []
        self.caption_count = 0
        self.video_count = 0

    def error(self, context: str, message: str):
        self.errors.append(f"{context}: {message}")

    def file(self, raw: object, context: str) -> Path | None:
        if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
            self.error(context, "expected a nonempty site-relative URL path")
            return None
        decoded = unquote(raw)
        parsed = urlsplit(decoded)
        if (parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or
                decoded.startswith("/") or "\\" in decoded or PureWindowsPath(decoded).is_absolute()):
            self.error(context, "path must be a local, relative URL without query or fragment")
            return None
        try:
            path = (self.site / decoded).resolve()
            path.relative_to(self.site)
        except (OSError, ValueError):
            self.error(context, "path resolves outside the site or is invalid")
            return None
        if not path.is_file():
            self.error(context, f"file not found: {raw}")
            return None
        return path

    def json_file(self, relative: str) -> object | None:
        path = self.file(relative, relative)
        if path is None:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            self.error(relative, f"cannot read JSON: {exc}")
            return None

    def probe(self, path: Path, context: str) -> float | None:
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-show_entries", "format=duration:stream=codec_type,codec_name,duration",
                 "-of", "json", str(path)], capture_output=True, text=True, timeout=45, check=True,
            )
            data = json.loads(proc.stdout)
            streams = data.get("streams", [])
            for kind in ("video", "audio"):
                matching = [s for s in streams if s.get("codec_type") == kind and s.get("codec_name")]
                if not matching:
                    self.error(context, f"missing {kind} stream")
                for stream in matching:
                    if stream.get("duration") not in (None, "N/A"):
                        stream_duration = float(stream["duration"])
                        if not math.isfinite(stream_duration) or stream_duration <= 0:
                            self.error(context, f"{kind} stream has invalid duration")
            duration = float(data["format"]["duration"])
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("duration must be a finite positive number")
            self.video_count += 1
            return duration
        except (OSError, subprocess.SubprocessError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self.error(context, f"ffprobe failed or returned invalid metadata: {exc}")
            return None

    def number(self, value: object, context: str) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            self.error(context, "expected a finite numeric time")
            return None
        return float(value)

    def timeline(self, info: object, media_duration: float | None, context: str):
        if not isinstance(info, dict):
            self.error(context, "missing or invalid languages[id] timeline")
            return
        duration = self.number(info.get("duration"), f"{context} duration")
        if duration is not None:
            if duration <= 0:
                self.error(context, "timeline duration must be positive")
            if media_duration is not None and abs(duration - media_duration) > TOLERANCE:
                self.error(context, f"timeline duration {duration:.3f}s differs from video {media_duration:.3f}s")
        scenes = info.get("scenes")
        if not isinstance(scenes, list) or not scenes:
            self.error(context, "scenes must be a nonempty array")
            return
        previous = 0.0
        scene_ids: set[str] = set()
        cue_ids: set[str] = set()
        for index, scene in enumerate(scenes):
            sc = f"{context} scene[{index}]"
            if not isinstance(scene, dict):
                self.error(sc, "scene must be an object")
                continue
            sid = scene.get("id")
            if not isinstance(sid, str) or not sid or sid in scene_ids:
                self.error(sc, "scene id must be a unique, nonempty string")
            else:
                scene_ids.add(sid)
            start = self.number(scene.get("start"), f"{sc} start")
            end = self.number(scene.get("end"), f"{sc} end")
            if start is not None and end is not None:
                if start < 0 or start < previous - 0.001 or start >= end:
                    self.error(sc, "scene times must be positive-length, ordered and nonoverlapping")
                if duration is not None and end > duration + 0.001:
                    self.error(sc, "scene extends past timeline duration")
                previous = end
            cues = scene.get("cues")
            if not isinstance(cues, list) or not cues:
                self.error(sc, "cues must be a nonempty array")
                continue
            cue_previous = start if start is not None else 0.0
            for ci, cue in enumerate(cues):
                cc = f"{sc} cue[{ci}]"
                if not isinstance(cue, dict):
                    self.error(cc, "cue must be an object")
                    continue
                cid = cue.get("id")
                if not isinstance(cid, str) or not cid or cid in cue_ids:
                    self.error(cc, "cue id must be a unique, nonempty string")
                else:
                    cue_ids.add(cid)
                cs = self.number(cue.get("start"), f"{cc} start")
                ce = self.number(cue.get("end"), f"{cc} end")
                if cs is not None and ce is not None:
                    if cs < cue_previous - 0.001 or cs >= ce:
                        self.error(cc, "cue times must be positive-length, ordered and nonoverlapping")
                    if start is not None and cs < start - 0.001:
                        self.error(cc, "cue starts before its scene")
                    if end is not None and ce > end + 0.001:
                        self.error(cc, "cue ends after its scene")
                    cue_previous = ce

    def captions(self, path: Path, duration: float | None, context: str):
        try:
            data = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        except (OSError, UnicodeError) as exc:
            self.error(context, f"cannot read UTF-8 captions: {exc}")
            return
        blocks = re.split(r"\n[ \t]*\n", data.strip())
        if not blocks or not re.match(r"^WEBVTT(?:[ \t].*)?(?:\n|$)", blocks[0]):
            self.error(context, "missing WEBVTT header")
            return
        count, previous = 0, 0.0
        for block in blocks[1:]:
            lines = block.splitlines()
            if not lines or re.match(r"^(NOTE(?:[ \t]|$)|STYLE$|REGION$)", lines[0]):
                continue
            timing_index = 0 if "-->" in lines[0] else 1
            if timing_index >= len(lines):
                self.error(context, "caption block has no timestamp")
                continue
            match = TIMING.fullmatch(lines[timing_index].strip())
            if not match:
                self.error(context, f"malformed timestamp: {lines[timing_index][:100]}")
                continue
            def seconds(prefix: str) -> float:
                parts = match.groupdict()
                h, m, s = int(parts[prefix+"h"] or 0), int(parts[prefix+"m"]), int(parts[prefix+"s"])
                if m > 59 or s > 59:
                    raise ValueError("minutes and seconds must be 00–59")
                return h*3600 + m*60 + s + int(parts[prefix+"ms"])/1000
            try:
                start, end = seconds("a"), seconds("b")
            except ValueError as exc:
                self.error(context, f"invalid timestamp: {exc}")
                continue
            if start < previous - 0.001 or start >= end:
                self.error(context, f"caption {count+1} has overlapping, unordered or nonpositive times")
            if duration is not None and end > duration + 0.05:
                self.error(context, f"caption {count+1} ends after the video")
            if not any(line.strip() for line in lines[timing_index+1:]):
                self.error(context, f"caption {count+1} has empty text")
            previous = end
            count += 1
        if not count:
            self.error(context, "no valid caption cues found")
        self.caption_count += 1

    def run(self):
        manifest = self.json_file("media/manifest.json")
        timing = self.json_file("data/timings.json")
        if not isinstance(manifest, dict) or not isinstance(manifest.get("tracks"), list) or not manifest["tracks"]:
            self.error("manifest", "tracks must be a nonempty array")
            return
        if not isinstance(timing, dict) or not isinstance(timing.get("languages"), dict):
            self.error("timings", "languages must be an object keyed by track id")
            return
        languages = timing["languages"]
        ids: set[str] = set()
        for i, track in enumerate(manifest["tracks"]):
            context = f"track[{i}]"
            if not isinstance(track, dict):
                self.error(context, "track must be an object")
                continue
            tid = track.get("id")
            if not isinstance(tid, str) or not tid or tid in ids:
                self.error(context, "id must be a unique, nonempty string")
                continue
            ids.add(tid)
            context = f"track {tid}"
            video = self.file(track.get("video"), f"{context} video")
            duration = self.probe(video, context) if video else None
            self.timeline(languages.get(tid), duration, context)
            captions = track.get("captions")
            if not isinstance(captions, dict) or not captions:
                self.error(context, "captions must be a nonempty language-to-path object")
                continue
            for language, raw in captions.items():
                cc = f"{context} captions[{language}]"
                path = self.file(raw, cc)
                if path:
                    self.captions(path, duration, cc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="site root containing media/manifest.json and data/timings.json")
    args = parser.parse_args()
    if not args.site.is_dir():
        print(f"ERROR: site directory does not exist: {args.site}", file=sys.stderr)
        return 2
    if not shutil.which("ffprobe"):
        print("ERROR: ffprobe not found on PATH", file=sys.stderr)
        return 2
    audit = Audit(args.site)
    audit.run()
    if audit.errors:
        print(f"FAIL: {len(audit.errors)} error(s); inspected {audit.video_count} videos and {audit.caption_count} caption files", file=sys.stderr)
        for error in audit.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"PASS: inspected {audit.video_count} videos, their timelines and {audit.caption_count} caption files")
    print("This mechanical check does not establish listening quality, translation accuracy, visual sync, browser behavior, accessibility, or licensing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
