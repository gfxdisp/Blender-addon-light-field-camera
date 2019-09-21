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

from . import render
from . import param
from . import util
from . import view
from . import scene

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
