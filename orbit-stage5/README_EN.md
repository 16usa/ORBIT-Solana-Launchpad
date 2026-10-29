# ORBIT Stage 5 — Devnet launch diagnostics

**Purpose:** When Phantom reports `Unexpected error` during token creation, show the exact processing step and available SDK/RPC error details directly on the Create Token screen. This is **diagnostic only**: it does not promise to fix the underlying transaction issue or send a transaction.

## Install via Replit Shell

Upload `orbit_stage5.zip` to the workspace and run:

```sh
cd /home/runner/workspace
unzip -o orbit_stage5.zip -d .
python3 orbit-stage5/apply_stage5.py
pnpm --filter @workspace/orbit-launchpad run check:syntax
pnpm --filter @workspace/orbit-launchpad run typecheck
pnpm --filter @workspace/orbit-launchpad run build
```

Manually refresh the development preview. Do **not** republish production yet. Before retrying token creation, check Phantom Devnet activity for any previous successful launch. If a new attempt fails, take a screenshot of **Launch diagnostics** (redact wallet details if desired). Never share seed phrases, private keys or signing credentials.

The installer backs up `App.tsx`. It does not restart processes, deploy, push commits, create tokens or invoke wallets. An unchanged or different version of ORBIT fails closed.
