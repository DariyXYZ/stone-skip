import os, re

BASE  = r"C:\VS Code\workfiles\Rock Skipping"
COVER = os.path.join(BASE, "cover_ascii.txt")
TITLE = os.path.join(BASE, "title_ascii.txt")
SRC   = r"C:\VS Code\workfiles\Rock Skipping\stone_game.html"
OUT   = r"C:\VS Code\workfiles\Rock Skipping\stone_game.html"
COLS  = 220

with open(COVER, encoding='utf-8') as f:
    cover_lines = f.read().splitlines()
with open(TITLE, encoding='utf-8') as f:
    title_lines = f.read().splitlines()

illus = [ln.ljust(COLS) for ln in cover_lines[:64]]
title = [ln.ljust(COLS) for ln in title_lines]

def jsesc(lines):
    return '\n'.join(l.replace('\\','\\\\').replace('`','\\`') for l in lines)

illus_js = jsesc(illus)
title_js = jsesc(title)

with open(SRC, encoding='utf-8') as f:
    html = f.read()

# 1. Defer game start: replace bare requestAnimationFrame(frame) at end with startGame()
html = re.sub(
    r'(// ── Init[^\n]*\n(?:.*\n)*?)'  # keep the init block header
    r'(requestAnimationFrame\(frame\);)',
    lambda m: m.group(1) + 'function startGame() { requestAnimationFrame(frame); }',
    html
)

# 2. Inject splash CSS before </style>
SPLASH_CSS = """
/* ── Splash overlay ─────────────────────────────────────────────────── */
#splash {
  position:fixed; inset:0; z-index:200; background:#000;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
}
#sp-stage, #sp-title {
  font-family:'Courier New',Courier,monospace;
  font-size:min(0.833vw,0.95vh);
  line-height:1.15; white-space:pre; letter-spacing:0;
  width:220ch; flex-shrink:0;
}
#sp-stage { color:#aaa; }
#sp-stage .spln { display:block; opacity:0; transition:opacity .06s linear; }
#sp-stage .spln.on { opacity:1; }
#sp-title { color:#fff; margin-top:.45em; opacity:0; transition:opacity .9s ease; }
#sp-title.on { opacity:1; }
#sp-prompt {
  font-family:'Courier New',monospace;
  font-size:min(0.7vw,1.1vh); color:#333; letter-spacing:4px;
  opacity:0; transition:opacity .8s; white-space:nowrap;
  margin-top:.7em; flex-shrink:0;
}
#sp-prompt.on { opacity:1; }
#sp-prompt span { animation:spblink 1.4s step-end infinite; }
@keyframes spblink { 50%{opacity:0} }
"""
html = html.replace('</style>', SPLASH_CSS + '</style>', 1)

# 3. Inject splash HTML before </body>
SPLASH_HTML = f"""
<div id="splash">
  <pre id="sp-stage"></pre>
  <pre id="sp-title">{title_js}</pre>
  <div id="sp-prompt"><span>·</span> press any key <span>·</span></div>
</div>
"""
html = html.replace('</body>', SPLASH_HTML + '</body>', 1)

# 4. Inject splash JS before </script></body>
SPLASH_JS = f"""
// ── Splash ────────────────────────────────────────────────────────────
(function() {{
  const SP_ILLUS = `{illus_js}`;
  const spStage  = document.getElementById('sp-stage');
  const spTitle  = document.getElementById('sp-title');
  const spPrompt = document.getElementById('sp-prompt');
  const DELAY    = 22;

  SP_ILLUS.split('\\n').forEach(ln => {{
    const el = document.createElement('span');
    el.className = 'spln';
    el.textContent = ln;
    spStage.appendChild(el);
  }});

  const spSpans = spStage.querySelectorAll('.spln');
  const spTotal = spSpans.length * DELAY;
  spSpans.forEach((el, i) => setTimeout(() => el.classList.add('on'), i * DELAY));
  setTimeout(() => spTitle.classList.add('on'), spTotal + 100);
  setTimeout(() => {{
    spPrompt.classList.add('on');
    document.addEventListener('keydown', spGo, {{once:true}});
    document.addEventListener('click',   spGo, {{once:true}});
  }}, spTotal + 900);

  function spGo() {{
    spPrompt.classList.remove('on');

    const cv  = document.createElement('canvas');
    cv.style.cssText = 'position:fixed;inset:0;z-index:300;pointer-events:none;';
    cv.width  = window.innerWidth;
    cv.height = window.innerHeight;
    document.body.appendChild(cv);
    const ctx = cv.getContext('2d');
    ctx.fillStyle = '#000';

    const SCX = cv.width  / 2, SCY = cv.height / 2;
    const fs  = parseFloat(getComputedStyle(spStage).fontSize);
    const CW  = fs * 0.601;
    const CH  = fs * 1.15;

    const cells = [];

    spStage.querySelectorAll('.spln').forEach((ln, row) => {{
      const R = spStage.getBoundingClientRect();
      const text = ln.textContent;
      for (let col = 0; col < text.length; col++) {{
        if (text[col] === ' ') continue;
        const x = R.left + col * CW, y = R.top + row * CH;
        const dx = x + CW*.5 - SCX, dy = y + CH*.5 - SCY;
        cells.push({{ x, y, dist: Math.sqrt(dx*dx+dy*dy), angle: Math.atan2(dy,dx) }});
      }}
    }});

    const tR = spTitle.getBoundingClientRect();
    spTitle.textContent.split('\\n').forEach((line, row) => {{
      for (let col = 0; col < line.length; col++) {{
        if (line[col] === ' ') continue;
        const x = tR.left + col * CW, y = tR.top + row * CH;
        const dx = x + CW*.5 - SCX, dy = y + CH*.5 - SCY;
        cells.push({{ x, y, dist: Math.sqrt(dx*dx+dy*dy), angle: Math.atan2(dy,dx) }});
      }}
    }});

    const maxR = Math.max(...cells.map(c => c.dist)) + 30;
    const gone = new Uint8Array(cells.length);
    const T0   = performance.now();
    const DUR  = 1400;

    function spFrame(ts) {{
      const p  = Math.min((ts - T0) / DUR, 1);
      const ep = 1 - Math.pow(1 - p, 3);
      const r  = ep * maxR;
      const tt = (ts - T0) / 170;
      const amp = 16 * (1 - ep * 0.6);

      for (let i = 0; i < cells.length; i++) {{
        if (gone[i]) continue;
        const c = cells[i];
        const w = Math.sin(c.angle * 7 + tt      ) * amp
                + Math.sin(c.angle * 3 - tt * 1.4) * amp * 0.35;
        if (c.dist < r + w) {{
          ctx.fillRect(c.x, c.y, CW+1, CH+1);
          gone[i] = 1;
        }}
      }}

      if (p < 1) {{
        requestAnimationFrame(spFrame);
      }} else {{
        document.getElementById('splash').style.display = 'none';
        cv.remove();
        startGame();
      }}
    }}
    requestAnimationFrame(spFrame);
  }}
}})();
"""
html = html.replace('</script>\n</body>', SPLASH_JS + '\n</script>\n</body>', 1)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"written -> {OUT}")
