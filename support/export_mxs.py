#!/Library/Frameworks/Python.framework/Versions/3.4/bin/python3
# -*- coding: utf-8 -*-

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

import sys
import traceback
import argparse
import textwrap
import json
import struct
import shutil
import math
import datetime
import os

from pymaxwell import *


# logger = None
quiet = False
LOG_FILE_PATH = None


def log(msg, indent=0):
    if(quiet):
        return
    # print("{0}> {1}".format("    " * indent, msg))
    # logger.info("{0}> {1}".format("    " * indent, msg))
    m = "{0}> {1}".format("    " * indent, msg)
    print(m)
    if(LOG_FILE_PATH is not None):
        with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
            f.write("{}{}".format(m, "\n"))


class MXSBinMeshReaderLegacy():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        # signature = 0x004853454D4E4942
        signature = 20357755437992258
        l = r("<q")[0]
        self.offset = 0
        b = r(">q")[0]
        self.offset = 0
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            self.order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            self.order = ">"
        else:
            raise AssertionError("{}: not a MXSBinMesh file".format(self.__class__.__name__))
        o = self.order
        
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINMESH'):
            raise RuntimeError()
        _ = r(o + "?")
        # mesh name
        self.name = r(o + "250s")[0].decode(encoding="utf-8").replace('\x00', '')
        # number of steps
        self.steps = r(o + "i")[0]
        # number of vertices
        self.num_vertices = r(o + "i")[0]
        # vertices
        self.vertices = []
        for i in range(self.num_vertices * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.vertices.append(v)
        # vertex normals
        self.vertices_normals = []
        for i in range(self.num_vertices * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.vertices_normals.append(v)
        # number of triangles
        self.num_triangles = r(o + "i")[0]
        # number of uv channels
        self.num_channels = r(o + "i")[0]
        # uv channels ids
        self.uv_channels = []
        for i in range(self.num_channels):
            self.uv_channels.append(r(o + "i")[0])
        # triangles
        self.triangles = []
        for i in range(self.num_triangles):
            # triangles (int id, (int v1, int v2, int v3), (int n1, int n2, int n3))
            v = (r(o + "i")[0], r(o + "3i"), r(o + "3i"))
            self.triangles.append(v)
        # triangle normals (int id, int step, (float x, float y, float z))
        self.triangles_normals = []
        for i in range(self.num_triangles * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.triangles_normals.append(v)
        # triangle material assigment
        self.triangles_materials = []
        for i in range(self.num_triangles):
            # int id, int material slot/id
            v = (r(o + "i")[0], r(o + "i")[0])
            self.triangles_materials.append(v)
        # uvs
        self.triangles_uvs = []
        for i in range(self.num_triangles * self.num_channels):
            # (int id, int channel id, float u1, float v1, float w1, float u2, float v2, float w3, float u3, float v3, float w3)
            v = (r(o + "i")[0], r(o + "i")[0]) + r(o + "9d")
            self.triangles_uvs.append(v)
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")
        
        self.data = {'channel_uvw': self.uv_channels[:],
                     'f_setNormal': self.triangles_normals[:],
                     'f_setTriangle': self.triangles[:],
                     'f_setTriangleMaterial': self.triangles_materials[:],
                     'f_setTriangleUVW': self.triangles_uvs[:],
                     'name': str(self.name),
                     'v_setNormal': self.vertices_normals[:],
                     'v_setVertex': self.vertices[:], }


class MXSBinHairReaderLegacy():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        signature = 23161492825065794
        l = r("<q")[0]
        self.offset = 0
        b = r(">q")[0]
        self.offset = 0
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            self.order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            self.order = ">"
        else:
            raise AssertionError("{}: not a MXSBinHair file".format(self.__class__.__name__))
        o = self.order
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINHAIR'):
            raise RuntimeError()
        _ = r(o + "?")
        # number floats
        self.num = r(o + "i")[0]
        self.data = r(o + "{}d".format(self.num))
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")


class PercentDone():
    def __init__(self, total, prefix="> ", indent=0):
        self.current = 0
        self.percent = -1
        self.last = -1
        self.total = total
        self.prefix = prefix
        self.indent = indent
        self.t = "    "
        self.r = "\r"
        self.n = "\n"
    
    def step(self, numdone=1):
        if(quiet):
            return
        self.current += numdone
        self.percent = int(self.current / (self.total / 100))
        if(self.percent > self.last):
            sys.stdout.write(self.r)
            sys.stdout.write("{0}{1}{2}%".format(self.t * self.indent, self.prefix, self.percent))
            self.last = self.percent
        if(self.percent >= 100 or self.total == self.current):
            sys.stdout.write(self.r)
            # sys.stdout.write("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n))
            # logger.info("{0}{1}{2}%".format(self.t * self.indent, self.prefix, 100))
            sys.stdout.write("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n))
            if(LOG_FILE_PATH is not None):
                with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
                    f.write("{}".format("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n)))


class Materials():
    db = []


def material_placeholder(s):
    n = 'MATERIAL_PLACEHOLDER'
    # return clone if already loaded
    for p, m, e in Materials.db:
        if(p == n):
            c = m.createCopy()
            cm = s.addMaterial(c)
            return cm
    
    m = s.createMaterial(n)
    l = m.addLayer()
    b = l.addBSDF()
    r = b.getReflectance()
    a = Cattribute()
    a.activeType = MAP_TYPE_BITMAP
    t = CtextureMap()
    mgr = CextensionManager.instance()
    mgr.loadAllExtensions()
    e = mgr.createDefaultTextureExtension('Checker')
    ch = e.getExtensionData()
    ch.setUInt('Number of elements U', 32)
    ch.setUInt('Number of elements V', 32)
    t.addProceduralTexture(ch)
    a.textureMap = t
    r.setAttribute('color', a)
    
    Materials.db.append((n, m, True))
    
    return m


def material(path, s, embed, ):
    r = None
    for p, m, e in Materials.db:
        if(p == path):
            r = m
    if(r is None):
        t = s.readMaterial(path)
        r = s.addMaterial(t)
        Materials.db.append((path, r, embed))
        if(embed is False):
            # set as external
            r.setReference(1, path)
    return r


def texture(d, s):
    t = CtextureMap()
    t.setPath(d['path'])
    
    t.uvwChannelID = d['channel']
    
    t.brightness = d['brightness']
    
    t.contrast = d['contrast']
    t.saturation = d['saturation']
    t.hue = d['hue']
    
    t.useGlobalMap = d['use_override_map']
    t.useAbsoluteUnits = d['tile_method_units']
    
    t.uIsTiled = d['tile_method_type'][0]
    t.vIsTiled = d['tile_method_type'][1]
    
    t.uIsMirrored = d['mirror'][0]
    t.vIsMirrored = d['mirror'][1]
    
    vec = Cvector2D()
    vec.assign(d['offset'][0], d['offset'][1])
    t.offset = vec
    t.rotation = d['rotation']
    t.invert = d['invert']
    t.useAlpha = d['alpha_only']
    if(d['interpolation']):
        t.typeInterpolation = 1
    else:
        t.typeInterpolation = 0
    t.clampMin = d['rgb_clamp'][0]
    t.clampMax = d['rgb_clamp'][1]
    
    vec = Cvector2D()
    vec.assign(d['repeat'][0], d['repeat'][1])
    t.scale = vec
    
    # t.cosA
    # t.doGammaCorrection
    # t.normalMappingFlipGreen
    # t.normalMappingFlipRed
    # t.normalMappingFullRangeBlue
    # t.sinA
    # t.theTextureExtensions
    
    return t


def base_and_pivot(o, d):
    b = d['base']
    p = d['pivot']
    bb = Cbase()
    bb.origin = Cvector(*b[0])
    bb.xAxis = Cvector(*b[1])
    bb.yAxis = Cvector(*b[2])
    bb.zAxis = Cvector(*b[3])
    pp = Cbase()
    pp.origin = Cvector(*p[0])
    pp.xAxis = Cvector(*p[1])
    pp.yAxis = Cvector(*p[2])
    pp.zAxis = Cvector(*p[3])
    o.setBaseAndPivot(bb, pp)


def object_props(o, d):
    if(d['hidden_camera']):
        o.setHideToCamera(True)
    if(d['hidden_camera_in_shadow_channel']):
        o.setHideToCameraInShadowsPass(True)
    if(d['hidden_global_illumination']):
        o.setHideToGI(True)
    if(d['hidden_reflections_refractions']):
        o.setHideToReflectionsRefractions(True)
    if(d['hidden_zclip_planes']):
        o.excludeOfCutPlanes(True)
    if(d['opacity'] != 100.0):
        o.setOpacity(d['opacity'])
    if(d['hide']):
        o.setHide(d['hide'])
    c = Crgb()
    cc = [c / 255 for c in d['object_id']]
    c.assign(*cc)
    o.setColorID(c)


def camera(d, s):
    c = s.addCamera(d['name'], d['number_of_steps'], d['shutter'], d['film_width'], d['film_height'], d['iso'],
                    d['aperture'], d['diaphragm_angle'], d['diaphragm_blades'], d['frame_rate'],
                    d['resolution_x'], d['resolution_y'], d['pixel_aspect'], d['lens'], )
    
    # shutter_angle !!!!!!!!!!!!!!!!!!!!
    
    # will crash, just set it without asking for the list
    # l, _ = c.getCameraResponsePresetsList()
    # if(d['response'] in l):
    #     c.setCameraResponsePreset(d['response'])
    c.setCameraResponsePreset(d['response'])
    
    if(d['custom_bokeh']):
        c.setCustomBokeh(d['bokeh_ratio'], d['bokeh_angle'], True)
    
    o = Cvector()
    o.assign(*d['origin'])
    f = Cvector()
    f.assign(*d['focal_point'])
    u = Cvector()
    u.assign(*d['up'])
    # hard coded: (step: 0, _, _, _, _, _, stepTime: 1, focalLengthNeedCorrection: 1, )
    c.setStep(0, o, f, u, d['focal_length'], d['fstop'], 1, 1, )
    if(d['lens'] == 3):
        c.setFishLensProperties(d['fov'])
    if(d['lens'] == 4):
        c.setSphericalLensProperties(d['azimuth'])
    if(d['lens'] == 5):
        c.setCylindricalLensProperties(d['angle'])
    # c.setShutter(d['shutter'])
    c.setCutPlanes(d['set_cut_planes'][0], d['set_cut_planes'][1], d['set_cut_planes'][2], )
    c.setShiftLens(d['set_shift_lens'][0], d['set_shift_lens'][1], )
    if(d['screen_region'] != 'NONE'):
        r = d['screen_region_xywh']
        c.setScreenRegion(r[0], r[1], r[2], r[3], d['screen_region'])
    if(d['active']):
        c.setActive()
    return c


def empty(d, s):
    o = s.createMesh(d['name'], 0, 0, 0, 0,)
    base_and_pivot(o, d)
    object_props(o, d)
    return o


def mesh(d, s):
    r = MXSBinMeshReaderLegacy(d['mesh_data_path'])
    m = r.data
    o = s.createMesh(d['name'], d['num_vertexes'], d['num_normals'], d['num_triangles'], d['num_positions_per_vertex'], )
    for i in m['channel_uvw']:
        o.addChannelUVW(i)
    for i in range(len(m['v_setVertex'])):
        mv = Cvector()
        v = m['v_setVertex'][i]
        mv.assign(v[2][0], v[2][1], v[2][2])
        o.setVertex(v[0], v[1], mv)
        n = m['v_setNormal'][i]
        mn = Cvector()
        mn.assign(n[2][0], n[2][1], n[2][2])
        o.setNormal(n[0], n[1], mn)
    for n in m['f_setNormal']:
        mn = Cvector()
        mn.assign(n[2][0], n[2][1], n[2][2])
        o.setNormal(n[0], n[1], mn)
    for t in m['f_setTriangle']:
        o.setTriangle(t[0], t[1][0], t[1][1], t[1][2], t[2][0], t[2][1], t[2][2], )
    
    if(d['num_materials'] > 1):
        # multi material
        mats = []
        for mi in range(d['num_materials']):
            if(d['materials'][mi][1] == ""):
                # multi material, but none assigned.. to keep triangle group, create and assign blank material
                mat = material_placeholder(s)
            else:
                mat = material(d['materials'][mi][1], s, d['materials'][mi][0])
            mats.append(mat)
        for t, ma in m['f_setTriangleMaterial']:
            o.setTriangleMaterial(t, mats[ma])
    elif(d['num_materials'] == 1):
        # # single material
        # if(d['materials'][0][1] == ""):
        #     mat = material_placeholder(s)
        # else:
        #     mat = material(d['materials'][0][1], s, d['materials'][0][0])
        if(d['materials'][0][1] == ""):
            mat = None
        else:
            mat = material(d['materials'][0][1], s, d['materials'][0][0])
        # # this is causing error: Object [...] is not an emitter but has triangles with an emitter material applied to it
        # # details here: http://support.nextlimit.com/display/knfaq/Render+error+messages
        # # what is probably happening is, if setTriangleMaterial is used even with the same material on all triangles
        # # somewhere it is flagged as multi material mesh..
        # for t, ma in m['f_setTriangleMaterial']:
        #     o.setTriangleMaterial(t, mat)
        # # fix
        if(mat is not None):
            o.setMaterial(mat)
    else:
        # no material
        pass
    
    if(len(d['backface_material']) > 0):
        if(d['backface_material'][0] != ""):
            bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
            o.setBackfaceMaterial(bm)
    
    for t in m['f_setTriangleUVW']:
        o.setTriangleUVW(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], )
    base_and_pivot(o, d)
    object_props(o, d)
    
    if(d['subdiv_ext'] is not None):
        # 0: ('Subdivision Level', [2], 0, 99, '1 UINT', 4, 1, True)
        # 1: ('Subdivision Scheme', [0], 0, 2, '1 UINT', 4, 1, True)
        # 2: ('Interpolation', [2], 0, 3, '1 UINT', 4, 1, True)
        # 3: ('Crease', [0.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 4: ('Smooth Angle', [90.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 5: ('EXTENSION_NAME', 'SubdivisionModifier', '', '', '5 STRING', 1, 20, True)
        # 6: ('EXTENSION_VERSION', [1], 0, 1000000, '1 UINT', 4, 1, True)
        # 7: ('EXTENSION_ISENABLED', [1], 0, 1, '0 UCHAR', 1, 1, True)
        m = CextensionManager.instance()
        m.loadAllExtensions()
        e = m.createDefaultGeometryModifierExtension('SubdivisionModifier')
        p = e.getExtensionData()
        e = d['subdiv_ext']
        p.setUInt('Subdivision Level', e[0])
        p.setUInt('Subdivision Scheme', e[1])
        p.setUInt('Interpolation', e[2])
        p.setFloat('Crease', e[3])
        p.setFloat('Smooth Angle', e[4])
        o.applyGeometryModifierExtension(p)
    
    if(d['scatter_ext'] is not None):
        # 0: ('Object', '', '', '', '5 STRING', 1, 1, True)
        # 1: ('Inherit ObjectID', [0], 0, 1, '0 UCHAR', 1, 1, True)
        # 2: ('Density', [100.0], 9.999999747378752e-05, 10000000000.0, '3 FLOAT', 4, 1, True)
        # 3: ('Density Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 4: ('Scale X', [1.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 5: ('Scale Y', [1.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 6: ('Scale Z', [1.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 7: ('Scale Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 8: ('Scale X Variation', [20.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 9: ('Scale Y Variation', [20.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 10: ('Scale Z Variation', [20.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 11: ('Rotation X', [0.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 12: ('Rotation Y', [0.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 13: ('Rotation Z', [0.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 14: ('Rotation Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 15: ('Rotation X Variation', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 16: ('Rotation Y Variation', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 17: ('Rotation Z Variation', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 18: ('Direction Type', [0], 0, 1, '1 UINT', 4, 1, True)
        # 19: ('Initial Angle', [90.0], 0.0, 90.0, '3 FLOAT', 4, 1, True)
        # 20: ('Initial Angle Variation', [0.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 21: ('Initial Angle Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 22: ('Seed', [0], 0, 16383, '1 UINT', 4, 1, True)
        # 23: ('Enable LOD', [0], 0, 1, '0 UCHAR', 1, 1, True)
        # 24: ('LOD Min Distance', [10.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 25: ('LOD Max Distance', [50.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 26: ('LOD Max Distance Density', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 27: ('Display Percent', [10], 0, 100, '1 UINT', 4, 1, True)
        # 28: ('Display Max. Instances', [1000], 0, 100000, '1 UINT', 4, 1, True)
        # 29: ('TRIANGLES_WITH_CLONES', [0], 0, 0, '8 BYTEARRAY', 1, 1, True)
        # 30: ('EXTENSION_NAME', 'MaxwellScatter', '', '', '5 STRING', 1, 15, True)
        # 31: ('EXTENSION_VERSION', [1], 0, 1000000, '1 UINT', 4, 1, True)
        # 32: ('EXTENSION_ISENABLED', [1], 0, 1, '0 UCHAR', 1, 1, True)
        
        m = CextensionManager.instance()
        m.loadAllExtensions()
        e = m.createDefaultGeometryModifierExtension('MaxwellScatter')
        p = e.getExtensionData()
        e = d['scatter_ext']
        
        p.setString('Object', e['scatter_object'])
        p.setByte('Inherit ObjectID', e['inherit_objectid'])
        p.setFloat('Density', e['density'])
        texture_data_to_mxparams(e['density_map'], p, 'Density Map', )
        p.setUInt('Seed', e['seed'])
        p.setFloat('Scale X', e['scale_x'])
        p.setFloat('Scale Y', e['scale_y'])
        p.setFloat('Scale Z', e['scale_z'])
        texture_data_to_mxparams(e['scale_map'], p, 'Scale Map', )
        p.setFloat('Scale X Variation', e['scale_variation_x'])
        p.setFloat('Scale Y Variation', e['scale_variation_y'])
        p.setFloat('Scale Z Variation', e['scale_variation_z'])
        p.setFloat('Rotation X', e['rotation_x'])
        p.setFloat('Rotation Y', e['rotation_y'])
        p.setFloat('Rotation Z', e['rotation_z'])
        texture_data_to_mxparams(e['rotation_map'], p, 'Rotation Map', )
        p.setFloat('Rotation X Variation', e['rotation_variation_x'])
        p.setFloat('Rotation Y Variation', e['rotation_variation_y'])
        p.setFloat('Rotation Z Variation', e['rotation_variation_z'])
        p.setUInt('Direction Type', e['rotation_direction'])
        p.setByte('Enable LOD', e['lod'])
        p.setFloat('LOD Min Distance', e['lod_min_distance'])
        p.setFloat('LOD Max Distance', e['lod_max_distance'])
        p.setFloat('LOD Max Distance Density', e['lod_max_distance_density'])
        p.setUInt('Display Percent', e['display_percent'])
        p.setUInt('Display Max. Blades', e['display_max_blades'])
        o.applyGeometryModifierExtension(p)
    
    if(d['sea_ext'] is not None):
        m = CextensionManager.instance()
        m.loadAllExtensions()
        e = m.createDefaultGeometryLoaderExtension('MaxwellSea')
        p = e.getExtensionData()
        name = d['sea_ext'][0]
        hide_parent = d['sea_ext'][1]
        q = d['sea_ext'][2:]
        
        p.setFloat('Reference Time', q[0])
        p.setUInt('Resolution', q[1])
        p.setFloat('Ocean Depth', q[2])
        p.setFloat('Vertical Scale', q[3])
        p.setFloat('Ocean Dim', q[4])
        p.setUInt('Ocean Seed', q[5])
        p.setByte('Enable Choppyness', q[6])
        p.setFloat('Choppy factor', q[7])
        p.setFloat('Ocean Wind Mod.', q[8])
        p.setFloat('Ocean Wind Dir.', q[9])
        p.setFloat('Ocean Wind Alignment', q[10])
        p.setFloat('Ocean Min. Wave Length', q[11])
        p.setFloat('Damp Factor Against Wind', q[12])
        p.setByte('Enable White Caps', q[13])
        
        so = s.createGeometryLoaderObject(name, p)
        object_props(so, d)
        so.setParent(o)
        if(hide_parent):
            o.setHide(True)
    
    return o


def instance(d, s):
    bo = s.getObject(d['instanced'])
    o = s.createInstancement(d['name'], bo)
    if(d['num_materials'] == 1):
        # instance with different material is possible
        m = material(d['materials'][0][1], s, d['materials'][0][0])
        o.setMaterial(m)
    else:
        # multi material instances cannot be changed (i think)
        # and just skip instances without material
        pass
    if(len(d['backface_material']) > 0):
        if(d['backface_material'][0] != ""):
            bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
            o.setBackfaceMaterial(bm)
    
    base_and_pivot(o, d)
    object_props(o, d)
    return o


def scene(d, s):
    s.setRenderParameter('ENGINE', d["scene_quality"])
    s.setRenderParameter('NUM THREADS', d["scene_cpu_threads"])
    s.setRenderParameter('STOP TIME', d["scene_time"] * 60)
    s.setRenderParameter('SAMPLING LEVEL', d["scene_sampling_level"])
    s.setRenderParameter('USE MULTILIGHT', d["scene_multilight"])
    s.setRenderParameter('SAVE LIGHTS IN SEPARATE FILES', d["scene_multilight_type"])
    
    s.setRenderParameter('MXI FULLNAME', d["output_mxi"])
    s.setRenderParameter('DO NOT SAVE MXI FILE', not d["output_mxi_enabled"])
    s.setRenderParameter('DO NOT SAVE IMAGE FILE', not d["output_image_enabled"])
    # s.setRenderParameter('RENAME AFTER SAVING', d[""])
    # s.setRenderParameter('COPY MXI AFTER RENDER', d["output_mxi"])
    # s.setRenderParameter('COPY IMAGE AFTER RENDER', d["output_image"])
    # s.setRenderParameter('REMOVE FILES AFTER COPY', d[""])
    s.setRenderParameter('DO MOTION BLUR', d["globals_motion_blur"])
    s.setRenderParameter('DO DISPLACEMENT', d["globals_diplacement"])
    s.setRenderParameter('DO DISPERSION', d["globals_dispersion"])
    
    if(d['channels_render_type'] == 2):
        s.setRenderParameter('DO DIFFUSE LAYER', 0)
        s.setRenderParameter('DO REFLECTION LAYER', 1)
    elif(d['channels_render_type'] == 1):
        s.setRenderParameter('DO DIFFUSE LAYER', 1)
        s.setRenderParameter('DO REFLECTION LAYER', 0)
    else:
        s.setRenderParameter('DO DIFFUSE LAYER', 1)
        s.setRenderParameter('DO REFLECTION LAYER', 1)
    
    v = d['illum_caustics_illumination']
    if(v == 3):
        s.setRenderParameter('DO DIRECT LAYER', 0)
        s.setRenderParameter('DO INDIRECT LAYER', 0)
    elif(v == 2):
        s.setRenderParameter('DO DIRECT LAYER', 0)
        s.setRenderParameter('DO INDIRECT LAYER', 1)
    elif(v == 1):
        s.setRenderParameter('DO DIRECT LAYER', 1)
        s.setRenderParameter('DO INDIRECT LAYER', 0)
    else:
        s.setRenderParameter('DO DIRECT LAYER', 1)
        s.setRenderParameter('DO INDIRECT LAYER', 1)
    
    v = d['illum_caustics_refl_caustics']
    if(v == 3):
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 0)
    elif(v == 2):
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 1)
    elif(v == 1):
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 0)
    else:
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 1)
    
    v = d['illum_caustics_refr_caustics']
    if(v == 3):
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 0)
    elif(v == 2):
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 1)
    elif(v == 1):
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 0)
    else:
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 1)
    
    h, t = os.path.split(d["output_mxi"])
    n, e = os.path.splitext(t)
    base_path = os.path.join(h, n)
    
    def get_ext_depth(t, e=None):
        if(e is not None):
            t = "{}{}".format(e[1:].upper(), int(t[3:]))
        
        if(t == 'RGB8'):
            return ('.png', 8)
        elif(t == 'RGB16'):
            return ('.png', 16)
        elif(t == 'RGB32'):
            return ('.exr', 32)
        elif(t == 'PNG8'):
            return ('.png', 8)
        elif(t == 'PNG16'):
            return ('.png', 16)
        elif(t == 'TGA'):
            return ('.tga', 8)
        elif(t == 'TIF8'):
            return ('.tif', 8)
        elif(t == 'TIF16'):
            return ('.tif', 16)
        elif(t == 'TIF32'):
            return ('.tif', 32)
        elif(t == 'EXR16'):
            return ('.exr', 16)
        elif(t == 'EXR32'):
            return ('.exr', 32)
        elif(t == 'EXR_DEEP'):
            return ('.exr', 32)
        elif(t == 'JPG'):
            return ('.jpg', 8)
        elif(t == 'JP2'):
            return ('.jp2', 8)
        elif(t == 'HDR'):
            return ('.hdr', 32)
        elif(t == 'DTEX'):
            return ('.dtex', 32)
        else:
            return ('.tif', 8)
    
    _, depth = get_ext_depth(d["output_depth"], os.path.splitext(os.path.split(d["output_image"])[1])[1])
    s.setPath('RENDER', d["output_image"], depth)
    
    e, depth = get_ext_depth(d["channels_alpha_file"])
    s.setPath('ALPHA', "{}_alpha.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_shadow_file"])
    s.setPath('SHADOW', "{}_shadow.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_object_id_file"])
    s.setPath('OBJECT', "{}_object_id.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_material_id_file"])
    s.setPath('MATERIAL', "{}_material_id.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_motion_vector_file"])
    s.setPath('MOTION', "{}_motion_vector.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_z_buffer_file"])
    s.setPath('Z', "{}_z_buffer.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_roughness_file"])
    s.setPath('ROUGHNESS', "{}_roughness.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_fresnel_file"])
    s.setPath('FRESNEL', "{}_fresnel.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_normals_file"])
    s.setPath('NORMALS', "{}_normals.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_position_file"])
    s.setPath('POSITION', "{}_position.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_deep_file"])
    s.setPath('DEEP', "{}_deep.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_uv_file"])
    s.setPath('UV', "{}_uv.{}".format(base_path, e), depth)
    
    e, depth = get_ext_depth(d["channels_custom_alpha_file"])
    s.setPath('ALPHA_CUSTOM', "{}_custom_alpha.{}".format(base_path, e), depth)
    
    s.setRenderParameter('DO RENDER CHANNEL', int(d["channels_render"]))
    s.setRenderParameter('DO ALPHA CHANNEL', int(d["channels_alpha"]))
    s.setRenderParameter('OPAQUE ALPHA', int(d["channels_alpha_opaque"]))
    s.setRenderParameter('EMBED CHANNELS', d["channels_output_mode"])
    s.setRenderParameter('DO IDOBJECT CHANNEL', int(d["channels_object_id"]))
    s.setRenderParameter('DO IDMATERIAL CHANNEL', int(d["channels_material_id"]))
    s.setRenderParameter('DO SHADOW PASS CHANNEL', int(d["channels_shadow"]))
    s.setRenderParameter('DO MOTION CHANNEL', int(d["channels_motion_vector"]))
    s.setRenderParameter('DO ROUGHNESS CHANNEL', int(d["channels_roughness"]))
    s.setRenderParameter('DO FRESNEL CHANNEL', int(d["channels_fresnel"]))
    s.setRenderParameter('DO NORMALS CHANNEL', int(d["channels_normals"]))
    s.setRenderParameter('NORMALS CHANNEL SPACE', d["channels_normals_space"])
    s.setRenderParameter('POSITION CHANNEL SPACE', d["channels_position_space"])
    s.setRenderParameter('DO POSITION CHANNEL', int(d["channels_position"]))
    s.setRenderParameter('DO ZBUFFER CHANNEL', int(d["channels_z_buffer"]))
    s.setRenderParameter('ZBUFFER RANGE', (d["channels_z_buffer_near"], d["channels_z_buffer_far"]))
    s.setRenderParameter('DO DEEP CHANNEL', int(d["channels_deep"]))
    s.setRenderParameter('DEEP CHANNEL TYPE', d["channels_deep_type"])
    s.setRenderParameter('DEEP MIN DISTANCE', d["channels_deep_min_dist"])
    s.setRenderParameter('DEEP MAX SAMPLES', d["channels_deep_max_samples"])
    s.setRenderParameter('DO UV CHANNEL', int(d["channels_uv"]))
    
    # s.setRenderParameter('MOTION CHANNEL TYPE', ?)
    s.setRenderParameter('DO ALPHA CUSTOM CHANNEL', int(d["channels_custom_alpha"]))
    
    s.setRenderParameter('DO DEVIGNETTING', d["simulens_devignetting"])
    s.setRenderParameter('DEVIGNETTING', d["simulens_devignetting_value"])
    s.setRenderParameter('DO SCATTERING_LENS', d["simulens_scattering"])
    s.setRenderParameter('SCATTERING_LENS', d["simulens_scattering_value"])
    
    s.setRenderParameter('DO SHARPNESS', d["tone_sharpness"])
    s.setRenderParameter('SHARPNESS', d["tone_sharpness_value"])
    s.setToneMapping(d["tone_gamma"], d["tone_burn"])
    
    if(d["materials_override"]):
        s.setOverrideMaterial(True)
    if(d["materials_override_path"] != ""):
        s.setOverrideMaterial(d["materials_override_path"])
    
    if(d["simulens_diffraction"]):
        s.enableDiffraction()
        s.setDiffraction(d["simulens_diffraction_value"], d["simulens_frequency"], d["simulens_aperture_map"], d["simulens_obstacle_map"])
    
    s.setColorSpace(d["tone_color_space"])
    s.setWhitePoint(d["tone_whitepoint"], d["tone_tint"])
    
    if(d["materials_search_path"] != ""):
        s.addSearchingPath(d["materials_search_path"])


