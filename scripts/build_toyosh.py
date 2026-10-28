"""Deterministic photo-guided, fully volumetric osh asset. Execute through MCP."""
import bpy
import math
import random
import json
import pathlib
import struct
import zlib
import numpy as np
from mathutils import Vector, Matrix

ROOT = pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT = ROOT / 'output/toyosh'
TEX = OUT / 'textures'
SOURCE = pathlib.Path('/home/shohjahon/BESHKASHTAN_RASMLARI/ofiyat rasmlari/toyosh.jpg')
OUT.mkdir(parents=True, exist_ok=True)
TEX.mkdir(exist_ok=True)
random.seed(271026)
rng = np.random.default_rng(271026)
if bpy.data.scenes.get('ToyOsh'):
    raise RuntimeError('ToyOsh already exists: do not overwrite an existing scene automatically.')

original = {s.name: {o.name: {'type': o.type, 'matrix': [list(r) for r in o.matrix_world]}
                      for o in s.objects} for s in bpy.data.scenes}
(OUT / 'original_scene_state.json').write_text(json.dumps(original, indent=2))
scene = bpy.data.scenes.new('ToyOsh')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene['reference_image'] = str(SOURCE)
scene['assumed_plate_diameter_m'] = 0.28
scene['reconstruction_limit'] = 'One photograph: hidden surfaces and heights are inferred.'
asset = bpy.data.collections.new('ToyOsh_Asset')
studio = bpy.data.collections.new('ToyOsh_Studio')
scene.collection.children.link(asset)
scene.collection.children.link(studio)


def png(path, values):
    """Bake a numeric material field into an ordinary sRGB/data PNG."""
    a = (np.clip(values, 0, 1) * 255 + .5).astype(np.uint8)
    if a.ndim == 2:
        a = np.repeat(a[..., None], 3, axis=2)
    h, w, channels = a.shape
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\0' + row.tobytes() for row in a[::-1])
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2 if channels == 3 else 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    return path


def normal_from_height(h, amount):
    dy, dx = np.gradient(h)
    n = np.stack((-dx * amount, -dy * amount, np.ones_like(h)), axis=2)
    n /= np.linalg.norm(n, axis=2)[..., None]
    return n * .5 + .5


def texture(name, size, kind, tint=None):
    """Evaluate procedural albedo, micro-normal and packed ORM at UV texels."""
    v, u = np.mgrid[0:1:complex(size), 0:1:complex(size)]
    fine = rng.normal(0, 1, (size, size))
    if kind == 'rice':
        h = .14*np.sin(u*math.tau*21 + 1.3*np.sin(v*math.tau*3)) + .07*fine
        shade = 1 + .025*fine + .02*np.sin(v*math.tau*5)
        color = np.array(tint)[None, None, :] * shade[..., None]
        rough = .29 + .035*fine
        strength = 1.5
    elif kind == 'carrot':
        h = .18*np.sin(v*math.tau*45 + 1.4*np.sin(u*math.tau*4)) + .065*fine
        shade = 1 + .05*np.sin(v*math.tau*8) + .018*fine
        color = np.array(tint)[None, None, :] * shade[..., None]
        rough = .31 + .035*fine
        strength = 5
    elif kind == 'meat':
        # Source meat interior only; remove broad illumination with a low-frequency
        # divisor, retaining fiber/color information rather than photographic shadows.
        source = bpy.data.images.load(str(SOURCE), check_existing=True)
        sw, sh = source.size
        pixels = np.empty(sw*sh*4, np.float32)
        source.pixels.foreach_get(pixels)
        pixels = pixels.reshape(sh, sw, 4)[..., :3]
        crop = pixels[sh-829:sh-750, 878:1020]
        yy = np.minimum((v*(crop.shape[0]-1)).astype(int), crop.shape[0]-1)
        xx = np.minimum((u*(crop.shape[1]-1)).astype(int), crop.shape[1]-1)
        photo = np.maximum(crop[yy, xx], .005)
        lum = photo.mean(axis=2)
        low = np.full_like(lum, lum.mean())
        # Low-frequency block smoothing with periodic rolls; normalize shadows.
        for off in (12, 24, 48, 96):
            lum = (lum + np.roll(lum, off, 0) + np.roll(lum, -off, 0)
                   + np.roll(lum, off, 1) + np.roll(lum, -off, 1))/5
        detail = np.clip(photo / np.maximum(lum[..., None], .015), .56, 1.55)
        warp = v + .012*np.sin(u*math.tau*3) + .005*np.sin(u*math.tau*11)
        fibers = np.sin(warp*math.tau*95 + .7*np.sin(u*math.tau*7))
        bundles = np.sin(warp*math.tau*18 + np.sin(u*math.tau*3))
        h = .32*fibers + .12*bundles + .07*fine + .19*detail.mean(axis=2)
        color = np.array(tint)[None, None, :] * detail**.55 * (1+.075*bundles[..., None]+.025*fibers[..., None])
        rough = .38 + .04*bundles + .03*fine
        strength = 12
    elif kind == 'fat':
        h = .15*np.sin(u*29 + np.sin(v*13)) + .08*fine
        color = np.array(tint)[None, None, :] * (1+.04*fine[..., None])
        rough = .26 + .025*fine
        strength = 3
    else:
        h = .1*fine
        color = np.array(tint)[None, None, :] * (1+.06*fine[..., None])
        rough = .43 + .03*fine
        strength = 3
    png(TEX / (name+'_basecolor.png'), color)
    png(TEX / (name+'_normal.png'), normal_from_height(h, strength))
    png(TEX / (name+'_orm.png'), np.stack((np.ones_like(h), np.clip(rough,.15,.7), np.zeros_like(h)), axis=2))


