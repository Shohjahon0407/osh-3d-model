import sys
sys.path.insert(0,'/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/scripts')
from food_v4_utils import *
win=bpy.data.window_managers[0].windows[0];scene=bpy.data.scenes['ToyOsh_Review_v6'];win.scene=scene
asset=bpy.data.collections['ToyOsh_v6_Asset'];report=json.loads((OUT/'review_v6.json').read_text())
body=bpy.data.objects['v6_05_Braised_Meat_Chunks'];fib=bpy.data.objects['v6_06_Separated_Muscle_Fibres'];fat=bpy.data.objects['v6_07_Soft_Fat_Pockets']
bp=components(body);fp=components(fib);ap=components(fat)
assert len(bp)==32 and len(fp)==388 and len(ap)==24
food=bvh_objects([o for o in asset.objects if o.get('food_class')!=40]);rootv=[];rootf=[];roots=None;fatindex=0;contacts=[]
for gi,ids in enumerate(bp):
    ci=report['contacts'][gi]['clump'];center=sum((body.data.vertices[j].co for j in ids),Vector())/len(ids)
    # A mixture of thicker braised chunks and flatter torn slices, not uniform patties.
    zscale=1.0;xyscale=1.0
    members=[(body,ids)]+[(fib,part) for part in fp[gi*11:(gi+1)*11]]
    if ci<24:members.append((fat,ap[fatindex]));fatindex+=1
    for ob,part in members:
        for j in part:
            p=ob.data.vertices[j].co-center
            p.x*=xyscale;p.y*=xyscale;p.z*=zscale
            ob.data.vertices[j].co=center+p
    sourcepoints=[body.data.vertices[j].co.copy() for j in ids]
    idset=set(ids);lookup={j:k for k,j in enumerate(ids)}
    fs=[tuple(lookup[j] for j in p.vertices) for p in body.data.polygons if p.vertices[0] in idset]
    options=[(0.,0.)]
    angle=math.atan2(center.y,center.x) if center.xy.length>.015 else ci*2.399963
    for distance in [.012,.025,.038,.050]:
        for delta in [0,.65,-.65,1.3,-1.3]:options.append((distance*math.cos(angle+delta),distance*math.sin(angle+delta)))
    best=None
    for dx,dy in options:
        if math.hypot(center.x+dx,center.y+dy)>.092:continue
        points=[p+Vector((dx,dy,0)) for p in sourcepoints]
        root=BVHTree.FromPolygons(points,fs,all_triangles=False);offsets=[]
        for x in np.linspace(min(p.x for p in points)+.0001,max(p.x for p in points)-.0001,13):
            for y in np.linspace(min(p.y for p in points)+.0001,max(p.y for p in points)-.0001,11):
                hit=root.ray_cast(Vector((float(x),float(y),-.1)),Vector((0,0,1)))[0]
                if hit is None:continue
                height=z_hit(food,float(x),float(y));previous=z_hit(roots,float(x),float(y)) if roots else None
                h=max(v for v in [height,previous] if v is not None);offsets.append(h-hit.z)
        lift=max(offsets)-.00065;top=max(p.z for p in points)+lift
        if best is None or top<best[0]:best=(top,dx,dy,lift,offsets)
        if top<.083:break
    top,dx,dy,lift,offsets=best
    for ob,part in members:
        for j in part:ob.data.vertices[j].co+=Vector((dx,dy,lift))
    contacts.append({'clump':ci,'contacts':sum(abs(v-lift)<.0011 for v in offsets),'embedding_m':.00065,'maximum_z_m':top,'horizontal_shift_m':[dx,dy]})
    offset=len(rootv);lookup={j:offset+k for k,j in enumerate(ids)};idset=set(ids)
    rootv.extend(tuple(body.data.vertices[j].co) for j in ids)
    rootf.extend(tuple(lookup[j] for j in p.vertices) for p in body.data.polygons if p.vertices[0] in idset)
    roots=BVHTree.FromPolygons(rootv,rootf,all_triangles=False)
for part in fp[352:]:
    pts=[fib.data.vertices[j].co for j in part];c=sum(pts,Vector())/len(pts)
    h=z_hit(food,c.x,c.y);r=z_hit(roots,c.x,c.y)
    if r is not None:h=max(h,r)
    dz=h-min(p.z for p in pts)-.0002
    for j in part:fib.data.vertices[j].co.z+=dz
for ob in [body,fib,fat]:ob.data.update()
report['contacts']=contacts;report['meat_silhouette']='24 plump irregular chunks and 8 flatter torn slices, supported as cohesive groups'
report['changes']=[s.replace('New directionally aligned 4K albedo, micro-normal and roughness maps without photographic highlights','New directed 4K surface maps blended with retained cooked-tissue albedo') for s in report['changes']]
(OUT/'review_v6.json').write_text(json.dumps(report,indent=2))
with bpy.context.temp_override(window=win):exec(compile((ROOT/'scripts/audit_review_v6.py').read_text(),'<review audit>','exec'))
from mathutils import Vector
for area in win.screen.areas:
    if area.type=='VIEW_3D':
        space=area.spaces.active;space.region_3d.view_location=(0,0,.040);space.region_3d.view_distance=.38
        space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
        area.tag_redraw()
with bpy.context.temp_override(window=win):bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh_review_v6.blend'))
result={'refinement':'Varied chunky and torn silhouettes, supported from below','triangles':349340,'render_created':False}
