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

bl_info = {"name": "Maxwell Render",
           "description": "Maxwell Render integration",
           "author": "Jakub Uhlik",
           "version": (0, 3, 0),
           "blender": (2, 74, 0),
           "location": "Info header > render engine menu",
           "warning": "Alpha",
           "wiki_url": "https://github.com/uhlik/render_maxwell/wiki",
           "tracker_url": "https://github.com/uhlik/render_maxwell/issues",
           "category": "Render", }


if "bpy" in locals():
    import imp
    imp.reload(log)
    imp.reload(system)
    imp.reload(rfbin)
    imp.reload(mxs)
    imp.reload(maths)
    imp.reload(utils)
    imp.reload(engine)
    imp.reload(props)
    imp.reload(ops)
    imp.reload(ui)
    imp.reload(export)
    imp.reload(import_mxs)
else:
    from . import log
    from . import system
    from . import rfbin
    from . import mxs
    from . import maths
    from . import utils
    from . import engine
    from . import props
    from . import ops
    from . import ui
    from . import export
    from . import import_mxs


import os
import platform

import bpy
from bpy.props import StringProperty


class MaxwellRenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    python34_path = StringProperty(name="Python 3.4 Directory", default="", subtype='DIR_PATH', description="", )
    maxwell_path = StringProperty(name="Maxwell Render Directory", default="", subtype='DIR_PATH', description="", )
    
    def draw(self, context):
        l = self.layout
        s = platform.system()
        if(s == 'Darwin'):
            l.prop(self, "python34_path")
        l.prop(self, "maxwell_path")


def get_selected_panels():
    l = ['DATA_PT_camera_display', 'bl_ui.properties_data_mesh', 'bl_ui.properties_particle',
         'bl_ui.properties_render_layer', 'bl_ui.properties_texture', 'bl_ui.properties_scene', ]
    e = ['RENDERLAYER_PT_layer_options', 'RENDERLAYER_PT_layer_passes', 'RENDERLAYER_UL_renderlayers',
         'SCENE_PT_color_management', ]
    a = get_all_panels()
    r = []
    for p in a:
        if(p.__name__ in l or p.__module__ in l):
            if(p.__name__ not in e and p.__module__ not in e):
                r.append(p)
    return r


def get_all_panels():
    ts = dir(bpy.types)
    r = []
    for t in ts:
        o = getattr(bpy.types, t)
        if(hasattr(o, 'COMPAT_ENGINES')):
            if('BLENDER_RENDER' in o.COMPAT_ENGINES):
                r.append(o)
    return r


