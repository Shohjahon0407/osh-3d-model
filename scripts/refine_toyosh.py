"""Replace abstract meat shapes with photo-traced cut surfaces and torn sides."""
import bpy, math, random, pathlib, ast, struct, zlib
import numpy as np
from mathutils import Vector, Matrix

ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT=ROOT/'output/toyosh'
TEX=OUT/'textures'
scene=bpy.data.scenes['ToyOsh']
bpy.context.window.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
random.seed(271027)
rng=np.random.default_rng(271027)
mats={m.name.removeprefix('ToyOsh_'):m for m in bpy.data.materials if m.name.startswith('ToyOsh_')}
# Reuse the deterministic mesh/texture utilities without rebuilding the scene.
tree=ast.parse((ROOT/'scripts/build_toyosh.py').read_text())
names={'Mesh','ellipsoid','strip','mound','png','normal_from_height','load_tex','pbr'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[]),'<asset utilities>','exec'))

source=bpy.data.images.load('/home/shohjahon/BESHKASHTAN_RASMLARI/ofiyat rasmlari/toyosh.jpg',check_existing=True)
sw,sh=source.size
pixels=np.empty(sw*sh*4,np.float32)
source.pixels.foreach_get(pixels)
pixels=pixels.reshape(sh,sw,4)[...,:3]
size=2048
v,u=np.mgrid[0:1:complex(size),0:1:complex(size)]
xx=np.clip((960+(u-.5)*1700).astype(int),0,sw-1)
yy=np.clip((sh-1130+(v-.5)*1640).astype(int),0,sh-1)
albedo=pixels[yy,xx].copy()
lum=albedo.mean(axis=2)
# Broad illumination normalization; keep local tissue color/fiber information.
fy=np.fft.fftfreq(size)[:,None]; fx=np.fft.fftfreq(size)[None,:]
blur=np.fft.ifft2(np.fft.fft2(lum)*np.exp(-2*math.pi**2*28**2*(fx*fx+fy*fy))).real
gain=np.clip(.39/np.maximum(blur,.04),.86,1.14)
albedo*=gain[...,None]*.94
png(TEX/'meat_photo_basecolor.png',albedo)
high=lum-blur
png(TEX/'meat_photo_normal.png',normal_from_height(high,9))
png(TEX/'meat_photo_orm.png',np.stack((np.ones_like(lum),np.clip(.40+.07*high,.3,.5),np.zeros_like(lum)),axis=2))
mats['meat_photo']=pbr('meat_photo')

# Rice-only photographic patch, mirrored into a seamless bed texture. Individual
# outer grains retain their actual geometry and separately baked PBR materials.
f=1920/1368
x0,x1=int(470*f),int(542*f)
y0,y1=int(1130*f),int(1185*f)
crop=pixels[sh-y1:sh-y0,x0:x1]
crop=np.concatenate((crop,crop[:,::-1]),axis=1)
crop=np.concatenate((crop,crop[::-1]),axis=0)
rv,ru=np.mgrid[0:1:512j,0:1:512j]
rice_color=crop[(rv*(crop.shape[0]-1)).astype(int),(ru*(crop.shape[1]-1)).astype(int)]
png(TEX/'rice_bed_basecolor.png',rice_color*.94)
png(TEX/'rice_bed_normal.png',normal_from_height(rice_color.mean(axis=2),15))
png(TEX/'rice_bed_orm.png',np.stack((np.ones_like(ru),np.full_like(ru,.43),np.zeros_like(ru)),axis=2))
mats['rice_bed']=pbr('rice_bed')
core=bpy.data.objects['02_Rice_Interior']
core.data.materials.clear();core.data.materials.append(mats['rice_bed'])
for loop in core.data.uv_layers.active.data:
    loop.uv=(loop.uv-Vector((.5,.5)))*.52+Vector((.5,.5))

# Reduce synthetic micro-stripes on grains and on inferred meat sides.
for name,m in mats.items():
    for node in m.node_tree.nodes:
        if node.type=='NORMAL_MAP':
            node.inputs['Strength'].default_value=.18 if name.startswith('meat_') else (.12 if name.startswith('rice_') else .30)

