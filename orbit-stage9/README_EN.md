# ORBIT Stage 9 — wallet-first multi-signer signature diagnostic

The previous Stage 8 test showed that a simple unsigned V0 transaction was signed by Phantom, but the Raydium transaction (after locally signing with the new mint keypair) failed with `WalletSignTransactionError: Unexpected error`. One plausible cause is that certain mobile Phantom providers reject partially-signed transactions. This is **a hypothesis**, not yet a proven root cause.

Stage 9 keeps the real creation path unchanged. It modifies the Raydium no-broadcast diagnostic to:

1. Build the same SDK Devnet launch transaction, with an ephemeral test mint.
2. Create an **unsigned copy** of the message (with zero signer slots).
3. Confirm it has the expected wallet and mint signers, is within Solana's transaction size limit, and simulates correctly.
4. Ask Phantom to sign this unsigned transaction.
5. If successful, add the mint keypair signature **after** the wallet's signature and verify that the wallet signature was preserved.
6. Never broadcast or register a launch, upload metadata, or create any token.

If the test **passes**, wallet-first co-signing is a viable direction for fixing live launch execution. The user must **not** assume the live `Create Token` button is fixed: Stage 9 intentionally does not change that path.

If the test **fails**, both simple signing and wallet-first multi-signer signing behave differently. The diagnostic will show the required signer count, transaction size, and whether the SDK had already signed the transaction. Investigate Phantom transaction support / instruction warnings, wallet adapter version and SDK before attempting another launch. Do not automatically retry.

## Install (Replit Shell only)

Upload `orbit_stage9.zip` to the existing ORBIT workspace, then run:

```bash
cd /home/runner/workspace
unzip -o orbit_stage9.zip -d . && \
python3 orbit-stage9/apply_stage9.py && \
python3 orbit-stage9/verify_stage9.py && \
pnpm --filter @workspace/orbit-launchpad run test && \
pnpm --filter @workspace/orbit-launchpad run check:syntax && \
pnpm --filter @workspace/orbit-launchpad run typecheck && \
pnpm --filter @workspace/orbit-launchpad run build
```

Manually reload the ORBIT Development site; if changes are not live, manually restart the Dev Workflow. Use only **Test Raydium wallet-first signature (no broadcast)**. Do **not** press the live Create Token button until transaction signing is fixed.

No Republish, no Git push, no process kill/restart, no mainnet transactions.
