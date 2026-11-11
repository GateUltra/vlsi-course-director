"""Match semantic picture regions to another measured voice clock.

Only the picture is retimed. Optional --audio must already span the target
programme clock. Do not use cue retiming for phoneme-locked mouth animation.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import math
import subprocess
import tempfile
from pathlib import Path
from validate_media import load_json, matching_clocks, probe


def cuts_for(source, target, fps):
    matching_clocks(source, target, contiguous=True)
    if fps <= 0:
        raise ValueError("fps must be positive")
    regions = [("intro", 0, source["segments"][0]["start"], 0, target["segments"][0]["start"])]
    for a, b in zip(source["segments"], target["segments"]):
        regions.append((a["id"], a["start"], a["sceneEnd"], b["start"], b["sceneEnd"]))
    regions.append(("tail", source["segments"][-1]["sceneEnd"], source["duration"], target["segments"][-1]["sceneEnd"], target["duration"]))
    filtered = []
    for region in regions:
        sid, a, b, x, y = region
        if abs(b - a) < 1e-7 and abs(y - x) < 1e-7:
            continue
        if min(b - a, y - x) < 1e-7:
            raise ValueError(f"Region {sid} is absent in one clock; render that voice directly")
        filtered.append(region)
    regions = filtered
    cuts = []
    for i, (sid, a, b, x, y) in enumerate(regions):
        # Quantise cumulative boundaries, never independently round each length.
        source_start = round(a * fps)
        source_end = math.ceil(b * fps) if i == len(regions) - 1 else round(b * fps)
        start = round(x * fps)
        end = math.ceil(y * fps) if i == len(regions) - 1 else round(y * fps)
        source_n = source_end - source_start
        n = end - start
        if source_n == 0 and n == 0:
            continue
        if min(source_n, n) <= 0:
            raise ValueError(f"Region {sid} has no frames in one clock; extend it or render that voice directly")
        cuts.append({"id": sid, "sourceStartFrame": source_start, "sourceEndFrame": source_end, "startFrame": start, "endFrame": end})
    for left, right in zip(cuts, cuts[1:]):
        if left["endFrame"] != right["startFrame"] or left["sourceEndFrame"] != right["sourceStartFrame"]:
            raise ValueError("Clock contains an unrepresented frame gap")
    if cuts[0]["startFrame"] != 0 or cuts[-1]["endFrame"] != math.ceil(target["duration"] * fps):
        raise ValueError("Cuts do not cover complete programme")
    return cuts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Silent primary MP4")
    parser.add_argument("--source-clock", type=Path, required=True)
    parser.add_argument("--target-clock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audio", type=Path, help="Optional complete target narration/music WAV")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    if args.output.suffix.lower() != ".mp4":
        parser.error("--output must end in .mp4")
    if args.output.exists() and not args.overwrite:
        parser.error("Output exists; choose a new path or pass --overwrite")
    if args.output.resolve() in [p.resolve() for p in (args.source, args.source_clock, args.target_clock, args.audio) if p]:
        parser.error("Output cannot replace an input")
    source, target = load_json(args.source_clock), load_json(args.target_clock)
    cuts = cuts_for(source, target, args.fps)
    source_info = probe(args.source, args.ffprobe)
    video = next(s for s in source_info["streams"] if s["codec_type"] == "video")
    numerator, denominator = map(float, video["avg_frame_rate"].split("/"))
    if abs(numerator / denominator - args.fps) > 1e-6:
        raise ValueError("Source picture fps must match --fps")
    if abs(float(source_info["format"]["duration"]) - source["duration"]) > 1 / args.fps + .01:
        raise ValueError("Source movie duration does not match its clock")
    if args.audio:
        info = probe(args.audio, args.ffprobe)
        if not any(s["codec_type"] == "audio" for s in info["streams"]):
            raise ValueError("Target audio has no audio stream")
        if abs(float(info["format"]["duration"]) - target["duration"]) > .05:
            raise ValueError("Target audio must include the full target clock, including pauses, intro and tail")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def ffmpeg(parts):
        subprocess.run([args.ffmpeg, "-v", "error", "-y", *map(str, parts)], check=True)
    with tempfile.TemporaryDirectory(prefix="cue-retime-", dir=args.output.parent) as temporary:
        folder = Path(temporary)
        def encode(item):
            index, cut = item
            n = cut["endFrame"] - cut["startFrame"]
            old = cut["sourceEndFrame"] - cut["sourceStartFrame"]
            filters = f"setpts=PTS-STARTPTS,setpts={n / old:.12f}*PTS,fps={args.fps},tpad=stop_mode=clone:stop_duration=2"
            file = folder / f"{index:04d}.mp4"
            ffmpeg(["-ss", cut["sourceStartFrame"] / args.fps, "-t", old / args.fps, "-i", args.source, "-an", "-vf", filters, "-frames:v", n, "-c:v", "libx264", "-threads", 2, "-preset", "fast", "-crf", 18, "-pix_fmt", "yuv420p", "-g", args.fps, "-video_track_timescale", args.fps * 512, file])
            encoded = next(s for s in probe(file, args.ffprobe)["streams"] if s["codec_type"] == "video")
            if int(encoded.get("nb_frames", -1)) != n:
                raise ValueError(f"Unexpected frame count for {cut['id']}")
            return file
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            files = list(pool.map(encode, enumerate(cuts)))
        listing = folder / "concat.txt"
        listing.write_text("".join(f"file '{f.name}'\n" for f in files), encoding="utf8")
        picture = folder / "picture.mp4"
        ffmpeg(["-f", "concat", "-safe", 0, "-i", listing, "-c", "copy", "-movflags", "+faststart", picture])
        if args.audio:
            result = folder / "narrated.mp4"
            ffmpeg(["-i", picture, "-i", args.audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", target["duration"], "-movflags", "+faststart", result])
        else:
            result = picture
        result.replace(args.output)
    report = {"fps": args.fps, "frames": sum(c["endFrame"] - c["startFrame"] for c in cuts), "targetDuration": target["duration"], "audioRetimed": False, "cuts": cuts}
    args.output.with_suffix(".retime.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k != "cuts"}))


if __name__ == "__main__":
    main()
