"""Add supported, irregular meat clumps; retain 4K maps and visible rice detail."""
import sys
sys.path.insert(0,'/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/scripts')
from food_v4_utils import *
scene=bpy.data.scenes['ToyOsh'];bpy.context.window.scene=scene
asset=bpy.data.collections['ToyOsh_Asset'];random.seed(2710275)
body=bpy.data.objects['05_Slow_Cooked_Meat_Pieces']
fiber=bpy.data.objects['06_Torn_Meat_Fibers'];fat=bpy.data.objects['07_Gelatinous_Fat_Seams']
assert not scene.get('meat_quantity_version'), 'Already upgraded'
def signature(ob):
    a=np.asarray([tuple(ob.matrix_world@v.co) for v in ob.data.vertices],np.float32)
    return hashlib.sha256(a.tobytes()+topology_uv_hash(ob).encode()).hexdigest()
preserved={o.name:signature(o) for o in asset.objects if o.name!='09_Additional_Surface_Rice'}
parts=components(body);groups=[sum(parts[i*7:(i+1)*7],[]) for i in range(16)]+parts[112:]
roots=[parts[i*7] for i in range(16)];trees=[bvh_subset(body,g) for g in groups]
world={o.name:[o.matrix_world@v.co for v in o.data.vertices] for o in [body,fiber,fat]}
centers=[sum((world[body.name][j] for j in roots[i] if i<16),Vector())/len(roots[i]) for i in range(16)]
centers += [sum((world[body.name][j] for j in g),Vector())/len(g) for g in groups[16:]]
# Copy loop UVs without losing seams or material assignment.
face_cache={}
for ob in [body,fiber,fat]:
    face_cache[ob.name]=[(tuple(p.vertices),[tuple(ob.data.uv_layers.active.data[k].uv) for k in p.loop_indices],p.material_index) for p in ob.data.polygons]
def copy_part(builder,ob,ids,transform):
    ids=set(ids)
    for verts,uv,mat in face_cache[ob.name]:
        if verts[0] in ids:
            builder.add([tuple(transform@world[ob.name][j]) for j in verts],[tuple(range(len(verts)))],uv,mat)
def subset_geometry(ids,transform):
    lookup={j:i for i,j in enumerate(ids)};isect=set(ids)
    pts=[tuple(transform@world[body.name][j]) for j in ids]
    faces=[tuple(lookup[j] for j in p.vertices) for p in body.data.polygons if p.vertices[0] in isect]
    return pts,faces
base=bvh_objects([o for o in asset.objects if o.get('food_class')!=40])
rv=[];rf=[]
for ids in roots:
    p,f=subset_geometry(ids,Matrix.Identity(4));start=len(rv);rv.extend(p);rf.extend(tuple(start+j for j in q) for q in f)
root_tree=BVHTree.FromPolygons(rv,rf,all_triangles=False)
extra=MeshBuilder('11_Additional_Cooked_Meat',list(body.data.materials))
frays=MeshBuilder('12_Additional_Meat_Fibers',list(fiber.data.materials))
fats=MeshBuilder('13_Additional_Fat',list(fat.data.materials))
transforms={};support=[]
def place(gi,target,substantial):
    global root_tree
    c=centers[gi];ang=random.uniform(-2.5,2.5)
    scl=Matrix.Diagonal((random.uniform(.96,1.10),random.uniform(.94,1.08),random.uniform(.96,1.06),1))
    shape=Matrix.Rotation(ang,4,'Z')@scl@Matrix.Translation(-c)
    anchor=roots[gi] if substantial else groups[gi]
    best=None
    for attempt in range(7):
        x,y=target
        if attempt:
            a=math.atan2(y,x);x+=attempt*.006*math.cos(a);y+=attempt*.006*math.sin(a)
        transform=Matrix.Translation((x,y,0))@shape
        pts,faces=subset_geometry(anchor,transform)
        tree=BVHTree.FromPolygons(pts,faces,all_triangles=False)
        xs=[p[0] for p in pts];ys=[p[1] for p in pts];contacts=[]
        for sx in np.linspace(min(xs)+.0001,max(xs)-.0001,max(4,int((max(xs)-min(xs))/.0015))):
            for sy in np.linspace(min(ys)+.0001,max(ys)-.0001,max(4,int((max(ys)-min(ys))/.0015))):
                hit=tree.ray_cast(Vector((float(sx),float(sy),-.1)),Vector((0,0,1)))[0]
                if hit is None:continue
                z=z_hit(base,float(sx),float(sy));r=z_hit(root_tree,float(sx),float(sy))
                if z is None:continue
                if r is not None:z=max(z,r)
                contacts.append(z-hit.z)
        assert contacts
        lift=max(contacts)-(.00065 if substantial else .0002)
        candidate=Matrix.Translation((0,0,lift))@transform
        maxz=max((candidate@world[body.name][j]).z for j in groups[gi])
        if best is None or maxz<best[0]:best=(maxz,candidate,contacts,lift)
        if maxz<.086:break
    maxz,transform,contacts,lift=best
    copy_part(extra,body,groups[gi],transform);transforms[gi]=transform
    support.append({'source_group':gi,'new_center':list(transform@c),'maximum_z_m':maxz,'contact_samples':sum(abs(v-lift)<.0011 for v in contacts),'support':'rice/carrot or substantial meat root','embedding_m':.00065 if substantial else .0002})
    if substantial:
        p,f=subset_geometry(anchor,transform);offset=len(rv);rv.extend(p);rf.extend(tuple(offset+j for j in face) for face in f)
        root_tree=BVHTree.FromPolygons(rv,rf,all_triangles=False)
