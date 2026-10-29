ORBIT STAGE 22 -- ACTUAL LIVE VIDEO STREAMING (DEVELOPMENT MVP)

WHAT THIS INSTALLS
- Real camera + microphone streaming via LiveKit/WebRTC, not simulated video.
- Sign a nonce with Solana Phantom wallet to start a broadcast; only verified wallet may issue a publisher token.
- Public watch-only tokens; viewers cannot publish.
- Live listing with a heartbeat, stream sharing and ending, basic report capture.
- Mobile-friendly streaming UI. Works on suitable HTTPS mobile browsers with camera/mic permissions.
- Does not touch the token launch, buy/sell trading system or live menu popup.
- No background servers, GitHub push, or Republish.

REQUIRED EXTERNAL SERVICE
1. Create a LiveKit Cloud project at https://cloud.livekit.io/ (or provide your own LiveKit media server).
2. In Replit SECRETS for the running ORBIT API service, set:
   LIVEKIT_URL=wss://<YOUR-PROJECT>.livekit.cloud
   LIVEKIT_API_KEY=<KEY>
   LIVEKIT_API_SECRET=<SECRET>
3. Keep LIVEKIT_API_SECRET entirely on the server. Never use VITE_ prefix and never commit it.
4. Manually restart the ORBIT API service after setting these environment variables.
5. Ensure the Replit Vite proxy /api is routed to that API service (previously API_PORT 8080).
6. Use HTTPS for the frontend, allow camera/microphone permissions in mobile browser.

INSTALL (upload orbit_stage22_live.zip to /home/runner/workspace)
 cd /home/runner/workspace
 unzip -o orbit_stage22_live.zip -d .
 python3 orbit-stage22/apply.py
 python3 orbit-stage22/verify.py
 pnpm --filter @workspace/orbit-launchpad add livekit-client@2.23.0 livekit-server-sdk@2.19.2
 pnpm --filter @workspace/orbit-launchpad run test
 pnpm --filter @workspace/orbit-launchpad run check:syntax
 pnpm --filter @workspace/orbit-launchpad run typecheck
 pnpm --filter @workspace/orbit-launchpad run build

TEST
- On Development open Live (via the three-dot menu).
- With Phantom connected, enter stream title and tap Go live. Sign MESSAGE, NOT SOL TRANSACTION.
- When camera/mic permissions are granted and connected, stream appears under Live now.
- From a second phone/browser, open the stream and tap Enable sound.
- Try leaving and ending; ensure room disappears within ~80 seconds on crash.
- Ensure live purchase/create actions remain unchanged. Do not republish yet.

LIMITS -- NOT PRODUCTION READY
- Streaming requires configured, externally hosted LiveKit media server and may incur provider charges.
- Sessions are in-memory on one API instance; server restarts end listings, and multi-replica scaling requires shared persistent storage.
- 10 simultaneous broadcasters maximum, 120 participants per room maximum; service plan can restrict more.
- Non-persistent, read-only video; no recordings, chats or replays.
- A report is logged in data/live-reports.json but there is NO active moderation dashboard, abuse removal or automated content review.
- Do NOT open public live streaming to general users without moderation, takedown, content and reporting policies, service rate limits, and legal/privacy review.
- This is a Devnet/development MVP. Publishing requires additional infrastructure and testing.
- Data about crypto wallets is public, but signMessage does NOT authorize any SOL transfer.