# UV-space ornamental porcelain: navy ground, ivory lobed flowers, thin gold lines.
size = 2048
y, x = np.mgrid[-.145:.145:complex(size), -.145:.145:complex(size)]
r = np.sqrt(x*x+y*y)
ivory = np.array([.89, .895, .84])
navy = np.array([.022, .031, .049])
gold = np.array([.79, .57, .24])
plate_color = np.broadcast_to(ivory, (size, size, 3)).copy()
band = r > .081
plate_color[band] = navy
gold_mask = np.zeros((size, size), bool)
for i in range(14):
    a = math.tau*i/14 + .09
    radial = x*math.cos(a)+y*math.sin(a)
    tang = -x*math.sin(a)+y*math.cos(a)
    # Three connected lobes resemble the hand-painted cotton/flower ornament.
    d1 = ((radial-.115)/.019)**2 + (tang/.0115)**2
    d2 = ((radial-.103)/.0125)**2 + ((tang-.0105)/.0095)**2
    d3 = ((radial-.103)/.0125)**2 + ((tang+.0105)/.0095)**2
    d = np.minimum(np.minimum(d1,d2),d3)
    petal = (d < 1) & band
    plate_color[petal] = ivory
    edge = (abs(d-1) < .065) & band
    gold_mask |= edge
    notch = (((radial-.092)/.011)**2+(tang/.0045)**2 < 1) & band
    plate_color[notch] = navy
gold_mask |= (abs(r-.136)<.0008) | (abs(r-.083)<.00045)
plate_color[gold_mask] = gold
plate_color *= (1 + .004*np.sin(x*920)*np.sin(y*1100))[...,None]
png(TEX/'porcelain_basecolor.png', plate_color)
png(TEX/'porcelain_orm.png', np.stack((np.ones_like(r), np.where(gold_mask,.24,.21), gold_mask.astype(float)*.82),axis=2))
textures = [
    ('rice_ivory',256,'rice',(.86,.77,.55)),
    ('rice_cream',256,'rice',(.94,.86,.66)),
    ('rice_golden',256,'rice',(.78,.65,.38)),
    ('rice_white',256,'rice',(.93,.89,.76)),
    ('carrot_yellow',512,'carrot',(.84,.51,.075)),
    ('carrot_orange',512,'carrot',(.79,.35,.065)),
    ('meat_cut',1024,'meat',(.43,.285,.25)),
    ('meat_crust',512,'meat',(.245,.125,.085)),
    ('fat',256,'fat',(.66,.51,.32)),
    ('chickpea',128,'fat',(.72,.48,.20)),
    ('raisin',128,'seed',(.095,.055,.028)),
]
for args in textures:
    texture(*args)


