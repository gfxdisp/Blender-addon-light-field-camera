import bpy
import os
import os.path as path
import numpy as np
from . import util


def register():
    bpy.utils.register_class(RenderLightField)
    bpy.utils.register_class(RenderGeometry)
    bpy.utils.register_class(RenderDisparity)

def unregister():
    bpy.utils.unregister_class(RenderLightField)
    bpy.utils.unregister_class(RenderGeometry)
    bpy.utils.unregister_class(RenderDisparity)

class RenderGeometry(bpy.types.Operator):
    bl_idname = "render.geometry"
    bl_label = "render geometry"

    def init(self, context):
        scene = context.scene
        self.path = scene.render.filepath
        self.engine = scene.render.engine
        self.samples = scene.eevee.taa_render_samples
        self.done = False
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.taa_render_samples = 1 # sampling does not matter in this case

    def clear(self, context):
        scene = context.scene
        scene.render.engine = self.engine
        scene.eevee.taa_render_samples = self.samples
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)

    def cancel(self, context):
        self.done = True

    def post(self, scene, *args):
        self.done = True
        for type in ['depth', 'normal', 'flow']:
            geo = scene.geo
            if getattr(geo, type):
                filepath = path.join(
                    geo.base_path,
                    f'{type}{scene.frame_current:04d}.exr')
                images = bpy.data.images
                key = f'geo_{type}'
                if images.get(key):
                    images.remove(images[key])
                image = images.load(filepath, check_existing=False)
                image.name = key

    # def invoke(self, context, event):
    #     context.window_manager.modal_handler_add(self)
    #     self.timer = context.window_manager.event_timer_add(
    #         0.1, window=context.window)
    #     self.init(context)
    #     bpy.ops.render.render('INVOKE_DEFAULT')
    #     return {'RUNNING_MODAL'}

    # def modal(self, context, event):
    #     if self.done:
    #         context.window_manager.event_timer_remove(self.timer)
    #         self.timer = None
    #         self.clear(context)
    #         return {'FINISHED'}
    #     return {'PASS_THROUGH'}

    def execute(self, context):
        if context.scene.geo.enabled:
            self.init(context)
            bpy.ops.render.render()
            self.clear(context)
        return {'FINISHED'}

class RenderDisparity(bpy.types.Operator):
    bl_idname = "render.disparity"
    bl_label = "render light field disparity"

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
        os.makedirs(context.scene.render.filepath, exist_ok=True)
        filepath = path.join(context.scene.render.filepath, 'disparity')
        cam.lightfield.max_disp = disparity.max()
        cam.lightfield.min_disp = disparity.min()
        np.save(filepath, disparity)
        # util.imwrite(filepath, disparity)
        # image = images.load(filepath=filepath+'.exr', check_existing=False)
        # key = 'lf_disparity'
        # if images.get(key):
        #     images.remove(images[key])
        # image.name = key

    def init(self, context):
        scene = context.scene
        self.setup = {}
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
        bpy.ops.render.geometry()
        self.disparity(context)
        self.clear(context)
        return {'FINISHED'}


class RenderLightField(bpy.types.Operator):
    bl_idname = "render.lightfield"
    bl_label = "render light field"

    path: bpy.props.StringProperty(default='')

    def write_meta(self, context):
        lf = context.scene.camera.lightfield
        with open(path.join(self.path, 'param.txt'), 'w') as f:
            f.write(f'cmera: {context.scene.camera.name}\n')
            f.write(f'num_x: {lf.num_cols}\n')
            f.write(f'num_y: {lf.num_rows}\n')
            f.write(f'base_x: {lf.base_x}\n')
            f.write(f'base_y: {lf.base_y}\n')

    def pre(self, scene, *args):
        print(f'render on {self.progress:03d}/{len(self.poses):03d}')
        s, t = self.poses.idx2pos(self.progress)
        save_path = path.join(self.path, f'{s:02}_{t:02}')
        scene.render.filepath = save_path
        scene.camera.location = self.poses[self.progress]
        self.rendering = True

    def post(self, scene, *args):
        self.progress += 1
        self.rendering = False
        self.done = self.progress >= len(self.poses)

    def init(self, context):
        self.done = False
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
            if not self.rendering:
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

