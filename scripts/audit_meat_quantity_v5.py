import sys
sys.path.insert(0,'/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/scripts')
from food_v4_utils import *
scene=bpy.data.scenes['ToyOsh'];bpy.context.window.scene=scene
asset=bpy.data.collections['ToyOsh_Asset'];report=json.loads((OUT/'meat_quantity_v5.json').read_text())
counts={name:len(components(bpy.data.objects[name])) for name in ['03_Individual_Long_Grain_Rice','09_Additional_Surface_Rice','10_Rice_Gap_Fill','04_Braised_Yellow_and_Orange_Carrots']}
assert sum(counts[k] for k in counts if 'Rice' in k)==10000
assert counts['04_Braised_Yellow_and_Orange_Carrots']==90
unchanged={}
for name,old in report['original_objects_preserved'].items():
    ob=bpy.data.objects[name];a=np.asarray([tuple(ob.matrix_world@v.co) for v in ob.data.vertices],np.float32)
    unchanged[name]=hashlib.sha256(a.tobytes()+topology_uv_hash(ob).encode()).hexdigest()==old
assert all(unchanged.values())
tree,labels=bvh_objects(asset.objects,True);target=Vector((0,0,.027));coverage=[]
views=[('top',Vector((0,0,1))),('angle',Vector((.65,-.8,.8)).normalized())]
for name,x,y in [('front',0,-1),('back',0,1),('left',-1,0),('right',1,0)]:views.append((name,Vector((x*math.cos(math.radians(15)),y*math.cos(math.radians(15)),math.sin(math.radians(15))))))
for name,direction in views:
    right=Vector((0,0,1)).cross(direction)
    if right.length<.001:right=Vector((1,0,0))
    right.normalize();up=direction.cross(right).normalized();exposed=food=0
    height=.26 if name=='top' else .19
    for py in np.linspace(-height/2,height/2,160):
        for px in np.linspace(-.135,.135,160):
            p,n,i,d=tree.ray_cast(target+direction*.4+right*float(px)+up*float(py),-direction)
            if i is None:continue
            if labels[i]!=60:food+=1
            if labels[i]==10:exposed+=1
    coverage.append({'view':name,'exposed_core_rays':exposed,'food_rays':food,'core_exposure_fraction':exposed/max(1,food)})
print('COVERAGE',json.dumps(coverage),flush=True)
assert max(v['core_exposure_fraction'] for v in coverage)<.005
assert all(p['contact_samples']>0 for p in report['support'])
audit={'passed':True,'counts':counts,'preserved_objects':unchanged,'coverage':coverage,'maximum_core_exposure_fraction':max(v['core_exposure_fraction'] for v in coverage),'new_meat_groups_have_support':True,'triangles':report['triangles']}
(OUT/'meat_quantity_geometry_audit_v5.json').write_text(json.dumps(audit,indent=2))
print('MEAT_V5_AUDIT',json.dumps(audit),flush=True)
