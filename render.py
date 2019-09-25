import bpy
from . import util
import os.path as path
import numpy as np

def register():
    bpy.utils.register_class(RenderLightField)
    bpy.utils.register_class(RenderGeometry)
    bpy.utils.register_class(RenderDisparity)

def unregister():
    bpy.utils.unregister_class(RenderLightField)
    bpy.utils.unregister_class(RenderGeometry)
    bpy.utils.unregister_class(RenderDisparity)

class RenderGeometry(bpy.types.Operator):
    bl_idname = "render.geometry_render"
    bl_label = "render geometry"

    samples = 1

    def init(self, context):
        scene = context.scene
        if scene.render.engine == 'CYCLES':
            self.samples = scene.cycles.samples
            scene.cycles.samples = 1
        elif scene.render.engine == 'BLENDER_EEVEE':
            self.samples = scene.eevee.taa_render_samples
            scene.eevee.taa_render_samples = 1 # sampling does not matter in this case

    def post(self, context):
        images = bpy.data.images
        geo = context.scene.geo
        idx = context.scene.frame_current
        types = [ 'depth', 'normal', 'flow' ]
        geo = context.scene.geo
        for type in types:
            if getattr(geo, type):
                image = images.load(
                        path.join(geo.base_path, f'{type}{idx:04d}.exr'),
                        check_existing=False)
                key = f'geo_{type}'
                if images.get(key):
                    images.remove(images[key])
                image.name = key

    def clear(self, context):
        scene = context.scene
        if scene.render.engine == 'CYCLES':
            scene.cycles.samples = self.samples
        elif scene.render.engine == 'BLENDER_EEVEE':
            scene.eevee.taa_render_samples = self.samples

    def execute(self, context):
        if context.scene.geo.enabled:
            self.init(context)
            bpy.ops.render.render()
            self.post(context)
            self.clear(context)
        return {'FINISHED'}

class RenderDisparity(bpy.types.Operator):
    bl_idname = "render.disparity"
    bl_label = "render light field disparity"

    setup = {}

    def disparity(self, context):
        # from imageio import imwrite, imread
        cam = context.scene.camera
        images = bpy.data.images
        im_depth = images['geo_depth']
        z = util.imread(im_depth.filepath)[...,0]
        b = cam.lightfield.base_x
        # TODO: check all units
        f = cam.data.lens # focal length
        s = cam.data.sensor_width #  sensor size
        r = context.scene.render.resolution_x # resolution
        disparity = (f*b*r)/(s*z)
        filepath = path.join(context.scene.render.filepath, 'disparity')
        cam.lightfield.max_depth = z.max() * s / (f*r)
        cam.lightfield.min_depth = z.min() * s / (f*r)
        np.save(filepath, disparity)
        # util.imwrite(filepath, disparity)
        # image = images.load(filepath=filepath+'.exr', check_existing=False)
        # key = 'lf_disparity'
        # if images.get(key):
        #     images.remove(images[key])
        # image.name = key

    def init(self, context):
        scene = context.scene
        for type in ['depth', 'normal', 'flow', 'enabled']:
            self.setup[f'geo_{type}'] = getattr(scene.geo, type)
        scene.geo.enabled = True
        scene.geo.depth = True
        scene.geo.normal = False
        scene.geo.flow = False

    def clear(self, context):
        scene = context.scene
        for type in ['depth', 'normal', 'flow', 'enabled']:
            setattr(scene.geo, type, self.setup[f'geo_{type}'])

    def invoke(self, context, event):
        if context.object.type == 'CAMERA' and context.object.lightfield == 'enabled':
            context.scene.camera = context.object
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        self.init(context)
        bpy.ops.render.geometry_render()
        self.disparity(context)
        self.clear(context)
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
            f.write(f'num_x: {lf.num_cols}\n')
            f.write(f'num_y: {lf.num_rows}\n')
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
        self.poses = util.CamPoses(context.scene.camera)
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

