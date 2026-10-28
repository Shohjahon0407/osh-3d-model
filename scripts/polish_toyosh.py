"""Final photo alignment and visible grain coverage, without rebuilding textures."""
import bpy, ast, pathlib, math, random
import numpy as np
from mathutils import Vector, Matrix
ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT=ROOT/'output/toyosh';TEX=OUT/'textures'
scene=bpy.data.scenes['ToyOsh'];bpy.context.window.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
random.seed(271028)
mats={m.name.removeprefix('ToyOsh_'):m for m in bpy.data.materials if m.name.startswith('ToyOsh_')}
tree=ast.parse((ROOT/'scripts/build_toyosh.py').read_text())
names={'Mesh','ellipsoid','mound'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[]),'<mesh utilities>','exec'))

photo=mats['meat_photo']
def photo_surface(name,rough):
    mat=photo.copy();mat.name='ToyOsh_'+name
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    for sock in ['Roughness','Metallic','Normal']:
        for link in list(bsdf.inputs[sock].links):mat.node_tree.links.remove(link)
    bsdf.inputs['Roughness'].default_value=rough
    bsdf.inputs['Metallic'].default_value=0
    return mat

bed=bpy.data.objects['02_Rice_Interior']
bed.data.materials.clear();bed.data.materials.append(photo_surface('Photo_Guided_Rice_Bed',.44))
for poly in bed.data.polygons:
    for li in poly.loop_indices:
        co=bed.data.vertices[bed.data.loops[li].vertex_index].co
        bed.data.uv_layers.active.data[li].uv=(.5+co.x/.28,.5+co.y/.28)

plate=bpy.data.objects['01_Handpainted_Porcelain_Lagan']
plate.data.materials[0]=photo_surface('Reference_Porcelain_Ornament',.23)
for poly in plate.data.polygons:
    if poly.material_index==0:
        for li in poly.loop_indices:
            co=plate.data.vertices[plate.data.loops[li].vertex_index].co
            plate.data.uv_layers.active.data[li].uv=(.5+co.x/.28,.5+co.y/.28)

# Reuse the photo contour authoring pass, including the two central support pieces.
for name in ['05_Slow_Cooked_Meat_Pieces','06_Torn_Meat_Fibers']:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
tree=ast.parse((ROOT/'scripts/refine_toyosh.py').read_text())
body=[]
for n in tree.body:
    if isinstance(n,ast.FunctionDef) and n.name=='xy':body.append(n)
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='contours' for t in n.targets):body.append(n)
exec(compile(ast.Module(body=body,type_ignores=[]),'<reference contours>','exec'))
meat=Mesh('05_Slow_Cooked_Meat_Pieces',[mats['meat_photo'],mats['meat_crust']])
shreds=Mesh('06_Torn_Meat_Fibers',[mats['meat_cut'],mats['meat_crust']])
metadata=[]
for node in tree.body:
    if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple) and [x.id for x in node.target.elts]==['pi','points']:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<photo meat construction>','exec'))
meat.finish();shreds.finish()

# An additional sparse layer covers exposed bed at the rim and in open areas.
rice=Mesh('09_Additional_Surface_Rice',[mats[n] for n in ['rice_ivory','rice_cream','rice_golden','rice_white']])
for i in range(240):
    rr=math.sqrt(random.uniform(.10,1))
    a=random.uniform(0,math.tau)
    x=.110*rr*math.cos(a);y=.107*rr*math.sin(a)
    rice.add(*ellipsoid((x,y,mound(x,y)+.001),
        (random.uniform(.0034,.0046),random.uniform(.0009,.0012),.0009),
        random.uniform(0,math.tau),tilt=random.uniform(-.4,.4)),mat=random.choices([0,1,2,3],[.4,.3,.2,.1])[0])
rice.finish()

scene['asset_notes']='Photo-guided volumetric reconstruction. Individual rice, traced cut meat and inferred side walls, carrots, fat and lathed porcelain. Reference-derived albedo has broad illumination normalized; residual photographic highlights can remain.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
