import sys
sys.path.insert(0,'/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/scripts')
from food_v4_utils import *
scene=bpy.data.scenes['ToyOsh_Review_v6'];bpy.context.window.scene=scene
asset=bpy.data.collections['ToyOsh_v6_Asset'];report=json.loads((OUT/'review_v6.json').read_text());checks={};fixed=0
for ob in asset.objects:
    if ob.get('food_class')==40:
        uv=ob.data.uv_layers.active.data
        for p in ob.data.polygons:
            values=[uv[i].uv.y for i in p.loop_indices]
            if max(values)-min(values)>.5:
                for i in p.loop_indices:
                    if uv[i].uv.y<.5:uv[i].uv.y+=1
            a=[uv[i].uv.copy() for i in p.loop_indices]
            area=abs(sum(a[k].x*a[(k+1)%len(a)].y-a[(k+1)%len(a)].x*a[k].y for k in range(len(a))))
            if area<1e-10:
                n=p.normal;axis=Vector((0,0,1)) if abs(n.z)<.9 else Vector((1,0,0));u=n.cross(axis).normalized();v=n.cross(u).normalized()
                for k in p.loop_indices:
                    co=ob.data.vertices[ob.data.loops[k].vertex_index].co
                    uv[k].uv=(co.dot(u)*25,co.dot(v)*25)
                fixed+=1
        ob.data.update()
    bm=bmesh.new();bm.from_mesh(ob.data)
    entry={'triangles':sum(len(f.verts)-2 for f in bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-15 for f in bm.faces),'finite_vertices':all(math.isfinite(c) for v in bm.verts for c in v.co)}
    bm.free();checks[ob.name]=entry
    assert entry['finite_vertices'] and not entry['nonmanifold_edges'] and not entry['zero_area_faces'],(ob.name,entry)
assert sum(d['triangles'] for d in checks.values())<=350000
rice_count=sum(len(components(o)) for o in asset.objects if o.get('food_class')==20)
assert rice_count==10000
assert len(components(bpy.data.objects['v6_04_Soft_Yellow_Carrots']))==120
assert all(p['contacts']>=1 for p in report['contacts'])
newimages=[im for im in bpy.data.images if im.filepath and '/v6/' in im.filepath]
assert len(newimages)==4 and all(tuple(im.size)==(4096,4096) and im.packed_file for im in newimages)
assert not any(o.name.endswith('.001') for o in asset.objects)
report['geometry_audit']={'passed':True,'objects':checks,'degenerate_cap_uv_fixed':fixed,'rice_count_verified':rice_count,'4k_maps_packed':True,'source_scenes_retained':list(bpy.data.scenes.keys()),'final_render_created':False,'glb_export_created':False}
(OUT/'review_v6.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh_review_v6.blend'))
print('V6_AUDIT_OK',json.dumps({'triangles':sum(d['triangles'] for d in checks.values()),'rice':rice_count,'cap_uvs_fixed':fixed}),flush=True)
