"""Offline C4 policy lint plus actual PlantUML compilation; no CI claims."""
from pathlib import Path
import argparse, hashlib, json, os, platform, re, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]

def discover(root=ROOT):
    excluded = {'.git', '.venv', 'node_modules', '__pycache__', 'vendor'}
    return sorted(p for p in root.rglob('*.puml')
                  if not excluded.intersection(p.relative_to(root).parts))

def expand(path, stack=()):
    path = path.resolve()
    if path in stack:
        raise ValueError(f'Include cycle: {path}')
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Include escapes repository: {path}')
    text = path.read_text(encoding='utf8')
    def include(match):
        name = match[1].strip()
        if any(x in name for x in ('http:', 'https:', '<', '!', '$')):
            raise ValueError(f'Non-local include: {path}: {name}')
        target = (path.parent / name).resolve()
        if target.is_relative_to(ROOT / 'vendor'):
            if not target.is_file():
                raise ValueError(f'Missing vendor include: {target}')
            return "' __C4_VENDOR_INCLUDED__\n"  # upstream macros are not user declarations
        return expand(target, (*stack, path))
    return re.sub(r'^\s*!include\s+([^\n]+)', include, text, flags=re.M)

def lint(path):
    text = expand(path)
    if len(re.findall(r'^\s*@startuml\b', text, re.M)) != 1 or len(re.findall(r'^\s*@enduml\b', text, re.M)) != 1:
        raise ValueError(f'Expected one standalone diagram: {path}')
    if '__C4_VENDOR_INCLUDED__' not in text:
        return
    text = re.sub(r"(?m)^\s*'.*$", '', text)
    if '!pragma layout smetana' not in text:
        raise ValueError(f'Missing Smetana: {path}')
    if re.search(r'\b(?:Bi)?Rel_\w+\s*\(', text):
        raise ValueError(f'Directional relationship: {path}')
    if re.search(r'(?im)^\s*skinparam\b', text):
        raise ValueError(f'Local skinparam: {path}')
    ids = re.findall(r'\b(?:Person(?:_Ext)?|System(?:_Ext|_Boundary)?|Container(?:Db|_Boundary)?|Component(?:Db)?|Deployment_Node)\s*\(\s*(\w+)\s*,', text)
    if len(ids) != len(set(ids)):
        raise ValueError(f'Duplicate IDs: {path}')
    for a, b in re.findall(r'\b(?:Bi)?Rel\s*\(\s*(\w+)\s*,\s*(\w+)\s*,', text):
        if a not in ids or b not in ids:
            raise ValueError(f'Unresolved relationship {a}->{b}: {path}')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--jar')
    p.add_argument('--java', default='java')
    p.add_argument('--render', action='store_true')
    p.add_argument('--lint-only', action='store_true')
    a = p.parse_args()
    if not a.lint_only and not a.jar:
        p.error('--jar required unless --lint-only is selected')
    files = discover()
    standalone = [f for f in files if re.search(r'^\s*@startuml\b', f.read_text(encoding='utf8'), re.M)]
    report = {'success': False, 'python': sys.version, 'platform': platform.platform(), 'commands': [], 'remote_ci_claimed': False,
              'standalone': [f.relative_to(ROOT).as_posix() for f in standalone],
              'fragments': [f.relative_to(ROOT).as_posix() for f in files if f not in standalone],
              'source_sha256': {f.relative_to(ROOT).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
              'render_requested': a.render, 'lint_only': a.lint_only}
    out = ROOT / 'validation/architecture_checks.json'
    out.parent.mkdir(exist_ok=True)
    def run(cmd):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, encoding='utf8', errors='replace', timeout=600,
                           env={**os.environ, 'PYTHONUTF8': '1'})
        report['commands'].append({'command': cmd, 'exit_code': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr})
        if r.returncode:
            raise RuntimeError(f'Command failed: {cmd}')
        return r.stdout + r.stderr
    try:
        if not standalone:
            raise ValueError('No standalone diagrams discovered')
        for f in files:
            s = f.read_text(encoding='utf8')
            if f not in standalone and re.search(r'@(?:start|end)uml', s):
                raise ValueError(f'Invalid fragment: {f}')
            if f not in standalone and f.relative_to(ROOT).as_posix() not in (
                'lab5/integrated/common.puml', 'lab5/integrated/modules/backend.puml',
                'lab5/integrated/modules/frontend.puml', 'lab5/integrated/modules/ml.puml'):
                raise ValueError(f'Unregistered fragment (possibly missing @startuml): {f}')
        for f in standalone:
            lint(f)
        report['linted'] = [str(f.relative_to(ROOT)) for f in standalone]
        if '2.12.0' not in (ROOT / 'vendor/C4.puml').read_text(encoding='utf8'):
            raise ValueError('Wrong C4 version')
        if a.lint_only:
            report['success'] = True
            return 0
        jar = Path(a.jar).resolve()
        report['jar_sha256'] = hashlib.sha256(jar.read_bytes()).hexdigest()
        if report['jar_sha256'] != '862c7d6d0d3bde3c819eac4dfc03cf549046bf1d49c04d18a779eb2d834b77c9':
            raise ValueError('Unexpected PlantUML JAR checksum')
        base = [a.java, '-Djava.awt.headless=true', '-DPLANTUML_LIMIT_SIZE=16000', '-jar', str(jar)]
        if '1.2025.2' not in run(base + ['-version']):
            raise ValueError('Wrong PlantUML version')
        run(base + ['-charset', 'UTF-8', '-failfast2', '-checkonly'] + [str(f) for f in standalone])
        if a.render:
            for fmt in ['png', 'svg']:
                for f in standalone:
                    f.with_suffix('.'+fmt).unlink(missing_ok=True)
                run(base + ['-charset', 'UTF-8', '-Sdpi=180', '-failfast2', '-t'+fmt] + [str(f) for f in standalone])
                for f in standalone:
                    if not f.with_suffix('.'+fmt).is_file():
                        raise ValueError(f'Missing output: {f}')
        run([sys.executable, '-m', 'unittest', 'discover', '-s', 'src', '-v'])
        run([sys.executable, 'lab5/participants/ml/code/demo.py'])
        run([sys.executable, 'lab5/participants/frontend/lab3_code/route_optimization.py'])
        run([sys.executable, 'front_diagramms/route_optimization_frontend_kozharinov.py'])
        report['success'] = True
    except Exception as e:
        report['error'] = str(e)
    finally:
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k in ['success','error']}, ensure_ascii=False))
    return 0 if report['success'] else 1

if __name__ == '__main__':
    sys.exit(main())
