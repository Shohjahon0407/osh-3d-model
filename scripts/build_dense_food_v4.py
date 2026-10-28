"""Dense six-layer cooked rice, soft carrots and supported preserved v3 meat.

Execute through Blender MCP after archiving the current scene. All dimensions
are meters. The full model budget is 350k triangles / 35 MiB.
"""
import pathlib
ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
exec(compile((ROOT/'scripts/food_v4_utils.py').read_text(),'<food utilities>','exec'))
scene=bpy.data.scenes['ToyOsh'];win=bpy.data.window_managers[0].windows[0];win.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
random.seed(27102740)
def progress(stage,**data):
    (OUT/'food_v4_progress.json').write_text(json.dumps({'stage':stage,**data}))
progress('capturing_existing_meat')
if scene.get('food_detail_version',0)>=4:
    raise RuntimeError('Use the archived v3 scene for a deterministic rebuild.')

# Capture actual current meat; do not regenerate its approved shape.
meat=bpy.data.objects['05_Slow_Cooked_Meat_Pieces']
meat_parts=components(meat)
assert len(meat_parts)==130 and [len(p) for p in meat_parts[:7]]==[162,48,48,48,36,36,36]
groups=[sum(meat_parts[i*7:(i+1)*7],[]) for i in range(16)]+meat_parts[112:]
roots=[meat_parts[i*7] for i in range(16)]
old_trees=[bvh_subset(meat,part) for part in groups]
old_world={o.name:[o.matrix_world@v.co for v in o.data.vertices] for o in
           [meat,bpy.data.objects['06_Torn_Meat_Fibers'],bpy.data.objects['07_Gelatinous_Fat_Seams']]}
old_topology={o.name:topology_uv_hash(o) for o in
              [meat,bpy.data.objects['06_Torn_Meat_Fibers'],bpy.data.objects['07_Gelatinous_Fat_Seams']]}
child_assignment={}
for ob in [bpy.data.objects['06_Torn_Meat_Fibers'],bpy.data.objects['07_Gelatinous_Fat_Seams']]:
    assignments=[]
    for part in components(ob):
        pts=old_world[ob.name]
        anchor=sum((pts[j] for j in (part[:4] if ob.name.startswith('06_') else part)),Vector())/(4 if ob.name.startswith('06_') else len(part))
        distances=[tree.find_nearest(anchor)[3] for tree in old_trees]
        parent=min(range(len(groups)),key=lambda j:distances[j])
        assignments.append((part,parent))
    child_assignment[ob.name]=assignments

plate=bpy.data.objects['01_Handpainted_Porcelain_Lagan'];plate['food_class']=60;plate.pass_index=60
plate_tree=bvh_objects([plate]);plate_cache={}
def floor_z(x,y):
    key=(round(x/.0005),round(y/.0005))
    if key not in plate_cache:
        h=z_hit(plate_tree,key[0]*.0005,key[1]*.0005)
        plate_cache[key]=h if h is not None else .006
    return plate_cache[key]

def surface(x,y):
    q=(x/.118)**2+(y/.114)**2
    dome=max(0,1-q)
    lumps=.0012*(math.sin(x*95+y*39)+.55*math.sin(y*112-x*44))*dome
    return floor_z(x,y)+.037*dome**.60+lumps

def basis(x,y,angle,skirt=False):
    eps=.0005
    gx=max(-1.1,min(1.1,(surface(x+eps,y)-surface(x-eps,y))/(2*eps)))
    gy=max(-1.1,min(1.1,(surface(x,y+eps)-surface(x,y-eps))/(2*eps)))
    if skirt:angle=math.atan2(y,x)+math.pi*.5+random.uniform(-.45,.45)
    direction=Vector((math.cos(angle),math.sin(angle),gx*math.cos(angle)+gy*math.sin(angle)))
    direction.normalize()
    cross=Vector((0,0,1)).cross(direction).normalized()
    normal=direction.cross(cross).normalized()
    pitch=random.uniform(-.18,.18)
    direction2=direction*math.cos(pitch)+normal*math.sin(pitch)
    normal2=direction2.cross(cross).normalized()
    roll=random.uniform(-.50,.50)
    return direction2,cross*math.cos(roll)+normal2*math.sin(roll),normal2*math.cos(roll)-cross*math.sin(roll)

