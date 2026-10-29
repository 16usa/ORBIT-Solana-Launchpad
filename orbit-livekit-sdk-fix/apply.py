#!/usr/bin/env python3
"""ORBIT LiveKit production dependency fix. Does not restart servers or deploy."""
from pathlib import Path
import json
import subprocess
import sys

root = Path('/home/runner/workspace')
if not (root / 'pnpm-workspace.yaml').is_file():
    print('ERROR: Run inside the original ORBIT Replit workspace; pnpm-workspace.yaml not found.')
    sys.exit(1)
pkg = root / 'artifacts/api-server/package.json'
if not pkg.is_file():
    print(f'ERROR: API server package missing: {pkg}')
    sys.exit(1)
original = pkg.read_text(encoding='utf-8')
data = json.loads(original)
if data.get('name') != '@workspace/api-server':
    print('ERROR: Unexpected API package name. No changes made.')
    sys.exit(1)
deps = data.setdefault('dependencies', {})
if 'livekit-server-sdk' not in deps:
    deps['livekit-server-sdk'] = '^2.19.1'
    deps_sorted = dict(sorted(deps.items(), key=lambda x: x[0].lower()))
    data['dependencies'] = deps_sorted
    pkg.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Added livekit-server-sdk as a PRODUCTION dependency of @workspace/api-server.')
else:
    print('livekit-server-sdk already declared as an API server dependency:', deps['livekit-server-sdk'])
print('Installing dependencies and updating pnpm-lock.yaml...')
try:
    subprocess.run(['pnpm', 'install', '--no-frozen-lockfile'], cwd=root, check=True)
except Exception as exc:
    print('ERROR: Dependency install did not complete:', exc)
    print('Check connectivity/PNPM errors, then rerun this installer.')
    sys.exit(2)
print('Checking LiveKit Node SDK can be imported from API artifact...')
subprocess.run(['node', '--input-type=module', '-e',
                "import('livekit-server-sdk').then(m=>{if(!m.AccessToken) throw Error('AccessToken missing'); console.log('LIVEKIT SERVER SDK: OK')})"],
               cwd=pkg.parent, check=True)
print('PATCH INSTALLED. This changes package manifests/lockfile only.')
print('NO process was restarted, NO GitHub push, NO Republish.')
print('After confirming Development API is healthy, Republish the API artifact for the published .replit.app to receive the dependency.')
