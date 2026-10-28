"""Geometry/material utilities for the dense rice and cooked-carrot revision."""
import bpy, bmesh, math, pathlib, random, json, hashlib, struct, zlib, gc
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT=ROOT/'output/toyosh';TEX=OUT/'textures'

def png(path,values):
    a=(np.clip(values,0,1)*255+.5).astype(np.uint8)
    if a.ndim==2:a=np.repeat(a[:,:,None],3,axis=2)
    h,w,n=a.shape
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=b''.join(b'\0'+row.tobytes() for row in a[::-1])
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2 if n==3 else 6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))

class MeshBuilder:
    def __init__(self,name,materials):
        self.name=name;self.materials=materials
        self.vertices=[];self.faces=[];self.uv=[];self.material_ids=[]
        self.triangles=0
    def add(self,vertices,faces,uv,material=0):
        start=len(self.vertices)
        self.vertices.extend(vertices)
        for f in faces:
            self.faces.append(tuple(start+i for i in f))
            self.uv.extend(uv[i] for i in f)
            self.material_ids.append(material)
            self.triangles+=len(f)-2
    def finish(self,collection,semantic):
        mesh=bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.vertices,[],self.faces)
        for m in self.materials:mesh.materials.append(m)
        mesh.update()
        mesh.polygons.foreach_set('use_smooth',[True]*len(mesh.polygons))
        mesh.polygons.foreach_set('material_index',self.material_ids)
        layer=mesh.uv_layers.new(name='UVMap')
        layer.data.foreach_set('uv',np.asarray(self.uv,np.float32).ravel())
        bm=bmesh.new();bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4])
        bm.to_mesh(mesh);bm.free();mesh.update()
        ob=bpy.data.objects.new(self.name,mesh);collection.objects.link(ob)
        ob['food_class']=semantic;ob.pass_index=semantic
        return ob

def components(ob):
    adj=[[] for _ in ob.data.vertices]
    for e in ob.data.edges:
        a,b=e.vertices;adj[a].append(b);adj[b].append(a)
    seen=set();result=[]
    for i in range(len(adj)):
        if i in seen:continue
        seen.add(i);stack=[i];part=[]
        while stack:
            v=stack.pop();part.append(v)
            for j in adj[v]:
                if j not in seen:seen.add(j);stack.append(j)
        result.append(sorted(part))
    return result

def bvh_objects(objects,semantic=False):
    vertices=[];faces=[];labels=[]
    for ob in objects:
        if ob.type!='MESH':continue
        mesh=ob.data;mesh.calc_loop_triangles();offset=len(vertices)
        vertices.extend(tuple(ob.matrix_world@v.co) for v in mesh.vertices)
        faces.extend(tuple(offset+i for i in t.vertices) for t in mesh.loop_triangles)
        if semantic:labels.extend([int(ob.get('food_class',50))]*len(mesh.loop_triangles))
    tree=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    return (tree,labels) if semantic else tree

def bvh_subset(ob,indices):
    ids=set(indices);lookup={j:i for i,j in enumerate(indices)}
    vertices=[tuple(ob.matrix_world@ob.data.vertices[j].co) for j in indices]
    faces=[tuple(lookup[j] for j in p.vertices) for p in ob.data.polygons if all(j in ids for j in p.vertices)]
    return BVHTree.FromPolygons(vertices,faces,all_triangles=False)

def z_hit(tree,x,y,up=False):
    p,n,i,d=tree.ray_cast(Vector((x,y,-.01 if up else .20)),Vector((0,0,1 if up else -1)))
    return p.z if p is not None else None

def topology_uv_hash(ob):
    a=np.empty(len(ob.data.loops),np.int32);ob.data.loops.foreach_get('vertex_index',a)
    b=np.empty(len(ob.data.uv_layers.active.data)*2,np.float32)
    ob.data.uv_layers.active.data.foreach_get('uv',b)
    return hashlib.sha256(a.tobytes()+b.tobytes()).hexdigest()

def make_pbr(name,basecolor,normal,orm,normal_strength=.1,coat=.045):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    bsdf.inputs['IOR'].default_value=1.46
    bsdf.inputs['Specular IOR Level'].default_value=.30
    bsdf.inputs['Coat Weight'].default_value=coat
    bsdf.inputs['Coat Roughness'].default_value=.28
    for suffix,path,data in [('Color',basecolor,False),('Normal',normal,True),('ORM',orm,True)]:
        image=bpy.data.images.load(str(path),check_existing=True)
        if data:image.colorspace_settings.name='Non-Color'
        image.pack()
        node=nodes.new('ShaderNodeTexImage');node.image=image
        if suffix=='Color':links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
        elif suffix=='Normal':
            nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=normal_strength
            links.new(node.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
        else:
            sep=nodes.new('ShaderNodeSeparateColor');links.new(node.outputs['Color'],sep.inputs['Color'])
            links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
    return m

def bake_food_materials():
    rng=np.random.default_rng(2710274)
    v,u=np.mgrid[0:1:1024j,0:1:1024j].astype(np.float32)
    noise=rng.normal(0,1,u.shape).astype(np.float32)
    tau=math.tau
    paths={}
    for kind in ['rice','carrot']:
        if kind=='rice':
            crease=np.exp(-((v-.28)/.055)**2)*np.sin(math.pi*u)**2
            h=.014*noise-.15*crease+.018*np.sin(tau*(u*3+v*2))
            rough=np.clip(.37+.035*np.sin(tau*u*2)*np.cos(tau*v*3)-.075*np.maximum(0,np.sin(tau*(u*1.3+v))),.25,.47)
        else:
            h=.020*noise+.06*np.sin(tau*(v*13+.13*np.sin(tau*u*2)))
            rough=np.clip(.34+.035*np.sin(tau*(u*2+v))-.10*np.maximum(0,np.cos(tau*(u*1.8-v))),.22,.43)
        dy,dx=np.gradient(h)
        normal=np.stack((-dx*7,-dy*7,np.ones_like(h)),axis=2)
        normal/=np.linalg.norm(normal,axis=2)[:,:,None]
        npth=TEX/f'v4_{kind}_normal.png';opth=TEX/f'v4_{kind}_orm.png'
        png(npth,normal*.5+.5)
        png(opth,np.stack((np.ones_like(u),rough,np.zeros_like(u)),axis=2))
        paths[kind]=(npth,opth)
    rice=[]
    palette=[(.89,.80,.59),(.85,.72,.46),(.92,.85,.69),(.80,.65,.35),(.76,.58,.29)]
    for i,color in enumerate(palette):
        variation=1+.018*noise+.025*np.sin(tau*u*1.2)*np.sin(tau*v*2)
        end=1-.04*(np.abs(u-.5)*2)**4
        values=np.array(color,np.float32)[None,None,:]*(variation*end)[:,:,None]
        path=TEX/f'v4_rice_{i}_basecolor.png';png(path,values)
        rice.append(make_pbr(f'ToyOsh_v4_Rice_{i}',path,*paths['rice'],normal_strength=.10))
    carrot=[]
    for i,color in enumerate([(.80,.43,.035),(.72,.34,.018),(.72,.23,.020)]):
        variation=1+.040*np.sin(tau*(u*1.5+v*.4))+.015*noise
        values=np.array(color,np.float32)[None,None,:]*variation[:,:,None]
        path=TEX/f'v4_carrot_{i}_basecolor.png';png(path,values)
        carrot.append(make_pbr(f'ToyOsh_v4_Carrot_{i}',path,*paths['carrot'],normal_strength=.18,coat=.07))
    return rice,carrot