def environment(d, s):
    env = s.getEnvironment()
    if(d["env_type"] == 'PHYSICAL_SKY'):
        env.setActiveSky(d["sky_type"])
        if(d["sky_type"] == 'PHYSICAL'):
            if(not d["sky_use_preset"]):
                env.setPhysicalSkyAtmosphere(d["sky_intensity"], d["sky_ozone"], d["sky_water"], d["sky_turbidity_coeff"], d["sky_wavelength_exp"], d["sky_reflectance"], d["sky_asymmetry"], d["sky_planet_refl"], )
            else:
                env.loadSkyFromPreset(d["sky_preset"])
            
            sc = Crgb()
            scc = [c / 255 for c in d['sun_color']]
            sc.assign(*scc)
            if(d["sun_type"] == 'PHYSICAL'):
                env.setSunProperties(SUN_PHYSICAL, d["sun_temp"], d["sun_power"], d["sun_radius_factor"], sc)
            elif(d["sun_type"] == 'CUSTOM'):
                env.setSunProperties(SUN_CONSTANT, d["sun_temp"], d["sun_power"], d["sun_radius_factor"], sc)
            elif(d["sun_type"] == 'DISABLED'):
                env.setSunProperties(SUN_DISABLED, d["sun_temp"], d["sun_power"], d["sun_radius_factor"], sc)
            if(d["sun_location_type"] == 'LATLONG'):
                env.setSunPositionType(0)
                l = d["sun_date"].split(".")
                date = datetime.date(int(l[2]), int(l[1]), int(l[0]))
                day = int(date.timetuple().tm_yday)
                l = d["sun_time"].split(":")
                hour = int(l[0])
                minute = int(l[1])
                time = hour + (minute / 60)
                env.setSunLongitudeAndLatitude(d["sun_latlong_lon"], d["sun_latlong_lat"], d["sun_latlong_gmt"], day, time)
                env.setSunRotation(d["sun_latlong_ground_rotation"])
            elif(d["sun_location_type"] == 'ANGLES'):
                env.setSunPositionType(1)
                env.setSunAngles(d["sun_angles_zenith"], d["sun_angles_azimuth"])
            elif(d["sun_location_type"] == 'DIRECTION'):
                env.setSunPositionType(2)
                env.setSunDirection(Cvector(d["sun_dir_x"], d["sun_dir_y"], d["sun_dir_z"]))
        if(d["sky_type"] == 'CONSTANT'):
            hc = Crgb()
            hcc = [c / 255 for c in d['dome_horizon']]
            hc.assign(*hcc)
            zc = Crgb()
            zcc = [c / 255 for c in d['dome_zenith']]
            zc.assign(*zcc)
            env.setSkyConstant(d["dome_intensity"], hc, zc, d['dome_mid_point'])
    elif(d["env_type"] == 'IMAGE_BASED'):
        env.enableEnvironment(True)
        
        def state(s):
            if(s == 'HDR_IMAGE'):
                return 1
            if(s == 'SAME_AS_BG'):
                return 2
            return 0
        
        env.setEnvironmentWeight(d["ibl_intensity"])
        env.setEnvironmentLayer(IBL_LAYER_BACKGROUND,
                                d["ibl_bg_map"],
                                state("ibl_bg_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_bg_intensity"],
                                d["ibl_bg_scale_x"],
                                d["ibl_bg_scale_y"],
                                d["ibl_bg_offset_x"],
                                d["ibl_bg_offset_y"], )
        env.setEnvironmentLayer(IBL_LAYER_REFLECTION,
                                d["ibl_refl_map"],
                                state("ibl_refl_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_refl_intensity"],
                                d["ibl_refl_scale_x"],
                                d["ibl_refl_scale_y"],
                                d["ibl_refl_offset_x"],
                                d["ibl_refl_offset_y"], )
        env.setEnvironmentLayer(IBL_LAYER_REFRACTION,
                                d["ibl_refr_map"],
                                state("ibl_refr_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_refr_intensity"],
                                d["ibl_refr_scale_x"],
                                d["ibl_refr_scale_y"],
                                d["ibl_refr_offset_x"],
                                d["ibl_refr_offset_y"], )
        env.setEnvironmentLayer(IBL_LAYER_ILLUMINATION,
                                d["ibl_illum_map"],
                                state("ibl_illum_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_illum_intensity"],
                                d["ibl_illum_scale_x"],
                                d["ibl_illum_scale_y"],
                                d["ibl_illum_offset_x"],
                                d["ibl_illum_offset_y"], )
    else:
        env.setActiveSky('')


