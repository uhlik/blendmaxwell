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
import os

# from pymaxwell import *


LOG_FILE_PATH = None


def log(msg, indent=0):
    m = "{0}> {1}".format("    " * indent, msg)
    print(m)
    if(LOG_FILE_PATH is not None):
        with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
            f.write("{}{}".format(m, "\n"))


def material_placeholder(s, n=None, ):
    if(n is not None):
        # n = '{}_{}'.format(n, 'MATERIAL_PLACEHOLDER')
        pass
    else:
        n = 'MATERIAL_PLACEHOLDER'
    m = s.createMaterial(n)
    l = m.addLayer()
    b = l.addBSDF()
    r = b.getReflectance()
    a = Cattribute()
    a.activeType = MAP_TYPE_BITMAP
    t = CtextureMap()
    mgr = CextensionManager.instance()
    e = mgr.createDefaultTextureExtension('Checker')
    ch = e.getExtensionData()
    ch.setUInt('Number of elements U', 32)
    ch.setUInt('Number of elements V', 32)
    t.addProceduralTexture(ch)
    a.textureMap = t
    r.setAttribute('color', a)
    return m


def material_default(d, s, ):
    m = s.createMaterial(d['name'])
    l = m.addLayer()
    b = l.addBSDF()
    return m


def material_external(d, s, ):
    p = d['path']
    t = s.readMaterial(p)
    t.setName(d['name'])
    m = s.addMaterial(t)
    if(not d['embed']):
        m.setReference(1, p)
    return m


