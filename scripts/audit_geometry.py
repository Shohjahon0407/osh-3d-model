import bpy,bmesh,json,pathlib
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
scene=bpy.data.scenes['ToyOsh'];bpy.context.window.scene=scene
report={}
for ob in bpy.data.collections['ToyOsh_Asset'].objects:
    bm=bmesh.new();bm.from_mesh(ob.data)
    report[ob.name]={
        'boundary_edges':sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'zero_area_faces':sum(f.calc_area()<1e-15 for f in bm.faces),
        'min_z_m':min(v.co.z for v in bm.verts),
    }
    bm.free()
(out/'geometry_audit.json').write_text(json.dumps(report,indent=2))
print('GEOMETRY_AUDIT',json.dumps(report))
