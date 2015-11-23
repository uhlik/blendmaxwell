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

import os
import math
import shlex
import subprocess
import uuid
import shutil
import struct
import json
import sys
import re

import bpy
from mathutils import Matrix, Vector
from bpy_extras import io_utils
import bmesh

from .log import log, LogStyles
from . import utils
from . import maths
from . import system
from . import rfbin
from . import mxs


class MXSImportMacOSX():
    def __init__(self, mxs_path, emitters, objects, cameras, sun, keep_intermediates=False, ):
        self.TEMPLATE = system.check_for_import_template()
        self.mxs_path = os.path.realpath(mxs_path)
        self.import_emitters = emitters
        self.import_objects = objects
        self.import_cameras = cameras
        self.import_sun = sun
        self.keep_intermediates = keep_intermediates
        self._import()
    
    def _import(self):
        log("{0} {1} {0}".format("-" * 30, self.__class__.__name__), 0, LogStyles.MESSAGE, prefix="", )
        
        self.uuid = uuid.uuid1()
        h, t = os.path.split(self.mxs_path)
        n, e = os.path.splitext(t)
        self.tmp_dir = os.path.join(h, "{0}-tmp-{1}".format(n, self.uuid))
        if(os.path.exists(self.tmp_dir) is False):
            os.makedirs(self.tmp_dir)
        
        self.scene_data_name = "{0}-{1}.json".format(n, self.uuid)
        self.script_name = "{0}-{1}.py".format(n, self.uuid)
        self.scene_data_path = os.path.join(self.tmp_dir, self.scene_data_name)
        
        log("executing script..", 1, LogStyles.MESSAGE)
        self._pymaxwell()
        log("processing objects..", 1, LogStyles.MESSAGE)
        self._process()
        log("cleanup..", 1, LogStyles.MESSAGE)
        self._cleanup()
        log("done.", 1, LogStyles.MESSAGE)
    
    def _process(self):
        """Loop over all data from pymaxwell and create corresponding blender objects."""
        data = None
        
        if(not os.path.exists(self.scene_data_path)):
            raise RuntimeError("Protected MXS?")
        
        with open(self.scene_data_path, 'r') as f:
            data = json.load(f)
        
        for d in data:
            t = None
            try:
                t = d['type']
            except KeyError:
                log("element without type: {0}".format(d), 1, LogStyles.WARNING)
            if(d['type'] == 'EMPTY'):
                o = self._empty(d)
                d['created'] = o
            elif(d['type'] == 'MESH'):
                o = self._mesh(d)
                d['created'] = o
            elif(d['type'] == 'INSTANCE'):
                o = self._instance(d)
                d['created'] = o
            elif(d['type'] == 'CAMERA'):
                o = self._camera(d)
                d['created'] = o
            elif(d['type'] == 'SUN'):
                o = self._sun(d)
                d['created'] = o
            else:
                log("unknown type: {0}".format(t), 1, LogStyles.WARNING)
        
        # log("setting object hierarchy..", 1, LogStyles.MESSAGE)
        # self._hierarchy(data)
        log("setting object transformations..", 1, LogStyles.MESSAGE)
        self._transformations(data)
        log("setting object hierarchy..", 1, LogStyles.MESSAGE)
        self._hierarchy(data)
        log("finalizing..", 1, LogStyles.MESSAGE)
        self._finalize()
    
    def _empty(self, d):
        n = d['name']
        log("empty: {0}".format(n), 2)
        o = utils.add_object(n, None)
        return o
    
    def _mesh(self, d):
        nm = d['name']
        log("mesh: {0}".format(nm), 2)
        
        l = len(d['vertices']) + len(d['triangles'])
        nuv = len(d['trianglesUVW'])
        for i in range(nuv):
            l += len(d['trianglesUVW'][i])
        
        # mesh
        me = bpy.data.meshes.new(nm)
        vs = []
        fs = []
        sf = []
        for v in d['vertices']:
            vs.append(v)
        for t in d['triangles']:
            fs.append((t[0], t[1], t[2]))
            if(t[3] == t[4] == t[5]):
                sf.append(False)
            else:
                sf.append(True)
        
        me.from_pydata(vs, [], fs)
        for i, p in enumerate(me.polygons):
            p.use_smooth = sf[i]
        
        nuv = len(d['trianglesUVW'])
        for i in range(nuv):
            muv = d['trianglesUVW'][i]
            uv = me.uv_textures.new(name="uv{0}".format(i))
            uvloops = me.uv_layers[i]
            for j, p in enumerate(me.polygons):
                li = p.loop_indices
                t = muv[j]
                v0 = (t[0], t[1])
                v1 = (t[3], t[4])
                v2 = (t[6], t[7])
                # no need to loop, maxwell meshes are always(?) triangles
                uvloops.data[li[0]].uv = v0
                uvloops.data[li[1]].uv = v1
                uvloops.data[li[2]].uv = v2
        
        # mr90 = Matrix.Rotation(math.radians(90.0), 4, 'X')
        # me.transform(mr90)
        
        o = utils.add_object(nm, me)
        
        return o
    
    def _instance(self, d):
        log("instance: {0}".format(d['name']), 2)
        m = bpy.data.meshes[d['instanced']]
        o = utils.add_object(d['name'], m)
        return o
    
    def _camera(self, d):
        log("camera: {0}".format(d['name']), 2)
        
        mx_type = d['type']
        mx_name = d['name']
        mx_origin = d['origin']
        mx_focal_point = d['focal_point']
        mx_up = d['up']
        mx_focal_length = d['focal_length']
        mx_sensor_fit = d['sensor_fit']
        mx_film_width = d['film_width']
        mx_film_height = d['film_height']
        mx_xres = d['x_res']
        mx_yres = d['y_res']
        mx_active = d['active']
        mx_zclip = d['zclip']
        mx_zclip_near = d['zclip_near']
        mx_zclip_far = d['zclip_far']
        mx_shift_x = d['shift_x']
        mx_shift_y = d['shift_y']
        
        # convert axes
        cm = io_utils.axis_conversion(from_forward='-Y', to_forward='Z', from_up='Z', to_up='Y')
        cm.to_4x4()
        eye = Vector(mx_origin) * cm
        target = Vector(mx_focal_point) * cm
        up = Vector(mx_up) * cm
        
        cd = bpy.data.cameras.new(mx_name)
        c = bpy.data.objects.new(mx_name, cd)
        bpy.context.scene.objects.link(c)
        
        m = self._matrix_look_at(eye, target, up)
        c.matrix_world = m
        
        # distance
        mx_dof_distance = self._distance(mx_origin, mx_focal_point)
        
        # camera properties
        cd.lens = mx_focal_length
        cd.dof_distance = mx_dof_distance
        cd.sensor_fit = mx_sensor_fit
        cd.sensor_width = mx_film_width
        cd.sensor_height = mx_film_height
        
        cd.clip_start = mx_zclip_near
        cd.clip_end = mx_zclip_far
        cd.shift_x = mx_shift_x / 10.0
        cd.shift_y = mx_shift_y / 10.0
        
        if(mx_active):
            render = bpy.context.scene.render
            render.resolution_x = mx_xres
            render.resolution_y = mx_yres
            render.resolution_percentage = 100
            bpy.context.scene.camera = c
        
        return c
    
    def _sun(self, d):
        n = d['name']
        log("sun: {0}".format(n), 2)
        l = bpy.data.lamps.new(n, 'SUN')
        o = utils.add_object(n, l)
        v = Vector(d['xyz'])
        mrx90 = Matrix.Rotation(math.radians(90.0), 4, 'X')
        v.rotate(mrx90)
        m = self._matrix_look_at(v, Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)))
        o.matrix_world = m
        
        # align sun ray (which is 25bu long) end with scene center
        d = 25
        l, r, s = m.decompose()
        n = Vector((0.0, 0.0, 1.0))
        n.rotate(r)
        loc = maths.shift_vert_along_normal(l, n, d - 1)
        o.location = loc
        
        return o
    
    def _hierarchy(self, data):
        """Set parent child relationships in scene."""
        types = ['MESH', 'INSTANCE', 'EMPTY']
        for d in data:
            t = d['type']
            if(t in types):
                # o = self._get_object_by_name(d['name'])
                o = d['created']
                if(d['parent'] is not None):
                    # p = self._get_object_by_name(d['parent'])
                    p = None
                    for q in data:
                        if(q['name'] == d['parent']):
                            p = q['created']
                            break
                    o.parent = p
    
    def _transformations(self, data):
        """Apply transformation to all objects."""
        types = ['MESH', 'INSTANCE', 'EMPTY']
        mrx90 = Matrix.Rotation(math.radians(90.0), 4, 'X')
        mrxneg90 = Matrix.Rotation(math.radians(-90.0), 4, 'X')
        for d in data:
            t = d['type']
            if(t in types):
                o = d['created']
                if(o.type == 'MESH'):
                    if(d['type'] != 'INSTANCE'):
                        o.data.transform(mrx90)
                
                m = self._base_and_pivot_to_matrix(d)
                o.matrix_local = m * mrxneg90
    
    def _distance(self, a, b):
        ax, ay, az = a
        bx, by, bz = b
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5
    
    def _base_and_pivot_to_matrix(self, d):
        '''
        am = io_utils.axis_conversion(from_forward='-Z', from_up='Y', to_forward='Y', to_up='Z', ).to_4x4()
        b = d['base']
        o = b[0]
        x = b[1]
        y = b[2]
        z = b[3]
        bm = Matrix([(x[0], y[0], z[0], o[0]), (x[1], y[1], z[1], o[1]), (x[2], y[2], z[2], o[2]), (0.0, 0.0, 0.0, 1.0)])
        p = d['pivot']
        o = p[0]
        x = p[1]
        y = p[2]
        z = p[3]
        pm = Matrix([(x[0], y[0], z[0], o[0]), (x[1], y[1], z[1], o[1]), (x[2], y[2], z[2], o[2]), (0.0, 0.0, 0.0, 1.0)])
        mat = am * bm * pm
        obj.matrix_world = mat
        '''
        am = io_utils.axis_conversion(from_forward='-Z', from_up='Y', to_forward='Y', to_up='Z', ).to_4x4()
        
        def cbase_to_matrix4(cbase):
            o = cbase[0]
            x = cbase[1]
            y = cbase[2]
            z = cbase[3]
            m = Matrix([(x[0], y[0], z[0], o[0]),
                        (x[1], y[1], z[1], o[1]),
                        (x[2], y[2], z[2], o[2]),
                        (0.0, 0.0, 0.0, 1.0)])
            return m
        
        bm = cbase_to_matrix4(d['base'])
        pm = cbase_to_matrix4(d['pivot'])
        m = am * bm * pm
        return m
    
    def _matrix_look_at(self, eye, target, up):
        # https://github.com/mono/opentk/blob/master/Source/OpenTK/Math/Matrix4.cs
        
        z = eye - target
        x = up.cross(z)
        y = z.cross(x)
        
        x.normalize()
        y.normalize()
        z.normalize()
        
        rot = Matrix()
        rot[0][0] = x[0]
        rot[0][1] = y[0]
        rot[0][2] = z[0]
        rot[0][3] = 0
        rot[1][0] = x[1]
        rot[1][1] = y[1]
        rot[1][2] = z[1]
        rot[1][3] = 0
        rot[2][0] = x[2]
        rot[2][1] = y[2]
        rot[2][2] = z[2]
        rot[2][3] = 0
        
        # eye not need to be minus cmp to opentk
        # perhaps opentk has z inverse axis
        tran = Matrix.Translation(eye)
        return tran * rot
    
    def _pymaxwell(self):
        # generate script
        self.script_path = os.path.join(self.tmp_dir, self.script_name)
        with open(self.script_path, mode='w', encoding='utf-8') as f:
            # read template
            with open(self.TEMPLATE, encoding='utf-8') as t:
                code = "".join(t.readlines())
            # write template to a new file
            f.write(code)
        
        if(system.PLATFORM == 'Darwin'):
            system.python34_run_script_helper_import(self.script_path, self.mxs_path, self.scene_data_path, self.import_emitters, self.import_objects, self.import_cameras, self.import_sun, )
        elif(system.PLATFORM == 'Linux'):
            pass
        elif(system.PLATFORM == 'Windows'):
            pass
        else:
            pass
    
    def _finalize(self):
        # maybe i am just setting normals badly? how to find out?
        
        # remove strange smooth shading >> cycle edit mode on all meshes..
        # i have no idea why this happens, never happended before, but this seems to fix that.
        cycled_meshes = []
        for o in bpy.data.objects:
            if(o.type == 'MESH'):
                # skip instances, apply only on first mesh multiuser encountered..
                if(o.data in cycled_meshes):
                    pass
                else:
                    bpy.ops.object.select_all(action='DESELECT')
                    o.select = True
                    bpy.context.scene.objects.active = o
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    cycled_meshes.append(o.data)
    
    def _cleanup(self):
        if(self.keep_intermediates):
            return
        
        # remove script, data, temp directory
        def rm(p):
            if(os.path.exists(p)):
                os.remove(p)
            else:
                log("_cleanup(): {} does not exist?".format(p), 1, LogStyles.WARNING, )
        
        rm(self.script_path)
        rm(self.scene_data_path)
        
        if(os.path.exists(self.tmp_dir)):
            os.rmdir(self.tmp_dir)
        else:
            log("_cleanup(): {} does not exist?".format(self.tmp_dir), 1, LogStyles.WARNING, )


