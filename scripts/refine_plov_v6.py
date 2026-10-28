"""Reference-guided editable review scene. No final render or export is run."""
import sys
sys.path.insert(0,'/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/scripts')
from food_v4_utils import *
from mathutils import noise
random.seed(2710276)
TEX=OUT/'textures'/'v6';TEX.mkdir(exist_ok=True)
source=bpy.data.scenes['ToyOsh'];asset_source=bpy.data.collections['ToyOsh_Asset']
assert bpy.data.scenes.get('ToyOsh_Review_v6') is None
scene=bpy.data.scenes.new('ToyOsh_Review_v6');bpy.context.window.scene=scene
asset=bpy.data.collections.new('ToyOsh_v6_Asset');scene.collection.children.link(asset)
scene.world=source.world.copy() if source.world else bpy.data.worlds.new('v6_World')
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=3840;scene.render.resolution_y=2160;scene.render.resolution_percentage=100
scene['review_version']=6;scene['status']='Awaiting user visual review; no final render/export yet'
scene['triangle_budget']=350000;scene['file_budget_mib']=35
# Copy the food foundation only. Imported GLB duplicates remain in their old scene.
for ob in asset_source.objects:
    if ob.get('food_class')==40 or ob.name.startswith(('04_','05_','06_','07_','11_','12_','13_')):continue
    new=ob.copy();new.data=ob.data.copy();new.name='v6_'+ob.name;asset.objects.link(new)
    new.hide_viewport=False;new.hide_render=False;new.hide_set(False)
plate=bpy.data.objects['v6_01_Handpainted_Porcelain_Lagan']
basefood=[o for o in asset.objects if o!=plate];food_tree=bvh_objects(basefood)
plate_tree=bvh_objects([plate])
print('V6_FOUNDATION',len(asset.objects),flush=True)
# Directed microstructure maps represent surface relief and albedo separately.
# U follows muscle fibres; no photographic lighting is baked into the maps.
if not (TEX/'meat_braised_albedo_4k.png').exists():
    size=4096
    u=np.linspace(0,1,size,dtype=np.float32)[None,:];v=np.linspace(0,1,size,dtype=np.float32)[:,None]
    phase=v*math.tau*100+.40*np.sin(u*math.tau*2+v*19)+.18*np.sin(u*math.tau*7+v*5)
    fibril=np.sin(phase)+.25*np.sin(phase*2.07+u*11)
    patch=np.sin(u*16+np.sin(v*13))*np.cos(v*21-u*3)
    short=np.maximum(0,np.sin(u*math.tau*21+v*31))**16
    height=(fibril*.006+np.sin(v*math.tau*31+u*7)*.005)*(1-.25*short)
    dy,dx=np.gradient(height)
    normal=np.stack((-dx*12,-dy*12,np.ones_like(height)),axis=2)
    normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    # Quantized tangent normal is compact and preserves soft submillimetre relief.
    normal=np.round((normal*.5+.5)*127)/127
    png(TEX/'meat_fibrils_normal_4k.png',normal)
    rough=np.clip(.36+.045*patch+.025*np.sin(phase)-.055*np.maximum(0,np.sin(u*19+v*14)),.25,.46)
    png(TEX/'meat_moisture_orm_4k.png',np.stack((np.ones_like(rough),rough,np.zeros_like(rough)),axis=2))
    variation=1+.065*patch+.025*fibril-.025*short
    for tag,color in [('cut',(.57,.335,.205)),('braised',(.43,.215,.105))]:
        png(TEX/f'meat_{tag}_albedo_4k.png',np.asarray(color,dtype=np.float32)[None,None,:]*variation[:,:,None])
    del normal,height,dx,dy,rough,variation,phase,fibril,patch,short;gc.collect()
