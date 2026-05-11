from PIL import Image

src = Image.open('logo.jpg').convert('RGBA')

for size in [192, 512]:
    img = src.resize((size, size), Image.LANCZOS)
    img.save(f'icon-{size}.png')
    print(f'icon-{size}.png saved')