for name in ['02_Rice_Interior','03_Individual_Long_Grain_Rice','04_Braised_Yellow_and_Orange_Carrots','09_Additional_Surface_Rice']:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
rice_materials,carrot_materials=bake_food_materials()
progress('materials_ready')

# Closed interior is buried beneath several real grain layers, never a food photo.
core=MeshBuilder('02_Rice_Interior',[rice_materials[0]])
vertices=[(0,0,surface(0,0)-.009)];uv=[(.5,.5)];faces=[]
NR=10;NS=80
for j in range(1,NR+1):
    r=j/NR
    for i in range(NS):
        a=math.tau*i/NS;x=.109*r*math.cos(a);y=.105*r*math.sin(a)
        vertices.append((x,y,max(floor_z(x,y)+.0004,surface(x,y)-.009)))
        uv.append((.5+x/.024,.5+y/.024))
for i in range(NS):faces.append((0,1+i,1+(i+1)%NS))
for j in range(NR-1):
    for i in range(NS):
        a=1+j*NS+i;b=1+j*NS+(i+1)%NS
        faces.append((a,a+NS,b+NS,b))
bottom_ring=len(vertices)
for i in range(NS):
    a=math.tau*i/NS;x=.109*math.cos(a);y=.105*math.sin(a)
    vertices.append((x,y,floor_z(x,y)+.0002));uv.append((i/NS,0))
bottom=len(vertices);vertices.append((0,0,floor_z(0,0)+.0002));uv.append((.5,.5))
for i in range(NS):
    a=1+(NR-1)*NS+i;b=1+(NR-1)*NS+(i+1)%NS
    faces.append((a,b,bottom_ring+(i+1)%NS,bottom_ring+i))
    faces.append((bottom,bottom_ring+(i+1)%NS,bottom_ring+i))
core.add(vertices,faces,uv);core_ob=core.finish(asset,10)

# Rounded rectangular cross sections, unequal chopped ends and soft bends.
carrots=MeshBuilder('04_Braised_Yellow_and_Orange_Carrots',carrot_materials)
carrot_records=[]
profile=[(1,.55),(.55,1),(-.55,1),(-1,.55),(-1,-.55),(-.55,-1),(.55,-1),(1,-.55)]
for i in range(90):
    for attempt in range(100):
        rr=math.sqrt(random.uniform(.01,.94));a=random.uniform(0,math.tau)
        cx=.115*rr*math.cos(a);cy=.110*rr*math.sin(a)
        angle=random.uniform(0,math.tau);length=random.uniform(.012,.040)
        if all(((cx+t*length*math.cos(angle))/.119)**2+((cy+t*length*math.sin(angle))/.115)**2<1.01 for t in [-.5,.5]):break
    width=random.uniform(.003,.007);thickness=random.uniform(.002,.004)
    bend=random.uniform(-.004,.004);embed=random.uniform(-.0016,-.0001)
    verts=[];uv=[];faces=[];bottom_ids=[]
    first=random.uniform(.70,1.08);last=random.uniform(.48,1.03)
    for j in range(6):
        t=j/5;px=(t-.5)*length;curve=bend*math.sin(math.pi*t)
        shape=(first*(1-t)+last*t)*(.88+.16*math.sin(math.pi*t))
        for k,(py,pz) in enumerate(profile):
            yy=curve+py*width*.5*shape*(1+.07*math.sin(j*1.8+k+i))
            x=cx+px*math.cos(angle)-yy*math.sin(angle)
            y=cy+px*math.sin(angle)+yy*math.cos(angle)
            z=surface(x,y)+embed+pz*thickness*.5*(.88+.12*math.sin(j*2.1+i))
            verts.append((x,y,z));uv.append((t,k/8))
            if pz<0:bottom_ids.append(len(verts)-1)
    for j in range(5):
        for k in range(8):
            a=j*8+k;b=j*8+(k+1)%8;faces.append((a,b,b+8,a+8))
    faces.extend([tuple(reversed(tuple(range(8)))),tuple(40+k for k in range(8))])
    lift=max(0,max(floor_z(x,y)+.00008-z for x,y,z in verts))
    verts=[(x,y,z+lift) for x,y,z in verts]
    material=random.choices([0,1,2],[.60,.25,.15])[0]
    carrots.add(verts,faces,uv,material)
    carrot_records.append({'center':[cx,cy],'length_m':length,'width_m':width,'thickness_m':thickness,'material':material})
