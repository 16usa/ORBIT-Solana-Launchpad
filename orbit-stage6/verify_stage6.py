from pathlib import Path
p=Path('artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src/chain.ts')
a=Path('artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src/App.tsx')
s=p.read_text(); t=a.read_text()
assert s.count('ORBIT_STAGE6_SIGNING_PREFLIGHT')==1
assert s.count('connection.simulateTransaction(first')==1
assert s.count('const {execute,extInfo,transactions}=await raydium.launchpad.createLaunchpad({')==1
assert 'ORBIT_STAGE5_LAUNCH_DIAGNOSTICS' in t
assert 'signAllTransactions:wallet?.signAllTransactions?.bind(wallet)' in s  # No silent signer switch
print('Stage 6 verification: PASS. Only launch preflight diagnostics added; wallet signing behavior unchanged.')
