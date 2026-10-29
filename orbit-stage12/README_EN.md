# ORBIT Stage 12 — Read-only Raydium LaunchLab audit

Last verified GitHub baseline: `16usa/ORBIT-Solana-Launchpad`, commit `40470a1` (Stage 11).

## Purpose

Previous attempts passed an **unsigned Devnet RPC preflight** but Phantom rejected the actual creation transaction. This is **not proof of a Phantom bug**, nor proof that a complex LaunchLab instruction is safe. Avoid bypassing any wallet security warnings.

Stage 12 adds **Inspect Raydium launch (read-only; no wallet prompt)** to the ORBIT Create Token page, replacing the old wallet-first signing test button. It uses the same Raydium SDK launch builder with a throwaway diagnostic mint and URI, but it **does not request any wallet signature, send a transaction, upload metadata, register a token or change balances**.

The report includes: Devnet genesis hash, test-SOL balance, transaction size, signer roles, Address Lookup Table count, all invoked program IDs and whether their accounts are executable, program allowlist anomalies, fee estimate, RPC simulation result and log excerpt, and approximate payer-balance impact when supplied by the RPC. This helps compare what the local RPC sees with what Phantom displays. The report explicitly warns that `sigVerify:false` does not validate any signature.

**No change** is made to `launchToken()` or the trading logic. This patch is a diagnostic aid, not a claim that token creation is fixed.

## Installation (Replit Shell only)

Upload `orbit_stage12.zip` at the workspace root, then:

```bash
cd /home/runner/workspace
unzip -o orbit_stage12.zip -d . && python3 orbit-stage12/apply_stage12.py && python3 orbit-stage12/verify_stage12.py && pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build
```

No process restart, Git push, deployment, or browser action is performed by installer. Development Workflow can be manually refreshed; **do not Republish**.

## Safe next step

Use a **dedicated disposable Devnet wallet**. Open ORBIT in Phantom's in-app browser and press **Inspect Raydium launch (read-only; no wallet prompt)**. No Phantom popup should appear. Copy or screenshot the resulting diagnostics. Do not press Create Token while Phantom continues to show red transaction warnings. Never use **Confirm (unsafe)** to work around this problem.