carrot_ob=carrots.finish(asset,30);carrot_tree=bvh_objects([carrot_ob])
progress('carrots_ready',carrots=90)

outer=MeshBuilder('03_Individual_Long_Grain_Rice',rice_materials)
inner=MeshBuilder('09_Additional_Surface_Rice',rice_materials)
gap_fill=MeshBuilder('10_Rice_Gap_Fill',rice_materials)
templates={}
def template(segments,rings):
    key=(segments,rings)
    if key in templates:return templates[key]
    vv=[];uv=[];ff=[]
    for j in range(rings+1):
        phi=math.pi*j/rings
        for i in range(segments+1):
            theta=math.tau*i/segments
            vv.append((math.cos(phi),math.sin(phi)*math.cos(theta),math.sin(phi)*math.sin(theta)))
            uv.append((j/rings,i/segments))
    for j in range(rings):
        for i in range(segments):
            a=j*(segments+1)+i;b=a+1;c=b+segments+1;d=a+segments+1
            ff.append((b,c,d) if j==0 else ((a,b,d) if j==rings-1 else (a,b,c,d)))
    templates[key]=(vv,ff,uv)
    return templates[key]

particles=[];spatial={};CELL=.0038
def crowded(center,axes,angle):
    x,y,z=center;key=(int(x/CELL),int(y/CELL),int(z/.0025))
    ca=math.cos(angle);sa=math.sin(angle)
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            for dz in [-1,0,1]:
                for n in spatial.get((key[0]+dx,key[1]+dy,key[2]+dz),[]):
                    q=particles[n];px=x-q[0];py=y-q[1];pz=z-q[2]
                    if abs(px)>.007 or abs(py)>.007 or abs(pz)>.0025:continue
                    along=px*ca+py*sa;across=-px*sa+py*ca
                    metric=(along/(.66*(axes[0]+q[3])))**2+(across/(.70*(axes[1]+q[4])))**2+(pz/(.84*(axes[2]+q[5])))**2
                    if metric<1:return True
    return False

def add_grain(builder,center,axes,frame,material,lod=36,record=True):
    unit,faces,uv=template(6,4) if lod==36 else template(5,3)
    a,b,c=axes;bx,by,bz=frame;bend=random.uniform(-.00030,.00030)
    asym=random.uniform(-.055,.055);vertices=[]
    for x,y,z in unit:
        xx=x*a
        yy=y*b*(1+asym*x)+bend*(1-x*x)
        zz=z*c*(.9 if z<0 else 1)+.00006*(1-x*x)
        vertices.append((center[0]+bx.x*xx+by.x*yy+bz.x*zz,
                         center[1]+bx.y*xx+by.y*yy+bz.y*zz,
                         center[2]+bx.z*xx+by.z*yy+bz.z*zz))
    lift=max(0,max(floor_z(x,y)+.00004-z for x,y,z in vertices))
    if lift:vertices=[(x,y,z+lift) for x,y,z in vertices]
    builder.add(vertices,faces,uv,material)
    if record:
        x,y,z=center;z+=lift
        particles.append((x,y,z,a,b,c))
        key=(int(x/CELL),int(y/CELL),int(z/.0025))
        spatial.setdefault(key,[]).append(len(particles)-1)

layer_spec=[(2600,0,36),(1900,.00115,36),(1400,.00230,36),
            (1400,.00345,20),(1000,.00460,20),(600,.00575,20)]
