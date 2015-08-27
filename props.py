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
from bpy.props import PointerProperty, FloatProperty, IntProperty, BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntVectorProperty
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
    if(_overrides.sun_skip):
        return
    _overrides.sun_skip = True
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
    
    _overrides.sun_skip = False


def _override_output_image(self, context):
    if(_overrides.output_image):
        return
    _overrides.output_image = True
    
    self.output_image = bpy.path.abspath(self.output_image)
    
    h, t = os.path.split(self.output_image)
    n, e = os.path.splitext(t)
    es = ['.png', '.jpg', '.tga', '.tif', '.jp2', '.hdr', '.exr', '.bmp', ]
    if(not e.lower() in es):
        e = '.png'
    
    p = bpy.path.ensure_ext(self.output_image, e, case_sensitive=False, )
    if(p != self.output_image and p != e):
        self.output_image = p
    
    _overrides.output_image = False


def _override_output_mxi(self, context):
    if(_overrides.output_mxi):
        return
    _overrides.output_mxi = True
    
    self.output_mxi = bpy.path.abspath(self.output_mxi)
    
    e = '.mxi'
    p = bpy.path.ensure_ext(self.output_mxi, '.mxi', case_sensitive=False, )
    if(p != self.output_mxi and p != e):
        self.output_mxi = p
    
    _overrides.output_mxi = False


def _update_gpu_dof(self, context):
    cam = context.camera
    dof_options = cam.gpu_dof
    dof_options.fstop = self.fstop


def _get_custom_alphas(self, context):
    r = []
    for i, g in enumerate(bpy.data.groups):
        gmx = g.maxwell_render
        if(gmx.custom_alpha_use):
            r.append((g.name, g.name, '', ))
    if(len(r) == 0):
        # return empty list if no groups in scene
        return [("0", "", ""), ]
    return r


class _overrides():
    sun_skip = False
    output_image = False
    output_mxi = False