def custom_alphas(d, s):
    ags = d['channels_custom_alpha_groups']
    for a in ags:
        s.createCustomAlphaChannel(a['name'], a['opaque'])
        for n in a['objects']:
            o = s.getObject(n)
            o.addToCustomAlpha(a['name'])


def particles(d, s):
    mgr = CextensionManager.instance()
    mgr.loadAllExtensions()
    
    ext = mgr.createDefaultGeometryProceduralExtension('MaxwellParticles')
    params = ext.getExtensionData()
    
    params.setString('FileName', d['bin_filename'])
    params.setFloat('Radius Factor', d['bin_radius_multiplier'])
    params.setFloat('MB Factor', d['bin_motion_blur_multiplier'])
    params.setFloat('Shutter 1/', d['bin_shutter_speed'])
    params.setFloat('Load particles %', d['bin_load_particles'])
    params.setUInt('Axis', d['bin_axis_system'])
    params.setInt('Frame#', d['bin_frame_number'])
    params.setFloat('fps', d['bin_fps'])
    params.setInt('Create N particles per particle', d['bin_extra_create_np_pp'])
    params.setFloat('Extra particles dispersion', d['bin_extra_dispersion'])
    params.setFloat('Extra particles deformation', d['bin_extra_deformation'])
    params.setByte('Load particle Force', d['bin_load_force'])
    params.setByte('Load particle Vorticity', d['bin_load_vorticity'])
    params.setByte('Load particle Normal', d['bin_load_normal'])
    params.setByte('Load particle neighbors no.', d['bin_load_neighbors_num'])
    params.setByte('Load particle UV', d['bin_load_uv'])
    params.setByte('Load particle Age', d['bin_load_age'])
    params.setByte('Load particle Isolation Time', d['bin_load_isolation_time'])
    params.setByte('Load particle Viscosity', d['bin_load_viscosity'])
    params.setByte('Load particle Density', d['bin_load_density'])
    params.setByte('Load particle Pressure', d['bin_load_pressure'])
    params.setByte('Load particle Mass', d['bin_load_mass'])
    params.setByte('Load particle Temperature', d['bin_load_temperature'])
    params.setByte('Load particle ID', d['bin_load_id'])
    params.setFloat('Min Force', d['bin_min_force'])
    params.setFloat('Max Force', d['bin_max_force'])
    params.setFloat('Min Vorticity', d['bin_min_vorticity'])
    params.setFloat('Max Vorticity', d['bin_max_vorticity'])
    params.setInt('Min Nneighbors', d['bin_min_nneighbors'])
    params.setInt('Max Nneighbors', d['bin_max_nneighbors'])
    params.setFloat('Min Age', d['bin_min_age'])
    params.setFloat('Max Age', d['bin_max_age'])
    params.setFloat('Min Isolation Time', d['bin_min_isolation_time'])
    params.setFloat('Max Isolation Time', d['bin_max_isolation_time'])
    params.setFloat('Min Viscosity', d['bin_min_viscosity'])
    params.setFloat('Max Viscosity', d['bin_max_viscosity'])
    params.setFloat('Min Density', d['bin_min_density'])
    params.setFloat('Max Density', d['bin_max_density'])
    params.setFloat('Min Pressure', d['bin_min_pressure'])
    params.setFloat('Max Pressure', d['bin_max_pressure'])
    params.setFloat('Min Mass', d['bin_min_mass'])
    params.setFloat('Max Mass', d['bin_max_mass'])
    params.setFloat('Min Temperature', d['bin_min_temperature'])
    params.setFloat('Max Temperature', d['bin_max_temperature'])
    params.setFloat('Min Velocity', d['bin_min_velocity'])
    params.setFloat('Max Velocity', d['bin_max_velocity'])
    
    o = s.createGeometryProceduralObject(d['name'], params)
    
    # mat = material(d['material'], s, d['material_embed'])
    # o.setMaterial(mat)
    
    if(d['material'] != ""):
        mat = material(d['material'], s, d['material_embed'])
        o.setMaterial(mat)
    if(d['backface_material'] != ""):
        bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
        o.setBackfaceMaterial(bm)
    
    base_and_pivot(o, d)
    object_props(o, d)


