# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import math
import sys
import os

import bpy
from mathutils import Matrix, Vector

from .log import log, LogStyles


def get_addon_bl_info():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    m = sys.modules[a]
    return m.bl_info


def get_plugin_id():
    bli = get_addon_bl_info()
    n = bli.get('name', "")
    d = bli.get('description', "")
    v = bli.get('version', (0, 0, 0, ))
    v = ".".join([str(i) for i in v])
    r = ""
    if(n != ""):
        r = "{} ({}), version: {}".format(n, d, v)
    return r


def add_object(name, data):
    """Fastest way of adding new objects.
    All existing objects gets deselected, then new one is added, selected and made active.
    
    name - Name of the new object
    data - Data of the new object, Empty objects can be added by passing None.
    Returns newly created object.
    
    About 40% faster than object_utils.object_data_add and with Empty support.
    """
    
    so = bpy.context.scene.objects
    for i in so:
        i.select = False
    o = bpy.data.objects.new(name, data)
    so.link(o)
    o.select = True
    if(so.active is None or so.active.mode == 'OBJECT'):
        so.active = o
    return o


def wipe_out_object(ob, and_data=True):
    # http://blenderartists.org/forum/showthread.php?222667-Remove-object-and-clear-from-memory&p=1888116&viewfull=1#post1888116
    
    data = bpy.data.objects[ob.name].data
    # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
    # so if there's more than one user for this data, never wipeOutData. will be done with the last user
    # if in the list
    if(data is not None):
        # change: if wiping empty, data in None and following will raise exception
        if(data.users > 1):
            and_data = False
    else:
        and_data = False
    
    # odd:
    ob = bpy.data.objects[ob.name]
    # if the ob (board) argument comes from bpy.data.groups['aGroup'].objects,
    #  bpy.data.groups['board'].objects['board'].users_scene
    
    for sc in ob.users_scene:
        sc.objects.unlink(ob)
    
    try:
        bpy.data.objects.remove(ob)
    except:
        log('data.objects.remove issue with %s' % ob.name, style=LogStyles.ERROR, )
    
    # never wipe data before unlink the ex-user object of the scene else crash (2.58 3 770 2)
    if(and_data):
        wipe_out_data(data)


def wipe_out_data(data):
    # http://blenderartists.org/forum/showthread.php?222667-Remove-object-and-clear-from-memory&p=1888116&viewfull=1#post1888116
    
    if(data.users == 0):
        try:
            data.user_clear()
            if type(data) == bpy.types.Mesh:
                bpy.data.meshes.remove(data)
            elif type(data) == bpy.types.PointLamp:
                bpy.data.lamps.remove(data)
            elif type(data) == bpy.types.Camera:
                bpy.data.cameras.remove(data)
            elif type(data) in [bpy.types.Curve, bpy.types.TextCurve]:
                bpy.data.curves.remove(data)
            elif type(data) == bpy.types.MetaBall:
                bpy.data.metaballs.remove(data)
            elif type(data) == bpy.types.Lattice:
                bpy.data.lattices.remove(data)
            elif type(data) == bpy.types.Armature:
                bpy.data.armatures.remove(data)
            else:
                log('data still here : forgot %s' % type(data), style=LogStyles.ERROR, )
        except:
            log('%s has no user_clear attribute.' % data.name, style=LogStyles.ERROR, )
    else:
        log('%s has %s user(s) !' % (data.name, data.users), style=LogStyles.ERROR, )


class InstanceMeshGenerator():
    """base instance mesh generator class"""
    def __init__(self):
        self.def_verts, self.def_edges, self.def_faces = self.generate()
        self.exponent_v = len(self.def_verts)
        self.exponent_e = len(self.def_edges)
        self.exponent_f = len(self.def_faces)
    
    def generate(self):
        dv = []
        de = []
        df = []
        # -------------------------------------------
        
        dv.append((0, 0, 0))
        
        # -------------------------------------------
        return dv, de, df


