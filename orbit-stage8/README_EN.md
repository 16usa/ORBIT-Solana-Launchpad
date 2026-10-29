# ORBIT Stage 8 — Raydium Launch Transaction Signature Diagnostic

## Why

Stage 7 proved that Phantom can sign an ordinary Solana version-0 transaction without broadcasting. This **does not prove** that the Raydium `createLaunchpad` transaction is valid or that the Raydium SDK execution pipeline can sign it. Do not repeatedly attempt real token creation while the cause is unknown.

## New test

**Test Raydium launch signature (no broadcast)** appears on the ORBIT Create Token page, while a Devnet wallet is connected.

1. Builds a **realistic Raydium launch transaction** using the same Devnet LaunchLab config, platform, SDK and mint-signing pattern as the create flow.
2. Validates required signers, fee payer and transaction size.
3. Simulates the first transaction against Devnet; shows program errors and logs if simulation fails.
4. If simulation passes, asks Phantom to **sign the actual Raydium transaction** — then discards it.

**It never sends, executes, or registers the transaction; it creates no token and charges no network fee.** It creates an ephemeral mint locally, but does not submit it. The metadata URI is a diagnostic placeholder and is never broadcast. The check might show a Phantom approval dialog, but it does not authorize a token launch. It can test only the first transaction; any subsequent transaction depends on the first being executed.

If **the simple signature passes but the Raydium signature fails**, inspect the precise error from the Raydium transaction/signature. If **both pass but Create Token fails**, focus on the SDK `execute({sequentially:true})` flow and multi-transaction handling, while checking the wallet's Devnet activity before another real attempt.

## Install — existing Replit workspace, Shell only

Upload `orbit_stage8.zip` to ORBIT (not another project), then:

```sh
cd /home/runner/workspace
unzip -o orbit_stage8.zip -d .
python3 orbit-stage8/apply_stage8.py
python3 orbit-stage8/verify_stage8.py
pnpm --filter @workspace/orbit-launchpad run test
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

Stop on an error. The installer is safe to rerun (and preserves a `.orbit-backups/stage8-*` copy). No automatic restart, package install, Git push, Mainnet enablement, or Republish.

Refresh ORBIT Development. If the button doesn't appear, manually restart the development workflow. Click the new **Test Raydium launch signature (no broadcast)** button **once** and share the exact message in **Launch diagnostics**.

## Limitations

A passing test does not prove that real mint creation or trading will succeed, and it is not a security audit. Production deployment, permanent metadata storage, proper program authorization, wallet permissions, mainnet safety and economic correctness still need review. Mainnet token launching remains disabled.
