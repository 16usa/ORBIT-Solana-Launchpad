#!/usr/bin/env python3
"""ORBIT Stage 11: resolve expected V0 ALT accounts before program validation.

Edits web/src/chain.ts only. No network requests, transaction sending,
process restarts, Git actions, or publishing. Fails closed on unknown source.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import sys

ROOT = Path.cwd() / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad'
CHAIN = ROOT / 'web/src/chain.ts'
MARK = 'ORBIT_STAGE11_ALT_RESOLUTION'
BEGIN = 'export async function launchToken('
END = 'export async function curveTrade('

# Stage 10 came from either ZIP or the later direct-Shell installer.
ALT_GUARD = re.compile(
    r'(?m)^[ \t]*if\([^\r\n]*addressTableLookups\.length\)[ \t]*\r?\n'
    r'[ \t]*throw new Error\([^\r\n]*\);[ \t]*\r?\n'
)
MESSAGE_DECL = re.compile(r'(?m)^[ \t]*const message=(?:original\.message|tx\.message as MessageV0);[ \t]*$')

ALT_BLOCK = '''
 // ORBIT_STAGE11_ALT_RESOLUTION
 // Solana V0 Address Lookup Tables are valid. Resolve every referenced table
 // on the same Devnet RPC, then validate programs using ALL resolved keys.
 // Missing tables or program IDs not on the existing allowlist fail closed.
 const lookupTables=await Promise.all(
  message.addressTableLookups.map(async lookup=>{
   const result=await connection.getAddressLookupTable(
    lookup.accountKey,{commitment:'confirmed'}
   );
   if(!result.value)
    throw new Error('Missing Devnet address lookup table: '+lookup.accountKey.toBase58());
   return result.value;
  })
 );
 const resolvedKeys=message.getAccountKeys({addressLookupTableAccounts:lookupTables});
 for(const ix of message.compiledInstructions){
  if(!resolvedKeys.get(ix.programIdIndex) ||
     ix.accountKeyIndexes.some(i=>!resolvedKeys.get(i)))
   throw new Error('Unresolved Devnet transaction account index; launch blocked');
 }
'''


def prepare(source: str) -> str:
    if source.count(MARK) == 1:
        print('STAGE 11 ALREADY INSTALLED: no file changed')
        return source
    if MARK in source:
        raise ValueError('Partial or duplicate Stage 11 marker. No changes.')
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError('Unexpected ORBIT source layout; no changes.')
    a = source.index(BEGIN)
    b = source.index(END, a)
    before, section, after = source[:a], source[a:b], source[b:]
    if 'ORBIT_STAGE10_VERIFIED_DEVNET_LAUNCH' not in (before[-1500:] + section):
        raise ValueError('Stage 10 is required; refusing to modify another launch implementation.')

    guards = list(ALT_GUARD.finditer(section))
    if len(guards) != 1:
        raise ValueError(f'Expected one Stage 10 ALT guard, found {len(guards)}. No changes.')
    old = guards[0].group(0)
    if 'lookup' not in old.lower() or 'Unexpected' not in old:
        raise ValueError('Unrecognized ALT guard; no changes.')
    section = section[:guards[0].start()] + section[guards[0].end():]

    declarations = list(MESSAGE_DECL.finditer(section))
    if len(declarations) != 1:
        raise ValueError(f'Expected one Stage 10 message declaration, found {len(declarations)}.')
    idx = declarations[0].end()
    section = section[:idx] + ALT_BLOCK + section[idx:]

    # Validation from two Stage 10 implementations:
    # A: const programs = compiledInstructions.map(ix=>keys[ix.programIdIndex]...)
    # B: const called = compiledInstructions.map(ix=>{const key=message.staticAccountKeys[...]...})
    keyref = 'keys[ix.programIdIndex]'
    staticref = 'message.staticAccountKeys[ix.programIdIndex]'
    count_a = section.count(keyref)
    count_b = section.count(staticref)
    if (count_a, count_b) == (1, 0):
        section = section.replace(keyref, 'resolvedKeys.get(ix.programIdIndex)', 1)
    elif (count_a, count_b) == (0, 1):
        section = section.replace(staticref, 'resolvedKeys.get(ix.programIdIndex)', 1)
    else:
        raise ValueError(f'Program allowlist key resolver differs ({count_a},{count_b}); no changes.')

    # Keep the Stage 10 program ID allowlist intact, along with simulation,
    # wallet-signature checks, and explicit no-unsafe-wallet-warning behavior.
    for required in [
        'message.compiledInstructions',
        'simulateTransaction(tx',
        'wallet.signTransaction(tx)',
        'skipPreflight:false',
        "config.network!=='devnet'",
        'resolvedKeys.get(ix.programIdIndex)',
        'ORBIT_STAGE11_ALT_RESOLUTION',
    ]:
        if required not in section:
            raise ValueError(f'Stage 10 safety check missing: {required}. No changes.')
    # Stage 10 exists in multiple formatting variants. In the direct-Shell
    # variant, `signed.serialize()` starts on the NEXT line, so a literal
    # substring test incorrectly rejected an otherwise valid safety guard.
    if not re.search(
        r'\bconnection\s*\.\s*sendRawTransaction\s*\(\s*'
        r'signed\s*\.\s*serialize\s*\(\s*\)', section,
    ):
        raise ValueError('Stage 10 signed-transaction send path missing; no changes.')
    if section.index('getAddressLookupTable(') > section.index('wallet.signTransaction(tx)'):
        raise ValueError('ALT resolution must precede wallet signing.')
    if 'Unexpected address lookup table' in section or 'Unexpected lookup table in launch' in section:
        raise ValueError('Old lookup-table rejection remains; no changes.')
    updated = before + section + after
    if updated.count(MARK) != 1:
        raise ValueError('Unexpected marker count after patch; no changes.')
    return updated


def main() -> None:
    if not CHAIN.is_file():
        raise FileNotFoundError('ORBIT web/src/chain.ts missing. Run inside /home/runner/workspace.')
    original = CHAIN.read_text(encoding='utf-8')
    changed = prepare(original)
    if changed == original:
        return
    backupdir = ROOT / '.orbit-backups'
    backupdir.mkdir(exist_ok=True)
    backup = backupdir / ('chain-before-stage11-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.ts')
    if backup.exists():
        raise FileExistsError(f'Backup exists: {backup}; refusing to overwrite.')
    shutil.copy2(CHAIN, backup)
    CHAIN.write_text(changed, encoding='utf-8')
    print('STAGE 11 INSTALLED')
    print('Backup:', backup)
    print('The old ALT rejection is removed from launchToken().')
    print('No transactions, restarts, Git pushes, or Republish performed.')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('STAGE 11 STOPPED:', error, file=sys.stderr)
        sys.exit(1)