def grass(d, s):
    m = CextensionManager.instance()
    m.loadAllExtensions()
    
    e = m.createDefaultGeometryModifierExtension('MaxwellGrass')
    p = e.getExtensionData()
    
    # data = [(0, 'UCHAR'), (1, 'UINT'), (2, 'INT'), (3, 'FLOAT'), (4, 'DOUBLE'), (5, 'STRING'), (6, 'FLOATARRAY'), (7, 'DOUBLEARRAY'),
    #         (8, 'BYTEARRAY'), (9, 'INTARRAY'), (10, 'MXPARAMLIST'), (11, 'MXPARAMLISTARRAY'), (12, 'RGB'), ]
    # mp = p.getByIndex(3)[1]
    # for i in range(mp.getNumItems()):
    #     s = list(mp.getByIndex(i))
    #     for di, dt in data:
    #         if(di == s[4]):
    #             s[4] = "{} ({})".format(di, dt)
    #     print(str(tuple(s)))
    
    if(d['material'] != ""):
        mat = material(d['material'], s, d['material_embed'])
        p.setString('Material', mat.getName())
    
    if(d['backface_material'] != ""):
        bmat = material(d['backface_material'], s, d['backface_material_embed'])
        p.setString('Double Sided Material', bmat.getName())
    
    p.setUInt('Density', d['density'])
    texture_data_to_mxparams(d['density_map'], p, 'Density Map')
    
    p.setFloat('Length', d['length'])
    texture_data_to_mxparams(d['length_map'], p, 'Length Map')
    p.setFloat('Length Variation', d['length_variation'])
    
    p.setFloat('Root Width', d['root_width'])
    p.setFloat('Tip Width', d['tip_width'])
    
    p.setUInt('Direction Type', d['direction_type'])
    
    p.setFloat('Initial Angle', d['initial_angle'])
    p.setFloat('Initial Angle Variation', d['initial_angle_variation'])
    texture_data_to_mxparams(d['initial_angle_map'], p, 'Initial Angle Map')
    
    p.setFloat('Start Bend', d['start_bend'])
    p.setFloat('Start Bend Variation', d['start_bend_variation'])
    texture_data_to_mxparams(d['start_bend_map'], p, 'Start Bend Map')
    
    p.setFloat('Bend Radius', d['bend_radius'])
    p.setFloat('Bend Radius Variation', d['bend_radius_variation'])
    texture_data_to_mxparams(d['bend_radius_map'], p, 'Bend Radius Map')
    
    p.setFloat('Bend Angle', d['bend_angle'])
    p.setFloat('Bend Angle Variation', d['bend_angle_variation'])
    texture_data_to_mxparams(d['bend_angle_map'], p, 'Bend Angle Map')
    
    p.setFloat('Cut Off', d['cut_off'])
    p.setFloat('Cut Off Variation', d['cut_off_variation'])
    texture_data_to_mxparams(d['cut_off_map'], p, 'Cut Off Map')
    
    p.setUInt('Points per Blade', d['points_per_blade'])
    p.setUInt('Primitive Type', d['primitive_type'])
    
    p.setUInt('Seed', d['seed'])
    
    p.setByte('Enable LOD', d['lod'])
    p.setFloat('LOD Min Distance', d['lod_min_distance'])
    p.setFloat('LOD Max Distance', d['lod_max_distance'])
    p.setFloat('LOD Max Distance Density', d['lod_max_distance_density'])
    
    p.setUInt('Display Percent', d['display_percent'])
    p.setUInt('Display Max. Blades', d['display_max_blades'])
    
    o = s.getObject(d['object'])
    o.applyGeometryModifierExtension(p)


