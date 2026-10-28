import bpy
from pathlib import Path
out=Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
for image in bpy.data.images:
    path=Path(bpy.path.abspath(image.filepath))
    if path.parent==out/'textures' and path.is_file():
        image.reload()
        image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'toyosh.blend'))
