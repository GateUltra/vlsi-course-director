"""Explicit online synthesis and offline audio-driven clocks/captions."""
from __future__ import annotations
import asyncio
import datetime
import importlib.metadata
import json
import re
import shutil
import subprocess
import tempfile
import textwrap
import wave
from pathlib import Path
from _studio_contract import canonical, digest, file_hash, fixture_clips, local, text_hash, write_json

SAMPLE_RATE = 48000


def execute(command):
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise ValueError(f"Command failed: {Path(str(command[0])).name}\n{result.stderr.decode('utf8',errors='replace')[-4000:]}")
    return result.stdout


async def synthesize(course, cache: Path):
    import edge_tts
    version = importlib.metadata.version("edge-tts")
    available = {voice["ShortName"] for voice in await edge_tts.list_voices()}
    missing = [v["voice"] for v in course["voices"] if v["voice"] not in available]
    if missing:
        raise ValueError(f"Requested TTS voices unavailable; no fallback: {missing}")
    cache.mkdir(parents=True, exist_ok=True)
    result = []
    for voice in course["voices"]:
        for cue in course["cues"]:
            text = cue["narration"][voice["language"]]
            settings = {"provider":"edge_tts", "clientVersion":version, "text":text, **{k:voice[k] for k in ("voice","rate","pitch")}}
            key = digest(canonical(settings))
            path, meta = cache / (key + ".mp3"), cache / (key + ".json")
            metadata = None
            if path.is_file() and meta.is_file():
                candidate = json.loads(meta.read_text(encoding="utf8"))
                if candidate.get("settings") == settings and candidate.get("sha256") == file_hash(path):
                    metadata = candidate
            if metadata is None:
                for attempt in range(3):
                    temporary = cache / (key + ".part.mp3")
                    try:
                        await edge_tts.Communicate(text,voice=voice["voice"],rate=voice["rate"],pitch=voice["pitch"]).save(str(temporary))
                        if not temporary.is_file() or temporary.stat().st_size < 512:
                            raise ValueError("Empty speech response")
                        temporary.replace(path)
                        metadata = {"settings":settings,"sha256":file_hash(path),"generatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"backendVersion":"not exposed by service"}
                        write_json(meta,metadata)
                        break
                    except Exception:
                        temporary.unlink(missing_ok=True)
                        if attempt == 2:
                            raise
                        await asyncio.sleep(1 + attempt)
            result.append({"voiceId":voice["id"],"cueId":cue["id"],"file":path,"sha256":metadata["sha256"],"textSha256":text_hash(text),**{k:voice[k] for k in ("voice","rate","pitch")},"provenance":{"provider":"edge_tts","clientVersion":version,"generatedAt":metadata["generatedAt"],"backendVersion":metadata["backendVersion"],"synthetic":True,"cacheKey":key}})
            print(f"Audio ready: {voice['id']}/{cue['id']}", flush=True)
    return result


def freeze_audio(root: Path, course, destination: Path):
    destination = destination.resolve()
    if destination.exists():
        raise ValueError("Audio fixture destination exists; choose a new directory")
    if not destination.is_relative_to(root) or destination == root:
        raise ValueError("Audio fixture directory must be inside the course pack")
    manifest_path = local(root, course.get("audioFixtures"), must_exist=False)
    if manifest_path.parent != destination:
        raise ValueError("--out must match the parent directory of course.audioFixtures")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".studio-audio-",dir=destination.parent) as temp:
        temporary = Path(temp)
        clips = asyncio.run(synthesize(course,temporary / "cache"))
        prepared = temporary / "prepared"; prepared.mkdir()
        records = []
        for clip in clips:
            name=f"{clip['voiceId']}-{clip['cueId']}.mp3"
            shutil.copy2(clip["file"], prepared/name)
            record={k:v for k,v in clip.items() if k!="file"}
            record["path"]=(destination.relative_to(root)/name).as_posix()
            records.append(record)
        write_json(prepared/manifest_path.name,{"schemaVersion":"1.0","note":"Synthetic fixture audio: fixed input for offline reconstruction; online service backend is not pinned.","clips":records})
        prepared.replace(destination)
    fixture_clips(root,course)
    return {"audioFixtures":str(manifest_path),"clips":len(records),"mode":"explicit-online-freeze"}


def wrap_caption(text: str, language: str):
    """Two-line captions. Numeric tokens are never divided, including 48.1/48,1."""
    width = 24 if language in ("zh","ja") else 28 if language == "ko" else 43
    if language in ("zh","ja"):
        tokens=re.findall(r"\d+(?:[.,]\d+)*|.",text,flags=re.S)
        lines=[];current=""
        for token in tokens:
            if token in "\r\n":token=" "
            if current and len(current)+len(token)>width:
                lines.append(current.strip());current=""
            current+=token
        if current.strip():lines.append(current.strip())
    else:
        lines=textwrap.wrap(" ".join(text.split()),width=width,break_long_words=False,break_on_hyphens=False)
    chunks=["\n".join(lines[i:i+2]) for i in range(0,len(lines),2)]
    if not chunks:
        raise ValueError("Caption text is empty")
    return chunks


