import bpy
from .render import RenderLightField, RenderDisparity
from .util import create_plane

def register():
    bpy.utils.register_class(LFProperty)
    bpy.utils.register_class(LFPanel)
    lf = bpy.props.PointerProperty(type=LFProperty)
    bpy.types.Object.lightfield = lf

def unregister():
    bpy.utils.unregister_class(LFProperty)
    bpy.utils.unregister_class(LFPanel)
    del bpy.types.Object.lightfield

def base_x(self):
    if self.plane:
        return self.plane.scale[0] / max(1, self.num_cols-1)
    else:
        return 0
def set_base_x(self, x):
    if self.get('plane'):
        self.max_disp /= self.base_x
        self.min_disp /= self.base_x
        self.plane.scale[0] = x * max(1, self.num_cols-1)
        self.max_disp *= self.base_x
        self.min_disp *= self.base_x


def update_cols(self, context):
    self.plane.scale[0] = self.base_x * max(1, self.num_cols-1)

def base_y(self):
    if self.plane:
        return self.plane.scale[1] / max(1, self.num_rows-1)
    else:
        return 0
def set_base_y(self, y):
    if self.plane:
        self.plane.scale[1] = y * max(1, self.num_rows-1)
def update_rows(self, context):
    self.plane.scale[0] = self.base_y * max(1, self.num_rows-1)


def update_enabled(self, context):
    if (not self.enabled) and self.plane: #enable
        self['num_rows'] = 1
        self['num_cols'] = 1
        self['base_x'] = 1
        self['base_y'] = 1
        bpy.data.objects.remove(self.plane, do_unlink=True)
        self['plane'] = None
    elif self.enabled and (not self.plane): # disable
        cam = context.object
        plane = create_plane(context, size=1.0)
        self['plane'] = plane
        c = plane.constraints.new('COPY_LOCATION')
        c.target = cam
        c = plane.constraints.new('COPY_ROTATION')
        c.target = cam
        plane.hide_render = True
        plane.hide_select = True
        plane.display_type = 'WIRE'
        # cam.data.sensor_fit = 'AUTO'


class LFProperty(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name='enabled',
        default=False,
        description='enable camera to render light field',
        update=update_enabled)

    num_rows: bpy.props.IntProperty(
        name='rows',
        default=1,
        soft_min=0,
        description='number of rows of the camera array')
    num_cols: bpy.props.IntProperty(
        name='cols',
        default=1,
        soft_min=0,
        description='number of columns of the camera array')
    base_x: bpy.props.FloatProperty(
        name='base x',
        soft_min=0,
        get=base_x,
        set=set_base_x,
        description='the x baseline between each camera')
    base_y: bpy.props.FloatProperty(
        name='base y',
        soft_min=0,
        get=base_y,
        set=set_base_y,
        description='the y baseline distance between each camera')
    max_disp: bpy.props.FloatProperty(
        name='max disparity',
        default=0,
        description='the maximum disparity')
    min_disp: bpy.props.FloatProperty(
        name='min disparity',
        default=0,
        description='the minimum disparity')

    plane: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name='plane',
        poll=(lambda self, object: object.type=='MESH'),
        description='the plane for camera array')


class LFPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_lightfield_camera'
    bl_label = 'Light Field'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    def draw_header(self, ctx):
        layout = self.layout
        lf = ctx.object.lightfield
        layout.prop(lf, 'enabled', text='', toggle=False)

    def draw(self, ctx):
        # default spec
        layout = self.layout
        lf = ctx.object.lightfield
        layout.enabled = lf.enabled
        row = layout.row(align=True)
        row.prop(lf, 'num_cols')
        row.prop(lf, 'num_rows')
        row = layout.row(align=True)
        row.prop(lf, 'base_x')
        row.prop(lf, 'base_y')
        layout.separator()
        layout.operator(
            RenderLightField.bl_idname,
            text='Render LightField',
            icon='SCENE')
        layout.operator(
            RenderDisparity.bl_idname,
            text='Render Disparity Map',
            icon='SCENE')
        if lf.max_disp > 0:
            row = layout.row(align=True)
            row.enabled = False
            row.prop(lf, 'max_disp', slider=False)
            row.prop(lf, 'min_disp', slider=False)

    @classmethod
    def poll(cls, ctx):
        return ((ctx.object is not None)
                and ctx.object.type == 'CAMERA')