targets=[(-.045,.044),(.015,.058),(.050,.013),(-.048,.004),(-.027,.013),(.015,-.015),(.027,-.057),(-.014,-.054),(.048,-.024),(-.042,-.042),(.001,.031),(-.019,.045),(.024,.001),(-.018,-.021),(.003,.011),(.006,-.031)]
for i,xy in enumerate(targets):place((i*5+3)%16,xy,True)
for i in range(18):
    ang=i*2.399963+random.uniform(-.2,.2);r=random.uniform(.035,.073)
    place(16+i,(r*math.cos(ang),r*math.sin(ang)),False)
for ob,builder,step in [(fiber,frays,2),(fat,fats,1)]:
    for part in components(ob)[::step]:
        ids=part[:4] if ob==fiber else part
        center=sum((world[ob.name][j] for j in ids),Vector())/len(ids)
        gi=min(range(len(trees)),key=lambda i:trees[i].find_nearest(center)[3])
        copy_part(builder,ob,part,transforms[gi])
new_objects=[extra.finish(asset,40),frays.finish(asset,40),fats.finish(asset,40)]
print('MEAT_V5_ADDED',sum(b.triangles for b in [extra,frays,fats]),flush=True)
# Identify inner rice grains actually visible from six directions. Only unseen
# interior grains may trade tessellation for the extra meat geometry.
inner=bpy.data.objects['09_Additional_Surface_Rice'];iparts=components(inner)
component_of={j:i for i,p in enumerate(iparts) for j in p}
vertices=[];faces=[];labels=[]
for ob in asset.objects:
    offset=len(vertices);ob.data.calc_loop_triangles()
    vertices.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices)
    for tri in ob.data.loop_triangles:
        faces.append(tuple(offset+j for j in tri.vertices));labels.append(component_of[tri.vertices[0]] if ob==inner else -1)
tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
visible=set();target=Vector((0,0,.035));views=[Vector((0,0,1)),Vector((.65,-.8,.8)).normalized()]
for x,y in [(0,-1),(0,1),(-1,0),(1,0)]:views.append(Vector((x*.966,y*.966,.259)))
for direction in views:
    right=Vector((0,0,1)).cross(direction)
    if right.length<.01:right=Vector((1,0,0))
    right.normalize();up=direction.cross(right).normalized()
    # Include the acceptance rays as well as the denser review grid. The grids
    # sample different grain gaps, so protecting only one misses visible grains.
    for resolution,halfwidth,halfheight,lookat in [(220,.14,.14,target),(112,.135,.13 if direction.z>.999 else .095,Vector((0,0,.027)))]:
        for py in np.linspace(-halfheight,halfheight,resolution):
            for px in np.linspace(-halfwidth,halfwidth,resolution):
                hit,normal,index,dist=tree.ray_cast(lookat+direction*.4+right*float(px)+up*float(py),-direction)
                if index is not None and labels[index]>=0:visible.add(labels[index])
