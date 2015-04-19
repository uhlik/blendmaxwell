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
import platform
import datetime
import struct
import math

# from .log import log, LogStyles

# if(platform.system() != 'Darwin'):
#     from pymaxwell import *

'''
def prefs():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    return p


import bpy
import sys
sys.path.append(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'pymaxwell', 'python3.4')))
'''

'''
s = platform.system()
if(s == 'Darwin'):
    p = '/Applications/Maxwell 3/'
elif(s == 'Linux'):
    p = os.environ.get("MAXWELL3_ROOT")
elif(s == 'Windows'):
    p = os.environ.get("MAXWELL3_ROOT")

sys.path.append(os.path.abspath(os.path.join(p, 'python', 'pymaxwell', 'python3.4')))
'''


if __name__ == "__main__":
    from pymaxwell import *
    
    class LogStyles():
        MESSAGE = ""
    
    def log(*args, **kwargs):
        pass
    
else:
    from .log import log, LogStyles
    if(platform.system() != 'Darwin'):
        from pymaxwell import *


class MXSWriter():
    def __init__(self, path, append, instancer=False, wireframe=False, ):
        if(platform.system() == 'Darwin'):
            raise ImportError("No pymaxwell for Mac OS X..")
        
        log(self.__class__.__name__, 1, LogStyles.MESSAGE, prefix="* ", )
        
        self.path = path
        self.mxs = Cmaxwell(mwcallback)
        if(append):
            log("appending to existing scene..", 2, prefix="* ", )
            self.mxs.readMXS(self.path)
        else:
            log("creating new scene..", 2, prefix="* ", )
        
        self.mgr = CextensionManager.instance()
        self.mgr.loadAllExtensions()
        
        if(instancer):
            raise Exception("not implemented yet: wireframe")
            # remove this completely?
            pass
        
        if(wireframe):
            raise Exception("not implemented yet: wireframe")
            # make wireframe base, for later usage
            pass
    
    def finalize(self):
        # active camera, custom alphas, wireframe materials and hierarchy.. all the non standard stuff
        pass
    
    def write_out(self):
        log("saving scene..", 2)
        ok = self.mxs.writeMXS(self.path)
        log("done.", 2)
        return ok
    
    # materials
    def material_placeholder(self, s, ):
        return None
    
    def material(self, path, s, embed, ):
        return None
    
    # utils
    def base_and_pivot(self, o, d, ):
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
    
    def object_props(self, o, d, ):
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
    
    # objects
    def camera(self, d, ):
        s = self.mxs
        c = s.addCamera(d['name'], d['number_of_steps'], d['shutter'], d['film_width'], d['film_height'], d['iso'],
                        d['aperture'], d['diaphragm_angle'], d['diaphragm_blades'], d['frame_rate'],
                        d['resolution_x'], d['resolution_y'], d['pixel_aspect'], d['lens'], )
        
        # FIXME how to set shutter_angle?
        
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
        # TODO steps
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
    
    def empty(self, d, ):
        s = self.mxs
        o = s.createMesh(d['name'], 0, 0, 0, 0,)
        self.base_and_pivot(o, d)
        self.object_props(o, d)
        return o
    
    def mesh(self, d, m, ):
        s = self.mxs
        
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
                    mat = self.material_placeholder(s)
                else:
                    mat = self.material(d['materials'][mi][1], s, d['materials'][mi][0])
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
                mat = self.material(d['materials'][0][1], s, d['materials'][0][0])
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
                bm = self.material(d['backface_material'][0], s, d['backface_material_embed'][1])
                o.setBackfaceMaterial(bm)
        
        for t in m['f_setTriangleUVW']:
            o.setTriangleUVW(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], )
        
        self.base_and_pivot(o, d)
        self.object_props(o, d)
        
        if(d['subdiv_ext'] is not None):
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
            def texture_data_to_mxparams(d, mp):
                if(d is None):
                    return
                # mp.setString('CtextureMap.FileName', d['path'])
                # hey, seriously.. WTF?
                mp.setString('CtextureMap.FileName', ''.join(d['path']))
                mp.setByte('CtextureMap.uvwChannel', d['channel'])
                mp.setByte('CtextureMap.uIsTiled', d['tile_method_type'][0])
                mp.setByte('CtextureMap.vIsTiled', d['tile_method_type'][1])
                mp.setByte('CtextureMap.uIsMirrored', d['mirror'][0])
                mp.setByte('CtextureMap.vIsMirrored', d['mirror'][1])
                mp.setFloat('CtextureMap.scale.x', d['repeat'][0])
                mp.setFloat('CtextureMap.scale.y', d['repeat'][1])
                mp.setFloat('CtextureMap.offset.x', d['offset'][0])
                mp.setFloat('CtextureMap.offset.y', d['offset'][1])
                mp.setFloat('CtextureMap.rotation', d['rotation'])
                mp.setByte('CtextureMap.invert', d['invert'])
                mp.setByte('CtextureMap.useAbsoluteUnits', d['tile_method_units'])
                mp.setByte('CtextureMap.useAlpha', d['alpha_only'])
                mp.setByte('CtextureMap.typeInterpolation', d['interpolation'])
                mp.setFloat('CtextureMap.saturation', d['saturation'])
                mp.setFloat('CtextureMap.contrast', d['contrast'])
                mp.setFloat('CtextureMap.brightness', d['brightness'])
                mp.setFloat('CtextureMap.hue', d['hue'])
                mp.setFloat('CtextureMap.clampMin', d['rgb_clamp'][0])
                mp.setFloat('CtextureMap.clampMax', d['rgb_clamp'][1])
                mp.setFloat('CtextureMap.useGlobalMap', d['use_override_map'])
            
            m = CextensionManager.instance()
            m.loadAllExtensions()
            e = m.createDefaultGeometryModifierExtension('MaxwellScatter')
            p = e.getExtensionData()
            e = d['scatter_ext']
            
            p.setString('Object', e['scatter_object'])
            p.setByte('Inherit ObjectID', e['inherit_objectid'])
            p.setFloat('Density', e['density'])
            texture_data_to_mxparams(e['density_map'], p.getByName('Density Map')[0])
            p.setUInt('Seed', e['seed'])
            p.setFloat('Scale X', e['scale_x'])
            p.setFloat('Scale Y', e['scale_y'])
            p.setFloat('Scale Z', e['scale_z'])
            texture_data_to_mxparams(e['scale_map'], p.getByName('Scale Map')[0])
            p.setFloat('Scale X Variation', e['scale_variation_x'])
            p.setFloat('Scale Y Variation', e['scale_variation_y'])
            p.setFloat('Scale Z Variation', e['scale_variation_z'])
            p.setFloat('Rotation X', e['rotation_x'])
            p.setFloat('Rotation Y', e['rotation_y'])
            p.setFloat('Rotation Z', e['rotation_z'])
            texture_data_to_mxparams(e['rotation_map'], p.getByName('Rotation Map')[0])
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
        
        return o
    
    def instance(self, d, ):
        s = self.mxs
        bo = s.getObject(d['instanced'])
        o = s.createInstancement(d['name'], bo)
        if(d['num_materials'] == 1):
            # instance with different material is possible
            m = self.material(d['materials'][0][1], s, d['materials'][0][0])
            if(m is not None):
                o.setMaterial(m)
        else:
            # multi material instances cannot be changed (i think)
            # and just skip instances without material
            pass
        if(len(d['backface_material']) > 0):
            if(d['backface_material'][0] != ""):
                bm = self.material(d['backface_material'][0], s, d['backface_material_embed'][1])
                if(bm is not None):
                    o.setBackfaceMaterial(bm)
        
        self.base_and_pivot(o, d)
        self.object_props(o, d)
        return o
    
    def duplicate(self, d, ):
        o = self.instance(d)
        return o
    
    def particles(self, d, ):
        ext = self.mgr.createDefaultGeometryProceduralExtension('MaxwellParticles')
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
        
        if(d['material'] != ""):
            mat = self.material(d['material'], s, d['material_embed'])
            o.setMaterial(mat)
        if(d['backface_material'] != ""):
            bm = self.material(d['backface_material'][0], s, d['backface_material_embed'][1])
            o.setBackfaceMaterial(bm)
        
        self.base_and_pivot(o, d)
        self.object_props(o, d)
        return o
    
    def grass(self, d, ):
        e = self.mgr.createDefaultGeometryModifierExtension('MaxwellGrass')
        p = e.getExtensionData()
        
        def texture_data_to_mxparams(d, mp):
            if(d is None):
                return
            # mp.setString('CtextureMap.FileName', d['path'])
            # hey, seriously.. WTF?
            mp.setString('CtextureMap.FileName', ''.join(d['path']))
            mp.setByte('CtextureMap.uvwChannel', d['channel'])
            mp.setByte('CtextureMap.uIsTiled', d['tile_method_type'][0])
            mp.setByte('CtextureMap.vIsTiled', d['tile_method_type'][1])
            mp.setByte('CtextureMap.uIsMirrored', d['mirror'][0])
            mp.setByte('CtextureMap.vIsMirrored', d['mirror'][1])
            mp.setFloat('CtextureMap.scale.x', d['repeat'][0])
            mp.setFloat('CtextureMap.scale.y', d['repeat'][1])
            mp.setFloat('CtextureMap.offset.x', d['offset'][0])
            mp.setFloat('CtextureMap.offset.y', d['offset'][1])
            mp.setFloat('CtextureMap.rotation', d['rotation'])
            mp.setByte('CtextureMap.invert', d['invert'])
            mp.setByte('CtextureMap.useAbsoluteUnits', d['tile_method_units'])
            mp.setByte('CtextureMap.useAlpha', d['alpha_only'])
            mp.setByte('CtextureMap.typeInterpolation', d['interpolation'])
            mp.setFloat('CtextureMap.saturation', d['saturation'])
            mp.setFloat('CtextureMap.contrast', d['contrast'])
            mp.setFloat('CtextureMap.brightness', d['brightness'])
            mp.setFloat('CtextureMap.hue', d['hue'])
            mp.setFloat('CtextureMap.clampMin', d['rgb_clamp'][0])
            mp.setFloat('CtextureMap.clampMax', d['rgb_clamp'][1])
            mp.setFloat('CtextureMap.useGlobalMap', d['use_override_map'])
        
        if(d['material'] != ""):
            mat = self.material(d['material'], s, d['material_embed'])
            p.setString('Material', mat.getName())
        if(d['backface_material'] != ""):
            bmat = self.material(d['backface_material'], s, d['backface_material_embed'])
            p.setString('Double Sided Material', bmat.getName())
        
        p.setUInt('Density', d['density'])
        
        mxp = p.getByName('Density Map')[0]
        texture_data_to_mxparams(d['density_map'], p.getByName('Density Map')[0])
        
        p.setFloat('Length', d['length'])
        texture_data_to_mxparams(d['length_map'], p.getByName('Length Map')[0])
        p.setFloat('Length Variation', d['length_variation'])
        
        p.setFloat('Root Width', d['root_width'])
        p.setFloat('Tip Width', d['tip_width'])
        
        p.setUInt('Direction Type', d['direction_type'])
        
        p.setFloat('Initial Angle', d['initial_angle'])
        p.setFloat('Initial Angle Variation', d['initial_angle_variation'])
        texture_data_to_mxparams(d['initial_angle_map'], p.getByName('Initial Angle Map')[0])
        
        p.setFloat('Start Bend', d['start_bend'])
        p.setFloat('Start Bend Variation', d['start_bend_variation'])
        texture_data_to_mxparams(d['start_bend_map'], p.getByName('Start Bend Map')[0])
        
        p.setFloat('Bend Radius', d['bend_radius'])
        p.setFloat('Bend Radius Variation', d['bend_radius_variation'])
        texture_data_to_mxparams(d['bend_radius_map'], p.getByName('Bend Radius Map')[0])
        
        p.setFloat('Bend Angle', d['bend_angle'])
        p.setFloat('Bend Angle Variation', d['bend_angle_variation'])
        texture_data_to_mxparams(d['bend_angle_map'], p.getByName('Bend Angle Map')[0])
        
        p.setFloat('Cut Off', d['cut_off'])
        p.setFloat('Cut Off Variation', d['cut_off_variation'])
        texture_data_to_mxparams(d['cut_off_map'], p.getByName('Cut Off Map')[0])
        
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
        return o
    
    def hair(self, d, ):
        if(d['extension'] == 'MaxwellHair'):
            e = self.mgr.createDefaultGeometryProceduralExtension('MaxwellHair')
        if(d['extension'] == 'MGrassP'):
            e = self.mgr.createDefaultGeometryProceduralExtension('MGrassP')
        
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
        r = MXSBinHairReader(bhp)
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
            mat = self.material(d['material'], s, d['material_embed'])
            o.setMaterial(mat)
        if(d['backface_material'] != ""):
            bm = self.material(d['backface_material'][0], s, d['backface_material_embed'][1])
            o.setBackfaceMaterial(bm)
        
        self.base_and_pivot(o, d)
        self.object_props(o, d)
        return o
    
    def wireframe(self, d, md, ):
        pass
    
    # settings
    def hierarchy(self, d, ):
        s = self.mxs
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
    
    def scene(self, d, ):
        s = self.mxs
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
        s.setRenderParameter('COPY MXI AFTER RENDER', d["output_mxi"])
        s.setRenderParameter('COPY IMAGE AFTER RENDER', d["output_image"])
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
            
            if(t == 'PNG8'):
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
    
    def environment(self, d, ):
        s = self.mxs
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


