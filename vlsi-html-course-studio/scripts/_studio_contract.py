"""Course-pack 1.0 admission, provenance and portable build identity."""
from __future__ import annotations
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

ENGINE_VERSION = "2.0.0"
CONTRACT_VERSION = "1.0"
SKILL = Path(__file__).resolve().parents[1]
ID = re.compile(r"^[a-zA-Z0-9_-]+$")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def text_hash(value: str) -> str:
    return digest(value.encode("utf8"))


def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf8")


def load(path: Path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def bad(value):
        raise ValueError(f"Nonfinite JSON number: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=pairs, parse_constant=bad)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf8")


def local(root: Path, value: str, *, must_exist=True) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or "?" in value or "#" in value:
        raise ValueError(f"Expected portable relative path: {value!r}")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Path must remain inside pack: {value}")
    result = (root / candidate).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes pack: {value}")
    if must_exist and (not result.is_file() or not result.stat().st_size):
        raise ValueError(f"Missing or empty file: {value}")
    return result


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def number(value, label, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def unique(items, label, key="id"):
    if not isinstance(items, list) or not items:
        raise ValueError(f"{label} must be a nonempty list")
    ids = [item.get(key) if isinstance(item, dict) else item for item in items]
    if any(not isinstance(i, str) or not ID.fullmatch(i) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError(f"Invalid or duplicate {label} IDs")
    return ids


def validate_course(root: Path):
    root = Path(root).resolve(strict=True)
    course = load(root / "lesson.json")
    if not isinstance(course, dict) or course.get("contractVersion") != CONTRACT_VERSION:
        raise ValueError("Unsupported course contractVersion; expected 1.0")
    unique([course], "course")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", str(course.get("version", ""))):
        raise ValueError("Course version must be a semantic version")
    for field in ("title", "description"):
        nonempty(course.get(field), field)
    local(root, course.get("adapter"))
    local(root, "check.mjs")
    voice_ids = unique(course.get("voices"), "voices")
    cue_ids = unique(course.get("cues"), "cues")
    languages = unique(course.get("captionLanguages"), "captionLanguages")
    if course.get("defaultVoice") not in voice_ids:
        raise ValueError("defaultVoice is absent from voices")
    for voice in course["voices"]:
        for field in ("language", "label", "voice", "rate", "pitch"):
            nonempty(voice.get(field), f"{voice['id']}.{field}")
        if voice.get("provider") != "edge_tts":
            raise ValueError("Current TTS provider adapter supports edge_tts only; fixtures remain offline")
        if not re.fullmatch(r"[+-]\d+%", voice["rate"]) or not re.fullmatch(r"[+-]\d+Hz", voice["pitch"]):
            raise ValueError("Voice rate/pitch must use signed percent / Hz")
    for cue in course["cues"]:
        for field in ("chapter", "title", "intent", "sceneId"):
            nonempty(cue.get(field), f"{cue['id']}.{field}")
        if not ID.fullmatch(cue["sceneId"]) or not ID.fullmatch(cue["chapter"]):
            raise ValueError("Scene/chapter IDs must be portable identifiers")
        number(cue.get("holdAfter", 0), "holdAfter", maximum=30)
        for voice in course["voices"]:
            nonempty(cue.get("narration", {}).get(voice["language"]), f"{cue['id']} narration {voice['language']}")
        for language in languages:
            nonempty(cue.get("captions", {}).get(language), f"{cue['id']} caption {language}")
    unique(course.get("exercises"), "exercises")
    for exercise in course["exercises"]:
        if exercise.get("cueId") not in cue_ids:
            raise ValueError(f"Exercise {exercise['id']} references unknown cue")
        nonempty(exercise.get("prompt"), "exercise prompt")
        if not isinstance(exercise.get("config"), dict):
            raise ValueError("Exercise config must be an object")
    timing = course.get("timing", {})
    if not isinstance(timing, dict) or "intro" in course or "tail" in course:
        raise ValueError("Use optional timing:{intro,tail}; top-level timing fields are unsupported")
    for field in ("intro", "tail"):
        number(timing.get(field, .3), field, maximum=30)
    if "bgm" in course:
        local(root, course["bgm"])
        number(course.get("bgmGain", .03), "bgmGain", maximum=.3)
    if "audioFixtures" in course:
        local(root, course["audioFixtures"], must_exist=False)
    canonical(course)  # reject nonfinite values even inside opaque domain fields
    return course


def inventory(root: Path):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not portable build inputs: {path}")
        if any(p in ("__pycache__", ".git", "node_modules", ".venv") for p in path.relative_to(root).parts):
            continue
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {"sha256": file_hash(path), "bytes": path.stat().st_size}
    return result


def engine_inventory():
    result = {"runtime/" + k: v for k, v in inventory(SKILL / "assets" / "runtime").items()}
    names = ["studio.py", "_studio_contract.py", "_studio_audio.py", "_studio_build.py", "check_adapter.mjs", "serve_site.py", "serve_studio.py", "render_html.py", "validate_media.py"]
    for name in names:
        path = SKILL / "scripts" / name
        result["scripts/" + name] = {"sha256": file_hash(path), "bytes": path.stat().st_size}
    return result


def check_adapter(root: Path, node="node"):
    for command in ([node, str(SKILL / "scripts/check_adapter.mjs"), str(root)], [node, str(root / "check.mjs")]):
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf8", errors="replace")
        if result.returncode:
            raise ValueError(f"Course check failed ({Path(command[-1]).name}):\n{result.stdout}\n{result.stderr}")
    return {"adapterContract": True, "independentDomainTests": True}


def fixture_clips(root: Path, course):
    manifest = load(local(root, course.get("audioFixtures")))
    if manifest.get("schemaVersion") != "1.0" or not isinstance(manifest.get("clips"), list):
        raise ValueError("Unsupported audio fixture manifest")
    expected = {(v["id"], c["id"]): (v, c) for v in course["voices"] for c in course["cues"]}
    found, clips = set(), []
    for clip in manifest["clips"]:
        pair = (clip.get("voiceId"), clip.get("cueId"))
        if pair not in expected or pair in found:
            raise ValueError(f"Extra or duplicate audio fixture: {pair}")
        found.add(pair)
        voice, cue = expected[pair]
        for field in ("voice", "rate", "pitch"):
            if clip.get(field) != voice[field]:
                raise ValueError(f"Stale audio fixture setting {pair}: {field}")
        if clip.get("textSha256") != text_hash(cue["narration"][voice["language"]]):
            raise ValueError(f"Stale audio text: {pair}")
        path = local(root, clip.get("path"))
        if clip.get("sha256") != file_hash(path):
            raise ValueError(f"Audio fixture bytes changed: {pair}")
        if not isinstance(clip.get("provenance"), dict) or not (clip["provenance"].get("provider") or clip["provenance"].get("source")):
            raise ValueError(f"Audio fixture needs provenance: {pair}")
        clips.append({**clip, "file": path})
    if found != set(expected):
        raise ValueError(f"Missing audio fixtures: {sorted(set(expected) - found)}")
    return clips
