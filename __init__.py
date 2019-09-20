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
import light_field_camera.scene as scene
import importlib
importlib.reload(render)
importlib.reload(param)
importlib.reload(util)
importlib.reload(view)
importlib.reload(scene)

def register():
    param.register()
    render.register()
    view.register()
    scene.register()


def unregister():
    param.unregister()
    render.unregister()
    view.unregister()
    scene.unregister()