def load_tex(path, data=False):
    im = bpy.data.images.load(str(path), check_existing=True)
    if data:
        im.colorspace_settings.name = 'Non-Color'
    im.pack()
    return im


def pbr(name, textured=True, color=None, rough=.3, metal=0):
    m = bpy.data.materials.new('ToyOsh_'+name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if not textured:
        bsdf.inputs['Base Color'].default_value = (*color,1)
        return m
    c = nodes.new('ShaderNodeTexImage')
    c.image = load_tex(TEX/(name+'_basecolor.png'))
    links.new(c.outputs['Color'],bsdf.inputs['Base Color'])
    orm = nodes.new('ShaderNodeTexImage')
    orm.image = load_tex(TEX/(name+'_orm.png'), True)
    sep = nodes.new('ShaderNodeSeparateColor')
    links.new(orm.outputs['Color'],sep.inputs['Color'])
    links.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
    links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
    npth = TEX/(name+'_normal.png')
    if npth.exists():
        n = nodes.new('ShaderNodeTexImage')
        n.image = load_tex(npth, True)
        nm = nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = .36 if name.startswith('rice') else .6
        links.new(n.outputs['Color'],nm.inputs['Color'])
        links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
    return m


mats = {n:pbr(n) for n, *_ in textures}
mats['porcelain'] = pbr('porcelain')
mats['gold'] = pbr('gold',False,(.72,.48,.16),.22,.82)
mats['porcelain_bottom'] = pbr('porcelain_bottom',False,(.75,.76,.69),.23)


class Mesh:
    def __init__(self,name,materials):
        self.name=name
        self.verts=[]
        self.faces=[]
        self.uvs=[]
        self.ids=[]
        self.materials=materials

    def add(self,verts,faces,uvs,mat=0):
        start=len(self.verts)
        self.verts.extend(verts)
        for f in faces:
            self.faces.append(tuple(start+j for j in f))
            self.uvs.append([uvs[j] for j in f])
            self.ids.append(mat)

    def finish(self):
        mesh=bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts,[],self.faces)
        mesh.materials.clear()
        for mat in self.materials:
            mesh.materials.append(mat)
        mesh.update()
        uv=mesh.uv_layers.new(name='UVMap')
        for poly, coords, mid in zip(mesh.polygons,self.uvs,self.ids):
            poly.use_smooth=True
            poly.material_index=mid
            for li,co in zip(poly.loop_indices,coords):
                uv.data[li].uv=co
        ob=bpy.data.objects.new(self.name,mesh)
        asset.objects.link(ob)
        return ob


def ellipsoid(center,axes,angle=0,segments=8,rings=4,seed=None,irregular=0,tilt=0):
    verts=[]
    uv=[]
    faces=[]
    phase=seed if seed is not None else random.random()*30
    rotation=Matrix.Rotation(angle,3,'Z') @ Matrix.Rotation(tilt,3,'Y')
    for j in range(rings+1):
        phi=math.pi*j/rings
        for i in range(segments+1):
            theta=math.tau*i/segments
            s=math.sin(phi)
            wobble=1+irregular*(.4*math.sin(3*theta+phase)*s+.3*math.cos(7*theta+2*phi+phase)+.16*math.sin(13*theta+7*phi))
            p=Vector((axes[0]*s*math.cos(theta)*wobble,
                      axes[1]*s*math.sin(theta)*wobble,
                      axes[2]*math.cos(phi)*(1+irregular*.3*math.sin(5*theta+phase)*s)))
            p=rotation@p+Vector(center)
            verts.append(tuple(p))
            uv.append((i/segments,j/rings))
    for j in range(rings):
        for i in range(segments):
            a=j*(segments+1)+i
            b=a+1
            c=b+segments+1
            d=a+segments+1
            if j==0:
                faces.append((b,c,d))
            elif j==rings-1:
                faces.append((a,b,d))
            else:
                faces.append((a,b,c,d))
    # The latitude ordering above runs from north to south; reverse for outward normals.
    faces=[tuple(reversed(f)) for f in faces]
    return verts,faces,uv


