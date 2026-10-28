"""Upgrade only the meat, fibers and fatty seams of the open ToyOsh asset."""
import bpy, math, random, pathlib, json, ast, hashlib
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
import bmesh

ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT=ROOT/'output/toyosh';TEX=OUT/'textures'
scene=bpy.data.scenes['ToyOsh']
window=bpy.data.window_managers[0].windows[0]
window.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
random.seed(2710274)
tree=ast.parse((ROOT/'scripts/build_toyosh.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in {'Mesh','mound','ellipsoid'}],type_ignores=[]),'<mesh utilities>','exec'))
tree=ast.parse((ROOT/'scripts/refine_toyosh.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name=='xy') or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='contours' for t in n.targets))],type_ignores=[]),'<reference contours>','exec'))

meat_names={'05_Slow_Cooked_Meat_Pieces','06_Torn_Meat_Fibers','07_Gelatinous_Fat_Seams'}
def signature(ob):
    values=np.empty(len(ob.data.vertices)*3,np.float32)
    ob.data.vertices.foreach_get('co',values)
    return {'geometry_sha256':hashlib.sha256(values.tobytes()).hexdigest(),
            'materials':[m.name for m in ob.data.materials],
            'matrix':[list(r) for r in ob.matrix_world]}
before={o.name:signature(o) for o in asset.objects if o.name not in meat_names}

def image(name,data=False):
    suffix='.jpg' if name=='basecolor' else '.png'
    path=TEX/('cooked_meat_4k_'+name+suffix)
    im=bpy.data.images.load(str(path),check_existing=True)
    if data:im.colorspace_settings.name='Non-Color'
    assert tuple(im.size)==(4096,4096), (im.name,list(im.size))
    im.pack()
    return im

albedo=image('basecolor');normal=image('normal',True);orm=image('orm',True)
def meat_material(name,shade=1,coat=.16):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.diffuse_color=(.25*shade,.14*shade,.09*shade,1)
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    bsdf.inputs['IOR'].default_value=1.45
    bsdf.inputs['Coat Weight'].default_value=coat
    bsdf.inputs['Coat Roughness'].default_value=.20
    bsdf.inputs['Specular IOR Level'].default_value=.32
    c=nodes.new('ShaderNodeTexImage');c.image=albedo;c.label='4K cooked fibers / albedo'
    if shade!=1:
        mult=nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY'
        mult.inputs[0].default_value=1
        mult.inputs[2].default_value=(shade,shade*.97,shade*.94,1)
        links.new(c.outputs['Color'],mult.inputs[1])
        links.new(mult.outputs[0],bsdf.inputs['Base Color'])
    else:links.new(c.outputs['Color'],bsdf.inputs['Base Color'])
    p=nodes.new('ShaderNodeTexImage');p.image=orm;p.label='4K packed roughness'
    sep=nodes.new('ShaderNodeSeparateColor');links.new(p.outputs[0],sep.inputs[0])
    links.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
    links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
    n=nodes.new('ShaderNodeTexImage');n.image=normal;n.label='4K physical fibril normals'
    nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.62
    links.new(n.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
    mat['texture_resolution']=4096
    return mat

cut=meat_material('ToyOsh_Cooked_Meat_4K_Cut')
crust=meat_material('ToyOsh_Cooked_Meat_4K_Braised_Exterior',.68,.20)
fat_mat=bpy.data.materials.new('ToyOsh_Rendered_Gelatin_Fat_4K')
fat_mat.use_nodes=True
fat_bsdf=fat_mat.node_tree.nodes.get('Principled BSDF')
fat_bsdf.inputs['Base Color'].default_value=(.38,.265,.135,1)
fat_bsdf.inputs['Roughness'].default_value=.22
fat_bsdf.inputs['IOR'].default_value=1.45
fat_bsdf.inputs['Coat Weight'].default_value=.30
fat_bsdf.inputs['Coat Roughness'].default_value=.16
fn=fat_mat.node_tree.nodes.new('ShaderNodeTexImage');fn.image=normal
fm=fat_mat.node_tree.nodes.new('ShaderNodeNormalMap');fm.inputs['Strength'].default_value=.08
fat_mat.node_tree.links.new(fn.outputs['Color'],fm.inputs['Color'])
fat_mat.node_tree.links.new(fm.outputs['Normal'],fat_bsdf.inputs['Normal'])

for name in meat_names:
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)

meat=Mesh('05_Slow_Cooked_Meat_Pieces',[cut,crust])
fibers_mesh=Mesh('06_Torn_Meat_Fibers',[cut])
fat=Mesh('07_Gelatinous_Fat_Seams',[fat_mat])
piece_report=[]
fiber_count=0
N=48;R=6
for pi,points in enumerate(contours):
    poly=[Vector(xy(*p)) for p in points]
    center=sum(poly,Vector((0,0)))/len(poly)
    cx,cy=center
    arr=np.array([tuple(p-center) for p in poly])
    vals,vectors=np.linalg.eigh(arr.T@arr)
    major=Vector(vectors[:,np.argmax(vals)]);minor=Vector((-major.y,major.x))
    along=[(p-center).dot(major) for p in poly]
    across=[(p-center).dot(minor) for p in poly]
    amin,amax=min(along),max(along);bmin,bmax=min(across),max(across)
    u0=random.uniform(.025,.08);v0=random.uniform(.04,.13)
    uspan=random.uniform(.78,.88);vspan=random.uniform(.63,.74)
    def uv_for(px,py):
        q=Vector((px-cx,py-cy))
        return (u0+(q.dot(major)-amin)/(amax-amin)*uspan,
                v0+(q.dot(minor)-bmin)/(bmax-bmin)*vspan)
    lengths=[(poly[(i+1)%len(poly)]-p).length for i,p in enumerate(poly)]
    perimeter=sum(lengths);edge=[]
    for i in range(N):
        d=perimeter*i/N
        for k,length in enumerate(lengths):
            if d<=length:
                p=poly[k].lerp(poly[(k+1)%len(poly)],d/length)
                break
            d-=length
        edge.append(p)
    center_base=mound(cx,cy)-.001
    thick=[.012,.012,.011,.013,.012,.011,.010,.010,.013,.008,.018,.013][pi]
    def surface(px,py,rr):
        q=Vector((px-cx,py-cy));a=q.dot(major);b=q.dot(minor)
        # Broken 0.7–2 mm bundles affect silhouette; 4K normals carry finer fibrils.
        ridges=.00036*math.sin(b*3900+.45*math.sin(a*350))+.00020*math.sin(b*7300+a*200)
        breakup=.00050*math.sin(px*760+pi)*math.sin(py*1150+pi*.7)
        return center_base+thick*(1-.30*rr**3)+ridges+breakup
    verts=[(cx,cy,surface(cx,cy,0))];uv=[uv_for(cx,cy)];faces=[]
    for j in range(1,R+1):
        rr=j/R
        for i,p in enumerate(edge):
            wobble=1+.018*math.sin(i*2.21+pi)*rr*(1-rr)
            xx=cx+(p.x-cx)*rr*wobble;yy=cy+(p.y-cy)*rr*wobble
            verts.append((xx,yy,surface(xx,yy,rr)));uv.append(uv_for(xx,yy))
    for i in range(N):faces.append((0,1+i,1+(i+1)%N))
    for j in range(R-1):
        for i in range(N):
            a=1+j*N+i;b=1+j*N+(i+1)%N
            faces.append((a,a+N,b+N,b))
    top_bvh=BVHTree.FromPolygons(verts,faces,all_triangles=False)
    meat.add(verts,faces,uv,0)
    sv=[];suv=[];sf=[]
    for j in range(4):
        for i,p in enumerate(edge):
            rr=[1,1.006,.94,.83][j]
            if j==1:rr+=.012*math.sin(i*1.94+pi)
            xx=cx+(p.x-cx)*rr;yy=cy+(p.y-cy)*rr
            ztop=surface(p.x,p.y,1);bottom=mound(xx,yy)-.001
            zz=[ztop,ztop-.0018,bottom+.002,bottom][j]
            sv.append((xx,yy,zz))
            uu,vv=uv_for(p.x,p.y)
            suv.append((uu,vv-(ztop-zz)/max(thick,.004)*.23))
    for j in range(3):
        for i in range(N):
            a=j*N+i;b=j*N+(i+1)%N
            sf.append((a,b,b+N,a+N))
    sf.append(tuple(reversed(tuple(3*N+i for i in range(N)))))
    meat.add(sv,sf,suv,1)

    # Thin, attached muscle strands. Each control point is ray-fitted to the
    # actual cut mesh, preventing detached fibers floating over the surface.
    count=0;attempt=0
    while count<30 and attempt<160:
        attempt+=1
        p=edge[random.randrange(N)];rr=random.uniform(.20,.94)
        xx=cx+(p.x-cx)*rr;yy=cy+(p.y-cy)*rr
        length=random.uniform(.0018,.0065)
        direction=Vector((major.x,major.y,0))
        angle=random.uniform(-.18,.18)
        direction=Matrix.Rotation(angle,3,'Z')@direction
        cross=Vector((-direction.y,direction.x,0))
        path=[]
        radius=random.uniform(.000055,.000115)
        for j in range(3):
            t=j/2-.5
            pp=Vector((xx,yy,.12))+direction*(length*t)+cross*(math.sin((t+.5)*math.pi)*.00018)
            hit,norm,_,_=top_bvh.ray_cast(pp,Vector((0,0,-1)))
            if hit is None:break
            hit.z+=radius*.30
            path.append((hit,norm))
        if len(path)!=3:continue
        fv=[];fuv=[];ff=[]
        for j,(p,norm) in enumerate(path):
            for k in range(4):
                a=math.tau*k/4
                taper=.62 if j in (0,2) else 1
                q=p+cross*(math.cos(a)*radius*taper)+norm*(math.sin(a)*radius*taper)
                fv.append(tuple(q));fuv.append(uv_for(q.x,q.y))
        for j in range(2):
            for k in range(4):
                a=j*4+k;b=j*4+(k+1)%4
                ff.append((a,b,b+4,a+4))
        ff.extend([(3,2,1,0),(8,9,10,11)])
        fibers_mesh.add(fv,ff,fuv)
        count+=1;fiber_count+=1
    # A few raised gelatinous seams; broad fatty color/roughness variation lives
    # in the full 4K material instead of thick uniform bands.
    if pi in [0,1,3,4,6,10]:
        for k in range(2):
            p=edge[(pi*7+k*19)%N].lerp(center,.43)
            hit,norm,_,_=top_bvh.ray_cast(Vector((p.x,p.y,.12)),Vector((0,0,-1)))
            if hit is not None:
                hit.z+=.00014
                angle=math.atan2(major.y,major.x)
                fat.add(*ellipsoid(tuple(hit),(.0032,.00085,.00055),angle,segments=8,rings=4,seed=pi+k,irregular=.35))
    piece_report.append({'piece':pi,'fiber_direction':list(major),'attached_fibers':count})

new_objects=[meat.finish(),fibers_mesh.finish(),fat.finish()]
for ob in new_objects:
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
    bm.to_mesh(ob.data);bm.free();ob.data.update()
    ob['detail_version']='Cooked meat 4K v2'
    ob['texture_resolution']=4096
after={o.name:signature(o) for o in asset.objects if o.name not in meat_names}
assert before==after,'A non-meat mesh or material changed'
triangles=0
for ob in asset.objects:
    ob.data.calc_loop_triangles();triangles+=len(ob.data.loop_triangles)
assert triangles<=150000,triangles
scene['meat_detail_version']=2
scene['maximum_texture_dimension']=4096
scene['meat_material_resolution']='4096 x 4096'
scene['asset_notes']='Cooked meat v2: dedicated 4K PBR maps, directional cooked fibrils, braised exterior, oil/fat roughness, ray-fitted fine attached fiber geometry. Other food and porcelain unchanged.'
report={'version':2,'triangles':triangles,'attached_fibers':fiber_count,'pieces':piece_report,'non_meat_parts_unchanged':before==after,'maps':[albedo.filepath,normal.filepath,orm.filepath]}
(OUT/'meat_upgrade.json').write_text(json.dumps(report,indent=2))
with bpy.context.temp_override(window=window):
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
result=report
