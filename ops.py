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
import shlex
import subprocess

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty
from bpy.types import Operator
from mathutils import Vector
from bl_operators.presets import AddPresetBase
from bpy_extras.io_utils import ImportHelper

from . import maths
from . import system
from . import import_mxs


class ImportMXS(Operator, ImportHelper):
    bl_idname = "maxwell_render.import_mxs"
    bl_label = 'Import MXS'
    bl_description = 'Import Maxwell Render Scene (.MXS)'
    
    filename_ext = ".mxs"
    filter_glob = StringProperty(default="*.mxs", options={'HIDDEN'}, )
    keep_intermediates = BoolProperty(name="Keep Intermediates", description="Keep intermediate products", default=False, )
    check_extension = True
    
    objects = BoolProperty(name="Objects", default=True, )
    cameras = BoolProperty(name="Cameras", default=True, )
    sun = BoolProperty(name="Sun (as Sun Lamp)", default=True, )
    
    def draw(self, context):
        l = self.layout
        
        sub = l.column()
        sub.prop(self, 'objects')
        sub.prop(self, 'cameras')
        sub.prop(self, 'sun')
        
        if(system.PLATFORM == 'Darwin'):
            l.separator()
            l.prop(self, 'keep_intermediates')
    
    def execute(self, context):
        if(not self.objects and not self.cameras and not self.sun):
            return {'CANCELLED'}
        
        if(system.PLATFORM == 'Darwin'):
            d = {'mxs_path': self.filepath,
                 'objects': self.objects,
                 'cameras': self.cameras,
                 'sun': self.sun,
                 'keep_intermediates': self.keep_intermediates, }
            im = import_mxs.MXSImportLegacy(**d)
            
        elif(system.PLATFORM == 'Linux'):
            self.report({'WARNING'}, "Not available yet..")
        elif(system.PLATFORM == 'Windows'):
            self.report({'WARNING'}, "Not available yet..")
        else:
            pass
        
        return {'FINISHED'}
    
    @classmethod
    def register(cls):
        bpy.types.INFO_MT_file_import.append(menu_func_import)
    
    @classmethod
    def unregister(cls):
        bpy.types.INFO_MT_file_import.remove(menu_func_import)


def menu_func_import(self, context):
    self.layout.operator(ImportMXS.bl_idname, text="Maxwell Render Scene (.mxs)")


class EnvironmentSetSun(Operator):
    bl_idname = "maxwell_render.set_sun"
    bl_label = "Set Sun"
    bl_description = "Set direction from selected Sun lamp"
    
    @classmethod
    def poll(cls, context):
        o = context.active_object
        return (o and o.type == 'LAMP' and o.data.type == 'SUN')
    
    def execute(self, context):
        m = context.world.maxwell_render
        s = context.active_object
        w = s.matrix_world
        _, r, _ = w.decompose()
        v = Vector((0, 0, 1))
        v.rotate(r)
        m.sun_dir_x = v.x
        m.sun_dir_y = v.y
        m.sun_dir_z = v.z
        return {'FINISHED'}


class EnvironmentNow(Operator):
    bl_idname = "maxwell_render.now"
    bl_label = "Now"
    bl_description = "Set current date and time"
    
    def execute(self, context):
        import datetime
        
        m = context.world.maxwell_render
        d = m.sun_date
        t = m.sun_time
        n = datetime.datetime.now()
        m.sun_date = n.strftime('%d.%m.%Y')
        m.sun_time = n.strftime('%H:%M')
        return {'FINISHED'}


class CameraAutoFocus(Operator):
    bl_idname = "maxwell_render.auto_focus"
    bl_label = "Auto Focus"
    bl_description = "Auto focus camera to closest object in the middle of camera"
    
    @classmethod
    def poll(cls, context):
        o = context.active_object
        return (o and o.type == 'CAMERA')
    
    def execute(self, context):
        s = context.scene
        c = context.active_object
        mw = c.matrix_world
        d = 1000000.0
        e, t, u = maths.eye_target_up_from_matrix(mw, d)
        a = e.copy()
        b = maths.shift_vert_along_normal(a, t, d)
        hit, _, _, loc, _ = s.ray_cast(a, b)
        if(hit):
            c.data.dof_distance = maths.distance_vectors(a, loc)
        else:
            self.report({'WARNING'}, "No object to focus to..")
            return {'CANCELLED'}
        return {'FINISHED'}


