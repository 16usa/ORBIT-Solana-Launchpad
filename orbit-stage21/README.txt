ORBIT STAGE 21 — THREE-DOT POPUP MENU

Changes only web/src/App.tsx and web/src/styles.css.
The bottom-right three dots open a dark, floating popup (similar to the supplied
Pump.fun mobile navigation reference), rather than navigating to a Menu page.
The current page stays visible. Only existing ORBIT destinations are included:
Explore tokens, Leaderboard, Live, Rewards, and Create token.

The popup closes on outside tap, Escape, another bottom-nav tap, or navigation.
Old #/menu links now resolve to Explore. Desktop navigation remains supported.

INSTALL FROM REPLIT SHELL (NO REPLIT AGENT):
  cd /home/runner/workspace
  unzip -o orbit_stage21_menu_popup.zip -d .
  python3 orbit-stage21/apply.py
  python3 orbit-stage21/verify.py
  pnpm --filter @workspace/orbit-launchpad run test
  pnpm --filter @workspace/orbit-launchpad run check:syntax
  pnpm --filter @workspace/orbit-launchpad run typecheck
  pnpm --filter @workspace/orbit-launchpad run build

Do not republish; check on Development URL first.
Installer creates backups in .orbit-backups/stage21-popup-menu-*/.
Safe to apply twice; no automatic restarts, GitHub push or blockchain actions.
