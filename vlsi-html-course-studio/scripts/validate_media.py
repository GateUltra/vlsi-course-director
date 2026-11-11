"""Check local lesson manifest, measured clocks, captions and encoded media.

No online requests or speech generation. Mechanical checks do not prove teaching
accuracy, pronunciation, translation quality, or audio-to-picture synchrony.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_clock(clock, *, contiguous=False):
    def number(value, name):
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number")
        return value
    duration = number(clock.get("duration"), "duration")
    segments = clock.get("segments")
    if duration <= 0 or not isinstance(segments, list) or not segments:
        raise ValueError("Clock needs positive duration and nonempty segments")
    ids = set()
    previous = None
    for segment in segments:
        sid = segment.get("id")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError(f"Missing or duplicate cue id: {sid!r}")
        ids.add(sid)
        start, end, scene_end = [number(segment.get(k), f"{sid}.{k}") for k in ("start", "end", "sceneEnd")]
        if not 0 <= start <= end <= scene_end <= duration or scene_end <= start:
            raise ValueError(f"Invalid clock interval for {sid}")
        if previous is not None:
            if start < previous - 1e-7:
                raise ValueError(f"Overlapping cue: {sid}")
            if contiguous and abs(start - previous) > 1e-7:
                raise ValueError(f"Unrepresented gap before {sid}; put pauses inside sceneEnd")
        previous = scene_end
    return clock


def matching_clocks(source, target, *, contiguous=False):
    validate_clock(source, contiguous=contiguous)
    validate_clock(target, contiguous=contiguous)
    a = [s["id"] for s in source["segments"]]
    b = [s["id"] for s in target["segments"]]
    if a != b:
        raise ValueError("Source and target must contain the same cue IDs in the same order")


def probe(path, ffprobe="ffprobe"):
    return json.loads(subprocess.check_output([
        ffprobe, "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height,avg_frame_rate,duration,nb_frames,start_time",
        "-of", "json", str(path)], text=True))


def local_asset(root, value):
    if not isinstance(value, str) or not value:
        raise ValueError("Asset path must be a nonempty relative string")
    parsed = urlsplit(value)
    path = Path(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or path.is_absolute():
        raise ValueError(f"Use a local relative asset path: {value}")
    result = (root / path).resolve()
    try:
        result.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Asset escapes site root: {value}") from exc
    if not result.is_file() or not result.stat().st_size:
        raise ValueError(f"Missing or empty asset: {value}")
    return result


def check_vtt(path, duration):
    text = Path(path).read_text(encoding="utf-8-sig")
    if not text.startswith("WEBVTT"):
        raise ValueError(f"Missing WEBVTT header: {path}")
    pattern = r"(?m)^(\d{2,}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2,}:\d{2}:\d{2}\.\d{3})[^\n]*$"
    def seconds(value):
        h, m, s = value.split(":")
        if int(m) >= 60 or float(s) >= 60:
            raise ValueError(f"Invalid VTT timestamp: {value}")
        return int(h) * 3600 + int(m) * 60 + float(s)
    matches = list(re.finditer(pattern, text))
    if not matches or len(matches) != text.count("-->"):
        raise ValueError(f"Missing/malformed VTT timestamps: {path}")
    previous = 0
    for match in matches:
        start, end = map(seconds, match.groups())
        if start < previous - .002 or not 0 <= start < end <= duration + .002:
            raise ValueError(f"Overlapping or out-of-bounds caption: {path}: {match.group()}")
        # Cue settings are allowed, but an actual text payload must follow.
        tail = text[match.end():].split("\n\n", 1)[0].strip()
        if not tail:
            raise ValueError(f"Empty caption text: {path}")
        previous = end
    return len(matches)


def validate_site(root, manifest_path, *, ffprobe="ffprobe", ffmpeg="ffmpeg", decode=False):
    root = Path(root).resolve(strict=True)
    manifest = load_json(manifest_path)
    tracks = manifest.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("Manifest needs nonempty tracks")
    track_ids = [t.get("id") for t in tracks]
    if any(not isinstance(s, str) or not s for s in track_ids) or len(set(track_ids)) != len(track_ids):
        raise ValueError("Track IDs must be nonempty and unique")
    if manifest.get("defaultVoice") not in track_ids:
        raise ValueError("defaultVoice must name a track")
    reference = None
    records = []
    for track in tracks:
        timing = local_asset(root, track["timing"])
        clock = validate_clock(load_json(timing), contiguous=True)
        if clock.get("provisional") is True:
            raise ValueError(f"Final narration cannot use a provisional storyboard clock: {track['id']}")
        if reference is not None:
            matching_clocks(reference, clock, contiguous=True)
        reference = reference or clock
        video = local_asset(root, track["video"])
        data = probe(video, ffprobe)
        streams = data.get("streams", [])
        v = next((s for s in streams if s["codec_type"] == "video"), None)
        a = next((s for s in streams if s["codec_type"] == "audio"), None)
        if not v or not a:
            raise ValueError(f"Final narrated video needs both video and audio streams: {video}")
        numerator, denominator = map(float, v["avg_frame_rate"].split("/"))
        fps = numerator / denominator if denominator else 0
        if fps <= 0:
            raise ValueError(f"Invalid video frame rate: {video}")
        actual = float(data["format"]["duration"])
        if not math.isfinite(actual) or abs(actual - clock["duration"]) > 1 / fps + .01:
            raise ValueError(f"Duration mismatch for {track['id']}: media {actual}, clock {clock['duration']}")
        for stream in (v, a):
            kind = stream["codec_type"]
            try:
                stream_duration = float(stream["duration"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Cannot verify {kind} stream duration: {video}") from exc
            tolerance = 1 / fps + .01 if kind == "video" else .05
            if not math.isfinite(stream_duration) or abs(stream_duration - clock["duration"]) > tolerance:
                raise ValueError(f"{kind} stream duration mismatch for {track['id']}: {stream_duration}, clock {clock['duration']}")
            if abs(float(stream.get("start_time", 0))) > .05:
                raise ValueError(f"Nonzero stream offset: {video}")
        captions = track.get("captions", {})
        missing = set(manifest.get("captionLanguages", [])) - set(captions)
        if missing:
            raise ValueError(f"{track['id']} lacks requested caption languages: {sorted(missing)}")
        caption_counts = {lang: check_vtt(local_asset(root, path), clock["duration"]) for lang, path in captions.items()}
        if decode:
            subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(video), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], check=True, stdout=subprocess.DEVNULL)
        records.append({"id": track["id"], "duration": actual, "videoDuration": float(v["duration"]), "audioDuration": float(a["duration"]), "clockDuration": clock["duration"], "fps": fps, "videoCodec": v["codec_name"], "audioCodec": a["codec_name"], "captionCues": caption_counts, "fullDecode": decode})
    return {"tracks": records, "scope": "Mechanical file, clock, caption and media checks; no human audition or translation review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--manifest", default="media/manifest.json", help="Relative to --site")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--decode", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.site.resolve(strict=True)
    result = validate_site(root, local_asset(root, args.manifest), ffprobe=args.ffprobe, ffmpeg=args.ffmpeg, decode=args.decode)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf8")
    print(output)


if __name__ == "__main__":
    main()
