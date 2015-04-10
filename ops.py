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
import platform

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty
from bpy.types import Operator
from mathutils import Vector
from bl_operators.presets import AddPresetBase

from . import maths


def prefs():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    return p


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
        
        s = platform.system()
        if(s == 'Darwin'):
            app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Mxed.app', 'Contents', 'MacOS', 'Mxed', )))
            command_line = "{0} -new:'{1}'".format(app, p, )
            args = shlex.split(command_line, )
            process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
        elif(s == 'Linux'):
            # app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'mxed', )))
            # command_line = "nohup {0} -new:'{1}'".format(app, p, )
            # args = shlex.split(command_line, )
            # process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
            pass
        elif(s == 'Windows'):
            pass
        else:
            self.report({'ERROR'}, "Unknown platform")
            return {'CANCELLED'}
        
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
        
        s = platform.system()
        if(s == 'Darwin'):
            app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Mxed.app', 'Contents', 'MacOS', 'Mxed', )))
            command_line = "{0} -mxm:'{1}'".format(app, p, )
            args = shlex.split(command_line, )
            p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
        elif(s == 'Linux'):
            # app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'mxed', )))
            # command_line = "nohup {0} -mxm:'{1}'".format(app, p, )
            # args = shlex.split(command_line, )
            # p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
            pass
        elif(s == 'Windows'):
            pass
        else:
            self.report({'ERROR'}, "Unknown platform")
            return {'CANCELLED'}
        
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
        
        s = platform.system()
        if(s == 'Darwin'):
            if(self.application == 'STUDIO'):
                app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Studio.app', ))
                if(self.instance_app):
                    # command_line = 'open -n -a {0} {1}'.format(shlex.quote(app), shlex.quote(p))
                    app = os.path.join(app, "Contents/MacOS/Studio")
                    command_line = '{0} -mxs:{1}'.format(shlex.quote(app), shlex.quote(p))
                else:
                    command_line = 'open -a {0} {1}'.format(shlex.quote(app), shlex.quote(p))
                args = shlex.split(command_line)
                p = subprocess.Popen(args)
            elif(self.application == 'MAXWELL'):
                app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Maxwell.app', ))
                if(self.instance_app):
                    # command_line = 'open -n -a {0} {1}'.format(shlex.quote(app), shlex.quote(p))
                    app = os.path.join(app, "Contents/MacOS/Maxwell")
                    command_line = '{0} -mxs:{1}'.format(shlex.quote(app), shlex.quote(p))
                else:
                    command_line = 'open -a {0} {1}'.format(shlex.quote(app), shlex.quote(p))
                args = shlex.split(command_line)
                p = subprocess.Popen(args)
            else:
                self.report({'ERROR'}, "Unknown application")
                return {'CANCELLED'}
        elif(s == 'Linux'):
            # subprocess.Popen(['xdg-open', p], )
            
            # app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio', ))
            # command_line = 'nohup {0} {1}'.format(shlex.quote(app), shlex.quote(p))
            # args = shlex.split(command_line)
            # p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
            pass
        elif(s == 'Windows'):
            # app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio.exe', ))
            # os.startfile(os.path.normpath(p))
            pass
        else:
            self.report({'ERROR'}, "Unknown platform")
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
                     
                     "r.resolution_x", "r.resolution_y", "r.resolution_percentage", "r.pixel_aspect_x", "r.pixel_aspect_y", ]