class PrivateProperties(PropertyGroup):
    material = StringProperty(name="m", default="", )
    
    @classmethod
    def register(cls):
        bpy.types.Scene.maxwell_render_private = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Scene.maxwell_render_private


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
    output_image = StringProperty(name="Image", default="", subtype='FILE_PATH', description="Image path", update=_override_output_image, )
    output_mxi_enabled = BoolProperty(name="MXI", default=True, description="Render .MXI", )
    output_mxi = StringProperty(name="MXI", default="", subtype='FILE_PATH', description=".MXI path", update=_override_output_mxi, )
    
    materials_override = BoolProperty(name="Override", default=False, description="Override all materials in scene with one material", )
    materials_override_path = StringProperty(name="Override File", default="", subtype='FILE_PATH', description="Path to override material (.MXM)", )
    materials_search_path = StringProperty(name="Search Path", default="", subtype='DIR_PATH', description="Set the path where Studio should look for any textures and other files used in your scene to avoid 'missing textures' errors when rendering.", )
    
    materials_directory = StringProperty(name="Default Material Directory", default="//", subtype='DIR_PATH', description="Default directory where new materials are created upon running operator 'Create Material'", )
    
    globals_motion_blur = BoolProperty(name="Motion Blur", default=True, description="Global enable/disable motion blur", )
    globals_diplacement = BoolProperty(name="Displacement", default=True, description="Global enable/disable displacement", )
    globals_dispersion = BoolProperty(name="Dispersion", default=True, description="Global enable/disable dispaersion", )
    
    extra_sampling_enabled = BoolProperty(name="Enabled", default=False, description="Enable rendering extra-sampling based on custom-alpha/alpha/user-input-bitmap.", )
    extra_sampling_sl = FloatProperty(name="Sampling Level", default=14.0, min=1.0, max=50.00, precision=2, description="Target SL when DO EXTRA SAMPLING is enabled.", )
    extra_sampling_mask = EnumProperty(name="Mask", items=[('CUSTOM_ALPHA_0', "Custom Alpha", ""), ('ALPHA_1', "Alpha", ""), ('BITMAP_2', "Bitmap", "")], default='CUSTOM_ALPHA_0', description="Sets the extra-sampling mask.", )
    extra_sampling_custom_alpha = EnumProperty(name="Mask", items=_get_custom_alphas, description="The name of the custom alpha to be used when mask is Custom Alpha.", )
    extra_sampling_user_bitmap = StringProperty(name="Bitmap", default="", subtype='FILE_PATH', description="Path of the image to use when mask is Birmap", )
    extra_sampling_invert = BoolProperty(name="Invert Mask", default=False, description="Inverts alpha mask for render extra-sampling.", )
    
    # render_use_layers = EnumProperty(name="Export layers", items=[('VIEWPORT', "Viewport Layers", ""), ('RENDER', "Render Layers", ""), ], default='VIEWPORT', description="Export objects from scene or render layers", )
    
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
    
    tone_color_space = EnumProperty(name="Color Space",
                                    items=[('SRGB_0', "sRGB IEC61966-2.1", ""),
                                           ('ADOBE98_1', "Adobe RGB 98", ""),
                                           ('APPLE_2', "Apple RGB / SGI", ""),
                                           ('PAL_3', "PAL / SECAM (EBU3213)", ""),
                                           ('NTSC_4', "NTSC 1953", ""),
                                           ('NTSC1979_5', "NTSC 1979 (SMPTE-C)", ""),
                                           ('WIDEGAMUT_6', "Wide Gamut RGB", ""),
                                           ('PROPHOTO_7', "ProPhoto RGB (ROMM)", ""),
                                           ('ECIRRGB_8', "ECI RGB", ""),
                                           ('CIE1931_9', "CIE 1931", ""),
                                           ('BRUCERGB_10', "Bruce RGB", ""),
                                           ('COLORMATCH_11', "ColorMatch RGB", ""),
                                           ('BESTRGB_12', "Best RGB", ""),
                                           ('DONRGB4_13', "Don RGB 4", ""),
                                           ('HDTV_14', "HDTV (Rec.709)", ""),
                                           ('ACES_15', "ACES", ""), ],
                                    default='SRGB_0', description="Image color space", )
    tone_burn = FloatProperty(name="Burn", default=0.8, min=0.0, max=1.0, precision=2, description="Image burn value", )
    tone_gamma = FloatProperty(name="Monitor Gamma", default=2.20, min=0.10, max=3.50, precision=2, description="Image gamma value", )
    tone_sharpness = BoolProperty(name="Sharpness", default=False, description="Image sharpness", )
    tone_sharpness_value = FloatProperty(name="Sharpness", default=60.0, min=0.0, max=100.0, precision=2, description="Image sharpness value", )
    tone_whitepoint = FloatProperty(name="White Point (K)", default=6500.0, min=2000.0, max=20000.0, precision=1, description="", )
    tone_tint = FloatProperty(name="Tint", default=0.0, min=-100.0, max=100.0, precision=1, description="", )
    
    simulens_aperture_map = StringProperty(name="Aperture Map", default="", subtype='FILE_PATH', description="Path to aperture map", )
    simulens_obstacle_map = StringProperty(name="Obstacle Map", default="", subtype='FILE_PATH', description="Path to obstacle map", )
    simulens_diffraction = BoolProperty(name="Diffraction", default=False, description="Use lens diffraction", )
    simulens_diffraction_value = FloatProperty(name="Diffraction Value", default=50.0, min=0.0, max=2500.0, precision=2, description="Lens diffraction value", )
    simulens_frequency = FloatProperty(name="Frequency", default=50.0, min=0.0, max=2500.0, precision=2, description="Lens frequency value", )
    simulens_scattering = BoolProperty(name="Scattering", default=False, description="Use lens scattering", )
    simulens_scattering_value = FloatProperty(name="Scattering Value", default=0.0, min=0.0, max=2500.0, precision=2, description="Lens scattering value", )
    simulens_devignetting = BoolProperty(name="Devigneting (%)", default=False, description="Use lens devignetting", )
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
    
    export_protect_mxs = BoolProperty(name="Protect MXS", default=False, description="", )
    
    export_output_directory = StringProperty(name="Output Directory", subtype='DIR_PATH', default="//", description="Output directory for Maxwell scene (.MXS) file", )
    export_use_instances = BoolProperty(name="Use Instances", default=True, description="Convert multi-user mesh objects to instances", )
    export_use_subdivision = BoolProperty(name="Use Subdivision Modifiers", default=False, description="Export all Subdivision modifiers if they are Catmull-Clark type and at the end of modifier stack on regular mesh objects.", )
    export_keep_intermediates = BoolProperty(name="Keep Intermediates", default=False, description="Do not remove intermediate files used for scene export (usable only for debugging purposes)", )
    # export_auto_open = BoolProperty(name="Open In Studio", description="", default=True, )
    
    export_use_transformation_hacks = BoolProperty(name="Use Transformation Hacks", default=True, description="Try to fix transformation errors in Studio", )
    
    export_open_with = EnumProperty(name="Open With", items=[('STUDIO', "Studio", ""), ('MAXWELL', "Maxwell", ""), ('NONE', "None", "")], default='STUDIO', description="After export, open in ...", )
    instance_app = BoolProperty(name="Open a new instance of application", default=False, description="Open a new instance of the application even if one is already running", )
    
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
    
    export_overwrite = BoolProperty(name="Overwrite Existing", default=True, description="", )
    export_incremental = BoolProperty(name="Incremental", default=False, description="Always export a new file", )
    
    # export_log = StringProperty(name="Export Log String", default="", )
    # export_log_display = BoolProperty(name="Display Log", default=False, description="Display export log in Export Log panel", )
    export_log_open = BoolProperty(name="Open Log", default=False, description="Open export log in text editor when finished", )
    
    exporting_animation_now = BoolProperty(default=False, options={'HIDDEN'}, )
    exporting_animation_frame_number = IntProperty(default=1, options={'HIDDEN'}, )
    exporting_animation_first_frame = BoolProperty(default=True, options={'HIDDEN'}, )
    private_name = StringProperty(default="", options={'HIDDEN'}, )
    private_increment = StringProperty(default="", options={'HIDDEN'}, )
    private_suffix = StringProperty(default="", options={'HIDDEN'}, )
    private_path = StringProperty(default="", options={'HIDDEN'}, )
    private_basepath = StringProperty(default="", options={'HIDDEN'}, )
    private_image = StringProperty(default="", options={'HIDDEN'}, )
    private_mxi = StringProperty(default="", options={'HIDDEN'}, )
    
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
    dome_zenith = FloatVectorProperty(name="Zenith Color", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    dome_horizon = FloatVectorProperty(name="Horizon Color", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
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
    
    # hide = BoolProperty(name="Export, but Hide from Render", default=False, )
    hide = BoolProperty(name="Export as Hidden Object", default=False, description="Object will be exported, but with visibility set to Hidden. Useful for finishing scene in Studio")
    override_instance = BoolProperty(name="Override Instancing", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_render


class ReferenceProperties(PropertyGroup):
    enabled = BoolProperty(name="Enabled", default=False, )
    path = StringProperty(name="MXS File", default="", subtype='FILE_PATH', )
    flag_override_hide = BoolProperty(name="Hidden", default=False, )
    flag_override_hide_to_camera = BoolProperty(name="Camera", default=False, )
    flag_override_hide_to_refl_refr = BoolProperty(name="Reflections/Refractions", default=False, )
    flag_override_hide_to_gi = BoolProperty(name="Global Illumination", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_render_reference = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_render_reference


class MaterialProperties(PropertyGroup):
    embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    mxm_file = StringProperty(name="MXM File", default="", subtype='FILE_PATH', description="Path to material (.MXM) file", )
    
    # use = EnumProperty(name="Type", items=[('CUSTOM', "Custom", ""), ('EMITTER', "Emitter", ""), ('AGS', "AGS", ""), ('OPAQUE', "Opaque", ""), ('TRANSPARENT', "Transparent", ""),
    #                                        ('METAL', "Metal", ""), ('TRANSLUCENT', "Translucent", ""), ('CARPAINT', "Carpaint", ""), ('HAIR', "Hair", ""), ], default='CUSTOM', )
    use = EnumProperty(name="Type", items=[('CUSTOM', "Custom", ""), ('EMITTER', "Emitter", ""), ('AGS', "AGS", ""), ('OPAQUE', "Opaque", ""), ('TRANSPARENT', "Transparent", ""),
                                           ('METAL', "Metal", ""), ('TRANSLUCENT', "Translucent", ""), ('CARPAINT', "Carpaint", ""), ], default='CUSTOM', )
    # use = EnumProperty(name="Type", items=[('CUSTOM', "Custom", ""), ], default='CUSTOM', )
    
    flag = BoolProperty(name="Flag", default=False, description="True - redraw preview, False - skip", options={'HIDDEN'}, )
    
    @classmethod
    def register(cls):
        bpy.types.Material.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Material.maxwell_render


class TextureProperties(PropertyGroup):
    path = StringProperty(name="Path", default="", subtype='FILE_PATH', description="", )
    use_global_map = BoolProperty(name="Use Override Map", default=False, )
    tiling_method = EnumProperty(name="Tiling Method", items=[('TILE_XY', "Tile XY", ""), ('TILE_X', "Tile X", ""), ('TILE_Y', "Tile Y", ""), ('NO_TILING', "No Tiling", ""), ], default='TILE_XY', )
    tiling_units = EnumProperty(name="Tiling Units", items=[('0', "Relative", ""), ('1', "Meters", ""), ], default='0', )
    repeat = FloatVectorProperty(name="Repeat", default=(1.0, 1.0), min=-1000.0, max=1000.0, precision=3, size=2, )
    mirror_x = BoolProperty(name="Mirror X", default=False, )
    mirror_y = BoolProperty(name="Mirror Y", default=False, )
    offset = FloatVectorProperty(name="Offset", default=(0.0, 0.0), min=-1000.0, max=1000.0, precision=3, size=2, )
    rotation = FloatProperty(name="Rotation", default=math.radians(0.000), min=math.radians(0.000), max=math.radians(360.000), precision=3, subtype='ANGLE', )
    invert = BoolProperty(name="Invert", default=False, )
    use_alpha = BoolProperty(name="Alpha Only", default=False, )
    interpolation = BoolProperty(name="Interpolation", default=False, )
    brightness = FloatProperty(name="Brightness", default=0.0, min=-100.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    contrast = FloatProperty(name="Contrast", default=0.0, min=-100.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    saturation = FloatProperty(name="Saturation", default=0.0, min=-100.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    hue = FloatProperty(name="Hue", default=0.0, min=-180.0, max=180.0, precision=3, subtype='PERCENTAGE', )
    clamp = IntVectorProperty(name="RGB Clamp", default=(0, 255), min=0, max=255, subtype='NONE', size=2, )
    
    use = EnumProperty(name="Type", items=[('IMAGE', "Image", ""), ('BRICK', "Brick", ""), ('CHECKER', "Checker", ""), ('CIRCLE', "Circle", ""), ('GRADIENT3', "Gradient3", ""),
                                           ('GRADIENT', "Gradient", ""), ('GRID', "Grid", ""), ('MARBLE', "Marble", ""), ('NOISE', "Noise", ""), ('VORONOI', "Voronoi", ""),
                                           ('TILEDTEXTURE', "TiledTexture", ""), ('WIREFRAMETEXTURE', "WireframeTexture", ""), ], default='IMAGE', )
    
    brick_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    brick_brick_width = FloatProperty(name="Brick Width", default=0.21, min=0.0, max=1.0, precision=4, )
    brick_brick_height = FloatProperty(name="Brick Height", default=0.1, min=0.0, max=1.0, precision=4, )
    brick_brick_offset = IntProperty(name="Brick Offset", default=50, min=0, max=100, )
    brick_random_offset = IntProperty(name="Random Offset", default=20, min=0, max=100, )
    brick_double_brick = BoolProperty(name="Double Brick", default=False, )
    brick_small_brick_width = FloatProperty(name="Small Brick Width", default=0.1050, min=0.0, max=1.0, precision=4, )
    brick_round_corners = BoolProperty(name="Round Corners", default=False, )
    brick_boundary_sharpness_u = FloatProperty(name="Transition Sharpness U", default=0.9, min=0.0, max=1.0, precision=4, )
    brick_boundary_sharpness_v = FloatProperty(name="Transition Sharpness V", default=0.9, min=0.0, max=1.0, precision=4, )
    brick_boundary_noise_detail = IntProperty(name="Boundary Noise Detail", default=0, min=0, max=100, )
    brick_boundary_noise_region_u = FloatProperty(name="Boundary Noise Region U", default=0.0, min=0.0, max=1.0, precision=4, )
    brick_boundary_noise_region_v = FloatProperty(name="Boundary Noise Region V", default=0.0, min=0.0, max=1.0, precision=4, )
    brick_seed = IntProperty(name="Seed", default=4357, min=0, max=1000000, )
    brick_random_rotation = BoolProperty(name="Random Rotation", default=True, )
    brick_color_variation = IntProperty(name="Brightness Variation", default=20, min=0, max=100, )
    brick_brick_color_0 = FloatVectorProperty(name="Brick Color 1", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    brick_brick_texture_0 = StringProperty(name="Brick Texture 1", default="", )
    brick_sampling_factor_0 = IntProperty(name="Sample Size 1", default=10, min=0, max=100, )
    brick_weight_0 = IntProperty(name="Weight 1", default=100, min=0, max=100, )
    brick_brick_color_1 = FloatVectorProperty(name="Brick Color 2", default=(0.0, 0.0, 0.0), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    brick_brick_texture_1 = StringProperty(name="Brick Texture 2", default="", )
    brick_sampling_factor_1 = IntProperty(name="Sample Size 2", default=9, min=0, max=100, )
    brick_weight_1 = IntProperty(name="Weight 2", default=100, min=0, max=100, )
    brick_brick_color_2 = FloatVectorProperty(name="Brick Color 3", default=(255 / 89.250, 255 / 89.250, 255 / 89.250), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    brick_brick_texture_2 = StringProperty(name="Brick Texture 3", default="", )
    brick_sampling_factor_2 = IntProperty(name="Sample Size 3", default=12, min=0, max=100, )
    brick_weight_2 = IntProperty(name="Weight 3", default=100, min=0, max=100, )
    brick_mortar_thickness = FloatProperty(name="Mortar Thickness", default=0.012, min=0.0, max=1.0, precision=4, )
    brick_mortar_color = FloatVectorProperty(name="Mortar Color", default=(255 / 129.795, 255 / 129.795, 255 / 129.795), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    brick_mortar_texture = StringProperty(name="Mortar Texture", default="", )
    
    checker_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    checker_number_of_elements_u = IntProperty(name="Checks U", default=4, min=0, max=1000, )
    checker_number_of_elements_v = IntProperty(name="Checks V", default=4, min=0, max=1000, )
    checker_color_0 = FloatVectorProperty(name="Background Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    checker_color_1 = FloatVectorProperty(name="Checker Color", default=(0 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    checker_transition_sharpness = FloatProperty(name="Sharpness", default=1.0, min=0.0, max=1.0, precision=3, )
    checker_falloff = EnumProperty(name="Fall-off", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    
    circle_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    circle_background_color = FloatVectorProperty(name="Background Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    circle_circle_color = FloatVectorProperty(name="Circle Color", default=(0 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    circle_radius_u = FloatProperty(name="Radius U", default=1.0, min=0.0, max=1.0, precision=3, )
    circle_radius_v = FloatProperty(name="Radius U", default=1.0, min=0.0, max=1.0, precision=3, )
    circle_transition_factor = FloatProperty(name="Sharpness", default=1.0, min=0.0, max=1.0, precision=3, )
    circle_falloff = EnumProperty(name="Fall-off", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    
    gradient3_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    gradient3_gradient_u = BoolProperty(name="Active", default=True, )
    gradient3_color0_u = FloatVectorProperty(name="Start Color", default=(255 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient3_color1_u = FloatVectorProperty(name="Mid Color", default=(0 / 255, 255 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient3_color2_u = FloatVectorProperty(name="End Color", default=(0 / 255, 0 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient3_gradient_type_u = EnumProperty(name="Transition Type", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    gradient3_color1_u_position = FloatProperty(name="Mid Color Position", default=0.5, min=0.0, max=1.0, precision=3, )
    gradient3_gradient_v = BoolProperty(name="Active", default=False, )
    gradient3_color0_v = FloatVectorProperty(name="Start Color", default=(255 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient3_color1_v = FloatVectorProperty(name="Mid Color", default=(0 / 255, 255 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient3_color2_v = FloatVectorProperty(name="End Color", default=(0 / 255, 0 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient3_gradient_type_v = EnumProperty(name="Transition Type", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    gradient3_color1_v_position = FloatProperty(name="Mid Color Position", default=0.5, min=0.0, max=1.0, precision=3, )
    
    gradient_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    gradient_gradient_u = BoolProperty(name="Active", default=True, )
    gradient_color0_u = FloatVectorProperty(name="Start Color", default=(255 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient_color1_u = FloatVectorProperty(name="End Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient_gradient_type_u = EnumProperty(name="Transition Type", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    gradient_transition_factor_u = FloatProperty(name="Transition Position", default=1.0, min=0.0, max=1.0, precision=3, )
    gradient_gradient_v = BoolProperty(name="Active", default=False, )
    gradient_color0_v = FloatVectorProperty(name="Start Color", default=(0 / 255, 0 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient_color1_v = FloatVectorProperty(name="End Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    gradient_gradient_type_v = EnumProperty(name="Transition Type", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    gradient_transition_factor_v = FloatProperty(name="Transition Position", default=1.0, min=0.0, max=1.0, precision=3, )
    
    grid_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    grid_horizontal_lines = BoolProperty(name="Grid U", default=True, )
    grid_vertical_lines = BoolProperty(name="Grid V", default=True, )
    grid_cell_width = FloatProperty(name="Cell Width", default=0.2500, min=0.0, max=1.0, precision=4, )
    grid_cell_height = FloatProperty(name="Cell Height", default=0.1250, min=0.0, max=1.0, precision=4, )
    grid_boundary_thickness_u = FloatProperty(name="Background Thickness U", default=0.0650, min=0.0, max=1.0, precision=4, )
    grid_boundary_thickness_v = FloatProperty(name="Background Thickness V", default=0.0650, min=0.0, max=1.0, precision=4, )
    grid_transition_sharpness = FloatProperty(name="Sharpness", default=0.0, min=0.0, max=1.0, precision=4, )
    grid_cell_color = FloatVectorProperty(name="Cell Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    grid_boundary_color = FloatVectorProperty(name="Boundary Color", default=(0 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    grid_falloff = EnumProperty(name="Fall-off", items=[('0', "Linear", ""), ('1', "Quadratic", ""), ('2', "Sinusoidal", ""), ], default='0', )
    
    marble_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    marble_coordinates_type = EnumProperty(name="Coordinates Type", items=[('0', "Texture coordinates", ""), ('1', "World coordinates", ""), ], default='1', )
    marble_color0 = FloatVectorProperty(name="Vein Color 1", default=(199 / 255, 202 / 255, 210 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    marble_color1 = FloatVectorProperty(name="Vein Color 2", default=(152 / 255, 156 / 255, 168 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    marble_color2 = FloatVectorProperty(name="Vein Color 3", default=(87 / 255, 91 / 255, 98 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    marble_frequency = FloatProperty(name="Frequency", default=0.6, min=0.0, max=1000.0, precision=3, )
    marble_detail = FloatProperty(name="Detail", default=4.0, min=0.0, max=100.0, precision=3, )
    marble_octaves = IntProperty(name="Octaves", default=7, min=1, max=100, )
    marble_seed = IntProperty(name="Seed", default=4372, min=1, max=1000000, )
    
    noise_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    noise_coordinates_type = EnumProperty(name="Coordinates Type", items=[('0', "Texture coordinates", ""), ('1', "World coordinates", ""), ], default='0', )
    noise_noise_color = FloatVectorProperty(name="Vein Color 1", default=(0 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    noise_background_color = FloatVectorProperty(name="Vein Color 1", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    noise_detail = FloatProperty(name="Detail", default=6.2, min=1.0, max=1000.0, precision=4, )
    noise_persistance = FloatProperty(name="Persistance", default=0.55, min=0.0, max=1.0, precision=4, )
    noise_octaves = IntProperty(name="Octaves", default=4, min=1, max=50, )
    noise_low_value = FloatProperty(name="Low Clip", default=0.0, min=0.0, max=1.0, precision=4, )
    noise_high_value = FloatProperty(name="High Clip", default=1.0, min=0.0, max=1.0, precision=4, )
    noise_seed = IntProperty(name="Seed", default=4357, min=1, max=1000000, )
    
    voronoi_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    voronoi_coordinates_type = EnumProperty(name="Coordinates Type", items=[('0', "Texture coordinates", ""), ('1', "World coordinates", ""), ], default='0', )
    voronoi_color0 = FloatVectorProperty(name="Background Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    voronoi_color1 = FloatVectorProperty(name="Cell Color", default=(0 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    voronoi_detail = IntProperty(name="Detail", default=8, min=1, max=10000, )
    voronoi_distance = EnumProperty(name="Distance", items=[('0', "Euclidian", ""), ('1', "Manhattan", ""), ('2', "Minkowski4", ""), ('3', "Chebyshev", ""), ], default='0', )
    voronoi_combination = EnumProperty(name="Combination", items=[('0', "D1", ""), ('1', "D2", ""), ('2', "D3", ""), ('3', "D1+D2", ""), ('4', "D2-D1", ""), ('5', "D3-D2", ""),
                                                                  ('6', "D1*D2", ""), ('7', "D1*D3", ""), ('8', "D2*D3", ""), ('9', "1-D1", ""), ('10', "1-D2", ""),
                                                                  ('11', "1-(D1+D2)", ""), ('12', "1-(D1*D2)", ""), ], default='0', )
    voronoi_low_value = FloatProperty(name="Low Clip", default=0.0, min=0.0, max=1.0, precision=4, )
    voronoi_high_value = FloatProperty(name="High Clip", default=1.0, min=0.0, max=1.0, precision=4, )
    voronoi_seed = IntProperty(name="Seed", default=4357, min=1, max=1000000, )
    
    tiled_blend_procedural = FloatProperty(name="Blending Factor", default=0.0, min=0.0, max=100.0, precision=3, subtype='PERCENTAGE', )
    tiled_filename = StringProperty(name="File Name", default="", subtype='FILE_PATH', )
    tiled_token_mask = StringProperty(name="Token mask", default="texture.<UDIM>.png", )
    tiled_base_color = FloatVectorProperty(name="Base Color", default=(204 / 255, 204 / 255, 204 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    tiled_use_base_color = BoolProperty(name="Use Base Color", default=True, )
    
    wireframe_fill_color = FloatVectorProperty(name="Fill Color", default=(204 / 255, 204 / 255, 204 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    wireframe_edge_color = FloatVectorProperty(name="Edge Color", default=(0 / 255, 0 / 255, 0 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    wireframe_coplanar_edge_color = FloatVectorProperty(name="Coplanar Edge Color", default=(76.5 / 255, 76.5 / 255, 76.5 / 255), min=0.0, max=1.0, precision=3, subtype='COLOR', )
    wireframe_edge_width = FloatProperty(name="Edge Width (cm)", default=2.00, min=0.0, max=1000000.0, precision=3, )
    wireframe_coplanar_edge_width = FloatProperty(name="Coplanar Edge Width (cm)", default=1.00, min=0.0, max=1000000.0, precision=3, )
    wireframe_coplanar_threshold = FloatProperty(name="Coplanar Threshold", default=math.radians(20.000), min=math.radians(0.000), max=math.radians(100.000), precision=1, subtype='ANGLE', )
    
    @classmethod
    def register(cls):
        bpy.types.Texture.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Texture.maxwell_render


class CustomAlphaPropertyGroup(PropertyGroup):
    custom_alpha_use = BoolProperty(name="Use", default=False, )
    custom_alpha_opaque = BoolProperty(name="Opaque", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.Group.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Group.maxwell_render


class SunProperties(PropertyGroup):
    override = BoolProperty(name="Override Environment Settings", default=False, description="When True, this lamp will override Sun direction from Environment Settings", update=_override_sun, )
    
    @classmethod
    def register(cls):
        bpy.types.SunLamp.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.SunLamp.maxwell_render


class ParticlesProperties(PropertyGroup):
    use = EnumProperty(name="Type", items=[('GRASS', "Grass", ""),
                                           ('HAIR', "Hair", ""),
                                           ('PARTICLES', "Particles", ""),
                                           # ('MESHER', "Mesher", ""),
                                           ('CLONER', "Cloner", ""),
                                           ('NONE', "None", "")], default='NONE', )
    
    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.maxwell_render = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.ParticleSettings.maxwell_render


class ExtGrassProperties(PropertyGroup):
    material = StringProperty(name="MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    backface_material = StringProperty(name="Backface MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    backface_material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    
    density = IntProperty(name="Density (blades/m2)", default=3000, min=0, max=100000000, )
    density_map = StringProperty(name="Density Map", default="", )
    
    length = FloatProperty(name="Length (cm)", default=10.0, min=0.0, max=100000.0, precision=3, )
    length_map = StringProperty(name="Length Map", default="", )
    length_variation = FloatProperty(name="Length Variation (%)", default=20.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    
    root_width = FloatProperty(name="Root Width (mm)", default=5.0, min=0.00001, max=100000.0, precision=3, )
    tip_width = FloatProperty(name="Tip Width (mm)", default=1.0, min=0.00001, max=100000.0, precision=3, )
    
    direction_type = EnumProperty(name="Direction Type", items=[('0', "Polygon Normal", ""), ('1', "World Z", "")], default='0', )
    
    initial_angle = FloatProperty(name="Initial Angle", default=math.radians(80.000), min=math.radians(0.000), max=math.radians(90.000), precision=1, subtype='ANGLE', )
    initial_angle_variation = FloatProperty(name="Initial Angle Variation (%)", default=25.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    initial_angle_map = StringProperty(name="Initial Angle Map", default="", )
    
    start_bend = FloatProperty(name="Start Bend (%)", default=40.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    start_bend_variation = FloatProperty(name="Start Bend Variation (%)", default=25.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    start_bend_map = StringProperty(name="Start Bend Map", default="", )
    
    bend_radius = FloatProperty(name="Bend Radius (cm)", default=10.0, min=0.0, max=10000.0, precision=1, )
    bend_radius_variation = FloatProperty(name="Bend Radius Variation (%)", default=25.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    bend_radius_map = StringProperty(name="Bend Radius Map", default="", )
    
    bend_angle = FloatProperty(name="Bend Angle", default=math.radians(80.000), min=math.radians(0.000), max=math.radians(360.000), precision=1, subtype='ANGLE', )
    bend_angle_variation = FloatProperty(name="Bend Radius Variation (%)", default=25.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    bend_angle_map = StringProperty(name="Bend Radius Map", default="", )
    
    cut_off = FloatProperty(name="Cut Off (%)", default=100.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    cut_off_variation = FloatProperty(name="Cut Off Variation (%)", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    cut_off_map = StringProperty(name="Cut Off Map", default="", )
    
    points_per_blade = IntProperty(name="Points Per Blade", default=4, min=2, max=20, )
    primitive_type = EnumProperty(name="Primitive Type", items=[('0', "Curve", ""), ('1', "Flat", ""), ('2', "Cylinder", "")], default='0', )
    seed = IntProperty(name="Random Seed", default=0, min=0, max=16300, )
    
    lod = BoolProperty(name="Enable Level of Detail", default=False, )
    lod_min_distance = FloatProperty(name="Min Distance (m)", default=10.0, min=0.0, max=100000.0, precision=2, )
    lod_max_distance = FloatProperty(name="Max Distance (m)", default=50.0, min=0.0, max=100000.0, precision=2, )
    lod_max_distance_density = FloatProperty(name="Max Distance Density (%)", default=10.0, min=0.0, max=100.0, precision=2, subtype='PERCENTAGE', )
    
    display_percent = FloatProperty(name="Display Percent (%)", default=10.0, min=0.0, max=100.0, precision=0, subtype='PERCENTAGE', )
    display_max_blades = IntProperty(name="Display Max. Blades", default=1000, min=0, max=100000, )
    
    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.maxwell_grass_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.ParticleSettings.maxwell_grass_extension


class ExtParticlesProperties(PropertyGroup):
    # material_file = StringProperty(name="MXM File", default="", subtype='FILE_PATH', )
    # material_embed = BoolProperty(name="Embed Into Scene", default=True, )
    
    material = StringProperty(name="MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    backface_material = StringProperty(name="Backface MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    backface_material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    
    opacity = FloatProperty(name="Opacity", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE', )
    hidden_camera = BoolProperty(name="Camera", default=False, )
    hidden_camera_in_shadow_channel = BoolProperty(name="Camera In Shadow Channel", default=False, )
    hidden_global_illumination = BoolProperty(name="Global Illumination", default=False, )
    hidden_reflections_refractions = BoolProperty(name="Reflections/Refractions", default=False, )
    hidden_zclip_planes = BoolProperty(name="Z-clip Planes", default=False, )
    object_id = FloatVectorProperty(name="Object ID", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    
    hide = BoolProperty(name="Hide From Render", default=False, )
    hide_parent = BoolProperty(name="Hide Parent Object (Emitter)", default=False, )
    
    source = EnumProperty(name="Source", items=[('BLENDER_PARTICLES', "Blender Particles", ""), ('EXTERNAL_BIN', "External Bin", "")], default='BLENDER_PARTICLES', )
    bin_directory = StringProperty(name=".bin Output Directory", default="//", subtype='DIR_PATH', description="Output directory for .bin file(s)", )
    bin_overwrite = BoolProperty(name="Overwrite Existing", default=True, )
    embed = BoolProperty(name="Embed in MXS", default=True, )
    bl_use_velocity = BoolProperty(name="Particle Velocity", default=False, )
    bl_use_size = BoolProperty(name="Size Per Particle", default=False, )
    bl_size = FloatProperty(name="Size", default=0.1, min=0.000001, max=1000000.0, step=3, precision=6, )
    
    bin_type = EnumProperty(name="Type", items=[('STATIC', "Static", ""), ('SEQUENCE', "Sequence", "")], default='STATIC', )
    seq_limit = BoolProperty(name="Limit Sequence", default=False, )
    seq_start = IntProperty(name="Start Frame", default=0, min=0, max=100000000, )
    seq_end = IntProperty(name="Stop Frame", default=100, min=0, max=100000000, )
    private_bin_filename = StringProperty(name="File Name", default="", subtype='FILE_PATH', )
    
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
    
    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.maxwell_particles_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.ParticleSettings.maxwell_particles_extension


class ExtHairProperties(PropertyGroup):
    material = StringProperty(name="MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    backface_material = StringProperty(name="Backface MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    backface_material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    
    opacity = FloatProperty(name="Opacity", default=100.0, min=0.0, max=100.0, subtype='PERCENTAGE', )
    hidden_camera = BoolProperty(name="Camera", default=False, )
    hidden_camera_in_shadow_channel = BoolProperty(name="Camera In Shadow Channel", default=False, )
    hidden_global_illumination = BoolProperty(name="Global Illumination", default=False, )
    hidden_reflections_refractions = BoolProperty(name="Reflections/Refractions", default=False, )
    hidden_zclip_planes = BoolProperty(name="Z-clip Planes", default=False, )
    object_id = FloatVectorProperty(name="Object ID", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, precision=2, subtype='COLOR', )
    hide = BoolProperty(name="Hide From Render", default=False, )
    hide_parent = BoolProperty(name="Hide Parent Object (Emitter)", default=False, )
    
    hair_type = EnumProperty(name="Hair Type", items=[('HAIR', "Hair", ""), ('GRASS', "Grass", ""), ], default='HAIR', )
    
    hair_root_radius = FloatProperty(name="Root Radius (mm)", default=0.1, min=0.001, max=100000.0, precision=3, )
    hair_tip_radius = FloatProperty(name="Tip Radius (mm)", default=0.05, min=0.001, max=100000.0, precision=3, )
    grass_root_width = FloatProperty(name="Root Width (mm)", default=5.0, min=0.001, max=100000.0, precision=3, )
    grass_tip_width = FloatProperty(name="Tip Width (mm)", default=1.0, min=0.001, max=100000.0, precision=3, )
    
    uv_layer = StringProperty(name="UV Layer", default="", )
    
    display_percent = FloatProperty(name="Display Percent (%)", default=10.0, min=0.0, max=100.0, precision=0, subtype='PERCENTAGE', )
    display_max_blades = IntProperty(name="Display Max. Blades", default=1000, min=0, max=100000, )
    display_max_hairs = IntProperty(name="Display Max. Hairs", default=1000, min=0, max=100000, )
    
    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.maxwell_hair_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.ParticleSettings.maxwell_hair_extension


class ExtScatterProperties(PropertyGroup):
    enabled = BoolProperty(name="Maxwell Scatter", default=False, )
    
    scatter_object = StringProperty(name="Object", default="", )
    inherit_objectid = BoolProperty(name="Inherit ObjectID", default=False, )
    
    density = FloatProperty(name="Density (Units/m2)", default=100.0, min=0.0001, max=100000000.0, precision=3, )
    density_map = StringProperty(name="Density Map", default="", )
    seed = IntProperty(name="Random Seed", default=0, min=0, max=16300, )
    
    scale_x = FloatProperty(name="X", default=1.0, min=0.0, max=100000.0, precision=3, )
    scale_y = FloatProperty(name="Y", default=1.0, min=0.0, max=100000.0, precision=3, )
    scale_z = FloatProperty(name="Z", default=1.0, min=0.0, max=100000.0, precision=3, )
    scale_map = StringProperty(name="Length Map", default="", )
    scale_variation_x = FloatProperty(name="X", default=20.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    scale_variation_y = FloatProperty(name="X", default=20.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    scale_variation_z = FloatProperty(name="X", default=20.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    
    rotation_x = FloatProperty(name="X", default=math.radians(0.000), min=math.radians(0.000), max=math.radians(360.000), precision=1, subtype='ANGLE', )
    rotation_y = FloatProperty(name="Y", default=math.radians(0.000), min=math.radians(0.000), max=math.radians(360.000), precision=1, subtype='ANGLE', )
    rotation_z = FloatProperty(name="Z", default=math.radians(0.000), min=math.radians(0.000), max=math.radians(360.000), precision=1, subtype='ANGLE', )
    rotation_map = StringProperty(name="Rotation Map", default="", )
    rotation_variation_x = FloatProperty(name="X", default=10.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    rotation_variation_y = FloatProperty(name="Y", default=10.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    rotation_variation_z = FloatProperty(name="Z", default=10.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    rotation_direction = EnumProperty(name="Direction", items=[('0', "Polygon Normal", ""), ('1', "World Z", "")], default='0', )
    
    lod = BoolProperty(name="Enable Level of Detail", default=False, )
    lod_min_distance = FloatProperty(name="Min Distance (m)", default=10.0, min=0.0, max=100000.0, precision=2, )
    lod_max_distance = FloatProperty(name="Max Distance (m)", default=50.0, min=0.0, max=100000.0, precision=2, )
    lod_max_distance_density = FloatProperty(name="Max Distance Density (%)", default=10.0, min=0.0, max=100.0, precision=2, subtype='PERCENTAGE', )
    
    display_percent = FloatProperty(name="Display Percent (%)", default=10.0, min=0.0, max=100.0, precision=0, subtype='PERCENTAGE', )
    display_max_blades = IntProperty(name="Display Max. Instances", default=1000, min=0, max=100000, )
    
    # 19: ('Initial Angle', [90.0], 0.0, 90.0, '3 FLOAT', 4, 1, True)
    # 20: ('Initial Angle Variation', [0.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
    # 21: ('Initial Angle Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
    # 29: ('TRIANGLES_WITH_CLONES', [0], 0, 0, '8 BYTEARRAY', 1, 1, True)
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_scatter_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_scatter_extension


class ExtSubdivisionProperties(PropertyGroup):
    enabled = BoolProperty(name="Subdivision Modifier", default=False, )
    level = IntProperty(name="Subdivision Level", default=2, min=0, max=99, )
    scheme = EnumProperty(name="Subdivision Scheme", items=[('0', "Catmull-Clark", ""), ('1', "Loop", "")], default='0', )
    interpolation = EnumProperty(name="UV Interpolation", items=[('0', "None", ""), ('1', "Edges", ""), ('2', "Edges And Corners", ""), ('3', "Sharp", "")], default='2', )
    crease = FloatProperty(name="Edge Crease (%)", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    smooth = FloatProperty(name="Smooth Angle", default=math.radians(90.000), min=math.radians(0.000), max=math.radians(360.000), precision=1, subtype='ANGLE', )
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_subdivision_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_subdivision_extension


class ExtSeaProperties(PropertyGroup):
    enabled = BoolProperty(name="Maxwell Sea", default=False, )
    hide_parent = BoolProperty(name="Hide Container Object", default=True, )
    resolution = EnumProperty(name="Quality", items=[('0', "4x4", ""), ('1', "8x8", ""), ('2', "16x16", ""), ('3', "32x32", ""), ('4', "64x64", ""),
                                                     ('5', "128x128", ""), ('6', "256x256", ""), ('7', "512x512", ""), ('8', "1024x1024", ""),
                                                     ('9', "2048x2048", ""), ('10', "4096x4096", ""), ('11', "8192x8192", ""), ], default='6', )
    reference_time = FloatProperty(name="Reference Time (s)", default=0.0, min=0.0, max=100000.0, precision=4, )
    ocean_wind_mod = FloatProperty(name="Wind Speed (m/s)", default=30.0, min=0.0, max=100000.0, precision=3, )
    ocean_wind_dir = FloatProperty(name="Wind Direction (º)", default=math.radians(45.000), min=math.radians(0.000), max=math.radians(360.000), precision=1, subtype='ANGLE', )
    vertical_scale = FloatProperty(name="Vertical Scale", default=0.1, min=0.0, max=100000.0, precision=5, )
    damp_factor_against_wind = FloatProperty(name="Weight Against Wind", default=0.5, min=0.0, max=1.0, precision=4, subtype='PERCENTAGE', )
    ocean_wind_alignment = FloatProperty(name="Wind Alignment", default=2.0, min=0.0, max=100000.0, precision=4, )
    ocean_min_wave_length = FloatProperty(name="Min Wave Length (m)", default=0.1, min=0.0, max=100000.0, precision=4, )
    ocean_dim = FloatProperty(name="Dimension (m)", default=250.0, min=0.0, max=1000000.0, precision=2, )
    ocean_depth = FloatProperty(name="Depth (m)", default=200.0, min=0.0, max=100000.0, precision=2, )
    ocean_seed = IntProperty(name="Seed", default=4217, min=0, max=65535, )
    enable_choppyness = BoolProperty(name="Enable Choppyness", default=False, )
    choppy_factor = FloatProperty(name="Choppy Factor", default=0.0, min=0.0, max=100000.0, precision=2, )
    enable_white_caps = BoolProperty(name="Enable White Caps", default=False, )
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_sea_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_sea_extension


class ExtClonerProperties(PropertyGroup):
    source = EnumProperty(name="Source", items=[('BLENDER_PARTICLES', "Blender Particles", ""), ('EXTERNAL_BIN', "External Bin", "")], default='BLENDER_PARTICLES', )
    directory = StringProperty(name=".bin Output Directory", default="//", subtype='DIR_PATH', description="Output directory for .bin file(s)", )
    overwrite = BoolProperty(name="Overwrite Existing", default=True, )
    bl_use_velocity = BoolProperty(name="Particle Velocity", default=True, )
    bl_use_size = BoolProperty(name="Size Per Particle", default=False, )
    bl_size = FloatProperty(name="Size", default=0.1, min=0.000001, max=1000000.0, step=3, precision=6, )
    
    filename = StringProperty(name="File Name", default="", subtype='FILE_PATH', )
    embed = BoolProperty(name="Embed in MXS", default=True, )
    
    radius = FloatProperty(name="Radius Multiplier", default=1.0, min=0.000001, max=1000000.0, )
    mb_factor = FloatProperty(name="Motion Blur Multiplier", default=1.0, min=0.0, max=1000000.0, )
    load_percent = FloatProperty(name="Load (%)", default=100.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    start_offset = IntProperty(name="Start Offset", default=0, min=0, max=100000000, )
    extra_npp = IntProperty(name="Extra Part. Per Particle", default=0, min=0, max=100000000, )
    extra_p_dispersion = FloatProperty(name="Extra Part. Dispersion", default=0.0, min=0.0, max=1000000.0, )
    extra_p_deformation = FloatProperty(name="Extra Part. Deformation", default=0.0, min=0.0, max=1000000.0, )
    align_to_velocity = BoolProperty(name="Align To Velocity", default=False, )
    scale_with_radius = BoolProperty(name="Scale With Particle Radius", default=False, )
    inherit_obj_id = BoolProperty(name="Inherit Object Id", default=False, )
    
    display_percent = FloatProperty(name="Display Percent (%)", default=10.0, min=0.0, max=100.0, precision=0, subtype='PERCENTAGE', )
    display_max = IntProperty(name="Display Max. Particles", default=1000, min=0, max=100000, )
    
    # axis_system = EnumProperty(name="PRT & ABC Axis System", items=[('YZX_0', "YZX (xsi maya houdini)", ""), ('ZXY_1', "ZXY (3dsmax maya)", ""), ('YXZ_2', "YXZ (lw c4d rf)", "")], default='YZX_0', )
    # frame = IntProperty(name="Frame Number", default=0, min=-100000000, max=100000000, )
    # fps = FloatProperty(name="FPS", default=1.0, min=0.0, max=1000000.0, )
    
    @classmethod
    def register(cls):
        bpy.types.ParticleSettings.maxwell_cloner_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.ParticleSettings.maxwell_cloner_extension


class ExtVolumetricsProperties(PropertyGroup):
    enabled = BoolProperty(name="Enabled", default=False, )
    vtype = EnumProperty(name="Type", items=[('CONSTANT_1', "Constant", ""), ('NOISE3D_2', "Noise 3D", "")], default='CONSTANT_1', )
    
    density = FloatProperty(name="Field Density", default=1.0, min=0.000001, max=10000.0, precision=6, )
    
    noise_seed = IntProperty(name="Seed", default=4357, min=0, max=1000000, )
    noise_low = FloatProperty(name="Low Value", default=0.0, min=0.0, max=1.0, precision=6, )
    noise_high = FloatProperty(name="High Value", default=1.0, min=0.000001, max=1.0, precision=6, )
    noise_detail = FloatProperty(name="Detail", default=2.2, min=1.0, max=100.0, precision=4, )
    noise_octaves = IntProperty(name="Octaves", default=4, min=1, max=50, )
    noise_persistence = FloatProperty(name="Persistance", default=0.55, min=0.0, max=1.0, precision=4, )
    
    material = StringProperty(name="MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    backface_material = StringProperty(name="Backface MXM File", description="Path to material (.MXM) file", default="", subtype='FILE_PATH', )
    backface_material_embed = BoolProperty(name="Embed Into Scene", default=True, description="When enabled, material file (.MXM) will be embedded to scene, otherwise will be referenced", )
    
    @classmethod
    def register(cls):
        bpy.types.Object.maxwell_volumetrics_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Object.maxwell_volumetrics_extension


class ExtMaterialProperties(PropertyGroup):
    emitter_type = EnumProperty(name="Type", items=[('0', "Area", ""), ('1', "IES", ""), ('2', "Spot", ""), ], default='0', )
    emitter_ies_data = StringProperty(name="Data", default="", subtype='FILE_PATH', )
    emitter_ies_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=100000.0, precision=1, )
    emitter_spot_map_enabled = BoolProperty(name="Spot Map Enabled", default=False, )
    emitter_spot_map = StringProperty(name="Spot Map", default="", )
    emitter_spot_cone_angle = FloatProperty(name="Cone Angle", default=math.radians(45.0), min=math.radians(0.01), max=math.radians(179.99), precision=2, subtype='ANGLE', )
    emitter_spot_falloff_angle = FloatProperty(name="FallOff Angle", default=math.radians(10.0), min=math.radians(0.0), max=math.radians(89.99), precision=2, subtype='ANGLE', )
    emitter_spot_falloff_type = EnumProperty(name="FallOff Type", items=[('0', "Linear", ""), ('1', "Square Root", ""), ('2', "Sinusoidal", ""), ('3', "Squared Sinusoidal", ""),
                                                                         ('4', "Quadratic", ""), ('5', "Cubic", ""), ], default='0', )
    emitter_spot_blur = FloatProperty(name="Blur", default=1.0, min=0.01, max=1000.00, precision=2, )
    emitter_emission = EnumProperty(name="Emission", items=[('0', "Color", ""), ('1', "Temperature", ""), ('2', "HDR Image", ""), ], default='0', )
    emitter_color = FloatVectorProperty(name="Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, subtype='COLOR', )
    emitter_color_black_body_enabled = BoolProperty(name="Temperature Enabled", default=False, )
    emitter_color_black_body = FloatProperty(name="Temperature (K)", default=6500.0, min=273.0, max=100000.0, precision=1, )
    emitter_luminance = EnumProperty(name="Luminance", items=[('0', "Power & Efficacy", ""), ('1', "Lumen", ""), ('2', "Lux", ""), ('3', "Candela", ""), ('4', "Luminance", ""), ], default='0', )
    emitter_luminance_power = FloatProperty(name="Power (W)", default=40.0, min=0.0, max=1000000000.0, precision=1, )
    emitter_luminance_efficacy = FloatProperty(name="Efficacy (lm/W)", default=17.6, min=0.0, max=683.0, precision=1, )
    emitter_luminance_output = FloatProperty(name="Output (lm, lm, lm/m, cd, cd/m)", default=100.0, min=0.0, max=1000000000.0, precision=1, )
    emitter_temperature_value = FloatProperty(name="Value (K)", default=6500.0, min=273.0, max=100000.0, precision=3, )
    emitter_hdr_map = StringProperty(name="Image", default="", )
    emitter_hdr_intensity = FloatProperty(name="Intensity", default=1.0, min=0.0, max=1000000.0, precision=1, )
    
    ags_color = FloatVectorProperty(name="Color", default=(1.0, 1.0, 1.0), min=0.0, max=1.0, subtype='COLOR', )
    ags_reflection = FloatProperty(name="Reflection (%)", default=12.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    ags_type = EnumProperty(name="Type", items=[('0', "Normal", ""), ('1', "Clear", "")], default='0', )
    
    opaque_color_type = BoolProperty(name="Color Type", default=False, )
    opaque_color = FloatVectorProperty(name="Color", default=(220 / 255, 220 / 255, 220 / 255), min=0.0, max=1.0, subtype='COLOR', )
    opaque_color_map = StringProperty(name="Color Map", default="", )
    opaque_shininess_type = BoolProperty(name="Shininess Type", default=False, )
    opaque_shininess = FloatProperty(name="Shininess (%)", default=40.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    opaque_shininess_map = StringProperty(name="Shininess Map", default="", )
    opaque_roughness_type = BoolProperty(name="Roughness Type", default=False, )
    opaque_roughness = FloatProperty(name="Roughness (%)", default=25.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    opaque_roughness_map = StringProperty(name="Roughness Map", default="", )
    opaque_clearcoat = BoolProperty(name="Clearcoat", default=False, )
    
    transparent_color_type = BoolProperty(name="Color Type", default=False, )
    transparent_color = FloatVectorProperty(name="Color", default=(182 / 255, 182 / 255, 182 / 255), min=0.0, max=1.0, subtype='COLOR', )
    transparent_color_map = StringProperty(name="Color Map", default="", )
    transparent_ior = FloatProperty(name="Ref. Index", default=1.51, min=1.001, max=2.5, precision=3, )
    transparent_transparency = FloatProperty(name="Transparency (cm)", default=30.0, min=0.1, max=999.0, precision=1, )
    transparent_roughness_type = BoolProperty(name="Roughness Type", default=False, )
    transparent_roughness = FloatProperty(name="Roughness (%)", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    transparent_roughness_map = StringProperty(name="Roughness Map", default="", )
    transparent_specular_tint = FloatProperty(name="Specular Tint (%)", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    transparent_dispersion = FloatProperty(name="Dispersion (%)", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    transparent_clearcoat = BoolProperty(name="Clearcoat", default=False, )
    
    metal_ior = EnumProperty(name="Type", items=[('0', "Aluminium", ""), ('1', "Chromium", ""), ('2', "Cobalt", ""), ('3', "Copper", ""), ('4', "Germanium", ""), ('5', "Gold", ""),
                                                 ('6', "Iron", ""), ('7', "Nickel", ""), ('8', "Silver", ""), ('9', "Titanium", ""), ('10', "Vanadium", ""), ], default='0', )
    metal_tint = FloatProperty(name="Tint", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    metal_color_type = BoolProperty(name="Color Type", default=False, )
    metal_color = FloatVectorProperty(name="Color", default=(167 / 255, 167 / 255, 167 / 255), min=0.0, max=1.0, subtype='COLOR', )
    metal_color_map = StringProperty(name="Color Map", default="", )
    metal_roughness_type = BoolProperty(name="Roughness Type", default=False, )
    metal_roughness = FloatProperty(name="Roughness", default=30.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    metal_roughness_map = StringProperty(name="Roughness Map", default="", )
    metal_anisotropy_type = BoolProperty(name="Anisotropy Type", default=False, )
    metal_anisotropy = FloatProperty(name="Anisotropy", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    metal_anisotropy_map = StringProperty(name="Anisotropy Map", default="", )
    metal_angle_type = BoolProperty(name="Angle Type", default=False, )
    metal_angle = FloatProperty(name="Angle", default=math.radians(0.0), min=math.radians(0.0), max=math.radians(360.0), precision=1, subtype='ANGLE', )
    metal_angle_map = StringProperty(name="Angle Map", default="", )
    metal_dust_type = BoolProperty(name="Dust & Dirt Type", default=False, )
    metal_dust = FloatProperty(name="Dust & Dirt", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    metal_dust_map = StringProperty(name="Dust & Dirt Map", default="", )
    metal_perforation_enabled = BoolProperty(name="Perforation Enabled", default=False, )
    metal_perforation_map = StringProperty(name="Perforation Map", default="", )
    
    translucent_scale = FloatProperty(name="Scale (x10 cm)", default=8.0, min=0.00001, max=1000000.0, precision=2, )
    translucent_ior = FloatProperty(name="Ref. Index", default=1.3, min=1.001, max=2.5, precision=3, )
    translucent_color_type = BoolProperty(name="Color Type", default=False, )
    translucent_color = FloatVectorProperty(name="Color", default=(250 / 255, 245 / 255, 230 / 255), min=0.0, max=1.0, subtype='COLOR', )
    translucent_color_map = StringProperty(name="Color Map", default="", )
    translucent_hue_shift = FloatProperty(name="Hue Shift", default=0.0, min=-120.0, max=120.0, precision=1, )
    translucent_invert_hue = BoolProperty(name="Invert Hue", default=True, )
    translucent_vibrance = FloatProperty(name="Vibrance", default=11.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    translucent_density = FloatProperty(name="Density", default=90.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    translucent_opacity = FloatProperty(name="Opacity", default=50.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    translucent_roughness_type = BoolProperty(name="Roughness Type", default=False, )
    translucent_roughness = FloatProperty(name="Roughness", default=17.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    translucent_roughness_map = StringProperty(name="Roughness Map", default="", )
    translucent_specular_tint = FloatProperty(name="Specular Tint (%)", default=0.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    translucent_clearcoat = BoolProperty(name="Clearcoat", default=False, )
    translucent_clearcoat_ior = FloatProperty(name="Clearcoat IOR", default=1.3, min=1.001, max=2.5, precision=3, )
    
    carpaint_color = FloatVectorProperty(name="Color", default=(100 / 255, 0 / 255, 16 / 255), min=0.0, max=1.0, subtype='COLOR', )
    carpaint_metallic = FloatProperty(name="Metallic", default=100.0, min=0.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    carpaint_topcoat = FloatProperty(name="Topcoat", default=50.0, min=1.001, max=100.0, precision=3, subtype='PERCENTAGE', )
    
    # hair_color_type = BoolProperty(name="Color Type", default=False, )
    # hair_color = FloatVectorProperty(name="Color", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, subtype='COLOR', )
    # hair_color_map = StringProperty(name="Color Map", default="", )
    # hair_root_tip_map = StringProperty(name="Root-Tip Map", default="", )
    # hair_root_tip_weight_type = BoolProperty(name="Root-Tip Weight Type", default=False, )
    # hair_root_tip_weight = FloatProperty(name="Root-Tip Weight", default=50.0, min=1.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    # hair_root_tip_weight_map = StringProperty(name="Root-Tip Weight Map", default="", )
    # hair_primary_highlight_strength = FloatProperty(name="Strength", default=40.0, min=1.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    # hair_primary_highlight_spread = FloatProperty(name="Spread", default=36.0, min=1.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    # hair_primary_highlight_tint = FloatVectorProperty(name="Tint", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, subtype='COLOR', )
    # hair_secondary_highlight_strength = FloatProperty(name="Strength", default=40.0, min=1.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    # hair_secondary_highlight_spread = FloatProperty(name="Spread", default=45.0, min=1.0, max=100.0, precision=1, subtype='PERCENTAGE', )
    # hair_secondary_highlight_tint = FloatVectorProperty(name="Tint", default=(255 / 255, 255 / 255, 255 / 255), min=0.0, max=1.0, subtype='COLOR', )
    
    @classmethod
    def register(cls):
        bpy.types.Material.maxwell_material_extension = PointerProperty(type=cls)
    
    @classmethod
    def unregiser(cls):
        del bpy.types.Material.maxwell_material_extension
