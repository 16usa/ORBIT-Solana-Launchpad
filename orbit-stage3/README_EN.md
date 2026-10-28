# ORBIT Stage 3 — Devnet production configuration and mobile wallet fallback

Applies to your existing **ORBIT** Replit workspace only. This is not a new site.

## Changes

- Sets **non-secret** API production environment variables in `artifacts/api-server/.replit-artifact/artifact.toml`: `SOLANA_CLUSTER=devnet`, `RPC_URL`, `VITE_RPC_URL`, `RAYDIUM_PROGRAM_ID`, `PUBLIC_BASE_URL=https://orbit-solana-launchpad.replit.app`, and `ENABLE_MAINNET_TRADING=false`.
- Fixes the blank mobile wallet-picker experience: when no Solana wallet is detected, the wallet button directs the user to ORBIT inside Phantom's in-app browser. A normal wallet selector remains when compatible wallets are actually detected.
- Adds explanatory wallet guidance to account and trading panels; no seed phrases, private key requests, simulated wallet sessions, or automatic signatures.
- Includes offline regression checks for Stage 3 deployment settings, mobile wallet deep-link target, and unchanged Devnet restrictions.

## Install via Replit Shell (only)

Unzip `orbit_stage3.zip` at the workspace root and run:

```sh
cd /home/runner/workspace
unzip -o orbit_stage3.zip -d .
python3 orbit-stage3/apply_stage3.py
python3 orbit-stage3/verify_stage3.py
node orbit-stage3/test_config.mjs
pnpm --filter @workspace/orbit-launchpad run test
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

The installer **does not restart or stop processes, run package installation, git push, or publish**. It creates a backup under `.orbit-backups/stage3-*` and only changes specific ORBIT files. If any check fails, **do not publish**; inspect the error.

## IMPORTANT: make the production config live

Replit's published deployment has a separate process/environment. After successful tests, **manually publish/redeploy ORBIT** in Replit. Building the source alone does not change the existing `.replit.app` deployment.

Verify the live production settings *after* publication:

```sh
curl -fsS https://orbit-solana-launchpad.replit.app/api/config
curl -fsS https://orbit-solana-launchpad.replit.app/api/network-status
```

`/api/config` should show `network: devnet`, `publicBase: https://orbit-solana-launchpad.replit.app` and `raydiumProgramAllowlisted: true`. An RPC error or missing on-chain LaunchLab configuration will still block launch; test inside Phantom on Devnet. **No real token creation, buy, or sell has been verified by this patch.**

## Safety / limitations

- API and images are still saved on Replit's **ephemeral filesystem**. Token metadata may disappear after a redeploy. **Do not use this version for mainnet or valuable tokens.** Permanent storage and independent security audit are required before launch.
- If Replit Publishing has manually configured environment values/secrets that override files, update those through Publishing settings; the script does not read or modify them.
- `RAYDIUM_PROGRAM_ID` is the previously used Devnet value. The code checks on-chain readiness separately; inclusion in configuration does **not** prove the program/configuration can execute token launches.
- The Phantom browse deep link requires the user to click. If deep linking does not work, open the site URL directly in Phantom's in-app browser.
- This patch does not make the empty Explore list populate automatically or enable livestreams, historical candles or mainnet trading.
