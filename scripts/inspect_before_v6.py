import bpy,json,pathlib
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
result={'file':bpy.data.filepath,'scenes':{s.name:len(s.objects) for s in bpy.data.scenes},'objects':[{'name':o.name,'type':o.type,'collections':[c.name for c in o.users_collection],'vertices':len(o.data.vertices) if o.type=='MESH' else 0,'location':list(o.location)} for o in bpy.data.objects],'collections':[c.name for c in bpy.data.collections]}
(out/'before_v6_inspection.json').write_text(json.dumps(result,indent=2))
