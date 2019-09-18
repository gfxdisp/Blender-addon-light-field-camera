import bpy
from light_field_camera.util import CamPoses
import os.path as path

class RenderLightField(bpy.types.Operator):
    bl_idname = "render.lightfield_render"
    bl_label = "button to render light field"

    rendering = False
    done = False
    timer = None
    path = ''

    progress = 0
    camera = None
    poses = None

    def pre(self, context):
        self.rendering = True
        self.camera.location = self.poses[self.progress]
        save_path = path.join(self.path, f'{self.progress:02d}.png')
        context.render.filepath = save_path

    def post(self, context):
        self.progress += 1
        self.rendering = False
        self.done = self.progress >= len(self.poses)

    def init(self, context):
        self.rendering = False
        self.poses = CamPoses(self.camera)
        self.progress = 0
        self.path = context.scene.render.filepath
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        bpy.app.handlers.render_pre.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        context.window_manager.event_timer_remove(self.timer)
        self.timer = None
        context.scene.render.filepath = self.path
        bpy.app.handlers.render_pre.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)

        self.camera.location = self.poses.pos

        self.report({'INFO'}, 'clear')

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.camera = context.object
        context.scene.camera = self.camera
        self.init(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            self.clear(context)
            return {'FINISHED'}
        if event.type == 'TIMER':
            if not self.rendering and self.timer:
                bpy.ops.render.render(
                    "INVOKE_DEFAULT",
                    write_still=True)
        elif event.type == 'ESC':
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        if not (context.object and context.object.lightfield.enabled):
            return {'FINISHED'}
        self.camera = context.scene.camera
        self.init(context)
        while not self.done:
            bpy.ops.render.render(write_still=True)
        self.clear(context)

        return {'FINISHED'}