layer_report=[]
for layer,(count,depth,lod) in enumerate(layer_spec):
    accepted=0;attempts=0
    while accepted<count:
        attempts+=1
        if attempts>count*180:raise RuntimeError(f'Packing layer {layer}: {accepted}/{count}')
        rr=math.sqrt(random.random())*(.985 if layer<3 else .94)
        a=random.uniform(0,math.tau);x=.117*rr*math.cos(a);y=.113*rr*math.sin(a)
        z=surface(x,y)-depth+random.uniform(-.00030,.00090)
        axes=(random.uniform(.003,.004),random.uniform(.00090,.00125),random.uniform(.00065,.0010))
        if z-axes[2]<floor_z(x,y)+.00005:continue
        angle=random.uniform(0,math.tau)
        car_top=z_hit(carrot_tree,x,y)
        if car_top is not None:
            car_bottom=z_hit(carrot_tree,x,y,True)
            if z+axes[2]>car_bottom and z-axes[2]<car_top:
                if layer==0 and random.random()<.17:z=car_top+axes[2]*.85
                else:continue
        if crowded((x,y,z),axes,angle):continue
        add_grain(outer if lod==36 else inner,(x,y,z),axes,basis(x,y,angle),random.choices(range(5),[.34,.30,.16,.14,.06])[0],lod)
        accepted+=1
    layer_report.append({'layer':layer,'grains':accepted,'depth_m':depth,'triangles_per_grain':lod,'attempts':attempts})
    progress('packing_rice',layer=layer,grains=len(particles),attempts=attempts)

# Six hundred grains wrap the edge of the mound, providing side-view coverage.
for i in range(600):
    a=random.uniform(0,math.tau);rr=random.uniform(.88,1.008)
    x=.117*rr*math.cos(a);y=.113*rr*math.sin(a)
    top=surface(x,y);bottom=floor_z(x,y)+.00105
    z=random.uniform(bottom,max(bottom,top-.0004))
    axes=(random.uniform(.003,.004),random.uniform(.0009,.0012),random.uniform(.0007,.0010))
    add_grain(outer,(x,y,z),axes,basis(x,y,a,True),random.choices(range(5),[.32,.31,.18,.13,.06])[0])
layer_report.append({'layer':'edge','grains':600,'triangles_per_grain':36})
outer_ob=outer.finish(asset,20);inner_ob=inner.finish(asset,20)
outer_ob['grain_count']=6500;inner_ob['grain_count']=3000
print('FOOD_V4_PACKED',len(particles),flush=True)
progress('rice_mesh_ready',grains=len(particles))

# The rest of the script settles preserved food and checks actual visibility.
base_food=[plate,core_ob,outer_ob,inner_ob,carrot_ob]
food_tree=bvh_objects(base_food)

# Place existing chickpeas, raisins and cumin on/in the new rice surface.
garnish=bpy.data.objects['08_Chickpeas_Raisins_and_Cumin'];garnish['food_class']=50;garnish.pass_index=50
garnish_moves=[]
for part in components(garnish):
    points=[garnish.matrix_world@garnish.data.vertices[j].co for j in part]
    center=sum(points,Vector())/len(points)
    support=z_hit(food_tree,center.x,center.y)
    if support is None:continue
    bottom=min(p.z for p in points)
    embed=min(.0010,(max(p.z for p in points)-bottom)*.22)
    delta=support-bottom-embed
    local=garnish.matrix_world.inverted().to_3x3()@Vector((0,0,delta))
    for j in part:garnish.data.vertices[j].co+=local
    garnish_moves.append(delta)
garnish.data.update()
food_tree=bvh_objects(base_food+[garnish])

# Only substantial muscle roots may support another clump. The former use of
# single long thin tips as supports caused the visible hovering in low views.
root_vertices=[];root_faces=[];root_tree=None
displacements=[];contact_report=[]
root_centers=[]
for part in roots:
    pts=[old_world[meat.name][j] for j in part]
    root_centers.append(sum(pts,Vector())/len(pts))