def timestamp(value):
    total=round(value*1000)
    return f"{total//3600000:02}:{total//60000%60:02}:{total//1000%60:02}.{total%1000:03}"


def write_captions(site: Path, course, clock):
    if [c["id"] for c in course["cues"]] != [s["id"] for s in clock["segments"]]:
        raise ValueError("Caption source and clock must contain exactly the same ordered cue IDs")
    outputs={}
    for language in course["captionLanguages"]:
        blocks=[]
        for cue, segment in zip(course["cues"],clock["segments"]):
            chunks=wrap_caption(cue["captions"][language],language)
            span=segment["end"]-segment["start"]
            if span < .04*len(chunks):
                raise ValueError("Speech window is too short for its caption chunks")
            minimum=min(1.1,span/len(chunks));rest=span-minimum*len(chunks)
            weights=[max(1,len(chunk.replace("\n",""))) for chunk in chunks];cursor=segment["start"]
            for i,(chunk,weight) in enumerate(zip(chunks,weights)):
                end=segment["end"] if i==len(chunks)-1 else cursor+minimum+rest*weight/sum(weights)
                blocks.append(f"{cue['id']}-{i+1}\n{timestamp(cursor)} --> {timestamp(end)}\n{chunk}")
                cursor=end
        relative=f"media/captions/{clock['id']}-{language}.vtt"
        path=site/relative;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text("WEBVTT\n\n"+"\n\n".join(blocks)+"\n",encoding="utf8")
        outputs[language]=relative
    return outputs


def assemble(site: Path, root: Path, course, clips, identity, ffmpeg):
    by_pair={(c["voiceId"],c["cueId"]):c for c in clips}
    tracks=[]
    for voice in course["voices"]:
        directory=site/"production"/voice["id"];directory.mkdir(parents=True)
        raw=directory/"narration-raw.wav";segments=[]
        cursor=round(course.get("timing",{}).get("intro",.3)*SAMPLE_RATE)
        with wave.open(str(raw),"wb") as output:
            output.setparams((1,2,SAMPLE_RATE,0,"NONE","not compressed"));output.writeframes(b"\0\0"*cursor)
            for cue in course["cues"]:
                clip=by_pair[(voice["id"],cue["id"])]
                samples=execute([ffmpeg,"-v","error","-i",str(clip["file"]),"-f","s16le","-ac","1","-ar",str(SAMPLE_RATE),"-"])
                frames=len(samples)//2
                if not frames or len(samples)%2:raise ValueError("Invalid decoded audio")
                start=cursor/SAMPLE_RATE;output.writeframes(samples);cursor+=frames;end=cursor/SAMPLE_RATE
                hold=round(cue.get("holdAfter",0)*SAMPLE_RATE);output.writeframes(b"\0\0"*hold);cursor+=hold
                segments.append({"id":cue["id"],"start":start,"end":end,"sceneEnd":cursor/SAMPLE_RATE,"textSha256":clip["textSha256"],"audioSha256":clip["sha256"]})
            tail=round(course.get("timing",{}).get("tail",.3)*SAMPLE_RATE);output.writeframes(b"\0\0"*tail);cursor+=tail
        narration=directory/"narration.wav"
        execute([ffmpeg,"-v","error","-y","-i",str(raw),"-af","loudnorm=I=-17:TP=-2:LRA=7","-ar",str(SAMPLE_RATE),"-ac","1",str(narration)])
        mixed=directory/"mix.wav"
        if "bgm" in course:
            execute([ffmpeg,"-v","error","-y","-i",str(narration),"-stream_loop","-1","-i",str(local(root,course["bgm"])),"-filter_complex",f"[1:a]volume={course.get('bgmGain',.03)}[bed];[0:a][bed]amix=inputs=2:duration=first:normalize=0[a]","-map","[a]","-ar",str(SAMPLE_RATE),"-ac","1",str(mixed)])
        else:shutil.copy2(narration,mixed)
        clock={"id":voice["id"],"duration":cursor/SAMPLE_RATE,"segments":segments,"buildIdentity":identity,"measurement":"decoded mono PCM sample count at 48000 Hz","provisional":False}
        timing=f"media/timings/{voice['id']}.json";write_json(site/timing,clock)
        captions=write_captions(site,course,clock)
        video=f"media/lesson-{voice['id']}.mp4"
        sources=[{"src":video,"type":'video/mp4; codecs="avc1.640028, mp4a.40.2"'},{"src":f"media/lesson-{voice['id']}.webm","type":'video/webm; codecs="vp8, opus"'}]
        tracks.append({"id":voice["id"],"label":voice["label"],"language":voice["language"],"video":video,"sources":sources,"timing":timing,"captions":captions})
    return tracks
