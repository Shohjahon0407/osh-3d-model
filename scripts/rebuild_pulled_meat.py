"""Rebuild meat as torn muscle fascicles rather than texture-covered slabs.

Keep the existing 4K color source. The silhouette, clefts, fanned ends, loose
shreds, contact placement and fat pockets are real mesh geometry.
Run through MCP against the current ToyOsh file; v2 is archived separately.
"""
import bpy, bmesh, pathlib, ast, math, random, json, hashlib, struct, zlib
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT=ROOT/'output/toyosh';TEX=OUT/'textures'
scene=bpy.data.scenes['ToyOsh']
win=bpy.data.window_managers[0].windows[0];win.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
random.seed(27102731)
tree=ast.parse((ROOT/'scripts/build_toyosh.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in {'Mesh','ellipsoid','png'}],type_ignores=[]),'<mesh tools>','exec'))
names={'05_Slow_Cooked_Meat_Pieces','06_Torn_Meat_Fibers','07_Gelatinous_Fat_Seams'}

def fingerprint(ob):
    values=np.empty(len(ob.data.vertices)*3,np.float32)
    ob.data.vertices.foreach_get('co',values)
    return hashlib.sha256(values.tobytes()).hexdigest()

before={o.name:fingerprint(o) for o in asset.objects if o.name not in names}
cut=bpy.data.materials['ToyOsh_Cooked_Meat_4K_Cut']
crust=bpy.data.materials['ToyOsh_Cooked_Meat_4K_Braised_Exterior']
fat_mat=bpy.data.materials['ToyOsh_Rendered_Gelatin_Fat_4K']
# Moist meat reflects in broken patches. A continuous thick coat contributed
# to the wrapped appearance; keep most of the oily response in the roughness map.
cut.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.15
crust.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.11
fat_mat.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value=.32

for name in names:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)

body=Mesh('05_Slow_Cooked_Meat_Pieces',[cut,crust])
frays=Mesh('06_Torn_Meat_Fibers',[cut,crust])
fat_mesh=Mesh('07_Gelatinous_Fat_Seams',[fat_mat,bpy.data.materials['ToyOsh_rice_cream']])

def bvh_from_objects(objects):
    verts=[];faces=[]
    for ob in objects:
        if ob.type!='MESH':continue
        start=len(verts);ob.data.calc_loop_triangles()
        verts.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices)
        faces.extend(tuple(start+i for i in tri.vertices) for tri in ob.data.loop_triangles)
    return BVHTree.FromPolygons(verts,faces,all_triangles=True)

floor_bvh=bvh_from_objects(list(asset.objects))
meat_bvh=None
def ray_z(tree,x,y):
    if tree is None:return None
    p,normal,index,distance=tree.ray_cast(Vector((x,y,.20)),Vector((0,0,-1)))
    return p.z if p is not None else None

def support_z(x,y,include_meat=True):
    vals=[ray_z(floor_bvh,x,y)]
    if include_meat:vals.append(ray_z(meat_bvh,x,y))
    vals=[v for v in vals if v is not None]
    return max(vals) if vals else .006

def update_meat_bvh():
    global meat_bvh
    if body.faces:
        meat_bvh=BVHTree.FromPolygons(body.verts,body.faces,all_triangles=False)

def smooth_floor(x,y,include_meat=True):
    # Small footprint averages rice grain spikes while respecting the heap below.
    return sum(support_z(x+dx,y+dy,include_meat) for dx,dy in
               [(0,0),(.0012,0),(-.0012,0),(0,.0012),(0,-.0012)])/5

# A fascicle is a flattened, bending, torn solid. Primary cross-sections have
# two raised lips and a true central cleft; their silhouette has no outer skin.
PROFILE8=[(1,0),(.70,.83),(0,.55),(-.70,.77),(-1,-.05),(-.65,-.67),(0,-1),(.65,-.72)]
PROFILE6=[(1,0),(.45,.88),(-.55,.73),(-1,-.06),(-.42,-.87),(.57,-.72)]
PROFILE4=[(1,0),(0,1),(-1,0),(0,-1)]

