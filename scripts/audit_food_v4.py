"""Independent contact/particle audit on the current scene (no mesh changes)."""
import pathlib
ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
exec(compile((ROOT/'scripts/food_v4_utils.py').read_text(),'<food utilities>','exec'))
plate=bvh_objects([bpy.data.objects['01_Handpainted_Porcelain_Lagan']])
carrot=bvh_objects([bpy.data.objects['04_Braised_Yellow_and_Orange_Carrots']])
counts={};penetration=0;worst=None;buried_centers=[]
for name in ['03_Individual_Long_Grain_Rice','09_Additional_Surface_Rice','10_Rice_Gap_Fill','04_Braised_Yellow_and_Orange_Carrots']:
    ob=bpy.data.objects[name];parts=components(ob);counts[name]=len(parts)
    for v in ob.data.vertices:
        p=ob.matrix_world@v.co;floor=z_hit(plate,p.x,p.y)
        if floor is not None and floor-p.z>penetration:
            penetration=floor-p.z;worst={'object':name,'position':list(p)}
    if name.startswith('04_'):continue
    for i,part in enumerate(parts):
        center=sum((ob.matrix_world@ob.data.vertices[j].co for j in part),Vector())/len(part)
        top=z_hit(carrot,center.x,center.y);bottom=z_hit(carrot,center.x,center.y,True)
        if top is not None and bottom is not None and bottom<center.z<top:
            depth=min(center.z-bottom,top-center.z)
            if depth>.0008:buried_centers.append({'object':name,'grain':i,'depth_m':depth})
report={'rice_grains':sum(n for k,n in counts.items() if not k.startswith('04_')),
        'components':counts,'maximum_plate_penetration_m':penetration,'worst_plate_point':worst,
        'grain_centers_inside_carrot_vertical_envelope':len(buried_centers),
        'carrot_envelope_note':'Conservative union of top/bottom rays; overlapping carrots can give false positive center classifications.',
        'center_samples':buried_centers[:20]}
assert report['rice_grains']==10000
assert counts['04_Braised_Yellow_and_Orange_Carrots']==90
assert penetration<.00025,report
(OUT/'food_geometry_audit_v4.json').write_text(json.dumps(report,indent=2))
result=report