class MXSImportWinLin():
    def __init__(self, mxs_path, emitters=True, objects=True, cameras=True, sun=True, ):
        self.mxs_path = os.path.realpath(mxs_path)
        self.import_emitters = emitters
        self.import_objects = objects
        if(self.import_objects):
            self.import_emitters = False
        self.import_cameras = cameras
        self.import_sun = sun
        self._import()
    
    def _import(self):
        log("{0} {1} {0}".format("-" * 30, self.__class__.__name__), 0, LogStyles.MESSAGE, prefix="", )
        reader = mxs.MXSReader(self.mxs_path)
        
        if(self.import_objects or self.import_emitters):
            data = reader.objects(self.import_emitters)
            for d in data:
                t = None
                try:
                    t = d['type']
                except KeyError:
                    log("element without type: {0}".format(d), 1, LogStyles.WARNING)
                if(t is None):
                    continue
                if(t == 'EMPTY'):
                    o = self._empty(d)
                    d['created'] = o
                elif(t == 'MESH'):
                    o = self._mesh(d)
                    d['created'] = o
                elif(t == 'INSTANCE'):
                    o = self._instance(d)
                    d['created'] = o
                else:
                    log("unknown type: {0}".format(t), 1, LogStyles.WARNING)
            
            log("setting object hierarchy..", 1, LogStyles.MESSAGE)
            self._hierarchy(data)
            log("setting object transformations..", 1, LogStyles.MESSAGE)
            self._transformations(data)
            log("finalizing..", 1, LogStyles.MESSAGE)
            self._finalize()
        
        if(self.import_cameras):
            data = reader.cameras()
            for d in data:
                t = None
                try:
                    t = d['type']
                except KeyError:
                    log("element without type: {0}".format(d), 1, LogStyles.WARNING)
                if(t is None):
                    continue
                if(t == 'CAMERA'):
                    o = self._camera(d)
                else:
                    log("unknown type: {0}".format(t), 1, LogStyles.WARNING)
        
        if(self.import_sun):
            data = reader.sun()
            for d in data:
                t = None
                try:
                    t = d['type']
                except KeyError:
                    log("element without type: {0}".format(d), 1, LogStyles.WARNING)
                if(t is None):
                    continue
                if(t == 'SUN'):
                    o = self._sun(d)
                else:
                    log("unknown type: {0}".format(t), 1, LogStyles.WARNING)
        
        log("done.", 1)
    
    def _empty(self, d):
        n = d['name']
        log("empty: {0}".format(n), 2)
        o = utils.add_object(n, None)
        return o
    
    def _mesh(self, d):
        nm = d['name']
        log("mesh: {0}".format(nm), 2)
        
        l = len(d['vertices']) + len(d['triangles'])
        nuv = len(d['trianglesUVW'])
        for i in range(nuv):
            l += len(d['trianglesUVW'][i])
        
        me = bpy.data.meshes.new(nm)
        vs = []
        fs = []
        sf = []
        for v in d['vertices']:
            vs.append(v)
        for t in d['triangles']:
            fs.append((t[0], t[1], t[2]))
            if(t[3] == t[4] == t[5]):
                sf.append(False)
            else:
                sf.append(True)
        
        me.from_pydata(vs, [], fs)
        for i, p in enumerate(me.polygons):
            p.use_smooth = sf[i]
        
        nuv = len(d['trianglesUVW'])
        for i in range(nuv):
            muv = d['trianglesUVW'][i]
            uv = me.uv_textures.new(name="uv{0}".format(i))
            uvloops = me.uv_layers[i]
            for j, p in enumerate(me.polygons):
                li = p.loop_indices
                t = muv[j]
                v0 = (t[0], t[1])
                v1 = (t[3], t[4])
                v2 = (t[6], t[7])
                # no need to loop, maxwell meshes are always(?) triangles
                uvloops.data[li[0]].uv = v0
                uvloops.data[li[1]].uv = v1
                uvloops.data[li[2]].uv = v2
        
        o = utils.add_object(nm, me)
        return o
    
    def _instance(self, d):
        log("instance: {0}".format(d['name']), 2)
        m = bpy.data.meshes[d['instanced']]
        o = utils.add_object(d['name'], m)
        return o
    
    def _camera(self, d):
        log("camera: {0}".format(d['name']), 2)
        
        mx_type = d['type']
        mx_name = d['name']
        mx_origin = d['origin']
        mx_focal_point = d['focal_point']
        mx_up = d['up']
        mx_focal_length = d['focal_length']
        mx_sensor_fit = d['sensor_fit']
        mx_film_width = d['film_width']
        mx_film_height = d['film_height']
        mx_xres = d['x_res']
        mx_yres = d['y_res']
        mx_active = d['active']
        mx_zclip = d['zclip']
        mx_zclip_near = d['zclip_near']
        mx_zclip_far = d['zclip_far']
        mx_shift_x = d['shift_x']
        mx_shift_y = d['shift_y']
        
        # convert axes
        cm = io_utils.axis_conversion(from_forward='-Y', to_forward='Z', from_up='Z', to_up='Y')
        cm.to_4x4()
        eye = Vector(mx_origin) * cm
        target = Vector(mx_focal_point) * cm
        up = Vector(mx_up) * cm
        
        cd = bpy.data.cameras.new(mx_name)
        c = bpy.data.objects.new(mx_name, cd)
        bpy.context.scene.objects.link(c)
        
        m = self._matrix_look_at(eye, target, up)
        c.matrix_world = m
        
        # distance
        mx_dof_distance = self._distance(mx_origin, mx_focal_point)
        
        # camera properties
        cd.lens = mx_focal_length
        cd.dof_distance = mx_dof_distance
        cd.sensor_fit = mx_sensor_fit
        cd.sensor_width = mx_film_width
        cd.sensor_height = mx_film_height
        
        cd.clip_start = mx_zclip_near
        cd.clip_end = mx_zclip_far
        cd.shift_x = mx_shift_x / 10.0
        cd.shift_y = mx_shift_y / 10.0
        
        if(mx_active):
            render = bpy.context.scene.render
            render.resolution_x = mx_xres
            render.resolution_y = mx_yres
            render.resolution_percentage = 100
            bpy.context.scene.camera = c
        
        return c
    
    def _sun(self, d):
        n = d['name']
        log("sun: {0}".format(n), 2)
        l = bpy.data.lamps.new(n, 'SUN')
        o = utils.add_object(n, l)
        v = Vector(d['xyz'])
        mrx90 = Matrix.Rotation(math.radians(90.0), 4, 'X')
        v.rotate(mrx90)
        m = self._matrix_look_at(v, Vector((0.0, 0.0, 0.0)), Vector((0.0, 0.0, 1.0)))
        o.matrix_world = m
        
        # align sun ray (which is 25bu long) end with scene center
        d = 25
        l, r, s = m.decompose()
        n = Vector((0.0, 0.0, 1.0))
        n.rotate(r)
        loc = maths.shift_vert_along_normal(l, n, d - 1)
        o.location = loc
        
        return o
    
    def _hierarchy(self, data):
        types = ['MESH', 'INSTANCE', 'EMPTY']
        for d in data:
            t = d['type']
            if(t in types):
                # o = self._get_object_by_name(d['name'])
                o = d['created']
                if(d['parent'] is not None):
                    # p = self._get_object_by_name(d['parent'])
                    p = None
                    for q in data:
                        if(q['name'] == d['parent']):
                            p = q['created']
                            break
                    o.parent = p
    
    def _transformations(self, data):
        types = ['MESH', 'INSTANCE', 'EMPTY']
        mrx90 = Matrix.Rotation(math.radians(90.0), 4, 'X')
        for d in data:
            t = d['type']
            if(t in types):
                # o = self._get_object_by_name(d['name'])
                o = d['created']
                m = self._base_and_pivot_to_matrix(d)
                if(o.type == 'MESH'):
                    if(d['type'] != 'INSTANCE'):
                        o.data.transform(mrx90)
                o.matrix_local = m
    
    def _distance(self, a, b):
        ax, ay, az = a
        bx, by, bz = b
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5
    
    def _base_and_pivot_to_matrix(self, d):
        b = d['base']
        p = d['pivot']
        o, x, y, z = b
        m = Matrix(((x[0], z[0] * -1, y[0], o[0]),
                    (x[2] * -1, z[2], y[2] * -1, o[2] * -1),
                    (x[1], z[1] * -1, y[1], o[1]),
                    (0.0, 0.0, 0.0, 1.0), ))
        return m
    
    def _matrix_look_at(self, eye, target, up):
        # https://github.com/mono/opentk/blob/master/Source/OpenTK/Math/Matrix4.cs
        
        z = eye - target
        x = up.cross(z)
        y = z.cross(x)
        
        x.normalize()
        y.normalize()
        z.normalize()
        
        rot = Matrix()
        rot[0][0] = x[0]
        rot[0][1] = y[0]
        rot[0][2] = z[0]
        rot[0][3] = 0
        rot[1][0] = x[1]
        rot[1][1] = y[1]
        rot[1][2] = z[1]
        rot[1][3] = 0
        rot[2][0] = x[2]
        rot[2][1] = y[2]
        rot[2][2] = z[2]
        rot[2][3] = 0
        
        # eye not need to be minus cmp to opentk
        # perhaps opentk has z inverse axis
        tran = Matrix.Translation(eye)
        return tran * rot
    
    def _finalize(self):
        # maybe i am just setting normals badly? how to find out?
        
        # remove strange smooth shading >> cycle edit mode on all meshes..
        # i have no idea why this happens, never happended before, but this seems to fix that.
        cycled_meshes = []
        for o in bpy.data.objects:
            if(o.type == 'MESH'):
                # skip instances, apply only on first mesh multiuser encountered..
                if(o.data in cycled_meshes):
                    pass
                else:
                    bpy.ops.object.select_all(action='DESELECT')
                    o.select = True
                    bpy.context.scene.objects.active = o
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    cycled_meshes.append(o.data)