class MXSWriter2():
    def __init__(self, path, append=False, ):
        """Create scene or load existing.
        path    string (path)
        append  bool
        """
        
        # if('Cmaxwell' not in locals()):
        #     raise ImportError("No pymaxwell..")
        #     return
        
        if(__name__ != "__main__"):
            if(platform.system() == 'Darwin'):
                raise ImportError("No pymaxwell for Mac OS X..")
        
        log(self.__class__.__name__, 1, LogStyles.MESSAGE, prefix="* ", )
        
        self.path = path
        self.mxs = Cmaxwell(mwcallback)
        if(append):
            log("appending to existing scene..", 2, prefix="* ", )
            self.mxs.readMXS(self.path)
        else:
            log("creating new scene..", 2, prefix="* ", )
        
        self.mgr = CextensionManager.instance()
        self.mgr.loadAllExtensions()
        
        self.matdb = []
    
    def set_base_and_pivot(self, o, base=None, pivot=None, ):
        """Convert float tuples to Cbases and set to object.
        o       CmaxwellObject
        base    ((3 float), (3 float), (3 float), (3 float)) or None
        pivot   ((3 float), (3 float), (3 float), (3 float)) or None
        """
        if(base is None):
            base = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        if(pivot is None):
            pivot = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        b = Cbase()
        b.origin = Cvector(*base[0])
        b.xAxis = Cvector(*base[1])
        b.yAxis = Cvector(*base[2])
        b.zAxis = Cvector(*base[3])
        p = Cbase()
        p.origin = Cvector(*pivot[0])
        p.xAxis = Cvector(*pivot[1])
        p.yAxis = Cvector(*pivot[2])
        p.zAxis = Cvector(*pivot[3])
        o.setBaseAndPivot(b, p)
    
    def set_object_props(self, o, hide=False, opacity=100, cid=(255, 255, 255), hcam=False, hcamsc=False, hgi=False, hrr=False, hzcp=False, ):
        """Set common object properties.
        o           CmaxwellObject
        hide        bool
        opacity     float
        cid         (int, int, int) 0-255 rgb
        hcam        bool
        hcamsc      bool
        hgi         bool
        hrr         bool
        hzcp        bool
        """
        if(hide):
            o.setHide(hide)
        if(opacity != 100.0):
            o.setOpacity(opacity)
        c = Crgb()
        c.assign(*[v / 255 for v in cid])
        o.setColorID(c)
        if(hcam):
            o.setHideToCamera(True)
        if(hcamsc):
            o.setHideToCameraInShadowsPass(True)
        if(hgi):
            o.setHideToGI(True)
        if(hrr):
            o.setHideToReflectionsRefractions(True)
        if(hzcp):
            o.excludeOfCutPlanes(True)
    
    def camera(self, props, steps, active=False, lens_extra=None, response=None, region=None, custom_bokeh=(1.0, 0.0, False), cut_planes=(0.0, 1e7, False), shift_lens=(0.0, 0.0), ):
        """Create camera.
        props           (string name, int nSteps, float shutter, float filmWidth, float filmHeight, float iso, int diaphragmType, float angle,
                         int nBlades, float fps, int xRes, int yRes, float pixelAspect, int lensType, int projectionType)
        steps           [(int iStep, [3 float] origin, [3 float] focalPoint, [3 float] up, float focalLength, float fStop, bool focalLengthNeedCorrection), ..., ]
        active          bool
        lens_extra      float or None
        response        string or None
        region          (float x1, float y1, float x2, float y2, string type) or None
        custom_bokeh    (float ratio, float angle, bool enabled) or None
        cut_planes      (float near, float far, bool enabled) or None
        shift_lens      (float x, float y) or None
        """
        
        # TODO how to set shutter_angle?
        
        s = self.mxs
        c = s.addCamera(*props)
        for step in steps:
            l = list(step[:])
            l[1] = Cvector(*l[1])
            l[2] = Cvector(*l[2])
            l[3] = Cvector(*l[3])
            c.setStep(*l)
        
        # TYPE_THIN_LENS, TYPE_PINHOLE, TYPE_ORTHO
        if(lens_extra is not None):
            if(props[13] == TYPE_FISHEYE):
                c.setFishLensProperties(lens_extra)
            if(props[13] == TYPE_SPHERICAL):
                c.setSphericalLensProperties(lens_extra)
            if(props[13] == TYPE_CYLINDRICAL):
                c.setCylindricalLensProperties(lens_extra)
        if(response is not None):
            c.setCameraResponsePreset(response)
        if(custom_bokeh is not None):
            c.setCustomBokeh(*custom_bokeh)
        if(cut_planes is not None):
            c.setCutPlanes(*cut_planes)
        if(shift_lens is not None):
            c.setShiftLens(*shift_lens)
        if(region is not None):
            c.setScreenRegion(*region)
        
        if(active):
            c.setActive()
        return c
    
    def load_material(self, path, embed, ):
        """Load material from mxm file.
        path    string or None
        embed   bool
        """
        s = self.mxs
        r = None
        for p, m, e in self.matdb:
            if(p == path):
                r = m
        pok = False
        if(path is not None):
            if(path is not ""):
                if(path.endswith('.mxm')):
                    if(os.path.exists(path)):
                        pok = True
        if(r is None and pok):
            t = s.readMaterial(path)
            r = s.addMaterial(t)
            self.matdb.append((path, r, embed))
            if(embed is False):
                r.setReference(1, path)
        return r
    
    def material_placeholder(self):
        """Create material placeholder when needed to keem trangle material groups."""
        s = self.mxs
        n = 'MATERIAL_PLACEHOLDER'
        # return clone if already loaded
        for p, m, e in self.matdb:
            if(p == n):
                c = m.createCopy()
                cm = s.addMaterial(c)
                return cm
        # load binary mxm file from base64
        import base64
        import os
        checker = b'TVhNPQoHQAdkZWZhdWx0AAAAAAAAAADrFyo+Tw1CP8ukdz8IAAAAAAAAAAA+QANyZ2IAAAA/AAAA\nPwAAAD8KdGV4dHVyZW1hcAAAAAAAAADwPwAAAAAAAPA/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAQEAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAAAAAAADwPwAAAAAA\nAPA/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAACAPwAAAAAAAAAAAAAA8D8AAAAAAADwPwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAAADcmdiAAAAPwAA\nAD8AAAA/CnRleHR1cmVtYXAAAAAAAAAA8D8AAAAAAADwPwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAEBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAAAJEAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAPA/AAAAAAAA8D8AAAAAAADwPwAAAgAA\nBUxheWVyAQAAAQAAAAAAAABZQANyZ2IAAAA/AAAAPwAAAD8KdGV4dHVyZW1hcAAAAAAAAADwPwAA\nAAAAAPA/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAACAPwAAAAAAAAAEQlNERgEAAAAAAAAAAFlAA3JnYgAAAD8AAAA/AAAAPwp0ZXh0dXJl\nbWFwAAAAAAAAAPA/AAAAAAAA8D8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAEAAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAWUADcmdiAAAAPwAAAD8AAAA/CnRl\neHR1cmVtYXAAAAAAAAAA8D8AAAAAAADwPwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAAAAAAAA\nAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAANyZ2IAAAA/AAAAPwAA\nAD8KdGV4dHVyZW1hcAAAAAAAAADwPwAAAAAAAPA/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQEA\nAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAAAAAAAAAAAD5AA3JnYgAAAD8A\nAAA/AAAAPwp0ZXh0dXJlbWFwAAAAAAAAAPA/AAAAAAAA8D8AAAAAAAAAAAAAAAAAAAAAAAAAAAAA\nAAABAQAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAAADcmdi\nAAAAPwAAAD8AAAA/CnRleHR1cmVtYXAAAAAAAAAA8D8AAAAAAADwPwAAAAAAAAAAAAAAAAAAAAAA\nAAAAAAAAAAEBAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAEAAAAA\nAABZQANyZ2KamRk/mpkZP5qZGT8KdGV4dHVyZW1hcAAAAAAAAADwPwAAAAAAAPA/AAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAQEAAAABAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAPwAAAAAA\nAQAAAAAAAFlAA3JnYgAAgD8AAIA/AACAPwp0ZXh0dXJlbWFwAAAAAAAAAPA/AAAAAAAA8D8AAAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAAAAEAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIA/\nAAAAAAAAAAAAAAAIQAAAAAAAAElAAAAAAAAAAAABAAAAAAAAWUADcmdiAAAAAAAAAAAAAAAACnRl\neHR1cmVtYXAAAAAAAAAA8D8AAAAAAADwPwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEBAAAAAQAA\nAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAACV1iboCy4RPh+I00puUHNAAQAA\nAAAAAFlAA3JnYgAAAD8AAAA/AAAAPwp0ZXh0dXJlbWFwAAAAAAAAAPA/AAAAAAAA8D8AAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAAABAQAAAAEAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIA/AAAA\nAAAAAAAAAAAAAAAAAAAAAAAAAPyp8dJNYlA/A3JnYgAAAD8AAAA/AAAAPwp0ZXh0dXJlbWFwAAAA\nAAAAAPA/AAAAAAAA8D8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAAAAAAAAEAAAAAAAAAAAAA\nAAAAAAAAAAAAAAAAAAAAAIA/AAAAAACN7bWg98awPnsUrkfheoQ/AAAAAAAAAA==\n'
        # save it do working directory
        loc, _ = os.path.split(os.path.realpath(__file__))
        p = os.path.join(loc, "{}.mxm".format(n))
        with open(p, "wb") as bf:
            b = base64.decodebytes(checker)
            d = bf.write(b)
        # load it
        t = s.readMaterial(p)
        t.setName(n)
        m = s.addMaterial(t)
        self.matdb.append((n, m, True))
        # and erase it
        os.remove(p)
        return m
    
    def empty(self, name, base, pivot, object_props=None, ):
        """Create empty object.
        name            string
        base            ((3 float), (3 float), (3 float), (3 float))
        pivot           ((3 float), (3 float), (3 float), (3 float))
        object_props    (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        """
        s = self.mxs
        o = s.createMesh(name, 0, 0, 0, 0, )
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        return o
    
    def mesh(self, name, base, pivot, num_positions, vertices, normals, triangles, triangle_normals, uv_channels, object_props=None, num_materials=0, materials=[], triangle_materials=None, backface_material=None, ):
        """Create mesh object.
        name                string
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        num_positions       int
        vertices            [[(float x, float y, float z), ..., ], [...], ]
        normals             [[(float x, float y, float z), ..., ], [...], ]
        triangles           [(int iv0, int iv1, int iv2, int in0, int in1, int in2, ), ..., ], ]   # (3x vertex index, 3x normal index)
        triangle_normals    [[(float x, float y, float z), ..., ], [...], ]
        uv_channels         [[(float u1, float v1, float w1, float u2, float v2, float w2, float u3, float v3, float w3, ), ..., ], ..., ] or None      # ordered by uv index and ordered by triangle index
        num_materials       int
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        materials           [(string path, bool embed), ..., ] or None
        triangle_materials  [(int tri_id, int mat_id), ..., ] or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        o = s.createMesh(name, len(vertices[0]), len(normals[0]) + len(triangle_normals[0]), len(triangles), num_positions)
        if(uv_channels is not None):
            for i in range(len(uv_channels)):
                o.addChannelUVW(i)
        an = 0
        for ip in range(num_positions):
            verts = vertices[ip]
            norms = normals[ip]
            for i, loc in enumerate(verts):
                o.setVertex(i, ip, Cvector(*loc), )
                o.setNormal(i, ip, Cvector(*norms[i]), )
                an += 1
        for ip in range(num_positions):
            trinorms = triangle_normals[ip]
            for i, nor in enumerate(trinorms):
                o.setNormal(an + i, ip, Cvector(*nor), )
        for i, tri in enumerate(triangles):
            o.setTriangle(i, *tri)
        if(uv_channels is not None):
            for iuv, uv in enumerate(uv_channels):
                for it, t in enumerate(uv):
                    o.setTriangleUVW(it, iuv, *t)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(materials is not None):
            if(num_materials > 1):
                # multi material
                mats = []
                for mi in range(num_materials):
                    mat = self.load_material(*materials[mi])
                    if(mat is None):
                        mat = self.material_placeholder()
                    mats.append(mat)
                for tid, mid in triangle_materials:
                    o.setTriangleMaterial(tid, mats[mid])
            elif(num_materials == 1):
                # single material
                mat = self.load_material(*materials[0])
                if(mat is not None):
                    # set for whole object, no need to care about triangles
                    o.setMaterial(mat)
        else:
            # no material
            pass
        
        if(backface_material is not None):
            # only single backface material
            mat = self.load_material(*backface_material)
            if(mat is not None):
                o.setBackfaceMaterial(mat)
        
        return o
    
    def instance(self, name, instanced_name, base, pivot, object_props=None, material=None, backface_material=None, ):
        """Create instance of mesh object. Instanced object must exist in scene.
        name                string
        instanced_name      string
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        bo = s.getObject(instanced_name)
        o = s.createInstancement(name, bo)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(material is not None):
            m = self.load_material(*material)
            if(m is not None):
                o.setMaterial(m)
        if(backface_material is not None):
            m = self.load_material(*backface_material)
            if(m is not None):
                o.setBackfaceMaterial(m)
        
        return o
    
    def hierarchy(self, tree, ):
        """Set hierarchy of all objects at once.
        tree    [(obj_name, parent_name or None, ), ..., ]
        """
        s = self.mxs
        for on, pn in tree:
            if(pn is not None):
                o = s.getObject(on)
                p = s.getObject(pn)
                o.setParent(p)
    
    def environment(self, env_type=None, sky_type=None, sky=None, dome=None, sun_type=None, sun=None, ibl=None, ):
        """Set Environment properties.
        env_type    string or None      PHYSICAL_SKY, IMAGE_BASED, NONE
        sky_type    string or None      PHYSICAL, CONSTANT
        sky         dict or None        {sky_use_preset         bool
                                         sky_preset             string (path)
                                         sky_intensity          float
                                         sky_planet_refl        float
                                         sky_ozone              float
                                         sky_water              float
                                         sky_turbidity_coeff    float
                                         sky_wavelength_exp     float
                                         sky_reflectance        float
                                         sky_asymmetry          float}
        dome        dict or None        {dome_intensity         float
                                         dome_zenith            [float, float, float]
                                         dome_horizon           [float, float, float]
                                         dome_mid_point         float}
        sun_type    string or None      DISABLED, PHYSICAL, CUSTOM
        sun         dict or None        {sun_power                      float
                                         sun_radius_factor              float
                                         sun_temp                       float
                                         sun_color                      [float, float, float]
                                         sun_location_type              string      LATLONG, ANGLES, DIRECTION
                                         sun_latlong_lat                float
                                         sun_latlong_lon                float
                                         sun_date                       string
                                         sun_time                       string
                                         sun_latlong_gmt                int
                                         sun_latlong_gmt_auto           bool
                                         sun_latlong_ground_rotation    float
                                         sun_angles_zenith              float
                                         sun_angles_azimuth             float
                                         sun_dir_x                      float
                                         sun_dir_y                      float
                                         sun_dir_z                      float}
        ibl         dict or None        {ibl_intensity          float
                                         ibl_interpolation      bool
                                         ibl_screen_mapping     bool
                                         ibl_bg_type            string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_bg_map             string (path)
                                         ibl_bg_intensity       float
                                         ibl_bg_scale_x         float
                                         ibl_bg_scale_y         float
                                         ibl_bg_offset_x        float
                                         ibl_bg_offset_y        float
                                         ibl_refl_type          string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_refl_map           string (path)
                                         ibl_refl_intensity     float
                                         ibl_refl_scale_x       float
                                         ibl_refl_scale_y       float
                                         ibl_refl_offset_x      float
                                         ibl_refl_offset_y      float
                                         ibl_refr_type          string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_refr_map           string (path)
                                         ibl_refr_intensity     float
                                         ibl_refr_scale_x       float
                                         ibl_refr_scale_y       float
                                         ibl_refr_offset_x      float
                                         ibl_refr_offset_y      float
                                         ibl_illum_type         string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_illum_map          string (path)
                                         ibl_illum_intensity    float
                                         ibl_illum_scale_x      float
                                         ibl_illum_scale_y      float
                                         ibl_illum_offset_x     float
                                         ibl_illum_offset_y     float}
        """
        s = self.mxs
        env = s.getEnvironment()
        if(env_type == 'PHYSICAL_SKY'):
            if(sky_type is not None):
                env.setActiveSky(sky_type)
                if(sky_type == 'PHYSICAL'):
                    if(not sky["sky_use_preset"]):
                        env.setPhysicalSkyAtmosphere(sky["sky_intensity"],
                                                     sky["sky_ozone"],
                                                     sky["sky_water"],
                                                     sky["sky_turbidity_coeff"],
                                                     sky["sky_wavelength_exp"],
                                                     sky["sky_reflectance"],
                                                     sky["sky_asymmetry"],
                                                     sky["sky_planet_refl"], )
                    else:
                        env.loadSkyFromPreset(sky["sky_preset"])
                    
                    sc = Crgb()
                    sc.assign(*[c / 255 for c in sun['sun_color']])
                    if(sun_type == 'PHYSICAL'):
                        env.setSunProperties(SUN_PHYSICAL, sun["sun_temp"], sun["sun_power"], sun["sun_radius_factor"], sc)
                    elif(sun_type == 'CUSTOM'):
                        env.setSunProperties(SUN_CONSTANT, sun["sun_temp"], sun["sun_power"], sun["sun_radius_factor"], sc)
                    else:
                        # sun_type == 'DISABLED' or sun_type == None
                        env.setSunProperties(SUN_DISABLED, sun["sun_temp"], sun["sun_power"], sun["sun_radius_factor"], sc)
                    
                    if(sun['sun_location_type'] == 'LATLONG'):
                        env.setSunPositionType(0)
                        l = sun["sun_date"].split(".")
                        date = datetime.date(int(l[2]), int(l[1]), int(l[0]))
                        day = int(date.timetuple().tm_yday)
                        l = sun["sun_time"].split(":")
                        hour = int(l[0])
                        minute = int(l[1])
                        time = hour + (minute / 60)
                        env.setSunLongitudeAndLatitude(sun["sun_latlong_lon"], sun["sun_latlong_lat"], sun["sun_latlong_gmt"], day, time)
                        env.setSunRotation(sun["sun_latlong_ground_rotation"])
                    elif(sun['sun_location_type'] == 'ANGLES'):
                        env.setSunPositionType(1)
                        env.setSunAngles(sun["sun_angles_zenith"], sun["sun_angles_azimuth"])
                    elif(sun['sun_location_type'] == 'DIRECTION'):
                        env.setSunPositionType(2)
                        env.setSunDirection(Cvector(sun["sun_dir_x"], sun["sun_dir_y"], sun["sun_dir_z"]))
                
                elif(sky_type == 'CONSTANT'):
                    hc = Crgb()
                    hc.assign(*[c / 255 for c in dome['dome_horizon']])
                    zc = Crgb()
                    zc.assign(*[c / 255 for c in dome['dome_zenith']])
                    env.setSkyConstant(dome["dome_intensity"], hc, zc, dome['dome_mid_point'])
        elif(env_type == 'IMAGE_BASED'):
            env.enableEnvironment(True)
            
            def state(s):
                if(s == 'HDR_IMAGE'):
                    return 1
                if(s == 'SAME_AS_BG'):
                    return 2
                return 0
            
            env.setEnvironmentWeight(ibl["ibl_intensity"])
            env.setEnvironmentLayer(IBL_LAYER_BACKGROUND, ibl["ibl_bg_map"], state(ibl["ibl_bg_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_bg_intensity"], ibl["ibl_bg_scale_x"], ibl["ibl_bg_scale_y"], ibl["ibl_bg_offset_x"], ibl["ibl_bg_offset_y"], )
            env.setEnvironmentLayer(IBL_LAYER_REFLECTION, ibl["ibl_refl_map"], state(ibl["ibl_refl_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_refl_intensity"], ibl["ibl_refl_scale_x"], ibl["ibl_refl_scale_y"], ibl["ibl_refl_offset_x"], ibl["ibl_refl_offset_y"], )
            env.setEnvironmentLayer(IBL_LAYER_REFRACTION, ibl["ibl_refr_map"], state(ibl["ibl_refr_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_refr_intensity"], ibl["ibl_refr_scale_x"], ibl["ibl_refr_scale_y"], ibl["ibl_refr_offset_x"], ibl["ibl_refr_offset_y"], )
            env.setEnvironmentLayer(IBL_LAYER_ILLUMINATION, ibl["ibl_illum_map"], state(ibl["ibl_illum_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_illum_intensity"], ibl["ibl_illum_scale_x"], ibl["ibl_illum_scale_y"], ibl["ibl_illum_offset_x"], ibl["ibl_illum_offset_y"], )
        else:
            # env_type == 'NONE' or env_type == None
            env.setActiveSky('')
    
    def parameters(self, scene, materials=None, generals=None, tone=None, simulens=None, illum_caustics=None, ):
        """Set scene render parameters.
        scene           dict    {cpu_threads        int,
                                 multilight         int,
                                 multilight_type    int,
                                 quality            string      RS1, RS0
                                 sampling_level     float,
                                 time               int, },
        materials       dict    {override           bool,
                                 override_path      string (path),
                                 search_path        string (path), } or None
        generals        dict    {diplacement        bool,
                                 dispersion         bool,
                                 motion_blur        bool, } or None
        tone            dict    {burn               float,
                                 color_space        int,
                                 gamma              float,
                                 sharpness          bool,
                                 sharpness_value    float,
                                 tint               float,
                                 whitepoint         float, } or None
        simulens        dict    {aperture_map       string (path),
                                 devignetting       bool,
                                 devignetting_value float,
                                 diffraction        bool,
                                 diffraction_value  float,
                                 frequency          float,
                                 obstacle_map       string (path),
                                 scattering         bool,
                                 scattering_value   float, } or None
        illum_caustics  dict    {illumination       int,
                                 refl_caustics      int,
                                 refr_caustics      int, } or None
        """
        s = self.mxs
        s.setRenderParameter('ENGINE', scene["quality"])
        s.setRenderParameter('NUM THREADS', scene["cpu_threads"])
        s.setRenderParameter('STOP TIME', scene["time"] * 60)
        s.setRenderParameter('SAMPLING LEVEL', scene["sampling_level"])
        s.setRenderParameter('USE MULTILIGHT', scene["multilight"])
        s.setRenderParameter('SAVE LIGHTS IN SEPARATE FILES', scene["multilight_type"])
        
        if(generals is not None):
            s.setRenderParameter('DO MOTION BLUR', generals["motion_blur"])
            s.setRenderParameter('DO DISPLACEMENT', generals["diplacement"])
            s.setRenderParameter('DO DISPERSION', generals["dispersion"])
        
        if(illum_caustics is not None):
            v = illum_caustics['illumination']
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
            v = illum_caustics['refl_caustics']
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
            v = illum_caustics['refr_caustics']
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
        
        if(simulens is not None):
            s.setRenderParameter('DO DEVIGNETTING', simulens["devignetting"])
            s.setRenderParameter('DEVIGNETTING', simulens["devignetting_value"])
            s.setRenderParameter('DO SCATTERING_LENS', simulens["scattering"])
            s.setRenderParameter('SCATTERING_LENS', simulens["scattering_value"])
            if(simulens["diffraction"]):
                s.enableDiffraction()
                s.setDiffraction(simulens["diffraction_value"], simulens["frequency"], simulens["aperture_map"], simulens["obstacle_map"])
        
        if(tone is not None):
            s.setRenderParameter('DO SHARPNESS', tone["sharpness"])
            s.setRenderParameter('SHARPNESS', tone["sharpness_value"])
            s.setToneMapping(tone["gamma"], tone["burn"])
            s.setColorSpace(tone["color_space"])
            s.setWhitePoint(tone["whitepoint"], tone["tint"])
        
        if(materials is not None):
            if(materials["override"]):
                s.setOverrideMaterial(True)
            if(materials["override_path"] != ""):
                s.setOverrideMaterial(materials["override_path"])
            if(materials["search_path"] != ""):
                s.addSearchingPath(materials["search_path"])
    
    def channels(self, base_path, mxi, image, image_depth='RGB8', channels_output_mode=0, channels_render=True, channels_render_type=0, channels=None, ):
        """Set scene render channels.
        base_path               string (path)
        mxi                     string (path)
        image                   string (path)
        image_depth             string              RGB8, RGB16, RGB32
        channels_output_mode    int
        channels_render         bool
        channels_render_type    int
        channels                dict     {channels_alpha                  bool
                                          channels_alpha_file             string
                                          channels_alpha_opaque           bool
                                          channels_custom_alpha           bool
                                          channels_custom_alpha_file      string
                                          channels_deep                   bool
                                          channels_deep_file              string
                                          channels_deep_max_samples       int
                                          channels_deep_min_dist          float
                                          channels_deep_type              int
                                          channels_fresnel                bool
                                          channels_fresnel_file           string
                                          channels_material_id            bool
                                          channels_material_id_file       string
                                          channels_motion_vector          bool
                                          channels_motion_vector_file     string
                                          channels_normals                bool
                                          channels_normals_file           string
                                          channels_normals_space          int
                                          channels_object_id              bool
                                          channels_object_id_file         string
                                          channels_position               bool
                                          channels_position_file          string
                                          channels_position_space         int
                                          channels_roughness              bool
                                          channels_roughness_file         string
                                          channels_shadow                 bool
                                          channels_shadow_file            string
                                          channels_uv                     bool
                                          channels_uv_file                string
                                          channels_z_buffer               bool
                                          channels_z_buffer_far           float
                                          channels_z_buffer_file          string
                                          channels_z_buffer_near          float} or None
        """
        s = self.mxs
        
        s.setRenderParameter('DO NOT SAVE MXI FILE', (mxi is None))
        s.setRenderParameter('DO NOT SAVE IMAGE FILE', (image is None))
        if(mxi is not None):
            s.setRenderParameter('MXI FULLNAME', mxi)
            s.setRenderParameter('COPY MXI AFTER RENDER', mxi)
        if(image is not None):
            s.setRenderParameter('COPY IMAGE AFTER RENDER', image)
        # s.setRenderParameter('RENAME AFTER SAVING', d[""])
        # s.setRenderParameter('REMOVE FILES AFTER COPY', d[""])
        
        if(channels_render_type == 2):
            s.setRenderParameter('DO DIFFUSE LAYER', 0)
            s.setRenderParameter('DO REFLECTION LAYER', 1)
        elif(channels_render_type == 1):
            s.setRenderParameter('DO DIFFUSE LAYER', 1)
            s.setRenderParameter('DO REFLECTION LAYER', 0)
        else:
            s.setRenderParameter('DO DIFFUSE LAYER', 1)
            s.setRenderParameter('DO REFLECTION LAYER', 1)
        
        def get_ext_depth(t, e=None):
            if(e is not None):
                t = "{}{}".format(e[1:].upper(), int(t[3:]))
            
            if(t == 'PNG8'):
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
        
        if(image is not None):
            if(image_depth is None):
                image_depth = 'PNG8'
            _, depth = get_ext_depth(image_depth, os.path.splitext(os.path.split(image)[1])[1])
            s.setPath('RENDER', image, depth)
        
        s.setRenderParameter('DO RENDER CHANNEL', int(channels_render))
        s.setRenderParameter('EMBED CHANNELS', channels_output_mode)
        
        if(channels is not None):
            e, depth = get_ext_depth(channels["channels_alpha_file"])
            s.setPath('ALPHA', "{}_alpha{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_shadow_file"])
            s.setPath('SHADOW', "{}_shadow{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_object_id_file"])
            s.setPath('OBJECT', "{}_object_id{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_material_id_file"])
            s.setPath('MATERIAL', "{}_material_id{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_motion_vector_file"])
            s.setPath('MOTION', "{}_motion_vector{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_z_buffer_file"])
            s.setPath('Z', "{}_z_buffer{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_roughness_file"])
            s.setPath('ROUGHNESS', "{}_roughness{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_fresnel_file"])
            s.setPath('FRESNEL', "{}_fresnel{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_normals_file"])
            s.setPath('NORMALS', "{}_normals{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_position_file"])
            s.setPath('POSITION', "{}_position{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_deep_file"])
            s.setPath('DEEP', "{}_deep{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_uv_file"])
            s.setPath('UV', "{}_uv{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_custom_alpha_file"])
            s.setPath('ALPHA_CUSTOM', "{}_custom_alpha{}".format(base_path, e), depth)
            
            s.setRenderParameter('DO ALPHA CHANNEL', int(channels["channels_alpha"]))
            s.setRenderParameter('OPAQUE ALPHA', int(channels["channels_alpha_opaque"]))
            s.setRenderParameter('DO IDOBJECT CHANNEL', int(channels["channels_object_id"]))
            s.setRenderParameter('DO IDMATERIAL CHANNEL', int(channels["channels_material_id"]))
            s.setRenderParameter('DO SHADOW PASS CHANNEL', int(channels["channels_shadow"]))
            s.setRenderParameter('DO MOTION CHANNEL', int(channels["channels_motion_vector"]))
            s.setRenderParameter('DO ROUGHNESS CHANNEL', int(channels["channels_roughness"]))
            s.setRenderParameter('DO FRESNEL CHANNEL', int(channels["channels_fresnel"]))
            s.setRenderParameter('DO NORMALS CHANNEL', int(channels["channels_normals"]))
            s.setRenderParameter('NORMALS CHANNEL SPACE', channels["channels_normals_space"])
            s.setRenderParameter('POSITION CHANNEL SPACE', channels["channels_position_space"])
            s.setRenderParameter('DO POSITION CHANNEL', int(channels["channels_position"]))
            s.setRenderParameter('DO ZBUFFER CHANNEL', int(channels["channels_z_buffer"]))
            s.setRenderParameter('ZBUFFER RANGE', (channels["channels_z_buffer_near"], channels["channels_z_buffer_far"]))
            s.setRenderParameter('DO DEEP CHANNEL', int(channels["channels_deep"]))
            s.setRenderParameter('DEEP CHANNEL TYPE', channels["channels_deep_type"])
            s.setRenderParameter('DEEP MIN DISTANCE', channels["channels_deep_min_dist"])
            s.setRenderParameter('DEEP MAX SAMPLES', channels["channels_deep_max_samples"])
            s.setRenderParameter('DO UV CHANNEL', int(channels["channels_uv"]))
            # s.setRenderParameter('MOTION CHANNEL TYPE', ?)
            s.setRenderParameter('DO ALPHA CUSTOM CHANNEL', int(channels["channels_custom_alpha"]))
    
    def custom_alphas(self, groups, ):
        """Set custom alphas.
        groups      list of dicts: {'name': string, 'objects': list of strings, 'opaque': bool, }
        """
        s = self.mxs
        for a in groups:
            s.createCustomAlphaChannel(a['name'], a['opaque'])
            for n in a['objects']:
                o = s.getObject(n)
                o.addToCustomAlpha(a['name'])
    
    def hair(self, name, extension, base, pivot, root_radius, tip_radius, data, object_props=None, display_percent=10, display_max=1000, material=None, backface_material=None, ):
        """Create hair/grass object.
        name                string
        extension           string ('MaxwellHair' ,'MGrassP')
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        root_radius         float
        tip_radius          float
        data                dict of extension data
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        display_percent     int
        display_max         int
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryProceduralExtension(extension)
        p = e.getExtensionData()
        p.setByteArray('HAIR_MAJOR_VER', data['HAIR_MAJOR_VER'])
        p.setByteArray('HAIR_MINOR_VER', data['HAIR_MINOR_VER'])
        p.setByteArray('HAIR_FLAG_ROOT_UVS', data['HAIR_FLAG_ROOT_UVS'])
        
        m = memoryview(struct.pack("I", data['HAIR_GUIDES_COUNT'][0])).tolist()
        p.setByteArray('HAIR_GUIDES_COUNT', m)
        m = memoryview(struct.pack("I", data['HAIR_GUIDES_POINT_COUNT'][0])).tolist()
        p.setByteArray('HAIR_GUIDES_POINT_COUNT', m)
        
        c = Cbase()
        c.origin = Cvector(0.0, 0.0, 0.0)
        c.xAxis = Cvector(1.0, 0.0, 0.0)
        c.yAxis = Cvector(0.0, 1.0, 0.0)
        c.zAxis = Cvector(0.0, 0.0, 1.0)
        
        p.setFloatArray('HAIR_POINTS', list(data['HAIR_POINTS']), c)
        p.setFloatArray('HAIR_NORMALS', list(data['HAIR_NORMALS']), c)
        
        p.setUInt('Display Percent', display_percent)
        if(extension == 'MaxwellHair'):
            p.setUInt('Display Max. Hairs', display_max)
            p.setDouble('Root Radius', root_radius)
            p.setDouble('Tip Radius', tip_radius)
        if(extension == 'MGrassP'):
            p.setUInt('Display Max. Hairs', display_max)
            p.setDouble('Root Radius', root_width)
            p.setDouble('Tip Radius', tip_width)
        
        o = s.createGeometryProceduralObject(name, p)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(material is not None):
            mat = self.load_material(material)
            if(mat is not None):
                o.setMaterial(mat)
        if(backface_material is not None):
            mat = self.load_material(backface_material)
            if(mat is not None):
                o.setBackfaceMaterial(mat)
        
        return o
    
    def texture_data_to_mxparams(self, data, mxparams):
        if(data is None):
            return
        # mp.setString('CtextureMap.FileName', d['path'])
        # hey, seriously.. WTF?
        mxparams.setString('CtextureMap.FileName', ''.join(data['path']))
        mxparams.setByte('CtextureMap.uvwChannel', data['channel'])
        mxparams.setByte('CtextureMap.uIsTiled', data['tile_method_type'][0])
        mxparams.setByte('CtextureMap.vIsTiled', data['tile_method_type'][1])
        mxparams.setByte('CtextureMap.uIsMirrored', data['mirror'][0])
        mxparams.setByte('CtextureMap.vIsMirrored', data['mirror'][1])
        mxparams.setFloat('CtextureMap.scale.x', data['repeat'][0])
        mxparams.setFloat('CtextureMap.scale.y', data['repeat'][1])
        mxparams.setFloat('CtextureMap.offset.x', data['offset'][0])
        mxparams.setFloat('CtextureMap.offset.y', data['offset'][1])
        mxparams.setFloat('CtextureMap.rotation', data['rotation'])
        mxparams.setByte('CtextureMap.invert', data['invert'])
        mxparams.setByte('CtextureMap.useAbsoluteUnits', data['tile_method_units'])
        mxparams.setByte('CtextureMap.useAlpha', data['alpha_only'])
        mxparams.setByte('CtextureMap.typeInterpolation', data['interpolation'])
        mxparams.setFloat('CtextureMap.saturation', data['saturation'])
        mxparams.setFloat('CtextureMap.contrast', data['contrast'])
        mxparams.setFloat('CtextureMap.brightness', data['brightness'])
        mxparams.setFloat('CtextureMap.hue', data['hue'])
        mxparams.setFloat('CtextureMap.clampMin', data['rgb_clamp'][0])
        mxparams.setFloat('CtextureMap.clampMax', data['rgb_clamp'][1])
        mxparams.setFloat('CtextureMap.useGlobalMap', data['use_override_map'])
    
    def grass(self, name, object_name, properties, material=None, backface_material=None, ):
        """Create grass object modifier extension.
        name                string
        object_name         string
        properties          dict of many, many properties, see code..
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryModifierExtension('MaxwellGrass')
        p = e.getExtensionData()
        
        if(material is not None):
            mat = self.load_material(*material)
            if(mat is not None):
                p.setString('Material', mat.getName())
        if(backface_material is not None):
            mat = self.load_material(*backface_material)
            if(mat is not None):
                p.setString('Double Sided Material', bmat.getName())
        
        p.setUInt('Density', properties['density'])
        
        mxp = p.getByName('Density Map')[0]
        self.texture_data_to_mxparams(properties['density_map'], p.getByName('Density Map')[0])
        
        p.setFloat('Length', properties['length'])
        self.texture_data_to_mxparams(properties['length_map'], p.getByName('Length Map')[0])
        p.setFloat('Length Variation', properties['length_variation'])
        
        p.setFloat('Root Width', properties['root_width'])
        p.setFloat('Tip Width', properties['tip_width'])
        
        p.setUInt('Direction Type', properties['direction_type'])
        
        p.setFloat('Initial Angle', properties['initial_angle'])
        p.setFloat('Initial Angle Variation', properties['initial_angle_variation'])
        self.texture_data_to_mxparams(properties['initial_angle_map'], p.getByName('Initial Angle Map')[0])
        
        p.setFloat('Start Bend', properties['start_bend'])
        p.setFloat('Start Bend Variation', properties['start_bend_variation'])
        self.texture_data_to_mxparams(properties['start_bend_map'], p.getByName('Start Bend Map')[0])
        
        p.setFloat('Bend Radius', properties['bend_radius'])
        p.setFloat('Bend Radius Variation', properties['bend_radius_variation'])
        self.texture_data_to_mxparams(properties['bend_radius_map'], p.getByName('Bend Radius Map')[0])
        
        p.setFloat('Bend Angle', properties['bend_angle'])
        p.setFloat('Bend Angle Variation', properties['bend_angle_variation'])
        self.texture_data_to_mxparams(properties['bend_angle_map'], p.getByName('Bend Angle Map')[0])
        
        p.setFloat('Cut Off', properties['cut_off'])
        p.setFloat('Cut Off Variation', properties['cut_off_variation'])
        self.texture_data_to_mxparams(properties['cut_off_map'], p.getByName('Cut Off Map')[0])
        
        p.setUInt('Points per Blade', properties['points_per_blade'])
        p.setUInt('Primitive Type', properties['primitive_type'])
        
        p.setUInt('Seed', properties['seed'])
        
        p.setByte('Enable LOD', properties['lod'])
        p.setFloat('LOD Min Distance', properties['lod_min_distance'])
        p.setFloat('LOD Max Distance', properties['lod_max_distance'])
        p.setFloat('LOD Max Distance Density', properties['lod_max_distance_density'])
        
        p.setUInt('Display Percent', properties['display_percent'])
        p.setUInt('Display Max. Blades', properties['display_max_blades'])
        
        o = s.getObject(object_name)
        o.applyGeometryModifierExtension(p)
        return o
    
    def particles(self, name, properties, base, pivot, object_props=None, material=None, backface_material=None, ):
        """Create particles object.
        name                string
        properties          dict
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryProceduralExtension('MaxwellParticles')
        p = e.getExtensionData()
        d = properties
        
        p.setString('FileName', d['filename'])
        p.setFloat('Radius Factor', d['radius_multiplier'])
        p.setFloat('MB Factor', d['motion_blur_multiplier'])
        p.setFloat('Shutter 1/', d['shutter_speed'])
        p.setFloat('Load particles %', d['load_particles'])
        p.setUInt('Axis', d['axis_system'])
        p.setInt('Frame#', d['frame_number'])
        p.setFloat('fps', d['fps'])
        p.setInt('Create N particles per particle', d['extra_create_np_pp'])
        p.setFloat('Extra particles dispersion', d['extra_dispersion'])
        p.setFloat('Extra particles deformation', d['extra_deformation'])
        p.setByte('Load particle Force', d['load_force'])
        p.setByte('Load particle Vorticity', d['load_vorticity'])
        p.setByte('Load particle Normal', d['load_normal'])
        p.setByte('Load particle neighbors no.', d['load_neighbors_num'])
        p.setByte('Load particle UV', d['load_uv'])
        p.setByte('Load particle Age', d['load_age'])
        p.setByte('Load particle Isolation Time', d['load_isolation_time'])
        p.setByte('Load particle Viscosity', d['load_viscosity'])
        p.setByte('Load particle Density', d['load_density'])
        p.setByte('Load particle Pressure', d['load_pressure'])
        p.setByte('Load particle Mass', d['load_mass'])
        p.setByte('Load particle Temperature', d['load_temperature'])
        p.setByte('Load particle ID', d['load_id'])
        p.setFloat('Min Force', d['min_force'])
        p.setFloat('Max Force', d['max_force'])
        p.setFloat('Min Vorticity', d['min_vorticity'])
        p.setFloat('Max Vorticity', d['max_vorticity'])
        p.setInt('Min Nneighbors', d['min_nneighbors'])
        p.setInt('Max Nneighbors', d['max_nneighbors'])
        p.setFloat('Min Age', d['min_age'])
        p.setFloat('Max Age', d['max_age'])
        p.setFloat('Min Isolation Time', d['min_isolation_time'])
        p.setFloat('Max Isolation Time', d['max_isolation_time'])
        p.setFloat('Min Viscosity', d['min_viscosity'])
        p.setFloat('Max Viscosity', d['max_viscosity'])
        p.setFloat('Min Density', d['min_density'])
        p.setFloat('Max Density', d['max_density'])
        p.setFloat('Min Pressure', d['min_pressure'])
        p.setFloat('Max Pressure', d['max_pressure'])
        p.setFloat('Min Mass', d['min_mass'])
        p.setFloat('Max Mass', d['max_mass'])
        p.setFloat('Min Temperature', d['min_temperature'])
        p.setFloat('Max Temperature', d['max_temperature'])
        p.setFloat('Min Velocity', d['min_velocity'])
        p.setFloat('Max Velocity', d['max_velocity'])
        
        o = s.createGeometryProceduralObject(name, p)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(material is not None):
            mat = self.load_material(material)
            if(mat is not None):
                o.setMaterial(mat)
        if(backface_material is not None):
            mat = self.load_material(backface_material)
            if(mat is not None):
                o.setBackfaceMaterial(mat)
        
        return o
    
    def subdivision(self, object_name, level=2, scheme=0, interpolation=2, crease=0.0, smooth_angle=math.radians(90.0), ):
        """Create subdivision object modifier extension.
        object_name     string
        level           int
        scheme          int     (0, "Catmull-Clark"), (1, "Loop")
        interpolation   int     (0, "None"), (1, "Edges"), (2, "Edges And Corners"), (3, "Sharp")
        crease          float
        smooth          float
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryModifierExtension('SubdivisionModifier')
        p = e.getExtensionData()
        
        p.setUInt('Subdivision Level', level)
        p.setUInt('Subdivision Scheme', scheme)
        p.setUInt('Interpolation', interpolation)
        p.setFloat('Crease', crease)
        p.setFloat('Smooth Angle', smooth_angle)
        
        o = s.getObject(object_name)
        o.applyGeometryModifierExtension(p)
        return o
    
    def scatter(self, object_name, scatter_object, inherit_objectid=False, density=None, seed=0, scale=None, rotation=None, lod=None, display_percent=10, display_max=1000, ):
        """Create scatter object modifier extension.
        object_name                 string
        scatter_object              string
        inherit_objectid            bool
        density                     (float, density_map or None) or None
        seed                        int
        scale                       ((float, float, float), scale_map or None, scale_variation (float, float, float)) or None
        rotation                    ((float, float, float), rotation_map or None, rotation_variation (float, float, float), rotation_direction int (0, "Polygon Normal"), (1, "World Z")) or None
        lod                         (bool, lod_min_distance float, lod_max_distance float, lod_max_distance_density float) or None
        display_percent             int
        display_max                 int
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryModifierExtension('MaxwellScatter')
        p = e.getExtensionData()
        
        p.setString('Object', scatter_object)
        p.setByte('Inherit ObjectID', inherit_objectid)
        if(density is not None):
            p.setFloat('Density', density[0])
            self.texture_data_to_mxparams(density[1], p.getByName('Density Map')[0])
        p.setUInt('Seed', seed)
        if(scale is not None):
            p.setFloat('Scale X', scale[0][0])
            p.setFloat('Scale Y', scale[0][1])
            p.setFloat('Scale Z', scale[0][2])
            self.texture_data_to_mxparams(scale[1], p.getByName('Scale Map')[0])
            p.setFloat('Scale X Variation', scale[2][0])
            p.setFloat('Scale Y Variation', scale[2][1])
            p.setFloat('Scale Z Variation', scale[2][2])
        if(rotation is not None):
            p.setFloat('Rotation X', rotation[0][0])
            p.setFloat('Rotation Y', rotation[0][1])
            p.setFloat('Rotation Z', rotation[0][2])
            self.texture_data_to_mxparams(rotation[1], p.getByName('Rotation Map')[0])
            p.setFloat('Rotation X Variation', rotation[2][0])
            p.setFloat('Rotation Y Variation', rotation[2][1])
            p.setFloat('Rotation Z Variation', rotation[2][2])
            p.setUInt('Direction Type', rotation[3])
        if(lod is not None):
            p.setByte('Enable LOD', lod[0])
            p.setFloat('LOD Min Distance', lod[1])
            p.setFloat('LOD Max Distance', lod[2])
            p.setFloat('LOD Max Distance Density', lod[3])
        p.setUInt('Display Percent', display_percent)
        p.setUInt('Display Max. Blades', display_max)
        
        o = s.getObject(object_name)
        o.applyGeometryModifierExtension(p)
        return o
    
    def write(self):
        """Write scene fo file."""
        log("saving scene..", 2)
        ok = self.mxs.writeMXS(self.path)
        log("done.", 2)
        return ok


if __name__ == "__main__":
    def test():
        path = "/Volumes/internal-2tb/teoplib/tmp/test.mxs"
        mxs = MXSWriter2(path)
        
        '''
        d = {'props': ("Camera", 1, 0.004, 0.032, 0.018000000000000002, 100.0, "CIRCULAR", 1.0471975803375244, 6, 24, 960, 540, 1.0, 0, ),
             'steps': ((0, [-2.8184449672698975, 4.383333206176758, 5.104832172393799], [-0.3223283290863037, 1.4271321296691895, 0.4408073425292969], [0.23018550872802734, 0.8729405403137207, -0.43010425567626953], 0.035, 11.0, 1), ),
             'active': True, 'lens_extra': None, 'response': None, 'region': None, 'custom_bokeh': None, 'cut_planes': None, 'shift_lens': None, }
        mxs.camera(**d)
        '''
        
        mxs.camera(('Camera', 1, 0.004, 0.032, 0.018000000000000002, 100.0, 'CIRCULAR', 1.0471975803375244, 6, 24, 960, 540, 1.0, 0, ),
                   ((0, (-2.8184449672698975, 4.383333206176758, 5.104832172393799), (-0.3223283290863037, 1.4271321296691895, 0.4408073425292969), (0.23018550872802734, 0.8729405403137207, -0.43010425567626953), 0.035, 11.0, 1),),
                   True, None, 'Maxwell', None, None, None, )
        
        # '''
        d = {'name': "Empty",
             'base': [[-0.5253749489784241, 0.25817662477493286, -0.44481390714645386], [0.9348477721214294, 0.20595940947532654, -0.28920647501945496], [-0.3544178903102875, 0.5898690819740295, -0.7255635261535645], [0.021157313138246536, 0.7807914018630981, 0.6244334578514099]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ], }
        mxs.empty(**d)
        
        d = {'name': "Cube",
             'base': [[1.2964980602264404, -0.39985325932502747, 0.7126237154006958], [-0.10209614783525467, -0.5031424164772034, 0.8581515550613403], [0.5799700021743774, 0.6707702279090881, 0.46227920055389404], [-0.8082149028778076, 0.5448989868164062, 0.22332444787025452]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'num_positions': 1,
             'vertices': [((-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), ), ],
             'normals': [((-0.5773491859436035, -0.5773491859436035, 0.5773491859436035), (-0.5773491859436035, 0.5773491859436035, 0.5773491859436035), (-0.5773491859436035, -0.5773491859436035, -0.5773491859436035), (-0.5773491859436035, 0.5773491859436035, -0.5773491859436035), (0.5773491859436035, -0.5773491859436035, 0.5773491859436035), (0.5773491859436035, 0.5773491859436035, 0.5773491859436035), (0.5773491859436035, -0.5773491859436035, -0.5773491859436035), (0.5773491859436035, 0.5773491859436035, -0.5773491859436035))],
             'triangles': [(3, 2, 0, 8, 8, 8), (7, 6, 2, 9, 9, 9), (5, 4, 6, 10, 10, 10), (1, 0, 4, 11, 11, 11), (2, 6, 4, 12, 12, 12), (7, 3, 1, 13, 13, 13), (1, 3, 0, 14, 14, 14), (3, 7, 2, 15, 15, 15), (7, 5, 6, 16, 16, 16), (5, 1, 4, 17, 17, 17), (0, 2, 4, 18, 18, 18), (5, 7, 1, 19, 19, 19), ],
             'triangle_normals': [((-1.0, 0.0, -0.0), (0.0, -2.9802322387695312e-08, -1.0), (1.0, -0.0, 0.0), (0.0, 2.9802322387695312e-08, 1.0), (0.0, -1.0, 2.9802322387695312e-08), (0.0, 1.0, -2.9802322387695312e-08), (-1.0, 0.0, 0.0), (-0.0, -2.9802322387695312e-08, -1.0), (1.0, -0.0, 0.0), (-0.0, 2.9802322387695312e-08, 1.0), (0.0, -1.0, 2.9802322387695312e-08), (0.0, 1.0, -2.9802322387695312e-08))],
             'uv_channels': [((0.33333340287208557, 0.6666666269302368, 0.0, 0.6666666865348816, 0.6666666567325592, 0.0, 0.6666667461395264, 0.3333333730697632, 0.0), (0.0, 0.6666665971279144, 0.0, 0.333333283662796, 0.6666666567325592, 0.0, 0.3333333432674408, 0.3333333730697632, 0.0), (0.0, 0.9999999105930613, 0.0, 0.3333333134651184, 1.0, 0.0, 0.33333340287208557, 0.6666667461395264, 0.0), (0.6666666865348816, 1.0, 0.0, 0.6666667461395264, 0.6666667461395264, 0.0, 0.33333346247673035, 0.6666666865348816, 0.0), (1.0, 0.6666667759418488, 0.0, 0.6666667461395264, 0.6666667759418488, 0.0, 0.6666667461395264, 0.9999999701976865, 0.0), (0.33333325386047363, 0.3333333134651184, 0.0, 0.333333283662796, 5.960464477539063e-08, 0.0, 4.967052547044659e-08, 5.960464477539063e-08, 0.0), (0.33333346247673035, 0.3333333730697632, 0.0, 0.33333340287208557, 0.6666666269302368, 0.0, 0.6666667461395264, 0.3333333730697632, 0.0), (3.973642037635727e-08, 0.3333333134651184, 0.0, 0.0, 0.6666665971279144, 0.0, 0.3333333432674408, 0.3333333730697632, 0.0), (1.291433733285885e-07, 0.6666666567325592, 0.0, 0.0, 0.9999999105930613, 0.0, 0.33333340287208557, 0.6666667461395264, 0.0), (0.33333340287208557, 0.9999999602635832, 0.0, 0.6666666865348816, 1.0, 0.0, 0.33333346247673035, 0.6666666865348816, 0.0), (1.0, 1.0, 0.0, 1.0, 0.6666667759418488, 0.0, 0.6666667461395264, 0.9999999701976865, 0.0), (0.0, 0.33333325386047363, 0.0, 0.33333325386047363, 0.3333333134651184, 0.0, 4.967052547044659e-08, 5.960464477539063e-08, 0.0),), ((0.0, 0.08858555555343628, 0.0, 0.12544512748718262, 0.626363068819046, 0.0, 0.5000001192092896, 1.0, 0.0), (0.5, 0.0, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0, 0.12544512748718262, 0.626363068819046, 0.0), (1.0, 0.08858531713485718, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0), (0.5000002384185791, 0.3003859519958496, 0.0, 0.5000001192092896, 1.0, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (0.12544512748718262, 0.626363068819046, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (0.5, 0.0, 0.0, 0.0, 0.08858555555343628, 0.0, 0.5000002384185791, 0.3003859519958496, 0.0), (0.5000002384185791, 0.3003859519958496, 0.0, 0.0, 0.08858555555343628, 0.0, 0.5000001192092896, 1.0, 0.0), (0.0, 0.08858555555343628, 0.0, 0.5, 0.0, 0.0, 0.12544512748718262, 0.626363068819046, 0.0), (0.5, 0.0, 0.0, 1.0, 0.08858531713485718, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0), (1.0, 0.08858531713485718, 0.0, 0.5000002384185791, 0.3003859519958496, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (0.5000001192092896, 1.0, 0.0, 0.12544512748718262, 0.626363068819046, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (1.0, 0.08858531713485718, 0.0, 0.5, 0.0, 0.0, 0.5000002384185791, 0.3003859519958496, 0.0)), ],
             # 'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'object_props': None,
             'num_materials': 2,
             'materials': [["/Volumes/internal-2tb/teoplib/tmp/test_objects/plastic.mxm", True, ], [None, True]],
             'triangle_materials': [(0, 0), (1, 1), (2, 0), (3, 1), (4, 1), (5, 0), (6, 0), (7, 1), (8, 0), (9, 1), (10, 1), (11, 0)],
             'backface_material': None, }
        mxs.mesh(**d)
        
        d = {'name': "Cube.001",
             'base': [[-0.8372452855110168, 1.1259527206420898, -0.3333452343940735], [-0.021821729838848114, -0.10754019767045975, 0.183418869972229], [0.12396112829446793, 0.14336848258972168, 0.098806232213974], [-0.17274552583694458, 0.11646515130996704, 0.04773273319005966]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'num_positions': 1,
             'vertices': [((-1.0, -1.0, 1.0), (-1.0, 1.0, 1.0), (-1.0, -1.0, -1.0), (-1.0, 1.0, -1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), ), ],
             'normals': [((-0.5773491859436035, -0.5773491859436035, 0.5773491859436035), (-0.5773491859436035, 0.5773491859436035, 0.5773491859436035), (-0.5773491859436035, -0.5773491859436035, -0.5773491859436035), (-0.5773491859436035, 0.5773491859436035, -0.5773491859436035), (0.5773491859436035, -0.5773491859436035, 0.5773491859436035), (0.5773491859436035, 0.5773491859436035, 0.5773491859436035), (0.5773491859436035, -0.5773491859436035, -0.5773491859436035), (0.5773491859436035, 0.5773491859436035, -0.5773491859436035)), ],
             'triangles': [(3, 2, 0, 8, 8, 8), (7, 6, 2, 9, 9, 9), (5, 4, 6, 10, 10, 10), (1, 0, 4, 11, 11, 11), (2, 6, 4, 12, 12, 12), (7, 3, 1, 13, 13, 13), (1, 3, 0, 14, 14, 14), (3, 7, 2, 15, 15, 15), (7, 5, 6, 16, 16, 16), (5, 1, 4, 17, 17, 17), (0, 2, 4, 18, 18, 18), (5, 7, 1, 19, 19, 19), ],
             'triangle_normals': [((-1.0, 0.0, -0.0), (0.0, -2.9802322387695312e-08, -1.0), (1.0, -0.0, 0.0), (0.0, 2.9802322387695312e-08, 1.0), (0.0, -1.0, 2.9802322387695312e-08), (0.0, 1.0, -2.9802322387695312e-08), (-1.0, 0.0, 0.0), (-0.0, -2.9802322387695312e-08, -1.0), (1.0, -0.0, 0.0), (-0.0, 2.9802322387695312e-08, 1.0), (0.0, -1.0, 2.9802322387695312e-08), (0.0, 1.0, -2.9802322387695312e-08), ), ],
             'uv_channels': [],
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'num_materials': 1,
             'materials': [["/Volumes/internal-2tb/teoplib/tmp/test_objects/clay.mxm", True]],
             'triangle_materials': None,
             'backface_material': None, }
        mxs.mesh(**d)
        
        d = {'name': "Cube.002",
             'instanced_name': "Cube.001",
             'base': [[-0.4790751338005066, 1.5562844276428223, -0.057391971349716187], [-0.021821729838848114, -0.10754019767045975, 0.183418869972229], [0.12396112829446793, 0.14336848258972168, 0.098806232213974], [-0.17274552583694458, 0.11646515130996704, 0.04773273319005966]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'material': None,
             'backface_material': None, }
        mxs.instance(**d)
        
        d = {'name': "Cube.003",
             'instanced_name': "Cube.001",
             'base': [[-0.09456577897071838, 1.97418212890625, 0.23240837454795837], [-0.021821729838848114, -0.10754019767045975, 0.183418869972229], [0.12396112829446793, 0.14336848258972168, 0.098806232213974], [-0.17274552583694458, 0.11646515130996704, 0.04773273319005966]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'material': None,
             'backface_material': None, }
        mxs.instance(**d)
        
        d = {'name': "Icosphere",
             'base': [[0.058789610862731934, -1.2491323947906494, 2.2190544605255127], [0.18772241473197937, 0.08105795830488205, -0.06646223366260529], [-0.03949476033449173, 0.1809723824262619, 0.10916268825531006], [0.09709678590297699, -0.08310196548700333, 0.17289765179157257]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'num_positions': 1,
             'vertices': [((0.0, -1.0, 4.371138828673793e-08), (0.7235999703407288, -0.4472149610519409, 0.5257200002670288), (-0.27638500928878784, -0.4472149610519409, 0.8506399989128113), (-0.8944249749183655, -0.4472149908542633, 1.9548387797385658e-08), (-0.27638500928878784, -0.4472150206565857, -0.8506399989128113), (0.7235999703407288, -0.4472150206565857, -0.5257200002670288), (0.27638500928878784, 0.4472150206565857, 0.8506399989128113), (-0.7235999703407288, 0.4472150206565857, 0.5257200002670288), (-0.7235999703407288, 0.4472149610519409, -0.5257200002670288), (0.27638500928878784, 0.4472149610519409, -0.8506399989128113), (0.8944249749183655, 0.4472149908542633, -1.9548387797385658e-08), (0.0, 1.0, -4.371138828673793e-08), ), ],
             'normals': [((0.0, -1.0, 0.0), (0.7235938310623169, -0.44718772172927856, 0.5257118344306946), (-0.2763756215572357, -0.44718772172927856, 0.8506424427032471), (-0.8944059610366821, -0.44718772172927856, 0.0), (-0.2763756215572357, -0.44718772172927856, -0.8506424427032471), (0.7235938310623169, -0.44718772172927856, -0.5257118344306946), (0.2763756215572357, 0.44718772172927856, 0.8506424427032471), (-0.7235938310623169, 0.44718772172927856, 0.5257118344306946), (-0.7235938310623169, 0.44718772172927856, -0.5257118344306946), (0.2763756215572357, 0.44718772172927856, -0.8506424427032471), (0.8944059610366821, 0.44718772172927856, 0.0), (0.0, 1.0, 0.0), ), ],
             'triangles': [(0, 1, 2, 0, 1, 2), (1, 0, 5, 1, 0, 5), (0, 2, 3, 0, 2, 3), (0, 3, 4, 0, 3, 4), (0, 4, 5, 0, 4, 5), (1, 5, 10, 1, 5, 10), (2, 1, 6, 2, 1, 6), (3, 2, 7, 3, 2, 7), (4, 3, 8, 4, 3, 8), (5, 4, 9, 5, 4, 9), (1, 10, 6, 1, 10, 6), (2, 6, 7, 2, 6, 7), (3, 7, 8, 3, 7, 8), (4, 8, 9, 4, 8, 9), (5, 9, 10, 5, 9, 10), (6, 10, 11, 6, 10, 11), (7, 6, 11, 7, 6, 11), (8, 7, 11, 8, 7, 11), (9, 8, 11, 9, 8, 11), (10, 9, 11, 10, 9, 11)],
             'triangle_normals': [((0.18759654462337494, -0.7946510314941406, 0.5773536562919617), (0.6070646047592163, -0.7946524024009705, 3.1127502353456293e-08), (-0.4911220669746399, -0.7946521639823914, 0.35682904720306396), (-0.4911220967769623, -0.7946522235870361, -0.3568290174007416), (0.18759652972221375, -0.7946510910987854, -0.5773535966873169), (0.9822461009025574, -0.18759679794311523, 1.0634596314673672e-08), (0.3035355508327484, -0.1875891238451004, 0.9341714978218079), (-0.7946491837501526, -0.1875869631767273, 0.5773593783378601), (-0.7946492433547974, -0.18758699297904968, -0.5773593783378601), (0.3035355508327484, -0.1875891536474228, -0.9341714978218079), (0.7946492433547974, 0.18758699297904968, 0.5773593783378601), (-0.3035355508327484, 0.1875891536474228, 0.9341714978218079), (-0.9822461009025574, 0.18759679794311523, -1.0634596314673672e-08), (-0.3035355508327484, 0.1875891238451004, -0.9341714978218079), (0.7946491837501526, 0.1875869631767273, -0.5773593783378601), (0.4911220967769623, 0.7946522235870361, 0.3568290174007416), (-0.18759652972221375, 0.7946510910987854, 0.5773535966873169), (-0.6070646047592163, 0.7946524024009705, -4.5047720220736664e-08), (-0.18759654462337494, 0.7946510314941406, -0.5773536562919617), (0.4911220669746399, 0.7946521639823914, -0.35682904720306396), ), ],
             'uv_channels': None,
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'num_materials': 0,
             'materials': None,
             'triangle_materials': None,
             'backface_material': None, }
        mxs.mesh(**d)
        
        d = {'name': "Hair",
             'extension': "MaxwellHair",
             'base': [[0.0, 0.0, -0.0], [1.0, 0.0, -0.0], [0.0, 1.0, -0.0], [-0.0, -0.0, 1.0]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'root_radius': 0.01,
             'tip_radius': 0.01,
             'data': {'HAIR_MAJOR_VER': [1, 0, 0, 0],
                      'HAIR_FLAG_ROOT_UVS': [0],
                      'HAIR_POINTS': [-0.08098446577787399, -8.230035319911622e-09, -0.18828126788139343, -0.08161671459674835, 0.006709327921271324, -0.18981792032718658, -0.08219374716281891, 0.013758555985987186,
                                      -0.1911616176366806, -0.0827208012342453, 0.021131295710802078, -0.19232967495918274, -0.08320312201976776, 0.028811177238821983, -0.19333940744400024, -0.08364595472812653,
                                      0.03678181767463684, -0.19420813024044037, -0.08405454456806183, 0.045026831328868866, -0.19495317339897156, -0.0844341292977333, 0.05352985858917236, -0.19559183716773987,
                                      -0.08478996157646179, 0.0622745156288147, -0.19614143669605255, -0.08512728661298752, 0.07124441117048264, -0.19661930203437805, -0.08545134216547012, 0.08042317628860474,
                                      -0.19704273343086243, -0.08576737344264984, 0.08979444950819016, -0.19742906093597412, -0.0860806256532669, 0.09934180229902267, -0.1977955847978592, -0.08639635145664215,
                                      0.10904893279075623, -0.19815964996814728, -0.08671978861093521, 0.1188993975520134, -0.19853852689266205, -0.08705617487430573, 0.12887683510780334, -0.19894957542419434,
                                      0.18669630587100983, 1.2760666134870036e-10, 0.0029192999936640263, 0.1924477517604828, 0.20498400926589966, 0.015546927228569984, 0.16896528005599976, 0.48171451687812805,
                                      -0.030823545530438423, 0.12152867019176483, 0.675149142742157, -0.12342479825019836, 0.03405354917049408, 0.7854002714157104, -0.31963273882865906, -0.05324919521808624,
                                      0.7664400339126587, -0.5339993834495544, -0.14240793883800507, 0.7470872402191162, -0.7616661190986633, -0.20505712926387787, 0.6742979884147644, -0.9932375550270081,
                                      -0.22614668309688568, 0.5240526795387268, -1.2255773544311523, -0.24538792669773102, 0.5746803879737854, -1.3054486513137817, -0.2599891424179077, 0.8179532885551453,
                                      -1.1948378086090088, -0.2675756812095642, 1.0684677362442017, -1.095952033996582, -0.2970235347747803, 1.2900983095169067, -1.0531044006347656, -0.4159618616104126,
                                      1.5084326267242432, -1.1486798524856567, -0.4360794425010681, 1.6717115640640259, -1.1217832565307617, -0.3102194666862488, 1.7080762386322021, -0.9249669313430786,
                                      0.11021610349416733, -1.5439215461654499e-09, -0.03532080724835396, 0.11578115820884705, 0.2092379927635193, -0.02174588106572628, 0.08565031737089157, 0.4760940968990326,
                                      -0.08518961817026138, 0.024907179176807404, 0.6467247009277344, -0.21202613413333893, -0.06521051377058029, 0.7219012379646301, -0.42971500754356384, -0.13939443230628967,
                                      0.6633701920509338, -0.6412039399147034, -0.18716225028038025, 0.5538044571876526, -0.8476521968841553, -0.2162693440914154, 0.412445068359375, -1.058916687965393,
                                      -0.24210676550865173, 0.27128562331199646, -1.29081130027771, -0.2789740264415741, 0.33750325441360474, -1.3906707763671875, -0.31049978733062744, 0.585605263710022,
                                      -1.3075333833694458, -0.31732693314552307, 0.8292117118835449, -1.205169439315796, -0.32928213477134705, 1.045772671699524, -1.1278631687164307, -0.3991813361644745,
                                      1.2537394762039185, -1.143176794052124, -0.47000476717948914, 1.51251220703125, -1.1530373096466064, -0.5026390552520752, 1.7350858449935913, -1.131240963935852,
                                      0.14845618605613708, 1.799134841107275e-09, 0.041159406304359436, 0.1540692150592804, 0.20510773360729218, 0.05359848216176033, 0.12857572734355927, 0.47897017002105713,
                                      0.003709168639034033, 0.07743366807699203, 0.6673396825790405, -0.09538230299949646, -0.011915743350982666, 0.7733772993087769, -0.2945317327976227, -0.09824696183204651,
                                      0.7524213194847107, -0.5058798789978027, -0.18836745619773865, 0.7316505312919617, -0.7338322997093201, -0.2527914047241211, 0.6636014580726624, -0.9631161689758301,
                                      -0.2783769369125366, 0.5201365351676941, -1.2011133432388306, -0.29782241582870483, 0.5676276087760925, -1.2856444120407104, -0.3090299367904663, 0.8042133450508118,
                                      -1.1723966598510742, -0.31410589814186096, 1.0559749603271484, -1.0676623582839966, -0.338509738445282, 1.2725093364715576, -1.0191138982772827, -0.45558837056159973,
                                      1.495270013809204, -1.1100883483886719, -0.4824630320072174, 1.661075472831726, -1.092484474182129, -0.3598640263080597, 1.6973611116409302, -0.9003852009773254,
                                      -0.04274435713887215, 1.799134841107275e-09, 0.041159406304359436, -0.04116692394018173, 0.22080476582050323, 0.04782946780323982, -0.08509949594736099, 0.47232764959335327,
                                      -0.04565710574388504, -0.16433177888393402, 0.5957497954368591, -0.2163965255022049, -0.2591060996055603, 0.6253291368484497, -0.4542386829853058, -0.3253854513168335,
                                      0.5362178683280945, -0.6696209907531738, -0.3521300256252289, 0.3904913663864136, -0.8486403822898865, -0.3785335123538971, 0.23515070974826813, -1.0731079578399658,
                                      -0.415400892496109, 0.14213548600673676, -1.3049039840698242, -0.46083864569664, 0.26801860332489014, -1.3760498762130737, -0.49102020263671875, 0.5394375920295715,
                                      -1.2767506837844849, -0.4904232919216156, 0.7559590935707092, -1.1783846616744995, -0.5104337334632874, 1.000835657119751, -1.1028550863265991, -0.563571572303772,
                                      1.2033684253692627, -1.0986595153808594, -0.6362817287445068, 1.4848405122756958, -1.1042433977127075, -0.6612340807914734, 1.691002368927002, -1.074325442314148],
                      'HAIR_NORMALS': [1.0],
                      'HAIR_GUIDES_POINT_COUNT': [16],
                      'HAIR_MINOR_VER': [0, 0, 0, 0],
                      'HAIR_GUIDES_COUNT': [5], },
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'display_percent': 10,
             'display_max': 1000,
             'material': None,
             'backface_material': None, }
        mxs.hair(**d)
        
        d = {'object_name': "Icosphere",
             'level': 2,
             'scheme': 1,
             'interpolation': 2,
             'crease': 0.0,
             'smooth_angle': math.radians(90.0), }
        mxs.subdivision(**d)
        
        d = {'object_name': "Cube",
             'scatter_object': "Icosphere",
             'inherit_objectid': True,
             'density': (100.0, None),
             'seed': 0,
             'scale': ((1.0, 1.0, 1.0), None, (20.0, 20.0, 20.0), ),
             'rotation': ((0.0, 0.0, 0.0), None, (10.0, 10.0, 10.0), 0),
             'lod': (False, 10.0, 50.0, 10.0),
             'display_percent': 10,
             'display_max': 1000, }
        mxs.scatter(**d)
        
        d = {"name": "Grass",
             "object_name": "Icosphere",
             'properties': {
                 "density": 3000, "density_map": {"path": ["/Volumes/internal-2tb/teoplib/tmp/map.tif"], "alpha_only": False, "tile_method_units": 0, "saturation": 0.0, "interpolation": False, "use_override_map": False, "rgb_clamp": [0.0, 255.0], "repeat": [1.0, 1.0], "brightness": 0.0, "invert": False, "rotation": 0.0, "offset": [0.0, 0.0], "hue": 0.0, "channel": 0, "contrast": 0.0, "mirror": [False, False], "tile_method_type": [True, True], "type": "IMAGE"},
                 "length": 10.0, "length_map": {"path": ["/Volumes/internal-2tb/teoplib/tmp/map.tif"], "alpha_only": False, "tile_method_units": 0, "saturation": 0.0, "interpolation": False, "use_override_map": False, "rgb_clamp": [0.0, 255.0], "repeat": [1.0, 1.0], "brightness": 0.0, "invert": False, "rotation": 0.0, "offset": [0.0, 0.0], "hue": 0.0, "channel": 0, "contrast": 0.0, "mirror": [False, False], "tile_method_type": [True, True], "type": "IMAGE"}, "length_variation": 20.0,
                 "root_width": 5.0,
                 "tip_width": 1.0,
                 "direction_type": 0,
                 "initial_angle": 79.99999767274336, "initial_angle_map": None, "initial_angle_variation": 25.0,
                 "start_bend": 40.0, "start_bend_map": None, "start_bend_variation": 25.0,
                 "bend_radius": 10.0, "bend_radius_map": None, "bend_radius_variation": 25.0,
                 "bend_angle": 79.99999767274336, "bend_angle_map": None, "bend_angle_variation": 25.0,
                 "cut_off": 100.0, "cut_off_map": None, "cut_off_variation": 0.0,
                 "points_per_blade": 8,
                 "primitive_type": 1,
                 "seed": 0,
                 "lod": False, "lod_max_distance": 50.0, "lod_max_distance_density": 10.0, "lod_min_distance": 10.0,
                 "display_max_blades": 1000, "display_percent": 10, },
             "material": ("/Volumes/internal-2tb/teoplib/tmp/test_objects/plastic.mxm", False),
             "backface_material": None, }
        mxs.grass(**d)
        
        d = {"name": "Particles",
             'properties': {"axis_system": 0,
                            "extra_create_np_pp": 0, "extra_deformation": 0.0, "extra_dispersion": 0.0,
                            "filename": "/Volumes/internal-2tb/teoplib/tmp/Particle_Test_01.bin",
                            "fps": 24.0, "frame_number": 0,
                            "load_age": 0, "load_density": 0, "load_force": 0, "load_id": 0, "load_isolation_time": 0, "load_mass": 0, "load_neighbors_num": 0, "load_normal": 0,
                            "load_particles": 100.0, "load_pressure": 0, "load_temperature": 0, "load_uv": 0, "load_viscosity": 0, "load_vorticity": 0,
                            "max_age": 1.0, "max_density": 1.0, "max_force": 1.0, "max_isolation_time": 1.0, "max_mass": 1.0, "max_nneighbors": 1,
                            "max_pressure": 1.0, "max_temperature": 1.0, "max_velocity": 1.0, "max_viscosity": 1.0, "max_vorticity": 1.0,
                            "min_age": 0.0, "min_density": 0.0, "min_force": 0.0, "min_isolation_time": 0.0, "min_mass": 0.0, "min_nneighbors": 0,
                            "min_pressure": 0.0, "min_temperature": 0.0, "min_velocity": 0.0, "min_viscosity": 0.0, "min_vorticity": 0.0,
                            "motion_blur_multiplier": 1.0, "radius_multiplier": 1.0, "shutter_speed": 125.0, },
             'base': [[0.0, 0.0, -0.0], [1.0, 0.0, -0.0], [0.0, 1.0, -0.0], [-0.0, -0.0, 1.0]],
             'pivot': [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
             'object_props': [False, 100, (255, 255, 255), False, False, False, False, False, ],
             'material': None, 'backface_material': None, }
        mxs.particles(**d)
        
        tree = [("Empty", None), ("Cube", "Empty"), ("Cube.001", "Empty"), ("Cube.002", "Empty"), ("Cube.003", "Empty"), ("Icosphere", "Cube"), ("ParticleSystem", None), ]
        mxs.hierarchy(tree)
        # '''
        
        d = {'name': "Cube",
             'base': ((1.2964980602264404, -0.3998532295227051, 0.7126235961914062), (-0.10209611058235168, -0.5031424164772034, 0.8581515550613403), (0.5799700021743774, 0.6707702279090881, 0.46227923035621643), (-0.8082148432731628, 0.544899046421051, 0.2233244776725769)),
             'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
             'num_positions': 1,
             'vertices': [[(-1.0, -0.9999999403953552, 1.0), (-1.0, 1.0, 0.9999999403953552), (-1.0, -1.0, -0.9999999403953552), (-1.0, 0.9999999403953552, -1.0), (1.0, -0.9999999403953552, 1.0), (1.0, 1.0, 0.9999999403953552), (1.0, -1.0, -0.9999999403953552), (1.0, 0.9999999403953552, -1.0)]],
             'normals': [[(-0.5773491859436035, -0.5773491859436035, 0.5773491859436035), (-0.5773491859436035, 0.5773491859436035, 0.5773491859436035), (-0.5773491859436035, -0.5773491859436035, -0.5773491859436035), (-0.5773491859436035, 0.5773491859436035, -0.5773491859436035), (0.5773491859436035, -0.5773491859436035, 0.5773491859436035), (0.5773491859436035, 0.5773491859436035, 0.5773491859436035), (0.5773491859436035, -0.5773491859436035, -0.5773491859436035), (0.5773491859436035, 0.5773491859436035, -0.5773491859436035)]],
             'triangles': [(3, 2, 0, 8, 8, 8), (7, 6, 2, 9, 9, 9), (5, 4, 6, 10, 10, 10), (1, 0, 4, 11, 11, 11), (2, 6, 4, 12, 12, 12), (7, 3, 1, 13, 13, 13), (1, 3, 0, 14, 14, 14), (3, 7, 2, 15, 15, 15), (7, 5, 6, 16, 16, 16), (5, 1, 4, 17, 17, 17), (0, 2, 4, 18, 18, 18), (5, 7, 1, 19, 19, 19)],
             'triangle_normals': [[(-1.0, 0.0, -0.0), (0.0, -2.9802322387695312e-08, -1.0), (1.0, -0.0, 0.0), (0.0, 2.9802322387695312e-08, 1.0), (0.0, -1.0, 2.9802322387695312e-08), (0.0, 1.0, -2.9802322387695312e-08), (-1.0, 0.0, 0.0), (-0.0, -2.9802322387695312e-08, -1.0), (1.0, -0.0, 0.0), (-0.0, 2.9802322387695312e-08, 1.0), (0.0, -1.0, 2.9802322387695312e-08), (0.0, 1.0, -2.9802322387695312e-08)]],
             'uv_channels': [[(0.0, 0.08858555555343628, 0.0, 0.12544512748718262, 0.626363068819046, 0.0, 0.5000001192092896, 1.0, 0.0), (0.5, 0.0, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0, 0.12544512748718262, 0.626363068819046, 0.0), (1.0, 0.08858531713485718, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0), (0.5000002384185791, 0.3003859519958496, 0.0, 0.5000001192092896, 1.0, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (0.12544512748718262, 0.626363068819046, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (0.5, 0.0, 0.0, 0.0, 0.08858555555343628, 0.0, 0.5000002384185791, 0.3003859519958496, 0.0), (0.5000002384185791, 0.3003859519958496, 0.0, 0.0, 0.08858555555343628, 0.0, 0.5000001192092896, 1.0, 0.0), (0.0, 0.08858555555343628, 0.0, 0.5, 0.0, 0.0, 0.12544512748718262, 0.626363068819046, 0.0), (0.5, 0.0, 0.0, 1.0, 0.08858531713485718, 0.0, 0.49999988079071045, 0.4283735156059265, 0.0), (1.0, 0.08858531713485718, 0.0, 0.5000002384185791, 0.3003859519958496, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (0.5000001192092896, 1.0, 0.0, 0.12544512748718262, 0.626363068819046, 0.0, 0.8745548725128174, 0.6263629496097565, 0.0), (1.0, 0.08858531713485718, 0.0, 0.5, 0.0, 0.0, 0.5000002384185791, 0.3003859519958496, 0.0)]],
             'object_props': (False, 100.0, (255, 255, 255), False, False, False, False, False),
             'num_materials': 2,
             'materials': [('/Volumes/internal-2tb/teoplib/tmp/test_objects/plastic.mxm', True), ('/Volumes/internal-2tb/teoplib/tmp/test_objects/clay.mxm', True)],
             'triangle_materials': [(0, 0), (1, 1), (2, 0), (3, 1), (4, 1), (5, 0), (6, 0), (7, 1), (8, 0), (9, 1), (10, 1), (11, 0)],
             'backface_material': ('', True), }
        mxs.mesh(**d)
        
        d = {'name': "Sphere",
             'base': ((-0.3084367513656616, 1.3997334241867065, 0.5207718014717102), (-0.4606761932373047, -0.004029299132525921, -0.49143877625465393), (0.46539798378944397, 0.21284303069114685, -0.4380106031894684), (0.15790167450904846, -0.6390871405601501, -0.14277763664722443)),
             'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
             'num_positions': 1,
             'vertices': [[(-0.3826834559440613, 0.9238795042037964, -4.038405521100685e-08), (-0.7071067690849304, 0.7071067690849304, -3.0908619663705394e-08), (-0.9238795042037964, 0.3826834261417389, -1.672762373061687e-08), (-1.0, -4.371138828673793e-08, 1.910685465164705e-15), (-0.9238795042037964, -0.38268351554870605, 1.672762728333055e-08), (-0.7071067690849304, -0.7071067690849304, 3.0908619663705394e-08), (-0.38268348574638367, -0.9238795042037964, 4.038405521100685e-08), (-0.3535534143447876, 0.9238795042037964, -0.1464466154575348), (-0.6532814502716064, 0.7071067690849304, -0.27059802412986755), (-0.8535533547401428, 0.3826833963394165, -0.3535533845424652), (-0.9238795042037964, -6.043900668828428e-08, -0.3826833963394165), (-0.8535533547401428, -0.38268354535102844, -0.35355332493782043), (-0.6532814502716064, -0.7071067690849304, -0.2705979645252228), (-0.3535534143447876, -0.9238795042037964, -0.14644654095172882), (-0.27059808373451233, 0.9238795042037964, -0.27059799432754517), (-0.4999999701976776, 0.7071067690849304, -0.49999991059303284), (-0.6532814502716064, 0.3826833963394165, -0.6532813906669617), (-0.7071067690849304, -7.462000439772964e-08, -0.7071067094802856), (-0.6532814502716064, -0.38268354535102844, -0.6532813906669617), (-0.4999999701976776, -0.7071067690849304, -0.49999985098838806), (-0.27059805393218994, -0.9238795042037964, -0.2705979645252228), (-0.14644668996334076, 0.9238795042037964, -0.35355329513549805), (-0.27059805393218994, 0.7071067690849304, -0.6532813310623169), (-0.3535533547401428, 0.3826833963394165, -0.8535532355308533), (-0.3826833963394165, -8.40954399450311e-08, -0.9238793849945068), (-0.3535533547401428, -0.38268354535102844, -0.8535532355308533), (-0.27059805393218994, -0.7071067690849304, -0.6532812118530273), (-0.14644663035869598, -0.9238795042037964, -0.35355326533317566), (-1.3070317095298378e-07, 0.9238795042037964, -0.38268330693244934), (-7.109852617759316e-08, 0.7071067094802856, -0.7071065902709961), (-1.1493881402202533e-08, 0.3826833963394165, -0.9238793253898621), (-1.1493881402202533e-08, -8.742276236262114e-08, -0.9999997615814209), (-1.1493881402202533e-08, -0.38268354535102844, -0.9238793253898621), (-7.109852617759316e-08, -0.7071068286895752, -0.7071064710617065), (-5.61973649837455e-08, -0.9238795042037964, -0.38268324732780457), (-2.0877942574770714e-07, 1.0, 9.579050441743675e-08), (0.14644642174243927, 0.9238795042037964, -0.35355326533317566), (0.270597904920578, 0.7071067690849304, -0.6532812118530273), (0.35355332493782043, 0.3826833963394165, -0.8535531163215637), (0.3826833665370941, -8.409543283960375e-08, -0.9238792061805725), (0.35355332493782043, -0.38268354535102844, -0.8535531163215637), (0.270597904920578, -0.7071067690849304, -0.6532810926437378), (0.14644649624824524, -0.9238795042037964, -0.3535531759262085), (0.27059781551361084, 0.9238795042037964, -0.2705979347229004), (0.4999997615814209, 0.7071067690849304, -0.49999967217445374), (0.6532813310623169, 0.3826833963394165, -0.6532811522483826), (0.7071065902709961, -7.461999018687493e-08, -0.7071064114570618), (0.6532813310623169, -0.38268354535102844, -0.6532811522483826), (0.4999997615814209, -0.7071067690849304, -0.49999961256980896), (0.2705978751182556, -0.9238795042037964, -0.27059781551361084), (0.3535531163215637, 0.9238795042037964, -0.14644652605056763), (0.6532811522483826, 0.7071067690849304, -0.27059775590896606), (0.8535531163215637, 0.3826833963394165, -0.35355308651924133), (0.9238792061805725, -6.043899247742957e-08, -0.38268303871154785), (0.8535531163215637, -0.38268354535102844, -0.35355302691459656), (0.6532811522483826, -0.7071067690849304, -0.2705976963043213), (0.3535531461238861, -0.9238795042037964, -0.1464463621377945), (0.382683128118515, 0.9238795042037964, 3.230070078075187e-08), (0.707106351852417, 0.7071067690849304, 2.354912425062139e-07), (0.9238791465759277, 0.3826834261417389, 2.7947456260335457e-07), (0.9999995231628418, -4.3711374075883214e-08, 3.260045104980236e-07), (0.9238791465759277, -0.38268351554870605, 3.12929813617302e-07), (0.707106351852417, -0.7071067690849304, 2.973084747281973e-07), (0.382683128118515, -0.9238795042037964, 2.0247577481313783e-07), (0.35355305671691895, 0.9238795042037964, 0.1464465856552124), (0.6532809734344482, 0.7071067690849304, 0.2705981731414795), (0.8535528779029846, 0.3826834559440613, 0.35355356335639954), (0.9238789677619934, -2.6983755674336862e-08, 0.3826836347579956), (0.8535528779029846, -0.38268348574638367, 0.3535536229610443), (0.6532809734344482, -0.7071067690849304, 0.27059823274612427), (0.35355302691459656, -0.9238795042037964, 0.14644674956798553), (0.2705977261066437, 0.9238795042037964, 0.2705979645252228), (0.49999940395355225, 0.7071067690849304, 0.4999999701976776), (0.6532808542251587, 0.3826834559440613, 0.6532815098762512), (0.7071061134338379, -1.2802768623032534e-08, 0.7071068286895752), (0.6532808542251587, -0.38268348574638367, 0.6532815098762512), (0.49999940395355225, -0.7071067690849304, 0.5000000596046448), (0.2705976665019989, -0.9238795042037964, 0.27059808373451233), (0.14644630253314972, 0.9238795042037964, 0.35355323553085327), (0.2705974876880646, 0.7071067690849304, 0.6532812714576721), (0.35355278849601746, 0.3826834559440613, 0.8535532355308533), (0.38268277049064636, -3.3273366284447548e-09, 0.9238793849945068), (0.35355278849601746, -0.38268348574638367, 0.8535532355308533), (0.2705974876880646, -0.7071067690849304, 0.6532813906669617), (0.14644622802734375, -0.9238795042037964, 0.35355332493782043), (-2.4991246050376503e-07, 0.9238795042037964, 0.3826832175254822), (-4.883310111836181e-07, 0.7071068286895752, 0.7071064114570618), (-5.181333335713134e-07, 0.3826834559440613, 0.9238792061805725), (-6.075403007343994e-07, -1.4210854715202004e-14, 0.9999996423721313), (-5.181333335713134e-07, -0.38268348574638367, 0.9238792061805725), (-4.883310111836181e-07, -0.7071067094802856, 0.7071065306663513), (-3.3931942766685097e-07, -0.9238795042037964, 0.38268327713012695), (-0.14644677937030792, 0.9238795042037964, 0.3535531461238861), (-0.2705983817577362, 0.7071067690849304, 0.6532809734344482), (-0.35355377197265625, 0.3826834559440613, 0.8535529375076294), (-0.3826838731765747, -3.3273543920131488e-09, 0.9238789677619934), (-0.35355377197265625, -0.38268348574638367, 0.8535529375076294), (-0.2705983817577362, -0.7071067690849304, 0.6532810926437378), (-0.14644686877727509, -0.9238795042037964, 0.3535531759262085), (-1.5099580252808664e-07, -1.0, 4.371138828673793e-08), (-0.2705981135368347, 0.9238795042037964, 0.27059781551361084), (-0.5000001192092896, 0.7071067690849304, 0.49999943375587463), (-0.6532816886901855, 0.3826834559440613, 0.6532809138298035), (-0.7071070075035095, -1.2802800597455644e-08, 0.7071060538291931), (-0.6532816886901855, -0.38268348574638367, 0.6532809138298035), (-0.5000001192092896, -0.7071067690849304, 0.4999994933605194), (-0.2705982029438019, -0.9238795042037964, 0.27059781551361084), (-0.3535533845424652, 0.9238795042037964, 0.14644639194011688), (-0.6532813906669617, 0.7071067690849304, 0.2705974876880646), (-0.853553295135498, 0.3826834559440613, 0.35355275869369507), (-0.9238795042037964, -2.698379653054417e-08, 0.3826827108860016), (-0.853553295135498, -0.38268348574638367, 0.35355281829833984), (-0.6532813906669617, -0.7071067690849304, 0.27059754729270935), (-0.3535534143447876, -0.9238795042037964, 0.14644639194011688)]],
             'normals': [[(-0.4030884802341461, 0.9151585698127747, 0.0), (-0.7188329696655273, 0.69515061378479, 0.0), (-0.9272744059562683, 0.3743400275707245, 0.0), (-1.0, 0.0, 0.0), (-0.9272744059562683, -0.3743400275707245, 0.0), (-0.7188329696655273, -0.69515061378479, 0.0), (-0.4030884802341461, -0.9151585698127747, 0.0), (-0.3723868429660797, 0.9151585698127747, -0.15424054861068726), (-0.6641132831573486, 0.69515061378479, -0.27509385347366333), (-0.8566851019859314, 0.3743400275707245, -0.35483869910240173), (-0.9238563179969788, 0.0, -0.382671594619751), (-0.8566851019859314, -0.3743400275707245, -0.35483869910240173), (-0.6641132831573486, -0.69515061378479, -0.27509385347366333), (-0.3723868429660797, -0.9151585698127747, -0.15424054861068726), (-0.2850123643875122, 0.9151585698127747, -0.2850123643875122), (-0.5082857608795166, 0.69515061378479, -0.5082857608795166), (-0.6556596755981445, 0.3743400275707245, -0.6556596755981445), (-0.7070833444595337, 0.0, -0.7070833444595337), (-0.6556596755981445, -0.3743400275707245, -0.6556596755981445), (-0.5082857608795166, -0.69515061378479, -0.5082857608795166), (-0.2850123643875122, -0.9151585698127747, -0.2850123643875122), (-0.15424054861068726, 0.9151585698127747, -0.3723868429660797), (-0.27509385347366333, 0.69515061378479, -0.6641132831573486), (-0.35483869910240173, 0.3743400275707245, -0.8566851019859314), (-0.382671594619751, 0.0, -0.9238563179969788), (-0.35483869910240173, -0.3743400275707245, -0.8566851019859314), (-0.27509385347366333, -0.69515061378479, -0.6641132831573486), (-0.15424054861068726, -0.9151585698127747, -0.3723868429660797), (0.0, 0.9151585698127747, -0.4030884802341461), (0.0, 0.69515061378479, -0.7188329696655273), (0.0, 0.3743400275707245, -0.9272744059562683), (0.0, 0.0, -1.0), (0.0, -0.3743400275707245, -0.9272744059562683), (0.0, -0.69515061378479, -0.7188329696655273), (0.0, -0.9151585698127747, -0.4030884802341461), (0.0, 1.0, 0.0), (0.15424054861068726, 0.9151585698127747, -0.3723868429660797), (0.27509385347366333, 0.69515061378479, -0.6641132831573486), (0.35483869910240173, 0.3743400275707245, -0.8566851019859314), (0.382671594619751, 0.0, -0.9238563179969788), (0.35483869910240173, -0.3743400275707245, -0.8566851019859314), (0.27509385347366333, -0.69515061378479, -0.6641132831573486), (0.15424054861068726, -0.9151585698127747, -0.3723868429660797), (0.2850123643875122, 0.9151585698127747, -0.2850123643875122), (0.5082857608795166, 0.69515061378479, -0.5082857608795166), (0.6556596755981445, 0.3743400275707245, -0.6556596755981445), (0.7070833444595337, 0.0, -0.7070833444595337), (0.6556596755981445, -0.3743400275707245, -0.6556596755981445), (0.5082857608795166, -0.69515061378479, -0.5082857608795166), (0.2850123643875122, -0.9151585698127747, -0.2850123643875122), (0.3723868429660797, 0.9151585698127747, -0.15424054861068726), (0.6641132831573486, 0.69515061378479, -0.27509385347366333), (0.8566851019859314, 0.3743400275707245, -0.35483869910240173), (0.9238563179969788, 0.0, -0.382671594619751), (0.8566851019859314, -0.3743400275707245, -0.35483869910240173), (0.6641132831573486, -0.69515061378479, -0.27509385347366333), (0.3723868429660797, -0.9151585698127747, -0.15424054861068726), (0.4030884802341461, 0.9151585698127747, 0.0), (0.7188329696655273, 0.69515061378479, 0.0), (0.9272744059562683, 0.3743400275707245, 0.0), (1.0, 0.0, 0.0), (0.9272744059562683, -0.3743400275707245, 0.0), (0.7188329696655273, -0.69515061378479, 0.0), (0.4030884802341461, -0.9151585698127747, 0.0), (0.3723868429660797, 0.9151585698127747, 0.15424054861068726), (0.6641132831573486, 0.69515061378479, 0.27509385347366333), (0.8566851019859314, 0.3743400275707245, 0.35483869910240173), (0.9238563179969788, 0.0, 0.382671594619751), (0.8566851019859314, -0.3743400275707245, 0.35483869910240173), (0.6641132831573486, -0.69515061378479, 0.27509385347366333), (0.3723868429660797, -0.9151585698127747, 0.15424054861068726), (0.2850123643875122, 0.9151585698127747, 0.2850123643875122), (0.5082857608795166, 0.69515061378479, 0.5082857608795166), (0.6556596755981445, 0.3743400275707245, 0.6556596755981445), (0.7070833444595337, 0.0, 0.7070833444595337), (0.6556596755981445, -0.3743400275707245, 0.6556596755981445), (0.5082857608795166, -0.69515061378479, 0.5082857608795166), (0.2850123643875122, -0.9151585698127747, 0.2850123643875122), (0.15424054861068726, 0.9151585698127747, 0.3723868429660797), (0.27509385347366333, 0.69515061378479, 0.6641132831573486), (0.35483869910240173, 0.3743400275707245, 0.8566851019859314), (0.382671594619751, 0.0, 0.9238563179969788), (0.35483869910240173, -0.3743400275707245, 0.8566851019859314), (0.27509385347366333, -0.69515061378479, 0.6641132831573486), (0.15424054861068726, -0.9151585698127747, 0.3723868429660797), (0.0, 0.9151585698127747, 0.4030884802341461), (0.0, 0.69515061378479, 0.7188329696655273), (0.0, 0.3743400275707245, 0.9272744059562683), (0.0, 0.0, 1.0), (0.0, -0.3743400275707245, 0.9272744059562683), (0.0, -0.69515061378479, 0.7188329696655273), (0.0, -0.9151585698127747, 0.4030884802341461), (-0.15424054861068726, 0.9151585698127747, 0.3723868429660797), (-0.27509385347366333, 0.69515061378479, 0.6641132831573486), (-0.35483869910240173, 0.3743400275707245, 0.8566851019859314), (-0.382671594619751, 0.0, 0.9238563179969788), (-0.35483869910240173, -0.3743400275707245, 0.8566851019859314), (-0.27509385347366333, -0.69515061378479, 0.6641132831573486), (-0.15424054861068726, -0.9151585698127747, 0.3723868429660797), (0.0, -1.0, 0.0), (-0.2850123643875122, 0.9151585698127747, 0.2850123643875122), (-0.5082857608795166, 0.69515061378479, 0.5082857608795166), (-0.6556596755981445, 0.3743400275707245, 0.6556596755981445), (-0.7070833444595337, 0.0, 0.7070833444595337), (-0.6556596755981445, -0.3743400275707245, 0.6556596755981445), (-0.5082857608795166, -0.69515061378479, 0.5082857608795166), (-0.2850123643875122, -0.9151585698127747, 0.2850123643875122), (-0.3723868429660797, 0.9151585698127747, 0.15424054861068726), (-0.6641132831573486, 0.69515061378479, 0.27509385347366333), (-0.8566851019859314, 0.3743400275707245, 0.35483869910240173), (-0.9238563179969788, 0.0, 0.382671594619751), (-0.8566851019859314, -0.3743400275707245, 0.35483869910240173), (-0.6641132831573486, -0.69515061378479, 0.27509385347366333), (-0.3723868429660797, -0.9151585698127747, 0.15424054861068726)]],
             'triangles': [(5, 12, 13, 5, 12, 13), (4, 11, 12, 4, 11, 12), (4, 3, 10, 4, 3, 10), (2, 9, 10, 2, 9, 10), (2, 1, 8, 2, 1, 8), (0, 7, 8, 0, 7, 8), (13, 12, 19, 13, 12, 19), (11, 18, 19, 11, 18, 19), (10, 17, 18, 10, 17, 18), (9, 16, 17, 9, 16, 17), (8, 15, 16, 8, 15, 16), (7, 14, 15, 7, 14, 15), (19, 26, 27, 19, 26, 27), (18, 25, 26, 18, 25, 26), (17, 24, 25, 17, 24, 25), (16, 23, 24, 16, 23, 24), (15, 22, 23, 15, 22, 23), (14, 21, 22, 14, 21, 22), (26, 33, 34, 26, 33, 34), (25, 32, 33, 25, 32, 33), (24, 31, 32, 24, 31, 32), (23, 30, 31, 23, 30, 31), (23, 22, 29, 23, 22, 29), (22, 21, 28, 22, 21, 28), (34, 33, 41, 34, 33, 41), (32, 40, 41, 32, 40, 41), (31, 39, 40, 31, 39, 40), (30, 38, 39, 30, 38, 39), (29, 37, 38, 29, 37, 38), (29, 28, 36, 29, 28, 36), (42, 41, 48, 42, 41, 48), (41, 40, 47, 41, 40, 47), (40, 39, 46, 40, 39, 46), (38, 45, 46, 38, 45, 46), (37, 44, 45, 37, 44, 45), (37, 36, 43, 37, 36, 43), (49, 48, 55, 49, 48, 55), (48, 47, 54, 48, 47, 54), (47, 46, 53, 47, 46, 53), (46, 45, 52, 46, 45, 52), (44, 51, 52, 44, 51, 52), (44, 43, 50, 44, 43, 50), (55, 62, 63, 55, 62, 63), (54, 61, 62, 54, 61, 62), (53, 60, 61, 53, 60, 61), (52, 59, 60, 52, 59, 60), (51, 58, 59, 51, 58, 59), (51, 50, 57, 51, 50, 57), (63, 62, 69, 63, 62, 69), (62, 61, 68, 62, 61, 68), (60, 67, 68, 60, 67, 68), (59, 66, 67, 59, 66, 67), (58, 65, 66, 58, 65, 66), (58, 57, 64, 58, 57, 64), (69, 76, 77, 69, 76, 77), (69, 68, 75, 69, 68, 75), (67, 74, 75, 67, 74, 75), (67, 66, 73, 67, 66, 73), (65, 72, 73, 65, 72, 73), (64, 71, 72, 64, 71, 72), (76, 83, 84, 76, 83, 84), (76, 75, 82, 76, 75, 82), (74, 81, 82, 74, 81, 82), (74, 73, 80, 74, 73, 80), (72, 79, 80, 72, 79, 80), (71, 78, 79, 71, 78, 79), (84, 83, 90, 84, 83, 90), (82, 89, 90, 82, 89, 90), (81, 88, 89, 81, 88, 89), (81, 80, 87, 81, 80, 87), (79, 86, 87, 79, 86, 87), (79, 78, 85, 79, 78, 85), (91, 90, 97, 91, 90, 97), (90, 89, 96, 90, 89, 96), (88, 95, 96, 88, 95, 96), (88, 87, 94, 88, 87, 94), (87, 86, 93, 87, 86, 93), (85, 92, 93, 85, 92, 93), (97, 105, 106, 97, 105, 106), (96, 104, 105, 96, 104, 105), (95, 103, 104, 95, 103, 104), (95, 94, 102, 95, 94, 102), (93, 101, 102, 93, 101, 102), (93, 92, 100, 93, 92, 100), (106, 105, 112, 106, 105, 112), (105, 104, 111, 105, 104, 111), (103, 110, 111, 103, 110, 111), (103, 102, 109, 103, 102, 109), (101, 108, 109, 101, 108, 109), (100, 107, 108, 100, 107, 108), (99, 6, 13, 99, 6, 13), (0, 35, 7, 0, 35, 7), (99, 13, 20, 99, 13, 20), (7, 35, 14, 7, 35, 14), (99, 20, 27, 99, 20, 27), (14, 35, 21, 14, 35, 21), (99, 27, 34, 99, 27, 34), (21, 35, 28, 21, 35, 28), (99, 34, 42, 99, 34, 42), (28, 35, 36, 28, 35, 36), (99, 42, 49, 99, 42, 49), (36, 35, 43, 36, 35, 43), (99, 49, 56, 99, 49, 56), (43, 35, 50, 43, 35, 50), (99, 56, 63, 99, 56, 63), (50, 35, 57, 50, 35, 57), (99, 63, 70, 99, 63, 70), (57, 35, 64, 57, 35, 64), (99, 70, 77, 99, 70, 77), (64, 35, 71, 64, 35, 71), (99, 77, 84, 99, 77, 84), (71, 35, 78, 71, 35, 78), (99, 84, 91, 99, 84, 91), (78, 35, 85, 78, 35, 85), (99, 91, 98, 99, 91, 98), (85, 35, 92, 85, 35, 92), (99, 98, 106, 99, 98, 106), (92, 35, 100, 92, 35, 100), (99, 106, 113, 99, 106, 113), (100, 35, 107, 100, 35, 107), (99, 113, 6, 99, 113, 6), (112, 5, 6, 112, 5, 6), (111, 4, 5, 111, 4, 5), (110, 3, 4, 110, 3, 4), (110, 109, 2, 110, 109, 2), (109, 108, 1, 109, 108, 1), (108, 107, 0, 108, 107, 0), (107, 35, 0, 107, 35, 0), (6, 5, 13, 6, 5, 13), (5, 4, 12, 5, 4, 12), (11, 4, 10, 11, 4, 10), (3, 2, 10, 3, 2, 10), (9, 2, 8, 9, 2, 8), (1, 0, 8, 1, 0, 8), (20, 13, 19, 20, 13, 19), (12, 11, 19, 12, 11, 19), (11, 10, 18, 11, 10, 18), (10, 9, 17, 10, 9, 17), (9, 8, 16, 9, 8, 16), (8, 7, 15, 8, 7, 15), (20, 19, 27, 20, 19, 27), (19, 18, 26, 19, 18, 26), (18, 17, 25, 18, 17, 25), (17, 16, 24, 17, 16, 24), (16, 15, 23, 16, 15, 23), (15, 14, 22, 15, 14, 22), (27, 26, 34, 27, 26, 34), (26, 25, 33, 26, 25, 33), (25, 24, 32, 25, 24, 32), (24, 23, 31, 24, 23, 31), (30, 23, 29, 30, 23, 29), (29, 22, 28, 29, 22, 28), (42, 34, 41, 42, 34, 41), (33, 32, 41, 33, 32, 41), (32, 31, 40, 32, 31, 40), (31, 30, 39, 31, 30, 39), (30, 29, 38, 30, 29, 38), (37, 29, 36, 37, 29, 36), (49, 42, 48, 49, 42, 48), (48, 41, 47, 48, 41, 47), (47, 40, 46, 47, 40, 46), (39, 38, 46, 39, 38, 46), (38, 37, 45, 38, 37, 45), (44, 37, 43, 44, 37, 43), (56, 49, 55, 56, 49, 55), (55, 48, 54, 55, 48, 54), (54, 47, 53, 54, 47, 53), (53, 46, 52, 53, 46, 52), (45, 44, 52, 45, 44, 52), (51, 44, 50, 51, 44, 50), (56, 55, 63, 56, 55, 63), (55, 54, 62, 55, 54, 62), (54, 53, 61, 54, 53, 61), (53, 52, 60, 53, 52, 60), (52, 51, 59, 52, 51, 59), (58, 51, 57, 58, 51, 57), (70, 63, 69, 70, 63, 69), (69, 62, 68, 69, 62, 68), (61, 60, 68, 61, 60, 68), (60, 59, 67, 60, 59, 67), (59, 58, 66, 59, 58, 66), (65, 58, 64, 65, 58, 64), (70, 69, 77, 70, 69, 77), (76, 69, 75, 76, 69, 75), (68, 67, 75, 68, 67, 75), (74, 67, 73, 74, 67, 73), (66, 65, 73, 66, 65, 73), (65, 64, 72, 65, 64, 72), (77, 76, 84, 77, 76, 84), (83, 76, 82, 83, 76, 82), (75, 74, 82, 75, 74, 82), (81, 74, 80, 81, 74, 80), (73, 72, 80, 73, 72, 80), (72, 71, 79, 72, 71, 79), (91, 84, 90, 91, 84, 90), (83, 82, 90, 83, 82, 90), (82, 81, 89, 82, 81, 89), (88, 81, 87, 88, 81, 87), (80, 79, 87, 80, 79, 87), (86, 79, 85, 86, 79, 85), (98, 91, 97, 98, 91, 97), (97, 90, 96, 97, 90, 96), (89, 88, 96, 89, 88, 96), (95, 88, 94, 95, 88, 94), (94, 87, 93, 94, 87, 93), (86, 85, 93, 86, 85, 93), (98, 97, 106, 98, 97, 106), (97, 96, 105, 97, 96, 105), (96, 95, 104, 96, 95, 104), (103, 95, 102, 103, 95, 102), (94, 93, 102, 94, 93, 102), (101, 93, 100, 101, 93, 100), (113, 106, 112, 113, 106, 112), (112, 105, 111, 112, 105, 111), (104, 103, 111, 104, 103, 111), (110, 103, 109, 110, 103, 109), (102, 101, 109, 102, 101, 109), (101, 100, 108, 101, 100, 108), (113, 112, 6, 113, 112, 6), (112, 111, 5, 112, 111, 5), (111, 110, 4, 111, 110, 4), (3, 110, 2, 3, 110, 2), (2, 109, 1, 2, 109, 1), (1, 108, 0, 1, 108, 0)],
             'triangle_normals': [[(-0.5522086024284363, -0.8264384865760803, -0.10984117537736893), (-0.8203257322311401, -0.5481243133544922, -0.1631729155778885), (-0.9626372456550598, -0.19148050248622894, -0.19148053228855133), (-0.9626372456550598, 0.19148044288158417, -0.19148050248622894), (-0.8203257918357849, 0.5481241941452026, -0.16317304968833923), (-0.5522086024284363, 0.8264384269714355, -0.10984115302562714), (-0.4681398272514343, -0.8264385461807251, -0.3128011226654053), (-0.6954385638237, -0.5481244325637817, -0.46467721462249756), (-0.8160844445228577, -0.19148051738739014, -0.5452902317047119), (-0.8160843253135681, 0.19148050248622894, -0.5452902317047119), (-0.6954386234283447, 0.5481241345405579, -0.4646773338317871), (-0.46813976764678955, 0.8264384865760803, -0.3128011226654053), (-0.31280094385147095, -0.8264384865760803, -0.46813997626304626), (-0.46467703580856323, -0.5481244325637817, -0.6954385638237), (-0.5452899932861328, -0.19148047268390656, -0.8160845637321472), (-0.5452900528907776, 0.19148045778274536, -0.8160845637321472), (-0.46467721462249756, 0.5481241345405579, -0.6954387426376343), (-0.3128010332584381, 0.8264384865760803, -0.4681398868560791), (-0.1098412424325943, -0.8264385461807251, -0.5522085428237915), (-0.16317282617092133, -0.5481244325637817, -0.8203257322311401), (-0.19148026406764984, -0.1914803832769394, -0.9626373648643494), (-0.1914803385734558, 0.191480353474617, -0.9626372456550598), (-0.16317275166511536, 0.5481241345405579, -0.8203258514404297), (-0.10984106361865997, 0.8264384865760803, -0.552208662033081), (0.1098414808511734, -0.8264384269714355, -0.5522085428237915), (0.16317307949066162, -0.5481245517730713, -0.820325493812561), (0.19148071110248566, -0.19148032367229462, -0.9626373052597046), (0.19148065149784088, 0.19148030877113342, -0.9626371264457703), (0.1631731241941452, 0.5481241941452026, -0.8203257918357849), (0.10984117537736893, 0.8264383673667908, -0.552208662033081), (0.31280121207237244, -0.8264383673667908, -0.4681399166584015), (0.4646773040294647, -0.5481245517730713, -0.6954383254051208), (0.5452904105186462, -0.19148032367229462, -0.8160843253135681), (0.5452904105186462, 0.19148029386997223, -0.8160843253135681), (0.46467745304107666, 0.5481242537498474, -0.6954383850097656), (0.31280115246772766, 0.8264384865760803, -0.4681398868560791), (0.46814003586769104, -0.8264384269714355, -0.3128010332584381), (0.6954386234283447, -0.5481244921684265, -0.4646768867969513), (0.8160846829414368, -0.19148029386997223, -0.545289933681488), (0.816084623336792, 0.19148027896881104, -0.5452899932861328), (0.6954387426376343, 0.5481242537498474, -0.464677095413208), (0.4681399464607239, 0.8264384269714355, -0.3128010332584381), (0.5522087216377258, -0.8264384865760803, -0.10984096676111221), (0.8203257918357849, -0.5481244325637817, -0.1631726622581482), (0.9626373648643494, -0.19148021936416626, -0.1914801150560379), (0.9626372456550598, 0.19148017466068268, -0.19148017466068268), (0.8203257918357849, 0.5481242537498474, -0.1631726771593094), (0.552208662033081, 0.8264384269714355, -0.10984106361865997), (0.5522086024284363, -0.8264384269714355, 0.10984133183956146), (0.8203256726264954, -0.5481243133544922, 0.16317330300807953), (0.9626372456550598, -0.19148030877113342, 0.19148074090480804), (0.9626371264457703, 0.19148032367229462, 0.191480815410614), (0.8203257322311401, 0.5481243133544922, 0.16317324340343475), (0.5522086024284363, 0.8264384865760803, 0.10984127968549728), (0.46813979744911194, -0.8264384865760803, 0.3128013610839844), (0.6954383850097656, -0.5481243133544922, 0.4646776616573334), (0.8160842657089233, -0.19148039817810059, 0.5452905893325806), (0.8160841464996338, 0.1914803385734558, 0.5452905893325806), (0.6954383254051208, 0.5481243133544922, 0.4646776020526886), (0.4681399166584015, 0.8264384269714355, 0.31280121207237244), (0.31280088424682617, -0.8264384269714355, 0.46813997626304626), (0.46467697620391846, -0.5481241345405579, 0.6954388618469238), (0.5452898740768433, -0.1914803683757782, 0.8160846829414368), (0.5452898740768433, 0.19148042798042297, 0.8160846829414368), (0.4646768569946289, 0.5481242537498474, 0.6954387426376343), (0.31280091404914856, 0.8264383673667908, 0.46814003586769104), (0.10984067618846893, -0.8264384269714355, 0.5522087216377258), (0.1631726175546646, -0.5481242537498474, 0.8203259110450745), (0.19147998094558716, -0.19148032367229462, 0.9626373648643494), (0.19148005545139313, 0.19148042798042297, 0.9626373648643494), (0.163172647356987, 0.5481242537498474, 0.8203257918357849), (0.10984095931053162, 0.8264384865760803, 0.5522087216377258), (-0.10984129458665848, -0.8264384269714355, 0.5522087216377258), (-0.16317330300807953, -0.5481241941452026, 0.8203257918357849), (-0.19148103892803192, -0.19148020446300507, 0.962637186050415), (-0.1914808750152588, 0.19148041307926178, 0.9626372456550598), (-0.16317355632781982, 0.5481241941452026, 0.8203256726264954), (-0.10984132438898087, 0.826438307762146, 0.5522087216377258), (-0.3128015100955963, -0.8264383673667908, 0.46813973784446716), (-0.4646775722503662, -0.5481243133544922, 0.6954383254051208), (-0.5452907681465149, -0.19148015975952148, 0.8160842061042786), (-0.5452906489372253, 0.19148026406764984, 0.8160841464996338), (-0.464677631855011, 0.548124372959137, 0.6954382658004761), (-0.3128012418746948, 0.8264383673667908, 0.4681398272514343), (-0.468140184879303, -0.826438307762146, 0.3128008544445038), (-0.6954389214515686, -0.5481242537498474, 0.46467670798301697), (-0.8160848021507263, -0.19148039817810059, 0.5452898144721985), (-0.8160849213600159, 0.19148024916648865, 0.5452895760536194), (-0.6954389810562134, 0.5481241941452026, 0.46467679738998413), (-0.468140184879303, 0.8264383673667908, 0.3128010332584381), (-0.19494371116161346, -0.9800475835800171, -0.038776759058237076), (-0.19494374096393585, 0.9800475835800171, -0.03877673298120499), (-0.1652653068304062, -0.9800476431846619, -0.11042678356170654), (-0.1652652770280838, 0.9800476431846619, -0.11042676866054535), (-0.11042673140764236, -0.9800476431846619, -0.16526535153388977), (-0.11042675375938416, 0.9800477027893066, -0.165265291929245), (-0.03877665475010872, -0.9800475835800171, -0.19494375586509705), (-0.03877665847539902, 0.9800475239753723, -0.19494368135929108), (0.03877677023410797, -0.9800475835800171, -0.19494372606277466), (0.038776692003011703, 0.9800475835800171, -0.19494368135929108), (0.11042682081460953, -0.9800476431846619, -0.165265291929245), (0.11042676120996475, 0.9800476431846619, -0.1652652621269226), (0.16526538133621216, -0.9800476431846619, -0.11042668670415878), (0.1652652770280838, 0.9800476431846619, -0.11042669415473938), (0.19494375586509705, -0.9800475835800171, -0.03877665475010872), (0.19494372606277466, 0.9800476431846619, -0.0387766994535923), (0.19494371116161346, -0.9800475239753723, 0.03877681493759155), (0.19494372606277466, 0.9800476431846619, 0.03877676650881767), (0.1652652472257614, -0.9800475239753723, 0.11042683571577072), (0.16526532173156738, 0.9800475835800171, 0.11042681336402893), (0.11042667925357819, -0.9800476431846619, 0.16526539623737335), (0.11042670905590057, 0.9800475239753723, 0.16526536643505096), (0.038776617497205734, -0.9800475835800171, 0.19494378566741943), (0.03877665475010872, 0.9800475835800171, 0.19494381546974182), (-0.03877681866288185, -0.9800475239753723, 0.19494371116161346), (-0.038776788860559464, 0.9800475239753723, 0.19494381546974182), (-0.11042685806751251, -0.9800476431846619, 0.165265291929245), (-0.11042685061693192, 0.9800475835800171, 0.16526535153388977), (-0.16526541113853455, -0.9800475835800171, 0.11042666435241699), (-0.16526544094085693, 0.9800475835800171, 0.11042674630880356), (-0.19494372606277466, -0.9800476431846619, 0.03877682238817215), (-0.5522086024284363, -0.8264384865760803, 0.10984150320291519), (-0.8203256726264954, -0.5481241941452026, 0.1631733924150467), (-0.9626371264457703, -0.19148047268390656, 0.19148088991641998), (-0.9626371264457703, 0.19148056209087372, 0.19148091971874237), (-0.8203257322311401, 0.5481242537498474, 0.16317348182201385), (-0.5522086024284363, 0.8264384269714355, 0.10984136909246445), (-0.19494375586509705, 0.9800475239753723, 0.03877680376172066), (-0.5522086024284363, -0.8264384269714355, -0.1098412498831749), (-0.8203257918357849, -0.5481242537498474, -0.16317296028137207), (-0.9626372456550598, -0.19148044288158417, -0.19148045778274536), (-0.9626373052597046, 0.19148050248622894, -0.19148056209087372), (-0.8203258514404297, 0.5481241941452026, -0.16317303478717804), (-0.5522086024284363, 0.8264384865760803, -0.10984115302562714), (-0.4681398272514343, -0.8264385461807251, -0.3128011226654053), (-0.6954384446144104, -0.5481243133544922, -0.46467727422714233), (-0.8160843849182129, -0.19148047268390656, -0.5452902317047119), (-0.8160845041275024, 0.19148042798042297, -0.5452902913093567), (-0.6954386234283447, 0.5481241345405579, -0.4646773338317871), (-0.4681398570537567, 0.8264384269714355, -0.3128010928630829), (-0.31280094385147095, -0.8264384865760803, -0.4681399166584015), (-0.46467697620391846, -0.5481244325637817, -0.6954386830329895), (-0.5452900528907776, -0.19148050248622894, -0.8160845041275024), (-0.5452899932861328, 0.19148047268390656, -0.8160845637321472), (-0.4646771550178528, 0.5481241345405579, -0.6954387426376343), (-0.3128010034561157, 0.8264384269714355, -0.4681398868560791), (-0.10984096676111221, -0.8264383673667908, -0.5522087216377258), (-0.16317294538021088, -0.5481244921684265, -0.8203256130218506), (-0.191480353474617, -0.19148047268390656, -0.9626373052597046), (-0.19148024916648865, 0.19148042798042297, -0.9626372456550598), (-0.16317284107208252, 0.5481241941452026, -0.8203258514404297), (-0.10984090715646744, 0.8264384269714355, -0.5522087216377258), (0.10984128713607788, -0.8264383673667908, -0.552208662033081), (0.16317328810691833, -0.5481244325637817, -0.8203256130218506), (0.1914806365966797, -0.1914803385734558, -0.9626371264457703), (0.19148071110248566, 0.1914803683757782, -0.9626373052597046), (0.16317309439182281, 0.5481241941452026, -0.8203257322311401), (0.10984114557504654, 0.8264384865760803, -0.552208662033081), (0.3128012716770172, -0.8264384269714355, -0.4681398272514343), (0.46467727422714233, -0.5481245517730713, -0.6954383850097656), (0.5452904105186462, -0.19148030877113342, -0.8160842657089233), (0.5452904105186462, 0.19148029386997223, -0.8160843253135681), (0.4646774232387543, 0.5481242537498474, -0.6954384446144104), (0.3128013014793396, 0.8264384865760803, -0.4681398868560791), (0.46814000606536865, -0.8264383673667908, -0.3128008544445038), (0.6954386234283447, -0.5481244325637817, -0.46467703580856323), (0.816084623336792, -0.19148026406764984, -0.545289933681488), (0.8160846829414368, 0.19148021936416626, -0.5452899932861328), (0.695438802242279, 0.5481242537498474, -0.4646770656108856), (0.46814003586769104, 0.8264384269714355, -0.3128010332584381), (0.5522087812423706, -0.8264383673667908, -0.10984102636575699), (0.8203257322311401, -0.548124372959137, -0.1631726771593094), (0.9626373648643494, -0.19148027896881104, -0.19148018956184387), (0.9626373052597046, 0.19148026406764984, -0.1914801299571991), (0.8203257918357849, 0.5481242537498474, -0.16317275166511536), (0.5522087216377258, 0.8264384865760803, -0.10984096676111221), (0.5522086024284363, -0.8264384269714355, 0.10984139144420624), (0.8203257322311401, -0.5481243133544922, 0.16317324340343475), (0.9626371264457703, -0.19148017466068268, 0.1914808452129364), (0.9626372456550598, 0.19148023426532745, 0.19148071110248566), (0.8203257322311401, 0.5481242537498474, 0.16317322850227356), (0.5522086024284363, 0.8264384269714355, 0.10984133183956146), (0.46813976764678955, -0.8264384269714355, 0.312801331281662), (0.6954383850097656, -0.5481242537498474, 0.464677631855011), (0.8160842061042786, -0.19148027896881104, 0.5452907681465149), (0.8160842061042786, 0.19148042798042297, 0.5452905297279358), (0.6954383850097656, 0.5481241941452026, 0.4646775722503662), (0.4681397080421448, 0.8264384865760803, 0.3128013610839844), (0.3128008246421814, -0.8264384269714355, 0.46814003586769104), (0.46467697620391846, -0.5481241345405579, 0.695438802242279), (0.545289933681488, -0.19148042798042297, 0.8160846829414368), (0.5452898740768433, 0.19148039817810059, 0.8160846829414368), (0.46467694640159607, 0.5481241941452026, 0.6954387426376343), (0.31280091404914856, 0.8264384269714355, 0.4681400954723358), (0.10984085500240326, -0.8264384269714355, 0.5522087812423706), (0.16317245364189148, -0.5481240749359131, 0.8203259706497192), (0.19148004055023193, -0.1914803832769394, 0.9626373648643494), (0.19147996604442596, 0.1914803385734558, 0.9626373648643494), (0.16317258775234222, 0.5481242537498474, 0.8203257918357849), (0.1098410114645958, 0.8264384269714355, 0.552208662033081), (-0.10984140634536743, -0.8264384865760803, 0.5522086024284363), (-0.16317330300807953, -0.5481241941452026, 0.8203257322311401), (-0.1914808452129364, -0.1914803832769394, 0.962637186050415), (-0.19148103892803192, 0.19148021936416626, 0.9626371264457703), (-0.16317325830459595, 0.548124372959137, 0.8203256130218506), (-0.10984162986278534, 0.8264384269714355, 0.5522084832191467), (-0.3128013014793396, -0.8264383673667908, 0.4681397080421448), (-0.4646777808666229, -0.5481241345405579, 0.6954383254051208), (-0.5452907085418701, -0.19148026406764984, 0.8160842061042786), (-0.5452907681465149, 0.19148017466068268, 0.8160841464996338), (-0.4646775722503662, 0.548124372959137, 0.6954382658004761), (-0.31280142068862915, 0.8264383673667908, 0.4681398272514343), (-0.46814021468162537, -0.8264383673667908, 0.3128008544445038), (-0.6954389810562134, -0.5481241941452026, 0.46467679738998413), (-0.8160848617553711, -0.19148023426532745, 0.5452896356582642), (-0.8160847425460815, 0.19148044288158417, 0.5452897548675537), (-0.6954389810562134, 0.5481243133544922, 0.4646766185760498), (-0.4681401550769806, 0.8264383673667908, 0.3128008246421814), (-0.5522086024284363, -0.8264383673667908, 0.10984142124652863), (-0.8203256130218506, -0.5481242537498474, 0.16317351162433624), (-0.962637186050415, -0.19148056209087372, 0.19148096442222595), (-0.9626370668411255, 0.19148048758506775, 0.1914808452129364), (-0.8203257918357849, 0.5481241941452026, 0.1631733477115631), (-0.5522085428237915, 0.8264384269714355, 0.109841488301754)]],
             'uv_channels': None,
             'object_props': (False, 100.0, (255, 255, 255), False, False, False, False, False),
             'num_materials': 0,
             'materials': None,
             'triangle_materials': None,
             'backface_material': ('', True), }
        mxs.mesh(**d)
        
        d = {'env_type': 'PHYSICAL_SKY',
             'sky_type': 'PHYSICAL',
             'sky': {"sky_asymmetry": 0.699999988079071, "sky_intensity": 1.0, "sky_ozone": 0.4000000059604645, "sky_planet_refl": 0.25, "sky_preset": "", "sky_reflectance": 0.8, "sky_turbidity_coeff": 0.03999999910593033, "sky_use_preset": False, "sky_water": 2.0, "sky_wavelength_exp": 1.2000000476837158, },
             'dome': {"dome_horizon": [255, 255, 255], "dome_intensity": 10000.0, "dome_mid_point": 45.00000125223908, "dome_zenith": [255, 255, 255], },
             'sun_type': 'PHYSICAL',
             'sun': {"sun_angles_azimuth": 0.7853981852531433, "sun_angles_zenith": 0.7853981852531433, "sun_color": [255, 255, 255], "sun_date": "14.04.2015", "sun_dir_x": 0.0, "sun_dir_y": 1.0, "sun_dir_z": 0.0, "sun_lamp_priority": False, "sun_latlong_gmt": 0, "sun_latlong_ground_rotation": 0.0, "sun_latlong_lat": 40.0, "sun_latlong_lon": -3.0, "sun_location_type": "DIRECTION", "sun_power": 1.0, "sun_radius_factor": 1.0, "sun_temp": 5776.0, "sun_time": "19:45", },
             'ibl': {"ibl_intensity": 1.0, "ibl_interpolation": False, "ibl_screen_mapping": False,
                     "ibl_bg_type": "HDR_IMAGE", "ibl_bg_intensity": 1.0, "ibl_bg_map": "", "ibl_bg_offset_x": 0.0, "ibl_bg_offset_y": 0.0, "ibl_bg_scale_x": 1.0, "ibl_bg_scale_y": 1.0,
                     "ibl_illum_type": "SAME_AS_BG", "ibl_illum_intensity": 1.0, "ibl_illum_map": "", "ibl_illum_offset_x": 0.0, "ibl_illum_offset_y": 0.0, "ibl_illum_scale_x": 1.0, "ibl_illum_scale_y": 1.0,
                     "ibl_refl_type": "SAME_AS_BG", "ibl_refl_intensity": 1.0, "ibl_refl_map": "", "ibl_refl_offset_x": 0.0, "ibl_refl_offset_y": 0.0, "ibl_refl_scale_x": 1.0, "ibl_refl_scale_y": 1.0,
                     "ibl_refr_type": "SAME_AS_BG", "ibl_refr_intensity": 1.0, "ibl_refr_map": "", "ibl_refr_offset_x": 0.0, "ibl_refr_offset_y": 0.0, "ibl_refr_scale_x": 1.0, "ibl_refr_scale_y": 1.0, }, }
        mxs.environment(**d)
        
        d = {'scene': {'cpu_threads': 0, 'multilight': 0, 'multilight_type': 0, 'quality': "RS1", 'sampling_level': 12.0, 'time': 60, },
             'materials': {'override': False, 'override_path': "", 'search_path': "", },
             'generals': {'diplacement': True, 'dispersion': True, 'motion_blur': True, },
             'tone': {'burn': 0.800000011920929, 'color_space': 0, 'gamma': 2.200000047683716, 'sharpness': False, 'sharpness_value': 0.6, 'tint': 0.0, 'whitepoint': 6500.0, },
             'simulens': {'aperture_map': "", 'devignetting': False, 'devignetting_value': 0.0, 'diffraction': False, 'diffraction_value': 0.02,
                          'frequency': 0.02, 'obstacle_map': "", 'scattering': False, 'scattering_value': 0.0, },
             'illum_caustics': {'illumination': 0, 'refl_caustics': 0, 'refr_caustics': 0, }, }
        mxs.parameters(**d)
        
        mxi_path = "/Volumes/internal-2tb/teoplib/tmp/test_data.mxi"
        image_path = "/Volumes/internal-2tb/teoplib/tmp/test_data.png"
        h, t = os.path.split(mxi_path)
        n, e = os.path.splitext(t)
        base_path = os.path.join(h, n)
        d = {'base_path': base_path, 'mxi': mxi_path, 'image': image_path, 'image_depth': "RGB8", 'channels_output_mode': 0, 'channels_render': True, 'channels_render_type': 0,
             'channels': {"channels_alpha": False, "channels_alpha_file": "PNG16", "channels_alpha_opaque": False, "channels_custom_alpha": False, "channels_custom_alpha_file": "PNG16",
                          "channels_deep": False, "channels_deep_file": "EXR_DEEP", "channels_deep_max_samples": 20, "channels_deep_min_dist": 0.20000000298023224, "channels_deep_type": 0,
                          "channels_fresnel": False, "channels_fresnel_file": "PNG16", "channels_material_id": False, "channels_material_id_file": "PNG16",
                          "channels_motion_vector": False, "channels_motion_vector_file": "PNG16", "channels_normals": False, "channels_normals_file": "PNG16", "channels_normals_space": 0,
                          "channels_object_id": False, "channels_object_id_file": "PNG16", "channels_position": False, "channels_position_file": "PNG16", "channels_position_space": 0,
                          "channels_roughness": False, "channels_roughness_file": "PNG16", "channels_shadow": False, "channels_shadow_file": "PNG16", "channels_uv": False, "channels_uv_file": "PNG16",
                          "channels_z_buffer": False, "channels_z_buffer_far": 0.0, "channels_z_buffer_file": "PNG16", "channels_z_buffer_near": 0.0, }, }
        mxs.channels(**d)
        
        '''
        d = {'groups': [{'name': 'custom alpha', 'objects': ["Cube", "Cube.001"], 'opaque': True, }, ], }
        mxs.custom_alphas(**d)
        '''
        
        mxs.write()
    
    test()