def material(d, s, ):
    """create material by type"""
    if(d['subtype'] == 'EXTERNAL'):
        if(d['path'] == ''):
            # m = material_default(d, s)
            m = material_placeholder(s, d['name'])
        else:
            m = material_external(d, s)
            
            if(d['override']):
                # global properties
                if(d['override_map']):
                    t = texture(d['override_map'], s, )
                    m.setGlobalMap(t)
                
                if(d['bump']):
                    a = Cattribute()
                    a.activeType = MAP_TYPE_BITMAP
                    a.textureMap = texture(d['bump_map'], s, )
                    a.value = d['bump_value']
                    m.setAttribute('bump', a)
                
                m.setDispersion(d['dispersion'])
                m.setMatteShadow(d['shadow'])
                m.setMatte(d['matte'])
                m.setNestedPriority(d['priority'])
                
                c = Crgb()
                cc = [c / 255 for c in d['id']]
                c.assign(*cc)
                m.setColorID(c)
        
    elif(d['subtype'] == 'EXTENSION'):
        if(d['use'] == 'EMITTER'):
            m = s.createMaterial(d['name'])
            l = m.addLayer()
            e = l.createEmitter()
            
            if(d['emitter_type'] == 0):
                e.setLobeType(EMISSION_LOBE_DEFAULT)
            elif(d['emitter_type'] == 1):
                e.setLobeType(EMISSION_LOBE_IES)
                e.setLobeIES(d['emitter_ies_data'])
                e.setIESLobeIntensity(d['emitter_ies_intensity'])
            elif(d['emitter_type'] == 2):
                # e.setLobeType(EMISSION_LOBE_BITMAP)
                e.setLobeType(EMISSION_LOBE_SPOTLIGHT)
                if(d['emitter_spot_map'] is not None):
                    t = texture(d['emitter_spot_map'], s)
                    e.setLobeImageProjectedMap(d['emitter_spot_map_enabled'], t)
                e.setSpotConeAngle(d['emitter_spot_cone_angle'])
                e.setSpotFallOffAngle(d['emitter_spot_falloff_angle'])
                e.setSpotFallOffType(d['emitter_spot_falloff_type'])
                e.setSpotBlur(d['emitter_spot_blur'])
            
            if(d['emitter_emission'] == 0):
                e.setActiveEmissionType(EMISSION_TYPE_PAIR)
                
                ep = CemitterPair()
                c = Crgb8()
                c.assign(*d['emitter_color'])
                ep.rgb.assign(c.toRGB())
                ep.temperature = d['emitter_color_black_body']
                ep.watts = d['emitter_luminance_power']
                ep.luminousEfficacy = d['emitter_luminance_efficacy']
                ep.luminousPower = d['emitter_luminance_output']
                ep.illuminance = d['emitter_luminance_output']
                ep.luminousIntensity = d['emitter_luminance_output']
                ep.luminance = d['emitter_luminance_output']
                e.setPair(ep)
                
                if(d['emitter_color_black_body_enabled']):
                    e.setActivePair(EMISSION_COLOR_TEMPERATURE)
                else:
                    if(d['emitter_luminance'] == 0):
                        u = EMISSION_UNITS_WATTS_AND_LUMINOUS_EFFICACY
                    elif(d['emitter_luminance'] == 1):
                        u = EMISSION_UNITS_LUMINOUS_POWER
                    elif(d['emitter_luminance'] == 2):
                        u = EMISSION_UNITS_ILLUMINANCE
                    elif(d['emitter_luminance'] == 3):
                        u = EMISSION_UNITS_LUMINOUS_INTENSITY
                    elif(d['emitter_luminance'] == 4):
                        u = EMISSION_UNITS_LUMINANCE
                    e.setActivePair(EMISSION_RGB, u)
            
            elif(d['emitter_emission'] == 1):
                e.setActiveEmissionType(EMISSION_TYPE_TEMPERATURE)
                e.setTemperature(d['emitter_temperature_value'])
            elif(d['emitter_emission'] == 2):
                e.setActiveEmissionType(EMISSION_TYPE_MXI)
                a = Cattribute()
                a.activeType = MAP_TYPE_BITMAP
                t = texture(d['emitter_hdr_map'], s)
                a.textureMap = t
                a.value = d['emitter_hdr_intensity']
                e.setMXI(a)
            
            e.setState(True)
        else:
            m = CextensionManager.instance()
            if(d['use'] == 'AGS'):
                e = m.createDefaultMaterialModifierExtension('AGS')
                p = e.getExtensionData()
            
                c = Crgb8()
                c.assign(*d['ags_color'])
                p.setRgb('Color', c.toRGB())
                p.setFloat('Reflection', d['ags_reflection'])
                p.setUInt('Type', d['ags_type'])
            
            elif(d['use'] == 'OPAQUE'):
                e = m.createDefaultMaterialModifierExtension('Opaque')
                p = e.getExtensionData()
            
                p.setByte('Color Type', d['opaque_color_type'])
                c = Crgb8()
                c.assign(*d['opaque_color'])
                p.setRgb('Color', c.toRGB())
                texture_data_to_mxparams(d['opaque_color_map'], p, 'Color Map', )
            
                p.setByte('Shininess Type', d['opaque_shininess_type'])
                p.setFloat('Shininess', d['opaque_shininess'])
                texture_data_to_mxparams(d['opaque_shininess_map'], p, 'Shininess Map', )
            
                p.setByte('Roughness Type', d['opaque_roughness_type'])
                p.setFloat('Roughness', d['opaque_roughness'])
                texture_data_to_mxparams(d['opaque_roughness_map'], p, 'Roughness Map', )
            
                p.setByte('Clearcoat', d['opaque_clearcoat'])
            
            elif(d['use'] == 'TRANSPARENT'):
                e = m.createDefaultMaterialModifierExtension('Transparent')
                p = e.getExtensionData()
            
                p.setByte('Color Type', d['transparent_color_type'])
                c = Crgb8()
                c.assign(*d['transparent_color'])
                p.setRgb('Color', c.toRGB())
                texture_data_to_mxparams(d['transparent_color_map'], p, 'Color Map', )
            
                p.setFloat('Ior', d['transparent_ior'])
                p.setFloat('Transparency', d['transparent_transparency'])
            
                p.setByte('Roughness Type', d['transparent_roughness_type'])
                p.setFloat('Roughness', d['transparent_roughness'])
                texture_data_to_mxparams(d['transparent_roughness_map'], p, 'Roughness Map', )
            
                p.setFloat('Specular Tint', d['transparent_specular_tint'])
                p.setFloat('Dispersion', d['transparent_dispersion'])
                p.setByte('Clearcoat', d['transparent_clearcoat'])
            
            elif(d['use'] == 'METAL'):
                e = m.createDefaultMaterialModifierExtension('Metal')
                p = e.getExtensionData()
            
                p.setUInt('IOR', d['metal_ior'])
            
                p.setFloat('Tint', d['metal_tint'])
            
                p.setByte('Color Type', d['metal_color_type'])
                c = Crgb8()
                c.assign(*d['metal_color'])
                p.setRgb('Color', c.toRGB())
                texture_data_to_mxparams(d['metal_color_map'], p, 'Color Map', )
            
                p.setByte('Roughness Type', d['metal_roughness_type'])
                p.setFloat('Roughness', d['metal_roughness'])
                texture_data_to_mxparams(d['metal_roughness_map'], p, 'Roughness Map', )
            
                p.setByte('Anisotropy Type', d['metal_anisotropy_type'])
                p.setFloat('Anisotropy', d['metal_anisotropy'])
                texture_data_to_mxparams(d['metal_anisotropy_map'], p, 'Anisotropy Map', )
            
                p.setByte('Angle Type', d['metal_angle_type'])
                p.setFloat('Angle', d['metal_angle'])
                texture_data_to_mxparams(d['metal_angle_map'], p, 'Angle Map', )
            
                p.setByte('Dust Type', d['metal_dust_type'])
                p.setFloat('Dust', d['metal_dust'])
                texture_data_to_mxparams(d['metal_dust_map'], p, 'Dust Map', )
            
                p.setByte('Perforation Enabled', d['metal_perforation_enabled'])
                texture_data_to_mxparams(d['metal_perforation_map'], p, 'Perforation Map', )
            
            elif(d['use'] == 'TRANSLUCENT'):
                e = m.createDefaultMaterialModifierExtension('Translucent')
                p = e.getExtensionData()
            
                p.setFloat('Scale', d['translucent_scale'])
                p.setFloat('Ior', d['translucent_ior'])
            
                p.setByte('Color Type', d['translucent_color_type'])
                c = Crgb8()
                c.assign(*d['translucent_color'])
                p.setRgb('Color', c.toRGB())
                texture_data_to_mxparams(d['translucent_color_map'], p, 'Color Map', )
            
                p.setFloat('Hue Shift', d['translucent_hue_shift'])
                p.setByte('Invert Hue', d['translucent_invert_hue'])
                p.setFloat('Vibrance', d['translucent_vibrance'])
                p.setFloat('Density', d['translucent_density'])
                p.setFloat('Opacity', d['translucent_opacity'])
            
                p.setByte('Roughness Type', d['translucent_roughness_type'])
                p.setFloat('Roughness', d['translucent_roughness'])
                texture_data_to_mxparams(d['translucent_roughness_map'], p, 'Roughness Map', )
            
                p.setFloat('Specular Tint', d['translucent_specular_tint'])
                p.setByte('Clearcoat', d['translucent_clearcoat'])
                p.setFloat('Clearcoat Ior', d['translucent_clearcoat_ior'])
            
            elif(d['use'] == 'CARPAINT'):
                e = m.createDefaultMaterialModifierExtension('Car Paint')
                p = e.getExtensionData()
            
                c = Crgb8()
                c.assign(*d['carpaint_color'])
                p.setRgb('Color', c.toRGB())
            
                p.setFloat('Metallic', d['carpaint_metallic'])
                p.setFloat('Topcoat', d['carpaint_topcoat'])
            
            elif(d['use'] == 'HAIR'):
                e = m.createDefaultMaterialModifierExtension('Hair')
                p = e.getExtensionData()
                
                p.setByte('Color Type', d['hair_color_type'])
                
                c = Crgb8()
                c.assign(*d['hair_color'])
                p.setRgb('Color', c.toRGB())
                texture_data_to_mxparams(d['hair_color_map'], p, 'Color Map', )
                
                texture_data_to_mxparams(d['hair_root_tip_map'], p, 'Root-Tip Map', )
                
                p.setByte('Root-Tip Weight Type', d['hair_root_tip_weight_type'])
                p.setFloat('Root-Tip Weight', d['hair_root_tip_weight'])
                texture_data_to_mxparams(d['hair_root_tip_weight_map'], p, 'Root-Tip Weight Map', )
                
                p.setFloat('Primary Highlight Strength', d['hair_primary_highlight_strength'])
                p.setFloat('Primary Highlight Spread', d['hair_primary_highlight_spread'])
                c = Crgb8()
                c.assign(*d['hair_primary_highlight_tint'])
                p.setRgb('Primary Highlight Tint', c.toRGB())
                
                p.setFloat('Secondary Highlight Strength', d['hair_secondary_highlight_strength'])
                p.setFloat('Secondary Highlight Spread', d['hair_secondary_highlight_spread'])
                c = Crgb8()
                c.assign(*d['hair_secondary_highlight_tint'])
                p.setRgb('Secondary Highlight Tint', c.toRGB())
            
            m = s.createMaterial(d['name'])
            m.applyMaterialModifierExtension(p)
            
            # global properties
            if(d['override_map']):
                t = texture(d['override_map'], s, )
                m.setGlobalMap(t)
            
            if(d['bump']):
                a = Cattribute()
                a.activeType = MAP_TYPE_BITMAP
                a.textureMap = texture(d['bump_map'], s, )
                a.value = d['bump_value']
                m.setAttribute('bump', a)
            
            m.setDispersion(d['dispersion'])
            m.setMatteShadow(d['shadow'])
            m.setMatte(d['matte'])
            
            m.setNestedPriority(d['priority'])
            
            c = Crgb()
            cc = [c / 255 for c in d['id']]
            c.assign(*cc)
            m.setColorID(c)
            
            return m
    else:
        raise TypeError("Material '{}' {} is unknown type".format(d['name'], d['subtype']))


