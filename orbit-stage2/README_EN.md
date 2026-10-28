# ORBIT — Stage 2 / Devnet launch preflight and pool lifecycle

This patch applies to the **existing** `16usa/ORBIT-Solana-Launchpad` project **after** the previous Devnet hardening patch. It is not a standalone app or a deployable replacement.

## Installation — Replit Shell only

1. Upload `orbit_stage2.zip` to `/home/runner/workspace` in the **ORBIT** Replit project.
2. Open Replit Shell, run:

```sh
cd /home/runner/workspace
unzip -o orbit_stage2.zip -d .
python3 orbit-stage2/apply_stage2.py
pnpm --filter @workspace/orbit-launchpad run test
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

The installer creates a timestamped backup under `artifacts/orbit-launchpad/original/orbit-solana-launchpad/.orbit-backups/` before any changes. It edits only five known ORBIT files and **does not** install dependencies, run/kill/restart processes, deploy, or commit/push to GitHub. If source code differs from the expected revision or the patch was already applied, it exits without modifying files.

## Changes

- `GET /api/network-status`: non-cached readiness check against the configured Solana RPC plus the allowlisted Raydium program's executable account (no wallet signing).
- The Create Token page has an explicit Devnet connectivity check, then verifies that the specified LaunchLab config exists, belongs to the Raydium program, and quotes in SOL **before uploading metadata or asking the wallet to sign**.
- Supports optional `VITE_RAYDIUM_LAUNCH_CONFIG_ID` when the default derived config is absent. Set only to a config you have independently verified. Never invent this address.
- In the trade screen, route selection follows the live bonding-curve state: funding (0), waiting for migration (1), migrated (2). No manual route bypass and no curve submission for graduated tokens.
- Before buy/sell, checks canonical pool PDA, program, mint pair, quote decimals, configuration owner, and status using live RPC data.
- The selected token's on-chain pool state can be refreshed even if it is beyond the first 15 tokens. Graduated tokens don't claim to have a current bonding-curve quote.
- One additional offline test for safe behavior when the program ID is invalid.

## Verification and limitations

Offline checks in the authoring environment: 19/19 Node tests passed and TypeScript/TSX syntax check passed. The full TypeScript typecheck and Vite production build need the installed Replit workspace dependencies and must be rerun in Shell. **No actual on-chain launch or signed buy/sell has been executed by this patch.** Devnet RPC / LaunchLab config availability and Phantom wallet transactions must be verified before claiming live trading works.

Mainnet trading remains disabled under the Stage 1 safeguards. Files and metadata are still stored locally; they are not durable enough for mainnet launches. No smart contract was deployed and no assets were moved.

## If the site does not reflect changes

The patch never restarts processes. After tests pass, restart ORBIT **manually** in Replit and revisit the Create Token page. Check the `Check Devnet connection` button for actual RPC and config status.
