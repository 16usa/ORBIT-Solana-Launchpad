#!/usr/bin/env python3
"""ORBIT Devnet hardening patch. Only edits known ORBIT files; no installs, restarts or pushes."""
from pathlib import Path
from datetime import datetime, timezone
import sys
import shutil


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one matching source block, got {count}; no files changed")
    return text.replace(old, new, 1)


def plan_patch(root):
    targets = {}
    app = root / 'server/app.mjs'
    core = root / 'server/core.mjs'
    ui = root / 'web/src/App.tsx'
    api = root / 'web/src/api.ts'
    chain = root / 'web/src/chain.ts'
    vite = root / 'vite.config.ts'
    test = root / 'tests/server.test.mjs'
    for p in [app, core, ui, api, chain, vite, test]:
        if not p.is_file():
            raise RuntimeError(f"Missing ORBIT source: {p}")

    s = app.read_text()
    s = replace_once(s,
        "const publicBase=formatPublicUrl(process.env.PUBLIC_BASE_URL||'');",
        """const publicBase=formatPublicUrl(process.env.PUBLIC_BASE_URL||'');
// Fail closed: this prototype has local, non-durable metadata and is NOT safe for mainnet launches.
const launchEnabled=cluster==='devnet' && !!publicBase && !!process.env.RAYDIUM_PROGRAM_ID;
const launchBlockReason=cluster==='mainnet-beta'
  ? 'Mainnet token creation is disabled pending permanent metadata storage, integration tests and a security review.'
  : !publicBase
    ? 'Set PUBLIC_BASE_URL to a reachable HTTPS origin before testing Devnet launches.'
    : !process.env.RAYDIUM_PROGRAM_ID
      ? 'Set the verified Raydium Devnet program ID (RAYDIUM_PROGRAM_ID) before launching.'
      : '';
// A Jupiter API key by itself must never enable real-money trades accidentally.
const mainnetTradingEnabled=cluster==='mainnet-beta'
  && process.env.ENABLE_MAINNET_TRADING==='true'
  && !!process.env.JUPITER_API_KEY;""", "server: launch controls")
    s = replace_once(s,
        " if(cluster==='mainnet-beta' && !allowed)throw new Error('RAYDIUM_PROGRAM_ID allowlist is required on mainnet');\n if(allowed && input.programId!==allowed)throw new Error('Program is not allowlisted');",
        """ if(!allowed)throw new Error('RAYDIUM_PROGRAM_ID allowlist is required before registering any launch');
 if(input.programId!==allowed)throw new Error('Program is not allowlisted');
 const instructions=transaction.transaction.message.instructions||[];
 if(!instructions.some(i=>i.programId===allowed))throw new Error('Launch transaction did not invoke the allowlisted Raydium program');""", "server: chain verification")
    s = replace_once(s,
        "if(pathname==='/api/config'){return json(res,200,{network:cluster,rpc:rpcPublic,publicBase,tradeEnabled:!!process.env.JUPITER_API_KEY,raydiumProgramAllowlisted:!!process.env.RAYDIUM_PROGRAM_ID});}",
        "if(pathname==='/api/config'){return json(res,200,{network:cluster,rpc:rpcPublic,publicBase,tradeEnabled:mainnetTradingEnabled,mainnetTradingEnabled,launchEnabled,launchBlockReason,raydiumProgramAllowlisted:!!process.env.RAYDIUM_PROGRAM_ID});}", "server: config")
    s = replace_once(s,
        "   if(!filename) return error(res,400,'Upload image first');",
        "   if(!filename) return error(res,400,'Upload image first');\n   if(!launchEnabled)return error(res,503,launchBlockReason);", "server: metadata gate")
    s = replace_once(s,
        "   const v=parseLaunchInput(await readJson(req,4000));const metadataFile=path.join(metadir,v.metadataId+'.json');",
        "   const v=parseLaunchInput(await readJson(req,4000));\n   if(!launchEnabled)return error(res,503,launchBlockReason);\n   const metadataFile=path.join(metadir,v.metadataId+'.json');", "server: registration gate")
    old_jupiter="if(cluster!=='mainnet-beta'||!process.env.JUPITER_API_KEY)return error(res,503,'Mainnet Jupiter API not configured');"
    if s.count(old_jupiter)!=2: raise RuntimeError(f"server: expected 2 Jupiter route gates, found {s.count(old_jupiter)}")
    s = s.replace(old_jupiter,"if(!mainnetTradingEnabled)return error(res,503,'Mainnet trading is disabled until explicitly enabled and reviewed');")
    targets[app] = s

    s = core.read_text()
    s = replace_once(s,
        " if(uri.protocol!=='https:' && !/^http:\\/\\/localhost(?::\\d+)?$/.test(base)) throw new Error('PUBLIC_BASE_URL must use HTTPS');\n return uri.href.replace(/\\/$/,'');",
        """ if(uri.protocol!=='https:' && !/^http:\\/\\/localhost(?::\\d+)?$/.test(base)) throw new Error('PUBLIC_BASE_URL must use HTTPS');
 if(uri.username||uri.password||uri.search||uri.hash||uri.pathname!=='/')throw new Error('PUBLIC_BASE_URL must be an origin without credentials, path, query or fragment');
 return uri.origin;""", "core: immutable metadata base URL")
    targets[core] = s

    s = api.read_text()
    s = replace_once(s,
        'publicBase:string;tradeEnabled:boolean;raydiumProgramAllowlisted:boolean',
        'publicBase:string;tradeEnabled:boolean;mainnetTradingEnabled:boolean;launchEnabled:boolean;launchBlockReason:string;raydiumProgramAllowlisted:boolean',
        "client: config types")
    targets[api] = s

    s = chain.read_text()
    s = replace_once(s,
        " if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect a wallet that supports transaction signing');\n const raydium=await sdk(connection,config,wallet);",
        " if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect a wallet that supports transaction signing');\n if(!config.launchEnabled)throw new Error(config.launchBlockReason||'Token creation is currently disabled');\n const raydium=await sdk(connection,config,wallet);", "chain: launch gating")
    s = replace_once(s,
        " if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect wallet');\n if(slippageBps<10||slippageBps>500)",
        " if(!wallet.publicKey||!wallet.signAllTransactions)throw new Error('Connect wallet');\n if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled)throw new Error('Mainnet trading is disabled until reviewed');\n if(slippageBps<10||slippageBps>500)", "chain: curve safety")
    targets[chain] = s

    s = ui.read_text()
    s = replace_once(s,
        "if(!config.publicBase){notify('Set PUBLIC_BASE_URL to your public HTTPS domain on the server first');return}",
        "if(!config.launchEnabled){notify(config.launchBlockReason||'Token creation is currently disabled');return}", "UI: creator gate")
    s = replace_once(s,
        "{!config.publicBase&&<p className=\"warning-text\">Token creation requires PUBLIC_BASE_URL set to a public HTTPS URL.</p>}",
        "{!config.launchEnabled&&<p className=\"warning-text\">{config.launchBlockReason}</p>}", "UI: creator status")
    s = replace_once(s,
        "disabled={busy||!config.publicBase}",
        "disabled={busy||!config.launchEnabled}", "UI: create button")
    s = replace_once(s,
        "if(route==='jupiter'&&!config.tradeEnabled){notify('Configure JUPITER_API_KEY to enable Jupiter');return}",
        "if(config.network==='mainnet-beta'&&!config.mainnetTradingEnabled){notify('Mainnet trading is disabled until reviewed');return}if(route==='jupiter'&&!config.tradeEnabled){notify('Jupiter swaps are not enabled');return}", "UI: trading safety")
    s = replace_once(s,
        "disabled={busy||!wallet.publicKey||route==='jupiter'&&!config.tradeEnabled}",
        "disabled={busy||!wallet.publicKey||config.network==='mainnet-beta'&&!config.mainnetTradingEnabled||route==='jupiter'&&!config.tradeEnabled}", "UI: trading button")
    targets[ui] = s

    s = vite.read_text()
    # Repo uses the standalone Vite web port (Replit 21532) while the API is on 8080.
    # Use a proxy in dev only; production paths remain routed by Replit's artifact router.
    if "server: {\n    host: '0.0.0.0'," in s:  # current GitHub version
        s = replace_once(s,
            "    allowedHosts: true,\n  },",
            "    allowedHosts: true,\n    proxy: Object.fromEntries(['/api', '/media', '/metadata'].map(route => [route, { target: `http://127.0.0.1:${process.env.API_PORT || '8080'}`, changeOrigin: true }])),\n  },",
            "Vite: proxied backend")
    elif 'server: {' in s and 'proxy:' in s:
        # Standalone ZIP has a hardcoded local :3000 proxy; it needs to respect API_PORT.
        s = replace_once(s,
            "'/api': 'http://127.0.0.1:3000', '/media': 'http://127.0.0.1:3000', '/metadata': 'http://127.0.0.1:3000'",
            "'/api': `http://127.0.0.1:${process.env.API_PORT || '3000'}`, '/media': `http://127.0.0.1:${process.env.API_PORT || '3000'}`, '/metadata': `http://127.0.0.1:${process.env.API_PORT || '3000'}`",
            "Vite: configurable standalone API")
    else:
        raise RuntimeError('Unrecognized Vite configuration; not changing it')
    targets[vite] = s

    s = test.read_text()
    s += """
test('Metadata origin URL rejects unsafe paths, credentials and query strings',()=>{
 assert.throws(()=>formatPublicUrl('https://demo.example/api?token=private'),/origin/);
 assert.throws(()=>formatPublicUrl('https://user:secret@demo.example/'),/origin/);
 assert.throws(()=>formatPublicUrl('https://demo.example/#temporary'),/origin/);
});
test('Launch readiness is explicit and boolean for UI safety checks',async()=>{
 const server=makeServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const response=await fetch(`http://127.0.0.1:${server.address().port}/api/config`);
  const config=await response.json();
  assert.equal(typeof config.launchEnabled,'boolean');
  assert.equal(typeof config.mainnetTradingEnabled,'boolean');
  assert.equal(typeof config.launchBlockReason,'string');
  assert.equal(config.launchEnabled && config.network==='mainnet-beta',false);
 }finally{await new Promise(resolve=>server.close(resolve))}
});
"""
    targets[test] = s
    return targets


def main():
    cwd=Path.cwd()
    candidates=[cwd/'artifacts/orbit-launchpad/original/orbit-solana-launchpad',cwd/'original/orbit-solana-launchpad',cwd]
    root=next((p for p in candidates if (p/'server/app.mjs').is_file()),None)
    if not root:
        print('ERROR: Run from the ORBIT GitHub workspace root (or original/orbit-solana-launchpad).',file=sys.stderr)
        return 2
    try:
        files=plan_patch(root)
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 3
    tag=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=root/'.orbit-backups'/tag
    for path in files:
        dest=backup/path.relative_to(root)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,dest)
    for path,new_content in files.items():
        path.write_text(new_content)
        print('Patched:',path.relative_to(root))
    print(f'Backups: {backup}')
    print('No dependencies installed, no process restarted, no Git push performed.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
