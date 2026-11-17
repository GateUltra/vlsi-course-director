"""Transactional narrated course build and cross-artifact verification."""
from __future__ import annotations
import asyncio
import contextlib
import datetime
import importlib.metadata
import json
import math
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from _studio_contract import ENGINE_VERSION, SKILL, canonical, check_adapter, digest, engine_inventory, file_hash, fixture_clips, inventory, load, local, text_hash, validate_course, write_json
from _studio_audio import assemble, execute, synthesize
from serve_studio import StudioHandler
from validate_media import validate_site


def doctor(args, *, tts=False, browser=True):
    if sys.version_info < (3,10):raise ValueError("Python 3.10+ required")
    result={"python":platform.python_version(),"platform":platform.platform(),"engineVersion":ENGINE_VERSION}
    for name,command in (("node",[args.node,"--version"]),("ffmpeg",[args.ffmpeg,"-version"]),("ffprobe",[args.ffprobe,"-version"])):
        result[name]=execute(command).decode("utf8",errors="replace").splitlines()[0]
    if int(result["node"].lstrip("v").split(".")[0]) < 18:raise ValueError("Node 18+ required")
    encoders=execute([args.ffmpeg,"-hide_banner","-encoders"]).decode("utf8",errors="replace")
    encoder_names={parts[1] for line in encoders.splitlines() if len(parts:=line.split())>=2}
    if not {"libx264","aac","libvpx","libopus"}.issubset(encoder_names):
        raise ValueError("FFmpeg needs libx264, AAC, libvpx (VP8) and libopus encoders for both browser media formats")
    result["requiredEncoders"]=["libx264","aac","libvpx","libopus"]
    if tts:result["edge-tts"]=importlib.metadata.version("edge-tts")
    if browser:
        from playwright.sync_api import sync_playwright
        result["playwright"]=importlib.metadata.version("playwright")
        with sync_playwright() as pw:
            options={"headless":True}
            if args.browser:options["executable_path"]=args.browser
            with pw.chromium.launch(**options) as instance:
                result["chromium"]=instance.version
                page=instance.new_page();page.set_content("<p>Preflight</p>")
                if page.locator("p").inner_text()!="Preflight":raise ValueError("Browser preflight failed")
    return result


@contextlib.contextmanager
def server(site):
    class Quiet(StudioHandler):
        def log_message(self,*args):pass
    httpd=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(site)))
    thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    try:yield f"http://127.0.0.1:{httpd.server_port}/"
    finally:httpd.shutdown();httpd.server_close();thread.join()


