"""Exercise a built v2 course in a real Chromium browser, without online assets.

Reports go outside the hashed site. Technical audio evidence is not a listening
or native-language review. Independent scientific expectations live in each pack.
"""
from __future__ import annotations
import argparse
import contextlib
import json
import threading
import time
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from serve_studio import StudioHandler


@contextlib.contextmanager
def serve(site):
    class Quiet(StudioHandler):
        def log_message(self, *_):
            pass
        def copyfile(self, source, output):
            # Seeking/replacing a media source intentionally cancels its HTTP body.
            try:
                super().copyfile(source, output)
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(site)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def seek(page, second):
    page.evaluate("t=>{const v=document.querySelector('#video');v.pause();v.currentTime=t}", second)
    page.wait_for_function("t=>{const v=document.querySelector('#video');return !v.seeking&&Math.abs(v.currentTime-t)<.06}", arg=second)


def check(site, report_path, browser_path=None):
    from playwright.sync_api import sync_playwright
    if report_path.resolve().is_relative_to(site.resolve()):
        raise ValueError("Browser report must be outside the integrity-checked site")
    shots = report_path.parent / (report_path.stem + "-screens")
    shots.mkdir(parents=True, exist_ok=True)
    report = {"passed": False, "scope": "Actual browser functionality, decoded audio signal and sampled layout. No subjective listening or native-language certification.", "voices": [], "captions": [], "chapters": [], "transfers": [], "exercises": [], "screenshots": []}
    errors, failed, canceled, external, http_errors = [], [], [], [], []
    started = time.monotonic()
    try:
        with serve(site) as url, sync_playwright() as pw:
            course_info = json.loads((site / "pack" / "lesson.json").read_text(encoding="utf8"))
            mime = {}
            for relative in ("core.mjs", "pack/" + course_info["adapter"]):
                with urllib.request.urlopen(url + relative) as response:
                    mime[relative] = response.headers.get_content_type()
                    require(mime[relative] in ("application/javascript", "text/javascript"), f"Module MIME type is invalid: {relative}: {mime[relative]}")
            report["moduleMimeTypes"] = mime
            launch = {"headless": True, "args": ["--autoplay-policy=no-user-gesture-required"]}
            if browser_path:
                launch["executable_path"] = browser_path
            with pw.chromium.launch(**launch) as browser:
                report["browser"] = browser.version
                report["browserLaunchMode"] = "explicit-executable" if browser_path else "playwright-default-headless"
                context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
                def route_request(route):
                    request_url = route.request.url
                    if request_url.startswith(url) or request_url.startswith("data:"):
                        route.continue_()
                    else:
                        external.append(request_url)
                        route.abort()
                context.route("**/*", route_request)
                page = context.new_page()
                page.set_default_timeout(20000)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("response", lambda response: http_errors.append({"status": response.status, "url": response.url.replace(url, "./")}) if response.status >= 400 else None)
                def failure(request):
                    item = {"url": request.url.replace(url, "./"), "failure": request.failure}
                    (canceled if "ERR_ABORTED" in (request.failure or "") else failed).append(item)
                page.on("requestfailed", failure)
                page.goto(url, wait_until="domcontentloaded")
                local_manifest = json.loads((site / "media" / "manifest.json").read_text(encoding="utf8"))
                source_types = sorted({source["type"] for track in local_manifest["tracks"] for source in track.get("sources", [{"src": track["video"], "type": 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"'}])})
                report["mediaSupport"] = page.evaluate("types=>{const v=document.querySelector('#video');return Object.fromEntries(types.map(type=>[type,v.canPlayType(type)]))}", source_types)
                selected_sources = {}
                for track in local_manifest["tracks"]:
                    sources = track.get("sources", [{"src": track["video"], "type": 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"'}])
                    supported = [source for source in sources if report["mediaSupport"].get(source["type"])]
                    require(supported, f"Browser has no supported source for {track['id']}; declared candidates: {sources}")
                    selected_sources[track["id"]] = supported[0]
                page.wait_for_function("window.ready===true||!document.querySelector('#error').hidden")
                require(page.evaluate("window.ready===true"), "Player startup failed: " + page.locator("#error").inner_text())
                course = page.evaluate("window.studio.course")
                manifest = page.evaluate("window.studio.manifest")
                report.update({"course": course["id"], "courseVersion": course["version"], "buildIdentity": manifest["buildIdentity"]})
                voices = [track["id"] for track in manifest["tracks"]]
                languages = manifest["captionLanguages"]
                screenshot = lambda name: (page.screenshot(path=str(shots / name), full_page=True), report["screenshots"].append(name))
                for voice in voices:
                    page.locator("#voice").select_option(voice)
                    page.wait_for_function("voice=>!studio.loading&&studio.voice===voice", arg=voice)
                    clock = page.evaluate("studio.clock")
                    require(page.evaluate("document.querySelector('#video').videoWidth>0"), "No decoded video dimensions")
                    first = clock["segments"][0]
                    seek(page, first["start"] + min(.6, (first["end"] - first["start"]) / 4))
                    audio = page.evaluate("""async()=>{
                      const v=document.querySelector('#video');v.muted=false;v.volume=1;
                      if(!window.__qaAudio){const c=new AudioContext();const source=c.createMediaElementSource(v);const a=c.createAnalyser();a.fftSize=1024;source.connect(a);a.connect(c.destination);window.__qaAudio={c,a}}
                      const {c,a}=window.__qaAudio;await c.resume();const begin=v.currentTime;await v.play();
                      const values=new Float32Array(a.fftSize),rms=[];
                      for(let i=0;i<30;i++){await new Promise(r=>setTimeout(r,40));a.getFloatTimeDomainData(values);rms.push(Math.sqrt(values.reduce((s,x)=>s+x*x,0)/values.length))}
                      v.pause();return {start:begin,end:v.currentTime,muted:v.muted,volume:v.volume,audioDecodedBytes:v.webkitAudioDecodedByteCount??null,width:v.videoWidth,height:v.videoHeight,nonzeroSamples:rms.filter(x=>x>1e-5).length,peakRms:Math.max(...rms),currentSrc:v.currentSrc}
                    }""")
                    audio["currentSrc"] = audio["currentSrc"].replace(url, "./")
                    audio["selectedType"] = selected_sources[voice]["type"]
                    require(audio["currentSrc"] == "./" + selected_sources[voice]["src"], f"Player selected unexpected source for {voice}: {audio['currentSrc']}")
                    require(audio["end"] - audio["start"] > .5, f"Playback did not advance for {voice}")
                    require(not audio["muted"] and audio["nonzeroSamples"] >= 5 and audio["peakRms"] > .0001, f"No sustained decoded speech signal for {voice}")
                    report["voices"].append({"id": voice, **audio})
                    for language in languages:
                        page.locator("#caption").select_option(language)
                        seek(page, first["start"] + min(.6, (first["end"] - first["start"]) / 4))
                        page.wait_for_function("lang=>{const t=[...document.querySelector('#video').textTracks].find(t=>t.language===lang);return t&&t.activeCues?.length>0&&!document.querySelector('#captions').hidden&&document.querySelector('#captions').textContent.trim().length>0}", arg=language)
                        report["captions"].append({"voice": voice, "language": language, "text": page.locator("#captions").inner_text()})
                    for button in page.locator("#chapters [data-cue]").all():
                        cue_id = button.get_attribute("data-cue")
                        expected = next(segment["start"] for segment in clock["segments"] if segment["id"] == cue_id)
                        button.click()
                        page.wait_for_function("t=>Math.abs(document.querySelector('#video').currentTime-t)<.06", arg=expected)
                        report["chapters"].append({"voice": voice, "cueId": cue_id, "time": page.evaluate("document.querySelector('#video').currentTime")})
                    for segment in clock["segments"]:
                        second = segment["start"] + .37 * (segment["sceneEnd"] - segment["start"])
                        seek(page, second)
                        expected = page.evaluate("studio.snapshotAt(document.querySelector('#video').currentTime)")
                        page.locator("#take").click()
                        require(page.evaluate("studio.state") == expected["state"], f"Exact imported state mismatch {voice}/{segment['id']}")
                        require(page.evaluate("document.querySelector('#video').paused"), "Transfer must pause movie")
                        require(page.evaluate("studio.imported") == expected, "Transfer metadata mismatch")
                        report["transfers"].append({"voice": voice, "cueId": segment["id"], "progress": expected["progress"], "exactState": True})
                    page.locator("#watch").scroll_into_view_if_needed()
                    screenshot(f"{voice}-desktop.png")
                # Semantic switching, including replacement while metadata is loading.
                current_clock = page.evaluate("studio.clock")
                last = current_clock["segments"][-1]
                seek(page, last["start"] + .43 * (last["sceneEnd"] - last["start"]))
                page.locator("#speed").select_option("1.25")
                page.locator("#caption").select_option(languages[0])
                before = page.evaluate("studio.snapshotAt(document.querySelector('#video').currentTime)")
                target = voices[0]
                page.locator("#voice").select_option(target)
                page.wait_for_function("id=>studio.voice===id&&!studio.loading", arg=target)
                after = page.evaluate("studio.snapshotAt(document.querySelector('#video').currentTime)")
                require(before["cueId"] == after["cueId"] and abs(before["progress"] - after["progress"]) < .01, "Voice switch changed semantic position")
                require(page.evaluate("document.querySelector('#video').paused&&document.querySelector('#video').playbackRate===1.25"), "Voice switch lost paused state or speed")
                require(page.evaluate("studio.captions") == languages[0], "Voice switch lost captions")
                if len(voices) > 1:
                    page.evaluate("async ids=>{await Promise.all([studio.selectVoice(ids[1]),studio.selectVoice(ids[0])])}", voices)
                    require(page.evaluate("studio.voice") == voices[0] and not page.evaluate("studio.loading"), "Rapid switch retained stale source")
                    rapid = page.evaluate("studio.snapshotAt(document.querySelector('#video').currentTime)")
                    require(rapid["cueId"] == before["cueId"] and abs(rapid["progress"] - before["progress"]) < .01, "Rapid switch changed semantic position")
                    page.evaluate("document.querySelector('#video').play()")
                    page.evaluate("id=>studio.selectVoice(id)", voices[1])
                    require(page.evaluate("!document.querySelector('#video').paused"), "Playing state was not restored after voice switch")
                    page.evaluate("document.querySelector('#video').pause()")
                report["semanticSwitch"] = {"passed": True, "rapidReplacement": len(voices) > 1, "preservesSpeedCaptionsAndPlayState": True}
                # Real keyboard input to a live range control, then exact reset.
                page.locator("#take").click()
                reset_state = page.evaluate("studio.state")
                control = page.locator("[data-control]").first
                control.focus()
                control.press("Home")
                control.press("ArrowRight")
                changed = page.evaluate("studio.state")
                require(changed != reset_state, "Keyboard range control did not update model")
                require(page.locator("#feedback").inner_text().strip(), "No model feedback after keyboard change")
                require(page.locator("#metrics .metric").count() > 0, "No external metric readouts")
                page.locator("#reset").click()
                require(page.evaluate("studio.state") == reset_state, "Reset did not restore exact imported snapshot")
                report["keyboardAndReset"] = True
                if page.evaluate("typeof studio.adapter.pointerAction==='function'"):
                    box = page.locator("#board").bounding_box()
                    page.mouse.move(box["x"] + box["width"] * .3, box["y"] + box["height"] * .3)
                    page.mouse.down()
                    page.mouse.move(box["x"] + box["width"] * .65, box["y"] + box["height"] * .55, steps=6)
                    page.mouse.up()
                    require(page.evaluate("studio.state") != reset_state, "Pointer drag did not change model")
                    report["pointerDrag"] = True
                else:
                    report["pointerDrag"] = "Not supplied by this course; numeric controls are the supported interaction"
                rejected = page.evaluate("()=>{const s=studio.snapshotAt(0);s.courseVersion='999.0.0';try{studio.importSnapshot(s);return false}catch{return true}}")
                require(rejected, "Wrong-version snapshot was accepted")
                report["wrongSnapshotRejected"] = True
                # Find integration cases via public controls. Mathematics is independently
                # asserted by pack check.mjs, not by this UI comparison with the adapter.
                cases = page.evaluate("""()=>{
                  const s=studio, base=s.state, controls=s.adapter.controls(base);
                  const states=[{state:base,actions:[]}];
                  for(const c of controls){const next=[];const vals=[...new Set([c.min,c.min+c.step,(c.min+c.max)/2,c.value,c.max-c.step,c.max])];for(const entry of states)for(const value of vals){try{const action={type:'set',id:c.id,value};const state=s.adapter.reduce(structuredClone(entry.state),action);s.adapter.validateState(state);next.push({state,actions:[...entry.actions,action]})}catch{}}states.splice(0,states.length,...next.slice(0,1000))}
                  return s.course.exercises.map(exercise=>{let good=[],bad=[];for(const entry of states){const grade=s.adapter.grade(entry.state,exercise);if(grade.pass&&good.length<2)good.push(entry);if(!grade.pass&&!bad.length)bad.push(entry)}return {id:exercise.id,good,bad}})
                }""")
                for case in cases:
                    require(case["good"] and case["bad"], f"Could not find both exercise outcomes via public controls: {case['id']}")
                    for expected_pass, entries in ((False, case["bad"]), (True, case["good"])):
                        for entry in entries:
                            page.evaluate("actions=>{for(const action of actions)studio.dispatch(action)}", entry["actions"])
                            page.locator(f"[data-exercise='{case['id']}']").click()
                            displayed = page.locator(f"[data-result='{case['id']}']")
                            require(bool(displayed.inner_text().strip()), "No visible exercise feedback")
                            require(("pass" in (displayed.get_attribute("class") or "").split()) == expected_pass, "Exercise outcome not reflected in UI")
                    report["exercises"].append({"id": case["id"], "passingStates": len(case["good"]), "failingStates": len(case["bad"]), "basis": "UI integration; independent arithmetic is in course check.mjs"})
                page.locator("#lab").scroll_into_view_if_needed()
                screenshot("lab-desktop.png")
                # Native fullscreen uses native captions, returns to the external strip.
                page.locator("#caption").select_option(languages[0])
                first = page.evaluate("studio.clock.segments[0]")
                seek(page, first["start"] + .7)
                page.locator("#video").scroll_into_view_if_needed()
                page.locator("#video").click(position={"x": 20, "y": 20})
                page.evaluate("document.querySelector('#video').pause()")
                page.evaluate("document.querySelector('#video').requestFullscreen()")
                page.wait_for_function("document.fullscreenElement===document.querySelector('#video')")
                page.wait_for_function("[...document.querySelector('#video').textTracks].some(t=>t.mode==='showing')")
                require(page.locator("#captions").is_hidden(), "External captions remained visible in fullscreen")
                page.screenshot(path=str(shots / "fullscreen.png"))
                report["screenshots"].append("fullscreen.png")
                page.evaluate("document.exitFullscreen()")
                page.wait_for_function("!document.fullscreenElement")
                page.wait_for_function("[...document.querySelector('#video').textTracks].some(t=>t.mode==='hidden')")
                report["nativeFullscreen"] = True
                page.set_viewport_size({"width": 390, "height": 844})
                page.locator("#watch").scroll_into_view_if_needed()
                page.locator("#caption").select_option(languages[-1])
                seek(page, first["start"] + .7)
                page.wait_for_function("!document.querySelector('#captions').hidden")
                mobile = page.evaluate("""()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                  captions:parseFloat(getComputedStyle(document.querySelector('#captions')).fontSize),
                  feedback:parseFloat(getComputedStyle(document.querySelector('#feedback')).fontSize),
                  metricValue:parseFloat(getComputedStyle(document.querySelector('#metrics strong')).fontSize),
                  metricLabel:parseFloat(getComputedStyle(document.querySelector('#metrics span')).fontSize),
                  controlLabel:parseFloat(getComputedStyle(document.querySelector('.lab-control .label')).fontSize)})""")
                require(mobile["scrollWidth"] <= mobile["width"] + 1, "Mobile horizontal overflow")
                require(mobile["captions"] >= 16 and mobile["feedback"] >= 14 and mobile["metricValue"] >= 16, "Essential mobile captions/feedback/readout below minimum font sizes")
                report["mobile"] = mobile
                screenshot("mobile.png")
                page.locator("#lab").scroll_into_view_if_needed()
                page.screenshot(path=str(shots / "mobile-lab.png"))
                report["screenshots"].append("mobile-lab.png")
                require(page.locator("#error").is_hidden(), "Player retained an error banner during otherwise valid playback")
                # Isolated negative case: the manifest explicitly offers no playable
                # source. No production file is edited and no substitute voice is valid.
                bad_manifest = json.loads(json.dumps(local_manifest))
                for track in bad_manifest["tracks"]:
                    if track["id"] == bad_manifest["defaultVoice"]:
                        track["sources"] = [{"src": "media/unsupported.nope", "type": "video/x-course-unsupported"}]
                bad_context = browser.new_context(viewport={"width": 900, "height": 700})
                bad_context.route("**/*", route_request)
                bad_context.route(url + "media/manifest.json", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(bad_manifest)))
                bad_page = bad_context.new_page()
                bad_requests = []
                bad_page.on("request", lambda request: bad_requests.append(request.url.replace(url, "./")) if request.resource_type == "media" else None)
                bad_page.goto(url, wait_until="domcontentloaded")
                bad_page.wait_for_function("!document.querySelector('#error').hidden", timeout=10000)
                message = bad_page.locator("#error").inner_text().strip()
                require(message and not bad_page.evaluate("window.ready===true") and not bad_requests and bad_page.locator("#take").is_disabled(), "Unsupported-source manifest did not fail explicitly before playback")
                report["unsupportedSourcesRejected"] = {"passed": True, "message": message, "mediaRequests": bad_requests, "scope": "Isolated served-manifest negative test; production files unchanged"}
                bad_context.close()
                require(not errors and not external and not http_errors and not failed, "Browser page, HTTP, failed-request or external-network errors")
                report["passed"] = True
                context.close()
    except Exception as error:
        report["failure"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        report.update({"wallSeconds": round(time.monotonic() - started, 2), "pageErrors": errors, "httpErrors": http_errors, "unexpectedRequestFailures": failed, "expectedCanceledRequests": len(canceled), "externalRequests": external})
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--browser")
    args = parser.parse_args()
    result = check(args.site.resolve(strict=True), args.report.resolve(), args.browser)
    print(json.dumps({"passed": result["passed"], "course": result["course"], "voices": len(result["voices"]), "captions": len(result["captions"]), "exactTransfers": len(result["transfers"]), "report": str(args.report)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
