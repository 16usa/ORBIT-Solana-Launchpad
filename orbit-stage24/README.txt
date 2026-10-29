ORBIT Stage 24 – Safari Live stream session lifecycle fix

THE BUG
In Stage 23, React's development StrictMode ran the LivePlayer effect cleanup
immediately after the first mount. That cleanup incorrectly POSTed /api/live/end.
The LiveKit server-side session was deleted BEFORE clicking Start camera & microphone.
The button then returned "Invalid session", as on the screenshots.
A second issue was no heartbeat until after camera permission; idle studios could
expire while iOS asked for camera/microphone access.

FIX
- A React effect cleanup disconnects the local media participant only. It NEVER
  invokes the destructive /api/live/end endpoint.
- End stream or X is still an explicit, authenticated server-side close.
- A 15s authenticated heartbeat begins as soon as Safari joins the room.
- Early heartbeat only keeps the private studio alive; it does not show "LIVE".
- After successful camera+mic publishing, one heartbeat with active:true marks
  the stream live and lets viewers join.
- A studio waiting for its initial WebRTC connection can remain pending 5 minutes.
- A disconnected active stream expires automatically after ~80 seconds without heartbeat.
- No media permissions are requested in Phantom. Safari permission remains user-triggered.

INSTALLATION IN REPLIT SHELL (after uploading orbit_stage24_live_fix.zip to /home/runner/workspace)

cd /home/runner/workspace
unzip -o orbit_stage24_live_fix.zip -d .
python3 orbit-stage24/apply_stage24.py
python3 orbit-stage24/verify_stage24.py
pnpm --filter @workspace/orbit-launchpad run test && pnpm --filter @workspace/orbit-launchpad run check:syntax && pnpm --filter @workspace/orbit-launchpad run typecheck && pnpm --filter @workspace/orbit-launchpad run build

Then RESTART THE API SERVICE MANUALLY to load server/live.mjs; restart/reload the Web Dev preview if needed.
No automatic service restart, GitHub push, Republish, or wallet transaction is performed.

TEST IN THE PHONE:
1. In Phantom, go to Dev ORBIT and request a NEW one-time Safari link.
2. Open link directly in Safari; tap Open studio in Safari ONCE.
3. Tap Start camera & microphone and approve prompts.
4. A live stream must appear in Live now; check video on a second device.
5. Tap End stream and make sure Live now count decreases.
If you see Invalid session after service restarts, obtain a new link; old server RAM state is not durable.

NOTE: Devnet MVP only. Streams held in RAM, not suitable for production without persistent sessions,
LiveKit room webhooks, abuse moderation, durable storage, and deployment integration testing.