def texture(d, s, ):
    t = CtextureMap()
    t.setPath(d['path'])
    
    t.uvwChannelID = d['channel']
    
    t.brightness = d['brightness'] / 100
    t.contrast = d['contrast'] / 100
    t.saturation = d['saturation'] / 100
    t.hue = d['hue'] / 180
    
    t.useGlobalMap = d['use_global_map']
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
    t.clampMin = d['rgb_clamp'][0] / 255
    t.clampMax = d['rgb_clamp'][1] / 255
    
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


def texture_data_to_mxparams(d, mp, name, ):
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
    
    t.brightness = d['brightness'] / 100
    t.contrast = d['contrast'] / 100
    t.hue = d['hue'] / 180
    t.saturation = d['saturation'] / 100
    
    t.clampMin = d['rgb_clamp'][0] / 255
    t.clampMax = d['rgb_clamp'][1] / 255
    
    t.useGlobalMap = d['use_global_map']
    # t.cosA = 1.000000
    # t.sinA = 0.000000
    ok = mp.setTextureMap(name, t)
    
    return mp


def main(args):
    log("loading data..", 2)
    with open(args.data_path, 'r') as f:
        data = json.load(f)
    
    log("creating material..", 2)
    mxs = Cmaxwell(mwcallback)
    
    m = CextensionManager.instance()
    m.loadAllExtensions()
    
    m = material(data, mxs, )
    if(m is not None):
        m.write(args.result_path)
    else:
        raise RuntimeError("Something unexpected happened..")
    
    log("done.", 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''Make Maxwell Extension Material from serialized data'''), epilog='',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('pymaxwell_path', type=str, help='path to directory containing pymaxwell')
    parser.add_argument('log_file', type=str, help='path to log file')
    parser.add_argument('data_path', type=str, help='path to serialized material data file')
    parser.add_argument('result_path', type=str, help='path to result .mxs')
    args = parser.parse_args()
    
    PYMAXWELL_PATH = args.pymaxwell_path
    
    try:
        from pymaxwell import *
    except ImportError:
        sys.path.insert(0, PYMAXWELL_PATH)
        from pymaxwell import *
    
    LOG_FILE_PATH = args.log_file
    
    try:
        main(args)
    except Exception as e:
        import traceback
        m = traceback.format_exc()
        log(m)
        sys.exit(1)
    sys.exit(0)
