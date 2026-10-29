#!/usr/bin/env python3
"""Read-only verification of the installed ORBIT Stage 11 source."""
from pathlib import Path
import sys
p = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src/chain.ts'
if not p.is_file():
    sys.exit('FAIL: Run inside /home/runner/workspace with ORBIT source')
s = p.read_text(encoding='utf-8')
start = s.find('export async function launchToken(')
end = s.find('export async function curveTrade(', start)
if start < 0 or end < 0:
    sys.exit('FAIL: launchToken block not found')
block = s[start:end]
tests = {
    'marker': s.count('ORBIT_STAGE11_ALT_RESOLUTION') == 1,
    'Stage 10 prerequisite': 'ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH' in s,
    'no obsolete ALT rejection': 'Unexpected address lookup table' not in block and 'Unexpected lookup table in launch' not in block,
    'fetch ALT on Devnet RPC': 'getAddressLookupTable(' in block,
    'resolve V0 keys': 'getAccountKeys({addressLookupTableAccounts:lookupTables})' in block,
    'program validation sees resolved keys': 'resolvedKeys.get(ix.programIdIndex)' in block,
    'account indexes checked': 'ix.accountKeyIndexes.some' in block,
    'Devnet-only guard': "config.network!=='devnet'" in block,
    'network simulation before wallet': block.find('simulateTransaction(tx') < block.find('wallet.signTransaction(tx)') and block.find('simulateTransaction(tx') > 0,
    'no skip-preflight': 'skipPreflight:false' in block and 'skipPreflight:true' not in block,
}
for title, ok in tests.items():
    print(('PASS' if ok else 'FAIL') + ': ' + title)
if not all(tests.values()):
    sys.exit(1)
print('STAGE 11 VERIFIED (static checks only; blockchain execution NOT tested)')
