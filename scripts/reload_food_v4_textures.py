import bpy,pathlib
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
for im in list(bpy.data.images):
    if im.name.startswith('v4_'):
        path=pathlib.Path(bpy.path.abspath(im.filepath))
        if path.stem.endswith('basecolor') and path.with_suffix('.jpg').exists():
            color=bpy.data.images.load(str(path.with_suffix('.jpg')),check_existing=True)
            color.pack();im.user_remap(color)
        else:im.reload();im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'toyosh.blend'))