class CameraSetRegion(Operator):
    bl_idname = "maxwell_render.camera_set_region"
    bl_label = "Render Border > Region"
    bl_description = "Copy render border (x, y, width, height) to render region"
    
    def execute(self, context):
        rp = context.scene.render
        x_res = int(rp.resolution_x * rp.resolution_percentage / 100.0)
        y_res = int(rp.resolution_y * rp.resolution_percentage / 100.0)
        x = int(x_res * rp.border_min_x)
        h = y_res - int(y_res * rp.border_min_y)
        w = int(x_res * rp.border_max_x)
        y = y_res - int(y_res * rp.border_max_y)
        m = context.camera.maxwell_render
        m.screen_region_x = x
        m.screen_region_y = y
        m.screen_region_w = w
        m.screen_region_h = h
        return {'FINISHED'}


class CameraResetRegion(Operator):
    bl_idname = "maxwell_render.camera_reset_region"
    bl_label = "Reset Region"
    bl_description = "Reset render region"
    
    def execute(self, context):
        rp = context.scene.render
        w = int(rp.resolution_x * rp.resolution_percentage / 100.0)
        h = int(rp.resolution_y * rp.resolution_percentage / 100.0)
        rp.border_min_x = 0
        rp.border_min_y = 0
        rp.border_max_x = w
        rp.border_max_y = h
        m = context.camera.maxwell_render
        m.screen_region_x = 0
        m.screen_region_y = 0
        m.screen_region_w = w
        m.screen_region_h = h
        rp.use_border = False
        return {'FINISHED'}


class CreateMaterial(Operator):
    bl_idname = "maxwell_render.create_material"
    bl_label = "Create Material"
    bl_description = "Launches Mxed material editor"
    
    filepath = StringProperty(subtype='FILE_PATH', )
    filename_ext = ".mxm"
    check_extension = True
    check_existing = BoolProperty(name="", default=True, options={'HIDDEN'}, )
    remove_dots = True
    
    filter_folder = BoolProperty(name="Filter folders", default=True, options={'HIDDEN'}, )
    filter_glob = StringProperty(default="*.mxm", options={'HIDDEN'}, )
    
    backface = BoolProperty(name="", default=False, options={'HIDDEN'}, )
    
    @classmethod
    def poll(cls, context):
        return (context.material or context.object)
    
    def invoke(self, context, event):
        n = context.material.name
        if(self.remove_dots):
            # remove dots, Maxwell doesn't like it - material name is messed up..
            n = n.replace(".", "_")
        if(self.backface):
            self.filepath = os.path.join(context.scene.maxwell_render.materials_directory, "{}_backface.mxm".format(n))
        else:
            self.filepath = os.path.join(context.scene.maxwell_render.materials_directory, "{}.mxm".format(n))
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def check(self, context):
        change_ext = False
        check_extension = self.check_extension
        
        if(check_extension is not None):
            filepath = self.filepath
            
            if(self.remove_dots):
                h, t = os.path.split(filepath)
                n, e = os.path.splitext(t)
                n = n.replace(".", "_")
                filepath = os.path.join(h, "{}{}".format(n, e))
            
            if(os.path.basename(filepath)):
                filepath = bpy.path.ensure_ext(filepath,
                                               self.filename_ext
                                               if check_extension
                                               else "")
                if(filepath != self.filepath):
                    self.filepath = filepath
                    change_ext = True
        return change_ext
    
    def execute(self, context):
        p = os.path.abspath(bpy.path.abspath(self.filepath))
        
        if(p == ""):
            self.report({'ERROR'}, "Filepath is empty")
            return {'CANCELLED'}
        if(os.path.isdir(p)):
            self.report({'ERROR'}, "Filepath is directory")
            return {'CANCELLED'}
        
        h, t = os.path.split(p)
        n, e = os.path.splitext(t)
        if(e.lower() != ".mxm"):
            self.report({'ERROR'}, "Extension is not .mxm")
            return {'CANCELLED'}
        
        if(not os.path.exists(os.path.dirname(p))):
            self.report({'ERROR'}, "Directory does not exist")
            return {'CANCELLED'}
        
        if(not os.access(os.path.dirname(p), os.W_OK)):
            self.report({'ERROR'}, "Directory is not writeable")
            return {'CANCELLED'}
        
        system.mxed_create_material_helper(p)
        
        if(self.backface):
            context.object.maxwell_render.backface_material_file = bpy.path.relpath(self.filepath)
        else:
            context.material.maxwell_render.mxm_file = bpy.path.relpath(self.filepath)
        return {'FINISHED'}