class MXMImportMacOSX():
    def __init__(self, mxm_path, ):
        self.TEMPLATE = system.check_for_import_mxm_template()
        self.mxm_path = os.path.realpath(mxm_path)
        self._import()
    
    def _import(self):
        log("{0} {1} {0}".format("-" * 30, self.__class__.__name__), 0, LogStyles.MESSAGE, prefix="", )
        
        self.uuid = uuid.uuid1()
        h, t = os.path.split(self.mxm_path)
        n, e = os.path.splitext(t)
        self.tmp_dir = os.path.join(h, "{0}-tmp-{1}".format(n, self.uuid))
        if(os.path.exists(self.tmp_dir) is False):
            os.makedirs(self.tmp_dir)
        
        self.data_name = "{0}-{1}.json".format(n, self.uuid)
        self.script_name = "{0}-{1}.py".format(n, self.uuid)
        self.data_path = os.path.join(self.tmp_dir, self.data_name)
        
        log("executing script..", 1, LogStyles.MESSAGE)
        self._pymaxwell()
        log("processing objects..", 1, LogStyles.MESSAGE)
        self._process()
        log("cleanup..", 1, LogStyles.MESSAGE)
        self._cleanup()
        log("done.", 1, LogStyles.MESSAGE)
    
    def _pymaxwell(self):
        # generate script
        self.script_path = os.path.join(self.tmp_dir, self.script_name)
        with open(self.script_path, mode='w', encoding='utf-8') as f:
            # read template
            with open(self.TEMPLATE, encoding='utf-8') as t:
                code = "".join(t.readlines())
            # write template to a new file
            f.write(code)
        
        if(system.PLATFORM == 'Darwin'):
            system.python34_run_script_helper_import_mxm(self.script_path, self.mxm_path, self.data_path, )
        elif(system.PLATFORM == 'Linux'):
            pass
        elif(system.PLATFORM == 'Windows'):
            pass
        else:
            pass
    
    def _process(self):
        data = None
        
        if(not os.path.exists(self.data_path)):
            raise RuntimeError("Protected MXS?")
        
        with open(self.data_path, 'r') as f:
            data = json.load(f)
        
        self.data = data
    
    def _cleanup(self):
        def rm(p):
            if(os.path.exists(p)):
                os.remove(p)
            else:
                log("_cleanup(): {} does not exist?".format(p), 1, LogStyles.WARNING, )
        
        rm(self.script_path)
        rm(self.data_path)
        
        if(os.path.exists(self.tmp_dir)):
            os.rmdir(self.tmp_dir)
        else:
            log("_cleanup(): {} does not exist?".format(self.tmp_dir), 1, LogStyles.WARNING, )


