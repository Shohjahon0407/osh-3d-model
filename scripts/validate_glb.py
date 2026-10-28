"""Offline GLB integrity checks independent of Blender's importer."""
import hashlib, io, json, math, pathlib, struct
from PIL import Image

out=pathlib.Path(__file__).resolve().parents[1]/'output/toyosh'
raw=(out/'toyosh.glb').read_bytes()
expected=json.loads((out/'validation.json').read_text())
texture_limit=int(expected.get('allowed_texture_dimension',2048))
magic,version,total=struct.unpack_from('<4sII',raw)
assert magic==b'glTF' and version==2 and total==len(raw)
pos=12;chunks={}
while pos<len(raw):
    length,kind=struct.unpack_from('<I4s',raw,pos)
    assert length%4==0
    chunks[kind]=raw[pos+8:pos+8+length];pos+=8+length
assert pos==len(raw)
doc=json.loads(chunks[b'JSON']);binary=chunks[b'BIN\0']
assert len(doc['buffers'])==1 and 'uri' not in doc['buffers'][0]
assert doc['buffers'][0]['byteLength']<=len(binary)
for view in doc['bufferViews']:
    assert view.get('buffer',0)==0
    assert view.get('byteOffset',0)+view['byteLength']<=len(binary)
formats={5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}
widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def accessor(index):
    a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
    code,size=formats[a['componentType']];width=widths[a['type']]
    start=view.get('byteOffset',0)+a.get('byteOffset',0)
    stride=view.get('byteStride',size*width)
    assert a.get('byteOffset',0)+max(0,a['count']-1)*stride+width*size<=view['byteLength']
    return [struct.unpack_from('<'+code*width,binary,start+i*stride) for i in range(a['count'])]
triangles=0
for mesh in doc['meshes']:
    for primitive in mesh['primitives']:
        assert primitive.get('mode',4)==4
        positions=accessor(primitive['attributes']['POSITION'])
        assert all(math.isfinite(v) for p in positions for v in p)
        indices=accessor(primitive['indices'])
        assert len(indices)%3==0 and max(i[0] for i in indices)<len(positions)
        triangles+=len(indices)//3
        normals=accessor(primitive['attributes']['NORMAL'])
        assert all(abs(sum(v*v for v in n)-1)<.005 for n in normals)
        uv=accessor(primitive['attributes']['TEXCOORD_0'])
        assert len(uv)==len(positions)
        assert all(math.isfinite(v) for p in uv for v in p)
images=[]
for im in doc['images']:
    assert 'uri' not in im
    view=doc['bufferViews'][im['bufferView']]
    start=view.get('byteOffset',0)
    data=binary[start:start+view['byteLength']]
    with Image.open(io.BytesIO(data)) as image:
        dimensions=image.size;image.verify()
    assert max(dimensions)<=texture_limit
    images.append({'name':im.get('name'),'dimensions':dimensions,'bytes':len(data)})
if expected.get('meat_detail_version',1)>=2:
    materials={m['name']:m for m in doc['materials']}
    meat=materials['ToyOsh_Cooked_Meat_4K_Cut']
    indices=[meat['pbrMetallicRoughness']['baseColorTexture']['index'],
             meat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],
             meat['normalTexture']['index']]
    for index in indices:
        source_index=doc['textures'][index]['source']
        assert images[source_index]['dimensions']==(4096,4096)
    exterior=materials['ToyOsh_Cooked_Meat_4K_Braised_Exterior']['pbrMetallicRoughness']
    factor=exterior['baseColorFactor']
    assert all(abs(a-b)<1e-5 for a,b in zip(factor,[.68,.68*.97,.68*.94,1]))
    upgrade=json.loads((out/'meat_upgrade.json').read_text())
    if expected.get('meat_detail_version',1)>=3:
        assert upgrade['non_meat_geometry_unchanged']
        assert upgrade['outer_wrapper_mesh'] is False
        assert upgrade['primary_fascicles']+upgrade['secondary_fascicles']>=90
        assert upgrade['inner_muscle_roots']==16
        assert upgrade['sculpted_fissured_roots']
        assert upgrade['loose_shreds']>=15
        assert upgrade['attached_fibers']>=100
        assert all(c['support_contacts']>=1 for c in upgrade['support_contacts'])
    else:
        assert upgrade['non_meat_parts_unchanged']
        assert upgrade['attached_fibers']>=300
if expected.get('food_detail_version',0)>=4:
    food=json.loads((out/'food_v4.json').read_text())
    assert 9500<=food['rice_grains']<=10000
    assert food['carrot_count']==90
    assert food['meat_shape_preserved'] and food['meat_topology_and_uv_preserved']
    assert food['meat_max_rigid_translation_error_m']<2e-7
    assert all(p['contacts']>=1 for p in food['meat_group_placement'])
    assert food['maximum_core_exposure_fraction']<=.005
    for im in images:
        if not im['name'].startswith('cooked_meat_4k'):assert max(im['dimensions'])<=2048
if expected.get('meat_quantity_version',0)>=5:
    quantity=json.loads((out/'meat_quantity_v5.json').read_text())
    geometry=json.loads((out/'meat_quantity_geometry_audit_v5.json').read_text())
    preservation=json.loads((out/'meat_material_preservation_v5.json').read_text())
    for im in doc['images']:
        if im.get('name','').startswith('cooked_meat_4k'):
            view=doc['bufferViews'][im['bufferView']]
            start=view.get('byteOffset',0)
            actual=hashlib.sha256(binary[start:start+view['byteLength']]).hexdigest()
            assert actual==preservation['sha256'][im['name']]
    assert quantity['total_main_clumps']==32 and quantity['total_loose_shreds']==36
    assert quantity['rice_grain_count']==10000
    assert geometry['passed'] and all(geometry['preserved_objects'].values())
    assert geometry['maximum_core_exposure_fraction']<.005
    assert preservation['meat_maps_byte_identical']
    assert all(p['contact_samples']>0 for p in quantity['support'])
assert triangles==expected['triangles']<=int(expected.get('triangle_budget',150000))
assert total<int(expected.get('file_budget_mib',20))*1024*1024
assert not doc.get('cameras')
assert not any('KHR_lights_punctual' in n.get('extensions',{}) for n in doc['nodes'])
source=pathlib.Path(expected['source'])
report={
    'passed':True,'triangles':triangles,'embedded_images':images,
    'external_resources':0,'size_bytes':total,
    'sha256_glb':hashlib.sha256(raw).hexdigest(),
    'sha256_source':hashlib.sha256(source.read_bytes()).hexdigest(),
    'meat_4k_verified':expected.get('meat_detail_version',1)>=2,
    'food_detail_version':int(expected.get('food_detail_version',0)),
    'meat_quantity_version':int(expected.get('meat_quantity_version',0)),
    'checks':['GLB header and chunk lengths','buffer/accessor bounds','finite positions and UVs','unit normals','valid triangle indices','embedded PNG/JPEG integrity','texture dimensions','triangle and file budgets','camera/light exclusion'],
    'validator_note':'Independent offline integrity audit plus Blender reimport; Khronos validator package could not be fetched because npm registry timed out.',
}
(out/'glb_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='embedded_images'},indent=2))
