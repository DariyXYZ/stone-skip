from PIL import Image, ImageEnhance
import sys, os

IMG   = r"C:\VS Code\workfiles\Rock Skipping\2026-05-07_20-33_20606cc3d1.jpg"
OUT   = r"C:\VS Code\workfiles\Rock Skipping\cover_ascii.txt"
WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 200

CHARS = ' .,:;+*?%S#@'   # dark → bright

img = Image.open(IMG).convert('L')
contrast = ImageEnhance.Contrast(img)
img = contrast.enhance(1.4)

aspect = img.height / img.width
rows   = max(1, round(WIDTH * aspect * 0.45))
img    = img.resize((WIDTH, rows), Image.LANCZOS)

px = list(img.getdata())
n  = len(CHARS) - 1

lines = []
for r in range(rows):
    row = ''
    for c in range(WIDTH):
        lum = px[r * WIDTH + c] / 255.0
        row += CHARS[round(lum * n)]
    lines.append(row)

text = '\n'.join(lines)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"done  {WIDTH}x{rows}  ->  {OUT}")
