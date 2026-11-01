import argparse, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--jar',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
logs=[]
for f in sorted((root/'diagrams').rglob('*.puml')):
    for mode in ('-checkonly','-tpng','-tsvg'):
        r=subprocess.run(['java','-Djava.awt.headless=true','-jar',str(Path(a.jar).resolve()),'-charset','UTF-8','-failfast2',mode,str(f)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(f'{f.relative_to(root)} {mode}: exit={r.returncode}\n{r.stdout}{r.stderr}')
        (root/'validation').mkdir(exist_ok=True)
        (root/'validation/render.txt').write_text('\n'.join(logs),encoding='utf-8')
        if r.returncode: raise SystemExit(r.returncode)
print(f'Validated and rendered {len(logs)//3} diagrams')
