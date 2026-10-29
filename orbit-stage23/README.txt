ORBIT STAGE 23 — SAFARI LIVE BRIDGE (DEVNET ONLY)

Purpose
  Sign a Live challenge in the Phantom in-app browser. ORBIT issues a
  time-limited, single-use Safari handoff link. Paste it into real Safari,
  redeem it, and tap Start camera & microphone. LiveKit media is requested
  only from Safari. No wallet private keys or LiveKit API secrets are put in
  the link. The URL contains a bearer code: treat it as sensitive and never
  share it publicly. It expires after five minutes or first redemption.

Install with Replit Shell (not Agent):
  cd /home/runner/workspace
  unzip -o orbit_stage23_safari.zip -d .
  python3 orbit-stage23/apply_stage23.py
  pnpm --filter @workspace/orbit-launchpad run test
  pnpm --filter @workspace/orbit-launchpad run check:syntax
  pnpm --filter @workspace/orbit-launchpad run typecheck
  pnpm --filter @workspace/orbit-launchpad run build

Expected real-device check:
  1. In Phantom, connect wallet and enter ORBIT -> Live -> stream title.
  2. Tap Go live, approve signMessage only (no SOL transaction).
  3. Tap Copy Safari link; open actual Safari and paste the link.
  4. Tap Open studio in Safari, then Start camera & microphone.
  5. Grant both permissions and confirm actual local video appears.
  6. On a second device, check Live now, join as viewer, verify video/audio.
  7. End stream, verify it disappears from listing.

Operational limits
  - API and frontend must run on the same stable HTTPS origin in both browsers.
  - Needs working LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET on API server.
  - The URL does not automatically launch external Safari from Phantom: iOS
    browser choices vary. Manually paste the link into Safari.
  - Single-instance server in-memory registry. Restart voids handoff links;
    scaling across multiple instances needs shared session storage.
  - No recording, long-term moderation, or production readiness provided.
  - Do not use mainnet funds. Do not store LIVEKIT_API_SECRET in frontend.
  - Rotate the previously exposed LiveKit API secret in LiveKit console.

No command in this patch restarts, kills, publishes or pushes a process/repo.
