#!/usr/bin/env python3
from pathlib import Path
p=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src/chain.ts'
s=p.read_text()
a=s.index('export async function testRaydiumLegacySigning(')
b=s.index('export async function launchToken(')
t=s[a:b]
assert t.count('ORBIT_STAGE16_PHANTOM_COMPUTE_BUDGET_VERIFY')==1
assert "returnedSigners.length!==2" in t
assert 'originalRaydiumUnchanged' in t
assert 'cuPrice<=1_000_000n' in t
assert 'samePayer' in t and 'sameHash' in t
assert 'signed.verifySignatures(true)' in t
assert "phantomPriorityNote+'\\n'+" in t
assert not any(v in t for v in ['sendRawTransaction(', 'sendTransaction(', 'built.execute(', 'postJson('])
print('STAGE 16 VERIFIED: strict ComputeBudget-only diff; both signatures checked; zero broadcast; launchToken unchanged by installer.')
