"""Fast color and texture-free geometry review before the final 4K renders."""
import bpy,pathlib
from mathutils import Vector
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
scene=bpy.data.scenes['ToyOsh'];bpy.context.window.scene=scene
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='CUDA';prefs.get_devices()
for device in prefs.devices:device.use=device.type=='CUDA'
scene.cycles.device='GPU';scene.cycles.samples=32
scene.cycles.use_denoising=True
if hasattr(scene.cycles,'denoising_use_gpu'):scene.cycles.denoising_use_gpu=True
scene.render.resolution_x=1400;scene.render.resolution_y=1000
target=Vector((-.005,.005,.032))
scene.camera.location=(.16,-.23,.22)
scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=.25
scene.render.filepath=str(out/'draft_meat_shape_color.png')
bpy.ops.render.render(write_still=True)
clay=bpy.data.materials.new('Geometry_Review_Only')
clay.use_nodes=True
bsdf=clay.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value=(.30,.27,.23,1)
bsdf.inputs['Roughness'].default_value=.82
scene.view_layers[0].material_override=clay
scene.camera.data.ortho_scale=.19
scene.render.filepath=str(out/'preview_meat_shape.png')
bpy.ops.render.render(write_still=True)
scene.view_layers[0].material_override=None