class CylinderMeshGenerator(InstanceMeshGenerator):
    def __init__(self, height=1, radius=0.5, sides=6, z_translation=0, z_rotation=0, z_scale=1, ngon_fill=True, inverse=False, enhanced=False, hed=-1, ):
        if(height <= 0):
            log("height is (or less than) 0, which is ridiculous. setting to 0.001..", 1)
            height = 0.001
        self.height = height
        
        if(radius <= 0):
            log("radius is (or less than) 0, which is ridiculous. setting to 0.001..", 1)
            radius = 0.001
        self.radius = radius
        
        if(sides < 3):
            log("sides are less than 3 which is ridiculous. setting to 3..", 1)
            sides = 3
        self.sides = sides
        
        self.z_translation = z_translation
        self.z_rotation = z_rotation
        if(z_scale <= 0):
            log("z scale is (or less than) 0, which is ridiculous. setting to 0.001..", 1)
            z_scale = 0.001
        self.z_scale = z_scale
        
        self.ngon_fill = ngon_fill
        self.inverse = inverse
        
        self.enhanced = enhanced
        if(self.enhanced):
            if(self.radius < self.height):
                if(hed == -1):
                    # default
                    hed = self.radius / 8
                elif(hed <= 0):
                    log("got ridiculous holding edge distance (smaller or equal to 0).. setting to radius/8", 1)
                    hed = self.radius / 8
                elif(hed >= self.radius):
                    log("got ridiculous holding edge distance (higher or equal to radius).. setting to radius/8", 1)
                    hed = self.radius / 8
            else:
                if(hed == -1):
                    # default
                    hed = self.height / 8
                elif(hed <= 0):
                    log("got ridiculous holding edge distance (smaller or equal to 0).. setting to height/8", 1)
                    hed = self.height / 8
                elif(hed >= self.height):
                    log("got ridiculous holding edge distance (higher or equal to height).. setting to height/8", 1)
                    hed = self.height / 8
        self.hed = hed
        
        super(CylinderMeshGenerator, self).__init__()
    
    def generate(self):
        dv = []
        de = []
        df = []
        # -------------------------------------------
        
        zt = Matrix.Translation(Vector((0, 0, self.z_translation)))
        zr = Matrix.Rotation(math.radians(self.z_rotation), 4, (0.0, 0.0, 1.0))
        zs = Matrix.Scale(self.z_scale, 4, (0.0, 0.0, 1.0))
        inv = 0
        if(self.inverse):
            inv = 180
        ri = Matrix.Rotation(math.radians(inv), 4, (0.0, 1.0, 0.0))
        mat = zt * zr * zs * ri
        
        def circle2d_coords(radius, steps, offset, ox, oy):
            r = []
            angstep = 2 * math.pi / steps
            for i in range(steps):
                x = math.sin(i * angstep + offset) * radius + ox
                y = math.cos(i * angstep + offset) * radius + oy
                r.append((x, y))
            return r
        
        def do_quads(o, s, q, cw):
            r = []
            for i in range(s):
                a = o + ((s * q) + i)
                b = o + ((s * q) + i + 1)
                if(b == o + ((s * q) + s)):
                    b = o + (s * q)
                c = o + ((s * q) + i + s)
                d = o + ((s * q) + i + s + 1)
                if(d == o + ((s * q) + s + s)):
                    d = o + ((s * q) + s)
                # debug
                # print(a, b, c, d)
                # production
                # print(a, c, d, b)
                # if(cw):
                #     df.append((a, b, d, c))
                # else:
                #     df.append((a, c, d, b))
                
                if(cw):
                    r.append((a, b, d, c))
                else:
                    r.append((a, c, d, b))
            return r
        
        def do_tris(o, s, c, cw):
            r = []
            for i in range(s):
                a = o + i
                b = o + i + 1
                if(b == o + s):
                    b = o
                # debug
                # print(a, b, c)
                # production
                # print(b, a, c)
                # if(cw):
                #     df.append((a, b, c))
                # else:
                #     df.append((b, a, c))
                if(cw):
                    r.append((a, b, c))
                else:
                    r.append((b, a, c))
            return r
        
        l = self.height
        r = self.radius
        s = self.sides
        h = self.hed
        z = 0.0
        
        if(self.enhanced):
            cvv = []
            
            # holding edge
            c = circle2d_coords(r - h, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], z)))
            
            # bottom circle
            c = circle2d_coords(r, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], z)))
            
            # holding edge
            c = circle2d_coords(r, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], h)))
            
            # holding edge
            c = circle2d_coords(r, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], l - h)))
            
            # bottom circle
            c = circle2d_coords(r, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], l)))
            
            # holding edge
            c = circle2d_coords(r - h, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], l)))
            
            if(self.ngon_fill is False):
                # bottom nad top center vertex
                cvv.append(Vector((z, z, z)))
                cvv.append(Vector((z, z, l)))
            
            for i, v in enumerate(cvv):
                # cvv[i] = v * mat
                cvv[i] = mat * v
            for v in cvv:
                dv.append(v.to_tuple())
            
            qr = 5
            for q in range(qr):
                df.extend(do_quads(0, s, q, False))
            
            if(self.ngon_fill):
                ng = []
                for i in range(s):
                    ng.append(i)
                df.append(tuple(ng))
                ng = []
                for i in range(len(dv) - s, len(dv)):
                    ng.append(i)
                df.append(tuple(reversed(ng)))
                
            else:
                df.extend(do_tris(0, s, len(dv) - 2, True))
                df.extend(do_tris(len(dv) - 2 - s, s, len(dv) - 1, False))
            
        else:
            cvv = []
            c = circle2d_coords(r, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], z)))
            c = circle2d_coords(r, s, 0, 0, 0)
            for i in c:
                cvv.append(Vector((i[0], i[1], l)))
            
            if(self.ngon_fill is False):
                cvv.append(Vector((0, 0, 0)))
                cvv.append(Vector((0, 0, l)))
            
            for i, v in enumerate(cvv):
                # cvv[i] = v * mat
                cvv[i] = mat * v
            for v in cvv:
                dv.append(v.to_tuple())
            
            if(self.ngon_fill):
                df.extend(do_quads(0, s, 0, False))
                
                ng = []
                for i in range(s):
                    ng.append(i)
                df.append(tuple(ng))
                ng = []
                for i in range(len(dv) - s, len(dv)):
                    ng.append(i)
                df.append(tuple(reversed(ng)))
                
            else:
                df.extend(do_quads(0, s, 0, False))
                df.extend(do_tris(0, s, len(dv) - 2, True))
                df.extend(do_tris(len(dv) - 2 - s, s, len(dv) - 1, False))
        
        # -------------------------------------------
        return dv, de, df