cut=make_pbr('v6_Meat_Moist_Cut',TEX/'meat_cut_albedo_4k.png',TEX/'meat_fibrils_normal_4k.png',TEX/'meat_moisture_orm_4k.png',1.1,.025)
crust=make_pbr('v6_Meat_Braised_Exterior',TEX/'meat_braised_albedo_4k.png',TEX/'meat_fibrils_normal_4k.png',TEX/'meat_moisture_orm_4k.png',.85,.035)
for m in [cut,crust]:
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Subsurface Weight'].default_value=.055
    p.inputs['Subsurface Radius'].default_value=(1,.45,.22);p.inputs['Subsurface Scale'].default_value=.0008
    # Break the continuous glossy film with fine irregular surface relief.
    nodes=m.node_tree.nodes;links=m.node_tree.links
    old=list(p.inputs['Roughness'].links)[0].from_socket
    rough=nodes.new('ShaderNodeMath');rough.operation='MULTIPLY_ADD'
    rough.inputs[1].default_value=1.05;rough.inputs[2].default_value=.09
    links.new(old,rough.inputs[0]);links.new(rough.outputs[0],p.inputs['Roughness'])
    uvnode=nodes.new('ShaderNodeTexCoord');noise_node=nodes.new('ShaderNodeTexNoise')
    noise_node.inputs['Scale'].default_value=140;noise_node.inputs['Detail'].default_value=3
    links.new(uvnode.outputs['UV'],noise_node.inputs['Vector'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.00018
    normal=list(p.inputs['Normal'].links)[0].from_socket
    links.new(normal,bump.inputs['Normal']);links.new(noise_node.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],p.inputs['Normal'])

def simple_material(name,color,roughness,sss=0,scale=.001,coat=.05):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=roughness;p.inputs['IOR'].default_value=1.45
    p.inputs['Specular IOR Level'].default_value=.35;p.inputs['Coat Weight'].default_value=coat
    p.inputs['Coat Roughness'].default_value=.24;p.inputs['Subsurface Weight'].default_value=sss
    p.inputs['Subsurface Scale'].default_value=scale;p.inputs['Subsurface Radius'].default_value=(1,.55,.25)
    return m
fatm=[simple_material('v6_Soft_Rendered_Fat',(.56,.38,.20),.38,.19,.0015,.05),simple_material('v6_Pale_Gelatin_Fat',(.69,.54,.33),.36,.24,.0015,.05)]
# Warm, moist starch with a small translucent edge; no hard varnish layer.
rice=[simple_material('v6_Rice_'+str(i),color,.29+i*.012,.19,.00065,.055) for i,color in enumerate([(.68,.47,.19),(.77,.60,.33),(.88,.76,.52),(.76,.52,.19),(.64,.39,.12)])]
for ob in asset.objects:
    if ob.get('food_class') in [10,20]:
        ob.data.materials.clear()
        for m in rice:ob.data.materials.append(m)
        # Preserve packing: subtly plump each exposed grain without moving centers.
        if ob.get('food_class')==20:
            for ids in components(ob):
                a=np.array([tuple(ob.data.vertices[j].co) for j in ids]);c=a.mean(axis=0)
                w,axes=np.linalg.eigh((a-c).T@(a-c));local=(a-c)@axes
                local[:,0]*=1.045;local[:,1]*=1.025;local[:,2]*=.98
                changed=local@axes.T+c
                for j,p in zip(ids,changed):ob.data.vertices[j].co=p
            ob.data.update()
# Rebuild soft carrots above and partly within rice, following the new references.
carrot_mats=[simple_material('v6_Cooked_Carrot_'+str(i),color,.29,.10,.0008,.085) for i,color in enumerate([(.72,.36,.015),(.82,.47,.022),(.64,.28,.009),(.75,.19,.009)])]
carrots=MeshBuilder('v6_04_Soft_Yellow_Carrots',carrot_mats)
profile=[(1,.45),(.55,1),(-.55,1),(-1,.45),(-1,-.45),(-.55,-1),(.55,-1),(1,-.45)]
food_tree=bvh_objects([o for o in asset.objects if o.get('food_class')!=60])
for i in range(120):
    a=random.uniform(0,math.tau);r=math.sqrt(random.uniform(.015,.86));cx=.111*r*math.cos(a);cy=.108*r*math.sin(a)
    angle=random.uniform(0,math.tau);L=random.uniform(.017,.038);W=random.uniform(.0026,.0058);H=random.uniform(.0018,.0032)
    bend=random.uniform(-.004,.004);vv=[];uv=[];ff=[]
    for j in range(4):
        t=j/3;x=(t-.5)*L;curve=bend*math.sin(math.pi*t);taper=.82+.16*math.sin(math.pi*t)
        for k,(py,pz) in enumerate(profile):
            yy=curve+py*W*.5*taper
            xx=cx+x*math.cos(angle)-yy*math.sin(angle);yy=cy+x*math.sin(angle)+yy*math.cos(angle)
            # Local softened stick drapes along the rice mound.
            top=z_hit(food_tree,xx,yy)
            if top is None:top=.012
            zz=top+.0004+pz*H*.5
            vv.append((xx,yy,zz));uv.append((t,k/8))
    for j in range(3):
        for k in range(8):ff.append((j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k))
    ff.extend([tuple(reversed(range(8))),tuple(range(24,32))])
    carrots.add(vv,ff,uv,random.choices(range(4),[.36,.34,.15,.15])[0])
carrot_ob=carrots.finish(asset,30)
food_tree=bvh_objects([o for o in asset.objects if o.get('food_class')!=60])
print('V6_CARROTS_READY',flush=True)
# New compact ragged meat: muscle mass, short surface fibres, soft fatty lobes.
body=MeshBuilder('v6_05_Braised_Meat_Chunks',[cut,crust])
strands=MeshBuilder('v6_06_Separated_Muscle_Fibres',[cut,crust])
fats=MeshBuilder('v6_07_Soft_Fat_Pockets',fatm)
rootverts=[];rootfaces=[];root_tree=None;contacts=[]
def combined_floor(x,y):
    a=z_hit(food_tree,x,y);b=z_hit(root_tree,x,y) if root_tree else None
    return max([v for v in [a,b] if v is not None],default=.010)

def tube(path,width,depth,sides=4,tip=.25,seed=0):
    rr=random.Random(seed);vv=[];uv=[];ff=[]
    for j,center in enumerate(path):
        t=j/(len(path)-1);taper=(.65+.35*math.sin(math.pi*t))*(1 if j<len(path)-1 else tip)
        for k in range(sides):
            ang=k*math.tau/sides;wiggle=1+.10*math.sin(k*1.4+j*2.3+seed)
            vv.append((center[0],center[1]+math.cos(ang)*width*taper*wiggle,center[2]+math.sin(ang)*depth*taper*wiggle));uv.append((t,k/sides))
    for j in range(len(path)-1):
        for k in range(sides):ff.append((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k))
    ff.extend([tuple(reversed(range(sides))),tuple((len(path)-1)*sides+k for k in range(sides))])
    return vv,ff,uv

def core(L,W,H,seed,fat=False):
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=2 if fat else 3,radius=1)
    bm.verts.index_update();vv=[];uv=[]
    for vert in bm.verts:
        x,y,z=vert.co
        phase=seed*.713
        rough=.12*math.sin(x*8+y*5+phase)*math.sin(z*7-y*6+phase*.3)
        rough+=.06*math.sin(x*15-y*13+z*11+phase)
        # Genuine longitudinal tears open toward the exposed upper/end surface.
        cleft=(max(0,math.cos(math.atan2(z,y)*7+.35*math.sin(x*5+phase)))**6)
        tear=cleft*(.08+.16*max(0,x)) if not fat else 0
        radial=max(.60,1+rough-tear)
        xx=x*L*.5*(1+.12*math.sin(y*6+z*3+phase))
        yy=y*W*.5*radial+.0006*math.sin(x*4+phase)*(1-x*x)
        zz=z*H*.5*radial
        if not fat:
            xx-=L*.08*math.sin(y*9+z*8+phase)*max(0,x)
            zz-=H*.055*(max(0,math.cos(y*15+phase+.25*x))**8)*max(0,z)
        else:
            yy*=1+.16*math.sin(x*6+phase);zz*=.82+.13*math.cos(y*7+phase)
        vv.append((xx,yy,zz));uv.append((.5+xx/L,(math.atan2(z,y)/math.tau)%1))
    ff=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free()
    return vv,ff,uv

