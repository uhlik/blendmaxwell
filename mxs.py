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