def cloner(d, s):
    m = CextensionManager.instance()
    m.loadAllExtensions()
    
    e = m.createDefaultGeometryModifierExtension('MaxwellCloner')
    p = e.getExtensionData()
    
    p.setString('FileName', d['filename'])
    p.setFloat('Radius Factor', d['radius'])
    p.setFloat('MB Factor', d['mb_factor'])
    p.setFloat('Load particles %', d['load_percent'])
    p.setUInt('Start offset', d['start_offset'])
    p.setUInt('Create N particles per particle', d['extra_npp'])
    p.setFloat('Extra particles dispersion', d['extra_p_dispersion'])
    p.setFloat('Extra particles deformation', d['extra_p_deformation'])
    
    p.setByte('Use velocity', d['align_to_velocity'])
    p.setByte('Scale with particle radius', d['scale_with_radius'])
    p.setByte('Inherit ObjectID', d['inherit_obj_id'])
    
    p.setInt('Frame#', d['frame'])
    p.setFloat('fps', d['fps'])
    
    p.setUInt('Display Percent', d['display_percent'])
    p.setUInt('Display Max. Particles', d['display_max'])
    
    if(not d['render_emitter']):
        o = s.getObject(d['object'])
        o.setHide(True)
    
    # o = s.getObject(d['object'])
    o = s.getObject(d['cloned_object'])
    o.applyGeometryModifierExtension(p)