class EditMaterial(Operator):
    bl_idname = "maxwell_render.edit_material"
    bl_label = "Edit Material"
    bl_description = "Launches Mxed material editor"
    
    backface = BoolProperty(name="", default=False, options={'HIDDEN'}, )
    
    @classmethod
    def poll(cls, context):
        return (context.material or context.object)
    
    def execute(self, context):
        if(self.backface):
            p = os.path.abspath(bpy.path.abspath(context.object.maxwell_render.backface_material_file))
        else:
            p = os.path.abspath(bpy.path.abspath(context.material.maxwell_render.mxm_file))
        
        if(p == ""):
            self.report({'ERROR'}, "Filepath is empty")
            return {'CANCELLED'}
        if(os.path.isdir(p)):
            self.report({'ERROR'}, "Filepath is directory")
            return {'CANCELLED'}
        
        h, t = os.path.split(p)
        n, e = os.path.splitext(t)
        if(e.lower() != ".mxm"):
            self.report({'ERROR'}, "Extension is not .mxm")
            return {'CANCELLED'}
        
        if(not os.path.exists(os.path.dirname(p))):
            self.report({'ERROR'}, "Directory does not exist")
            return {'CANCELLED'}
        
        if(not os.access(os.path.dirname(p), os.W_OK)):
            self.report({'ERROR'}, "Directory is not writeable")
            return {'CANCELLED'}
        
        system.mxed_edit_material_helper(p)
        
        return {'FINISHED'}


