ORBIT Stage 17: Canonical LEGACY wallet transaction comparison

Background
- Stage 16 found 2 bounded ComputeBudget instructions inserted by Phantom.
- However Stage 16 compared raw instruction isWritable/isSigner flags, which
  might differ after wallets deserialize/rebuild Solana legacy transactions.
- Stage 17 reconstructs an expected *serialized transaction message* from
  the original pre-wallet Raydium instruction plus those exact wallet-added
  ComputeBudget instructions and compares with the signed returned message
  byte-for-byte. No changes are accepted unless the canonical messages match.
- Logs separate evidence for program, account addresses, data, and raw flags.
- Both signatures must still verify, before and after co-signing the test mint.
- No transaction is broadcast, no mint created, no SOL spent.

INSTALL: upload this ZIP to Replit workspace and run:
cd /home/runner/workspace
unzip -o orbit_stage17.zip -d . && python3 orbit-stage17/apply_stage17.py && python3 orbit-stage17/verify_stage17.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

After install: manually reload development site. Press Test LEGACY wallet
signature (no broadcast) once. Do not approve red/unsafe Phantom warnings.
Do not click Create token yet. No automatic restart, push or Republish.

NOTE: Success is only a no-broadcast signing proof. It does not establish that
live token creation is safe or functional. Do not enable mainnet.
