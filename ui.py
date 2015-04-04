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

import bpy
from bpy.types import Panel
from mathutils import Matrix, Vector

from bl_ui.properties_data_camera import CameraButtonsPanel
from bl_ui.properties_object import ObjectButtonsPanel
from bl_ui.properties_render import RenderButtonsPanel
from bl_ui.properties_world import WorldButtonsPanel
from bl_ui.properties_render_layer import RenderLayerButtonsPanel
from bl_ui.properties_material import MaterialButtonsPanel
from bl_ui.properties_texture import TextureButtonsPanel
from bl_ui.properties_particle import ParticleButtonsPanel
from bl_ui.properties_data_lamp import DataButtonsPanel

from .engine import MaxwellRenderExportEngine


class ExportPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        sub = l.column()
        
        r = sub.row(align=True)
        r.operator("maxwell_render.render_export")
        r.operator("maxwell_render.animation_export")
        
        sub.label("Scene Export Directory:")
        sub.prop(m, 'export_output_directory', text="")


class ExportOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export Options"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        sub = l.column()
        
        sub.label("Workflow:")
        sub.prop(m, 'export_open_with')
        sub.prop(m, 'instance_app')
        
        sub.separator()
        r = sub.row()
        r.prop(m, 'export_overwrite')
        if(m.export_incremental):
            r.enabled = False
        sub.prop(m, 'export_incremental')
        
        sub.label("Options:")
        sub.prop(m, 'export_use_instances')
        sub.prop(m, 'export_keep_intermediates')
        sub.prop(m, 'export_log_open', )


class ExportSpecialsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export Specials"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        b = sub.box()
        
        b.prop(m, 'export_wireframe')
        if(m.export_wireframe):
            c = b.column()
            c.label("Wireframe Options:")
            r = c.row(align=True)
            r.prop(m, 'export_edge_radius')
            r.prop(m, 'export_edge_resolution')
            c.separator()
            
            c.label("Wire Material:")
            r = c.row()
            r.prop(m, 'export_wire_mat_color_id', text="ID", )
            r = c.row()
            r.prop(m, 'export_wire_mat_reflectance_0', text="Reflectance 0", )
            r = c.row()
            r.prop(m, 'export_wire_mat_reflectance_90', text="Reflectance 90", )
            r = c.row()
            r.prop(m, 'export_wire_mat_roughness', text="Roughness", )
            c.separator()
            
            c.label("Clay Material:")
            r = c.row()
            r.prop(m, 'export_clay_mat_color_id', text="ID", )
            r = c.row()
            r.prop(m, 'export_clay_mat_reflectance_0', text="Reflectance 0", )
            r = c.row()
            r.prop(m, 'export_clay_mat_reflectance_90', text="Reflectance 90", )
            r = c.row()
            r.prop(m, 'export_clay_mat_roughness', text="Roughness", )


class SceneOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Scene"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'scene_time')
        sub.prop(m, 'scene_sampling_level')
        r = sub.row()
        r.prop(m, 'scene_multilight')
        r.prop(m, 'scene_multilight_type', text="", )
        r = sub.row()
        r.prop(m, 'scene_cpu_threads')
        # r.prop(m, 'scene_priority')
        sub.prop(m, 'scene_quality')
        # sub.prop(m, 'scene_command_line')


class OutputOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Output"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'output_depth')
        
        s = sub.split(percentage=0.25)
        c = s.column()
        c.prop(m, 'output_image_enabled')
        c = s.column()
        c.prop(m, 'output_image', text="", )
        if(not m.output_image_enabled):
            c.enabled = False
        
        s = sub.split(percentage=0.25)
        c = s.column()
        c.prop(m, 'output_mxi_enabled')
        c = s.column()
        c.prop(m, 'output_mxi', text="", )
        if(not m.output_mxi_enabled):
            c.enabled = False


class MaterialsOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Materials"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        s = sub.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'materials_override')
        c = s.column()
        c.prop(m, 'materials_override_path', text="", )
        if(not m.materials_override):
            c.enabled = False
        
        sub.prop(m, 'materials_search_path')
        sub.separator()
        sub.prop(m, 'materials_directory')


class GlobalsOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Globals"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'globals_motion_blur')
        sub.prop(m, 'globals_diplacement')
        sub.prop(m, 'globals_dispersion')


class ToneMappingOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Tone Mapping"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'tone_color_space')
        sub.prop(m, 'tone_whitepoint')
        sub.prop(m, 'tone_tint')
        r = sub.row()
        r.prop(m, 'tone_burn')
        r.prop(m, 'tone_gamma')
        r = sub.row()
        s = r.split(percentage=0.5)
        c = s.column()
        c.prop(m, 'tone_sharpness')
        c = s.column()
        c.prop(m, 'tone_sharpness_value', text="", )
        if(not m.tone_sharpness):
            c.enabled = False


class SimulensOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Simulens"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'simulens_aperture_map')
        sub.prop(m, 'simulens_obstacle_map')
        r = sub.row()
        r.prop(m, 'simulens_diffraction')
        r.prop(m, 'simulens_diffraction_value', text="", )
        r = sub.row()
        s = r.split(percentage=0.5)
        c = s.column()
        s2 = c.split(percentage=0.075)
        c2 = s2.column()
        c2 = s2.column()
        c2.label('Frequency')
        c = s.column()
        c.prop(m, 'simulens_frequency', text="", )
        r = sub.row()
        r.prop(m, 'simulens_scattering')
        r.prop(m, 'simulens_scattering_value', text="", )
        r = sub.row()
        r.prop(m, 'simulens_devignetting')
        r.prop(m, 'simulens_devignetting_value', text="", )


class IllumCausticsOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Illumination & Caustics"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'illum_caustics_illumination')
        sub.prop(m, 'illum_caustics_refl_caustics')
        sub.prop(m, 'illum_caustics_refr_caustics')


class RenderLayersPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Layer"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, "render_use_layers")
        
        scene = context.scene
        rd = scene.render
        rl = rd.layers.active
        
        s = sub.split()
        c = s.column()
        c.prop(scene, "layers", text="Viewport Layers")
        if(m.render_use_layers == 'RENDER'):
            c.active = False
        c = s.column()
        c.prop(rl, "layers", text="Render Layers")
        if(m.render_use_layers == 'VIEWPORT'):
            c.active = False


class ChannelsOptionsPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Channels"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        sub.prop(m, 'channels_output_mode')
        
        r = sub.row()
        c = r.column()
        c.prop(m, 'channels_render')
        c = r.column()
        c.prop(m, 'channels_render_type', text="", )
        if(not m.channels_render):
            c.enabled = False
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_alpha')
        c = s.column()
        c.prop(m, 'channels_alpha_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_alpha_opaque')
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_z_buffer')
        c = s.column()
        c.prop(m, 'channels_z_buffer_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_z_buffer_near', text="Near (m)")
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_z_buffer_far', text="Far (m)")
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_shadow')
        c = s.column()
        c.prop(m, 'channels_shadow_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_material_id')
        c = s.column()
        c.prop(m, 'channels_material_id_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_object_id')
        c = s.column()
        c.prop(m, 'channels_object_id_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_motion_vector')
        c = s.column()
        c.prop(m, 'channels_motion_vector_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_roughness')
        c = s.column()
        c.prop(m, 'channels_roughness_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_fresnel')
        c = s.column()
        c.prop(m, 'channels_fresnel_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_normals')
        c = s.column()
        c.prop(m, 'channels_normals_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_normals_space', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_position')
        c = s.column()
        c.prop(m, 'channels_position_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_position_space', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_deep')
        c = s.column()
        c.prop(m, 'channels_deep_file', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_deep_type')
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_deep_min_dist')
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_deep_max_samples')
        
        r = sub.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_uv')
        c = s.column()
        c.prop(m, 'channels_uv_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_custom_alpha')
        c = s.column()
        c.prop(m, 'channels_custom_alpha_file', text="", )


class ChannelsCustomAlphasPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Custom Alphas"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        sub.label("Custom Alphas are defined by Object groups.")
        
        for g in bpy.data.groups:
            m = g.maxwell_render
            
            b = sub.box()
            s = b.split(percentage=0.20)
            
            c = s.column()
            c.prop(m, 'custom_alpha_use')
            
            s = s.split(percentage=0.65)
            
            c = s.column()
            r = c.row()
            r.label('Group: "{}"'.format(g.name))
            if(not m.custom_alpha_use):
                c.enabled = False
            
            c = s.column()
            c.prop(m, 'custom_alpha_opaque')
            if(not m.custom_alpha_use):
                c.enabled = False


class EnvironmentPanel(WorldButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Environment"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.world.maxwell_render
        
        sub.prop(m, 'env_type', text="", )


class SkySettingsPanel(WorldButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Sky"
    
    @classmethod
    def poll(cls, context):
        m = context.world.maxwell_render
        e = context.scene.render.engine
        return (m.env_type != 'NONE') and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.world.maxwell_render
        
        sub.prop(m, 'sky_type')
        if(m.sky_type == 'CONSTANT'):
            sub.prop(m, 'dome_intensity')
            sub.prop(m, 'dome_zenith')
            sub.prop(m, 'dome_horizon')
            sub.prop(m, 'dome_mid_point')
        else:
            sub.prop(m, 'sky_use_preset')
            if(m.sky_use_preset):
                sub.prop(m, 'sky_preset')
            else:
                sub.prop(m, 'sky_intensity')
                sub.prop(m, 'sky_planet_refl')
                sub.prop(m, 'sky_ozone')
                sub.prop(m, 'sky_water')
                sub.prop(m, 'sky_turbidity_coeff')
                sub.prop(m, 'sky_wavelength_exp')
                sub.prop(m, 'sky_reflectance')
                sub.prop(m, 'sky_asymmetry')


class SunSettingsPanel(WorldButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Sun"
    
    @classmethod
    def poll(cls, context):
        m = context.world.maxwell_render
        e = context.scene.render.engine
        return (m.env_type != 'NONE') and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.world.maxwell_render
        
        sub.prop(m, 'sun_lamp_priority')
        sub.separator()
        
        sub.prop(m, 'sun_type')
        if(m.sun_type != 'DISABLED'):
            sub.prop(m, 'sun_power')
            sub.prop(m, 'sun_radius_factor')
            r = sub.row()
            r.prop(m, 'sun_temp')
            if(m.sun_type == 'CUSTOM'):
                r.enabled = False
            r = sub.row()
            r.prop(m, 'sun_color')
            if(m.sun_type == 'PHYSICAL'):
                r.enabled = False
            sub.separator()
            
            sub.prop(m, 'sun_location_type')
            if(m.sun_location_type == 'ANGLES'):
                sub.prop(m, 'sun_angles_zenith')
                sub.prop(m, 'sun_angles_azimuth')
            elif(m.sun_location_type == 'DIRECTION'):
                sub.operator('maxwell_render.set_sun', "Set Sun")
                c = sub.column(align=True)
                c.prop(m, 'sun_dir_x')
                c.prop(m, 'sun_dir_y')
                c.prop(m, 'sun_dir_z')
            else:
                r = sub.row(align=True)
                r.prop(m, 'sun_latlong_lat')
                r.prop(m, 'sun_latlong_lon')
                sub.prop(m, 'sun_date')
                sub.prop(m, 'sun_time')
                
                r = sub.row()
                c = r.column()
                c.prop(m, 'sun_latlong_gmt')
                r.prop(m, 'sun_latlong_gmt_auto')
                if(m.sun_latlong_gmt_auto):
                    c.enabled = False
                
                sub.operator('maxwell_render.now', "Now")
                
                sub.prop(m, 'sun_latlong_ground_rotation')


class IBLSettingsPanel(WorldButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "IBL"
    
    @classmethod
    def poll(cls, context):
        m = context.world.maxwell_render
        e = context.scene.render.engine
        return (m.env_type != 'NONE' and m.env_type == 'IMAGE_BASED') and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.world.maxwell_render
        
        sub.prop(m, 'ibl_intensity')
        r = sub.row()
        r.prop(m, 'ibl_interpolation')
        r.prop(m, 'ibl_screen_mapping')
        
        b = sub.box()
        sb = b.column()
        sb.label("Background:")
        sb.prop(m, 'ibl_bg_type')
        sb.prop(m, 'ibl_bg_map')
        sb.prop(m, 'ibl_bg_intensity')
        r = sb.row(align=True)
        r.prop(m, 'ibl_bg_scale_x')
        r.prop(m, 'ibl_bg_scale_y')
        r = sb.row(align=True)
        r.prop(m, 'ibl_bg_offset_x')
        r.prop(m, 'ibl_bg_offset_y')
        
        b = sub.box()
        sb = b.column()
        sb.label("Reflection:")
        sb.prop(m, 'ibl_refl_type')
        if(m.ibl_refl_type == 'HDR_IMAGE'):
            sb.prop(m, 'ibl_refl_map')
            sb.prop(m, 'ibl_refl_intensity')
            r = sb.row(align=True)
            r.prop(m, 'ibl_refl_scale_x')
            r.prop(m, 'ibl_refl_scale_y')
            r = sb.row(align=True)
            r.prop(m, 'ibl_refl_offset_x')
            r.prop(m, 'ibl_refl_offset_y')
        
        b = sub.box()
        sb = b.column()
        sb.label("Refraction:")
        sb.prop(m, 'ibl_refr_type')
        if(m.ibl_refr_type == 'HDR_IMAGE'):
            sb.prop(m, 'ibl_refr_map')
            sb.prop(m, 'ibl_refr_intensity')
            r = sb.row(align=True)
            r.prop(m, 'ibl_refr_scale_x')
            r.prop(m, 'ibl_refr_scale_y')
            r = sb.row(align=True)
            r.prop(m, 'ibl_refr_offset_x')
            r.prop(m, 'ibl_refr_offset_y')
        
        b = sub.box()
        sb = b.column()
        sb.label("Illumination:")
        sb.prop(m, 'ibl_illum_type')
        if(m.ibl_illum_type == 'HDR_IMAGE'):
            sb.prop(m, 'ibl_illum_map')
            sb.prop(m, 'ibl_illum_intensity')
            r = sb.row(align=True)
            r.prop(m, 'ibl_illum_scale_x')
            r.prop(m, 'ibl_illum_scale_y')
            r = sb.row(align=True)
            r.prop(m, 'ibl_illum_offset_x')
            r.prop(m, 'ibl_illum_offset_y')


class SunLampPanel(DataButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Sun"
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        return (o and o.type == 'LAMP' and o.data.type == 'SUN') and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.data.maxwell_render
        
        sub.prop(m, 'override')


class CameraOpticsPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Optics"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.camera.maxwell_render
        o = context.camera
        r = context.scene.render
        
        sub.operator('maxwell_render.auto_focus', "Auto Focus")
        
        cam = context.camera
        sub.prop(o, 'dof_object')
        
        r = sub.row()
        r.enabled = cam.dof_object is None
        r.prop(o, 'dof_distance')
        
        sub.prop(m, 'lens')
        r = sub.row()
        r.prop(o, 'lens')
        if(m.lens == 'TYPE_ORTHO_2'):
            r.enabled = False
        sub.prop(m, 'shutter')
        sub.prop(m, 'fstop')
        if(m.lens == 'TYPE_FISHEYE_3'):
            sub.prop(m, 'fov')
        if(m.lens == 'TYPE_SPHERICAL_4'):
            sub.prop(m, 'azimuth')
        if(m.lens == 'TYPE_CYLINDRICAL_5'):
            sub.prop(m, 'angle')


class CameraSensorPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Sensor"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.camera.maxwell_render
        o = context.camera
        rp = context.scene.render
        
        r = sub.row(align=True)
        r.label("Resolution:")
        
        r.prop(rp, 'resolution_x', text="", )
        r.prop(rp, 'resolution_y', text="", )
        sub.prop(rp, 'resolution_percentage')
        
        r = sub.row(align=True)
        r.label("Filmback (mm):")
        r.prop(o, 'sensor_width', text="", )
        r.prop(o, 'sensor_height', text="", )
        sub.prop(o, 'sensor_fit')
        
        c = sub.column(align=True)
        c.prop(rp, 'pixel_aspect_x')
        c.prop(rp, 'pixel_aspect_y')
        
        sub.prop(m, 'iso')
        sub.prop(m, 'response')
        sub.prop(m, 'screen_region')
        r = sub.row()
        c = r.column(align=True)
        c.prop(m, 'screen_region_x')
        c.prop(m, 'screen_region_y')
        c.enabled = False
        c = r.column(align=True)
        c.prop(m, 'screen_region_w')
        c.prop(m, 'screen_region_h')
        c.enabled = False
        r = sub.row(align=True)
        r.operator("maxwell_render.camera_set_region")
        r.operator("maxwell_render.camera_reset_region")


class CameraOptionsPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.camera.maxwell_render
        o = context.camera
        r = context.scene.render
        
        sub.label("Diaphragm:")
        sub.prop(m, 'aperture')
        r = sub.row()
        r.prop(m, 'diaphragm_blades')
        r.prop(m, 'diaphragm_angle')
        if(m.aperture == 'CIRCULAR'):
            r.enabled = False
        
        sub.prop(m, 'custom_bokeh')
        r = sub.row()
        r.prop(m, 'bokeh_ratio')
        r.prop(m, 'bokeh_angle')
        if(not m.custom_bokeh):
            r.enabled = False
        
        sub.separator()
        sub.label("Rotary Disc Shutter:")
        r = sub.row()
        r.prop(m, 'shutter_angle')
        r.enabled = False
        sub.prop(m, 'frame_rate')
        
        sub.separator()
        sub.label("Z-clip Planes:")
        sub.prop(m, 'zclip')
        r = sub.row(align=True)
        r.prop(o, 'clip_start')
        r.prop(o, 'clip_end')
        
        sub.separator()
        sub.label("Shift Lens:")
        r = sub.row(align=True)
        r.prop(o, 'shift_x')
        r.prop(o, 'shift_y')
        
        sub.prop(m, 'hide')


class ObjectPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Object"
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'LAMP', 'SPEAKER']
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.maxwell_render
        
        sub.prop(m, 'hide')
        sub.prop(m, 'opacity')
        r = sub.row()
        r.prop(m, 'object_id')
        sub.label("Hidden from:")
        s = sub.split(percentage=0.5)
        c = s.column()
        c.prop(m, 'hidden_camera')
        c.prop(m, 'hidden_camera_in_shadow_channel')
        c.prop(m, 'hidden_global_illumination')
        c = s.column()
        c.prop(m, 'hidden_reflections_refractions')
        c.prop(m, 'hidden_zclip_planes')


class ObjectModifiersPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Object Modifiers"
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        
        sub = l.column()
        
        b = sub.box()
        subd = context.object.maxwell_subdivision_extension
        b.prop(subd, 'enabled')
        if(subd.enabled):
            b.prop(subd, 'level')
            r = b.row()
            r.prop(subd, 'scheme', expand=True)
            b.prop(subd, 'interpolation')
            b.prop(subd, 'crease')
            b.prop(subd, 'smooth')
        
        b = sub.box()
        scat = context.object.maxwell_scatter_extension
        b.prop(scat, 'enabled')
        if(scat.enabled):
            b.label("Not implemented yet..", icon='ERROR', )


class MaterialsPanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_options = {'HIDE_HEADER'}
    bl_label = ""
    
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material or context.object) and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        layout = self.layout
        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data
        if(ob):
            row = layout.row()
            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=2)
            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ZOOMIN', text="")
            col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")
            col.menu("MATERIAL_MT_specials", icon='DOWNARROW_HLT', text="")
            if(ob.mode == 'EDIT'):
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")
        split = layout.split(percentage=0.7)
        if(ob):
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()
            if(slot):
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif(mat):
            split.template_ID(space, "pin_id")
            split.separator()


class MaterialPanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "MXM"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.material.maxwell_render
        sub.prop(m, 'mxm_file')
        sub.prop(m, 'embed')
        
        r = sub.row(align=True)
        if(m.mxm_file == ''):
            r.operator('maxwell_render.create_material').backface = False
        else:
            r.operator('maxwell_render.edit_material').backface = False


class MaterialBackfacePanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Backface MXM"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.maxwell_render
        sub.prop(m, 'backface_material_file')
        sub.prop(m, 'backface_material_embed')
        
        r = sub.row(align=True)
        if(m.backface_material_file == ''):
            r.operator('maxwell_render.create_material').backface = True
        else:
            r.operator('maxwell_render.edit_material').backface = True


class TexturePanel(TextureButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Texture"
    
    @classmethod
    def poll(cls, context):
        return False
        
        if(not super().poll(context)):
            return False
        if(context.space_data.texture_context not in ['MATERIAL', 'PARTICLES']):
            return False
        return True
    
    def draw(self, context):
        l = self.layout
        m = context.texture.maxwell_render
        
        # tex = context.texture
        # l.template_image(tex, "image", tex.image_user)
        
        tex = None
        ts = context.texture_slot
        if(ts.texture is not None):
            if(ts.texture.type == 'IMAGE'):
                tex = ts.texture
        if(tex is None):
            l.active = False
        
        
        # s = l.split(percentage=0.25)
        # s.label("Path:")
        # s.prop(m, 'path', text="", )
        
        
        # l.prop_search(m, 'path', tex, 'image', text="")
        # l.prop_search(m, "path", bpy.data, "images")
        c = l.column()
        if(tex is not None and tex.image):
            image = tex.image
            c.active = False
            c.enabled = False
            c.prop(image, 'filepath', text="Path:")
            c.prop(tex, 'image')
        else:
            c.label("Load an image", icon='ERROR', )
        
        # l.template_image(tex, "image", tex.image_user, )
        
        # l.separator()
        l.label("Projection Properties:")
        l.prop(m, 'use_global_map')
        
        sub = l.column()
        sub.active = not m.use_global_map
        
        # l.prop(m, 'channel')
        tex = context.texture_slot
        # tex.texture_coords = 'UV'
        
        # col = split.column()
        # col.prop(tex, "texture_coords", text="")
        
        ob = context.object
        
        r = sub.row()
        s = r.split(percentage=0.25)
        s.label(text="Channel:")
        if(len(ob.data.uv_textures) == 0):
            s.label("No UV Maps", icon='ERROR', )
        else:
            s.prop_search(tex, "uv_layer", ob.data, "uv_textures", text="")
        
        r = sub.row()
        r.prop(m, 'tiling_method', expand=True, )
        r = sub.row()
        r.prop(m, 'tiling_units', expand=True, )
        
        r = sub.row()
        r.label("Mirror:")
        r.prop(m, 'mirror_x', text="X", )
        r.prop(m, 'mirror_y', text="Y", )
        
        r = sub.row()
        r.prop(m, 'repeat')
        
        # r = sub.row()
        # r.label("Mirror:")
        # r.prop(m, 'mirror_x', text="X", )
        # r.prop(m, 'mirror_y', text="Y", )
        
        r = sub.row()
        r.prop(m, 'offset')
        
        sub.prop(m, 'rotation')
        
        # r = sub.row()
        # s = r.split(percentage=0.32)
        # s.label(text="Rotation:")
        # s.prop(m, 'rotation')
        
        l.separator()
        l.label("Image Properties:")
        
        sub = l.column()
        r = sub.row()
        r.prop(m, 'invert')
        r.prop(m, 'use_alpha')
        r.prop(m, 'interpolation')
        # sub.prop(m, 'type_interpolation')
        
        # s = sub.split(percentage=0.5)
        # c = s.column(align=True)
        # c.prop(m, 'brightness')
        # c.prop(m, 'contrast')
        # c.prop(m, 'saturation')
        # c.prop(m, 'hue')
        #
        # c = s.column()
        # c.prop(m, 'type_interpolation')
        # c.prop(m, 'clamp')
        
        # r = sub.row()
        # r.prop(m, 'brightness')
        # r.prop(m, 'contrast')
        # r = sub.row()
        # r.prop(m, 'saturation')
        # r.prop(m, 'hue')
        
        sub.prop(m, 'brightness')
        sub.prop(m, 'contrast')
        sub.prop(m, 'saturation')
        sub.prop(m, 'hue')
        
        r = sub.row()
        r.prop(m, 'clamp')


class ParticlesPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Particles"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_render
        
        r = sub.row()
        r.prop(m, 'use', expand=True, )


class GrassExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Grass"
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        settings = 0
        
        if psys:
            settings = psys.settings
        elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
            settings = context.space_data.pin_id
        
        if not settings:
            return False
        
        m = context.particle_system.settings.maxwell_render
        if(m.use != 'GRASS'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        ps = context.particle_system.settings
        m = context.particle_system.settings.maxwell_grass_extension
        
        sub.label("Primitive:")
        s = sub.split(percentage=0.8)
        c = s.column()
        c.prop(m, 'material')
        c = s.column()
        c.prop(m, 'material_embed', text='Embed', )
        
        s = sub.split(percentage=0.8)
        c = s.column()
        c.prop(m, 'backface_material')
        c = s.column()
        c.prop(m, 'backface_material_embed', text='Embed', )
        
        sub.prop(m, 'points_per_blade')
        r = sub.row()
        r.label("Primitive Type:")
        r.prop(m, 'primitive_type', expand=True, )
        sub.separator()
        
        sub.label("Grass Density:")
        sub.prop(m, 'density')
        r = sub.row()
        r.prop_search(m, 'density_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'seed')
        sub.separator()
        
        sub.label("Blade Length:")
        sub.prop(m, 'length')
        r = sub.row()
        r.prop_search(m, 'length_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'length_variation')
        sub.separator()
        
        sub.label("Width:")
        sub.prop(m, 'root_width')
        sub.prop(m, 'tip_width')
        sub.separator()
        
        sub.label("Angle:")
        sub.prop(m, 'direction_type')
        sub.prop(m, 'initial_angle')
        r = sub.row()
        r.prop_search(m, 'initial_angle_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'initial_angle_variation')
        sub.separator()
        
        sub.label("Bend:")
        sub.prop(m, 'start_bend')
        r = sub.row()
        r.prop_search(m, 'start_bend_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'start_bend_variation')
        
        sub.prop(m, 'bend_radius')
        r = sub.row()
        r.prop_search(m, 'bend_radius_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'bend_radius_variation')
        
        sub.prop(m, 'bend_angle')
        r = sub.row()
        r.prop_search(m, 'bend_angle_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'bend_angle_variation')
        sub.separator()
        
        sub.label("Cut Off:")
        sub.prop(m, 'cut_off')
        r = sub.row()
        r.prop_search(m, 'cut_off_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'cut_off_variation')
        sub.separator()
        
        sub.prop(m, 'lod')
        r = sub.row()
        r.prop(m, 'lod_min_distance')
        r.prop(m, 'lod_max_distance')
        if(not m.lod):
            r.enabled = False
        r = sub.row()
        r.prop(m, 'lod_max_distance_density')
        if(not m.lod):
            r.enabled = False
        sub.separator()
        
        sub.label("Display:")
        sub.prop(m, 'display_percent')
        sub.prop(m, 'display_max_blades')


class ParticlesExtObjectPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Particles Object"
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        settings = 0
        
        if psys:
            settings = psys.settings
        elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
            settings = context.space_data.pin_id
        
        if not settings:
            return False
        
        m = context.particle_system.settings.maxwell_render
        # if(m.use == 'HAIR' or m.use == 'PARTICLES'):
        #     return True
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES) and (m.use == 'HAIR' or m.use == 'PARTICLES')
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        mm = context.particle_system.settings.maxwell_render
        if(mm.use == 'HAIR'):
            m = context.particle_system.settings.maxwell_hair_extension
        elif(mm.use == 'PARTICLES'):
            m = context.particle_system.settings.maxwell_particles_extension
        else:
            return
        
        # sub.label("Object Properties:")
        
        s = sub.split(percentage=0.8)
        c = s.column()
        c.prop(m, 'material')
        c = s.column()
        c.prop(m, 'material_embed', text='Embed', )
        
        s = sub.split(percentage=0.8)
        c = s.column()
        c.prop(m, 'backface_material')
        c = s.column()
        c.prop(m, 'backface_material_embed', text='Embed', )
        
        sub.separator()
        
        sub.prop(m, 'hide')
        sub.prop(m, 'hide_parent')
        sub.prop(m, 'opacity')
        r = sub.row()
        r.prop(m, 'object_id')
        sub.separator()
        
        sub.label("Hidden from:")
        s = sub.split(percentage=0.5)
        c = s.column()
        c.prop(m, 'hidden_camera')
        c.prop(m, 'hidden_camera_in_shadow_channel')
        c.prop(m, 'hidden_global_illumination')
        c = s.column()
        c.prop(m, 'hidden_reflections_refractions')
        c.prop(m, 'hidden_zclip_planes')
        sub.separator()


class HairExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Hair Properties"
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        settings = 0
        
        if psys:
            settings = psys.settings
        elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
            settings = context.space_data.pin_id
        
        if not settings:
            return False
        
        m = context.particle_system.settings.maxwell_render
        if(m.use != 'HAIR'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_hair_extension
        
        # sub.label("Not implemented yet..", icon='ERROR', )
        
        # sub.label("Object Properties:")
        #
        # s = sub.split(percentage=0.8)
        # c = s.column()
        # c.prop(m, 'material')
        # c = s.column()
        # c.prop(m, 'material_embed', text='Embed', )
        #
        # s = sub.split(percentage=0.8)
        # c = s.column()
        # c.prop(m, 'backface_material')
        # c = s.column()
        # c.prop(m, 'backface_material_embed', text='Embed', )
        #
        # sub.separator()
        #
        # sub.prop(m, 'hide')
        # sub.prop(m, 'hide_parent')
        # sub.prop(m, 'opacity')
        # r = sub.row()
        # r.prop(m, 'object_id')
        # sub.separator()
        #
        # sub.label("Hidden from:")
        # s = sub.split(percentage=0.5)
        # c = s.column()
        # c.prop(m, 'hidden_camera')
        # c.prop(m, 'hidden_camera_in_shadow_channel')
        # c.prop(m, 'hidden_global_illumination')
        # c = s.column()
        # c.prop(m, 'hidden_reflections_refractions')
        # c.prop(m, 'hidden_zclip_planes')
        # sub.separator()
        
        # sub.label("Hair Properties:")
        r = sub.row()
        r.prop(m, 'hair_type', expand=True, )
        sub.separator()
        
        if(m.hair_type == 'GRASS'):
            c = sub.column(align=True)
            c.prop(m, 'grass_root_width')
            c.prop(m, 'grass_tip_width')
        else:
            c = sub.column(align=True)
            c.prop(m, 'hair_root_radius')
            c.prop(m, 'hair_tip_radius')
        
        sub.separator()
        sub.prop(m, 'display_percent')
        if(m.hair_type == 'GRASS'):
            sub.prop(m, 'display_max_blades')
        else:
            sub.prop(m, 'display_max_hairs')


class ParticlesExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Particles Properties"
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        settings = 0
        
        if psys:
            settings = psys.settings
        elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
            settings = context.space_data.pin_id
        
        if not settings:
            return False
        
        m = context.particle_system.settings.maxwell_render
        if(m.use != 'PARTICLES'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_particles_extension
        
        # sub.label("Object Properties:")
        # s = sub.split(percentage=0.7)
        # c = s.column()
        # c.prop(m, 'material_file')
        # c = s.column()
        # c.prop(m, 'material_embed', text='Embed', )
        # sub.separator()
        # sub.prop(m, 'hide')
        # sub.prop(m, 'hide_parent')
        # sub.prop(m, 'opacity')
        # r = sub.row()
        # r.prop(m, 'object_id')
        # sub.separator()
        # sub.label("Hidden from:")
        # s = sub.split(percentage=0.5)
        # c = s.column()
        # c.prop(m, 'hidden_camera')
        # c.prop(m, 'hidden_camera_in_shadow_channel')
        # c.prop(m, 'hidden_global_illumination')
        # c = s.column()
        # c.prop(m, 'hidden_reflections_refractions')
        # c.prop(m, 'hidden_zclip_planes')
        # sub.separator()
        
        # sub.label("Sequence:")
        sub.prop(m, 'bin_filename')
        sub.prop(m, 'bin_radius_multiplier')
        sub.prop(m, 'bin_motion_blur_multiplier')
        sub.prop(m, 'bin_shutter_speed')
        sub.prop(m, 'bin_load_particles')
        sub.prop(m, 'bin_axis_system')
        sub.prop(m, 'bin_frame_number')
        sub.prop(m, 'bin_fps')
        sub.separator()
        
        sub.prop(m, 'bin_advanced')
        
        if(m.bin_advanced):
            sub.label("Multipoint:")
            sub.prop(m, 'bin_extra_create_np_pp')
            sub.prop(m, 'bin_extra_dispersion')
            sub.prop(m, 'bin_extra_deformation')
            sub.separator()
            
            sub.label("Extra Arrays Loading:")
            s = sub.split(percentage=0.5)
            c = s.column()
            c.prop(m, 'bin_load_force')
            c.prop(m, 'bin_load_vorticity')
            c.prop(m, 'bin_load_normal')
            c.prop(m, 'bin_load_neighbors_num')
            c.prop(m, 'bin_load_uv')
            c.prop(m, 'bin_load_age')
            c.prop(m, 'bin_load_isolation_time')
            c = s.column()
            c.prop(m, 'bin_load_viscosity')
            c.prop(m, 'bin_load_density')
            c.prop(m, 'bin_load_pressure')
            c.prop(m, 'bin_load_mass')
            c.prop(m, 'bin_load_temperature')
            c.prop(m, 'bin_load_id')
            sub.separator()
            
            sub.label("Magnitude Normalizing Values:")
            s = sub.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_force')
            c.prop(m, 'bin_max_force')
            c = s.column(align=True)
            c.prop(m, 'bin_min_vorticity')
            c.prop(m, 'bin_max_vorticity')
            s = sub.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_nneighbors')
            c.prop(m, 'bin_max_nneighbors')
            c = s.column(align=True)
            c.prop(m, 'bin_min_age')
            c.prop(m, 'bin_max_age')
            s = sub.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_isolation_time')
            c.prop(m, 'bin_max_isolation_time')
            c = s.column(align=True)
            c.prop(m, 'bin_min_viscosity')
            c.prop(m, 'bin_max_viscosity')
            s = sub.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_density')
            c.prop(m, 'bin_max_density')
            c = s.column(align=True)
            c.prop(m, 'bin_min_pressure')
            c.prop(m, 'bin_max_pressure')
            s = sub.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_mass')
            c.prop(m, 'bin_max_mass')
            c = s.column(align=True)
            c.prop(m, 'bin_min_temperature')
            c.prop(m, 'bin_max_temperature')
            s = sub.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_velocity')
            c.prop(m, 'bin_max_velocity')


class MesherExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Mesher"
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        settings = 0
        
        if psys:
            settings = psys.settings
        elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
            settings = context.space_data.pin_id
        
        if not settings:
            return False
        
        m = context.particle_system.settings.maxwell_render
        if(m.use != 'MESHER'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        # m = context.particle_system.settings.maxwell_mesher_extension
        
        sub.label("Not implemented yet..", icon='ERROR', )


class ScatterExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Scatter"
    
    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        engine = context.scene.render.engine
        settings = 0
        
        if psys:
            settings = psys.settings
        elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
            settings = context.space_data.pin_id
        
        if not settings:
            return False
        
        m = context.particle_system.settings.maxwell_render
        if(m.use != 'SCATTER'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        # m = context.particle_system.settings.maxwell_scatter_extension
        
        sub.label("Not implemented yet..", icon='ERROR', )
