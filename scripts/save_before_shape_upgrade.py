import bpy
win=bpy.data.window_managers[0].windows[0]
with bpy.context.temp_override(window=win):
    if bpy.context.object and bpy.context.object.mode!='OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.wm.save_as_mainfile(filepath='/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh/toyosh.blend')
result={'saved':bpy.data.filepath,'scene':win.scene.name,'mode':bpy.context.mode}