def hair(d, s):
    m = CextensionManager.instance()
    m.loadAllExtensions()
    
    if(d['extension'] == 'MaxwellHair'):
        e = m.createDefaultGeometryProceduralExtension('MaxwellHair')
    if(d['extension'] == 'MGrassP'):
        e = m.createDefaultGeometryProceduralExtension('MGrassP')
    
    p = e.getExtensionData()
    p.setByteArray('HAIR_MAJOR_VER', d['data']['HAIR_MAJOR_VER'])
    p.setByteArray('HAIR_MINOR_VER', d['data']['HAIR_MINOR_VER'])
    p.setByteArray('HAIR_FLAG_ROOT_UVS', d['data']['HAIR_FLAG_ROOT_UVS'])
    
    # p.setByteArray('HAIR_GUIDES_COUNT', d['data']['HAIR_GUIDES_COUNT'])
    m = memoryview(struct.pack("I", d['data']['HAIR_GUIDES_COUNT'][0])).tolist()
    p.setByteArray('HAIR_GUIDES_COUNT', m)
    
    # p.setByteArray('HAIR_GUIDES_POINT_COUNT', d['data']['HAIR_GUIDES_POINT_COUNT'])
    m = memoryview(struct.pack("I", d['data']['HAIR_GUIDES_POINT_COUNT'][0])).tolist()
    p.setByteArray('HAIR_GUIDES_POINT_COUNT', m)
    
    c = Cbase()
    c.origin = Cvector(0.0, 0.0, 0.0)
    c.xAxis = Cvector(1.0, 0.0, 0.0)
    c.yAxis = Cvector(0.0, 1.0, 0.0)
    c.zAxis = Cvector(0.0, 0.0, 1.0)
    
    bhp = d['hair_data_path']
    r = MXSBinHairReaderLegacy(bhp)
    p.setFloatArray('HAIR_POINTS', list(r.data), c)
    
    # p.setFloatArray('HAIR_POINTS', d['data']['HAIR_POINTS'], c)
    p.setFloatArray('HAIR_NORMALS', d['data']['HAIR_NORMALS'], c)
    
    p.setUInt('Display Percent', d['display_percent'])
    if(d['extension'] == 'MaxwellHair'):
        p.setUInt('Display Max. Hairs', d['display_max_hairs'])
        p.setDouble('Root Radius', d['hair_root_radius'])
        p.setDouble('Tip Radius', d['hair_tip_radius'])
    if(d['extension'] == 'MGrassP'):
        p.setUInt('Display Max. Hairs', d['display_max_blades'])
        p.setDouble('Root Radius', d['grass_root_width'])
        p.setDouble('Tip Radius', d['grass_tip_width'])
    
    # # for i in range(p.getNumItems()):
    # #     print(p.getByIndex(i))
    #
    # # print(p.getByName('HAIR_GUIDES_COUNT')[0])
    # # print(p.getByName('HAIR_GUIDES_POINT_COUNT')[0])
    # print()
    # print(d['data']['HAIR_GUIDES_COUNT'][0])
    # print(d['data']['HAIR_GUIDES_COUNT'][0] * d['data']['HAIR_GUIDES_POINT_COUNT'][0] * 3)
    # print(p.getByName('HAIR_GUIDES_COUNT'))
    # print(p.getByName('HAIR_GUIDES_POINT_COUNT'))
    # # print(p.getByName('HAIR_GUIDES_COUNT')[0][0] * p.getByName('HAIR_GUIDES_POINT_COUNT')[0][0] * 3)
    # print(len(p.getByName('HAIR_POINTS')[0]))
    # # print(p.getByName('HAIR_NORMALS')[0])
    # print()
    
    o = s.createGeometryProceduralObject(d['name'], p)
    
    if(d['material'] != ""):
        mat = material(d['material'], s, d['material_embed'])
        o.setMaterial(mat)
    if(d['backface_material'] != ""):
        bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
        o.setBackfaceMaterial(bm)
    
    base_and_pivot(o, d)
    object_props(o, d)


