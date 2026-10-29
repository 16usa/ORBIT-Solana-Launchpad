ORBIT Stage 14 — LEGACY wallet signing without broadcast

Purpose: Stage 13 proved a 855-byte Raydium LEGACY launch could be built and simulated without using address lookup tables. Stage 14 tests whether Phantom will sign that LEGACY message, without creating a token or broadcasting it.

Install in the existing Replit ORBIT workspace through Shell, manually:
cd /home/runner/workspace
unzip -o orbit_stage14.zip -d . && python3 orbit-stage14/apply_stage14.py && python3 orbit-stage14/verify_stage14.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

The installer changes only web/src/chain.ts and web/src/App.tsx. It creates backups. It does not restart, republish, push, invoke a wallet, or send blockchain transactions.

After installing, manually refresh Development in the Phantom browser. On Create Token choose "Test LEGACY wallet signature (no broadcast)" using a SEPARATE test-only Devnet wallet. This deliberately prompts a signature but NEVER broadcasts. If Phantom displays a malicious/simulation warning, DO NOT override it; close the prompt. Neither a passed signature nor an unsigned simulation proves that a real launch is safe. Mainnet remains disabled; original Create Token remains unchanged.