def plate_z(rad):
    return .006 + .009*max(0,min(1,(rad-.078)/.06))**1.8


plate=Mesh('01_Handpainted_Porcelain_Lagan',[mats['porcelain'],mats['porcelain_bottom'],mats['gold']])
# Continuous closed lathed cross-section includes underside, foot, shallow bowl and rim.
profile=[(.0002,.006),(.025,.006),(.060,.006),(.080,.0061),(.092,.0068),
         (.104,.0082),(.115,.010),(.125,.012),(.135,.0142),(.140,.015),
         (.141,.0144),(.140,.0132),(.133,.0118),(.120,.0085),(.102,.0045),
         (.079,.0018),(.067,.0018),(.066,.000),(.059,.000),(.058,.002),
         (.035,.0032),(.0002,.0032)]
N=128
pv=[]; pu=[]; pf=[]
for ri,(radius,z) in enumerate(profile):
    for i in range(N+1):
        a=math.tau*i/N
        scallop=(radius/.141)**6 * .0015*math.cos(14*a)
        rr=radius+scallop
        pv.append((rr*math.cos(a),rr*math.sin(a),z))
        pu.append((.5+rr*math.cos(a)/.290,.5+rr*math.sin(a)/.290))
for j in range(len(profile)-1):
    for i in range(N):
        a=j*(N+1)+i
        f=(a,a+1,a+N+2,a+N+1)
        mid=2 if j in (8,9,10) else (0 if j<8 else 1)
        plate.add([pv[k] for k in f],[(0,1,2,3)],[pu[k] for k in f],mid)
plate_ob=plate.finish()


def mound(x,y):
    rr=(x/.112)**2+(y/.109)**2
    return .010 + .023*max(0,1-rr)**.62 + .0011*math.sin(x*125+y*61)*max(0,1-rr)


# A closed, slightly corrugated interior supports the separately modeled outer grains.
core=Mesh('02_Rice_Interior',[mats['rice_golden']])
cv=[(0,0,mound(0,0)-.0015)]; cu=[(.5,.5)]; cf=[]
NR=15; NS=80
for j in range(1,NR+1):
    rr=j/NR
    for i in range(NS):
        a=math.tau*i/NS
        x=.112*rr*math.cos(a); y=.109*rr*math.sin(a)
        z=mound(x,y)-.0013 + .00025*math.sin(a*59+j*15)
        cv.append((x,y,z)); cu.append((rr*math.cos(a)*6+.5,rr*math.sin(a)*6+.5))
for i in range(NS): cf.append((0,1+i,1+(i+1)%NS))
for j in range(NR-1):
    for i in range(NS):
        a=1+j*NS+i; b=1+j*NS+(i+1)%NS
        cf.append((a,a+NS,b+NS,b))
bottom=len(cv); cv.append((0,0,.0064)); cu.append((.5,.5))
for i in range(NS):
    a=1+(NR-1)*NS+i; b=1+(NR-1)*NS+(i+1)%NS
    cf.append((a,b,bottom))
core.add(cv,cf,cu)
core_ob=core.finish()


rice=Mesh('03_Individual_Long_Grain_Rice',[mats[n] for n in ['rice_ivory','rice_cream','rice_golden','rice_white']])
for i in range(2180):
    rr=math.sqrt(random.random())
    a=random.uniform(0,math.tau)
    x=.111*rr*math.cos(a); y=.108*rr*math.sin(a)
    z=mound(x,y)+random.uniform(-.0003,.00065)
    angle=random.uniform(0,math.tau)
    tilt=random.uniform(-.28,.28)
    if rr>.88:
        tilt=random.uniform(-.55,.55)
    axes=(random.uniform(.0032,.0044),random.uniform(.00085,.00115),random.uniform(.00075,.00105))
    rice.add(*ellipsoid((x,y,z),axes,angle,tilt=tilt),mat=random.choices([0,1,2,3],[.40,.32,.18,.10])[0])