print('MEAT_V5_VISIBLE_INNER',len(visible),flush=True)
del tree,vertices,faces,labels;gc.collect()
def triangles():
    total=0
    for ob in asset.objects:ob.data.calc_loop_triangles();total+=len(ob.data.loop_triangles)
    return total
before=triangles();needed=max(0,math.ceil((before-349700)/8))
eligible=[i for i in range(len(iparts)) if i not in visible]
eligible.sort(key=lambda i:sum(inner.data.vertices[j].co.z for j in iparts[i])/len(iparts[i]))
selected=set(eligible[:needed]);builder=MeshBuilder('09_Additional_Surface_Rice',list(inner.data.materials))
vertuv={}
for p in inner.data.polygons:
    for j,k in zip(p.vertices,p.loop_indices):vertuv.setdefault(j,tuple(inner.data.uv_layers.active.data[k].uv))
material_by_comp={component_of[p.vertices[0]]:p.material_index for p in inner.data.polygons}
compfaces={i:[] for i in range(len(iparts))}
for p in inner.data.polygons:compfaces[component_of[p.vertices[0]]].append(p)
for ci,part in enumerate(iparts):
    if ci not in selected:
        for p in compfaces[ci]:
            ids=list(p.vertices);uv=[tuple(inner.data.uv_layers.active.data[k].uv) for k in p.loop_indices]
            builder.add([tuple(inner.data.vertices[j].co) for j in ids],[tuple(range(len(ids)))],uv,p.material_index)
    else:
        points=np.array([tuple(inner.data.vertices[j].co) for j in part]);center=points.mean(axis=0)
        eigval,eigvec=np.linalg.eigh((points-center).T@(points-center));axis=eigvec[:,2];u=eigvec[:,0];v=eigvec[:,1]
        order=np.argsort((points-center)@axis);pole0=int(order[0]);pole1=int(order[-1])
        ring0=list(map(int,order[1:6]));ring1=list(map(int,order[6:11]))
        angle=lambda j:math.atan2(float((points[j]-center)@v),float((points[j]-center)@u))
        ring0.sort(key=angle);r0=[ring0[k] for k in [0,2,4]]
        r1=[]
        for j in r0:
            best=min((k for k in ring1 if k not in r1),key=lambda k:abs(math.atan2(math.sin(angle(k)-angle(j)),math.cos(angle(k)-angle(j)))))
            r1.append(best)
        chosen=[pole0]+r0+r1+[pole1];vs=points[chosen];vs+=center-vs.mean(axis=0)
        fs=[]
        for k in range(3):
            nxt=(k+1)%3
            fs.extend([(0,1+nxt,1+k),(1+k,1+nxt,4+nxt,4+k),(7,4+k,4+nxt)])
        builder.add(vs.tolist(),fs,[vertuv[part[j]] for j in chosen],material_by_comp[ci])
oldname=inner.name;bpy.data.objects.remove(inner,do_unlink=True)
newinner=builder.finish(asset,20);newinner.name=oldname;newinner['grain_count']=3000;newinner['hidden_grains_lod12']=len(selected)
# If six-view protection leaves too few candidates, simplify added meat only.
current=triangles()
if current>350000:
    ob=new_objects[0];ob.data.calc_loop_triangles();n=len(ob.data.loop_triangles)
    modifier=ob.modifiers.new('Budget extra meat only','DECIMATE');modifier.ratio=(n-(current-349700))/n
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=modifier.name)
assert triangles()<=350000
assert all(signature(bpy.data.objects[name])==s for name,s in preserved.items())
scene['meat_quantity_version']=5
scene['meat_main_clumps']=32;scene['meat_loose_shreds']=36
report={'version':5,'added_main_clumps':16,'total_main_clumps':32,'added_loose_shreds':18,'total_loose_shreds':36,'added_fine_frays':60,'total_fine_frays':180,'original_objects_preserved':preserved,'meat_4k_maps':'unchanged; shared original material/UV maps','rice_grain_count':10000,'hidden_rice_grains_simplified':len(selected),'visible_inner_grains_protected':len(visible),'triangles':triangles(),'support':support,'maximum_meat_z_m':max(p['maximum_z_m'] for p in support)}
(OUT/'meat_quantity_v5.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
print('MEAT_V5_DONE',json.dumps({k:v for k,v in report.items() if k not in ['support','original_objects_preserved']}),flush=True)