class EditExtensionMaterial(Operator):
    bl_idname = "maxwell_render.edit_extension_material"
    bl_label = "Edit Extension Material in Mxed"
    bl_description = "Saves MXM if needed and launches Mxed material editor"
    
    filepath = StringProperty(subtype='FILE_PATH', )
    filename_ext = ".mxm"
    check_extension = True
    check_existing = BoolProperty(name="", default=True, options={'HIDDEN'}, )
    remove_dots = True
    
    filter_folder = BoolProperty(name="Filter folders", default=True, options={'HIDDEN'}, )
    filter_glob = StringProperty(default="*.mxm", options={'HIDDEN'}, )
    
    backface = BoolProperty(name="", default=False, options={'HIDDEN'}, )
    
    @classmethod
    def poll(cls, context):
        return (context.material or context.object)
    
    def invoke(self, context, event):
        n = context.material.name
        if(self.remove_dots):
            # remove dots, Maxwell doesn't like it - material name is messed up..
            n = n.replace(".", "_")
        if(self.backface):
            self.filepath = os.path.join(context.scene.maxwell_render.materials_directory, "{}_backface.mxm".format(n))
        else:
            self.filepath = os.path.join(context.scene.maxwell_render.materials_directory, "{}.mxm".format(n))
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def check(self, context):
        change_ext = False
        check_extension = self.check_extension
        
        if(check_extension is not None):
            filepath = self.filepath
            
            if(self.remove_dots):
                h, t = os.path.split(filepath)
                n, e = os.path.splitext(t)
                n = n.replace(".", "_")
                filepath = os.path.join(h, "{}{}".format(n, e))
            
            if(os.path.basename(filepath)):
                filepath = bpy.path.ensure_ext(filepath,
                                               self.filename_ext
                                               if check_extension
                                               else "")
                if(filepath != self.filepath):
                    self.filepath = filepath
                    change_ext = True
        return change_ext
    
    def execute(self, context):
        p = os.path.abspath(bpy.path.abspath(self.filepath))
        
        if(p == ""):
            self.report({'ERROR'}, "Filepath is empty")
            return {'CANCELLED'}
        if(os.path.isdir(p)):
            self.report({'ERROR'}, "Filepath is directory")
            return {'CANCELLED'}
        
        h, t = os.path.split(p)
        n, e = os.path.splitext(t)
        if(e.lower() != ".mxm"):
            self.report({'ERROR'}, "Extension is not .mxm")
            return {'CANCELLED'}
        
        if(not os.path.exists(os.path.dirname(p))):
            self.report({'ERROR'}, "Directory does not exist")
            return {'CANCELLED'}
        
        if(not os.access(os.path.dirname(p), os.W_OK)):
            self.report({'ERROR'}, "Directory is not writeable")
            return {'CANCELLED'}
        
        # system.mxed_create_material_helper(p)
        #
        # if(self.backface):
        #     context.object.maxwell_render.backface_material_file = bpy.path.relpath(self.filepath)
        # else:
        #     context.material.maxwell_render.mxm_file = bpy.path.relpath(self.filepath)
        
        def ext_material(mat, ob):
            m = mat.maxwell_render
            mx = mat.maxwell_material_extension
            
            def color_to_rgb8(c):
                return tuple([int(255 * v) for v in c])
            
            def texture_to_data(name):
                if(name == ""):
                    return None
                tex = bpy.data.textures[name]
                if(tex.type != 'IMAGE'):
                    return None
                
                m = tex.maxwell_render
                d = {'type': 'IMAGE',
                     'path': bpy.path.abspath(tex.image.filepath),
                     'channel': 0,
                     'use_override_map': m.use_global_map,
                     'tile_method_type': [True, True],
                     'tile_method_units': int(m.tiling_units[-1:]),
                     'repeat': [m.repeat[0], m.repeat[1]],
                     'mirror': [m.mirror_x, m.mirror_y],
                     'offset': [m.offset[0], m.offset[1]],
                     'rotation': m.rotation,
                     'invert': m.invert,
                     'alpha_only': m.use_alpha,
                     'interpolation': m.interpolation,
                     'brightness': m.brightness,
                     'contrast': m.contrast,
                     'saturation': m.saturation,
                     'hue': m.hue,
                     'rgb_clamp': [m.clamp[0], m.clamp[1]], }
                
                if(m.tiling_method == 'NO_TILING'):
                    tm = [False, False]
                elif(m.tiling_method == 'TILE_X'):
                    tm = [True, False]
                elif(m.tiling_method == 'TILE_Y'):
                    tm = [False, True]
                else:
                    tm = [True, True]
                d['tile_method_type'] = tm
                
                slot = None
                for ts in mat.texture_slots:
                    if(ts is not None):
                        if(ts.texture is not None):
                            if(ts.texture.name == name):
                                slot = ts
                                break
                
                for i, uv in enumerate(ob.data.uv_textures):
                    if(uv.name == slot.uv_layer):
                        d['channel'] = i
                        break
                
                return d
            
            if(m.use == 'EMITTER'):
                d = {'type': 'EMITTER',
                     'name': mat.name,
                     'emitter_type': int(mx.emitter_type),
                     'emitter_ies_data': bpy.path.abspath(mx.emitter_ies_data),
                     'emitter_ies_intensity': mx.emitter_ies_intensity,
                     'emitter_spot_map_enabled': mx.emitter_spot_map_enabled,
                     'emitter_spot_map': texture_to_data(mx.emitter_spot_map),
                     'emitter_spot_cone_angle': math.degrees(mx.emitter_spot_cone_angle),
                     'emitter_spot_falloff_angle': math.degrees(mx.emitter_spot_falloff_angle),
                     'emitter_spot_falloff_type': int(mx.emitter_spot_falloff_type),
                     'emitter_spot_blur': mx.emitter_spot_blur,
                     'emitter_emission': int(mx.emitter_emission),
                     'emitter_color': color_to_rgb8(mx.emitter_color),
                     'emitter_color_black_body_enabled': mx.emitter_color_black_body_enabled,
                     'emitter_color_black_body': mx.emitter_color_black_body,
                     'emitter_luminance': int(mx.emitter_luminance),
                     'emitter_luminance_power': mx.emitter_luminance_power,
                     'emitter_luminance_efficacy': mx.emitter_luminance_efficacy,
                     'emitter_luminance_output': mx.emitter_luminance_output,
                     'emitter_temperature_value': mx.emitter_temperature_value,
                     'emitter_hdr_map': texture_to_data(mx.emitter_hdr_map),
                     'emitter_hdr_intensity': mx.emitter_hdr_intensity, }
            elif(m.use == 'AGS'):
                d = {'type': 'AGS',
                     'name': mat.name,
                     'ags_color': color_to_rgb8(mx.ags_color),
                     'ags_reflection': mx.ags_reflection,
                     'ags_type': int(mx.ags_type), }
            elif(m.use == 'OPAQUE'):
                d = {'type': 'OPAQUE',
                     'name': mat.name,
                     'opaque_color_type': mx.opaque_color_type,
                     'opaque_color': color_to_rgb8(mx.opaque_color),
                     'opaque_color_map': texture_to_data(mx.opaque_color_map),
                     'opaque_shininess_type': mx.opaque_shininess_type,
                     'opaque_shininess': mx.opaque_shininess,
                     'opaque_shininess_map': texture_to_data(mx.opaque_shininess_map),
                     'opaque_roughness_type': mx.opaque_roughness_type,
                     'opaque_roughness': mx.opaque_roughness,
                     'opaque_roughness_map': texture_to_data(mx.opaque_roughness_map),
                     'opaque_clearcoat': mx.opaque_clearcoat, }
            elif(m.use == 'TRANSPARENT'):
                d = {'type': 'TRANSPARENT',
                     'name': mat.name,
                     'transparent_color_type': mx.transparent_color_type,
                     'transparent_color': color_to_rgb8(mx.transparent_color),
                     'transparent_color_map': texture_to_data(mx.transparent_color_map),
                     'transparent_ior': mx.transparent_ior,
                     'transparent_transparency': mx.transparent_transparency,
                     'transparent_roughness_type': mx.transparent_roughness_type,
                     'transparent_roughness': mx.transparent_roughness,
                     'transparent_roughness_map': texture_to_data(mx.transparent_roughness_map),
                     'transparent_specular_tint': mx.transparent_specular_tint,
                     'transparent_dispersion': mx.transparent_dispersion,
                     'transparent_clearcoat': mx.transparent_clearcoat, }
            elif(m.use == 'METAL'):
                d = {'type': 'METAL',
                     'name': mat.name,
                     'metal_ior': int(mx.metal_ior),
                     'metal_tint': mx.metal_tint,
                     'metal_color_type': mx.metal_color_type,
                     'metal_color': color_to_rgb8(mx.metal_color),
                     'metal_color_map': texture_to_data(mx.metal_color_map),
                     'metal_roughness_type': mx.metal_roughness_type,
                     'metal_roughness': mx.metal_roughness,
                     'metal_roughness_map': texture_to_data(mx.metal_roughness_map),
                     'metal_anisotropy_type': mx.metal_anisotropy_type,
                     'metal_anisotropy': mx.metal_anisotropy,
                     'metal_anisotropy_map': texture_to_data(mx.metal_anisotropy_map),
                     'metal_angle_type': mx.metal_angle_type,
                     'metal_angle': mx.metal_angle,
                     'metal_angle_map': texture_to_data(mx.metal_angle_map),
                     'metal_dust_type': mx.metal_dust_type,
                     'metal_dust': mx.metal_dust,
                     'metal_dust_map': texture_to_data(mx.metal_dust_map),
                     'metal_perforation_enabled': mx.metal_perforation_enabled,
                     'metal_perforation_map': texture_to_data(mx.metal_perforation_map), }
            elif(m.use == 'TRANSLUCENT'):
                d = {'type': 'TRANSLUCENT',
                     'name': mat.name,
                     'translucent_scale': mx.translucent_scale,
                     'translucent_ior': mx.translucent_ior,
                     'translucent_color_type': mx.translucent_color_type,
                     'translucent_color': color_to_rgb8(mx.translucent_color),
                     'translucent_color_map': texture_to_data(mx.translucent_color_map),
                     'translucent_hue_shift': mx.translucent_hue_shift,
                     'translucent_invert_hue': mx.translucent_invert_hue,
                     'translucent_vibrance': mx.translucent_vibrance,
                     'translucent_density': mx.translucent_density,
                     'translucent_opacity': mx.translucent_opacity,
                     'translucent_roughness_type': mx.translucent_roughness_type,
                     'translucent_roughness': mx.translucent_roughness,
                     'translucent_roughness_map': texture_to_data(mx.translucent_roughness_map),
                     'translucent_specular_tint': mx.translucent_specular_tint,
                     'translucent_clearcoat': mx.translucent_clearcoat,
                     'translucent_clearcoat_ior': mx.translucent_clearcoat_ior, }
            elif(m.use == 'CARPAINT'):
                d = {'type': 'CARPAINT',
                     'name': mat.name,
                     'carpaint_color': color_to_rgb8(mx.carpaint_color),
                     'carpaint_metallic': mx.carpaint_metallic,
                     'carpaint_topcoat': mx.carpaint_topcoat, }
            # elif(m.use == 'HAIR'):
            #     pass
            else:
                # CUSTOM
                raise ValueError('materials of type CUSTOM should be handled somewhere else..')
            
            return d
        
        path = system.mxed_create_and_edit_ext_material_helper(p, ext_material(context.material, context.object))
        
        m = context.material.maxwell_render
        m.use = 'CUSTOM'
        m.mxm_file = path
        
        return {'FINISHED'}