def get_default_presets():
    # TODO: have a look at presets if they are still the same or updated
    presets = {
        'exposure': {
            'subdirs': False,
            'defines': [
                "import bpy",
                "m = bpy.context.camera.maxwell_render",
            ],
            'presets': {
                'dark_interior': {'shutter': 10.0, 'fstop': 5.6, },
                'bright_interior': {'shutter': 50.0, 'fstop': 5.6, },
                'overcast_exterior': {'shutter': 200.0, 'fstop': 5.6, },
                'bright_exterior': {'shutter': 500.0, 'fstop': 5.6, },
                'night_exterior': {'shutter': 20.0, 'fstop': 5.6, },
            }
        },
        'material': {
            'subdirs': True,
            'defines': [
                "import bpy",
                "m = bpy.context.object.active_material.maxwell_material_extension",
            ],
            'presets': {
                'opaque': {
                    'white_clay': {'opaque_color_type': False, 'opaque_color': (220 / 255, 220 / 255, 220 / 255), 'opaque_color_map': "", 'opaque_shininess_type': False, 'opaque_shininess': 40.0, 'opaque_shininess_map': "", 'opaque_roughness_type': False, 'opaque_roughness': 25.0, 'opaque_roughness_map': "", 'opaque_clearcoat': False, },
                },
                'transparent': {
                    'high_grade_glass': {'transparent_color_type': False, 'transparent_color': (182 / 255, 182 / 255, 182 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 30, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'low_grade_glass': {'transparent_color_type': False, 'transparent_color': (204 / 255, 220 / 255, 194 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 20, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'brown_bottle_glass': {'transparent_color_type': False, 'transparent_color': (236 / 255, 170 / 255, 0 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 0.2, 'transparent_roughness_type': 0, 'transparent_roughness': 5, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'green_bottle_glass': {'transparent_color_type': False, 'transparent_color': (212 / 255, 236 / 255, 0 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 0.2, 'transparent_roughness_type': 0, 'transparent_roughness': 5, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'turquoise_glassware': {'transparent_color_type': False, 'transparent_color': (115 / 255, 226 / 255, 234 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 3, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'frosted_clear_glass': {'transparent_color_type': False, 'transparent_color': (182 / 255, 182 / 255, 182 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 30, 'transparent_roughness_type': 0, 'transparent_roughness': 100, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'frosted_color_glass': {'transparent_color_type': False, 'transparent_color': (220 / 255, 0 / 255, 0 / 255), 'transparent_color_map': "", 'transparent_ior': 1.51, 'transparent_transparency': 30, 'transparent_roughness_type': 0, 'transparent_roughness': 100, 'transparent_roughness_map': "", 'transparent_specular_tint': 30, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'water': {'transparent_color_type': False, 'transparent_color': (255 / 255, 255 / 255, 255 / 255), 'transparent_color_map': "", 'transparent_ior': 1.33, 'transparent_transparency': 0, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                    'ice': {'transparent_color_type': False, 'transparent_color': (255 / 255, 255 / 255, 255 / 255), 'transparent_color_map': "", 'transparent_ior': 1.33, 'transparent_transparency': 30, 'transparent_roughness_type': 0, 'transparent_roughness': 70, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': True, },
                    'diamond': {'transparent_color_type': False, 'transparent_color': (220 / 255, 220 / 255, 220 / 255), 'transparent_color_map': "", 'transparent_ior': 2.41, 'transparent_transparency': 30, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 44.7, 'transparent_clearcoat': False, },
                    'ruby': {'transparent_color_type': False, 'transparent_color': (162 / 255, 0 / 255, 0 / 255), 'transparent_color_map': "", 'transparent_ior': 1.76, 'transparent_transparency': 3, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 27.8, 'transparent_clearcoat': False, },
                    'emerald': {'transparent_color_type': False, 'transparent_color': (0 / 255, 162 / 255, 0 / 255), 'transparent_color_map': "", 'transparent_ior': 1.57, 'transparent_transparency': 3, 'transparent_roughness_type': 0, 'transparent_roughness': 0, 'transparent_roughness_map': "", 'transparent_specular_tint': 0, 'transparent_dispersion': 0, 'transparent_clearcoat': False, },
                },
                'metal': {
                    'aluminium': {'metal_ior': "0", 'metal_color_type': False, 'metal_color': (167 / 255, 167 / 255, 168 / 255), 'metal_color_map': "", 'metal_tint': 0.0, 'metal_roughness_type': 0, 'metal_roughness': 30.0, 'metal_roughness_map': "", 'metal_anisotropy_type': 0, 'metal_anisotropy': 0, 'metal_anisotropy_map': "", 'metal_angle_type': 0, 'metal_angle': 0, 'metal_angle_map': "", 'metal_dust_type': 0, 'metal_dust': 0, 'metal_dust_map': "", 'metal_perforation_enabled': False, 'metal_perforation_map': "", },
                    '24k_jewelry_gold': {'metal_ior': "5", 'metal_color_type': False, 'metal_color': (206 / 255, 90 / 255, 7 / 255), 'metal_color_map': "", 'metal_tint': 0.0, 'metal_roughness_type': 0, 'metal_roughness': 0.0, 'metal_roughness_map': "", 'metal_anisotropy_type': 0, 'metal_anisotropy': 0, 'metal_anisotropy_map': "", 'metal_angle_type': 0, 'metal_angle': 0, 'metal_angle_map': "", 'metal_dust_type': 0, 'metal_dust': 0, 'metal_dust_map': "", 'metal_perforation_enabled': False, 'metal_perforation_map': "", },
                    'mirror': {'metal_ior': "8", 'metal_color_type': False, 'metal_color': (255 / 255, 255 / 255, 255 / 255), 'metal_color_map': "", 'metal_tint': 0.0, 'metal_roughness_type': 0, 'metal_roughness': 0.0, 'metal_roughness_map': "", 'metal_anisotropy_type': 0, 'metal_anisotropy': 0, 'metal_anisotropy_map': "", 'metal_angle_type': 0, 'metal_angle': 0, 'metal_angle_map': "", 'metal_dust_type': 0, 'metal_dust': 0, 'metal_dust_map': "", 'metal_perforation_enabled': False, 'metal_perforation_map': "", },
                },
                'translucent': {
                    'silicone_gel': {'translucent_scale': 8.0, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (250 / 255, 245 / 255, 230 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 0.0, 'translucent_invert_hue': True, 'translucent_vibrance': 11, 'translucent_density': 90, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 17, 'translucent_roughness_map': "", 'translucent_specular_tint': 0.0, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'polyurethane': {'translucent_scale': 0.2, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (236 / 255, 220 / 255, 122 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 19, 'translucent_invert_hue': False, 'translucent_vibrance': 10, 'translucent_density': 20, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 35, 'translucent_roughness_map': "", 'translucent_specular_tint': 20, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'orange_juice': {'translucent_scale': 0.8, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (232 / 255, 169 / 255, 52 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 34, 'translucent_invert_hue': False, 'translucent_vibrance': 45, 'translucent_density': 50, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 0, 'translucent_roughness_map': "", 'translucent_specular_tint': 20, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'honey': {'translucent_scale': 0.7, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (191 / 255, 121 / 255, 10 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 0, 'translucent_invert_hue': False, 'translucent_vibrance': 30, 'translucent_density': 20, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 0, 'translucent_roughness_map': "", 'translucent_specular_tint': 0, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'caoutchouc': {'translucent_scale': 0.3, 'translucent_ior': 1.2, 'translucent_color_type': False, 'translucent_color': (195 / 255, 147 / 255, 5 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 20, 'translucent_invert_hue': False, 'translucent_vibrance': 20, 'translucent_density': 30, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 0, 'translucent_roughness_map': "", 'translucent_specular_tint': 20, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'flint': {'translucent_scale': 1.5, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (242 / 255, 234 / 255, 217 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 0, 'translucent_invert_hue': True, 'translucent_vibrance': 7, 'translucent_density': 90, 'translucent_opacity': 75, 'translucent_roughness_type': False, 'translucent_roughness': 20, 'translucent_roughness_map': "", 'translucent_specular_tint': 0, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'milk': {'translucent_scale': 0.5, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (216 / 255, 210 / 255, 193 / 255), 'translucent_color_map': "", 'translucent_hue_shift': -10, 'translucent_invert_hue': True, 'translucent_vibrance': 8, 'translucent_density': 80, 'translucent_opacity': 80, 'translucent_roughness_type': False, 'translucent_roughness': 0, 'translucent_roughness_map': "", 'translucent_specular_tint': 0, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'wax_red': {'translucent_scale': 0.2, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (90 / 255, 1 / 255, 4 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 0, 'translucent_invert_hue': False, 'translucent_vibrance': 25, 'translucent_density': 40, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 40, 'translucent_roughness_map': "", 'translucent_specular_tint': 20, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'rubber_blue': {'translucent_scale': 1, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (6 / 255, 36 / 255, 204 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 10, 'translucent_invert_hue': False, 'translucent_vibrance': 25, 'translucent_density': 80, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 100, 'translucent_roughness_map': "", 'translucent_specular_tint': 80, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'rubber_lime': {'translucent_scale': 1, 'translucent_ior': 1.3, 'translucent_color_type': False, 'translucent_color': (200 / 255, 233 / 255, 2 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 10, 'translucent_invert_hue': False, 'translucent_vibrance': 10, 'translucent_density': 50, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 30, 'translucent_roughness_map': "", 'translucent_specular_tint': 80, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'vapor': {'translucent_scale': 1, 'translucent_ior': 1.001, 'translucent_color_type': False, 'translucent_color': (255 / 255, 255 / 255, 255 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 0, 'translucent_invert_hue': False, 'translucent_vibrance': 0, 'translucent_density': 30, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 0, 'translucent_roughness_map': "", 'translucent_specular_tint': 0, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                    'smoke': {'translucent_scale': 1, 'translucent_ior': 1.001, 'translucent_color_type': False, 'translucent_color': (1 / 255, 1 / 255, 1 / 255), 'translucent_color_map': "", 'translucent_hue_shift': 0, 'translucent_invert_hue': False, 'translucent_vibrance': 0, 'translucent_density': 30, 'translucent_opacity': 50, 'translucent_roughness_type': False, 'translucent_roughness': 0, 'translucent_roughness_map': "", 'translucent_specular_tint': 0, 'translucent_clearcoat': False, 'translucent_clearcoat_ior': 1.3, },
                },
                'carpaint': {
                    'cherry_metallic': {'carpaint_color': (100 / 255, 0 / 255, 16 / 255), 'carpaint_metallic': 100.0, 'carpaint_topcoat': 50.0, },
                },
                'emitter': {
                    'incandescent_lamp_40w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 2700.0, 'emitter_luminance': '0', 'emitter_luminance_power': 40.0, 'emitter_luminance_efficacy': 10.8, 'emitter_luminance_output': 430.0, },
                    'incandescent_lamp_60w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 2700.0, 'emitter_luminance': '0', 'emitter_luminance_power': 60.0, 'emitter_luminance_efficacy': 11.5, 'emitter_luminance_output': 690.0, },
                    'incandescent_lamp_100w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 2700.0, 'emitter_luminance': '0', 'emitter_luminance_power': 100.0, 'emitter_luminance_efficacy': 13.8, 'emitter_luminance_output': 1380.0, },
                    'compact_fluorescent_lamp_warm_7w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 7.0, 'emitter_luminance_efficacy': 57.1, 'emitter_luminance_output': 399.7, },
                    'compact_fluorescent_lamp_warm_9w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 9.0, 'emitter_luminance_efficacy': 66.7, 'emitter_luminance_output': 600.3, },
                    'compact_fluorescent_lamp_cold_7w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 5000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 7.0, 'emitter_luminance_efficacy': 57.1, 'emitter_luminance_output': 399.7, },
                    'compact_fluorescent_lamp_cold_9w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 5000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 9.0, 'emitter_luminance_efficacy': 66.7, 'emitter_luminance_output': 600.3, },
                    'tubular_fluorescent_lamp_warm_20w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 20.0, 'emitter_luminance_efficacy': 51.5, 'emitter_luminance_output': 1030, },
                    'tubular_fluorescent_lamp_warm_40w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 40.0, 'emitter_luminance_efficacy': 65.0, 'emitter_luminance_output': 2600, },
                    'tubular_fluorescent_lamp_warm_65w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 65.0, 'emitter_luminance_efficacy': 63.0, 'emitter_luminance_output': 4095, },
                    'tubular_fluorescent_lamp_midrange_20w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 4500.0, 'emitter_luminance': '0', 'emitter_luminance_power': 20.0, 'emitter_luminance_efficacy': 51.5, 'emitter_luminance_output': 1030, },
                    'tubular_fluorescent_lamp_midrange_40w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 4500.0, 'emitter_luminance': '0', 'emitter_luminance_power': 40.0, 'emitter_luminance_efficacy': 65.0, 'emitter_luminance_output': 2600, },
                    'tubular_fluorescent_lamp_midrange_65w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 4500.0, 'emitter_luminance': '0', 'emitter_luminance_power': 65.0, 'emitter_luminance_efficacy': 63.0, 'emitter_luminance_output': 4095, },
                    'tubular_fluorescent_lamp_cold_20w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 20.0, 'emitter_luminance_efficacy': 51.5, 'emitter_luminance_output': 1030, },
                    'tubular_fluorescent_lamp_cold_40w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 40.0, 'emitter_luminance_efficacy': 65.0, 'emitter_luminance_output': 2600, },
                    'tubular_fluorescent_lamp_cold_65w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 65.0, 'emitter_luminance_efficacy': 63.0, 'emitter_luminance_output': 4095, },
                    'high_pressure_mercury_lamp_250w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3500.0, 'emitter_luminance': '0', 'emitter_luminance_power': 250.0, 'emitter_luminance_efficacy': 54.0, 'emitter_luminance_output': 13500.0, },
                    'high_pressure_mercury_lamp_400w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3500.0, 'emitter_luminance': '0', 'emitter_luminance_power': 400.0, 'emitter_luminance_efficacy': 57.5, 'emitter_luminance_output': 23000.0, },
                    'high_pressure_mercury_lamp_700w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3500.0, 'emitter_luminance': '0', 'emitter_luminance_power': 700.0, 'emitter_luminance_efficacy': 60.0, 'emitter_luminance_output': 42000.0, },
                    'high_pressure_sodium_lamp_250w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 2300.0, 'emitter_luminance': '0', 'emitter_luminance_power': 250.0, 'emitter_luminance_efficacy': 100.0, 'emitter_luminance_output': 25000.0, },
                    'high_pressure_sodium_lamp_400w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 2300.0, 'emitter_luminance': '0', 'emitter_luminance_power': 400.0, 'emitter_luminance_efficacy': 118.0, 'emitter_luminance_output': 47200.0, },
                    'high_pressure_sodium_lamp_1000w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 2300.0, 'emitter_luminance': '0', 'emitter_luminance_power': 1000.0, 'emitter_luminance_efficacy': 120.0, 'emitter_luminance_output': 120000.0, },
                    'low_pressure_sodium_lamp_55w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 1800.0, 'emitter_luminance': '0', 'emitter_luminance_power': 55.0, 'emitter_luminance_efficacy': 145.0, 'emitter_luminance_output': 7975.0, },
                    'low_pressure_sodium_lamp_135w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 1800.0, 'emitter_luminance': '0', 'emitter_luminance_power': 135.0, 'emitter_luminance_efficacy': 167.0, 'emitter_luminance_output': 22545.0, },
                    'low_pressure_sodium_lamp_180w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 1800.0, 'emitter_luminance': '0', 'emitter_luminance_power': 180.0, 'emitter_luminance_efficacy': 180.0, 'emitter_luminance_output': 32400.0, },
                    'tungsten_halogen_low_tension_lamp_20w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 20.0, 'emitter_luminance_efficacy': 16.0, 'emitter_luminance_output': 320.0, },
                    'tungsten_halogen_low_tension_lamp_35w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 35.0, 'emitter_luminance_efficacy': 17.0, 'emitter_luminance_output': 595.0, },
                    'tungsten_halogen_low_tension_lamp_50w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 50.0, 'emitter_luminance_efficacy': 18.2, 'emitter_luminance_output': 910.0, },
                    'tungsten_halogen_tension_lamp_40w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 40.0, 'emitter_luminance_efficacy': 12.2, 'emitter_luminance_output': 490.0, },
                    'tungsten_halogen_tension_lamp_60w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 60.0, 'emitter_luminance_efficacy': 14.0, 'emitter_luminance_output': 840.0, },
                    'tungsten_halogen_tension_lamp_100w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 100.0, 'emitter_luminance_efficacy': 16.0, 'emitter_luminance_output': 1600.0, },
                    'tungsten_halogen_tension_lamp_150w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 3000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 150.0, 'emitter_luminance_efficacy': 17.0, 'emitter_luminance_output': 2550.0, },
                    'metal_halide_hmi_lamp_200w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 200.0, 'emitter_luminance_efficacy': 80.0, 'emitter_luminance_output': 16000.0, },
                    'metal_halide_hmi_lamp_400w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 400.0, 'emitter_luminance_efficacy': 82.5, 'emitter_luminance_output': 33000.0, },
                    'metal_halide_hmi_lamp_575w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 575.0, 'emitter_luminance_efficacy': 85.2, 'emitter_luminance_output': 48990.0, },
                    'metal_halide_hmi_lamp_1200w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 1200.0, 'emitter_luminance_efficacy': 91.6, 'emitter_luminance_output': 109920.0, },
                    'metal_halide_hmi_lamp_2500w': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 6000.0, 'emitter_luminance': '0', 'emitter_luminance_power': 2500.0, 'emitter_luminance_efficacy': 96.0, 'emitter_luminance_output': 240000.0, },
                    'candle': {'emitter_color': (255 / 255, 255 / 255, 255 / 255), 'emitter_color_black_body_enabled': False, 'emitter_color_black_body': 1200.0, 'emitter_luminance': '0', 'emitter_luminance_power': 40.0, 'emitter_luminance_efficacy': 0.3, 'emitter_luminance_output': 12.4, },
                },
            },
        },
    }
    return presets


def setup():
    # make all subdirs for presets
    pd = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets", "maxwell_render")
    l = ['camera', 'channels', 'environment', 'exposure', 'material', 'render', ]
    for d in l:
        p = os.path.join(pd, d)
        if(not os.path.exists(p)):
            os.makedirs(p)
    
    defaults = get_default_presets()
    for subdir, presets in defaults.items():
        preset_subdir = os.path.join("maxwell_render", subdir)
        preset_directory = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets", preset_subdir)
        preset_paths = bpy.utils.preset_paths(preset_subdir)
        if(preset_directory not in preset_paths):
            if(not os.path.exists(preset_directory)):
                os.makedirs(preset_directory)
        
        # search for presets, .py file is considered as preset
        def walk(p):
            r = {'files': [], 'dirs': [], }
            for(root, dirs, files) in os.walk(p):
                r['files'].extend(files)
                r['dirs'].extend(dirs)
                break
            return r
        
        subdirs = presets['subdirs']
        defines = presets['defines']
        if(subdirs):
            for k, v in presets['presets'].items():
                found = []
                p = os.path.join(preset_directory, k)
                if(not os.path.exists(p)):
                    os.makedirs(p)
                c = walk(p)
                for f in c['files']:
                    if(f.endswith(".py")):
                        found.append(f[:-3])
                for k2, v2 in v.items():
                    if(k2 not in found):
                        e = "\n"
                        s = ""
                        for i in range(len(defines)):
                            s += defines[i] + e
                        for k3, v3 in v2.items():
                            if(type(v3) is str and v3 != ""):
                                s += 'm.{} = "{}"{}'.format(k3, v3, e)
                            elif(v3 == ""):
                                s += 'm.{} = ""{}'.format(k3, e)
                            else:
                                s += 'm.{} = {}{}'.format(k3, v3, e)
                        with open(os.path.join(p, "{}.py".format(k2)), mode='w', encoding='utf-8') as f:
                            f.write(s)
        else:
            found = []
            p = preset_directory
            c = walk(p)
            for f in c['files']:
                if(f.endswith(".py")):
                    found.append(f[:-3])
            for k, v in presets['presets'].items():
                if(k not in found):
                    e = "\n"
                    s = ""
                    for i in range(len(defines)):
                        s += defines[i] + e
                    for k3, v3 in v.items():
                        if(type(v3) is str and v3 != ""):
                            s += 'm.{} = "{}"{}'.format(k3, v3, e)
                        elif(v3 == ""):
                            s += 'm.{} = ""{}'.format(k3, e)
                        else:
                            s += 'm.{} = {}{}'.format(k3, v3, e)
                    with open(os.path.join(p, "{}.py".format(k)), mode='w', encoding='utf-8') as f:
                        f.write(s)


def register():
    setup()
    
    # bpy.utils.register_module(__name__, verbose=True)
    bpy.utils.register_module(__name__)
    
    # get preferences
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    s = platform.system()
    if(p.python34_path == ''):
        if(s == 'Darwin'):
            py = '/Library/Frameworks/Python.framework/Versions/3.4/'
        elif(s == 'Linux'):
            py = '/usr/bin/'
        elif(s == 'Windows'):
            py = ""
        else:
            raise OSError("Unknown platform: {}.".format(s))
        p.python34_path = py
    else:
        # user set something, leave it as it is
        pass
    
    if(p.maxwell_path == ''):
        if(s == 'Darwin'):
            mx = '/Applications/Maxwell 3/'
        elif(s == 'Linux'):
            mx = os.environ.get("MAXWELL3_ROOT")
        elif(s == 'Windows'):
            mx = os.environ.get("MAXWELL3_ROOT")
        else:
            raise OSError("Unknown platform: {}.".format(s))
        p.maxwell_path = mx
    else:
        # user set something, leave it as it is
        pass
    
    # for p in get_all_panels():
    for p in get_selected_panels():
        p.COMPAT_ENGINES.add(engine.MaxwellRenderExportEngine.bl_idname)


def unregister():
    # bpy.utils.unregister_module(__name__, verbose=True)
    bpy.utils.unregister_module(__name__)
    
    # for p in get_all_panels():
    for p in get_selected_panels():
        p.COMPAT_ENGINES.remove(engine.MaxwellRenderExportEngine.bl_idname)


if __name__ == "__main__":
    register()
    
    # oh, btw, run this from time to time..
    # pep8 --ignore=W293,E501 .
