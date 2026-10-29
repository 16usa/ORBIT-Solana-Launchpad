#!/usr/bin/env python3
"""Read-only source verification of the Stage 18 TypeScript compile fix."""
import os
import sys
from pathlib import Path
root = Path(os.environ.get('ORBIT_TYPEFIX_FIXTURE_ROOT', '/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
p = root / 'web/src/chain.ts'
try:
    s = p.read_text(encoding='utf-8')
    assert s.count('ORBIT_STAGE18_BUFFER_TYPE_FIX') == 1, 'missing fix marker'
    assert s.count("const data=Buffer.from(orig.data.split(',').filter(Boolean).map(Number));") == 1, 'Buffer conversion not found'
    assert "const data=Uint8Array.from(orig.data.split(',').filter(Boolean).map(Number));" not in s, 'old Uint8Array conversion remains'
    assert s.count("import { Buffer } from 'buffer';") == 1, 'Buffer import missing or duplicated'
    assert 'ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH' in s, 'Stage 18 was replaced unexpectedly'
    assert 'skipPreflight:false' in s and 'signed.verifySignatures(true)' in s, 'Stage 18 safety checks missing'
    print('STAGE 18 TYPE FIX VERIFIED. Run Replit typecheck next.')
except Exception as exc:
    print('STAGE 18 TYPE FIX VERIFICATION FAILED:', exc, file=sys.stderr)
    sys.exit(1)
