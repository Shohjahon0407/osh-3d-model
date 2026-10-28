"""Run in Blender background: normalize meshes, render, export, reimport and audit."""
import bpy
import bmesh
import pathlib
import json
import math
import struct
import sys
from mathutils import Vector

OUT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
scene=bpy.data.scenes['ToyOsh']
bpy.context.window.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
texture_limit=int(scene.get('maximum_texture_dimension',2048))
meat_v2=scene.get('meat_detail_version',0)>=2
meat_v3=scene.get('meat_detail_version',0)>=3
food_v4=scene.get('food_detail_version',0)>=4
triangle_budget=int(scene.get('triangle_budget',150000))
file_budget_mib=int(scene.get('file_budget_mib',20))
macro_only='--macro-only' in sys.argv
skip_renders='--skip-renders' in sys.argv

for ob in asset.objects:
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    if ob.name=='01_Handpainted_Porcelain_Lagan':
        # Close the two tiny center rings of the lathed cross-section.
        bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    # Triangulate caps explicitly so tangent export is deterministic.
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()

plate=bpy.data.objects['01_Handpainted_Porcelain_Lagan']
scale=.28/max(plate.dimensions.x,plate.dimensions.y)
for vert in plate.data.vertices:
    vert.co.x*=scale
    vert.co.y*=scale
plate.data.update()

# Prefer the available NVIDIA GPU; CPU rendering remains a functional fallback.
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='CUDA'
    prefs.get_devices()
    found=False
    for device in prefs.devices:
        device.use=device.type=='CUDA'
        found |= device.type=='CUDA'
    scene.cycles.device='GPU' if found else 'CPU'
except Exception:
    scene.cycles.device='CPU'

scene.render.resolution_x=1200
scene.render.resolution_y=1200
scene.cycles.samples=64
scene.cycles.use_denoising=True
if food_v4 and hasattr(scene.cycles,'denoising_use_gpu'):
    scene.cycles.denoising_use_gpu=True

# Preserve and check the pre-existing scene before writing the final .blend.
original=json.loads((OUT/'original_scene_state.json').read_text())
preserved=True
for name,objects in original.items():
    s=bpy.data.scenes.get(name)
    assert s is not None, f'Original scene missing: {name}'
    # Inactive scenes have unevaluated matrix_world values after file loading.
    bpy.context.window.scene=s
    bpy.context.view_layer.update()
    assert set(o.name for o in s.objects)==set(objects)
    for name,old in objects.items():
        ob=s.objects[name]
        assert ob.type==old['type']
        assert all(abs(ob.matrix_world[i][j]-old['matrix'][i][j])<1e-7 for i in range(4) for j in range(4))
bpy.context.window.scene=scene
bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT')
for ob in asset.objects:
    ob.select_set(True)
bpy.context.view_layer.objects.active=plate
bpy.ops.export_scene.gltf(
    filepath=str(OUT/'toyosh.glb'),
    export_format='GLB',
    use_selection=True,
    export_yup=True,
    export_materials='EXPORT',
    export_cameras=False,
    export_lights=False,
    export_extras=True,
    export_image_format='AUTO',
    export_normals=True,
    # glTF consumers generate tangent frames from normals/UVs when omitted.
    # Avoid a redundant per-vertex tangent stream for the highly split v3 mesh.
    export_tangents=not meat_v3,
)
if meat_v2:
    # Blender's exporter drops this MixRGB multiplication. Express it as the
    # standard linear glTF baseColorFactor; both materials share the same image.
    path=OUT/'toyosh.glb'
    raw=path.read_bytes()
    json_length=struct.unpack_from('<I',raw,12)[0]
    document=json.loads(raw[20:20+json_length])
    material_by_name={m['name']:m for m in document['materials']}
    interior=material_by_name['ToyOsh_Cooked_Meat_4K_Cut']['pbrMetallicRoughness']
    exterior=material_by_name['ToyOsh_Cooked_Meat_4K_Braised_Exterior']['pbrMetallicRoughness']
    source_a=document['textures'][interior['baseColorTexture']['index']]['source']
    source_b=document['textures'][exterior['baseColorTexture']['index']]['source']
    assert source_a==source_b
    material=bpy.data.materials['ToyOsh_Cooked_Meat_4K_Braised_Exterior']
    multiplier=next(n for n in material.node_tree.nodes if n.type=='MIX_RGB')
    exterior['baseColorFactor']=list(multiplier.inputs[2].default_value)
    encoded=json.dumps(document,separators=(',',':')).encode()
    encoded+=b' '*((-len(encoded))%4)
    tail=raw[20+json_length:]
    packed=struct.pack('<4sII',b'glTF',2,20+len(encoded)+len(tail))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+tail
    path.write_bytes(packed)
assert (OUT/'toyosh.glb').stat().st_size<file_budget_mib*1024*1024, 'GLB exceeds the selected file budget; optimize maps before rendering.'

