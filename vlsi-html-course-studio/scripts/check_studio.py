"""Real contract regression checks using an isolated copy of a course pack.

No online service is called. --site additionally exercises stale-build rejection
against a completed build. Temporary artifacts are removed automatically.
"""
from __future__ import annotations
import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from _studio_contract import check_adapter, fixture_clips, inventory, load, validate_course, write_json
from _studio_audio import execute, freeze_audio, wrap_caption, write_captions
from _studio_build import build, caption_coverage, validate_webm, verify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course",type=Path,required=True)
    parser.add_argument("--site",type=Path)
    parser.add_argument("--node",default="node")
    parser.add_argument("--ffmpeg",default="ffmpeg")
    parser.add_argument("--ffprobe",default="ffprobe")
    args=parser.parse_args();source=args.course.resolve(strict=True)
    course=validate_course(source);check_adapter(source,args.node);fixture_clips(source,course)
    passed=[]
    def rejected(name,operation,contains=None):
        try:operation()
        except Exception as error:
            if contains and contains not in str(error):raise AssertionError(f"{name}: wrong failure: {error}") from error
            passed.append(name);return
        raise AssertionError(f"{name}: malformed input was accepted")
    with tempfile.TemporaryDirectory(prefix="studio-regression-") as temporary:
        work=Path(temporary);pack=work/"pack";shutil.copytree(source,pack)
        def bad_course(name,change):
            changed=copy.deepcopy(course);change(changed);write_json(pack/"lesson.json",changed)
            rejected(name,lambda:validate_course(pack))
            write_json(pack/"lesson.json",course)
        bad_course("duplicate cue IDs",lambda c:c["cues"].append(copy.deepcopy(c["cues"][0])))
        bad_course("unknown contract version",lambda c:c.update(contractVersion="999"))
        bad_course("missing translated caption",lambda c:c["cues"][0]["captions"].pop(c["captionLanguages"][0]))
        bad_course("exercise references missing cue",lambda c:c["exercises"][0].update(cueId="not_present"))
        bad_course("negative explicit hold",lambda c:c["cues"][0].update(holdAfter=-1))
        bad_course("adapter path traversal",lambda c:c.update(adapter="../outside.mjs"))
        changed=copy.deepcopy(course);changed["cues"][0]["sceneId"]="unimplemented_scene";write_json(pack/"lesson.json",changed)
        rejected("unknown scene implementation",lambda:check_adapter(pack,args.node),"Unimplemented")
        write_json(pack/"lesson.json",course)
        fixture_path=pack/course["audioFixtures"];fixtures=load(fixture_path)
        for name,mutate in [
            ("missing audio clip",lambda m:m["clips"].pop()),
            ("duplicate audio pair",lambda m:m["clips"].append(copy.deepcopy(m["clips"][0]))),
            ("stale voice setting",lambda m:m["clips"][0].update(rate="+9%")),
            ("changed audio bytes",lambda m:m["clips"][0].update(sha256="0"*64)),
            ("stale narration hash",lambda m:m["clips"][0].update(textSha256="0"*64)),
        ]:
            malformed=copy.deepcopy(fixtures);mutate(malformed);write_json(fixture_path,malformed)
            rejected(name,lambda:fixture_clips(pack,course))
        write_json(fixture_path,fixtures)
        changed=copy.deepcopy(course);new=copy.deepcopy(changed["cues"][-1]);new["id"]="appended_cue";changed["cues"].append(new)
        write_json(pack/"lesson.json",changed)
        rejected("appended narration requires matching audio",lambda:fixture_clips(pack,changed),"Missing audio")
        clock={"id":course["defaultVoice"],"duration":len(course["cues"])*3,"segments":[{"id":c["id"],"start":i*3,"end":i*3+2,"sceneEnd":(i+1)*3} for i,c in enumerate(course["cues"])]}
        rejected("appended cue cannot be zip-truncated",lambda:write_captions(work,changed,clock),"exactly the same")
        out=work/"must-not-exist"
        build_args=SimpleNamespace(audio_mode="fixture",fps=12,width=640,height=360,node=args.node,ffmpeg=args.ffmpeg,ffprobe=args.ffprobe,browser=None,cache=None)
        rejected("incomplete build fails before final directory",lambda:build(pack,out,build_args),"Missing audio")
        if out.exists():raise AssertionError("Failed build left a final directory")
        write_json(pack/"lesson.json",course)
        write_captions(work,course,clock)
        for language in course["captionLanguages"]:
            caption_coverage(work/f"media/captions/{clock['id']}-{language}.vtt",course,language)
        passed.append("complete caption coverage and text round-trip")
        for language in ["en","zh","ja","ko"]:
            text=("Values 48.1 and 48,5 stay together. " if language=="en" else "宽度为48.1，高度为48,5。")*8
            chunks=wrap_caption(text,language)
            for token in ("48.1","48,5"):
                if sum(c.count(token) for c in chunks)!=text.count(token):raise AssertionError("Numeric token split")
        passed.append("decimal-safe multilingual wrapping")
        # A backend failure may leave cache diagnostics but never a final fixture dir.
        new_audio=pack/"new-audio";new_course=copy.deepcopy(course);new_course["audioFixtures"]="new-audio/fixtures.json"
        def fail(coroutine):
            coroutine.close()
            raise RuntimeError("injected offline provider failure")
        # Avoid opening even an asyncio Windows self-pipe for this offline fault injection.
        with patch("_studio_audio.asyncio.run",fail):
            rejected("failed synthesis preserves absent final fixtures",lambda:freeze_audio(pack,new_course,new_audio),"injected offline")
        if new_audio.exists():raise AssertionError("Failed synthesis left final fixture directory")
        # Real codec tests: the WebM container may outlast a truncated Opus stream.
        # Counting decoded samples, not container duration, must expose that case.
        def tiny_webm(name, video_seconds, audio_seconds):
            path=work/name
            execute([args.ffmpeg,"-v","error","-y","-f","lavfi","-i",f"color=c=0xf5efe0:s=320x180:r=10:d={video_seconds}","-f","lavfi","-i",f"sine=frequency=440:sample_rate=48000:duration={audio_seconds}","-c:v","libvpx","-deadline","good","-cpu-used","4","-b:v","1M","-c:a","libopus","-b:a","128k",str(path)])
            return path
        tiny_clock={"duration":1.2};tiny_config={"fps":10,"width":320,"height":180}
        webm=validate_webm(tiny_webm("valid.webm",1.2,1.2),tiny_clock,tiny_config,args)
        if webm["frames"]!=12 or abs(webm["decodedAudioDuration"]-1.2)>.001:raise AssertionError("Incorrect WebM measurement")
        passed.append("actual VP8/Opus frame and decoded-sample measurement")
        rejected("WebM truncated audio rejected independently",lambda:validate_webm(tiny_webm("short-audio.webm",1.2,.2),tiny_clock,tiny_config,args),"decoded audio duration")
        rejected("WebM truncated video rejected independently",lambda:validate_webm(tiny_webm("short-video.webm",.6,1.2),tiny_clock,tiny_config,args),"frame count/duration")
        if args.site:
            verify(args.site,args,course_path=source);passed.append("completed build cross-artifact verification")
            changed=copy.deepcopy(course);changed["cues"][0]["narration"][course["voices"][0]["language"]]+=" A changed sentence."
            write_json(pack/"lesson.json",changed)
            rejected("changed source invalidates build",lambda:verify(args.site,args,course_path=pack),"Source course changed")
            site_copy=work/"site";shutil.copytree(args.site,site_copy)
            manifest=load(site_copy/"media/manifest.json");caption=site_copy/next(iter(manifest["tracks"][0]["captions"].values()))
            caption.write_text(caption.read_text(encoding="utf8").replace("\n\n","\n\n",1)+"\n",encoding="utf8")
            rejected("changed artifact invalidates build",lambda:verify(site_copy,args),"assets missing, added, or changed")
            # Updating an inventory cannot conceal semantic caption drift.
            lines=caption.read_text(encoding="utf8").splitlines();lines[4]="A semantically unrelated statement."
            caption.write_text("\n".join(lines)+"\n",encoding="utf8")
            record=load(site_copy/"build-record.json");files=inventory(site_copy);files.pop("build-record.json");record["files"]=files;write_json(site_copy/"build-record.json",record)
            rejected("format-valid stale caption rejected semantically",lambda:verify(site_copy,args),"Caption text is stale/incomplete")
    print(json.dumps({"passed":True,"checks":passed,"count":len(passed),"onlineCalls":0},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
