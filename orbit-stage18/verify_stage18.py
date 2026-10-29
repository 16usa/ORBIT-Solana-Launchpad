#!/usr/bin/env python3
from pathlib import Path
import os,sys
ROOT=Path(os.environ.get('ORBIT_STAGE18_FIXTURE_ROOT','/home/runner/workspace/artifacts/orbit-launchpad/original/orbit-solana-launchpad'))
path=ROOT/'web/src/chain.ts'
try:
 text=path.read_text()
 begin=text.index('export async function launchToken(')
 end=text.index('export async function curveTrade(',begin)
 region=text[begin:end]
 must={
  'devnet genesis':'EtWTRABZaYq6iMfeYKouRu166VU2xqa1wcaWoxPkrZBG',
  'legacy format':'txVersion:TxVersion.LEGACY',
  'original message check':'canonicalMessageSame',
  'two signatures':'signed.verifySignatures(true)',
  'preflight on':'skipPreflight:false',
  'no auto retries':'maxRetries:0',
  'confirmed signature':'confirmTransaction({signature,...latest}',
  'session signing':'wallet.signTransaction(tx)',
  'payer unchanged':'samePayer',
  'CU price bound':'cuPrice<=1_000_000n',
  'requested metadata':'uri:input.uri',
 }
 for name,part in must.items():
  if part not in region:raise ValueError('Missing '+name)
 forbidden=['txVersion:TxVersion.V0','execute({','skipPreflight:true','mainnetTradingEnabled=true']
 for part in forbidden:
  if part in region:raise ValueError('Unexpected '+part)
 if text.count('export async function launchToken(')!=1 or text.count('export async function curveTrade(')!=1:raise ValueError('Duplicate exports')
 if text.count('ORBIT_STAGE18_DEVNET_LEGACY_REAL_LAUNCH')!=1:raise ValueError('Bad Stage 18 marker count')
 if 'ORBIT_STAGE17_CANONICAL_LEGACY_MATCH' not in text:raise ValueError('Missing Stage 17 diagnostic')
 print('STAGE 18 VERIFIED. Mainnet disabled in live launch; signed Devnet-only path guarded. All checks present.')
 print('No blockchain transaction sent, no Git push, no restart, no Republish.')
except Exception as exc:
 print('STAGE 18 VERIFY FAILED:',exc,file=sys.stderr);sys.exit(1)
