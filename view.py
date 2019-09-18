import bpy
from light_field_camera.util import CamPoses

def add_preview_lightfield(self, context):
    self.layout.operator(
        PreviewLightField.bl_idname,
        text='Eanble LightField View',
        icon='VIEW3D')

class PreviewLightField(bpy.types.Operator):
    bl_idname = "view3d.lightfield_preview"
    bl_label = "interface for preview light field"

    camera = None
    poses = None
    current_pos = [0, 0]
    setup = {}

    def update_view(self, s, t):
        s, t = self.poses.bound(s, t)
        self.current_pos = s, t
        self.camera.location = self.poses[s, t]

    def init(self, context):
        self.camera = context.object
        space = context.area.spaces.active
        self.setup['perspective'] = space.region_3d.view_perspective
        bpy.ops.view3d.object_as_camera()
        self.reset(context)

    def clear(self, context):
        self.camera.location = self.poses.pos
        space = context.area.spaces.active
        space.region_3d.view_perspective = self.setup['perspective']
        self.camera = None
        self.poses = None

    def reset(self, context):
        # shift camera back to the center
        if self.poses:
            shift = self.camera.location - self.poses[self.current_pos]
            self.camera.location = self.poses.pos + shift

        self.poses = CamPoses(self.camera)
        lf = self.camera.lightfield
        self.update_view(lf.num_rows//2, lf.num_cols//2)

    def modal(self, context, event):
        if event.type == 'ESC':
            self.clear(context)
            return {'FINISHED'}
        s, t = self.current_pos
        update = {
            'LEFT_ARROW': (0, -1),
            'RIGHT_ARROW': (0, 1),
            'UP_ARROW': (-1, 0),
            'DOWN_ARROW': (1, 0)
        }
        if event.type in update:
            ds, dt = update[event.type]
            self.update_view(s+ds, t+dt)
            return {'RUNNING_MODAL'}
        elif event.type == 'RET':
            self.reset(context)
            return {'RUNNING_MODAL'}
        else:
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        cam = context.object
        if cam.type != 'CAMERA' or not cam.lightfield.enabled:
            return {'FINISHED'}
        self.init(context)
        context.window_manager.modal_handler_add(self)
        # bpy.ops.view3d.camera_to_view()
        return {'RUNNING_MODAL'}
