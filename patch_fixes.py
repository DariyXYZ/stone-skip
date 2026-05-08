import re

COLS = 220
PAD = 5

with open(r'C:\VS Code\workfiles\Rock Skipping\title_ascii.txt', encoding='utf-8') as f:
    raw_lines = f.read().splitlines()

# Pad to 220, centered
title_lines = [(' ' * PAD + ln).ljust(COLS) for ln in raw_lines]

def jsesc(lines):
    return '\n'.join(l.replace('\\', '\\\\').replace('`', '\\`') for l in lines)

title_js = jsesc(title_lines)

with open(r'C:\VS Code\workfiles\Rock Skipping\stone_game.html', encoding='utf-8') as f:
    html = f.read()

# 1. Fix particles: add full-screen fill before hiding splash
old_end = "        document.getElementById('splash').style.display = 'none';\n        cv.remove();\n        startGame();"
new_end = "        ctx.fillRect(0, 0, cv.width, cv.height);\n        document.getElementById('splash').style.display = 'none';\n        cv.remove();\n        startGame();"

if old_end in html:
    html = html.replace(old_end, new_end, 1)
    print('Particles fix: OK')
else:
    print('Particles fix: FAILED - pattern not found')

# 2. Replace title content in #sp-title pre
old_pre = re.search(r'<pre id="sp-title">(.*?)</pre>', html, re.DOTALL)
if old_pre:
    html = html[:old_pre.start()] + '<pre id="sp-title">' + title_js + '</pre>' + html[old_pre.end():]
    print('Title replace: OK')
else:
    print('Title replace: FAILED - pre not found')

with open(r'C:\VS Code\workfiles\Rock Skipping\stone_game.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Written -> stone_game.html')
