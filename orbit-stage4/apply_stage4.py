#!/usr/bin/env python3
"""ORBIT Stage 4: Devnet LaunchLab PlatformConfig preflight.

No transactions, no dev server restart, no process kills, no GitHub push.
Only modifies chain.ts and App.tsx of existing ORBIT workspace.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys
import re

ROOT = Path.cwd().resolve()
SRC = ROOT / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = SRC / 'web/src/chain.ts'
APP = SRC / 'web/src/App.tsx'
MARKER = '// ORBIT_STAGE4_PLATFORM_PREFLIGHT'

PREFLIGHT = "// ORBIT_STAGE4_PLATFORM_PREFLIGHT\n// Raydium SDK defaults to the MAINNET platform unless platformId is supplied.\n// On Devnet use the SDK's Devnet platform constant; allow an explicitly\n// configured Devnet platform only when its on-chain account validates.\n// This read-only check never creates accounts or sends transactions.\nexport async function requireLaunchPlatform(\n connection:Connection, config:AppConfig, walletKey:PublicKey|null|undefined\n):Promise<PublicKey>{\n if(config.network!=='devnet')throw new Error('ORBIT token creation is restricted to Devnet; Mainnet launch remains disabled.');\n const programId=program(config);\n const override=String(import.meta.env.VITE_RAYDIUM_PLATFORM_ID||'').trim();\n let platformId:PublicKey;\n try{platformId=override?new PublicKey(override):DEVNET_PROGRAM_ID.LAUNCHPAD_PLATFORM}\n catch{throw new Error('Configured VITE_RAYDIUM_PLATFORM_ID is not a valid Solana address.');}\n const info=await connection.getAccountInfo(platformId,'confirmed');\n if(!info){\n  const help=override?'Your configured VITE_RAYDIUM_PLATFORM_ID':'Raydium SDK Devnet LAUNCHPAD_PLATFORM';\n  throw new Error(`${help} ${platformId.toBase58()} does not exist on Solana Devnet. Create/choose a verified Devnet PlatformConfig before launching; ORBIT will not fall back to the mainnet address.`);\n }\n if(!info.owner.equals(programId))throw new Error(`PlatformConfig ${platformId.toBase58()} is owned by ${info.owner.toBase58()}, not the Devnet LaunchLab program ${programId.toBase58()}.`);\n try{PlatformConfig.decode(info.data)}catch{throw new Error('The selected Devnet PlatformConfig could not be decoded by Raydium SDK.');}\n return platformId;\n}\n\n"



def once(src: str, old: str, new: str, title: str) -> str:
    n = src.count(old)
    if n != 1:
        raise RuntimeError(f'{title}: expected exactly one matching source fragment, got {n}. No files modified.')
    return src.replace(old, new, 1)


def run():
    if not CHAIN.is_file() or not APP.is_file():
        raise RuntimeError('Not the ORBIT workspace. Run from /home/runner/workspace.')
    chain = CHAIN.read_text('utf-8')
    app = APP.read_text('utf-8')
    if MARKER in chain:
        if 'await requireLaunchPlatform(connection,config,wallet.publicKey)' in chain and 'requireLaunchPlatform(connection,config,wallet.publicKey)' in app:
            print('ORBIT Stage 4 already installed. No changes made.')
            return
        raise RuntimeError('Partial Stage 4 markers detected. No changes made.')
    # Anchor near a stable helper, independent of Stage 2/3 changes.
    chain = once(chain, 'export async function launchToken(', PREFLIGHT + 'export async function launchToken(', 'chain preflight insertion')
    chain = once(chain,
       " const raydium=await sdk(connection,config,wallet);\n const programId=program(config);const mint=Keypair.generate();",
       " const platformId=await requireLaunchPlatform(connection,config,wallet.publicKey);\n const raydium=await sdk(connection,config,wallet);\n const programId=program(config);const mint=Keypair.generate();",
       'launch preflight before SDK transaction builder')
    # Replace SDK's implicit mainnet-only default and any unverified custom ID.
    chain = once(chain,
       "  ...(import.meta.env.VITE_RAYDIUM_PLATFORM_ID?{platformId:new PublicKey(import.meta.env.VITE_RAYDIUM_PLATFORM_ID)}:{})",
       "  platformId",
       'explicit verified PlatformConfig in createLaunchpad')
    imports = re.findall(r"import \{([^}]+)\} from './chain';", app)
    if len(imports) != 1 or 'launchToken' not in imports[0] or 'requireLaunchPlatform' in imports[0]:
        raise RuntimeError('UI import: expected one chain.ts import containing launchToken. No files modified.')
    app = once(app, "import {"+imports[0]+"} from './chain';",
               "import {"+imports[0].rstrip()+",requireLaunchPlatform} from './chain';", 'UI import')
    # Covers Stage 2/3 where the initial create form already performed RPC checks.
    app = once(app,
       "  const uploaded=await postJson<{id:string}>('/api/media',{base64:await uploadBase64(file)});",
       "  // Fail before uploading metadata when the wallet has no Devnet platform config.\n  await requireLaunchPlatform(connection,config,wallet.publicKey);\n  const uploaded=await postJson<{id:string}>('/api/media',{base64:await uploadBase64(file)});",
       'UI preflight before upload')
    # Validate all expectations BEFORE writing anything.
    assert MARKER in chain and chain.count('platformId\n') >= 1
    assert app.count('await requireLaunchPlatform(connection,config,wallet.publicKey);') == 1
    timestamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=SRC/'.orbit-backups'/f'stage4-{timestamp}'
    backup.mkdir(parents=True, exist_ok=False)
    shutil.copy2(CHAIN, backup/'chain.ts')
    shutil.copy2(APP, backup/'App.tsx')
    CHAIN.write_text(chain, encoding='utf-8')
    APP.write_text(app, encoding='utf-8')
    print('Stage 4 installed: Raydium Devnet PlatformConfig preflight.')
    print('Verified PlatformConfig passed explicitly to the Raydium SDK.')
    print('No token creation, transaction signing, process restart, or publication.')
    print('Backups:', backup)
    print('Next: TypeScript checks and Devnet preflight with your connected wallet.')


if __name__ == '__main__':
    try: run()
    except Exception as exc:
        print('INSTALL FAILED:', exc, file=sys.stderr)
        sys.exit(1)
