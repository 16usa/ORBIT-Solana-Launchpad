from pathlib import Path
root=Path.cwd()/'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
chain=(root/'web/src/chain.ts').read_text()
app=(root/'web/src/App.tsx').read_text()
assert '// ORBIT_STAGE4_PLATFORM_PREFLIGHT' in chain
assert 'PlatformConfig.decode(info.data)' in chain
assert 'info.owner.equals(programId)' in chain
assert "DEVNET_PROGRAM_ID.LAUNCHPAD_PLATFORM" in chain
assert 'platformId\n' in chain
assert '...(import.meta.env.VITE_RAYDIUM_PLATFORM_ID?' not in chain
assert 'await requireLaunchPlatform(connection,config,wallet.publicKey)' in chain
assert 'platformId=override?new PublicKey(override):DEVNET_PROGRAM_ID.LAUNCHPAD_PLATFORM' in chain
assert 'await requireLaunchPlatform(connection,config,wallet.publicKey);' in app
assert 'const uploaded=await postJson' in app
assert app.index('await requireLaunchPlatform(connection,config,wallet.publicKey);') < app.index("const uploaded=await postJson<{id:string}>")
assert "process.env.ENABLE_MAINNET_TRADING==='true'" in (root/'server/app.mjs').read_text()
print('ORBIT Stage 4 static safety checks: PASS (preflight, no implicit mainnet platform, no uploaded metadata before validation)')
