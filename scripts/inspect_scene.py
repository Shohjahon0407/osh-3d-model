import bpy
result = {
    'version': bpy.app.version_string,
    'filepath': bpy.data.filepath,
    'scenes': [{'name': s.name, 'objects': [
        {'name': o.name, 'type': o.type, 'location': list(o.location)}
        for o in s.objects]} for s in bpy.data.scenes],
}
