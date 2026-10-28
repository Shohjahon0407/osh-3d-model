import bpy,pathlib,json
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
win=bpy.data.window_managers[0].windows[0];win.scene=bpy.data.scenes['ToyOsh_Review_v6']
image=bpy.data.images.load(str(out/'textures/cooked_meat_4k_basecolor.jpg'),check_existing=True);image.pack()
for name in ['v6_Meat_Moist_Cut','v6_Meat_Braised_Exterior']:
    m=bpy.data.materials[name];nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes['Principled BSDF']
    base=list(p.inputs['Base Color'].links)[0].from_socket
    tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.label='Retained cooked-meat tissue variation'
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.62
    links.new(base,mix.inputs[1]);links.new(tex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])
    p.inputs['Coat Weight'].default_value=.025
# Repair cylindrical wrap seams and verify the editable review meshes again.
with bpy.context.temp_override(window=win):
    exec(compile(pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/scripts/audit_review_v6.py').read_text(),'<review audit>','exec'))
report=json.loads((out/'review_v6.json').read_text())
report['material_finish']='Original 4K cooked-tissue albedo blended with restrained new albedo; new 4K directed normals and moisture map plus fine procedural pores. Final PBR bake/export is deferred until review.'
report['limitations'].append('Retained tissue albedo contains some photographic shading; final material bake will follow visual approval.')
(out/'review_v6.json').write_text(json.dumps(report,indent=2))
for area in win.screen.areas:
    if area.type=='VIEW_3D':
        s=area.spaces.active;s.region_3d.view_distance=.23;s.region_3d.view_location=(0,0,.044)
        area.tag_redraw()
result={'scene':win.scene.name,'material_finish':'4K tissue detail with soft uneven moisture','final_render_created':False}
