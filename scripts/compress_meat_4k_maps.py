"""Keep all maps at 4K; compress color and quantize tangent directions for size."""
from pathlib import Path
from PIL import Image,ImageEnhance
import math,json,random
root=Path(__file__).resolve().parents[1]/'output/toyosh/textures'
with Image.open(root/'cooked_meat_4k_basecolor.png') as im:
    graded=ImageEnhance.Color(im.convert('RGB')).enhance(.84)
    graded=ImageEnhance.Brightness(graded).enhance(.95)
    graded.save(root/'cooked_meat_4k_basecolor.jpg',quality=85,subsampling=2,optimize=True)
for suffix in ['normal','orm']:
    path=root/f'cooked_meat_4k_{suffix}.png'
    with Image.open(path) as im:
        if suffix=='normal':
            original=im.convert('RGB')
            packed=original.quantize(colors=256,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
            rgb=packed.convert('RGB')
            errors=[]
            random.seed(271027)
            for _ in range(5000):
                xy=(random.randrange(im.width),random.randrange(im.height))
                a=[v/127.5-1 for v in original.getpixel(xy)]
                b=[v/127.5-1 for v in rgb.getpixel(xy)]
                dot=sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))
                errors.append(math.degrees(math.acos(max(-1,min(1,dot)))))
            errors.sort()
            report={'directions':256,'resolution':[4096,4096],'mean_angular_error_deg':sum(errors)/len(errors),'p95_angular_error_deg':errors[int(len(errors)*.95)]}
            assert report['p95_angular_error_deg']<5,report
            packed.save(path,optimize=True,compress_level=9)
            (root.parent/'normal_compression.json').write_text(json.dumps(report,indent=2))
            print(report)
        else:
            red,green,blue=im.convert('RGB').split()
            green=green.point(lambda value:round(value*.78))
            Image.merge('RGB',(red,green,blue)).save(path,optimize=True,compress_level=9)
