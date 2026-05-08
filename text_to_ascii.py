from PIL import Image, ImageDraw, ImageFont
import sys

TEXT      = "ROCK SKIPPING GAME"
COLS      = int(sys.argv[1]) if len(sys.argv) > 1 else 160
CHARS     = ' .,:;+*?%S#@'

# Try fonts from most to least Cinzel-like
FONTS = [
    r"C:\Windows\Fonts\TRAJAN~1.TTF",
    r"C:\Windows\Fonts\Trajan Pro Regular.ttf",
    r"C:\Windows\Fonts\TrajanPro-Regular.ttf",
    r"C:\Windows\Fonts\palab.ttf",   # Palatino Linotype Bold
    r"C:\Windows\Fonts\timesbd.ttf", # Times New Roman Bold
    r"C:\Windows\Fonts\georgia.ttf",
]

font = None
for path in FONTS:
    try:
        font = ImageFont.truetype(path, 180)
        print(f"# font: {path}", flush=True)
        break
    except Exception:
        continue

if font is None:
    font = ImageFont.load_default()
    print("# font: default", flush=True)

# measure text
tmp = Image.new('L', (1, 1), 0)
draw = ImageDraw.Draw(tmp)
bbox = draw.textbbox((0, 0), TEXT, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]

pad = 30
img = Image.new('L', (tw + pad*2, th + pad*2), 0)
draw = ImageDraw.Draw(img)
draw.text((pad - bbox[0], pad - bbox[1]), TEXT, font=font, fill=255)

# resize to target cols
rows = max(1, round(COLS * img.height / img.width * 0.45))
img  = img.resize((COLS, rows), Image.LANCZOS)

px = list(img.getdata())
n  = len(CHARS) - 1

lines = []
for r in range(rows):
    row = ''
    for c in range(COLS):
        lum = px[r * COLS + c] / 255.0
        row += CHARS[round(lum * n)]
    lines.append(row.rstrip())

result = '\n'.join(lines)
print(result)

out = r"C:\VS Code\workfiles\Rock Skipping\title_ascii.txt"
with open(out, 'w', encoding='utf-8') as f:
    f.write(result)
print(f"\n# saved -> {out}", flush=True)