rice_ob=rice.finish()


carrots=Mesh('04_Braised_Yellow_and_Orange_Carrots',[mats['carrot_yellow'],mats['carrot_orange']])


def strip(cx,cy,z,length,width,thick,angle,phase):
    verts=[]; uv=[]; faces=[]
    rings=6; sides=6
    for j in range(rings):
        t=j/(rings-1)
        taper=.68+.32*math.sin(math.pi*t)**.4
        for k in range(sides+1):
            a=math.tau*k/sides
            px=(t-.5)*length
            py=math.cos(a)*width*.5*taper + math.sin(t*math.pi)*width*.28*math.sin(phase)
            pz=math.sin(a)*thick*.5*taper + math.sin(t*math.pi)*thick*.2
            verts.append((cx+px*math.cos(angle)-py*math.sin(angle),cy+px*math.sin(angle)+py*math.cos(angle),z+pz))
            uv.append((t,k/sides))
    for j in range(rings-1):
        for k in range(sides):
            a=j*(sides+1)+k
            faces.append((a,a+1,a+sides+2,a+sides+1))
    faces.append(tuple(reversed(tuple(range(sides)))))
    faces.append(tuple((rings-1)*(sides+1)+k for k in range(sides)))
    return verts,faces,uv


for i in range(67):
    rr=math.sqrt(random.uniform(.08,.96))
    a=random.uniform(0,math.tau)
    x=.105*rr*math.cos(a); y=.103*rr*math.sin(a)
    # Larger visible strips around the meat, following the photograph.
    thick=random.uniform(.003,.005)
    z=mound(x,y)+thick*.35
    carrots.add(*strip(x,y,z,random.uniform(.014,.033),random.uniform(.0038,.007),thick,
                       random.uniform(0,math.tau),random.uniform(0,6)),mat=0 if random.random()<.83 else 1)
carrot_ob=carrots.finish()


# Reference-guided meat composition (x,y in meters, looking from above).
pieces=[
    (-.006,.044,.044,.027,.014,.010,-.53),
    (.016,.031,.045,.022,.014,.010,-.87),
    (-.021,.013,.049,.030,.017,.010,.42),
    (.006,.006,.052,.030,.014,.012,.73),
    (-.014,-.012,.047,.027,.014,.012,-.30),
    (.026,-.014,.043,.025,.014,.013,.92),
    (-.026,-.038,.037,.023,.015,.012,.22),
    (.000,-.043,.037,.024,.014,.012,-.35),
    (.032,-.047,.035,.018,.013,.013,.4),
    (-.080,.028,.024,.019,.011,.012,-.95),
    (-.052,-.018,.034,.021,.011,.009,.68),
    (.025,-.073,.025,.023,.008,.008,1.37),
]
meat=Mesh('05_Slow_Cooked_Meat_Pieces',[mats['meat_cut'],mats['meat_crust']])
for i,(x,y,z,l,w,h,a) in enumerate(pieces):
    v,f,uv=ellipsoid((x,y,z),(l,w,h),a,segments=28,rings=14,seed=i*1.72,irregular=.24,tilt=random.uniform(-.18,.18))
    # UVs follow the longitudinal grain, avoiding a flat photograph plane.
    meat.add(v,f,uv,mat=1 if i in (6,7,8,9) else 0)
meat_ob=meat.finish()


fibers=Mesh('06_Torn_Meat_Fibers',[mats['meat_cut'],mats['meat_crust'],mats['fat']])
for pi,(x,y,z,l,w,h,a) in enumerate(pieces):
    for j in range(19):
        u=random.uniform(-.80,.80); v=random.uniform(-.75,.75)
        if u*u+v*v>.85: continue
        lx=u*l; ly=v*w
        zz=z+h*math.sqrt(max(.05,1-u*u-v*v))-.00012
        xx=x+lx*math.cos(a)-ly*math.sin(a)
        yy=y+lx*math.sin(a)+ly*math.cos(a)
        fibers.add(*ellipsoid((xx,yy,zz),(random.uniform(.002,.0055),random.uniform(.00020,.00045),.00024),a+random.uniform(-.15,.15),segments=6,rings=3),mat=1 if pi in (6,7,8,9) else 0)
