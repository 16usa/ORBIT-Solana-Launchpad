#!/usr/bin/env python3
from pathlib import Path
s=(Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src/chain.ts').read_text()
start=s.index('export async function testRaydiumLegacySigning(')
end=s.index('export async function launchToken(')
sec=s[start:end]
assert sec.count('ORBIT_STAGE15_RETURNED_MESSAGE_DIFF')==1
assert 'Wallet/adapter returned a DIFFERENT LEGACY message' in sec
assert 'signed.verifySignatures(false)' in sec
assert 'tx.serializeMessage()' in sec
assert 'NO broadcast; NO token created' in sec
assert not any(x in sec for x in ['sendRawTransaction(', 'sendTransaction(', 'execute(', 'postJson('])
print('STAGE 15 VERIFIED: diagnostic-only code, no broadcast')
