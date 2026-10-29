ORBIT: fix published LiveKit streaming backend "Cannot find package 'livekit-server-sdk'".

Install with Replit Shell (upload the ZIP to /home/runner/workspace first):
  cd /home/runner/workspace
  unzip -o orbit_livekit_sdk_fix.zip -d .
  python3 orbit-livekit-sdk-fix/apply.py

Patch makes the LiveKit SDK a runtime dependency of artifacts/api-server/package.json;
updates pnpm-lock.yaml through pnpm install; verifies SDK import from API artifact.
No process restart, no GitHub push, and no republishing occurs automatically.

This is distinct from the Phantom iPhone camera/microphone permission issue.
Published orbit-solana-launchpad.replit.app uses a separate deployment:
after installation and verification, the ORBIT API artifact needs a Republish.

Security: Any LiveKit API secret exposed in a screenshot should be revoked/rotated
in LiveKit Cloud and updated only in server-side Replit Secrets (not frontend).