def render_voice(site, url, track, args, identity):
    from playwright.sync_api import sync_playwright
    clock=load(site/track["timing"]);frames=math.ceil(clock["duration"]*args.fps)
    directory=site/"production"/track["id"];picture=directory/"picture.mp4"
    errors=[]; network=[]
    with sync_playwright() as pw:
        options={"headless":True,"args":["--disable-background-timer-throttling","--hide-scrollbars"]}
        if args.browser:options["executable_path"]=args.browser
        with pw.chromium.launch(**options) as browser:
            page=browser.new_page(viewport={"width":args.width,"height":args.height},device_scale_factor=1)
            def route_request(route):
                request_url=route.request.url
                if request_url.startswith(url) or request_url.startswith("data:"):route.continue_()
                else:network.append(request_url);route.abort()
            page.route("**/*",route_request)
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.on("response",lambda r:errors.append(f"HTTP {r.status}: {r.url}") if r.status>=400 else None)
            page.goto(url+"render.html?voice="+track["id"],wait_until="domcontentloaded")
            try:
                page.wait_for_function("window.ready === true && typeof window.renderAt === 'function'")
            except Exception as exc:
                raise ValueError(f"Renderer did not become ready; page errors: {errors}; blocked requests: {network}") from exc
            exposed=page.evaluate("({clock:window.clock,buildIdentity:window.buildIdentity})")
            if exposed.get("clock")!=clock or exposed.get("buildIdentity")!=identity:
                raise ValueError("Required page clock/build identity does not match production inputs")
            page.evaluate("document.fonts.ready")
            page.evaluate("Promise.all([...document.images].map(im=>im.decode()))")
            representative=clock["segments"][0]
            time=(representative["start"]+representative["sceneEnd"])/2
            a=page.evaluate("t=>window.renderAt(t)",time)
            page.evaluate("t=>window.renderAt(t)",clock["duration"])
            b=page.evaluate("t=>window.renderAt(t)",time)
            if canonical(a)!=canonical(b):raise ValueError("Browser random-access render state changed")
            screenshots=site/"review"/track["id"];screenshots.mkdir(parents=True)
            for cue in clock["segments"]:
                page.evaluate("t=>window.renderAt(t)",(cue["start"]+cue["sceneEnd"])/2)
                page.screenshot(path=str(screenshots/(cue["id"]+".png")))
            command=[args.ffmpeg,"-v","error","-y","-f","image2pipe","-vcodec","mjpeg","-framerate",str(args.fps),"-i","-","-an","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p","-g",str(args.fps),"-movflags","+faststart",str(picture)]
            with (directory/"encode.log").open("wb") as log:
                process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
                try:
                    for frame in range(frames):
                        page.evaluate("t=>window.renderAt(t)",frame/args.fps)
                        process.stdin.write(page.screenshot(type="jpeg",quality=95))
                        if frame%(args.fps*10)==0:print(f"Render {track['id']}: {frame}/{frames}",flush=True)
                    process.stdin.close()
                    if process.wait()!=0:raise ValueError("FFmpeg picture encoding failed")
                except BaseException:
                    process.kill();process.wait()
                    if process.stdin and not process.stdin.closed:process.stdin.close()
                    raise
            if errors or network:raise ValueError(f"Render errors / external asset requests: {errors}; {network}")
    execute([args.ffmpeg,"-v","error","-y","-i",str(picture),"-i",str(directory/"mix.wav"),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","160k","-movflags","+faststart",str(site/track["video"])])
    webm=track["sources"][1]["src"]
    execute([args.ffmpeg,"-v","error","-y","-i",str(picture),"-i",str(directory/"mix.wav"),"-map","0:v:0","-map","1:a:0","-c:v","libvpx","-deadline","good","-cpu-used","4","-b:v","1M","-pix_fmt","yuv420p","-g",str(args.fps),"-c:a","libopus","-b:a","128k",str(site/webm)])
    return {"id":track["id"],"frames":frames,"fps":args.fps,"dimensions":[args.width,args.height],"strictClockIdentity":True,"randomAccess":True,"externalRequests":network,"pageErrors":errors,"formats":[{"path":track["video"],"container":"mp4","videoCodec":"h264","audioCodec":"aac"},{"path":webm,"container":"webm","videoCodec":"vp8","audioCodec":"opus"}]}


def validate_webm(path, clock, render_config, args):
    """WebM often omits stream duration; count video frames and decoded PCM samples.

    Container duration alone cannot detect a truncated audio stream. Opus pre-skip
    and discard padding are respected by FFmpeg's decoder before measuring audio.
    """
    data=json.loads(execute([args.ffprobe,"-v","error","-count_frames","-show_entries","format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,nb_read_frames,start_time","-of","json",str(path)]))
    streams=data.get("streams",[])
    video=next((s for s in streams if s.get("codec_type")=="video"),None)
    audio=next((s for s in streams if s.get("codec_type")=="audio"),None)
    if not video or not audio or video.get("codec_name")!="vp8" or audio.get("codec_name")!="opus":
        raise ValueError("WebM alternative requires both VP8 video and Opus audio")
    numerator,denominator=map(float,video["avg_frame_rate"].split("/"))
    fps=numerator/denominator if denominator else 0
    if not math.isfinite(fps) or abs(fps-render_config["fps"])>1e-7:
        raise ValueError("WebM frame rate differs from render contract")
    if [video.get("width"),video.get("height")] != [render_config["width"],render_config["height"]]:
        raise ValueError("WebM dimensions differ from render contract")
    frames=int(video.get("nb_read_frames",0))
    expected_frames=math.ceil(clock["duration"]*render_config["fps"])
    if frames!=expected_frames or abs(frames/fps-clock["duration"])>1/fps+.01:
        raise ValueError("WebM video frame count/duration differs from measured clock")
    for stream in (video,audio):
        offset=float(stream.get("start_time",0))
        if not math.isfinite(offset) or abs(offset)>.05:
            raise ValueError("WebM stream has excessive start offset")
    pcm=execute([args.ffmpeg,"-v","error","-xerror","-i",str(path),"-map","0:a:0","-f","s16le","-ar","48000","-ac","1","-"])
    if not pcm or len(pcm)%2:raise ValueError("WebM audio decoded to invalid PCM")
    audio_duration=len(pcm)/2/48000
    if abs(audio_duration-clock["duration"])>.05:
        raise ValueError("WebM decoded audio duration differs from measured clock")
    container_duration=float(data["format"]["duration"])
    if not math.isfinite(container_duration) or abs(container_duration-clock["duration"])>1/fps+.05:
        raise ValueError("WebM container duration differs from measured clock")
    execute([args.ffmpeg,"-v","error","-xerror","-i",str(path),"-map","0:v:0","-map","0:a:0","-f","null","-"])
    return {"container":"webm","videoCodec":"vp8","audioCodec":"opus","frames":frames,"fps":fps,"dimensions":[video["width"],video["height"]],"videoDuration":frames/fps,"decodedAudioDuration":audio_duration,"containerDuration":container_duration,"fullDecode":True,"audioDurationMethod":"decoded mono 48000 Hz PCM sample count, after Opus pre-skip/discard padding"}


def caption_coverage(path, course, language):
    text=path.read_text(encoding="utf8")
    blocks=re.split(r"\n\s*\n",text.strip())[1:]
    grouped={cue["id"]:[] for cue in course["cues"]};seen=[]
    for block in blocks:
        lines=block.splitlines()
        if len(lines)<3:raise ValueError("Malformed generated caption block")
        match=re.fullmatch(r"(.+)-(\d+)",lines[0])
        if not match or match.group(1) not in grouped:raise ValueError("Caption references unknown semantic cue")
        cue_id,index=match.group(1),int(match.group(2))
        if index!=len(grouped[cue_id])+1:raise ValueError("Missing or duplicate caption chunk")
        grouped[cue_id].append("\n".join(lines[2:]))
        if not seen or seen[-1]!=cue_id:seen.append(cue_id)
    if seen!=list(grouped):raise ValueError("Caption cue coverage/order differs from complete course")
    for cue in course["cues"]:
        expected=re.sub(r"\s+","",cue["captions"][language]);actual=re.sub(r"\s+","","".join(grouped[cue["id"]]))
        if expected!=actual:raise ValueError(f"Caption text is stale/incomplete: {cue['id']}/{language}")


def verify(site: Path, args, *, course_path=None):
    site=site.resolve(strict=True);record=load(site/"build-record.json")
    if record.get("engineVersion")!=ENGINE_VERSION:raise ValueError("Build requires its recorded engine release")
    intended_identity=digest(canonical({"engineVersion":ENGINE_VERSION,"engine":record["engineInventory"],"source":record["sourceInventory"],"audio":record["audioInputs"],"render":record["renderConfig"]}))
    if record.get("buildIdentity")!=intended_identity:raise ValueError("Build dependency identity is inconsistent with its inputs")
    course=validate_course(site/"pack")
    if inventory(site/"pack")!=record["sourceInventory"]:raise ValueError("Published pack differs from recorded course inputs")
    if course_path is not None and inventory(Path(course_path).resolve())!=record["sourceInventory"]:
        raise ValueError("Source course changed since build; regenerate dependent artifacts")
    if engine_inventory()!=record["engineInventory"]:raise ValueError("Production engine differs from this build's frozen engine")
    current=inventory(site);current.pop("build-record.json",None)
    if current!=record["files"]:raise ValueError("Build assets missing, added, or changed since verification")
    manifest=load(site/"media/manifest.json")
    if manifest.get("buildIdentity")!=record["buildIdentity"]:raise ValueError("Manifest build identity mismatch")
    expected=[c["id"] for c in course["cues"]]
    voices={v["id"]:v for v in course["voices"]}
    if [t["id"] for t in manifest["tracks"]]!=list(voices):raise ValueError("Voice track coverage/order mismatch")
    if manifest.get("captionLanguages")!=course["captionLanguages"] or manifest.get("defaultVoice")!=course["defaultVoice"]:
        raise ValueError("Manifest choices differ from course intent")
    clips={(c["voiceId"],c["cueId"]):c for c in record["audioInputs"]}
    alternatives=[]
    for track in manifest["tracks"]:
        clock=load(local(site,track["timing"]));voice=voices[track["id"]]
        if clock.get("buildIdentity")!=record["buildIdentity"] or [s["id"] for s in clock["segments"]]!=expected:
            raise ValueError("Clock identity or complete semantic cue sequence differs")
        for cue,segment in zip(course["cues"],clock["segments"]):
            clip=clips[(track["id"],cue["id"])]
            if segment.get("textSha256")!=text_hash(cue["narration"][voice["language"]]) or segment.get("audioSha256")!=clip["sha256"]:
                raise ValueError("Stale narration or audio in measured clock")
        if set(track["captions"])!=set(course["captionLanguages"]):raise ValueError("Caption language coverage mismatch")
        for language,path in track["captions"].items():caption_coverage(local(site,path),course,language)
        sources=track.get("sources")
        expected_sources=[{"src":track["video"],"type":'video/mp4; codecs="avc1.640028, mp4a.40.2"'},{"src":f"media/lesson-{track['id']}.webm","type":'video/webm; codecs="vp8, opus"'}]
        if sources!=expected_sources:raise ValueError("Track requires declared MP4 and WebM alternatives in the same semantic voice")
        alternative=validate_webm(local(site,sources[1]["src"]),clock,record["renderConfig"],args)
        alternatives.append({"id":track["id"],"path":sources[1]["src"],**alternative})
    media=validate_site(site,site/"media/manifest.json",ffprobe=args.ffprobe,ffmpeg=args.ffmpeg,decode=True)
    return {"passed":True,"engineVersion":ENGINE_VERSION,"buildIdentity":record["buildIdentity"],"sourceAndAssetHashes":True,"exactCueCaptionVoiceCoverage":True,"tracks":media["tracks"],"webmAlternatives":alternatives,"scope":"Technical consistency and complete decoding of both media formats; not a speech, translation or instructional quality review"}


def build(root: Path, destination: Path, args):
    root=root.resolve(strict=True);destination=destination.resolve()
    if destination.exists():raise ValueError("Build destination already exists; choose a new directory")
    if destination.is_relative_to(root):raise ValueError("Build output must be outside the course pack")
    if args.fps<=0 or args.width<=0 or args.height<=0 or args.width%2 or args.height%2:raise ValueError("Render needs positive fps and positive even dimensions")
    course=validate_course(root)
    check_adapter(root,args.node)
    clips=fixture_clips(root,course) if args.audio_mode=="fixture" else None
    environment=doctor(args,tts=args.audio_mode=="tts")
    sources=inventory(root);engine=engine_inventory()
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".studio-build-",dir=destination.parent) as temp:
        temporary=Path(temp);site=temporary/"site";site.mkdir()
        shutil.copytree(SKILL/"assets/runtime",site,dirs_exist_ok=True)
        shutil.copytree(root,site/"pack",ignore=shutil.ignore_patterns("__pycache__",".git","node_modules",".venv"))
        shutil.copy2(SKILL/"scripts/serve_site.py",site/"serve_site.py")
        shutil.copy2(SKILL/"scripts/serve_studio.py",site/"serve_studio.py")
        (site/".nojekyll").write_text("",encoding="utf8")
        if clips is None:
            cache=Path(args.cache).resolve() if args.cache else destination.parent/".studio-tts-cache"
            if cache.is_relative_to(root) or cache.is_relative_to(destination):raise ValueError("TTS cache must be outside course and output")
            clips=asyncio.run(synthesize(course,cache))
        audio_inputs=[{k:v for k,v in clip.items() if k not in ("file","path")} for clip in clips]
        identity=digest(canonical({"engineVersion":ENGINE_VERSION,"engine":engine,"source":sources,"audio":audio_inputs,"render":{"fps":args.fps,"width":args.width,"height":args.height}}))
        tracks=assemble(site,root,course,clips,identity,args.ffmpeg)
        manifest={"contractVersion":"1.0","engineVersion":ENGINE_VERSION,"buildIdentity":identity,"defaultVoice":course["defaultVoice"],"captionLanguages":course["captionLanguages"],"tracks":tracks}
        write_json(site/"media/manifest.json",manifest)
        renders=[]
        with server(site) as url:
            for track in tracks:renders.append(render_voice(site,url,track,args,identity))
        if inventory(root)!=sources or engine_inventory()!=engine:raise ValueError("Inputs changed during build; refusing mixed-version output")
        record={"engineVersion":ENGINE_VERSION,"contractVersion":"1.0","buildIdentity":identity,"createdAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"audioMode":args.audio_mode,"renderConfig":{"fps":args.fps,"width":args.width,"height":args.height},"sourceInventory":sources,"engineInventory":engine,"audioInputs":audio_inputs,"environment":environment,"renders":renders,"files":inventory(site)}
        write_json(site/"build-record.json",record)
        result=verify(site,args,course_path=root)
        record["mediaVerification"]={"mp4":result["tracks"],"webm":result["webmAlternatives"]}
        write_json(site/"build-record.json",record)
        # Keep verification outside hashed output to avoid a self-referential manifest.
        print(json.dumps({"verified":result["passed"],"voices":len(tracks),"buildIdentity":identity}),flush=True)
        site.replace(destination)
    return {"site":str(destination),"buildIdentity":identity,"audioMode":args.audio_mode,"voices":len(tracks),"technicalVerification":True,"browserUXReview":"run check_studio_browser.py separately"}