def local_surface(tree,x,y):
    p=tree.ray_cast(Vector((x,y,.08)),Vector((0,0,-1)))[0]
    return p.z if p else 0

# Majority central, with a few resting on the shoulder, as in the references.
placements=[]
for i in range(32):
    angle=i*2.399963;radius=.057*math.sqrt((i+.5)/32)
    if i in [27,30]:radius=.080
    placements.append((radius*math.cos(angle),radius*math.sin(angle)))
# Place outward pieces first, keeping the central pile gently higher.
for order,ci in enumerate(sorted(range(32),key=lambda i:-sum(v*v for v in placements[i]))):
    cx,cy=placements[ci];L=random.uniform(.017,.030);W=random.uniform(.012,.021);H=random.uniform(.0065,.0115)
    angle=random.uniform(0,math.tau);roll=random.uniform(-.25,.25)
    vv,ff,uv=core(L,W,H,ci+131)
    localtree=BVHTree.FromPolygons(vv,ff,all_triangles=False)
    comp=[(body,vv,ff,uv,1 if ci%4==0 else 0)]
    # Ten short lifted fibre bundles. Broad ends stay joined to the muscle.
    for k in range(8):
        yy=(k/7-.5)*W*.80;length=L*random.uniform(.42,.88)
        start=random.uniform(-.35,-.20)*L;path=[]
        for j in range(3):
            t=j/2;x=start+t*length;y=yy+.0005*math.sin(t*3+ci+k)
            z=local_surface(localtree,max(-L*.45,min(L*.45,x)),y)
            z+=.00012+(.0004*math.sin(t*math.pi) if j<2 else -.00015)
            path.append((x,y,z))
        sv,sf,suv=tube(path,random.uniform(.00038,.00072),random.uniform(.00022,.00042),4,.38,ci*50+k)
        comp.append((strands,sv,sf,suv,1 if (ci+k)%7==0 else 0))
    # Three frayed tips per clump, attached at the tear and curved down by gravity.
    for k in range(3):
        y=random.uniform(-.30,.30)*W;x=L*.31;z=local_surface(localtree,x,y)
        path=[(x,y,z),(x+.002,y+.0003,z-.0003),(x+.0035,y+.0006,z-.0011)]
        sv,sf,suv=tube(path,.00022,.00015,3,.15,ci+k)
        comp.append((strands,sv,sf,suv,0))
    # Soft fat is a separate pale lobe nestled into one side, never striped tissue.
    if ci<24:
        fv,ffat,fuv=core(L*.42,W*.37,H*.40,ci+481,fat=True)
        offset=Vector((-L*.12,W*.32,H*.18))
        fv=[tuple(Vector(v)+offset) for v in fv]
        # Small low-poly fat can be smooth shaded; preserve closed volume.
        comp.append((fats,fv,ffat,fuv,ci%2))
    rotation=Matrix.Rotation(angle,4,'Z')@Matrix.Rotation(roll,4,'X')
    trans=Matrix.Translation((cx,cy,0))@rotation
    rv=[tuple(trans@Vector(p)) for p in vv];rt=BVHTree.FromPolygons(rv,ff,all_triangles=False)
    offsets=[]
    for x in np.linspace(min(p[0] for p in rv)+.0001,max(p[0] for p in rv)-.0001,12):
        for y in np.linspace(min(p[1] for p in rv)+.0001,max(p[1] for p in rv)-.0001,9):
            hit=rt.ray_cast(Vector((float(x),float(y),-.1)),Vector((0,0,1)))[0]
            if hit is not None:offsets.append(combined_floor(float(x),float(y))-hit.z)
    assert offsets
    lift=max(offsets)-.00065;trans=Matrix.Translation((0,0,lift))@trans
    for builder,vs,fs,uvs,mi in comp:builder.add([tuple(trans@Vector(p)) for p in vs],fs,uvs,mi)
    start=len(rootverts);rootverts.extend(tuple(trans@Vector(p)) for p in vv);rootfaces.extend(tuple(start+j for j in f) for f in ff)
    root_tree=BVHTree.FromPolygons(rootverts,rootfaces,all_triangles=False)
    contacts.append({'clump':ci,'center':list(trans@Vector()),'contacts':sum(abs(v-lift)<.0011 for v in offsets),'embedding_m':.00065})
