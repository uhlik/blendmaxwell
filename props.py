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

import bpy
from bpy.props import PointerProperty, FloatProperty, IntProperty, BoolProperty, StringProperty, EnumProperty, FloatVectorProperty
from bpy.types import PropertyGroup
from mathutils import Vector


def _output_depth_items(scene, context):
    items = [('RGB8', "RGB 8 bpc", "", 0),
             ('RGB16', "RGB 16 bpc", "", 1),
             ('RGB32', "RGB 32 bpc", "", 2), ]
    
    m = bpy.context.scene.maxwell_render
    e = os.path.splitext(os.path.split(m.output_image)[1])[1][1:].lower()
    v = ''
    if(e == "tga" or e == "jpg"):
        return items[:1]
    elif(e == "png"):
        return items[:2]
    else:
        return items


def _gmt_auto(self, context):
    if(self.sun_latlong_gmt_auto):
        # http://stackoverflow.com/questions/1058342/rough-estimate-of-the-time-offset-from-gmt-from-latitude-longitude
        # direction is 1 for east, -1 for west, and longitude is in (-180,180)
        # not sure which to choose, prague is gmt+1 and longitude ~14, and it works for this combination..
        offset = 1 * self.sun_latlong_lon * 24 / 360
        self.sun_latlong_gmt = round(offset)


def _override_sun(self, context):
    if(_override_sun_skip.value):
        return
    _override_sun_skip.value = True
    suns = [o for o in bpy.data.objects if (o and o.type == 'LAMP' and o.data.type == 'SUN')]
    
    for o in suns:
        mx = o.data.maxwell_render
        if(mx == self):
            m = bpy.context.scene.world.maxwell_render
            s = o
            w = s.matrix_world
            _, r, _ = w.decompose()
            v = Vector((0, 0, 1))
            v.rotate(r)
            m.sun_dir_x = v.x
            m.sun_dir_y = v.y
            m.sun_dir_z = v.z
        else:
            mx.override = False
    
    _override_sun_skip.value = False


def _update_gpu_dof(self, context):
    cam = context.camera
    dof_options = cam.gpu_dof
    dof_options.fstop = self.fstop


class _override_sun_skip():
    value = False