def camera(loc,scale):
    scene.camera.location=loc
    scene.camera.rotation_euler=(Vector((0,0,.018))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=scale

views=[('preview_angle',(.23,-.31,.28),.335),
       ('preview_top',(0,-.00001,.45),.325),
       ('preview_side',(.23,-.36,.105),.335)]
for name,location,scale in ([] if macro_only or skip_renders else views):
    camera(location,scale)
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)

if meat_v2 and not skip_renders:
    # A true UHD render exposes the fine muscle strands and oily fat response.
    target=Vector((-.006,.014,.045 if food_v4 else .035))
    scene.camera.location=(.12,-.16,.17)
    scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=.165
    scene.render.resolution_x=3840
    scene.render.resolution_y=2160
    scene.cycles.samples=64
    if hasattr(scene.cycles,'denoising_use_gpu'):
        scene.cycles.denoising_use_gpu=True
    scene.render.filepath=str(OUT/'preview_meat_4k.png')
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=1200
    scene.render.resolution_y=1200
    scene.cycles.samples=64

if food_v4 and not skip_renders:
    target=Vector((.042,-.041,.034))
    scene.camera.location=(.18,-.24,.20)
    scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=.145
    scene.render.resolution_x=3840
    scene.render.resolution_y=2160
    scene.cycles.samples=64
    scene.render.filepath=str(OUT/'preview_rice_carrot_4k.png')
    bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=1200
    scene.render.resolution_y=1200

camera(views[0][1],views[0][2])
scene.render.filepath=str(OUT/'preview_angle.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))

stats={}
for ob in asset.objects:
    ob.data.calc_loop_triangles()
    stats[ob.name]={'vertices':len(ob.data.vertices),'triangles':len(ob.data.loop_triangles)}
triangles=sum(d['triangles'] for d in stats.values())
max_texture=max(max(im.size) for im in bpy.data.images if im.name not in ['Render Result','Viewer Node'] and im.size[0] and im.packed_file)

verify=bpy.data.scenes.new('ToyOsh_GLB_Validation')
bpy.context.window.scene=verify
bpy.ops.import_scene.gltf(filepath=str(OUT/'toyosh.glb'))
imported=[o for o in verify.objects if o.type=='MESH']
assert len(imported)==len(asset.objects)
assert all(o.data.uv_layers for o in imported)
assert all(m.use_nodes for o in imported for m in o.data.materials)
itri=0
for ob in imported:
    ob.data.calc_loop_triangles()
    itri+=len(ob.data.loop_triangles)
points=[ob.matrix_world@Vector(v) for ob in imported for v in ob.bound_box]
bounds={'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
images=[im for im in bpy.data.images if im.name not in ['Render Result','Viewer Node'] and im.size[0]]
glb_size=(OUT/'toyosh.glb').stat().st_size
assert triangles<=triangle_budget
assert itri==triangles
assert glb_size<file_budget_mib*1024*1024
assert max_texture<=texture_limit
report={
    'blender_version':bpy.app.version_string,
    'scene':'ToyOsh',
    'source':str(pathlib.Path('/home/shohjahon/BESHKASHTAN_RASMLARI/ofiyat rasmlari/toyosh.jpg')),
    'triangles':triangles,
    'glb_triangles_after_reimport':itri,
    'glb_mesh_count':len(imported),
    'glb_size_bytes':glb_size,
    'maximum_texture_dimension':max_texture,
    'allowed_texture_dimension':texture_limit,
    'meat_detail_version':int(scene.get('meat_detail_version',1)),
    'food_detail_version':int(scene.get('food_detail_version',0)),
    'meat_quantity_version':int(scene.get('meat_quantity_version',0)),
    'meat_main_clumps':int(scene.get('meat_main_clumps',16)),
    'triangle_budget':triangle_budget,
    'file_budget_mib':file_budget_mib,
    'additional_reference_images':json.loads((OUT/'meat_shape_v3.json').read_text())['reference_images'] if meat_v3 else [],
    'original_scene_preserved':preserved,
    'bounds_m':bounds,
    'dimensions_m':[bounds['max'][i]-bounds['min'][i] for i in range(3)],
    'objects':stats,
    'render_device':scene.cycles.device,
    'texture_method':('v4: six layers of cooked rice with native 1K procedural PBR, soft cooked carrots, and unchanged v3 4K meat image maps; meat rigidly resettled on substantial supports.' if food_v4 else ('Pulled meat v3: real torn/fanned fascicle solids, loose shreds and frayed tips using existing 4K PBR maps. Rice bed cleaned beneath the old meat footprints.' if meat_v3 else ('Dedicated cooked-tissue 4K color, physical-fibril normal and oil/fat ORM maps; generated source augmented with native 4K procedural detail. Other surfaces retain their previous maps.' if meat_v2 else 'Procedural PBR fields evaluated into PNG maps; photo-guided albedo on traced meat, rice bed and porcelain. Broad photographic illumination normalized approximately.'))),
    'limitations':['Uncalibrated references: unseen geometry and physical dimensions inferred.','Residual photographic highlights remain; albedo is not a calibrated intrinsic-color reconstruction.','Static contact fitting and visual physical plausibility; no rigid-body food simulation.'],
}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print('TOYOSH_VALIDATION',json.dumps(report))
