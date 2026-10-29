#!/usr/bin/env python3
"""Static installer verification for the ORBIT Stage 21 three-dot menu."""
import os
from pathlib import Path

root = Path(os.environ.get('ORBIT_WORKSPACE', '/home/runner/workspace'))
src = root / 'artifacts/orbit-launchpad/original/orbit-solana-launchpad/web/src'
app = (src / 'App.tsx').read_text(encoding='utf-8')
css = (src / 'styles.css').read_text(encoding='utf-8')
marker='ORBIT_STAGE21_MENU_POPUP'
assert app.count(marker)==1, 'menu component missing or repeated'
assert css.count(marker)==1, 'menu styles missing or repeated'
assert 'role="menu"' in app and 'role="menuitem"' in app, 'menu accessibility missing'
assert "const onOutside=(event:PointerEvent)" in app, 'outside click close missing'
assert "if(event.key==='Escape')" in app, 'Escape close missing'
assert "if(h==='menu')return {page:'discover',mint:''};" in app, 'legacy route not redirected'
assert "{route.page==='menu'&&<MenuPage/>}" not in app, 'old full menu page still rendered'
assert '.bottom-nav .orbit-more-popup button span' in css, 'mobile menu label visibility missing'
assert "{page:'leaderboard',title:'Leaderboard'" in app, 'navigation destinations missing'
print('STAGE 21 VERIFIED: floating three-dot menu; existing routes preserved.')