class SceneProperties(PropertyGroup):
    scene_time = IntProperty(name="Time (minutes)", default=60, min=1, max=50000, description="Maximum render time (in minutes) for the render", )
    scene_sampling_level = FloatProperty(name="Sampling Level", default=12.0, min=1.0, max=50.00, precision=2, description="Maximum sampling level required", )
    scene_multilight = EnumProperty(name="Multilight", items=[('DISABLED_0', "Disabled", ""), ('INTENSITY_1', "Intensity", ""), ('COLOR_2', "Color", "")], default='DISABLED_0', description="Multilight type", )
    scene_multilight_type = EnumProperty(name="Multilight Type", items=[('COMPOSITE_0', "Composite", ""), ('SEPARATE_1', "Separate", "")], default='COMPOSITE_0', description="Multilight layers type", )
    scene_cpu_threads = IntProperty(name="CPU Threads", default=0, min=0, max=1024, description="Number of CPU threads, set to 0 to use all", )
    # scene_priority = EnumProperty(name="Priority", items=[('LOW', "Low", ""), ('NORMAL', "Normal", "")], default='LOW', )
    scene_quality = EnumProperty(name="Quality", items=[('RS0', "Draft", ""), ('RS1', "Production", "")], default='RS1', description="Which type of render engine to use", )
    # scene_command_line = StringProperty(name="Command Line", default="", )
    
    output_depth = EnumProperty(name="Output Depth", items=_output_depth_items, description="Bit depth per channel for image output", )
    output_image_enabled = BoolProperty(name="Image", default=True, description="Render image", )
    output_image = StringProperty(name="Image", default="", subtype='FILE_PATH', description="Image path", )
    output_mxi_enabled = BoolProperty(name="MXI", default=True, description="Render .MXI", )
    output_mxi = StringProperty(name="MXI", default="", subtype='FILE_PATH', description=".MXI path", )
    
    materials_override = BoolProperty(name="Override", default=False, description="Override all materials in scene with one material", )
    materials_override_path = StringProperty(name="Override File", default="", subtype='FILE_PATH', description="Path to override material (.MXM)", )
    materials_search_path = StringProperty(name="Search Path", default="", subtype='DIR_PATH', description="Set the path where Studio should look for any textures and other files used in your scene to avoid 'missing textures' errors when rendering.", )
    
    materials_directory = StringProperty(name="Default Material Directory", default="//", subtype='DIR_PATH', description="Default directory where new materials are created upon running operator 'Create Material'", )
    
    globals_motion_blur = BoolProperty(name="Motion Blur", default=True, description="Global enable/disable motion blur", )
    globals_diplacement = BoolProperty(name="Displacement", default=True, description="Global enable/disable displacement", )
    globals_dispersion = BoolProperty(name="Dispersion", default=True, description="Global enable/disable dispaersion", )
    
    channels_output_mode = EnumProperty(name="Output Mode", items=[('SEPARATE_0', "Separate", ""), ('EMBEDDED_1', "Embedded", "")], default='SEPARATE_0', )
    channels_render = BoolProperty(name="Render", default=True, )
    channels_render_type = EnumProperty(name="Type", items=[('DIFFUSE_REFLECTIONS_0', "Diffuse + Reflections", ""), ('DIFFUSE_1', "Diffuse", ""), ('REFLECTIONS_2', "Reflections", "")], default='DIFFUSE_REFLECTIONS_0', )
    channels_alpha = BoolProperty(name="Alpha", default=False, )
    channels_alpha_file = EnumProperty(name="Alpha File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", "")], default='PNG16', )
    channels_alpha_opaque = BoolProperty(name="Opaque", default=False, )
    channels_z_buffer = BoolProperty(name="Z-buffer", default=False, )
    channels_z_buffer_file = EnumProperty(name="Z-buffer File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_z_buffer_near = FloatProperty(name="Z-buffer Near", default=0.0, min=-100000.000, max=100000.000, precision=3, )
    channels_z_buffer_far = FloatProperty(name="Z-buffer Far", default=0.0, min=-100000.000, max=100000.000, precision=3, )
    channels_shadow = BoolProperty(name="Shadow", default=False, )
    channels_shadow_file = EnumProperty(name="Shadow File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_material_id = BoolProperty(name="Material ID", default=False, )
    channels_material_id_file = EnumProperty(name="Material ID File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_object_id = BoolProperty(name="Object ID", default=False, )
    channels_object_id_file = EnumProperty(name="Object ID File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_motion_vector = BoolProperty(name="Motion Vector", default=False, )
    channels_motion_vector_file = EnumProperty(name="Motion Vector File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_roughness = BoolProperty(name="Roughness", default=False, )
    channels_roughness_file = EnumProperty(name="Roughness File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_fresnel = BoolProperty(name="Fresnel", default=False, )
    channels_fresnel_file = EnumProperty(name="Fresnel File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_normals = BoolProperty(name="Normals", default=False, )
    channels_normals_file = EnumProperty(name="Normals File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_normals_space = EnumProperty(name="Normals Space", items=[('WORLD_0', "World", ""), ('CAMERA_1', "Camera", "")], default='WORLD_0', )
    channels_position = BoolProperty(name="Position", default=False, )
    channels_position_file = EnumProperty(name="Position File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_position_space = EnumProperty(name="Normals Space", items=[('WORLD_0', "World", ""), ('CAMERA_1', "Camera", "")], default='WORLD_0', )
    channels_deep = BoolProperty(name="Deep", default=False, )
    channels_deep_file = EnumProperty(name="Deep File", items=[('EXR_DEEP', "EXR DEEP", ""), ('DTEX', "DTEX", "")], default='EXR_DEEP', )
    channels_deep_type = EnumProperty(name="Type", items=[('ALPHA_0', "Alpha", ""), ('RGBA_1', "RGBA", "")], default='ALPHA_0', )
    channels_deep_min_dist = FloatProperty(name="Min dist (m)", default=0.2, min=0.0, max=1000.000, precision=3, )
    channels_deep_max_samples = IntProperty(name="Max samples", default=20, min=1, max=100000, )
    channels_uv = BoolProperty(name="UV", default=False, )
    channels_uv_file = EnumProperty(name="UV File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", ""), ('JPG', "JPG", ""), ('JP2', "JP2", ""), ('HDR', "HDR", "")], default='PNG16', )
    channels_custom_alpha = BoolProperty(name="Custom Alpha", default=False, )
    channels_custom_alpha_file = EnumProperty(name="Custom Alpha File", items=[('PNG8', "PNG 8", ""), ('PNG16', "PNG 16", ""), ('TGA', "TGA", ""), ('TIF8', "TIF 8", ""), ('TIF16', "TIF 16", ""), ('TIF32', "TIF 32", ""), ('EXR16', "EXR 16", ""), ('EXR32', "EXR 32", "")], default='PNG16', )
    
    tone_color_space = EnumProperty(name="Color Space", items=[('SRGB_0', "sRGB IEC61966-2.1", ""), ('ARGB_1', "Adobe RGB 98", "")], default='SRGB_0', description="Image color space", )
    tone_burn = FloatProperty(name="Burn", default=0.8, min=0.0, max=1.0, precision=2, description="Image burn value", )
    tone_gamma = FloatProperty(name="Monitor Gamma", default=2.20, min=0.10, max=3.50, precision=2, description="Image gamma value", )
    tone_sharpness = BoolProperty(name="Sharpness", default=False, description="Image sharpness", )
    tone_sharpness_value = FloatProperty(name="Sharpness", default=60.0, min=0.0, max=100.0, precision=2, description="Image sharpness value", )
    tone_whitepoint = FloatProperty(name="White Point", default=6500.0, min=2000.0, max=20000.0, precision=1, description="", )
    tone_tint = FloatProperty(name="Tint", default=0.0, min=-100.0, max=100.0, precision=1, description="", )
    
    simulens_aperture_map = StringProperty(name="Aperture Map", default="", subtype='FILE_PATH', description="Path to aperture map", )
    simulens_obstacle_map = StringProperty(name="Obstacle Map", default="", subtype='FILE_PATH', description="Path to obstacle map", )
    simulens_diffraction = BoolProperty(name="Diffraction", default=False, description="Use lens diffraction", )
    simulens_diffraction_value = FloatProperty(name="Diffraction Value", default=50.0, min=0.0, max=2500.0, precision=2, description="Lens diffraction value", )
    simulens_frequency = FloatProperty(name="Frequency", default=50.0, min=0.0, max=2500.0, precision=2, description="Lens frequency value", )
    simulens_scattering = BoolProperty(name="Scattering", default=False, description="Use lens scattering", )
    simulens_scattering_value = FloatProperty(name="Scattering Value", default=0.0, min=0.0, max=2500.0, precision=2, description="Lens scattering value", )
    simulens_devignetting = BoolProperty(name="Devigneting", default=False, description="Use lens devignetting", )
    simulens_devignetting_value = FloatProperty(name="Devigneting", default=0.0, min=-100.0, max=100.0, precision=2, description="Lens devignetting value", )
    
    illum_caustics_illumination = EnumProperty(name="Illumination", items=[('BOTH_0', "Both", ""), ('DIRECT_1', "Direct", ""), ('INDIRECT_2', "Indirect", ""), ('NONE_3', "None", "")], default='BOTH_0', description="Illumination", )
    illum_caustics_refl_caustics = EnumProperty(name="Refl. Caustics", items=[('BOTH_0', "Both", ""), ('DIRECT_1', "Direct", ""), ('INDIRECT_2', "Indirect", ""), ('NONE_3', "None", "")], default='BOTH_0', description="Reflection caustics", )
    illum_caustics_refr_caustics = EnumProperty(name="Refr. Caustics", items=[('BOTH_0', "Both", ""), ('DIRECT_1', "Direct", ""), ('INDIRECT_2', "Indirect", ""), ('NONE_3', "None", "")], default='BOTH_0', description="Refraction caustics", )
    
    # overlay_enabled = BoolProperty(name="Overlay", default=False, )
    # overlay_text = StringProperty(name="Overlay Text", default="", )
    # overlay_position = EnumProperty(name="Position", items=[('BOTTOM', "Bottom", ""), ('TOP', "Top", "")], default='BOTTOM', )
    # overlay_color = FloatVectorProperty(name="Color", description="", default=(0.1, 0.1, 0.1), min=0.0, max=1.0, subtype='COLOR', )
    # overlay_background = BoolProperty(name="Background", default=False, )
    # overlay_background_color = FloatVectorProperty(name="Background Color", description="", default=(0.69, 0.69, 0.69), min=0.0, max=1.0, subtype='COLOR', )
    
    export_output_directory = StringProperty(name="Output Directory", subtype='DIR_PATH', default="//", description="Output directory for Maxwell scene (.MXS) file", )
    export_use_instances = BoolProperty(name="Use Instances", default=True, description="Convert multi-user mesh objects to instances", )
    export_keep_intermediates = BoolProperty(name="Keep Intermediates", default=False, description="Do not remove intermediate files used for scene export (usable only for debugging purposes)", )
    # export_auto_open = BoolProperty(name="Open In Studio", description="", default=True, )
    export_open_with = EnumProperty(name="Open With", items=[('STUDIO', "Studio", ""), ('MAXWELL', "Maxwell", ""), ('NONE', "None", "")], default='STUDIO', description="After export, open in ...", )
    export_wireframe = BoolProperty(name="Wireframe", default=False, description="Wireframe and Clay scene export", )
    export_edge_radius = FloatProperty(name="Edge Radius", default=0.00025, min=0.0, max=1.0, precision=6, description="Wireframe edge radius (meters)", )
    export_edge_resolution = IntProperty(name="Edge Resolution", default=32, min=3, max=128, description="Wireframe edge resolution", )
    export_wire_mat_color_id = FloatVectorProperty(name="Wire Color ID", default=(1.0, 0.0, 0.0), min=0.0, max=1.0, subtype='COLOR', description="Wireframe color ID", )
    export_wire_mat_reflectance_0 = FloatVectorProperty(name="Wire Reflectance 0", default=(20 / 255, 20 / 255, 20 / 255), min=0.0, max=1.0, subtype='COLOR', description="Wireframe reflectance 0 color", )
    export_wire_mat_reflectance_90 = FloatVectorProperty(name="Wire Reflectance 90", default=(45 / 255, 45 / 255, 45 / 255), min=0.0, max=1.0, subtype='COLOR', description="Wireframe reflectance 90 color", )
    export_wire_mat_roughness = FloatProperty(name="Wire Roughness", default=97.0, min=0.0, max=100.0, step=3, precision=2, subtype='PERCENTAGE', description="Wireframe roughness value", )
    export_clay_mat_color_id = FloatVectorProperty(name="Clay Color ID", default=(0.0, 1.0, 0.0), min=0.0, max=1.0, subtype='COLOR', description="Clay color ID", )
    export_clay_mat_reflectance_0 = FloatVectorProperty(name="Clay Reflectance 0", default=(210 / 255, 210 / 255, 210 / 255), min=0.0, max=1.0, subtype='COLOR', description="Clay reflectance 0 color", )
    export_clay_mat_reflectance_90 = FloatVectorProperty(name="Clay Reflectance 90", default=(230 / 255, 230 / 255, 230 / 255), min=0.0, max=1.0, subtype='COLOR', description="Clay reflectance 90 color", )
    export_clay_mat_roughness = FloatProperty(name="Clay Roughness", default=97.0, min=0.0, max=100.0, step=3, precision=2, subtype='PERCENTAGE', description="Clay roughness value", )
    
    export_overwrite = BoolProperty(name="Overwrite Existing Scene", default=True, description="", )
    
    export_log = StringProperty(name="Export Log String", default="", )
    export_log_display = BoolProperty(name="Display Log", default=False, description="Display export log in Export Log panel", )
    export_log_open = BoolProperty(name="Open Log", default=False, description="Open export log in text editor when finished", )
    
    exporting_animation_now = BoolProperty(default=False, )
    exporting_animation_frame_number = IntProperty(default=1, )
    
    @classmethod
    def register(cls):
        bpy.types.Scene.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Scene.maxwell_render


class EnvironmentProperties(PropertyGroup):
    env_type = EnumProperty(name="Type", items=[('NONE', "None", ""), ('PHYSICAL_SKY', "Physical Sky", ""), ('IMAGE_BASED', "Image Based", "")], default='PHYSICAL_SKY', description="Environment type", )
    
    sky_type = EnumProperty(name="Type", items=[('PHYSICAL', "Physical", ""), ('CONSTANT', "Constant Dome", "")], default='PHYSICAL', description="Sky type", )
    
    sky_use_preset = BoolProperty(name="Use Sky Preset", default=False, description="Use saved sky preset", )
    sky_preset = StringProperty(name="Sky Preset", default="", subtype='FILE_PATH', description="Saved sky preset path (.SKY)", )
    
    sky_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=10000.00, precision=2, )
    sky_planet_refl = FloatProperty(name="Planet Refl (%)", default=25.0, min=1.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    sky_ozone = FloatProperty(name="Ozone (cm)", default=0.4, min=0.0, max=50.0, precision=3, )
    sky_water = FloatProperty(name="Water (cm)", default=2.0, min=0.0, max=500.0, precision=3, )
    sky_turbidity_coeff = FloatProperty(name="Turbidity Coeff", default=0.040, min=0.0, max=10.0, precision=3, )
    sky_wavelength_exp = FloatProperty(name="Wavelength Exp", default=1.200, min=0.0, max=300.000, precision=3, )
    sky_reflectance = FloatProperty(name="Reflectance (%)", default=80.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    sky_asymmetry = FloatProperty(name="Assymetry", default=0.7, min=-0.999, max=0.999, precision=3, )
    
    dome_intensity = FloatProperty(name="Intensity (cd/m)", default=10000.0, min=0.0, max=1000000.0, precision=1, )
    dome_zenith = FloatVectorProperty(name="Color", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    dome_horizon = FloatVectorProperty(name="Color", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    dome_mid_point = FloatProperty(name="Mid Point", default=math.radians(45.000), min=math.radians(0.000), max=math.radians(90.000), precision=1, subtype='ANGLE', )
    
    sun_lamp_priority = BoolProperty(name="Sun Lamp Priority", default=False, description="When enabled, existing sun lamp will be used for direction", )
    
    sun_type = EnumProperty(name="Type", items=[('DISABLED', "Disabled", ""), ('PHYSICAL', "Physical", ""), ('CUSTOM', "Custom", "")], default='PHYSICAL', )
    sun_power = FloatProperty(name="Power", default=1.0, min=0.010, max=100.000, precision=3, )
    sun_radius_factor = FloatProperty(name="Radius Factor (x)", default=1.0, min=0.01, max=100.00, precision=2, )
    sun_temp = FloatProperty(name="Temperature (K)", default=5776.0, min=1.0, max=10000.0, precision=1, )
    sun_color = FloatVectorProperty(name="Color", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    sun_location_type = EnumProperty(name="Type", items=[('LATLONG', "Latitude / Longitude", ""), ('ANGLES', "Angles", ""), ('DIRECTION', "Direction", "")], default='DIRECTION', )
    sun_latlong_lat = FloatProperty(name="Lat", default=40.000, min=-90.000, max=90.000, precision=3, )
    sun_latlong_lon = FloatProperty(name="Lon", default=-3.000, min=-180.000, max=180.000, precision=3, update=_gmt_auto, )
    
    sun_date = StringProperty(name="Date", default="DD.MM.YYYY", description="Date in format DD.MM.YYYY", )
    sun_time = StringProperty(name="Time", default="HH:MM", description="Time in format HH:MM", )
    
    sun_latlong_gmt = IntProperty(name="GMT", default=0, min=-12, max=12, )
    sun_latlong_gmt_auto = BoolProperty(name="Auto", default=False, update=_gmt_auto, description="When enabled, GMT will be approximatelly calculated", )
    sun_latlong_ground_rotation = FloatProperty(name="Ground Rotation", default=math.radians(0.000), min=math.radians(0.000), max=math.radians(360.000), precision=3, subtype='ANGLE', )
    sun_angles_zenith = FloatProperty(name="Zenith", default=math.radians(45.000), min=math.radians(0.000), max=math.radians(90.000), precision=3, subtype='ANGLE', )
    sun_angles_azimuth = FloatProperty(name="Azimuth", default=math.radians(45.000), min=math.radians(0.000), max=math.radians(360.00), precision=3, subtype='ANGLE', )
    sun_dir_x = FloatProperty(name="X", default=0.0, min=-1000.000, max=1000.000, precision=3, )
    sun_dir_y = FloatProperty(name="Y", default=0.0, min=-1000.000, max=1000.000, precision=3, )
    sun_dir_z = FloatProperty(name="Z", default=1.0, min=-1000.000, max=1000.000, precision=3, )
    
    ibl_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=1000000.0, precision=1, )
    ibl_interpolation = BoolProperty(name="Interpolation", default=False, )
    ibl_screen_mapping = BoolProperty(name="Screen Mapping", default=False, )
    
    ibl_bg_type = EnumProperty(name="Type", items=[('HDR_IMAGE', "Hdr Image", ""), ('ACTIVE_SKY', "Active Sky", ""), ('DISABLED', "Disabled", "")], default='HDR_IMAGE', )
    ibl_bg_map = StringProperty(name="Image", default="", subtype='FILE_PATH', )
    ibl_bg_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_bg_scale_x = FloatProperty(name="Scale X", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_bg_scale_y = FloatProperty(name="Scale Y", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_bg_offset_x = FloatProperty(name="Offset X", default=0.0, min=-360.000, max=360.000, precision=3, )
    ibl_bg_offset_y = FloatProperty(name="Offset Y", default=0.0, min=-360.000, max=360.000, precision=3, )
    
    ibl_refl_type = EnumProperty(name="Type", items=[('HDR_IMAGE', "Hdr Image", ""), ('ACTIVE_SKY', "Active Sky", ""), ('SAME_AS_BG', "Same As Background", ""), ('DISABLED', "Disabled", "")], default='SAME_AS_BG', )
    ibl_refl_map = StringProperty(name="Image", default="", subtype='FILE_PATH', )
    ibl_refl_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_refl_scale_x = FloatProperty(name="Scale X", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_refl_scale_y = FloatProperty(name="Scale Y", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_refl_offset_x = FloatProperty(name="Offset X", default=0.0, min=-360.000, max=360.000, precision=3, )
    ibl_refl_offset_y = FloatProperty(name="Offset Y", default=0.0, min=-360.000, max=360.000, precision=3, )
    
    ibl_refr_type = EnumProperty(name="Type", items=[('HDR_IMAGE', "Hdr Image", ""), ('ACTIVE_SKY', "Active Sky", ""), ('SAME_AS_BG', "Same As Background", ""), ('DISABLED', "Disabled", "")], default='SAME_AS_BG', )
    ibl_refr_map = StringProperty(name="Image", default="", subtype='FILE_PATH', )
    ibl_refr_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_refr_scale_x = FloatProperty(name="Scale X", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_refr_scale_y = FloatProperty(name="Scale Y", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_refr_offset_x = FloatProperty(name="Offset X", default=0.0, min=-360.000, max=360.000, precision=3, )
    ibl_refr_offset_y = FloatProperty(name="Offset Y", default=0.0, min=-360.000, max=360.000, precision=3, )
    
    ibl_illum_type = EnumProperty(name="Type", items=[('HDR_IMAGE', "Hdr Image", ""), ('ACTIVE_SKY', "Active Sky", ""), ('SAME_AS_BG', "Same As Background", ""), ('DISABLED', "Disabled", "")], default='SAME_AS_BG', )
    ibl_illum_map = StringProperty(name="Image", default="", subtype='FILE_PATH', )
    ibl_illum_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_illum_scale_x = FloatProperty(name="Scale X", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_illum_scale_y = FloatProperty(name="Scale Y", default=1.0, min=0.0, max=1000.000, precision=3, )
    ibl_illum_offset_x = FloatProperty(name="Offset X", default=0.0, min=-360.000, max=360.000, precision=3, )
    ibl_illum_offset_y = FloatProperty(name="Offset Y", default=0.0, min=-360.000, max=360.000, precision=3, )
    
    @classmethod
    def register(cls):
        bpy.types.World.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.World.maxwell_render


class CameraProperties(PropertyGroup):
    # optics
    lens = EnumProperty(name="Lens", items=[('TYPE_THIN_LENS_0', "Thin Lens", ""), ('TYPE_PINHOLE_1', "Pin Hole", ""), ('TYPE_ORTHO_2', "Ortho", ""), ('TYPE_FISHEYE_3', "Fish Eye", ""), ('TYPE_SPHERICAL_4', "Spherical", ""), ('TYPE_CYLINDRICAL_5', "Cylindical", "")], default='TYPE_THIN_LENS_0', )
    shutter = FloatProperty(name="Shutter Speed", default=250.0, min=0.01, max=16000.0, precision=3, description="1 / shutter speed", )
    fstop = FloatProperty(name="f-Stop", default=11.0, min=1.0, max=100000.0, update=_update_gpu_dof, )
    fov = FloatProperty(name="FOV", default=math.radians(180.0), min=math.radians(0.0), max=math.radians(360.0), subtype='ANGLE', )
    azimuth = FloatProperty(name="Azimuth", default=math.radians(180.0), min=math.radians(0.0), max=math.radians(360.0), subtype='ANGLE', )
    angle = FloatProperty(name="Angle", default=math.radians(180.0), min=math.radians(0.0), max=math.radians(360.0), subtype='ANGLE', )
    # sensor
    # resolution_width = IntProperty(name="Width", default=640, min=32, max=65536, subtype="PIXEL", )
    # resolution_height = IntProperty(name="Height", default=480, min=32, max=65536, subtype="PIXEL", )
    # pixel_aspect = FloatProperty(name="Pixel Aspect", default=1.0, min=0.010, max=100.000, precision=3, )
    iso = FloatProperty(name="ISO", default=100.0, min=1.0, max=16000.0, )
    screen_region = EnumProperty(name="Selection", items=[('NONE', "None", ""), ('REGION', "Region", ""), ('BLOW UP', "Blow Up", "")], default='NONE', )
    screen_region_x = IntProperty(name="X", default=0, min=0, max=65000, subtype="PIXEL", )
    screen_region_y = IntProperty(name="Y", default=0, min=0, max=65000, subtype="PIXEL", )
    screen_region_w = IntProperty(name="Width", default=1, min=0, max=65000, subtype="PIXEL", )
    screen_region_h = IntProperty(name="Height", default=1, min=0, max=65000, subtype="PIXEL", )
    # diaphragm
    aperture = EnumProperty(name="Aperture", items=[('CIRCULAR', "Circular", ""), ('POLYGONAL', "Polygonal", "")], default='CIRCULAR', )
    diaphragm_blades = IntProperty(name="Blades", default=6, min=3, max=96, )
    diaphragm_angle = FloatProperty(name="Angle", default=math.radians(60.0), min=math.radians(0.0), max=math.radians(720.0), subtype='ANGLE', )
    custom_bokeh = BoolProperty(name="Custom Bokeh", default=False, )
    bokeh_ratio = FloatProperty(name="Bokeh Ratio", default=1.0, min=0.0, max=10000.0, )
    bokeh_angle = FloatProperty(name="Bokeh Angle", default=math.radians(0.0), min=math.radians(0.0), max=math.radians(20520.0), subtype='ANGLE', )
    # rotary disc shutter
    shutter_angle = FloatProperty(name="Shutter Angle", default=math.radians(17.280), min=math.radians(0.0), max=math.radians(5000.000), subtype='ANGLE', description="WARNING: currently unused..", )
    frame_rate = IntProperty(name="Frame Rate", default=24, min=1, max=10000, )
    # z-clip planes
    zclip = BoolProperty(name="Z-cLip", default=False, )
    # # just for info, it is hardcoded somewhere else..
    # projection_type = StringProperty(name="Projection Type", default='TYPE_PERSPECTIVE', options={'HIDDEN'}, )
    hide = BoolProperty(name="Hide (in Maxwell Studio)", default=False, )
    response = EnumProperty(name="Response", items=[('Maxwell', 'Maxwell', "", ), ('Advantix 100', 'Advantix 100', "", ), ('Advantix 200', 'Advantix 200', "", ),
                                                    ('Advantix 400', 'Advantix 400', "", ), ('Agfachrome CTPrecisa 200', 'Agfachrome CTPrecisa 200', "", ),
                                                    ('Agfachrome CTPrecisa 100', 'Agfachrome CTPrecisa 100', "", ), ('Agfachrome rsx2 050', 'Agfachrome rsx2 050', "", ),
                                                    ('Agfachrome rsx2 100', 'Agfachrome rsx2 100', "", ), ('Agfachrome rsx2 200', 'Agfachrome rsx2 200', "", ),
                                                    ('Agfacolor Futura 100', 'Agfacolor Futura 100', "", ), ('Agfacolor Futura 200', 'Agfacolor Futura 200', "", ),
                                                    ('Agfacolor Futura 400', 'Agfacolor Futura 400', "", ), ('Agfacolor Futura II 100', 'Agfacolor Futura II 100', "", ),
                                                    ('Agfacolor Futura II 200', 'Agfacolor Futura II 200', "", ), ('Agfacolor Futura II 400', 'Agfacolor Futura II 400', "", ),
                                                    ('Agfacolor HDC 100 Plus', 'Agfacolor HDC 100 Plus', "", ), ('Agfacolor HDC 200 Plus', 'Agfacolor HDC 200 Plus', "", ),
                                                    ('Agfacolor HDC 400 Plus', 'Agfacolor HDC 400 Plus', "", ), ('Agfacolor Optima II 100', 'Agfacolor Optima II 100', "", ),
                                                    ('Agfacolor Optima II 200', 'Agfacolor Optima II 200', "", ), ('Agfacolor Ultra 050', 'Agfacolor Ultra 050', "", ),
                                                    ('Agfacolor Vista 100', 'Agfacolor Vista 100', "", ), ('Agfacolor Vista 200', 'Agfacolor Vista 200', "", ),
                                                    ('Agfacolor Vista 400', 'Agfacolor Vista 400', "", ), ('Agfacolor Vista 800', 'Agfacolor Vista 800', "", ),
                                                    ('Agfapan APX 025 (B&W)', 'Agfapan APX 025 (B&W)', "", ), ('Agfapan APX 100 (B&W)', 'Agfapan APX 100 (B&W)', "", ),
                                                    ('Agfapan APX 400 (B&W)', 'Agfapan APX 400 (B&W)', "", ), ('Ektachrome 100 Plus (Color Rev.)', 'Ektachrome 100 Plus (Color Rev.)', "", ),
                                                    ('Ektachrome 100 (Color Rev.)', 'Ektachrome 100 (Color Rev.)', "", ), ('Ektachrome 320T (Color Rev.)', 'Ektachrome 320T (Color Rev.)', "", ),
                                                    ('Ektachrome 400X (Color Rev.)', 'Ektachrome 400X (Color Rev.)', "", ), ('Ektachrome 64 (Color Rev.)', 'Ektachrome 64 (Color Rev.)', "", ),
                                                    ('Ektachrome 64T (Color Rev.)', 'Ektachrome 64T (Color Rev.)', "", ), ('Ektachrome E100S', 'Ektachrome E100S', "", ),
                                                    ('Fujifilm Cine F-125', 'Fujifilm Cine F-125', "", ), ('Fujifilm Cine F-250', 'Fujifilm Cine F-250', "", ),
                                                    ('Fujifilm Cine F-400', 'Fujifilm Cine F-400', "", ), ('Fujifilm Cine FCI', 'Fujifilm Cine FCI', "", ),
                                                    ('Kodak Gold 100', 'Kodak Gold 100', "", ), ('Kodak Gold 200', 'Kodak Gold 200', "", ), ('Kodachrome 200', 'Kodachrome 200', "", ),
                                                    ('Kodachrome 25', 'Kodachrome 25', "", ), ('Kodachrome 64', 'Kodachrome 64', "", ), ('Kodak Max Zoom 800', 'Kodak Max Zoom 800', "", ),
                                                    ('Kodak Portra 100T', 'Kodak Portra 100T', "", ), ('Kodak Portra 160NC', 'Kodak Portra 160NC', "", ),
                                                    ('Kodak Portra 160VC', 'Kodak Portra 160VC', "", ), ('Kodak Portra 400NC', 'Kodak Portra 400NC', "", ),
                                                    ('Kodak Portra 400VC', 'Kodak Portra 400VC', "", ), ('Kodak Portra 800', 'Kodak Portra 800', "", ), ], default='Maxwell', )
    
    @classmethod
    def register(cls):
        bpy.types.Camera.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Camera.maxwell_render


class ObjectProperties(PropertyGroup):
    opacity = FloatProperty(name="Opacity", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE', )
    hidden_camera = BoolProperty(name="Camera", default=False, )
    hidden_camera_in_shadow_channel = BoolProperty(name="Camera In Shadow Channel", default=False, )
    hidden_global_illumination = BoolProperty(name="Global Illumination", default=False, )
    hidden_reflections_refractions = BoolProperty(name="Reflections/Refractions", default=False, )
    hidden_zclip_planes = BoolProperty(name="Z-clip Planes", default=False, )
    object_id = FloatVectorProperty(name="Object ID", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    
    backface_material_embed = BoolProperty(name="Embed Into Scene", default=True, )
    backface_material_file = StringProperty(name="Backface MXM File", default="", subtype='FILE_PATH', )
    
    hide = BoolProperty(name="Hide (in Maxwell Studio)", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_render


class MaterialProperties(PropertyGroup):
    embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    mxm_file = StringProperty(name="MXM File", default="", subtype='FILE_PATH', description="Path to material (.MXM) file", )
    
    @classmethod
    def register(cls):
        bpy.types.Material.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Material.maxwell_render


class CustomAlphaPropertyGroup(PropertyGroup):
    custom_alpha_use = BoolProperty(name="Use", default=False, )
    custom_alpha_opaque = BoolProperty(name="Opaque", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.Group.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Group.maxwell_render


class ParticlesProperties(PropertyGroup):
    use = EnumProperty(name="Type", items=[('USE_BIN', "RealFlow .BIN", ""), ('USE_BLENDER', "Blender Particles", ""), ('NONE', "None", "")], default='NONE', )
    
    bin_filename = StringProperty(name="File Name", default="", subtype='FILE_PATH', )
    bin_radius_multiplier = FloatProperty(name="Radius Multiplier", default=1.0, min=0.000001, max=1000000.0, step=3, precision=6, )
    bin_motion_blur_multiplier = FloatProperty(name="Motion Blur Multiplier", default=1.0, min=0.000001, max=1000000.0, step=3, precision=6, )
    bin_shutter_speed = FloatProperty(name="Shutter Speed", default=125.0, min=0.000001, max=1000000.0, step=2, precision=2, )
    bin_load_particles = FloatProperty(name="Load Particles (%)", default=100.0, min=0.0, max=100.0, step=2, precision=2, subtype='PERCENTAGE', )
    bin_axis_system = EnumProperty(name="Axis System", items=[('YZX_0', "YZX (xsi maya houdini)", ""), ('ZXY_1', "ZXY (3dsmax maya)", ""), ('YXZ_2', "YXZ (lw c4d rf)", "")], default='YZX_0', )
    bin_frame_number = IntProperty(name="Frame Number", default=0, min=-100000000, max=100000000, )
    bin_fps = FloatProperty(name="FPS", default=24.0, min=0.0, max=1000000.0, step=2, precision=2, )
    
    bin_advanced = BoolProperty(name="Advanced", default=False, )
    
    bin_extra_create_np_pp = IntProperty(name="Extra Particles Per Particle", default=0, min=0, max=100000000, )
    bin_extra_dispersion = FloatProperty(name="Extra Particles Dispersion", default=0.0, min=0.0, max=1000000.0, step=3, precision=6, )
    bin_extra_deformation = FloatProperty(name="Extra Particles Deformation", default=0.0, min=0.0, max=1000000.0, step=3, precision=6, )
    bin_load_force = BoolProperty(name="Load Force", default=False, )
    bin_load_vorticity = BoolProperty(name="Load Vorticity", default=False, )
    bin_load_normal = BoolProperty(name="Load Normal", default=False, )
    bin_load_neighbors_num = BoolProperty(name="Load Neighbours", default=False, )
    bin_load_uv = BoolProperty(name="Load UV", default=False, )
    bin_load_age = BoolProperty(name="Load Age", default=False, )
    bin_load_isolation_time = BoolProperty(name="Load Isolation Time", default=False, )
    bin_load_viscosity = BoolProperty(name="Load Viscosity", default=False, )
    bin_load_density = BoolProperty(name="Load Density", default=False, )
    bin_load_pressure = BoolProperty(name="Load Pressure", default=False, )
    bin_load_mass = BoolProperty(name="Load Mass", default=False, )
    bin_load_temperature = BoolProperty(name="Load Temperature", default=False, )
    bin_load_id = BoolProperty(name="Load ID", default=False, )
    bin_min_force = FloatProperty(name="Min Force", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_force = FloatProperty(name="Max Force", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_vorticity = FloatProperty(name="Min Vorticity", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_vorticity = FloatProperty(name="Max Vorticity", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_nneighbors = IntProperty(name="Min Neighbours", default=0, min=0, max=1000000, step=3, )
    bin_max_nneighbors = IntProperty(name="Max Neighbours", default=1, min=0, max=1000000, step=3, )
    bin_min_age = FloatProperty(name="Min Age", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_age = FloatProperty(name="Max Age", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_isolation_time = FloatProperty(name="Min Isolation Time", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_isolation_time = FloatProperty(name="Max Isolation Time", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_viscosity = FloatProperty(name="Min Viscosity", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_viscosity = FloatProperty(name="Max Viscosity", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_density = FloatProperty(name="Min Density", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_density = FloatProperty(name="Max Density", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_pressure = FloatProperty(name="Min Pressure", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_pressure = FloatProperty(name="Max Pressure", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_mass = FloatProperty(name="Min Mass", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_mass = FloatProperty(name="Max Mass", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_temperature = FloatProperty(name="Min Temperature", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_temperature = FloatProperty(name="Max Temperature", default=1.0, min=0.0, max=1000000.0, step=3, )
    bin_min_velocity = FloatProperty(name="Min Velocity Modulus", default=0.0, min=0.0, max=1000000.0, step=3, )
    bin_max_velocity = FloatProperty(name="Max Velocity Modulus", default=1.0, min=0.0, max=1000000.0, step=3, )
    
    material_file = StringProperty(name="MXM File", default="", subtype='FILE_PATH', )
    material_embed = BoolProperty(name="Embed Into Scene", default=True, )
    opacity = FloatProperty(name="Opacity", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE', )
    hidden_camera = BoolProperty(name="Camera", default=False, )
    hidden_camera_in_shadow_channel = BoolProperty(name="Camera In Shadow Channel", default=False, )
    hidden_global_illumination = BoolProperty(name="Global Illumination", default=False, )
    hidden_reflections_refractions = BoolProperty(name="Reflections/Refractions", default=False, )
    hidden_zclip_planes = BoolProperty(name="Z-clip Planes", default=False, )
    object_id = FloatVectorProperty(name="Object ID", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    
    hide = BoolProperty(name="Hide (in Maxwell Studio)", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.ParticleSettings.maxwell_render


class SunProperties(PropertyGroup):
    override = BoolProperty(name="Override Environment Settings", default=False, description="When True, this lamp will override Sun direction from Environment Settings", update=_override_sun, )
    
    @classmethod
    def register(cls):
        bpy.types.SunLamp.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.SunLamp.maxwell_render