class MXMImportWinLin():
    def __init__(self, mxm_path, ):
        def texture(t):
            if(t is None):
                return None
            if(t.isEmpty()):
                return None
            
            d = {'path': t.getPath(),
                 'use_global_map': t.useGlobalMap,
                 'channel': t.uvwChannelID,
                 'brightness': t.brightness * 100,
                 'contrast': t.contrast * 100,
                 'saturation': t.saturation * 100,
                 'hue': t.hue * 180,
                 'rotation': t.rotation,
                 'invert': t.invert,
                 'interpolation': t.typeInterpolation,
                 'use_alpha': t.useAlpha,
                 'repeat': [t.scale.x(), t.scale.y()],
                 'mirror': [t.uIsMirrored, t.vIsMirrored],
                 'offset': [t.offset.x(), t.offset.y()],
                 'clamp': [int(t.clampMin * 255), int(t.clampMax * 255)],
                 'tiling_units': t.useAbsoluteUnits,
                 'tiling_method': [t.uIsTiled, t.vIsTiled], }
            
            # t.cosA
            # t.doGammaCorrection
            # t.normalMappingFlipGreen
            # t.normalMappingFlipRed
            # t.normalMappingFullRangeBlue
            # t.sinA
            # t.theTextureExtensions
            
            return d
        
        def material(s, m):
            data = {}
            if(m.isNull()):
                return data
            
            # defaults
            bsdfd = {'visible': True, 'weight': 100.0, 'weight_map_enabled': False, 'weight_map': None, 'ior': 0, 'complex_ior': "",
                     'reflectance_0': (0.6, 0.6, 0.6, ), 'reflectance_0_map_enabled': False, 'reflectance_0_map': None,
                     'reflectance_90': (1.0, 1.0, 1.0, ), 'reflectance_90_map_enabled': False, 'reflectance_90_map': None,
                     'transmittance': (0.0, 0.0, 0.0), 'transmittance_map_enabled': False, 'transmittance_map': None,
                     'attenuation': 1.0, 'attenuation_units': 0, 'nd': 3.0, 'force_fresnel': False, 'k': 0.0, 'abbe': 1.0,
                     'r2_enabled': False, 'r2_falloff_angle': 75.0, 'r2_influence': 0.0,
                     'roughness': 100.0, 'roughness_map_enabled': False, 'roughness_map': None,
                     'bump': 30.0, 'bump_map_enabled': False, 'bump_map': None, 'bump_map_use_normal': False,
                     'anisotropy': 0.0, 'anisotropy_map_enabled': False, 'anisotropy_map': None,
                     'anisotropy_angle': 0.0, 'anisotropy_angle_map_enabled': False, 'anisotropy_angle_map': None,
                     'scattering': (0.5, 0.5, 0.5, ), 'coef': 0.0, 'asymmetry': 0.0,
                     'single_sided': False, 'single_sided_value': 1.0, 'single_sided_map_enabled': False, 'single_sided_map': None, 'single_sided_min': 0.001, 'single_sided_max': 10.0, }
            coatingd = {'enabled': False,
                        'thickness': 500.0, 'thickness_map_enabled': False, 'thickness_map': None, 'thickness_map_min': 100.0, 'thickness_map_max': 1000.0,
                        'ior': 0, 'complex_ior': "",
                        'reflectance_0': (0.6, 0.6, 0.6, ), 'reflectance_0_map_enabled': False, 'reflectance_0_map': None,
                        'reflectance_90': (1.0, 1.0, 1.0, ), 'reflectance_90_map_enabled': False, 'reflectance_90_map': None,
                        'nd': 3.0, 'force_fresnel': False, 'k': 0.0, 'r2_enabled': False, 'r2_falloff_angle': 75.0, }
            displacementd = {'enabled': False, 'map': None, 'type': 1, 'subdivision': 5, 'adaptive': False, 'subdivision_method': 0,
                             'offset': 0.5, 'smoothing': True, 'uv_interpolation': 2, 'height': 2.0, 'height_units': 0,
                             'v3d_preset': 0, 'v3d_transform': 0, 'v3d_rgb_mapping': 0, 'v3d_scale': (1.0, 1.0, 1.0), }
            emitterd = {'enabled': False, 'type': 0, 'ies_data': "", 'ies_intensity': 1.0,
                        'spot_map_enabled': False, 'spot_map': "", 'spot_cone_angle': 45.0, 'spot_falloff_angle': 10.0, 'spot_falloff_type': 0, 'spot_blur': 1.0,
                        'emission': 0, 'color': (1.0, 1.0, 1.0, ), 'color_black_body_enabled': False, 'color_black_body': 6500.0,
                        'luminance': 0, 'luminance_power': 40.0, 'luminance_efficacy': 17.6, 'luminance_output': 100.0, 'temperature_value': 6500.0,
                        'hdr_map': None, 'hdr_intensity': 1.0, }
            layerd = {'visible': True, 'opacity': 100.0, 'opacity_map_enabled': False, 'opacity_map': None, 'blending': 0, }
            globald = {'override_map': None, 'bump': False, 'bump_value': 30.0, 'bump_map': None, 'dispersion': False, 'shadow': False,
                       'matte': False, 'priority': 0, 'id': (255, 255, 255), 'active_display_map': None, }
            
            # structure
            structure = []
            nl, _ = m.getNumLayers()
            for i in range(nl):
                l = m.getLayer(i)
                ln, _ = l.getName()
                nb, _ = l.getNumBSDFs()
                bs = []
                for j in range(nb):
                    b = l.getBSDF(j)
                    bn = b.getName()
                    bs.append([bn, b])
                ls = [ln, l, bs]
                structure.append(ls)
            
            # default data
            data['global_props'] = globald.copy()
            data['displacement'] = displacementd.copy()
            data['layers'] = []
            for i, sl in enumerate(structure):
                bsdfs = []
                for j, sb in enumerate(sl[2]):
                    bsdfs.append({'name': sb[0],
                                  'bsdf_props': bsdfd.copy(),
                                  'coating': coatingd.copy(), })
                layer = {'name': sl[0],
                         'layer_props': layerd.copy(),
                         'bsdfs': bsdfs,
                         'emitter': emitterd.copy(), }
                data['layers'].append(layer)
            
            # custom data
            def global_props(m, d):
                t, _ = m.getGlobalMap()
                d['override_map'] = texture(t)
                a, _ = m.getAttribute('bump')
                if(a.activeType == MAP_TYPE_BITMAP):
                    d['bump'] = True
                    d['bump_value'] = a.value
                    d['bump_map'] = texture(a.textureMap)
                else:
                    d['bump'] = False
                    d['bump_value'] = a.value
                    d['bump_map'] = None
                
                d['dispersion'] = m.getDispersion()[0]
                d['shadow'] = m.getMatteShadow()[0]
                d['matte'] = m.getMatte()[0]
                d['priority'] = m.getNestedPriority()[0]
                
                c, _ = m.getColorID()
                d['id'] = [c.r() * 255, c.g() * 255, c.b() * 255]
                return d
            
            data['global_props'] = global_props(m, data['global_props'])
            
            def displacement(m, d):
                if(not m.isDisplacementEnabled()[0]):
                    return d
                d['enabled'] = True
                t, _ = m.getDisplacementMap()
                d['map'] = texture(t)
                
                displacementType, subdivisionLevel, smoothness, offset, subdivisionType, interpolationUvType, minLOD, maxLOD, _ = m.getDisplacementCommonParameters()
                height, absoluteHeight, adaptive, _ = m.getHeightMapDisplacementParameters()
                scale, transformType, mapping, preset, _ = m.getVectorDisplacementParameters()
                
                d['type'] = displacementType
                d['subdivision'] = subdivisionLevel
                d['adaptive'] = adaptive
                d['subdivision_method'] = subdivisionType
                d['offset'] = offset
                d['smoothing'] = bool(smoothness)
                d['uv_interpolation'] = interpolationUvType
                d['height'] = height
                d['height_units'] = absoluteHeight
                d['v3d_preset'] = preset
                d['v3d_transform'] = transformType
                d['v3d_rgb_mapping'] = mapping
                d['v3d_scale'] = (scale.x(), scale.y(), scale.z(), )
                
                return d
            
            data['displacement'] = displacement(m, data['displacement'])
            
            def cattribute_rgb(a):
                if(a.activeType == MAP_TYPE_BITMAP):
                    c = (a.rgb.r(), a.rgb.g(), a.rgb.b())
                    e = True
                    m = texture(a.textureMap)
                else:
                    c = (a.rgb.r(), a.rgb.g(), a.rgb.b())
                    e = False
                    m = None
                return c, e, m
            
            def cattribute_value(a):
                if(a.activeType == MAP_TYPE_BITMAP):
                    v = a.value
                    e = True
                    m = texture(a.textureMap)
                else:
                    v = a.value
                    e = False
                    m = None
                return v, e, m
            
            def layer_props(l, d):
                d['visible'] = l.getEnabled()[0]
                d['blending'] = l.getStackedBlendingMode()[0]
                a, _ = l.getAttribute('weight')
                if(a.activeType == MAP_TYPE_BITMAP):
                    d['opacity'] = a.value
                    d['opacity_map_enabled'] = True
                    d['opacity_map'] = texture(a.textureMap)
                else:
                    d['opacity'] = a.value
                    d['opacity_map_enabled'] = False
                    d['opacity_map'] = None
                return d
            
            def emitter(l, d):
                e = l.getEmitter()
                if(e.isNull()):
                    d['enabled'] = False
                    return d
                
                d['enabled'] = True
                d['type'] = e.getLobeType()[0]
                
                d['ies_data'] = e.getLobeIES()
                d['ies_intensity'] = e.getIESLobeIntensity()[0]
                
                t, _ = e.getLobeImageProjectedMap()
                d['spot_map_enabled'] = (not t.isEmpty())
                
                d['spot_map'] = texture(t)
                d['spot_cone_angle'] = e.getSpotConeAngle()[0]
                d['spot_falloff_angle'] = e.getSpotFallOffAngle()[0]
                d['spot_falloff_type'] = e.getSpotFallOffType()[0]
                d['spot_blur'] = e.getSpotBlur()[0]
                
                d['emission'] = e.getActiveEmissionType()[0]
                ep, _ = e.getPair()
                colorType, units, _ = e.getActivePair()
                
                d['color'] = (ep.rgb.r(), ep.rgb.g(), ep.rgb.b(), )
                d['color_black_body'] = ep.temperature
                
                d['luminance'] = units
                if(units == EMISSION_UNITS_WATTS_AND_LUMINOUS_EFFICACY):
                    d['luminance_power'] = ep.watts
                    d['luminance_efficacy'] = ep.luminousEfficacy
                elif(units == EMISSION_UNITS_LUMINOUS_POWER):
                    d['luminance_output'] = ep.luminousPower
                elif(units == EMISSION_UNITS_ILLUMINANCE):
                    d['luminance_output'] = ep.illuminance
                elif(units == EMISSION_UNITS_LUMINOUS_INTENSITY):
                    d['luminance_output'] = ep.luminousIntensity
                elif(units == EMISSION_UNITS_LUMINANCE):
                    d['luminance_output'] = ep.luminance
                if(colorType == EMISSION_COLOR_TEMPERATURE):
                    d['color_black_body_enabled'] = True
                
                d['temperature_value'] = e.getTemperature()[0]
                a, _ = e.getMXI()
                if(a.activeType == MAP_TYPE_BITMAP):
                    d['hdr_map'] = texture(a.textureMap)
                    d['hdr_intensity'] = a.value
                else:
                    d['hdr_map'] = None
                    d['hdr_intensity'] = a.value
                
                return d
            
            def bsdf_props(b, d):
                d['visible'] = b.getState()[0]
                
                a, _ = b.getWeight()
                if(a.activeType == MAP_TYPE_BITMAP):
                    d['weight_map_enabled'] = True
                    d['weight'] = a.value
                    d['weight_map'] = texture(a.textureMap)
                else:
                    d['weight_map_enabled'] = False
                    d['weight'] = a.value
                    d['weight_map'] = None
                
                r = b.getReflectance()
                d['ior'] = r.getActiveIorMode()[0]
                d['complex_ior'] = r.getComplexIor()
                
                d['reflectance_0'], d['reflectance_0_map_enabled'], d['reflectance_0_map'] = cattribute_rgb(r.getAttribute('color')[0])
                d['reflectance_90'], d['reflectance_90_map_enabled'], d['reflectance_90_map'] = cattribute_rgb(r.getAttribute('color.tangential')[0])
                d['transmittance'], d['transmittance_map_enabled'], d['transmittance_map'] = cattribute_rgb(r.getAttribute('transmittance.color')[0])
                d['attenuation_units'], d['attenuation'] = r.getAbsorptionDistance()
                d['nd'], d['abbe'], _ = r.getIOR()
                d['force_fresnel'], _ = r.getForceFresnel()
                d['k'], _ = r.getConductor()
                d['r2_falloff_angle'], d['r2_influence'], d['r2_enabled'], _ = r.getFresnelCustom()
                
                d['roughness'], d['roughness_map_enabled'], d['roughness_map'] = cattribute_value(b.getAttribute('roughness')[0])
                d['bump'], d['bump_map_enabled'], d['bump_map'] = cattribute_value(b.getAttribute('bump')[0])
                d['bump_map_use_normal'] = b.getNormalMapState()[0]
                d['anisotropy'], d['anisotropy_map_enabled'], d['anisotropy_map'] = cattribute_value(b.getAttribute('anisotropy')[0])
                d['anisotropy_angle'], d['anisotropy_angle_map_enabled'], d['anisotropy_angle_map'] = cattribute_value(b.getAttribute('angle')[0])
                
                a, _ = r.getAttribute('scattering')
                d['scattering'] = (a.rgb.r(), a.rgb.g(), a.rgb.b(), )
                d['coef'], d['asymmetry'], d['single_sided'], _ = r.getScatteringParameters()
                d['single_sided_value'], d['single_sided_map_enabled'], d['single_sided_map'] = cattribute_value(r.getScatteringThickness()[0])
                d['single_sided_min'], d['single_sided_max'], _ = r.getScatteringThicknessRange()
                
                return d
            
            def coating(b, d):
                nc, _ = b.getNumCoatings()
                if(nc > 0):
                    c = b.getCoating(0)
                else:
                    d['enabled'] = False
                    return d
                
                d['enabled'] = True
                d['thickness'], d['thickness_map_enabled'], d['thickness_map'] = cattribute_value(c.getThickness()[0])
                d['thickness_map_min'], d['thickness_map_max'], _ = c.getThicknessRange()
                
                r = c.getReflectance()
                d['ior'] = r.getActiveIorMode()[0]
                d['complex_ior'] = r.getComplexIor()
                
                d['reflectance_0'], d['reflectance_0_map_enabled'], d['reflectance_0_map'] = cattribute_rgb(r.getAttribute('color')[0])
                d['reflectance_90'], d['reflectance_90_map_enabled'], d['reflectance_90_map'] = cattribute_rgb(r.getAttribute('color.tangential')[0])
                
                d['nd'], _, _ = r.getIOR()
                d['force_fresnel'], _ = r.getForceFresnel()
                d['k'], _ = r.getConductor()
                d['r2_falloff_angle'], _, d['r2_enabled'], _ = r.getFresnelCustom()
                
                return d
            
            for i, sl in enumerate(structure):
                l = sl[1]
                data['layers'][i]['layer_props'] = layer_props(l, data['layers'][i]['layer_props'])
                data['layers'][i]['emitter'] = emitter(l, data['layers'][i]['emitter'])
                for j, bs in enumerate(sl[2]):
                    b = bs[1]
                    data['layers'][i]['bsdfs'][j]['bsdf_props'] = bsdf_props(b, data['layers'][i]['bsdfs'][j]['bsdf_props'])
                    data['layers'][i]['bsdfs'][j]['coating'] = coating(b, data['layers'][i]['bsdfs'][j]['coating'])
            
            return data
        
        
        log("{0} {1} {0}".format("-" * 30, self.__class__.__name__), 0, LogStyles.MESSAGE, prefix="", )
        log("path: {}".format(mxm_path), 1, LogStyles.MESSAGE)
        s = Cmaxwell(mwcallback)
        m = s.readMaterial(p)
        if(m.hasMaterialModifier()):
            # TODO: import extension materials
            pass
        self.data = material(s, m)
