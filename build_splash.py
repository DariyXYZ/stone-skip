import sys, os

BASE   = r"C:\VS Code\workfiles\Rock Skipping"
COVER  = os.path.join(BASE, "cover_ascii.txt")
TITLE  = os.path.join(BASE, "title_ascii.txt")
OUT    = r"C:\VS Code\workfiles\Rock Skipping\splash.html"
COLS   = 220   # both pres must be exactly this wide

with open(COVER, encoding='utf-8') as f:
    cover_lines = f.read().splitlines()

with open(TITLE, encoding='utf-8') as f:
    title_lines = f.read().splitlines()

# Illustration: lines 0..63, pad every line to exactly COLS chars
illus = [ln.ljust(COLS) for ln in cover_lines[:64]]

# Title: pad every line to COLS as well
title_lines = [ln.ljust(COLS) for ln in title_lines]

def jsesc(lines):
    return '\n'.join(l.replace('\\', '\\\\').replace('`', '\\`') for l in lines)

illus_js = jsesc(illus)
title_js = jsesc(title_lines)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Skipping Stones</title>
<style>
* { margin:0; padding:0; box-sizing:border-box }
html, body {
  width:100%; height:100%; background:#000;
  overflow:hidden;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
}
#stage, #title {
  font-family:'Courier New',Courier,monospace;
  font-size: min(0.833vw, 0.95vh);
  line-height: 1.15;
  white-space: pre;
  letter-spacing: 0;
  flex-shrink: 0;
  width: 220ch;        /* both elements exactly same width */
}
#stage { color:#aaa; }
#stage .ln { display:block; opacity:0; transition:opacity .06s linear; }
#stage .ln.on { opacity:1; }

#title {
  color:#fff;
  margin-top:.45em;
  opacity:0;
  transition:opacity .9s ease;
}
#title.on { opacity:1; }

#prompt {
  font-family:'Courier New',monospace;
  font-size: min(0.7vw, 1.1vh);
  color:#333;
  letter-spacing:4px;
  opacity:0; transition:opacity .8s;
  white-space:nowrap;
  margin-top:.7em;
  flex-shrink:0;
}
#prompt.on { opacity:1; }
#prompt span { animation:blink 1.4s step-end infinite; }
@keyframes blink { 50%{opacity:0} }
</style>
</head>
<body>
<pre id="stage"></pre>
<pre id="title">TITLE_PLACEHOLDER</pre>
<div id="prompt"><span>·</span> press any key <span>·</span></div>

<script>
const ILLUS = `ILLUS_PLACEHOLDER`;
const lines = ILLUS.split('\n');
const stage  = document.getElementById('stage');
const title  = document.getElementById('title');
const prompt = document.getElementById('prompt');
const DELAY  = 22;

lines.forEach(ln => {
  const el = document.createElement('span');
  el.className = 'ln';
  el.textContent = ln;
  stage.appendChild(el);
});

const spans = stage.querySelectorAll('.ln');
const total = spans.length * DELAY;
spans.forEach((el, i) => setTimeout(() => el.classList.add('on'), i * DELAY));
setTimeout(() => title.classList.add('on'),  total + 100);
setTimeout(() => {
  prompt.classList.add('on');
  document.addEventListener('keydown', go, {once:true});
  document.addEventListener('click',   go, {once:true});
}, total + 900);

// ── dissolve: characters blink out in concentric waves from center ────
function go() {
  prompt.classList.remove('on');

  // One canvas covers everything — we'll fill black over each char cell
  const cv  = document.createElement('canvas');
  cv.style.cssText = 'position:fixed;inset:0;z-index:100;pointer-events:none;';
  cv.width  = window.innerWidth;
  cv.height = window.innerHeight;
  document.body.appendChild(cv);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = '#000';

  const SCX = cv.width  / 2;
  const SCY = cv.height / 2;
  const fs  = parseFloat(getComputedStyle(stage).fontSize);
  const CW  = fs * 0.601;   // monospace char width
  const CH  = fs * 1.15;    // line height

  // ── collect every non-space character cell from both pres ───────────
  const cells = [];

  // #stage: lines are .ln child spans
  {
    const R = stage.getBoundingClientRect();
    stage.querySelectorAll('.ln').forEach((ln, row) => {
      const text = ln.textContent;
      for (let col = 0; col < text.length; col++) {
        if (text[col] === ' ') continue;
        const x  = R.left + col * CW;
        const y  = R.top  + row * CH;
        const dx = x + CW * 0.5 - SCX;
        const dy = y + CH * 0.5 - SCY;
        cells.push({ x, y, dist: Math.sqrt(dx*dx + dy*dy), angle: Math.atan2(dy, dx) });
      }
    });
  }

  // #title: plain text in <pre>, split by newline
  {
    const R = title.getBoundingClientRect();
    title.textContent.split('\n').forEach((line, row) => {
      for (let col = 0; col < line.length; col++) {
        if (line[col] === ' ') continue;
        const x  = R.left + col * CW;
        const y  = R.top  + row * CH;
        const dx = x + CW * 0.5 - SCX;
        const dy = y + CH * 0.5 - SCY;
        cells.push({ x, y, dist: Math.sqrt(dx*dx + dy*dy), angle: Math.atan2(dy, dx) });
      }
    });
  }

  const maxR  = Math.max(...cells.map(c => c.dist)) + 30;
  const gone  = new Uint8Array(cells.length);   // 0 = visible, 1 = erased
  const START = performance.now();
  const DUR   = 1400;

  function frame(ts) {
    const p  = Math.min((ts - START) / DUR, 1);
    const ep = 1 - Math.pow(1 - p, 3);   // ease-out cubic
    const r  = ep * maxR;
    const t  = (ts - START) / 170;
    const amp = 16 * (1 - ep * 0.6);     // wobble shrinks as wave expands

    for (let i = 0; i < cells.length; i++) {
      if (gone[i]) continue;
      const c = cells[i];
      // wave-front wobble: same two-frequency sin as water.py rings
      const w = Math.sin(c.angle * 7 + t      ) * amp
              + Math.sin(c.angle * 3 - t * 1.4) * amp * 0.35;
      if (c.dist < r + w) {
        ctx.fillRect(c.x, c.y, CW + 1, CH + 1);
        gone[i] = 1;
      }
    }

    if (p < 1) requestAnimationFrame(frame);
    else        window.location.href = 'stone_game.html';
  }
  requestAnimationFrame(frame);
}
</script>
</body>
</html>
"""

HTML = HTML.replace('ILLUS_PLACEHOLDER', illus_js)
HTML = HTML.replace('TITLE_PLACEHOLDER', title_js)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"written -> {OUT}")
print(f"illus: {len(illus)} lines x {COLS} cols   title: {len(title_lines)} lines")