def sweep(length,width,depth,rings=7,sides=8,seed=0,fan=0,bend=0,sag=0,uv_origin=(.1,.2),zoffset=0):
    """Local long axis is X. Width/depth are half-extents, units are meters."""
    rr=random.Random(seed)
    profile={8:PROFILE8,6:PROFILE6,4:PROFILE4}[sides]
    phase=rr.uniform(0,6.28)
    vertices=[];uv=[];faces=[];bottom=[]
    widths=[rr.uniform(.58,.95)]+[rr.uniform(.74,1.20) for _ in range(rings-2)]+[rr.uniform(.08,.31)]
    for j in range(rings):
        t=j/(rings-1);xx=(t-.5)*length
        # Separation increases at the torn ends, while the middle remains joined.
        cy=fan*t*t*1.7 + bend*math.sin(math.pi*t)
        cz=zoffset+sag*math.sin(math.pi*t)+.00025*math.sin(t*9+phase)
        for k,(py,pz) in enumerate(profile):
            irregular=1+.13*math.sin(j*2.13+k*1.73+phase)
            wy=width*widths[j]*irregular
            dz=depth*(.68+.32*widths[j])*(1+.14*math.cos(j*1.8+k*2.7+phase))
            # Jagged severed tips avoid a clean flat extrusion cap.
            tip=.00045*math.sin(k*2.31+phase) if j in (0,rings-1) else 0
            roll=.22*math.sin(t*math.pi+phase)
            yy=py*wy;zz=pz*dz
            vertices.append((xx+tip,cy+yy*math.cos(roll)-zz*math.sin(roll),
                             cz+yy*math.sin(roll)+zz*math.cos(roll)))
            uv.append((uv_origin[0]+(xx+length*.5)/.065,
                       uv_origin[1]+(cy+py*wy)/.065))
            if pz<-.05:bottom.append(len(vertices)-1)
    for j in range(rings-1):
        for k in range(sides):
            a=j*sides+k;b=j*sides+(k+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(tuple(range(sides)))),tuple((rings-1)*sides+k for k in range(sides))])
    return vertices,faces,uv,bottom

def transform_component(component,cx,cy,angle,along=0,across=0):
    verts,faces,uv,bottom=component
    c=math.cos(angle);s=math.sin(angle)
    transformed=[]
    for x,y,z in verts:
        x+=along;y+=across
        transformed.append((cx+x*c-y*s,cy+x*s+y*c,z))
    return [transformed,faces,uv,bottom]

def torn_root(axes,seed,uv_origin):
    """Sculpt a small fractured muscle mass with real longitudinal clefts."""
    bm=bmesh.new()
    bmesh.ops.create_icosphere(bm,subdivisions=3,radius=1)
    bm.verts.index_update()
    verts=[];uv=[];bottom=[]
    phase=seed*.91
    for vert in bm.verts:
        x,y,z=vert.co
        angle=math.atan2(z,y)
        # Clefts run along the muscle axis and grow toward the pulled end.
        clefts=(max(0,math.cos(angle*5+.45*math.sin(x*4+phase)))**8)
        tear=(.09+.17*max(0,x+.25))*clefts
        rough=.085*math.sin(y*10+z*5+phase)*math.sin(x*5-z*9)
        rough+=.045*math.sin(x*17+y*13-z*11+phase)
        radial=max(.62,1+rough-tear)
        xx=x*axes[0]*(1+.06*math.sin(y*8+phase))
        yy=y*axes[1]*radial
        zz=z*axes[2]*radial
        # Uneven broken lobes rather than the clean outline of an extruded slice.
        xx-=axes[0]*.075*math.sin(y*12+z*9+phase)*max(0,x)
        verts.append((xx,yy,zz+.0003))
        uv.append((uv_origin[0]+(xx+axes[0])/.065,uv_origin[1]+yy/.065))
        if zz<0:bottom.append(len(verts)-1)
    faces=[tuple(v.index for v in face.verts) for face in bm.faces]
    bm.free()
    return verts,faces,uv,bottom

