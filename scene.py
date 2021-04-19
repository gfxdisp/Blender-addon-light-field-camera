import bpy
import mathutils
import tempfile
from .render import RenderGeometry

def register():
    bpy.utils.register_class(GeoProperty)
    bpy.types.Scene.geo = bpy.props.PointerProperty(type=GeoProperty)
    bpy.utils.register_class(GeoPannel)

def unregister():
    bpy.utils.unregister_class(GeoProperty)
    del bpy.types.Scene.geo
    bpy.utils.unregister_class(GeoPannel)

def update_enabled(self, context):
    scene = context.scene
    if self.enabled:
        compositor_init(scene)
        update_properties(self, context)
    else:
        compositor_destroy(scene)

def compositor_init(scene):
    scene.use_nodes = True
    scene.render.use_compositing = True

    nodes = scene.node_tree.nodes
    links = scene.node_tree.links
    # TODO: store previous states
    for node in nodes:
        if node.type == 'OUTPUT_FILE':
            node.mute = True

    frame = nodes.new('NodeFrame')
    frame.name = 'GeoFrame'
    frame.label = 'Geometric Render'

    inputnode = nodes.new('CompositorNodeRLayers')
    inputnode.name = 'GeoRender'
    inputnode.label = 'Geometric Input'
    inputnode.hide = True
    inputnode.parent = frame

    outputnode = nodes.new('CompositorNodeOutputFile')
    outputnode.name = 'GeoFile'
    outputnode.label = 'Geometric File'
    outputnode.hide = True
    outputnode.parent = frame
    outputnode.format.file_format = 'OPEN_EXR'
    outputnode.format.color_mode = 'RGB'
    outputnode.format.color_depth = '16'

    frame.location = (-50, -50)

def compositor_destroy(scene):
    nodes = scene.node_tree.nodes
    for nodename in ['GeoFrame', 'GeoRender', 'GeoFile']:
        if nodes.get(nodename):
            nodes.remove(nodes[nodename])
    for node in nodes:
        if node.type == 'OUTPUT_FILE':
            node.mute = False

def update_properties(self, context):
    scene = context.scene
    if not self.enabled:
        return
    nodes = scene.node_tree.nodes
    links = scene.node_tree.links

    inputnode = nodes['GeoRender']
    outputnode = nodes['GeoFile']
    outputnode.file_slots.clear()
    outputnode.base_path = self.base_path
    layer = scene.view_layers[inputnode.layer]
    if self.depth:
        layer.use_pass_z = True
        outputnode.file_slots.new('depth')
        link = links.new(inputnode.outputs['Depth'], outputnode.inputs['depth'])
    if self.flow:
        layer.use_pass_vector = True
        outputnode.file_slots.new('flow')
        link = links.new(inputnode.outputs['Vector'], outputnode.inputs['flow'])
    if self.normal:
        layer.use_pass_normal = True
        outputnode.file_slots.new('normal')
        link = links.new(inputnode.outputs['Normal'], outputnode.inputs['normal'])


class GeoProperty(bpy.types.PropertyGroup):

    depth: bpy.props.BoolProperty(
        name='depth', description='render depth',
        update=update_properties)
    flow: bpy.props.BoolProperty(
        name='flow', description='render optical flow',
        update=update_properties)
    normal: bpy.props.BoolProperty(
        name='normal', description='render surface normal',
        update=update_properties)

    enabled: bpy.props.BoolProperty(
        name='enable',
        description='render only geometric property',
        update=update_enabled)
    base_path: bpy.props.StringProperty(
        name='basepath',
        description='the output directory for rendered result',
        subtype='DIR_PATH',
        default=tempfile.gettempdir(),
        update=update_properties)

class GeoPannel(bpy.types.Panel):
    bl_idname = "SCENE_PT_geo"
    bl_label = 'Render Geometry'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw_header(self, context):
        layout = self.layout
        geo = context.scene.geo
        layout.prop(geo, 'enabled', text='', toggle=False)

    def draw(self, context):
        layout = self.layout
        geo = context.scene.geo

        layout.enabled = geo.enabled
        layout.prop(geo, 'base_path', text='')
        layout.label(text='Properties')
        row = layout.grid_flow(align=True, columns=3)
        row.prop(geo, 'depth')
        row.prop(geo, 'flow')
        row.prop(geo, 'normal')

        layout.operator(RenderGeometry.bl_idname, icon='SCENE')

    @classmethod
    def poll(cls, ctx):
        return True
