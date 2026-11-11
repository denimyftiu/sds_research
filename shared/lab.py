"""Reproducible pilot harness. No target code is imported or executed."""
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', 'node_modules', 'vendor', '.venv', 'venv', 'dist', 'build', '__pycache__'}
AP_FIELDS = ['id', 'project', 'path', 'language', 'line', 'end_line', 'callee', 'candidate_style', 'reviewed_style', 'review_status']
F_FIELDS = ['id', 'tool', 'profile', 'project', 'path', 'line', 'end_line', 'rule', 'severity', 'access_id', 'candidate_style', 'match_status']
REVIEW_FIELDS = F_FIELDS + ['verdict', 'reviewer', 'evidence', 'triage_minutes', 'fix_minutes']


def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def write_csv(path, rows, fields):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def read_csv(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def uid(*parts):
    return hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:20]


def source_files(target):
    return sorted(p for p in Path(target).rglob('*') if p.suffix in {'.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx'} and not EXCLUDED.intersection(p.relative_to(target).parts))


def style_for(callee):
    tail = callee.split('.')[-1]
    if tail in {'execute', 'executemany', 'executescript', 'query', 'raw', 'rawQuery', 'text', 'RawSQL', 'extra', 'literal', 'whereRaw', 'orderByRaw'}:
        return 'raw'
    if '.objects.' in callee or tail in {'findAll', 'findOne', 'findByPk', 'findMany', 'findUnique', 'createMany', 'bulkCreate'}:
        return 'orm'
    if tail in {'where', 'select', 'join', 'insert', 'update', 'delete', 'filter', 'filter_by'}:
        return 'query_builder'
    return None


def inventory(target, output):
    """High recall candidates only: receiver types and JS syntax require manual audit."""
    if Path(output).exists(): raise ValueError('Access inventory exists; use a new output path to preserve manual edits')
    target = Path(target); rows = []; failures = []
    for p in source_files(target):
        rel = p.relative_to(target).as_posix(); project = rel.split('/')[0]
        content = p.read_text(errors='replace')
        if p.suffix == '.py':
            try:
                tree = ast.parse(content)
            except SyntaxError as exc:
                failures.append({'path': rel, 'error': str(exc)}); continue
            calls = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    callee = ast.unparse(node.func)
                    style = style_for(callee)
                    if style:
                        calls.append((node.lineno, node.end_lineno, callee, style))
            # One terminal access point for nested execute(text(...)) and fluent chains.
            calls = [c for c in calls if not any(o != c and o[0] <= c[0] and o[1] >= c[1] and len(o[2]) > len(c[2]) and o[2].startswith(c[2]+ '(') for o in calls)]
            calls = [c for c in calls if not (c[2].split('.')[-1] in {'text', 'RawSQL', 'literal'} and any(o[2].split('.')[-1] in {'execute', 'raw', 'query'} and o[0] <= c[0] and o[1] >= c[1] for o in calls))]
        else:
            # Deliberately lexical; multiline chains, comments and aliases need review.
            calls = []
            for n, line in enumerate(content.splitlines(), 1):
                if line.lstrip().startswith(('//', '*')): continue
                matches = list(re.finditer(r'\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(', line))
                found = [(m.group(1), style_for(m.group(1))) for m in matches]
                for callee, style in found:
                    if style: calls.append((n, n, callee, style))
        for line, end, callee, style in calls:
            rows.append(dict(zip(AP_FIELDS, [uid(rel,line,callee), project, rel, 'python' if p.suffix=='.py' else 'javascript', line, end, callee, style, '', 'pending'])))
    rows.sort(key=lambda r: (r['path'], r['line'], r['callee']))
    write_csv(output, rows, AP_FIELDS)
    dump(str(output)+'.coverage.json', {'source_files':len(source_files(target)), 'parse_failures':failures, 'classification':'candidate-only', 'limitations':['Unresolved receiver types and aliases', 'JavaScript/TypeScript lexical candidates; manual full-file audit required', 'Excluded generated/vendor/build directories', 'Python nested/fluent calls collapsed heuristically; review point granularity'], 'full_audit_complete':False})