for name in ['05_Slow_Cooked_Meat_Pieces','06_Torn_Meat_Fibers','07_Gelatinous_Fat_Seams','04_Braised_Yellow_and_Orange_Carrots']:
    ob=bpy.data.objects.get(name)
    if ob:
        bpy.data.objects.remove(ob,do_unlink=True)

def xy(px,py):
    return ((px-684)/605*.14,(810-py)/585*.14)

# Contours traced in the displayed reference coordinate system (1368 x 1824).
contours=[
    [(540,475),(582,454),(624,463),(653,483),(694,490),(718,518),(736,546),(776,568),(811,590),(837,621),(821,654),(783,674),(757,655),(716,632),(680,618),(641,586),(607,568),(565,539)],
    [(458,689),(486,659),(537,643),(581,624),(621,628),(655,645),(683,658),(698,685),(688,718),(655,749),(625,775),(594,789),(569,772),(543,751),(503,745),(473,725)],
    [(696,689),(725,672),(756,654),(789,655),(806,675),(810,709),(788,738),(759,757),(732,782),(692,799),(667,784),(679,752)],
    [(785,747),(817,726),(849,742),(875,779),(893,805),(885,839),(862,863),(846,901),(816,925),(784,912),(762,881),(748,850),(757,815),(773,789)],
    [(540,791),(573,782),(600,800),(618,824),(609,853),(586,881),(567,922),(539,939),(515,923),(503,895),(516,865),(521,827)],
    [(568,913),(601,899),(631,924),(657,922),(682,939),(714,966),(723,1004),(700,1037),(671,1058),(637,1044),(610,1061),(583,1047),(560,1010),(542,986),(552,945)],
    [(450,1017),(480,1021),(510,1034),(549,1051),(577,1083),(584,1113),(564,1142),(526,1156),(487,1132),(451,1115),(422,1090),(423,1058)],
    [(395,847),(419,824),(444,832),(468,860),(478,894),(470,924),(489,954),(473,987),(446,1004),(419,979),(393,967),(389,935),(405,907)],
    [(226,539),(250,553),(279,585),(293,622),(319,647),(340,678),(340,709),(319,737),(299,760),(265,753),(244,728),(229,689),(213,667),(215,620)],
    [(784,1130),(806,1150),(796,1192),(783,1221),(785,1257),(763,1301),(741,1318),(738,1289),(746,1254),(752,1222),(756,1187),(768,1154)],
    [(627,790),(655,767),(687,776),(719,786),(741,815),(734,846),(763,864),(745,896),(731,926),(705,947),(678,923),(657,905),(639,871),(612,851)],
    [(779,914),(815,913),(852,928),(881,954),(890,987),(877,1017),(855,1053),(820,1089),(793,1084),(778,1050),(762,1030),(761,994),(746,972),(762,947)],
]
meat=Mesh('05_Slow_Cooked_Meat_Pieces',[mats['meat_photo'],mats['meat_crust']])
shreds=Mesh('06_Torn_Meat_Fibers',[mats['meat_cut'],mats['meat_crust']])
metadata=[]
for pi,points in enumerate(contours):
    poly=[Vector(xy(*p)) for p in points]
    cx=sum(p.x for p in poly)/len(poly);cy=sum(p.y for p in poly)/len(poly)
    # Resample contour by arclength so the radial surface carries irregular cuts.
    lengths=[(poly[(i+1)%len(poly)]-p).length for i,p in enumerate(poly)]
    perimeter=sum(lengths)
    N=56;R=8
    edge=[]
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
        return center_base+thick*(1-.32*rr**3)+.00065*math.sin(px*1900+pi)*math.sin(py*1350)+.00035*math.sin(px*4100+py*900)
    verts=[(cx,cy,surface(cx,cy,0))];uv=[(.5+cx/.28,.5+cy/.28)];faces=[]
    for j in range(1,R+1):
        rr=j/R
        for i,p in enumerate(edge):
            wobble=1+.010*math.sin(i*2.7+pi)*rr*(1-rr)
            xx=cx+(p.x-cx)*rr*wobble;yy=cy+(p.y-cy)*rr*wobble
            verts.append((xx,yy,surface(xx,yy,rr)))
            uv.append((.5+xx/.28,.5+yy/.28))
    for i in range(N):faces.append((0,1+i,1+(i+1)%N))
    for j in range(R-1):
        for i in range(N):
            a=1+j*N+i;b=1+j*N+(i+1)%N
            faces.append((a,a+N,b+N,b))
    meat.add(verts,faces,uv,0)
    # Closed lower wall with inferred cooked exterior; bottom follows the rice bed.
    side_v=[];side_uv=[];side_f=[]
    for j in range(3):
        for i,p in enumerate(edge):
            rr=1 if j==0 else (.99 if j==1 else .83)
            xx=cx+(p.x-cx)*rr;yy=cy+(p.y-cy)*rr
            zz=surface(p.x,p.y,1) if j==0 else (surface(p.x,p.y,1)*.45+(mound(xx,yy)-.001)*.55 if j==1 else mound(xx,yy)-.001)
            side_v.append((xx,yy,zz));side_uv.append((i/N,j/2))
    for j in range(2):
        for i in range(N):
            a=j*N+i;b=j*N+(i+1)%N
            side_f.append((a,b,b+N,a+N))
    side_f.append(tuple(reversed(tuple(2*N+i for i in range(N)))))
    meat.add(side_v,side_f,side_uv,1)
    # Sparse torn fibers at cuts provide silhouette detail beyond the image texture.
    for i in range(14):
        k=random.randrange(N);p=edge[k]
        xx=cx+(p.x-cx)*.94;yy=cy+(p.y-cy)*.94
        zz=surface(xx,yy,.94)-.00025
        a=math.atan2(yy-cy,xx-cx)+random.uniform(-.4,.4)
        shreds.add(*ellipsoid((xx,yy,zz),(random.uniform(.0015,.0037),.0003,.00023),a,segments=6,rings=3),mat=1 if pi in (5,6,7,8) else 0)
    metadata.append({'center':[cx,cy],'thickness':thick})
