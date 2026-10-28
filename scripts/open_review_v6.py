import bpy
path='/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh/toyosh_review_v6.blend'
bpy.ops.wm.open_mainfile(filepath=path)
win=bpy.data.window_managers[0].windows[0];win.scene=bpy.data.scenes['ToyOsh_Review_v6'];win.view_layer.update()
for area in win.screen.areas:
    if area.type=='VIEW_3D':
        s=area.spaces.active;s.shading.type='MATERIAL';s.overlay.show_overlays=False
        s.region_3d.view_location=(0,0,.035);s.region_3d.view_distance=.36
        s.region_3d.view_rotation=win.scene.camera.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
        area.tag_redraw()
result={'scene':win.scene.name,'file':path,'review_ready':True,'final_render_created':False}
