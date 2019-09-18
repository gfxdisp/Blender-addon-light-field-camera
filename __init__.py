# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Light Field Camera",
    "author" : "Dingcheng Yue",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Render"
}

import bpy
C = bpy.context
D = bpy.data

import light_field_camera.render as render
import light_field_camera.param as param
import light_field_camera.util as util
import light_field_camera.view as view
import importlib
importlib.reload(render)
importlib.reload(param)
importlib.reload(util)
importlib.reload(view)

def register():
    bpy.utils.register_class(render.RenderLightField)
    bpy.utils.register_class(view.PreviewLightField)

    bpy.utils.register_class(param.LFPanel)
    bpy.utils.register_class(param.LFProperty)
    bpy.types.Object.lightfield = bpy.props.PointerProperty(
        type=param.LFProperty)
    bpy.types.VIEW3D_MT_view_viewpoint.append(view.add_preview_lightfield)


def unregister():
    bpy.utils.unregister_class(render.RenderLightField)
    bpy.utils.unregister_class(view.PreviewLightField)

    bpy.utils.unregister_class(param.LFPanel)
    bpy.utils.unregister_class(param.LFProperty)
    del bpy.types.Object.lightfield
    bpy.types.VIEW3D_MT_view_viewpoint.remove(view.add_preview_lightfield)
