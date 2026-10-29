#!/usr/bin/env python3
"""Correct a Stage 18 TypeScript Buffer type mismatch. No network or process operations."""
from pathlib import Path
from datetime import datetime, timezone
import os
import shutil
import sys
import tempfile

ROOT = Path(os.environ.get(
    'ORBIT_TYPEFIX_FIXTURE_ROOT',
    '/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'
))
TARGET = ROOT / 'web/src/chain.ts'
STAGE = 'ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH'
MARKER = 'ORBIT_STAGE18_BUFFER_TYPE_FIX'
OLD = "const data=Uint8Array.from(orig.data.split(',').filter(Boolean).map(Number));"
NEW = "const data=Buffer.from(orig.data.split(',').filter(Boolean).map(Number));"
IMPORT = "import { Buffer } from 'buffer';\n"


def install():
    if not TARGET.is_file():
        raise RuntimeError(f'ORBIT source file not found: {TARGET}')
    current = TARGET.read_text(encoding='utf-8')
    if STAGE not in current:
        raise RuntimeError('Stage 18 launch code is missing. No changes made.')
    if MARKER in current:
        if NEW not in current or IMPORT.strip() not in current:
            raise RuntimeError('Incomplete previous installation; no changes made.')
        print('TYPE FIX ALREADY INSTALLED')
        return
    if current.count(OLD) != 1:
        raise RuntimeError('Expected Stage 18 Uint8Array line not found exactly once. No changes made.')
    if 'new TransactionInstruction({' not in current:
        raise RuntimeError('TransactionInstruction constructor is missing. No changes made.')
    if 'import { Buffer } from' in current or 'import Buffer from' in current:
        raise RuntimeError('Unexpected existing Buffer import; manual review required.')
    firstline = current.splitlines()[0] if current.splitlines() else ''
    if not firstline.startswith('import '):
        raise RuntimeError('Unexpected import header. No changes made.')
    updated = IMPORT + current.replace(OLD, '// ' + MARKER + '\n   ' + NEW, 1)
    if updated.count(MARKER) != 1 or updated.count(NEW) != 1:
        raise RuntimeError('Patch verification failed. No changes made.')
    backup_dir = ROOT / '.orbit-backups' / ('stage18-typefix-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / 'chain.ts'
    shutil.copy2(TARGET, backup)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=TARGET.parent, prefix='.orbit18-typefix-', delete=False) as f:
            f.write(updated)
            temp_path = Path(f.name)
        os.replace(temp_path, TARGET)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
    print('STAGE 18 TYPE FIX INSTALLED')
    print('Backup:', backup)
    print('Only the Buffer import and one typed-array construction line changed.')
    print('No restart, push, Republish, or blockchain operation performed.')

if __name__ == '__main__':
    try:
        install()
    except Exception as exc:
        print('STAGE 18 TYPE FIX STOPPED:', exc, file=sys.stderr)
        sys.exit(1)