# Hand-arranged parent clumps follow the references: an uneven central pile,
# several smaller pieces off the pile and a long torn piece near the front.
# Each clump is made from joined fascicles, without a wrapper mesh or hidden slab.
clusters=[
    (-.006,.052,.037,.020,-.55,.012),
    (-.026,.024,.033,.019,.45,.012),
    (.014,.025,.031,.019,.88,.013),
    (.029,-.009,.028,.018,.82,.012),
    (-.012,-.005,.033,.021,-.25,.014),
    (-.028,-.030,.027,.018,.35,.012),
    (.010,-.037,.030,.020,-.40,.012),
    (-.080,.028,.025,.015,-1.0,.010),
    (-.052,-.015,.025,.015,.70,.010),
    (.026,-.079,.031,.010,1.38,.008),
    (.047,.036,.021,.014,1.0,.009),
    (-.046,.058,.022,.015,-.20,.009),
    (-.056,-.054,.020,.015,-.50,.008),
    (.046,-.047,.023,.014,.80,.009),
    (.003,.000,.023,.016,-1.05,.011),
    (-.004,-.060,.024,.016,.45,.009),
]
contact_report=[];primary_count=0;secondary_count=0;core_count=0
for ci,(cx,cy,L,W,angle,H) in enumerate(clusters):
    components=[];anchor_ids=[]
    u0=random.uniform(.04,.29);v0=random.uniform(.20,.65)
    # A broken inner muscle root holds the fascicles together. It occupies only
    # the root/middle of the piece and does not enclose the fanned tips or gaps.
    core_rich=ci in [0,1,2,3,4,6,8,14]
    core_axes=(L*(.37 if core_rich else .19),W*(.43 if core_rich else .22),H*(.50 if core_rich else .31))
    rootx=cx-math.cos(angle)*L*.13;rooty=cy-math.sin(angle)*L*.13
    cv,cf,cuv,core_bottom=torn_root(core_axes,ci+80,(u0,v0))
    core=transform_component((cv,cf,cuv,core_bottom),rootx,rooty,angle)
    components.append((core,0 if ci%3 else 1,True));core_count+=1
    for k in range(3):
        offset=([-.48,.06,.48][k]*.5+random.uniform(-.045,.045))*W
        length=L*random.uniform(.28,.58) if core_rich else L*random.uniform(.56,1.13)
        width=W*random.uniform(.09,.145) if core_rich else W*random.uniform(.135,.17)
        depth=H*random.uniform(.13,.20) if core_rich else H*random.uniform(.24,.31)
        fan=math.copysign(random.uniform(.0003,.0010) if core_rich else random.uniform(.0008,.0024),offset)
        comp=sweep(length,width,depth,rings=6,sides=8,seed=ci*100+k,
                   fan=fan,bend=random.uniform(-.001,.001),sag=random.uniform(-.0007,.0007),
                   uv_origin=(u0,v0+offset/.065),zoffset=(H*.40 if core_rich else 0)+random.uniform(-.0005,.001))
        comp=transform_component(comp,cx,cy,angle+random.uniform(-.20,.20),
                                 along=(L*.18 if core_rich else 0)+random.uniform(-.0035,.0035),across=offset)
        components.append((comp,1 if (ci+k)%6==0 else 0,True))
        primary_count+=1
    for k in range(3):
        offset=random.uniform(-.46,.46)*W
        length=L*random.uniform(.30,.75) if core_rich else L*random.uniform(.45,1.12)
        comp=sweep(length,W*random.uniform(.035,.075),H*random.uniform(.065,.12),
                   rings=6,sides=6,seed=ci*100+k+30,
                   fan=math.copysign(random.uniform(.0010,.0035),offset),
                   bend=random.uniform(-.0014,.0014),sag=random.uniform(-.0005,.0008),
                   uv_origin=(u0+random.uniform(0,.10),v0+offset/.065),
                   zoffset=H*(.48 if core_rich else .32)+random.uniform(-.0006,.0008))
        comp=transform_component(comp,cx,cy,angle+random.uniform(-.16,.16),
                                 along=(L*.21 if core_rich else 0)+random.uniform(-.004,.004),across=offset)
        components.append((comp,1 if (ci+k)%5==0 else 0,False))
        secondary_count+=1
    # Fit a support plane, then lower the complete cohesive clump onto actual
    # rice / previously placed meat. Small embedding represents compression.
    ax=math.cos(angle);ay=math.sin(angle)
    clump_roll=random.uniform(-.48,.48)
    for comp,mi,primary in components:
        vv,ff,uv,bottom=comp
        for i,(x,y,z) in enumerate(vv):
            along=(x-cx)*ax+(y-cy)*ay
            across=-(x-cx)*ay+(y-cy)*ax
            ac=across*math.cos(clump_roll)-z*math.sin(clump_roll)
            zz=across*math.sin(clump_roll)+z*math.cos(clump_roll)
            vv[i]=(cx+along*ax-ac*ay,cy+along*ay+ac*ax,zz)
    slope_a=(smooth_floor(cx+ax*L*.24,cy+ay*L*.24)-smooth_floor(cx-ax*L*.24,cy-ay*L*.24))/(L*.48)
    slope_b=(smooth_floor(cx-ay*W*.25,cy+ax*W*.25)-smooth_floor(cx+ay*W*.25,cy-ax*W*.25))/(W*.50)
    slope_a=max(-.42,min(.42,slope_a));slope_b=max(-.32,min(.32,slope_b))
    anchors=[]
    for comp,mi,primary in components:
        vv,ff,uv,bottom=comp
        for i,(x,y,z) in enumerate(vv):
            along=(x-cx)*ax+(y-cy)*ay;across=-(x-cx)*ay+(y-cy)*ax
            vv[i]=(x,y,z+along*slope_a+across*slope_b)
        if primary:anchors.extend(vv[i] for i in bottom)
    offsets=[support_z(x,y)-z for x,y,z in anchors]
    lift=max(offsets)-.00018
    contacts=sum(abs(lift-value)<.00075 for value in offsets)
    for comp,mi,primary in components:
        vv,ff,uv,bottom=comp
        vv=[(x,y,z+lift) for x,y,z in vv]
        body.add(vv,ff,uv,mi)
    update_meat_bvh()
    contact_report.append({'clump':ci,'support_contacts':contacts,'lift_m':lift,
                           'fascicles':6,'long_axis_rad':angle})

