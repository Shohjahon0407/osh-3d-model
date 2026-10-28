"""Bake native 4K PBR microdetail over an AI-created cooked-tissue color source.

The source resolution is recorded honestly. Fine normal/albedo/roughness fields
are evaluated at 4096, rather than just resizing the previous 1K material.
Execute in a disposable Blender background process (numpy is bundled there).
"""
import bpy, pathlib, math, numpy as np, json, ast, struct, zlib, gc

ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
OUT=ROOT/'output/toyosh'
TEX=OUT/'textures'
source_path=OUT/'material_sources/cooked_meat_source.png'
tree=ast.parse((ROOT/'scripts/build_toyosh.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='png'],type_ignores=[]),'<PNG writer>','exec'))
im=bpy.data.images.load(str(source_path))
sw,sh=im.size
rgba=np.empty(sw*sh*4,np.float32)
im.pixels.foreach_get(rgba)
src=rgba.reshape(sh,sw,4)[...,:3].copy()
del rgba
N=4096
color=np.empty((N,N,3),np.float32)
height=np.empty((N,N),np.float32)
rough=np.empty((N,N),np.float32)
x=np.linspace(0,1,N,dtype=np.float32)[None,:]
sx=x[0]*(sw-1)
xi=sx.astype(np.int32);xj=np.minimum(xi+1,sw-1);wx=(sx-xi)[None,:,None]
tau=np.float32(math.tau)

for start in range(0,N,128):
    end=min(start+128,N)
    y=(np.arange(start,end,dtype=np.float32)/(N-1))[:,None]
    sy=y[:,0]*(sh-1)
    yi=sy.astype(np.int32);yj=np.minimum(yi+1,sh-1);wy=(sy-yi)[:,None,None]
    a=src[yi[:,None],xi[None,:]]*(1-wx)+src[yi[:,None],xj[None,:]]*wx
    b=src[yj[:,None],xi[None,:]]*(1-wx)+src[yj[:,None],xj[None,:]]*wx
    c=(a*(1-wy)+b*wy).astype(np.float32)
    lum=c.mean(axis=2)
    saturation=(c.max(axis=2)-c.min(axis=2))/np.maximum(c.max(axis=2),.05)
    fat=np.clip((lum-.49)/.19,0,1)*np.clip((.55-saturation)/.35,0,1)
    flow=y+.0055*np.sin(tau*x*2.7)+.0015*np.sin(tau*(x*9.2+y*2.8))
    bundles=np.sin(tau*(flow*23+.15*np.sin(tau*x*3)))
    fibers=np.sin(tau*(flow*257+.20*np.sin(tau*x*6.3)))
    fine=np.sin(tau*(flow*541+.17*np.sin(tau*(x*14+y*2))))
    broken=.70+.30*np.sin(tau*(x*11.3+y*3.8))**2
    # Height is in meters over a 65 mm physical swatch.
    h=(.000035*fibers+.000012*fine)*broken*(1-.65*fat)+.000045*bundles+.00013*fat
    height[start:end]=h
    oil=np.clip((np.sin(tau*(x*3.2+y*1.9))+.4*np.cos(tau*(x*5.3-y*4.7))-.35),0,1)
    rr=np.clip(.43-.18*fat-.08*oil+.017*fibers,.19,.51)
    rough[start:end]=np.round(rr*63)/63
    # Native 4K color variation tracks the fine relief, without painting shadows.
    c*=((1+.018*fibers+.009*fine)*(1-.006*bundles))[...,None]
    c*=np.array([.95,.96,.97],np.float32)
    color[start:end]=np.clip(c,0,1)

png(TEX/'cooked_meat_4k_basecolor.png',color)
del color,src,c,a,b,lum,saturation,fat,flow,bundles,fibers,fine,oil,h,rr
gc.collect()
# Derive tangent normals from physical height, with the texture's physical scale.
dy,dx=np.gradient(height,np.float32(.065/(N-1)))
del height
normal=np.empty((N,N,3),np.float32)
normal[:,:,0]=-dx;normal[:,:,1]=-dy;normal[:,:,2]=1
del dx,dy
length=np.sqrt(np.sum(normal*normal,axis=2))
normal/=length[:,:,None]
normal*=.5;normal+=.5
png(TEX/'cooked_meat_4k_normal.png',normal)
del normal,length
orm=np.empty((N,N,3),np.float32)
orm[:,:,0]=1;orm[:,:,1]=rough;orm[:,:,2]=0
del rough
png(TEX/'cooked_meat_4k_orm.png',orm)
report={
    'maps':{'basecolor':[N,N],'normal':[N,N],'orm':[N,N]},
    'source_resolution':[sw,sh],
    'source_kind':'Built-in image_gen, using toyosh.jpg as cooked-meat/color reference',
    'microdetail':'Physical height, fat response, oil roughness and fine fibril variation evaluated at native 4096 texels.',
    'physical_swatch_m':.065,
    'source_note':'The generated color source is not a native 4K photograph. Source color is resampled, then supplemented by native 4K procedural microdetail.',
}
(OUT/'meat_4k_material.json').write_text(json.dumps(report,indent=2))
print('MEAT_MAPS_BAKED',json.dumps(report))
