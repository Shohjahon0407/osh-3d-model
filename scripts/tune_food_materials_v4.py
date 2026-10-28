"""Cooked yellow carrot hue and lightly oily starch response, same geometry."""
import pathlib
ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
exec(compile((ROOT/'scripts/food_v4_utils.py').read_text(),'<food utilities>','exec'))
rng=np.random.default_rng(2710274)
v,u=np.mgrid[0:1:1024j,0:1:1024j].astype(np.float32)
noise=rng.normal(0,1,u.shape).astype(np.float32);tau=math.tau
rough=np.clip(.33+.035*np.sin(tau*u*2)*np.cos(tau*v*3)-.075*np.maximum(0,np.sin(tau*(u*1.3+v))),.24,.43)
png(TEX/'v4_rice_orm.png',np.stack((np.ones_like(u),rough,np.zeros_like(u)),axis=2))
for i,color in enumerate([(.82,.64,.035),(.75,.52,.025),(.72,.30,.018)]):
    variation=1+.040*np.sin(tau*(u*1.5+v*.4))+.015*noise
    png(TEX/f'v4_carrot_{i}_basecolor.png',np.array(color,np.float32)[None,None,:]*variation[:,:,None])
for image in bpy.data.images:
    if image.name.startswith('v4_rice_orm') or image.name.startswith('v4_carrot_') and 'basecolor' in image.name:
        image.reload();image.pack()
for material in bpy.data.materials:
    if material.name.startswith('ToyOsh_v4_Rice_'):
        bsdf=material.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Coat Weight'].default_value=.065
        bsdf.inputs['Specular IOR Level'].default_value=.33
        for node in material.node_tree.nodes:
            if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.08
food=json.loads((OUT/'food_v4.json').read_text());food['finish']='Predominantly cooked yellow/golden carrots; rice roughness .24-.43 with a light oil coat.'
(OUT/'food_v4.json').write_text(json.dumps(food,indent=2))
win=bpy.data.window_managers[0].windows[0]
with bpy.context.temp_override(window=win):bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
result={'material_finish':'cooked yellow carrots and lightly oily rice'}