def scan(target, output):
    target = Path(target).resolve(); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    profile = ROOT/'topic_a/rules/pilot.json'
    commands = {
        'semgrep': ['semgrep', 'scan', '--config', str(profile), '--metrics=off', '--disable-version-check', '--no-git-ignore', '--json', str(target)],
        # The native Opengrep CLI does not accept Semgrep's --metrics flag.
        'opengrep': ['opengrep', 'scan', '--config', str(profile), '--disable-version-check', '--no-git-ignore', '--json', str(target)],
        'bandit': ['bandit', '-r', str(target), '-t', 'B608', '-f', 'json', '--ignore-nosec'],
    }
    provenance = {'target':str(target), 'profile':'pilot-custom', 'rules_sha256':hashlib.sha256(profile.read_bytes()).hexdigest(), 'files':{str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files(target)}, 'runs':{}}
    for tool, cmd in commands.items():
        started = time.perf_counter()
        details = {'valid':False, 'command':cmd}
        provenance['runs'][tool] = details
        try:
            version = subprocess.run([tool,'--version'], capture_output=True, text=True, check=True).stdout.strip()
            details['version'] = version
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            details.update(seconds=time.perf_counter()-started, returncode=proc.returncode, stderr=proc.stderr)
            (output/f'{tool}.stderr.log').write_text(proc.stderr)
            (output/f'{tool}.json').write_text(proc.stdout)
            data = json.loads(proc.stdout)
            errors = data.get('errors', [])
            valid = proc.returncode in ({0,1} if tool=='bandit' else {0}) and not errors
            details.update(valid=valid, errors=errors)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            details.update(valid=False, error=str(exc), seconds=time.perf_counter()-started)
    try:
        provenance['python_packages'] = Path('/opt/python-packages.txt').read_text()
    except FileNotFoundError:
        provenance['python_packages'] = 'outside container'
    dump(output/'run.json', provenance)
    if not all(r['valid'] for r in provenance['runs'].values()):
        for tool, result in provenance['runs'].items():
            if not result['valid']:
                diagnostic = result.get('stderr', '').strip() or result.get('error') or str(result.get('errors', []))
                print(f'{tool} failed (exit {result.get("returncode", "unavailable")}): {diagnostic}', file=sys.stderr)
        raise SystemExit('Incomplete scan: inspect run.json; failed tools must not be scored as zero findings.')


def load_findings(scans):
    scans = Path(scans); run = json.loads((scans/'run.json').read_text())
    if not run['runs'] or not all(r.get('valid') for r in run['runs'].values()):
        raise ValueError('Refusing incomplete/failed scan')
    target = Path(run['target'])
    findings = []
    for tool in run['runs']:
        data = json.loads((scans/f'{tool}.json').read_text())
        for r in data.get('results', []):
            if tool=='bandit':
                path,line,end,rule,severity = r['filename'],r['line_number'],max(r.get('line_range') or [r['line_number']]),r['test_id'],r['issue_severity']
            else:
                path,line,end,rule,severity = r['path'],r['start']['line'],r['end']['line'],r['check_id'],r['extra']['severity']
            path = Path(path)
            if path.is_absolute(): path = path.relative_to(target)
            else:
                # Engines invoked with absolute targets normally return absolute paths.
                resolved = path.resolve()
                if resolved.is_relative_to(target): path = resolved.relative_to(target)
            findings.append({'tool':tool,'path':path.as_posix(),'line':int(line),'end_line':int(end),'rule':rule,'severity':severity.upper()})
    return findings, run


def score(labels, scans, output):
    labels = json.loads(Path(labels).read_text()); findings, run = load_findings(scans)
    results = {}
    for tool in run['runs']:
        # Bandit unsupported JS is not a false negative or a true negative.
        applicable = [c for c in labels if tool!='bandit' or c['language']=='python']
        tp=fp=tn=fn=0; misses=[]; alarms=[]
        for c in applicable:
            hit = any(f['tool']==tool and f['path']==c['path'] and f['line']<=c['end_line'] and f['end_line']>=c['start_line'] for f in findings)
            if c['vulnerable']:
                tp += hit; fn += not hit
                if not hit: misses.append(c['id'])
            else:
                fp += hit; tn += not hit
                if hit: alarms.append(c['id'])
        results[tool] = {'tp':tp,'fp':fp,'tn':tn,'fn':fn,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None,'case_count':len(applicable),'misses':misses,'false_alarms':alarms}
    dump(output, {'status':'pilot-only; not a best-tool selection','profile':run['profile'],'metrics':results,'limitation':'Semgrep and Opengrep share engine ancestry and identical custom rules; Bandit is Python-only.'})


def normalize(target, scans, access, output):
    points = read_csv(access); findings, run = load_findings(scans)
    if Path(target).resolve()!=Path(run['target']).resolve(): raise ValueError('Scan target mismatch')
    rows = []; seen = set()
    for f in findings:
        candidates = [p for p in points if p['path']==f['path'] and int(p['line'])<=f['end_line'] and int(p['end_line'])>=f['line']]
        # Ambiguous mappings remain unresolved, never guessed into a denominator.
        p = candidates[0] if len(candidates)==1 else None
        project = f['path'].split('/')[0]
        key = uid(f['tool'], run['profile'], f['path'], f['line'], f['end_line'], f['rule'])
        if key in seen: continue
        seen.add(key)
        rows.append(dict(id=key,profile=run['profile'],project=project,access_id=p['id'] if p else '',candidate_style=p['candidate_style'] if p else 'unknown',match_status='matched' if p else ('ambiguous' if candidates else 'unmatched'),**f))
    write_csv(output, rows, F_FIELDS)


