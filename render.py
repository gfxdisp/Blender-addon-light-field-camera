import bpy
from .util import CamPoses
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
        images = bpy.data.images
        if geo.enabled:
            self.init(context)
            bpy.ops.render.render()
            self.clear(context)
            types = [ 'depth', 'normal', 'flow' ]
            for type in types:
                if getattr(geo, type):
                    images.load(
                            path.join(geo.base_path, f'{type}{idx:04d}.exr'),
                        check_existing=False)
                    if images.get(type):
                        images.remove(images[type])
                    images[f'{type}{idx:04d}.exr'].name = f'geo_{type}'
        return {'FINISHED'}

class RenderLightField(bpy.types.Operator):
    bl_idname = "render.lightfield_render"
    bl_label = "render light field"

    rendering = False
    done = False
    timer = None
    poses = None
    progress = 0

    path: bpy.props.StringProperty(default='')

    def write_meta(self, context):
        lf = context.scene.camera.lightfield
        with open(path.join(self.path, 'param.txt'), 'w') as f:
            f.write(f'cmera: {context.scene.camera.name}\n')
            f.write(f'num_x: {lf.num_x}\n')
            f.write(f'num_y: {lf.num_y}\n')
            f.write(f'base_x: {lf.base_x}\n')
            f.write(f'base_y: {lf.base_y}\n')

    def pre(self, scene):
        print(f'render on {self.progress:03d}/{len(self.poses):03d}')
        s, t = self.poses.idx2pos(self.progress)
        save_path = path.join(self.path, f'{s:02}_{t:02}')
        scene.render.filepath = save_path
        scene.camera.location = self.poses[self.progress]
        self.rendering = True

    def post(self, scene):
        self.progress += 1
        self.rendering = False
        self.done = self.progress >= len(self.poses)

    def init(self, context):
        self.rendering = False
        self.poses = CamPoses(context.scene.camera)
        self.progress = 0
        self.path = context.scene.render.filepath
        bpy.app.handlers.render_init.append(self.pre)
        bpy.app.handlers.render_write.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        context.scene.render.filepath = self.path
        bpy.app.handlers.render_init.remove(self.pre)
        bpy.app.handlers.render_write.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)

        context.scene.camera.location = self.poses.pos

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        if context.object.type == 'CAMERA' and context.object.lightfield.enabled:
            context.scene.camera = context.object
        self.init(context)
        self.write_meta(context)
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
        self.init(context)
        self.write_meta(context)
        while not self.done:
            bpy.ops.render.render(write_still=True)
        self.clear(context)

        return {'FINISHED'}



