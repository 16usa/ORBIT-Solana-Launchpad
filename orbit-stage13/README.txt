ORBIT Stage 13: compare legacy-format LaunchLab launch with V0 transaction.
NO blockchain submissions, NO wallet signature requests, NO changes to token creation.
Use only for the existing ORBIT Stage 12 Replit workspace.

Install in Replit Shell from /home/runner/workspace:
  unzip -o orbit_stage13.zip -d .
  python3 orbit-stage13/apply_stage13.py
  python3 orbit-stage13/verify_stage13.py
  pnpm --filter @workspace/orbit-launchpad run test
  pnpm --filter @workspace/orbit-launchpad run typecheck
  pnpm --filter @workspace/orbit-launchpad run build

Then refresh Development and click:
  Inspect LEGACY launch (read-only; no wallet prompt)

If message reports LEGACY too large, do not switch launch to legacy. If sim passes, this
only establishes that a legacy-format launch might be worth testing; do not bypass
Phantom risk warnings or click Create Token based on simulation alone.
