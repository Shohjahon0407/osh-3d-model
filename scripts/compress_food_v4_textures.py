"""High-quality color JPEGs, lossless data PNGs; leave 4K meat files alone."""
from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]/'output/toyosh/textures'
for path in root.glob('v4_*.png'):
    with Image.open(path) as im:
        if path.stem.endswith('basecolor'):
            im.convert('RGB').save(path.with_suffix('.jpg'),quality=94,subsampling=0,optimize=True)
        else:im.save(path,optimize=True,compress_level=9)