def hierarchy(d, s):
    log("setting object hierarchy..", 2)
    object_types = ['EMPTY', 'MESH', 'INSTANCE', 'PARTICLES', 'HAIR', ]
    exclude = ['SCENE', 'ENVIRONMENT', 'GRASS', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types and d[i]['type'] not in exclude):
            if(d[i]['parent'] is not None):
                ch = s.getObject(d[i]['name'])
                p = s.getObject(d[i]['parent'])
                ch.setParent(p)
    
    object_types = ['PARTICLES', 'HAIR', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types):
            if(d[i]['parent'] is not None):
                if(d[i]['hide_parent']):
                    p = s.getObject(d[i]['parent'])
                    p.setHide(True)


def wireframe_hierarchy(d, s, ws):
    # wire and clay empties data
    ced = {'name': 'clay',
           'parent': None,
           'base': ((0.0, 0.0, -0.0), (1.0, 0.0, -0.0), (0.0, 1.0, -0.0), (-0.0, -0.0, 1.0)),
           'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
           'opacity': 100.0,
           'hidden_camera': False,
           'hidden_camera_in_shadow_channel': False,
           'hidden_global_illumination': False,
           'hidden_reflections_refractions': False,
           'hidden_zclip_planes': False,
           'object_id': (0, 0, 0),
           'hide': False,
           'type': 'EMPTY', }
    ce = empty(ced, s)
    wed = {'name': 'wire',
           'parent': None,
           'base': ((0.0, 0.0, -0.0), (1.0, 0.0, -0.0), (0.0, 1.0, -0.0), (-0.0, -0.0, 1.0)),
           'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
           'opacity': 100.0,
           'hidden_camera': False,
           'hidden_camera_in_shadow_channel': False,
           'hidden_global_illumination': False,
           'hidden_reflections_refractions': False,
           'hidden_zclip_planes': False,
           'object_id': (0, 0, 0),
           'hide': False,
           'type': 'EMPTY', }
    we = empty(wed, s)
    object_types = ['EMPTY', 'MESH', 'INSTANCE', 'WIREFRAME_EDGE', 'WIREFRAME', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types):
            if(d[i]['type'] == 'WIREFRAME'):
                pass
            elif(d[i]['type'] == 'WIREFRAME_EDGE'):
                ch = s.getObject(d[i]['name'])
                ch.setParent(we)
            else:
                if(d[i]['parent'] is None):
                    ch = s.getObject(d[i]['name'])
                    ch.setParent(ce)
    # group all wires..
    for w in ws:
        w.setParent(we)


def wireframe_base(d, s):
    o = mesh(d, s)
    # zero scale wire instance source base mesh to be practically invisible :)
    o.setScale(Cvector(0, 0, 0))
    # o.setMaterial(mat)
    return o


def wireframe(d, s):
    r = []
    with open(d['matrices_path'], 'r') as f:
        md = json.load(f)
    bo = s.getObject(d['instanced'])
    for i, m in enumerate(md['matrices']):
        o = s.createInstancement("{0}-{1}".format(d['name'], i), bo)
        bp = {'base': m[0], 'pivot': m[1], }
        base_and_pivot(o, bp)
        object_props(o, d)
        r.append(o)
        # o.setMaterial(mat)
    return r


def wireframe_material(d, s):
    n = d['name']
    r0 = d['data']['reflectance_0']
    r90 = d['data']['reflectance_90']
    ci = d['data']['id']
    rough = d['data']['roughness']
    mat = s.createMaterial(n)
    l = mat.addLayer()
    l.setName(n)
    b = l.addBSDF()
    r = b.getReflectance()
    a = Cattribute()
    a.activeType = MAP_TYPE_RGB
    c = Crgb8()
    c.assign(*r0)
    a.rgb.assign(c.toRGB())
    r.setAttribute('color', a)
    a = Cattribute()
    a.activeType = MAP_TYPE_RGB
    c = Crgb8()
    c.assign(*r90)
    a.rgb.assign(c.toRGB())
    r.setAttribute('color.tangential', a)
    a = Cattribute()
    a.type = MAP_TYPE_VALUE
    a.value = rough
    b.setAttribute('roughness', a)
    c = Crgb8()
    c.assign(*ci)
    mat.setColorID(c.toRGB())
    return mat


