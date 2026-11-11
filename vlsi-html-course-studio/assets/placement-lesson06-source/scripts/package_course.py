"""Package only the portable course website, with all final media and source components."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'course';OUT=ROOT/'Placement_Lesson06_Complete_Website.zip'
manifest=json.loads((SITE/'media/manifest.json').read_text(encoding='utf8'))
for track in manifest['tracks']:
    for name in [track['video'],track['timing'],*track['captions'].values()]:
        file=SITE/name
        if not file.is_file() or file.stat().st_size==0:raise RuntimeError(f'Missing delivered asset: {name}')
files=[p for p in SITE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.tmp')]
temporary=OUT.with_suffix('.zip.tmp')
with zipfile.ZipFile(temporary,'w') as archive:
    for file in files:
        method=zipfile.ZIP_STORED if file.suffix.lower() in ('.mp4','.jpg','.png','.mp3','.wav') else zipfile.ZIP_DEFLATED
        archive.write(file,file.relative_to(SITE).as_posix(),compress_type=method)
with zipfile.ZipFile(temporary) as archive:
    assert archive.testzip() is None
    assert 'index.html' in archive.namelist() and 'START_PREVIEW.cmd' in archive.namelist()
temporary.replace(OUT)
report={'archive':OUT.name,'files':len(files),'bytes':OUT.stat().st_size,'sha256':hashlib.file_digest(OUT.open('rb'),'sha256').hexdigest(),'rootEntry':'index.html','includes':'All four videos, 28 captions, timing files, editable site components, local server and starter','excluded':'Production WAVs, raw speech caches, picture masters and Python rendering dependencies remain in the project workspace'}
(ROOT/'review-course/package-check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
