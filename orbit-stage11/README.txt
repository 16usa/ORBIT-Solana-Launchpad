ORBIT Stage 11 — Fix for "Unexpected address lookup table"

1. Upload orbit_stage11.zip to the root of the EXISTING ORBIT Replit workspace.
2. In Replit Shell paste:

cd /home/runner/workspace
unzip -o orbit_stage11.zip -d . && python3 orbit-stage11/apply_stage11.py && python3 orbit-stage11/verify_stage11.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

No auto-restart, no Git push, no Republish, no network transaction.
Works with ZIP and direct-Shell Stage 10 variants, including line-wrapped sendRawTransaction calls. Creates a timestamped source backup.

WHAT IT DOES:
- Removes Stage 10's overly-strict "Unexpected address lookup table" error.
- Loads and resolves Solana V0 Address Lookup Tables through Devnet RPC.
- Validates instruction program/account indexes using all resolved keys.
- Retains existing program allowlist and transaction preflight checks.

WHAT IT DOES NOT DO:
- Does not make Raydium or Phantom safe or guarantee a successful launch.
- Does not circumvent Phantom blocking or warnings.
- Does not transfer SOL or create a token during installation.

Do not bypass an unsafe Phantom warning. Do not test with an account containing real assets.
