"""Pack the cleaned under-meat rice image without changing the 4K meat maps."""
import bpy,pathlib
out=pathlib.Path('/home/shohjahon/MARKETPLACE/5kashtan/3dview_generator/output/toyosh')
mat=bpy.data.materials['ToyOsh_Photo_Guided_Rice_Bed']
node=mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].links[0].from_node
im=bpy.data.images.load(str(out/'textures/rice_bed_without_old_meat.jpg'),check_existing=True)
im.pack();node.image=im
bpy.ops.wm.save_as_mainfile(filepath=str(out/'toyosh.blend'))
