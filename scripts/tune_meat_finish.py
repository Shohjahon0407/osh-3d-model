"""Tune the checked close-up toward moist braised meat, without changing meshes."""
import bpy,pathlib
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
for name in ['ToyOsh_Cooked_Meat_4K_Cut','ToyOsh_Cooked_Meat_4K_Braised_Exterior']:
    mat=bpy.data.materials[name]
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Coat Weight'].default_value=.30 if name.endswith('Cut') else .27
    bsdf.inputs['Coat Roughness'].default_value=.13
    bsdf.inputs['Specular IOR Level'].default_value=.43
    for node in mat.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.40
bsdf=bpy.data.materials['ToyOsh_Rendered_Gelatin_Fat_4K'].node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Coat Weight'].default_value=.42
bsdf.inputs['Roughness'].default_value=.18
bpy.ops.wm.save_as_mainfile(filepath=str(out/'toyosh.blend'))
