import math
from PIL import Image, ImageDraw

for size in [192, 512]:
    img = Image.new('RGB', (size, size), '#000000')
    draw = ImageDraw.Draw(img)

    # Stone
    cx, cy = size // 2, int(size * 0.38)
    r = size // 7
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill='#c8bca0')

    # Water ripples
    wy = int(size * 0.60)
    lw = max(1, size // 128)
    for row, (amp, freq, col) in enumerate([(0.055, 7, '#777'), (0.035, 5, '#555')]):
        y0 = wy + row * size // 12
        pts = [(x, y0 + int(amp * size * math.sin(freq * math.pi * x / size)))
               for x in range(0, size + 1, 2)]
        for a, b in zip(pts, pts[1:]):
            draw.line([a, b], fill=col, width=lw)

    img.save(f'icon-{size}.png')
    print(f'icon-{size}.png')