def wireframe_assign_materials(d, s, ws, wm, cm):
    if(wm is None or cm is None):
        raise RuntimeError("wire or clay material is missing..")
    
    object_types = ['EMPTY', 'MESH', 'INSTANCE', 'WIREFRAME_EDGE', 'WIREFRAME', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types):
            if(d[i]['type'] == 'WIREFRAME'):
                pass
            elif(d[i]['type'] == 'WIREFRAME_EDGE'):
                o = s.getObject(d[i]['name'])
                o.setMaterial(wm)
            else:
                o = s.getObject(d[i]['name'])
                o.setMaterial(cm)
    # group all wires..
    for w in ws:
        w.setMaterial(wm)


def texture_data_to_mxparams(d, mp, name):
    if(d is None):
        return
    
    # t = mp.getTextureMap(name)[0]
    t = CtextureMap()
    t.setPath(d['path'])
    v = Cvector2D()
    v.assign(*d['repeat'])
    t.scale = v
    v = Cvector2D()
    v.assign(*d['offset'])
    t.offset = v
    t.rotation = d['rotation']
    t.uvwChannelID = d['channel']
    t.uIsTiled = d['tile_method_type'][0]
    t.vIsTiled = d['tile_method_type'][1]
    t.uIsMirrored = d['mirror'][0]
    t.vIsMirrored = d['mirror'][1]
    t.invert = d['invert']
    # t.doGammaCorrection = 0
    t.useAbsoluteUnits = d['tile_method_units']
    # t.normalMappingFlipRed = 0
    # t.normalMappingFlipGreen = 0
    # t.normalMappingFullRangeBlue = 0
    t.useAlpha = d['alpha_only']
    t.typeInterpolation = d['interpolation']
    t.saturation = d['saturation']
    t.contrast = d['contrast']
    t.brightness = d['brightness']
    t.hue = d['hue']
    t.clampMin = d['rgb_clamp'][0]
    t.clampMax = d['rgb_clamp'][1]
    t.useGlobalMap = d['use_override_map']
    # t.cosA = 1.000000
    # t.sinA = 0.000000
    ok = mp.setTextureMap(name, t)
    
    return mp


def main(args):
    log("loading data..", 2)
    with open(args.scene_data_path, 'r') as f:
        data = json.load(f)
    # create scene
    mxs = Cmaxwell(mwcallback)
    if(args.append is True):
        log("appending to existing scene..", 2)
        mxs.readMXS(args.result_path)
    else:
        log("creating new scene..", 2)
    # loop over scene data and create things by type
    if(args.wireframe):
        w_material = None
        c_material = None
        all_wires = []
    progress = PercentDone(len(data), indent=2, )
    for d in data:
        if(d['type'] == 'CAMERA'):
            camera(d, mxs)
        elif(d['type'] == 'EMPTY'):
            empty(d, mxs)
        elif(d['type'] == 'MESH'):
            mesh(d, mxs)
            if(args.instancer):
                # there should be just one mesh which is base, scale it to zero to be invisible..
                name = d['name']
                ob = mxs.getObject(d['name'])
                ob.setScale(Cvector(0.0, 0.0, 0.0))
        elif(d['type'] == 'INSTANCE'):
            try:
                if(d['base']):
                    mesh(d, mxs)
            except KeyError:
                instance(d, mxs)
        elif(d['type'] == 'SCENE'):
            scene(d, mxs)
            custom_alphas(d, mxs)
        elif(d['type'] == 'ENVIRONMENT'):
            environment(d, mxs)
        elif(d['type'] == 'PARTICLES'):
            particles(d, mxs)
        elif(d['type'] == 'GRASS'):
            grass(d, mxs)
        elif(d['type'] == 'HAIR'):
            hair(d, mxs)
        elif(d['type'] == 'CLONER'):
            cloner(d, mxs)
        elif(d['type'] == 'WIREFRAME_MATERIAL'):
            mat = wireframe_material(d, mxs)
            m = {'name': d['name'], 'data': mat, }
            if(d['name'] == 'wire'):
                w_material = mat
            elif(d['name'] == 'clay'):
                c_material = mat
            else:
                raise TypeError("'{0}' is unknown wireframe material".format(d['name']))
        elif(d['type'] == 'WIREFRAME_EDGE'):
            wireframe_base(d, mxs)
        elif(d['type'] == 'WIREFRAME'):
            ws = wireframe(d, mxs)
            all_wires.extend(ws)
        else:
            raise TypeError("{0} is unknown type".format(d['type']))
        progress.step()
    #
    hierarchy(data, mxs)
    #
    if(args.wireframe):
        wireframe_hierarchy(data, mxs, all_wires)
        wireframe_assign_materials(data, mxs, all_wires, w_material, c_material)
    #
    if(args.instancer):
        name = "instancer"
        
        def get_objects_names(mxs):
            it = CmaxwellObjectIterator()
            o = it.first(mxs)
            l = []
            while not o.isNull():
                name, _ = o.getName()
                l.append(name)
                o = it.next()
            return l
        
        ns = get_objects_names(mxs)
        ed = {'name': name,
              'parent': None,
              'base': ((0.0, 0.0, -0.0), (1.0, 0.0, -0.0), (0.0, 1.0, -0.0), (-0.0, -0.0, 1.0)),
              'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
              'opacity': 100.0,
              'hidden_camera': False,
              'hidden_camera_in_shadow_channel': False,
              'hidden_global_illumination': False,
              'hidden_reflections_refractions': False,
              'hidden_zclip_planes': False,
              'object_id': (255, 255, 255),
              'hide': False,
              'type': 'EMPTY', }
        e = empty(ed, mxs)
        for n in ns:
            ch = mxs.getObject(n)
            ch.setParent(e)
    
    # set active camera, again.. for some reason it gets reset
    for d in data:
        if(d['type'] == 'CAMERA'):
            if(d['active']):
                c = mxs.getCamera(d['name'])
                c.setActive()
    # save mxs
    log("saving scene..", 2)
    ok = mxs.writeMXS(args.result_path)
    log("done.", 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''Make Maxwell scene from serialized data'''), epilog='',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('-a', '--append', action='store_true', help='append to existing mxs (result_path)')
    parser.add_argument('-w', '--wireframe', action='store_true', help='scene data contains wireframe scene')
    parser.add_argument('-i', '--instancer', action='store_true', help='scene data contains instancer (python only)')
    parser.add_argument('-q', '--quiet', action='store_true', help='no logging except errors')
    parser.add_argument('log_file', type=str, help='path to log file')
    parser.add_argument('scene_data_path', type=str, help='path to serialized scene data file')
    parser.add_argument('result_path', type=str, help='path to result .mxs')
    args = parser.parse_args()
    
    quiet = args.quiet
    
    LOG_FILE_PATH = args.log_file
    
    try:
        main(args)
    except Exception as e:
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # sys.stdout.write("".join(lines))
        
        import traceback
        m = traceback.format_exc()
        log(m)
        
        # log("".join(lines))
        sys.exit(1)
    sys.exit(0)