meat.finish();shreds.finish()

# Small irregular fatty edges, rather than broad smooth bands across the meat.
fat=Mesh('07_Gelatinous_Fat_Seams',[mats['fat']])
for px,py,a in [(756,625,.7),(610,747,1.1),(575,862,1.3),(849,819,.9),(696,952,.5),(735,649,.5)]:
    x,y=xy(px,py)
    fat.add(*ellipsoid((x,y,mound(x,y)+.006),(.0048,.002,.002),a,segments=12,rings=5,irregular=.4))
fat.finish()

carrots=Mesh('04_Braised_Yellow_and_Orange_Carrots',[mats['carrot_yellow'],mats['carrot_orange']])
large=[(1090,948,.20,.034),(1011,892,.98,.037),(963,785,-.40,.038),(939,682,.02,.035),
       (930,1100,.80,.032),(890,1160,.63,.033),(696,1236,1.12,.027),(281,845,-.3,.041),
       (414,751,.90,.029),(441,659,.75,.027),(474,496,.64,.030),(526,559,.98,.028),
       (749,415,.57,.025),(815,440,.90,.026),(1049,535,-.4,.026),(1002,616,.73,.029),
       (625,399,-.10,.020),(503,925,.48,.023),(365,1094,.51,.025),(1060,1045,.62,.026)]
for px,py,a,length in large:
    x,y=xy(px,py);thick=random.uniform(.0035,.005)
    carrots.add(*strip(x,y,mound(x,y)+.0005,length,random.uniform(.0048,.0078),thick,a,random.uniform(0,6)),mat=0)
for i in range(43):
    rr=math.sqrt(random.uniform(.10,.94));a=random.uniform(0,math.tau)
    x=.104*rr*math.cos(a);y=.100*rr*math.sin(a)
    carrots.add(*strip(x,y,mound(x,y)+.0005,random.uniform(.011,.025),random.uniform(.0035,.0058),random.uniform(.0024,.004),random.uniform(0,6),random.uniform(0,6)),mat=0 if i%5 else 1)
carrots.finish()

# Calmer product light and warm, denser rice; avoid chalk-white clipping.
scene.view_settings.exposure=-.9
scene.view_settings.look='AgX - Medium High Contrast'
for name,energy in [('Key_Large_Softbox',7),('Fill_Softbox',2.5),('Rim_Softbox',3.5)]:
    bpy.data.lights[name].energy=energy

# Make all final surfaces smooth at UV seams and ensure correct outward normals.
import bmesh
for ob in asset.objects:
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data);bm.free();ob.data.update()

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
print('TOYOSH_REFINED',len(asset.objects))