# Larger separated shreds around the main pile, all resting on the food below.
loose_count=0
for i in range(18):
    ci=[0,1,3,5,6,7,8,9,10,11,12,13,15,1,3,6,8,12][i]
    cx,cy,L,W,angle,H=clusters[ci]
    a=angle+random.uniform(-.8,.8)
    x=cx+random.choice([-1,1])*math.cos(a)*random.uniform(.010,.020)
    y=cy+random.choice([-1,1])*math.sin(a)*random.uniform(.008,.018)
    radius=math.sqrt((x/.11)**2+(y/.106)**2)
    if radius>1.03:x/=radius/1.01;y/=radius/1.01
    comp=sweep(random.uniform(.007,.017),random.uniform(.00065,.0015),random.uniform(.00045,.001),
               rings=6,sides=6,seed=6000+i,fan=random.uniform(-.001,.001),
               bend=random.uniform(-.001,.001),sag=-.0004,
               uv_origin=(random.uniform(.1,.4),random.uniform(.2,.7)))
    vv,ff,uv,bottom=transform_component(comp,x,y,a)
    lift=max(support_z(vv[j][0],vv[j][1])-vv[j][2] for j in bottom)-.00010
    vv=[(px,py,pz+lift) for px,py,pz in vv]
    body.add(vv,ff,uv,1 if i%4==0 else 0)
    update_meat_bvh();loose_count+=1