fiber_ob=fibers.finish()


fat=Mesh('07_Gelatinous_Fat_Seams',[mats['fat']])
for i in [0,1,3,4,5]:
    x,y,z,l,w,h,a=pieces[i]
    ox=-math.sin(a)*w*.65; oy=math.cos(a)*w*.65
    fat.add(*ellipsoid((x+ox,y+oy,z+h*.28),(l*.72,.0032,.0035),a,segments=16,rings=6,seed=i,irregular=.30))
fat_ob=fat.finish()


garnish=Mesh('08_Chickpeas_Raisins_and_Cumin',[mats['chickpea'],mats['raisin'],mats['meat_crust']])
for i in range(53):
    a=random.uniform(0,math.tau); rr=random.uniform(.33,.95)
    x=.105*rr*math.cos(a); y=.103*rr*math.sin(a)
    if i<17:
        axes=(.0028,.0026,.0024); mi=0
    elif i<29:
        axes=(.0023,.0015,.0014); mi=1
    else:
        axes=(.0017,.00034,.0003); mi=2
    garnish.add(*ellipsoid((x,y,mound(x,y)+axes[2]*.6),axes,random.uniform(0,6.28),segments=8,rings=4,irregular=.13),mat=mi)
garnish_ob=garnish.finish()


# Studio collection is excluded from the GLB, leaving a clean isolated product.
world=bpy.data.worlds.new('ToyOsh_Soft_Studio')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.37,.45,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.22
scene.world=world


def area(name,loc,energy,size,color):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=energy
    data.shape='DISK'
    data.size=size
    data.color=color
    ob=bpy.data.objects.new(name,data)
    studio.objects.link(ob)
    ob.location=loc
    ob.rotation_euler=(Vector((0,0,.015))-ob.location).to_track_quat('-Z','Y').to_euler()


area('Key_Large_Softbox',(-.23,-.18,.40),10,.30,(1,.92,.82))
area('Fill_Softbox',(.25,.08,.28),5,.25,(.85,.92,1))
area('Rim_Softbox',(-.05,.28,.32),7,.23,(1,.96,.88))
cam_data=bpy.data.cameras.new('ToyOsh_Camera')
cam=bpy.data.objects.new('ToyOsh_Camera',cam_data)
studio.objects.link(cam)
scene.camera=cam
cam_data.type='ORTHO'
cam_data.ortho_scale=.345
cam_data.lens=52
cam.location=(.23,-.31,.28)
cam.rotation_euler=(Vector((0,0,.018))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES'
scene.cycles.samples=64
scene.cycles.use_denoising=True
scene.render.resolution_x=1200
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='8'

for ob in asset.objects:
    ob['asset']='ToyOsh'
    ob['units']='meters'
    ob.select_set(True)
bpy.context.view_layer.objects.active=meat_ob
for screen in bpy.data.screens:
    for ar in screen.areas:
        if ar.type=='VIEW_3D':
            ar.spaces.active.region_3d.view_distance=.44
            ar.spaces.active.region_3d.view_location=(0,0,.018)
            ar.spaces.active.clip_start=.001
            ar.spaces.active.shading.type='MATERIAL'

scene['asset_notes']='Rice, carrot, meat, fat and plate are closed volumetric meshes. PBR fields baked into PNG base color, tangent normal and ORM maps. No billboard geometry.'
stats={}
for ob in asset.objects:
    ob.data.calc_loop_triangles()
    stats[ob.name]={'vertices':len(ob.data.vertices),'triangles':len(ob.data.loop_triangles)}
total=sum(s['triangles'] for s in stats.values())
if total>150000:
    raise RuntimeError(f'Geometry budget exceeded: {total}')
(OUT/'build_stats.json').write_text(json.dumps({'objects':stats,'triangles':total,'seed':271026},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
result={'scene':scene.name,'triangles':total,'objects':len(asset.objects),'blend':str(OUT/'toyosh.blend')}