class OpenMXS(Operator):
    bl_idname = "maxwell_render.open_mxs"
    bl_label = "Open MXS"
    bl_description = ""
    
    filepath = StringProperty(name="Filepath", subtype='FILE_PATH', options={'HIDDEN'}, )
    application = EnumProperty(name="Application", items=[('STUDIO', "Studio", ""), ('MAXWELL', "Maxwell", ""), ('NONE', "", ""), ], default='STUDIO', options={'HIDDEN'}, )
    instance_app = BoolProperty(name="Open a new instance", default=False, )
    
    def execute(self, context):
        if(self.application == 'NONE'):
            return {'FINISHED'}
        
        p = os.path.abspath(bpy.path.abspath(self.filepath))
        
        if(p == ""):
            self.report({'ERROR'}, "Filepath is empty")
            return {'CANCELLED'}
        if(os.path.isdir(p)):
            self.report({'ERROR'}, "Filepath is directory")
            return {'CANCELLED'}
        
        h, t = os.path.split(p)
        n, e = os.path.splitext(t)
        if(e.lower() != ".mxs"):
            self.report({'ERROR'}, "Extension is not .mxs")
            return {'CANCELLED'}
        
        if(self.application == 'STUDIO'):
            system.studio_open_mxs_helper(p, self.instance_app)
        elif(self.application == 'MAXWELL'):
            system.maxwell_open_mxs_helper(p, self.instance_app)
        else:
            self.report({'ERROR'}, "Unknown application")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class Render_preset_add(AddPresetBase, Operator):
    """Add a new render preset."""
    bl_idname = 'maxwell_render.render_preset_add'
    bl_label = 'Add/Remove Render Preset'
    preset_menu = 'Render_presets'
    preset_subdir = 'maxwell_render/render'
    preset_defines = ["m = bpy.context.scene.maxwell_render", ]
    preset_values = ["m.scene_time", "m.scene_sampling_level", "m.scene_multilight", "m.scene_multilight_type", "m.scene_cpu_threads",
                     "m.scene_quality", "m.output_depth", "m.output_image_enabled", "m.output_mxi_enabled", "m.materials_override",
                     "m.materials_override_path", "m.materials_search_path", "m.materials_directory", "m.globals_motion_blur",
                     "m.globals_diplacement", "m.globals_dispersion", "m.tone_color_space", "m.tone_burn", "m.tone_gamma",
                     "m.tone_sharpness", "m.tone_sharpness_value", "m.tone_whitepoint", "m.tone_tint", "m.simulens_aperture_map",
                     "m.simulens_obstacle_map", "m.simulens_diffraction", "m.simulens_diffraction_value", "m.simulens_frequency",
                     "m.simulens_scattering", "m.simulens_scattering_value", "m.simulens_devignetting", "m.simulens_devignetting_value",
                     "m.illum_caustics_illumination", "m.illum_caustics_refl_caustics", "m.illum_caustics_refr_caustics", ]