# Small torn pieces settle near the clumps. Short, flat ends avoid the old spikes.
for i in range(36):
    a=i*2.399963;r=random.uniform(.025,.077);cx=r*math.cos(a);cy=r*math.sin(a)
    L=random.uniform(.006,.014);W=random.uniform(.001,.0024);D=random.uniform(.0006,.0013)
    path=[((t-.5)*L,.0006*math.sin(t*math.pi),-.0002*math.sin(t*math.pi)) for t in [0,.33,.67,1]]
    vv,ff,uv=tube(path,W,D,6,.5,i)
    rot=Matrix.Rotation(random.uniform(0,math.tau),4,'Z');vv=[tuple(rot@Vector(p)+Vector((cx,cy,0))) for p in vv]
    lift=max(combined_floor(x,y)-z for x,y,z in vv)-.00015
    strands.add([(x,y,z+lift) for x,y,z in vv],ff,uv,i%5==0)
meat_ob=body.finish(asset,40);strands_ob=strands.finish(asset,40);fat_ob=fats.finish(asset,40)
print('V6_MEAT_READY',body.triangles+strands.triangles+fats.triangles,flush=True)
# Refine existing garnish materials in the review copy only.
for ob in asset.objects:
    if ob.get('food_class')==50:
        for i,old in enumerate(list(ob.data.materials)):
            name=old.name.lower()
            color=(.49,.23,.045) if 'chick' in name else ((.075,.018,.008) if 'raisin' in name else (.028,.016,.006))
            ob.data.materials[i]=simple_material('v6_'+old.name,color,.31,.08 if 'chick' in name else .025,.001,.08)
