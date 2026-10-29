ORBIT Stage 16 — Phantom auto-added priority fee verification (no broadcast)

Stage 15 proves Phantom inserts two ComputeBudget instructions before a Raydium launch instruction.
Phantom documents this behavior at https://github.com/phantom/docs/blob/master/development-powertools/solana-priority-fees.md

Stage 16 verifies the two extras are exactly SetComputeUnitPrice and SetComputeUnitLimit, with no account keys, acceptable capped values, and an unmodified Raydium instruction, payer, blockhash, signer layout. It validates the wallet signature, adds the disposable diagnostic mint signature, and verifies both locally. It NEVER transmits this diagnostic transaction. All other differences stop.

No changes to the live Create Token code. Does not solve mobile V0 signing. Do not bypass Phantom security warnings. Test on Devnet with a separate empty wallet.

Install in Replit workspace Shell:
cd /home/runner/workspace
unzip -o orbit_stage16.zip -d . && python3 orbit-stage16/apply_stage16.py && python3 orbit-stage16/verify_stage16.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

Then reload Development (no Republish) and press Test LEGACY wallet signature (no broadcast).
