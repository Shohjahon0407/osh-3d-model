import bpy,pathlib,json
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
archive=pathlib.Path((out/'v6_archive_path.txt').read_text())
win=bpy.data.window_managers[0].windows[0]
with bpy.context.temp_override(window=win):
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath=str(archive/'live_before_v6.blend'),copy=True)
result={'backup':str(archive/'live_before_v6.blend'),'active_scene':win.scene.name,'file':bpy.data.filepath}
