# ORBIT Stage 4 — Devnet PlatformConfig preflight

## The exact error

The Raydium SDK uses `4Bu96XjU84XjPDSpveTVf6LYGCkfW5FK7SNkREWcEfV4` as a default PlatformConfig for **mainnet**. It may not exist on **Devnet**. This results in `platform id not found` even when the Solana RPC, LaunchLab program and `GlobalConfig` work correctly. Raydium's public SDK issue #112 describes the same failure.

## What this patch changes

- Checks for a Devnet **PlatformConfig** before image/metadata upload or transaction building.
- Uses `VITE_RAYDIUM_PLATFORM_ID` if set, but validates the account actually exists, is owned by the Devnet LaunchLab program, and decodes as `PlatformConfig`.
- When the Vite variable is absent, uses **`DEVNET_PROGRAM_ID.LAUNCHPAD_PLATFORM`** exported by the installed Raydium SDK, as recommended in Raydium SDK issue #112. It validates the account exists on Devnet and is owned by the Devnet LaunchLab program.
- Passes that verified platform ID explicitly to `createLaunchpad`, instead of letting the SDK silently fall back to a mainnet-only default.
- If no platform config exists, gives a clear error with the attempted Devnet platform address. This patch **does not create the platform account** or falsely claim that minting is ready.
- Does not change backend environment variables, transfer any SOL, enable Mainnet, or republish.

## Installation (Replit Shell only)

Upload `orbit_stage4.zip` to the existing ORBIT workspace, then:

```bash
cd /home/runner/workspace
unzip -o orbit_stage4.zip -d .
python3 orbit-stage4/apply_stage4.py
python3 orbit-stage4/verify_stage4.py
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run test
pnpm --filter @workspace/orbit-launchpad run build
```

No background process is restarted, no git commit/push and no deployment occurs. **Test using the Dev URL only.** You may need to manually refresh the Dev page for updated frontend code.

## Next step if the Raydium Devnet PlatformConfig is unavailable

A PlatformConfig must exist on Devnet. If the SDK-provided Devnet address is unavailable, configure a verified alternative Devnet PlatformConfig. Creating a new one requires a separate Raydium `createPlatformConfig` instruction using a connected wallet, a valid Devnet CPMM config, and explicit fee/migration settings. This is a **separate user-approved transaction**. It is not safe to invent another party's platform address or reuse the default mainnet address. We should verify these on-chain parameters before providing the creation step.

Mainnet remains disabled and temporary metadata storage is not suitable for real-money launches.
