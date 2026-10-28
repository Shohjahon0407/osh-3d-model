"""Keep PBR maps proportionate to their visible surface area in the mobile asset."""
from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]/'output/toyosh/textures'
for path in root.glob('*.png'):
    name=path.stem
    if name.startswith('cooked_meat_4k'):
        limit=4096
    elif name.startswith('v4_'):
        limit=1024
    elif name.startswith('porcelain'):
        limit=2048
    elif name=='meat_photo_basecolor':
        limit=1024
    elif name=='meat_photo_normal':
        limit=1024
    elif name.startswith('meat_photo'):
        limit=256
    elif name.startswith('meat_cut') or name.startswith('meat_crust'):
        limit=512 if name.endswith('basecolor') else 256
    elif name.endswith('orm'):
        limit=128
    elif name.startswith('rice'):
        limit=256
    else:
        limit=512 if name.endswith('basecolor') else 256
    with Image.open(path) as image:
        if max(image.size)>limit:
            image.thumbnail((limit,limit),Image.Resampling.LANCZOS)
            image.save(path,optimize=True)