class Channels_preset_add(AddPresetBase, Operator):
    """Add a new channels preset."""
    bl_idname = 'maxwell_render.channels_preset_add'
    bl_label = 'Add/Remove Channels Preset'
    preset_menu = 'Channels_presets'
    preset_subdir = 'maxwell_render/channels'
    preset_defines = ["m = bpy.context.scene.maxwell_render", ]
    preset_values = ["m.channels_output_mode", "m.channels_render", "m.channels_render_type", "m.channels_alpha", "m.channels_alpha_file",
                     "m.channels_alpha_opaque", "m.channels_z_buffer", "m.channels_z_buffer_file", "m.channels_z_buffer_near",
                     "m.channels_z_buffer_far", "m.channels_shadow", "m.channels_shadow_file", "m.channels_material_id",
                     "m.channels_material_id_file", "m.channels_object_id", "m.channels_object_id_file", "m.channels_motion_vector",
                     "m.channels_motion_vector_file", "m.channels_roughness", "m.channels_roughness_file", "m.channels_fresnel",
                     "m.channels_fresnel_file", "m.channels_normals", "m.channels_normals_file", "m.channels_normals_space",
                     "m.channels_position", "m.channels_position_file", "m.channels_position_space", "m.channels_deep",
                     "m.channels_deep_file", "m.channels_deep_type", "m.channels_deep_min_dist", "m.channels_deep_max_samples",
                     "m.channels_uv", "m.channels_uv_file", "m.channels_custom_alpha", "m.channels_custom_alpha_file", ]


