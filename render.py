import bpy
from light_field_camera.util import CamPoses
import os.path as path

def register():
    bpy.utils.register_class(RenderLightField)
    bpy.utils.register_class(RenderGeometry)

def unregister():
    bpy.utils.unregister_class(RenderLightField)
    bpy.utils.unregister_class(RenderGeometry)

class RenderGeometry(bpy.types.Operator):
    bl_idname = "render.geometry_render"
    bl_label = "render geometry"

    engine = 'EEVEE'
    samples = 1

    def init(self, context):
        scene = context.scene
        self.engine = scene.render.engine
        self.samples = scene.eevee.taa_render_samples
        scene.eevee.taa_render_samples = 1 # sampling does not matter in this case

    def clear(self, context):
        scene = context.scene
        scene.eevee.taa_render_samples = self.samples
        scene.render.engine = self.engine

    def execute(self, context):
        geo = context.scene.geo
        idx = context.scene.frame_current
        if geo.enabled:
            self.init(context)
            bpy.ops.render.render()
            self.clear(context)
            checks = [
                (geo.depth, f'depth{idx:04d}.exr'),
                (geo.normal, f'normal{idx:04d}.exr'),
                (geo.flow, f'flow{idx:04d}.exr')
            ]
            for check, file in checks:
                if check:
                    bpy.data.images.load(
                        path.join(geo.base_path, file),
                        check_existing=False)
        return {'FINISHED'}

class RenderLightField(bpy.types.Operator):
    bl_idname = "render.lightfield_render"
    bl_label = "render light field"

    rendering = False
    done = False
    timer = None
    path = ''

    progress = 0
    camera = None
    poses = None

    def pre(self, scene):
        print(f'render on {self.progress:03d}/{len(self.poses):03d}')
        save_path = path.join(self.path, f'{self.progress:02d}')
        scene.render.filepath = save_path
        self.camera.location = self.poses[self.progress]
        self.rendering = True

    def post(self, scene):
        self.progress += 1
        self.rendering = False
        self.done = self.progress >= len(self.poses)

    def init(self, context):
        self.rendering = False
        self.poses = CamPoses(self.camera)
        self.progress = 0
        self.path = context.scene.render.filepath
        bpy.app.handlers.render_pre.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        context.scene.render.filepath = self.path
        bpy.app.handlers.render_pre.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)

        self.camera.location = self.poses.pos

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        self.camera = context.object
        context.scene.camera = self.camera
        self.init(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
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



