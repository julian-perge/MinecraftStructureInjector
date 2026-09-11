"""Build a compact local gallery from actual Minecraft capture manifests."""
from pathlib import Path
import json,html,shutil
from PIL import Image

root=Path(__file__).resolve().parents[1]
source=root/'artifacts/raid';out=root/'gallery/raid';out.mkdir(parents=True,exist_ok=True)
final=out/'final';final.mkdir(exist_ok=True)
job=json.loads((source/'final/manifest.json').read_text())
patch=json.loads((source/'qualified/manifest.json').read_text())
patched={c['file'] for c in patch['captures']}
cards=[]
for c in job['captures']:
    name=Path(c['file']).stem+'.jpg'
    with Image.open(source/('qualified' if c['file'] in patched else 'final')/c['file']) as im:
        im.thumbnail((1280,720));im.convert('RGB').save(final/name,quality=88,optimize=True)
    label=html.escape(c['id'].replace('_',' ')+' / '+c['angle'])
    cards.append(f'<figure data-label="{label}"><a href="final/{name}"><img loading="lazy" src="final/{name}" alt="{label}"></a><figcaption>{label}</figcaption></figure>')
for i in range(1,5):
    folder=out/f'pass-{i}';folder.mkdir(exist_ok=True)
    for image in (source/f'pass-{i}').glob('review-*.jpg'):shutil.copy2(image,folder/image.name)
    review=source/f'pass-{i}/review.md'
    if review.exists():shutil.copy2(review,folder/'review.md')
regression=out/'final-review';regression.mkdir(exist_ok=True)
for image in (source/'final').glob('review-*.jpg'):shutil.copy2(image,regression/image.name)
shutil.copy2(source/'qualified/review-contact-sheet.jpg',regression/'junction-recheck.jpg')
(out/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Classic Raid — Structure Lab</title>
<style>body{font:16px system-ui;background:#101820;color:#edf3f7;margin:32px}h1{margin-bottom:8px}input{padding:12px;width:min(600px,90%);margin:20px 0;background:#22313e;color:white;border:1px solid #718391;border-radius:8px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}figure{margin:0;background:#22313e;border-radius:8px;overflow:hidden}img{width:100%;display:block}figcaption{padding:12px}a{color:#a6d9ff}</style>
<h1>Classic Raid</h1><p>Los Angeles mansion · Minecraft 1.21.1 · One block per metre · 121 in-game camera angles</p><p><a href="README.md">Build and review notes</a></p><input id="filter" aria-label="Filter camera views" placeholder="Filter: garage, pool, bedroom, courtyard…"><main>'''+''.join(cards)+'''</main><script>document.querySelector('#filter').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('figure').forEach(f=>f.hidden=!f.dataset.label.includes(q))})</script></html>''',encoding='utf-8')
print(out/'index.html')