class Environment_preset_add(AddPresetBase, Operator):
    """Add a new environment preset."""
    bl_idname = 'maxwell_render.environment_preset_add'
    bl_label = 'Add/Remove Environment Preset'
    preset_menu = 'Environment_presets'
    preset_subdir = 'maxwell_render/environment'
    preset_defines = ["m = bpy.context.world.maxwell_render", ]
    preset_values = ["m.env_type", "m.sky_type", "m.sky_use_preset", "m.sky_preset", "m.sky_intensity", "m.sky_planet_refl", "m.sky_ozone",
                     "m.sky_water", "m.sky_turbidity_coeff", "m.sky_wavelength_exp", "m.sky_reflectance", "m.sky_asymmetry", "m.dome_intensity",
                     "m.dome_zenith", "m.dome_horizon", "m.dome_mid_point", "m.sun_lamp_priority", "m.sun_type", "m.sun_power",
                     "m.sun_radius_factor", "m.sun_temp", "m.sun_color", "m.sun_location_type", "m.sun_latlong_lat", "m.sun_latlong_lon",
                     "m.sun_date", "m.sun_time", "m.sun_latlong_gmt", "m.sun_latlong_gmt_auto", "m.sun_latlong_ground_rotation",
                     "m.sun_angles_zenith", "m.sun_angles_azimuth", "m.sun_dir_x", "m.sun_dir_y", "m.sun_dir_z", "m.ibl_intensity",
                     "m.ibl_interpolation", "m.ibl_screen_mapping", "m.ibl_bg_type", "m.ibl_bg_map", "m.ibl_bg_intensity", "m.ibl_bg_scale_x",
                     "m.ibl_bg_scale_y", "m.ibl_bg_offset_x", "m.ibl_bg_offset_y", "m.ibl_refl_type", "m.ibl_refl_map", "m.ibl_refl_intensity",
                     "m.ibl_refl_scale_x", "m.ibl_refl_scale_y", "m.ibl_refl_offset_x", "m.ibl_refl_offset_y", "m.ibl_refr_type", "m.ibl_refr_map",
                     "m.ibl_refr_intensity", "m.ibl_refr_scale_x", "m.ibl_refr_scale_y", "m.ibl_refr_offset_x", "m.ibl_refr_offset_y",
                     "m.ibl_illum_type", "m.ibl_illum_map", "m.ibl_illum_intensity", "m.ibl_illum_scale_x", "m.ibl_illum_scale_y",
                     "m.ibl_illum_offset_x", "m.ibl_illum_offset_y", ]


class Camera_preset_add(AddPresetBase, Operator):
    """Add a new camera preset."""
    bl_idname = 'maxwell_render.camera_preset_add'
    bl_label = 'Add/Remove Camera Preset'
    preset_menu = 'Camera_presets'
    preset_subdir = 'maxwell_render/camera'
    preset_defines = ["m = bpy.context.camera.maxwell_render", "o = bpy.context.camera", "r = bpy.context.scene.render", ]
    preset_values = ["m.lens", "m.shutter", "m.fstop", "m.fov", "m.azimuth", "m.angle", "m.iso", "m.screen_region", "m.screen_region_x",
                     "m.screen_region_y", "m.screen_region_w", "m.screen_region_h", "m.aperture", "m.diaphragm_blades", "m.diaphragm_angle",
                     "m.custom_bokeh", "m.bokeh_ratio", "m.bokeh_angle", "m.shutter_angle", "m.frame_rate", "m.zclip", "m.hide", "m.response",
                     
                     "o.dof_distance", "o.lens", "o.sensor_width", "o.sensor_height", "o.sensor_fit", "o.clip_start",
                     "o.clip_end", "o.shift_x", "o.shift_y",
                     
                     "r.resolution_x", "r.resolution_y", "r.resolution_percentage", "r.pixel_aspect_x", "r.pixel_aspect_y",
                     "r.fps", "r.fps_base", ]