# Keep the original hand-painted plate pattern; refine ceramic/glaze response.
for i,old in enumerate(list(plate.data.materials)):
    m=old.copy();m.name='v6_'+old.name;plate.data.materials[i]=m
    if m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Coat Weight'].default_value=.22;bs.inputs['Coat Roughness'].default_value=.20
            for link in list(bs.inputs['Roughness'].links):m.node_tree.links.remove(link)
            bs.inputs['Roughness'].default_value=.22
# Studio is copied for eventual approved rendering. No render is launched here.
studio=bpy.data.collections.new('ToyOsh_v6_Studio');scene.collection.children.link(studio)
for old in bpy.data.collections['ToyOsh_Studio'].objects:
    ob=old.copy();ob.data=old.data.copy();ob.name='v6_'+old.name;studio.objects.link(ob)
    if ob.type=='CAMERA':scene.camera=ob
scene.camera.location=(.23,-.31,.28)
scene.camera.rotation_euler=(Vector((0,0,.03))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=.335
bpy.context.view_layer.update()
# All microstructure assets are packed; source scenes are retained in this file.
triangles=0;stats={}
for ob in asset.objects:
    ob.data.calc_loop_triangles();n=len(ob.data.loop_triangles);triangles+=n;stats[ob.name]=n
# Optimise only the new fatty lobes if the source grain tessellation requires it.
if triangles>350000:
    n=stats[fat_ob.name];mod=fat_ob.modifiers.new('Fat detail budget','DECIMATE');mod.ratio=max(.3,(n-(triangles-349500))/n)
    bpy.context.view_layer.objects.active=fat_ob;bpy.ops.object.modifier_apply(modifier=mod.name)
    fat_ob.data.calc_loop_triangles();triangles+=len(fat_ob.data.loop_triangles)-n;stats[fat_ob.name]=len(fat_ob.data.loop_triangles)
assert triangles<=350000,triangles
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            s=area.spaces.active;s.clip_start=.001;s.clip_end=100;s.overlay.show_overlays=False
            s.shading.type='MATERIAL';s.shading.use_scene_world=False;s.shading.use_scene_lights=False
            s.shading.studiolight_rotate_z=.45;s.shading.studiolight_intensity=.8
            s.region_3d.view_location=(0,0,.035);s.region_3d.view_distance=.38
            s.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
scene['food_detail_version']=6;scene['main_meat_clumps']=32;scene['rice_grains']=10000;scene['carrot_count']=120
report={'version':6,'status':'Review ready; final render/export deferred at user request','scene':scene.name,'triangles':triangles,'rice_grains':10000,'main_meat_clumps':32,'short_surface_fibre_bundles':256,'frayed_tips':96,'loose_shreds':36,'fat_pockets':24,'carrots':120,'meat_maps_resolution':4096,'references':['Uzbek Plov with Tender Beef and Carrots (1).png','Golden Pilaf with Tender Meat and Chickpeas.png','Ornate Bowl of Lamb Pilaf.png'],'contacts':contacts,'mesh_triangles':stats,'changes':['Compact soft-cut meat silhouettes, short attached muscle bundles, gravity-curved frays','Separate pale gelatin/fat lobes','New directionally aligned 4K albedo, micro-normal and roughness maps without photographic highlights','Warm lightly translucent rice; preserved dense 10000-grain packing','120 visible soft yellow/orange carrot sticks','Preserved original scenes and imported duplicates outside the clean review scene'],'limitations':['Reference-guided reconstruction, not a scanned meal','Visual realism requires user review; final rendering deferred']}
(OUT/'review_v6.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh_review_v6.blend'))
print('V6_READY',json.dumps({k:v for k,v in report.items() if k not in ['contacts','changes','mesh_triangles']}),flush=True)