# Frayed tips branch out of actual flesh. They may hang from a joined root,
# with gravity sag; their endpoints cannot pass through the supporting rice.
fray_count=0
for i in range(120):
    ci=i%len(clusters)
    cx,cy,L,W,angle,H=clusters[ci]
    along=random.uniform(-.42,.42)*L;across=random.uniform(-.42,.42)*W
    ca=math.cos(angle);sa=math.sin(angle)
    x=cx+along*ca-across*sa;y=cy+along*sa+across*ca
    root,normal,_,_=meat_bvh.ray_cast(Vector((x,y,.20)),Vector((0,0,-1)))
    if root is None:
        root,normal,_,_=meat_bvh.ray_cast(Vector((cx,cy,.20)),Vector((0,0,-1)))
    if root is None:continue
    direction=angle+(math.pi if along<0 else 0)+random.uniform(-.28,.28)
    length=random.uniform(.003,.0085)
    width=random.uniform(.00012,.00032);depth=width*random.uniform(.42,.72)
    comp=sweep(length,width,depth,rings=4,sides=4,seed=8000+i,
               fan=random.uniform(-.0004,.0004),bend=random.uniform(-.0006,.0006),
               uv_origin=(random.uniform(.10,.55),random.uniform(.15,.75)))
    vv,ff,uv,bottom=comp
    transformed=[]
    for px,py,pz in vv:
        t=(px+length*.5)/length
        xx=root.x+(px+length*.5)*math.cos(direction)-py*math.sin(direction)
        yy=root.y+(px+length*.5)*math.sin(direction)+py*math.cos(direction)
        zz=root.z+pz+.000035-.0016*t*t
        # Only the free end needs a lower bound; the root embeds into its bundle.
        if t>.2:zz=max(zz,support_z(xx,yy,False)+depth*.4)
        transformed.append((xx,yy,zz))
    frays.add(transformed,ff,uv,1 if i%7==0 else 0)
    fray_count+=1

# Irregular small fat pockets are embedded in clumps, not spread as an outer film.
fat_count=0
for i,ci in enumerate([0,1,2,3,4,5,6,7,9,10,13,15]):
    cx,cy,L,W,a,H=clusters[ci]
    x=cx+random.uniform(-.004,.004);y=cy+random.uniform(-.003,.003)
    hit,normal,_,_=meat_bvh.ray_cast(Vector((x,y,.20)),Vector((0,0,-1)))
    if hit is None:continue
    hit.z-=.00035
    fat_mesh.add(*ellipsoid(tuple(hit),(random.uniform(.0021,.0038),random.uniform(.0011,.0018),random.uniform(.0008,.0013)),
                           a,segments=8,rings=5,seed=ci*.8,irregular=.46))
    fat_count+=1

# A few grains cling to moist torn surfaces, as in the supplied close-ups.
clinging_rice=0
for ci in range(12):
    cx,cy,L,W,a,H=clusters[ci]
    x=cx+random.uniform(-.004,.004);y=cy+random.uniform(-.003,.003)
    hit,norm,_,_=meat_bvh.ray_cast(Vector((x,y,.20)),Vector((0,0,-1)))
    if hit is None:continue
    if norm.z<0:norm=-norm
    rotate=Vector((0,0,1)).rotation_difference(norm)
    rv,rf,ruv=ellipsoid((0,0,0),(.0028,.00085,.00075),random.uniform(0,6.28),segments=8,rings=4)
    center=hit+norm*.00030
    rv=[tuple(rotate@Vector(v)+center) for v in rv]
    fat_mesh.add(rv,rf,ruv,1);clinging_rice+=1

created=[body.finish(),frays.finish(),fat_mesh.finish()]
for ob in created:
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    assert not any(not e.is_manifold for e in bm.edges),ob.name
    bm.to_mesh(ob.data);bm.free();ob.data.update()
    ob['detail_version']='Pulled cooked meat v3 / real fascicle geometry'
    ob['texture_resolution']=4096

