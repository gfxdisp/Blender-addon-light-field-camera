import bpy
import bmesh
from mathutils import Vector
import numpy as np

def im2arr(image):
    h, w = image.size
    c = image.channels
    arr = np.array(image.pixels[:], shape=(h, w, c))
    return arr


def create_plane(context, size=1):
    x = size / 2
    verts = [(-x,-x,0), (x,-x,0), (x,x,0), (-x,x,0)]
    faces = [(0,1,2,3)]
    mesh = bpy.data.meshes.new('lf_plane')
    mesh.from_pydata(verts, [], faces)
    object = bpy.data.objects.new('plane', mesh)
    context.scene.collection.objects.link(object)
    return object

class CamPoses(object):
    def __init__(self, cam):
        self.pos = Vector(cam.location)
        lf = cam.lightfield
        self.grid = (lf.num_rows, lf.num_cols)
        dir = cam.matrix_world.to_3x3().normalized()
        self.dx = dir @ Vector((-1., 0., 0.)) * lf.base_x
        self.dy = dir @ Vector((0., 1., 0.)) * lf.base_y

    def __len__(self):
        return self.grid[0] * self.grid[1]

    def __getitem__(self, index):
        S, T = self.grid
        if isinstance(index, int):
            s, t = self.idx2pos(index)
        else:
            s, t = index
        dx = self.dx * (2*t/(T-1)-1) if T > 1 else Vector((0,0,0))
        dy = self.dy * (2*s/(S-1)-1) if S > 1 else Vector((0,0,0))
        return self.pos + dx + dy

    def bound(self, s, t):
        S, T = self.grid
        return (max(0, min(s, S-1)), max(0, min(t, T-1)))

    def pos2idx(self, s, t):
        T = self.grid[1]
        return s*T+t

    def idx2pos(self, index):
        T = self.grid[1]
        return index // T, index % T
