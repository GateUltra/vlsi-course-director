"""Build narrated HTML/SVG courses from replaceable, versioned course packs."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import sys
from pathlib import Path
from _studio_contract import check_adapter, fixture_clips, validate_course
from _studio_audio import freeze_audio
from _studio_build import build, doctor, verify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    def tools(command):
        command.add_argument("--node",default="node")
        command.add_argument("--ffmpeg",default="ffmpeg")
        command.add_argument("--ffprobe",default="ffprobe")
        command.add_argument("--browser",help="Installed Chromium/Chrome path; otherwise Playwright Chromium")
    preflight=commands.add_parser("doctor",help="Check tools, codecs and real browser launch; no online calls")
    tools(preflight);preflight.add_argument("--tts",action="store_true",help="Also require the edge-tts package, without connecting")
    check=commands.add_parser("check",help="Check course, adapter and independent domain cases")
    check.add_argument("--course",type=Path,required=True);check.add_argument("--node",default="node")
    check.add_argument("--audio-mode",choices=["fixture"],help="Additionally require complete verified offline speech fixtures")
    freeze=commands.add_parser("freeze-audio",help="Explicit ONLINE edge-tts synthesis into a new immutable fixture directory")
    freeze.add_argument("--course",type=Path,required=True);freeze.add_argument("--out",type=Path,required=True);tools(freeze)
    produce=commands.add_parser("build",help="Atomic complete narrated static-site build; no existing destination")
    produce.add_argument("--course",type=Path,required=True);produce.add_argument("--out",type=Path,required=True)
    produce.add_argument("--audio-mode",choices=["fixture","tts"],required=True)
    produce.add_argument("--cache",help="Online TTS cache, outside input/output; default sibling .studio-tts-cache")
    produce.add_argument("--fps",type=int,default=30);produce.add_argument("--width",type=int,default=1920);produce.add_argument("--height",type=int,default=1080);tools(produce)
    validate=commands.add_parser("verify",help="Verify input dependencies, complete semantic coverage and media decoding")
    validate.add_argument("--site",type=Path,required=True);validate.add_argument("--course",type=Path,help="Optional current pack; detects source changes since build");tools(validate)
    args=parser.parse_args()
    try:
        if args.command=="doctor":result=doctor(args,tts=args.tts)
        elif args.command=="check":
            root=args.course.resolve(strict=True);course=validate_course(root)
            result=check_adapter(root,args.node)
            if args.audio_mode:result["verifiedAudioClips"]=len(fixture_clips(root,course))
            result.update({"passed":True,"course":course["id"],"version":course["version"]})
        elif args.command=="freeze-audio":
            root=args.course.resolve(strict=True);course=validate_course(root)
            check_adapter(root,args.node);doctor(args,tts=True,browser=False)
            result=freeze_audio(root,course,args.out)
        elif args.command=="build":result=build(args.course,args.out,args)
        elif args.command=="verify":result=verify(args.site,args,course_path=args.course)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (Exception,) as exc:
        print(f"STUDIO FAILED [{type(exc).__name__}]: {exc}",file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":raise SystemExit(main())