# Remove the old meat print from the rice bed only, so gaps between the new
# fascicles reveal rice rather than the photograph of the former solid slabs.
bed_mat=bpy.data.materials['ToyOsh_Photo_Guided_Rice_Bed']
bsdf=bed_mat.node_tree.nodes.get('Principled BSDF')
node=bsdf.inputs['Base Color'].links[0].from_node
src_image=bpy.data.images.load(str(TEX/'meat_photo_basecolor.png'),check_existing=True)
w,h=src_image.size
buf=np.empty(w*h*4,np.float32);src_image.pixels.foreach_get(buf)
base=buf.reshape(h,w,4)[...,:3].copy();del buf
tile_image=bpy.data.images.load(str(TEX/'rice_bed_basecolor.png'),check_existing=True)
tw,th=tile_image.size
buf=np.empty(tw*th*4,np.float32);tile_image.pixels.foreach_get(buf)
tile=buf.reshape(th,tw,4)[...,:3].copy();del buf
Y,X=np.mgrid[0:h,0:w]
mask=np.zeros((h,w),bool)
tree=ast.parse((ROOT/'scripts/refine_toyosh.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name=='xy') or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='contours' for t in n.targets))],type_ignores=[]),'<old footprint masks>','exec'))
for points in contours:
    poly=[((.5+xy(px,py)[0]/.28)*w,(.5+xy(px,py)[1]/.28)*h) for px,py in points]
    inside=np.zeros_like(mask)
    for i,(x1,y1) in enumerate(poly):
        x2,y2=poly[(i+1)%len(poly)]
        inside^=((y1>Y)!=(y2>Y)) & (X<(x2-x1)*(Y-y1)/(y2-y1+1e-12)+x1)
    mask|=inside
for _ in range(6):mask=mask|np.roll(mask,1,0)|np.roll(mask,-1,0)|np.roll(mask,1,1)|np.roll(mask,-1,1)
feather=mask.astype(np.float32)
for _ in range(3):feather=(feather+np.roll(feather,1,0)+np.roll(feather,-1,0)+np.roll(feather,1,1)+np.roll(feather,-1,1))/5
tx=((X%180)/180*(tw-1)).astype(int);ty=((Y%150)/150*(th-1)).astype(int)
clean=base*(1-feather[:,:,None])+tile[ty,tx]*feather[:,:,None]
clean_path=TEX/'rice_bed_without_old_meat.png'
png(clean_path,clean)
clean_image=bpy.data.images.load(str(clean_path),check_existing=True);clean_image.pack()
node.image=clean_image

after={o.name:fingerprint(o) for o in asset.objects if o.name not in names}
assert before==after,'A non-meat mesh changed'
triangles=0
for ob in asset.objects:
    ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
assert triangles<=150000,triangles
zmax=max(v.co.z for ob in created for v in ob.data.vertices)
assert zmax<.105,zmax
scene['meat_detail_version']=3
scene['maximum_texture_dimension']=4096
scene['asset_notes']='Pulled cooked meat v3. No outer meat envelope: 16 clumps of fused/fanned muscle fascicles, 18 loose shreds, branching frayed tips, local fat pockets. Contact fitted to actual rice/meat supports. Existing 4K tissue maps retained.'
references=[
    '/home/shohjahon/Downloads/Ornate Plate of Hearty Pilaf.png',
    '/home/shohjahon/Downloads/Uzbek Plov with Tender Beef and Carrots.png',
    '/home/shohjahon/Downloads/Overhead Uzbek Plov with Braised Meat and Carrots.png',
    '/home/shohjahon/Downloads/Ornate Central Asian Pilaf Feast.png',
]
report={'version':3,'triangles':triangles,'parent_clumps':len(clusters),
        'inner_muscle_roots':core_count,
        'sculpted_fissured_roots':True,
        'primary_fascicles':primary_count,'secondary_fascicles':secondary_count,
        'loose_shreds':loose_count,'attached_fibers':fray_count,'fat_pockets':fat_count,
        'clinging_rice_grains':clinging_rice,
        'maximum_height_m':zmax,'non_meat_geometry_unchanged':before==after,
        'non_meat_parts_unchanged':False,
        'rice_bed_change':'Removed photographed old meat only beneath its old footprints; rice mesh and plate image unchanged.',
        'support_contacts':contact_report,'reference_images':references,
        'physics_method':'Static mesh contact fitting plus support-plane tilt; frayed tips rooted on actual meat and sagged toward the rice. No dynamic simulation.',
        'outer_wrapper_mesh':False}
(OUT/'meat_upgrade.json').write_text(json.dumps(report,indent=2))
(OUT/'meat_shape_v3.json').write_text(json.dumps(report,indent=2))
with bpy.context.temp_override(window=win):
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
result=report
