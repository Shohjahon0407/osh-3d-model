"""Reuse occluded gap-fill grains to cover the remaining visible core pixels.

Keeps the selected 10k grain / 350k triangle budgets. Only existing adaptive
grains are translated; no photograph or flat fill is used to conceal holes.
"""
import pathlib
ROOT=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator')
exec(compile((ROOT/'scripts/food_v4_utils.py').read_text(),'<food utilities>','exec'))
from collections import Counter
scene=bpy.data.scenes['ToyOsh'];win=bpy.data.window_managers[0].windows[0];win.scene=scene
asset=bpy.data.collections['ToyOsh_Asset']
providers=[bpy.data.objects['10_Rice_Gap_Fill'],bpy.data.objects['09_Additional_Surface_Rice']]
entries=[];vertex_group={}
for ob in providers:
    parts=components(ob)
    assert len(parts)==(500 if ob.name.startswith('10_') else 3000)
    lookup={}
    for part in parts:
        index=len(entries);entries.append((ob,part))
        lookup.update({v:index for v in part})
    vertex_group[ob.name]=lookup
plate_tree=bvh_objects([bpy.data.objects['01_Handpainted_Porcelain_Lagan']])

def scan(resolution=112):
    vv=[];ff=[];labels=[]
    for ob in asset.objects:
        ob.data.calc_loop_triangles();start=len(vv)
        vv.extend(tuple(ob.matrix_world@v.co) for v in ob.data.vertices)
        for tri in ob.data.loop_triangles:
            ff.append(tuple(start+i for i in tri.vertices))
            labels.append(1000+vertex_group[ob.name][tri.vertices[0]] if ob.name in vertex_group else int(ob.get('food_class',50)))
    tree=BVHTree.FromPolygons(vv,ff,all_triangles=True)
    tilt=math.radians(15)
    views=[('top',Vector((0,0,1))),('angle',Vector((.65,-.8,.8)).normalized()),
           ('front_low',Vector((0,-math.cos(tilt),math.sin(tilt)))),('back_low',Vector((0,math.cos(tilt),math.sin(tilt)))),
           ('left_low',Vector((-math.cos(tilt),0,math.sin(tilt)))),('right_low',Vector((math.cos(tilt),0,math.sin(tilt))))]
    report=[];holes=[];used=Counter()
    for name,direction in views:
        right=Vector((0,0,1)).cross(direction)
        if right.length<.001:right=Vector((1,0,0))
        right.normalize();up=direction.cross(right).normalized()
        camera=Vector((0,0,.027))+direction*.40
        food=0;exposed=0;height=.26 if name=='top' else .19
        for y in np.linspace(-height/2,height/2,resolution):
            for x in np.linspace(-.135,.135,resolution):
                hit,n,index,d=tree.ray_cast(camera+right*float(x)+up*float(y),-direction)
                if hit is None:continue
                label=labels[index]
                if label!=60:food+=1
                if label>=1000:used[label-1000]+=1
                if label==10:exposed+=1;holes.append((hit.copy(),direction.copy()))
        report.append({'view':name,'food_rays':food,'exposed_core_rays':exposed,'core_exposure_fraction':exposed/max(1,food)})
    del tree,vv,ff,labels;gc.collect()
    return report,holes,used

history=[];moved=0
for iteration in range(8):
    resolution=112 if iteration<3 else 160
    report,holes,used=scan(resolution)
    maximum=max(v['core_exposure_fraction'] for v in report)
    history.append({'iteration':iteration,'resolution':resolution,'maximum_core_exposure':maximum,
                    'core_rays':[r['exposed_core_rays'] for r in report]})
    if maximum<.003 and iteration>=3:break
    unused={i for i in range(len(entries)) if not used[i]}
    if not unused:break
    centers={i:sum((entries[i][0].matrix_world@entries[i][0].data.vertices[j].co for j in entries[i][1]),Vector())/len(entries[i][1]) for i in unused}
    # Spatially separate targets so nearby rays share the same new grain.
    picked=set()
    for hit,direction in holes:
        if not unused:break
        key=tuple(round(a/.0018) for a in hit)
        if key in picked:continue
        picked.add(key)
        gi=min(unused,key=lambda i:(centers[i]-hit).length_squared)
        unused.remove(gi)
        ob,part=entries[gi]
        target=hit+direction*.00020
        delta=target-centers[gi]
        world=[ob.matrix_world@ob.data.vertices[j].co+delta for j in part]
        lift=0
        for p in world:
            floor=z_hit(plate_tree,p.x,p.y)
            if floor is not None:lift=max(lift,floor+.00004-p.z)
        delta.z+=lift
        local=ob.matrix_world.inverted().to_3x3()@delta
        for j in part:ob.data.vertices[j].co+=local
        moved+=1
    for ob in providers:ob.data.update()
final,holes,used=scan(160)
food=json.loads((OUT/'food_v4.json').read_text())
food['coverage_after']=final
food['maximum_core_exposure_fraction']=max(r['core_exposure_fraction'] for r in final)
food['coverage_refinement']={'translated_grains':moved,'history':history,'final_scan_resolution':160}
(OUT/'food_v4.json').write_text(json.dumps(food,indent=2))
with bpy.context.temp_override(window=win):bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'toyosh.blend'))
result={'translated_grains':moved,'core_exposure':food['maximum_core_exposure_fraction'],'views':final}
