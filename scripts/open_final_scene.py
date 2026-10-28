import bpy
path='/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh/toyosh.blend'
bpy.ops.wm.open_mainfile(filepath=path)
scene=bpy.data.scenes['ToyOsh']
window=bpy.data.window_managers[0].windows[0]
window.scene=scene
window.view_layer.update()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.clip_start=.001
            space.clip_end=100
            space.region_3d.view_location=(0,0,.018)
            space.region_3d.view_distance=.43
            if scene.get('meat_detail_version',0)>=2:
                space.region_3d.view_location=(-.006,.014,.035)
                space.region_3d.view_distance=.27
            if scene.get('food_detail_version',0)>=4:
                space.region_3d.view_location=(0,0,.036)
                space.region_3d.view_distance=.37
            space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
            space.region_3d.view_perspective='ORTHO'
            space.overlay.show_overlays=False
            space.shading.type='MATERIAL'
with bpy.context.temp_override(window=window):
    bpy.ops.wm.save_as_mainfile(filepath=path)
result={'scene':scene.name,'file':bpy.data.filepath,'asset_objects':len(bpy.data.collections['ToyOsh_Asset'].objects),'original_scene_objects':[o.name for o in bpy.data.scenes['Scene'].objects]}