order=sorted(range(16),key=lambda j:root_centers[j].z)+list(range(16,len(groups)))
deltas=[0.0]*len(groups)
for gi in order:
    anchor_ids=roots[gi] if gi<16 else groups[gi]
    anchor_tree=bvh_subset(meat,anchor_ids)
    points=[meat.matrix_world@meat.data.vertices[j].co for j in anchor_ids]
    xmin,xmax=min(p.x for p in points),max(p.x for p in points)
    ymin,ymax=min(p.y for p in points),max(p.y for p in points)
    nx=max(3,int((xmax-xmin)/.0015)+1);ny=max(3,int((ymax-ymin)/.0015)+1)
    anchors=[]
    for x in np.linspace(xmin+.0001,xmax-.0001,nx):
        for y in np.linspace(ymin+.0001,ymax-.0001,ny):
            bottom=z_hit(anchor_tree,float(x),float(y),True)
            if bottom is None:continue
            floor=z_hit(food_tree,float(x),float(y))
            if floor is None:continue
            if root_tree is not None:
                previous=z_hit(root_tree,float(x),float(y))
                if previous is not None:floor=max(floor,previous)
            anchors.append((float(x),float(y),floor-bottom))
    if not anchors:raise RuntimeError(f'No support footprint for preserved meat group {gi}')
    maximum=max(p[2] for p in anchors)
    embed=.00045 if gi<16 else .00016
    delta=maximum-embed
    contacts=[p for p in anchors if abs(delta-p[2])<.00085]
    if gi<16 and len(contacts)<3:
        embed=.00075;delta=maximum-embed
        contacts=[p for p in anchors if abs(delta-p[2])<.00105]
    assert contacts
    local=meat.matrix_world.inverted().to_3x3()@Vector((0,0,delta))
    for j in groups[gi]:meat.data.vertices[j].co+=local
    deltas[gi]=delta
    contact_report.append({'group':gi,'kind':'muscle_root' if gi<16 else 'loose_shred',
                           'vertical_translation_m':delta,'contacts':len(contacts),
                           'soft_embedding_m':embed,'support':'rice/carrot or substantial muscle root'})
    if gi<16:
        ids=roots[gi];lookup={j:i+len(root_vertices) for i,j in enumerate(ids)};idset=set(ids)
        root_vertices.extend(tuple(meat.matrix_world@meat.data.vertices[j].co) for j in ids)
        root_faces.extend(tuple(lookup[j] for j in p.vertices) for p in meat.data.polygons if all(j in idset for j in p.vertices))
        root_tree=BVHTree.FromPolygons(root_vertices,root_faces,all_triangles=False)
    displacements.append(delta)
meat.data.update();meat['food_class']=40;meat.pass_index=40

shape_error=0.0
for gi,part in enumerate(groups):
    for j in part:
        expected=old_world[meat.name][j]+Vector((0,0,deltas[gi]))
        shape_error=max(shape_error,(meat.matrix_world@meat.data.vertices[j].co-expected).length)
for name,assignments in child_assignment.items():
    ob=bpy.data.objects[name]
    for part,gi in assignments:
        local=ob.matrix_world.inverted().to_3x3()@Vector((0,0,deltas[gi]))
        for j in part:
            ob.data.vertices[j].co+=local
            expected=old_world[name][j]+Vector((0,0,deltas[gi]))
            shape_error=max(shape_error,(ob.matrix_world@ob.data.vertices[j].co-expected).length)
    ob.data.update();ob['food_class']=40;ob.pass_index=40
assert shape_error<2e-7,shape_error
assert all(topology_uv_hash(bpy.data.objects[name])==signature for name,signature in old_topology.items())
print('FOOD_V4_MEAT_SETTLED',max(abs(x) for x in deltas),flush=True)
progress('meat_settled',groups=len(groups))

def coverage_scan(resolution=112):
    tree,labels=bvh_objects(list(asset.objects),True)
    views=[('top',Vector((0,0,1))),('angle',Vector((.65,-.8,.8)).normalized()),
           ('front_low',Vector((0,-math.cos(math.radians(15)),math.sin(math.radians(15))))),
           ('back_low',Vector((0,math.cos(math.radians(15)),math.sin(math.radians(15))))),
           ('left_low',Vector((-math.cos(math.radians(15)),0,math.sin(math.radians(15))))),
           ('right_low',Vector((math.cos(math.radians(15)),0,math.sin(math.radians(15)))))]
    report=[];holes=[]
    target=Vector((0,0,.027))
    for name,direction in views:
        right=Vector((0,0,1)).cross(direction)
        if right.length<.001:right=Vector((1,0,0))
        right.normalize();up=direction.cross(right).normalized()
        camera=target+direction*.40
        exposed=0;food=0
        height=.26 if name=='top' else .19
        for py in np.linspace(-height/2,height/2,resolution):
            for px in np.linspace(-.135,.135,resolution):
                origin=camera+right*float(px)+up*float(py)
                hit,normal,index,distance=tree.ray_cast(origin,-direction)
                if hit is None:continue
                semantic=labels[index]
                if semantic!=60:food+=1
                if semantic==10:
                    exposed+=1;holes.append((tuple(hit),tuple(normal),tuple(direction)))
        report.append({'view':name,'food_rays':food,'exposed_core_rays':exposed,
                       'core_exposure_fraction':exposed/max(1,food)})
    del tree,labels;gc.collect()
    return report,holes

