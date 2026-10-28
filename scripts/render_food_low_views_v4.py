"""Four low product views reveal density and support that a top view can hide."""
import bpy,pathlib,math
from mathutils import Vector
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
scene=bpy.data.scenes['ToyOsh'];bpy.context.window.scene=scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='CUDA';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='CUDA'
scene.cycles.device='GPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=True
scene.render.resolution_x=1200;scene.render.resolution_y=760
scene.camera.data.ortho_scale=.32
target=Vector((0,0,.030))
for name,dx,dy in [('front',0,-1),('back',0,1),('left',-1,0),('right',1,0)]:
    scene.camera.location=target+Vector((dx*.4,dy*.4,.107))
    scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(out/f'preview_{name}_low.png')
    bpy.ops.render.render(write_still=True)