def sample(findings, output, count=34, seed=20261111):
    if Path(output).exists(): raise ValueError('Review file exists; refusing to overwrite human work')
    rows = read_csv(findings); rng = random.Random(seed); selected=[]; strata={}
    # Tool-specific reviews preserve each tool's precision; correlated alerts remain separate.
    for row in rows: strata.setdefault(row['candidate_style'], []).append(row)
    for style, group in sorted(strata.items()):
        group.sort(key=lambda r:r['id']); rng.shuffle(group)
        selected.extend(dict(r,verdict='unreviewed',reviewer='',evidence='',triage_minutes='',fix_minutes='') for r in group[:count])
    write_csv(output, selected, REVIEW_FIELDS)
    dump(str(output)+'.sampling.json', {'seed':seed,'per_style_limit':count,'population':{k:len(v) for k,v in strata.items()},'selected':len(selected),'note':'Candidate-style strata; freeze audited classifications and resample before final study.'})


def report(access, findings, output):
    points=read_csv(access); fs=read_csv(findings); groups={}
    for p in points:
        key=(p['project'],p['candidate_style'])
        groups.setdefault(key,{'access_candidates':0,'findings':{},'flagged_access_points':{}})['access_candidates']+=1
    for (project,style), group in groups.items():
        languages={p['language'] for p in points if p['project']==project and p['candidate_style']==style}
        for tool in ['semgrep', 'opengrep', 'bandit']:
            if tool=='bandit' and languages!={'python'}: continue
            hits=[f for f in fs if f['tool']==tool and f['project']==project and f['candidate_style']==style and f['access_id']]
            group['findings'][tool]=len(hits)
            group['flagged_access_points'][tool]=len({f['access_id'] for f in hits})
        group['candidate_findings_per_100_points']={t:100*n/group['access_candidates'] for t,n in group['findings'].items()}
    dump(output, {'status':'WIP candidate densities only; no validated prevalence or precision claims','groups':[dict(project=k[0],style=k[1],**v) for k,v in sorted(groups.items())],'unmapped_findings':sum(f['match_status']!='matched' for f in fs),'reviewed_points':sum(p['review_status']=='reviewed' for p in points),'total_points':len(points),'inference':'Deferred until snapshots, full access-point audits and manual finding reviews are complete.'})


def fetch(lock, destination):
    projects=json.loads(Path(lock).read_text())
    if not projects: raise ValueError('Lock manifest is empty: screen candidates and record full commit SHAs first')
    for p in projects:
        if not re.fullmatch(r'[0-9a-f]{40}',p['commit'] or ''): raise ValueError('Expected full 40-character commit SHA')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',p['id']): raise ValueError('Invalid project id')
        if not re.fullmatch(r'https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git',p['repository']): raise ValueError('Expected GitHub HTTPS repository')
        dest=Path(destination)/p['id']; dest.mkdir(parents=True,exist_ok=False)
        subprocess.run(['git','init',str(dest)],check=True)
        subprocess.run(['git','-C',str(dest),'fetch','--depth','1',p['repository'],p['commit']],check=True)
        subprocess.run(['git','-C',str(dest),'checkout','--detach','FETCH_HEAD'],check=True)
        actual=subprocess.check_output(['git','-C',str(dest),'rev-parse','HEAD'],text=True).strip()
        if actual!=p['commit']: raise ValueError('Snapshot mismatch')
    dump(Path(destination)/'snapshots.json',projects)


def gates(findings, output):
    fs=read_csv(findings)
    dump(output, {'status':'seeded policy illustration only; no CI or commit replay performed','finding_count':len(fs),'policies':{'block_any':bool(fs),'block_high':any(f['severity'] in {'HIGH','CRITICAL','ERROR'} for f in fs),'report_only':False},'timing':None,'triage_cost':None,'fix_time':None,'severity_note':'ERROR/WARNING/INFO are engine rule levels, not calibrated vulnerability severities; mapping must be frozen before C.'})



def pilot(target, output_root):
    """Create an isolated B run; publish its pointer only after every stage succeeds."""
    output_root = Path(output_root).resolve()
    runs = output_root/'runs'; runs.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='pilot-', dir=runs))
    print(f'B run directory: {output}', flush=True)
    inventory(target, output/'access_points.csv')
    scan(target, output/'scans')
    normalize(target, output/'scans', output/'access_points.csv', output/'findings.csv')
    sample(output/'findings.csv', output/'review.csv')
    report(output/'access_points.csv', output/'findings.csv', output/'report.json')
    # Same-filesystem atomic replace: a failed run never replaces a successful pointer.
    pointer = {'directory': output.relative_to(output_root).as_posix()}
    with tempfile.NamedTemporaryFile(mode='w', dir=output_root, delete=False) as f:
        json.dump(pointer, f); f.write('\n'); temporary = f.name
    os.replace(temporary, output_root/'latest.json')
    print(f'B completed: {output} (recorded in {output_root / "latest.json"})', flush=True)


def pilot_gates(output_root, output):
    pointer = Path(output_root)/'latest.json'
    if not pointer.exists(): raise ValueError('No completed B run found; run make b first')
    latest = json.loads(pointer.read_text())
    gates(Path(output_root)/latest['directory']/'findings.csv', output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inventory','scan','score','normalize','sample','report','fetch','gates','pilot','pilot_gates','test'])
    parser.add_argument('args',nargs='*'); ns=parser.parse_args()
    if ns.command=='test':
        raise SystemExit(subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v']).returncode)
    globals()[ns.command](*ns.args)

if __name__=='__main__': main()