before_coverage,holes=coverage_scan()
adaptive_count=0;used=set()
for round_index in range(3):
    if not holes or adaptive_count>=500:break
    # Cover distinct real visibility holes, not arbitrary extra particles.
    random.shuffle(holes)
    for hit,normal,direction in holes:
        if adaptive_count>=500:break
        key=tuple(round(a/.0018) for a in hit)
        if key in used:continue
        used.add(key)
        n=Vector(normal)
        if n.z<-.1:n=-n
        center=Vector(hit)+n*.00065+Vector(direction)*.00018
        tangent=n.cross(Vector((1,0,0)))
        if tangent.length<.001:tangent=n.cross(Vector((0,1,0)))
        tangent.normalize();other=n.cross(tangent).normalized()
        angle=random.uniform(0,math.tau)
        bx=tangent*math.cos(angle)+other*math.sin(angle);by=n.cross(bx).normalized()
        add_grain(gap_fill,tuple(center),(random.uniform(.003,.004),random.uniform(.0010,.00125),.00085),
                  (bx,by,n),random.choices(range(5),[.34,.30,.16,.14,.06])[0])
        adaptive_count+=1
    previous=bpy.data.objects.get('10_Rice_Gap_Fill')
    if previous:bpy.data.objects.remove(previous,do_unlink=True)
    gap_ob=gap_fill.finish(asset,20);gap_ob['grain_count']=adaptive_count
    after_coverage,holes=coverage_scan()
    print('FOOD_V4_GAP_FILL',adaptive_count,[r['exposed_core_rays'] for r in after_coverage],flush=True)
    progress('filling_visibility_gaps',extra_grains=adaptive_count,core_rays=[r['exposed_core_rays'] for r in after_coverage])
if adaptive_count==0:after_coverage=before_coverage

for ob in asset.objects:
    if 'food_class' not in ob:ob['food_class']=50;ob.pass_index=50
triangles=0
for ob in asset.objects:
    ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
assert triangles<=350000,triangles
assert len(particles)==9500+adaptive_count
scene['food_detail_version']=4
scene['triangle_budget']=350000
scene['file_budget_mib']=35
scene['maximum_texture_dimension']=4096
scene['asset_notes']='v4 dense six-layer rice and soft cooked carrots. Existing v3 meat is rigidly translated onto rice or substantial roots; fine fibers cannot support a full clump. Meat topology, UVs and 4K texture files preserved.'
report={
    'version':4,'seed':27102740,'rice_grains':len(particles),'detailed_rice_grains':6500+adaptive_count,
    'inner_rice_grains':3000,'adaptive_grains':adaptive_count,'layers':layer_report,
    'carrots':carrot_records,'carrot_count':len(carrot_records),
    'triangles':triangles,'triangle_budget':350000,'file_budget_mib':35,
    'meat_shape_preserved':True,'meat_max_rigid_translation_error_m':shape_error,
    'meat_topology_and_uv_preserved':True,'meat_group_placement':contact_report,
    'garnish_vertical_translations_m':garnish_moves,
    'coverage_before':before_coverage,'coverage_after':after_coverage,
    'maximum_core_exposure_fraction':max(r['core_exposure_fraction'] for r in after_coverage),
    'grain_dimensions_m':{'length':[.006,.008],'width':[.0018,.0025],'thickness':[.0013,.002]},
    'new_material_max_texture_dimension':1024,
    'physics_method':'Deterministic multilayer packing, plate clearance, carrot interleaving and static root-footprint contact fitting; no dynamic simulation.'
}
(OUT/'food_v4.json').write_text(json.dumps(report,indent=2))
with bpy.context.temp_override(window=win):
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
progress('complete',grains=len(particles),triangles=triangles)
result={'version':4,'rice_grains':len(particles),'carrots':90,'triangles':triangles,
        'adaptive_grains':adaptive_count,'max_core_exposure':report['maximum_core_exposure_fraction'],
        'meat_shape_error_m':shape_error,'file':str(OUT/'toyosh.blend')}
