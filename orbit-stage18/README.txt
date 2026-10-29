ORBIT Stage 18 — DEVNET LEGACY LIVE LAUNCH

Stage 17 passed wallet-first signature validation on a LEGACY Raydium launch.
Stage 18 replaces ONLY launchToken() with a Devnet-only Legacy signing and broadcasting path, using the same strict Stage 17 canonical message comparison.
- Check exact official Devnet genesis hash.
- Build real token metadata transaction through Raydium SDK (Legacy, no ALT).
- Validate program allowlist, signer identities, transaction size, original unsigned simulation.
- Get wallet approval; allow ONLY unchanged transaction or exactly two bounded ComputeBudget prefixes with byte-exact reconstructed Raydium message.
- Verify Phantom signature, then co-sign mint and verify both signatures.
- Send ONCE through RPC with preflight enabled; confirm by signature.
- Keep previous code for all other pages and diagnostics.

THIS IS A REAL DEVNET ON-CHAIN LAUNCH. Clicking Create Token can spend approximately 0.02 Devnet SOL and create an actual Devnet mint. Use only a separately created TEST account with no real mainnet assets. Never bypass any Phantom safety warning. Do NOT click Create Token until you have reviewed the code, test outcome and wallet's network.

HOW TO INSTALL VIA REPLIT SHELL:
cd /home/runner/workspace
unzip -o orbit_stage18.zip -d . && python3 orbit-stage18/apply_stage18.py && python3 orbit-stage18/verify_stage18.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

Does NOT restart/kill any process; does NOT push GitHub; does NOT Republish.
