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

import platform

import bpy
from bpy.types import Panel, Menu
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
        r.operator("render.render", text="Render", icon='RENDER_STILL')
        r.operator("render.render", text="Animation", icon='RENDER_ANIMATION').animation = True
        
        rp = context.scene.render
        sub.separator()
        s = sub.split(percentage=0.33)
        s.label(text="Display:")
        r = s.row(align=True)
        r.prop(rp, "display_mode", text="")
        r.prop(rp, "use_lock_interface", icon_only=True)
        
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
        r = sub.row()
        r0 = r.row()
        r0.prop(m, 'export_overwrite')
        if(m.export_incremental):
            r0.enabled = False
        r1 = r.row()
        r1.prop(m, 'export_incremental')
        
        sub.prop(m, 'export_open_with')
        sub.prop(m, 'instance_app')
        sub.separator()
        
        sub.label("Options:")
        r = sub.row()
        c = r.column()
        c.prop(m, 'export_use_instances')
        c = r.column()
        c.prop(m, 'export_keep_intermediates')
        if(platform.system() != 'Darwin'):
            c.enabled = False
        r = sub.row()
        r.prop(m, 'export_log_open', )
        r.prop(m, 'export_protect_mxs', )


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
            sc = c.column(align=True)
            sc.prop(m, 'export_edge_radius')
            sc.prop(m, 'export_edge_resolution')
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
        
        c = sub.column_flow(align=True)
        r = c.row(align=True)
        r.menu("Render_presets", text=bpy.types.Render_presets.bl_label)
        r.operator("maxwell_render.render_preset_add", text="", icon='ZOOMIN')
        r.operator("maxwell_render.render_preset_add", text="", icon='ZOOMOUT').remove_active = True
        sub.separator()
        
        sub.prop(m, 'scene_time')
        sub.prop(m, 'scene_sampling_level')
        
        # r = sub.row()
        # s = r.split(percentage=0.62)
        # c = s.column()
        # c.prop(m, 'scene_multilight')
        # c = s.column()
        # c.prop(m, 'scene_multilight_type', text="", )
        
        s = sub.split(percentage=0.2)
        c = s.column()
        c.label("Multilight:")
        c = s.column()
        r = c.row()
        r.prop(m, 'scene_multilight', text="", )
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


class ExtraSamplingOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Extra Sampling"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        m = context.scene.maxwell_render
        self.layout.prop(m, "extra_sampling_enabled", text="")
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        r = sub.row()
        s = r.split(percentage=0.75)
        c = s.column()
        c.prop(m, 'extra_sampling_mask')
        c = s.column()
        c.prop(m, 'extra_sampling_invert', text="Invert", )
        
        sub.prop(m, 'extra_sampling_sl')
        sub.prop(m, 'extra_sampling_custom_alpha')
        sub.prop(m, 'extra_sampling_user_bitmap')


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
        
        s = sub.split(percentage=0.35)
        c = s.column()
        c.prop(m, 'simulens_diffraction')
        c = s.column()
        c.prop(m, 'simulens_diffraction_value', text="", )
        
        s = sub.split(percentage=0.35)
        c = s.column()
        c.label('Frequency')
        c = s.column()
        c.prop(m, 'simulens_frequency', text="", )
        
        s = sub.split(percentage=0.35)
        c = s.column()
        c.prop(m, 'simulens_scattering')
        c = s.column()
        c.prop(m, 'simulens_scattering_value', text="", )
        
        s = sub.split(percentage=0.35)
        c = s.column()
        c.prop(m, 'simulens_devignetting')
        c = s.column()
        c.prop(m, 'simulens_devignetting_value', text="", )


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
        
        # sub.prop(m, "render_use_layers")
        
        scene = context.scene
        rd = scene.render
        rl = rd.layers.active
        
        s = sub.split()
        c = s.column()
        # c.prop(scene, "layers", text="Viewport Layers")
        c.prop(scene, "layers", text="Scene")
        # if(m.render_use_layers == 'RENDER'):
        #     c.active = False
        c = s.column()
        # c.prop(rl, "layers", text="Render Layers")
        c.prop(rl, "layers", text="Layer")
        # if(m.render_use_layers == 'VIEWPORT'):
        #     c.active = False
        c.separator()


class ChannelsOptionsPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Channels"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        
        c = sub.column_flow(align=True)
        r = c.row(align=True)
        r.menu("Channels_presets", text=bpy.types.Channels_presets.bl_label)
        r.operator("maxwell_render.channels_preset_add", text="", icon='ZOOMIN')
        r.operator("maxwell_render.channels_preset_add", text="", icon='ZOOMOUT').remove_active = True
        sub.separator()
        
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
        
        c = sub.column_flow(align=True)
        r = c.row(align=True)
        r.menu("Environment_presets", text=bpy.types.Environment_presets.bl_label)
        r.operator("maxwell_render.environment_preset_add", text="", icon='ZOOMIN')
        r.operator("maxwell_render.environment_preset_add", text="", icon='ZOOMOUT').remove_active = True
        sub.separator()
        
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
            sub.separator()
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
        # r = sb.row(align=True)
        # r.prop(m, 'ibl_bg_scale_x')
        # r.prop(m, 'ibl_bg_scale_y')
        # r = sb.row(align=True)
        # r.prop(m, 'ibl_bg_offset_x')
        # r.prop(m, 'ibl_bg_offset_y')
        r = sb.row()
        c = r.column(align=True)
        c.prop(m, 'ibl_bg_scale_x')
        c.prop(m, 'ibl_bg_scale_y')
        c = r.column(align=True)
        c.prop(m, 'ibl_bg_offset_x')
        c.prop(m, 'ibl_bg_offset_y')
        
        b = sub.box()
        sb = b.column()
        sb.label("Reflection:")
        sb.prop(m, 'ibl_refl_type')
        if(m.ibl_refl_type == 'HDR_IMAGE'):
            sb.prop(m, 'ibl_refl_map')
            sb.prop(m, 'ibl_refl_intensity')
            # r = sb.row(align=True)
            # r.prop(m, 'ibl_refl_scale_x')
            # r.prop(m, 'ibl_refl_scale_y')
            # r = sb.row(align=True)
            # r.prop(m, 'ibl_refl_offset_x')
            # r.prop(m, 'ibl_refl_offset_y')
            r = sb.row()
            c = r.column(align=True)
            c.prop(m, 'ibl_refl_scale_x')
            c.prop(m, 'ibl_refl_scale_y')
            c = r.column(align=True)
            c.prop(m, 'ibl_refl_offset_x')
            c.prop(m, 'ibl_refl_offset_y')
        
        b = sub.box()
        sb = b.column()
        sb.label("Refraction:")
        sb.prop(m, 'ibl_refr_type')
        if(m.ibl_refr_type == 'HDR_IMAGE'):
            sb.prop(m, 'ibl_refr_map')
            sb.prop(m, 'ibl_refr_intensity')
            # r = sb.row(align=True)
            # r.prop(m, 'ibl_refr_scale_x')
            # r.prop(m, 'ibl_refr_scale_y')
            # r = sb.row(align=True)
            # r.prop(m, 'ibl_refr_offset_x')
            # r.prop(m, 'ibl_refr_offset_y')
            r = sb.row()
            c = r.column(align=True)
            c.prop(m, 'ibl_refr_scale_x')
            c.prop(m, 'ibl_refr_scale_y')
            c = r.column(align=True)
            c.prop(m, 'ibl_refr_offset_x')
            c.prop(m, 'ibl_refr_offset_y')
        
        b = sub.box()
        sb = b.column()
        sb.label("Illumination:")
        sb.prop(m, 'ibl_illum_type')
        if(m.ibl_illum_type == 'HDR_IMAGE'):
            sb.prop(m, 'ibl_illum_map')
            sb.prop(m, 'ibl_illum_intensity')
            # r = sb.row(align=True)
            # r.prop(m, 'ibl_illum_scale_x')
            # r.prop(m, 'ibl_illum_scale_y')
            # r = sb.row(align=True)
            # r.prop(m, 'ibl_illum_offset_x')
            # r.prop(m, 'ibl_illum_offset_y')
            r = sb.row()
            c = r.column(align=True)
            c.prop(m, 'ibl_illum_scale_x')
            c.prop(m, 'ibl_illum_scale_y')
            c = r.column(align=True)
            c.prop(m, 'ibl_illum_offset_x')
            c.prop(m, 'ibl_illum_offset_y')


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


class CameraPresetsPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Camera Presets"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        c = sub.column_flow(align=True)
        r = c.row(align=True)
        r.menu("Camera_presets", text=bpy.types.Camera_presets.bl_label)
        r.operator("maxwell_render.camera_preset_add", text="", icon='ZOOMIN')
        r.operator("maxwell_render.camera_preset_add", text="", icon='ZOOMOUT').remove_active = True


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
    
    _frame_rate_args_prev = None
    _preset_class = None
    
    @staticmethod
    def _draw_framerate_label(*args):
        # avoids re-creating text string each draw
        if CameraSensorPanel._frame_rate_args_prev == args:
            return CameraSensorPanel._frame_rate_ret
        
        fps, fps_base, preset_label = args
        
        if fps_base == 1.0:
            fps_rate = round(fps)
        else:
            fps_rate = round(fps / fps_base, 2)
        
        # TODO: Change the following to iterate over existing presets
        custom_framerate = (fps_rate not in {23.98, 24, 25, 29.97, 30, 50, 59.94, 60})
        
        if custom_framerate is True:
            fps_label_text = "Custom (%r fps)" % fps_rate
            show_framerate = True
        else:
            fps_label_text = "%r fps" % fps_rate
            show_framerate = (preset_label == "Custom")
        
        CameraSensorPanel._frame_rate_args_prev = args
        CameraSensorPanel._frame_rate_ret = args = (fps_label_text, show_framerate)
        return args
    
    @staticmethod
    def draw_framerate(sub, rd):
        if CameraSensorPanel._preset_class is None:
            CameraSensorPanel._preset_class = bpy.types.RENDER_MT_framerate_presets
        
        args = rd.fps, rd.fps_base, CameraSensorPanel._preset_class.bl_label
        fps_label_text, show_framerate = CameraSensorPanel._draw_framerate_label(*args)
        
        sub.menu("RENDER_MT_framerate_presets", text=fps_label_text)
        
        if show_framerate:
            sub.prop(rd, "fps")
            sub.prop(rd, "fps_base", text="/")
    
    @staticmethod
    def draw_blender_part(context, layout):
        scene = context.scene
        rd = scene.render
        
        split = layout.split()
        
        col = split.column()
        sub = col.column(align=True)
        sub.label(text="Resolution:")
        sub.prop(rd, "resolution_x", text="X")
        sub.prop(rd, "resolution_y", text="Y")
        sub.prop(rd, "resolution_percentage", text="")
        
        sub.label(text="Aspect Ratio:")
        sub.prop(rd, "pixel_aspect_x", text="X")
        sub.prop(rd, "pixel_aspect_y", text="Y")
        
        # row = col.row()
        # row.prop(rd, "use_border", text="Border")
        # sub = row.row()
        # sub.active = rd.use_border
        # sub.prop(rd, "use_crop_to_border", text="Crop")
        
        col = split.column()
        sub = col.column(align=True)
        sub.label(text="Frame Range:")
        sub.prop(scene, "frame_start")
        sub.prop(scene, "frame_end")
        sub.prop(scene, "frame_step")
        
        sub.label(text="Frame Rate:")
        
        CameraSensorPanel.draw_framerate(sub, rd)
        
        # subrow = sub.row(align=True)
        # subrow.label(text="Time Remapping:")
        # subrow = sub.row(align=True)
        # subrow.prop(rd, "frame_map_old", text="Old")
        # subrow.prop(rd, "frame_map_new", text="New")
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.camera.maxwell_render
        o = context.camera
        rp = context.scene.render
        
        self.draw_blender_part(context, sub)
        
        # r = sub.row(align=True)
        # r.label("Resolution:")
        # r.prop(rp, 'resolution_x', text="", )
        # r.prop(rp, 'resolution_y', text="", )
        # sub.prop(rp, 'resolution_percentage')
        
        r = sub.row(align=True)
        r.label("Filmback (mm):")
        r.prop(o, 'sensor_width', text="", )
        r.prop(o, 'sensor_height', text="", )
        sub.prop(o, 'sensor_fit')
        
        # c = sub.column(align=True)
        # c.prop(rp, 'pixel_aspect_x')
        # c.prop(rp, 'pixel_aspect_y')
        
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
        
        def base(ob):
            group = []
            for o in bpy.data.objects:
                if(o.data is not None):
                    if(o.data.users > 1 and o.data == ob.data):
                        group.append(o)
            nms = [o.name for o in group]
            ls = sorted(nms)
            if(len(ls) > 0):
                return ls[0]
        
        b = base(context.object)
        r = sub.row()
        r.prop(m, 'override_instance', text="Override Instancing{}".format(" of '{}'".format(b) if b is not None else ""), )
        if(b is None):
            r.active = False
        
        sub.prop(m, 'hide')
        sub.separator()
        
        sub.prop(m, 'opacity')
        sub.separator()
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


class ObjectReferencePanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell MXS Reference Object"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['EMPTY']
        vol = context.object.maxwell_volumetrics_extension.enabled
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES) and not vol
    
    def draw_header(self, context):
        m = context.object.maxwell_render_reference
        self.layout.prop(m, 'enabled', text="")
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.maxwell_render_reference
        
        sub.prop(m, 'path')
        
        q = 0.33
        
        r = sub.row()
        s = r.split(percentage=q)
        c = s.column()
        c.label(text='Override Flags:')
        c = s.column()
        c.prop(m, 'flag_override_hide')
        
        r = sub.row()
        s = r.split(percentage=q)
        c = s.column()
        c.label(text='Hidden From:')
        c = s.column()
        c.prop(m, 'flag_override_hide_to_camera')
        
        r = sub.row()
        s = r.split(percentage=q)
        c = s.column()
        c = s.column()
        c.prop(m, 'flag_override_hide_to_refl_refr')
        
        r = sub.row()
        s = r.split(percentage=q)
        c = s.column()
        c = s.column()
        c.prop(m, 'flag_override_hide_to_gi')


class ExtObjectVolumetricsPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Volumetrics"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['EMPTY']
        ref = context.object.maxwell_render_reference.enabled
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES) and not ref
    
    def draw_header(self, context):
        m = context.object.maxwell_volumetrics_extension
        self.layout.prop(m, 'enabled', text="")
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.maxwell_volumetrics_extension
        
        r = sub.row()
        r.prop(m, 'vtype', expand=True)
        
        sub.separator()
        
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
        
        sub.prop(m, 'density')
        if(m.vtype == 'NOISE3D_2'):
            sub.prop(m, 'noise_seed')
            sub.prop(m, 'noise_low')
            sub.prop(m, 'noise_high')
            sub.prop(m, 'noise_detail')
            sub.prop(m, 'noise_octaves')
            sub.prop(m, 'noise_persistence')


class ExtObjectSubdivisionPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Subdivision Modifier"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw_header(self, context):
        m = context.object.maxwell_subdivision_extension
        self.layout.prop(m, "enabled", text="")
    
    def draw(self, context):
        l = self.layout
        m = context.object.maxwell_subdivision_extension
        sub = l.column()
        if(not m.enabled):
            sub.active = False
        sub.prop(m, 'level')
        r = sub.row()
        r.prop(m, 'scheme', expand=True)
        sub.prop(m, 'interpolation')
        sub.prop(m, 'crease')
        sub.prop(m, 'smooth')


class ExtObjectScatterPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Scatter Modifier"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw_header(self, context):
        m = context.object.maxwell_scatter_extension
        self.layout.prop(m, "enabled", text="")
    
    def draw(self, context):
        l = self.layout
        m = context.object.maxwell_scatter_extension
        sub = l.column()
        if(not m.enabled):
            sub.active = False
        
        c = sub.column()
        c.label("Primitive:")
        c.prop_search(m, "scatter_object", context.scene, "objects")
        c.prop(m, 'inherit_objectid')
        c.separator()
        
        c = sub.column()
        c.label("Scatter Density:")
        c.prop(m, 'density')
        c = sub.column()
        c.prop_search(m, 'density_map', bpy.data, 'textures', icon='TEXTURE')
        c = sub.column()
        c.prop(m, 'seed')
        
        c = sub.column(align=True)
        c.label("Scale:")
        c.prop(m, 'scale_x')
        c.prop(m, 'scale_y')
        c.prop(m, 'scale_z')
        c.separator()
        c.prop_search(m, 'scale_map', bpy.data, 'textures', icon='TEXTURE')
        c.label("Scale Variation:")
        c.prop(m, 'scale_variation_x')
        c.prop(m, 'scale_variation_y')
        c.prop(m, 'scale_variation_z')
        
        c = sub.column(align=True)
        c.label("Rotation:")
        c.prop(m, 'rotation_x')
        c.prop(m, 'rotation_y')
        c.prop(m, 'rotation_z')
        c.separator()
        c.prop_search(m, 'rotation_map', bpy.data, 'textures', icon='TEXTURE')
        c.label("Rotation Variation:")
        c.prop(m, 'rotation_variation_x')
        c.prop(m, 'rotation_variation_y')
        c.prop(m, 'rotation_variation_z')
        
        sub.separator()
        c = sub.column()
        c.prop(m, 'lod')
        r = c.row(align=True)
        r.prop(m, 'lod_min_distance')
        r.prop(m, 'lod_max_distance')
        if(not m.lod):
            r.enabled = False
        r = c.row()
        r.prop(m, 'lod_max_distance_density')
        if(not m.lod):
            r.enabled = False
        
        sub.separator()
        c = sub.column()
        c.label("Display:")
        sc = c.column(align=True)
        sc.prop(m, 'display_percent')
        sc.prop(m, 'display_max_blades')


class ExtObjectSeaPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Sea"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # e = context.scene.render.engine
        # o = context.active_object
        # ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        # return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
        return False
    
    def draw_header(self, context):
        m = context.object.maxwell_sea_extension
        self.layout.prop(m, "enabled", text="")
    
    def draw(self, context):
        l = self.layout
        m = context.object.maxwell_sea_extension
        sub = l.column()
        if(not m.enabled):
            sub.active = False
        
        sub.prop(m, 'hide_parent')
        
        c = sub.column()
        c.label("Geometry:")
        c.prop(m, 'reference_time')
        c.prop(m, 'resolution')
        c.prop(m, 'ocean_depth')
        c.prop(m, 'vertical_scale')
        c.prop(m, 'ocean_dim')
        c.prop(m, 'ocean_seed')
        c.prop(m, 'enable_choppyness')
        c.prop(m, 'choppy_factor')
        c.separator()
        
        c = sub.column()
        c.label("Wind:")
        c.prop(m, 'ocean_wind_mod')
        c.prop(m, 'ocean_wind_dir')
        c.prop(m, 'ocean_wind_alignment')
        c.prop(m, 'ocean_min_wave_length')
        c.prop(m, 'damp_factor_against_wind')
        c.separator()


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


class MaterialPreviewPanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Preview"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        mat = context.material
        m = mat.maxwell_render
        
        l.template_preview(mat, show_buttons=False, )
        l.prop(m, 'flag', toggle=True, text="Refresh Preview", )
        # l.prop(bpy.context.scene.maxwell_render_private, 'material')


class MaterialPanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Material"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        
        sub.prop(m, 'use', text="Material Type", )
        sub.separator()
        
        if(m.use == 'EMITTER'):
            sub.prop(mx, 'emitter_type')
            sub.separator()
            if(mx.emitter_type == '0'):
                # Area
                pass
            elif(mx.emitter_type == '1'):
                # IES
                sub.prop(mx, 'emitter_ies_data')
                sub.separator()
                sub.prop(mx, 'emitter_ies_intensity')
                sub.separator()
            elif(mx.emitter_type == '2'):
                # Spot
                r = sub.row()
                s = r.split(percentage=0.2)
                c = s.column()
                c.label("Spot Map:")
                c = s.column()
                r = c.row()
                r.prop(mx, 'emitter_spot_map_enabled', text="", )
                r.prop_search(mx, 'emitter_spot_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                
                sub.prop(mx, 'emitter_spot_cone_angle')
                sub.prop(mx, 'emitter_spot_falloff_angle')
                sub.prop(mx, 'emitter_spot_falloff_type')
                sub.prop(mx, 'emitter_spot_blur')
                sub.separator()
            
            if(mx.emitter_type == '1'):
                # IES
                r = sub.row()
                s = r.split(percentage=0.2)
                c = s.column()
                c.label("Color:")
                c = s.column()
                r = c.row()
                r.prop(mx, 'emitter_color', text="", )
                r.prop(mx, 'emitter_color_black_body_enabled', text="", )
                r.prop(mx, 'emitter_color_black_body')
            elif(mx.emitter_type == '2'):
                # Spot
                r = sub.row()
                s = r.split(percentage=0.2)
                c = s.column()
                c.label("Color:")
                c = s.column()
                r = c.row()
                r.prop(mx, 'emitter_color', text="", )
                r.prop(mx, 'emitter_color_black_body_enabled', text="", )
                r.prop(mx, 'emitter_color_black_body')
                sub.separator()
                sub.prop(mx, 'emitter_luminance')
                if(mx.emitter_luminance == '0'):
                    # Power & Efficacy
                    sub.prop(mx, 'emitter_luminance_power')
                    sub.prop(mx, 'emitter_luminance_efficacy')
                    # r = sub.row()
                    # r.prop(mx, 'emitter_luminance_output', text="Output (lm)")
                    # r.enabled = False
                elif(mx.emitter_luminance == '1'):
                    # Lumen
                    sub.prop(mx, 'emitter_luminance_output', text="Output (lm)")
                elif(mx.emitter_luminance == '2'):
                    # Lux
                    sub.prop(mx, 'emitter_luminance_output', text="Output (lm/m)")
                elif(mx.emitter_luminance == '3'):
                    # Candela
                    sub.prop(mx, 'emitter_luminance_output', text="Output (cd)")
                elif(mx.emitter_luminance == '4'):
                    # Luminance
                    sub.prop(mx, 'emitter_luminance_output', text="Output (cd/m)")
            else:
                sub.prop(mx, 'emitter_emission')
                sub.separator()
                
                if(mx.emitter_emission == '0'):
                    sub.menu("Emitter_presets", text=bpy.types.Emitter_presets.bl_label)
                    sub.separator()
                    # Color
                    r = sub.row()
                    s = r.split(percentage=0.2)
                    c = s.column()
                    c.label("Color:")
                    c = s.column()
                    r = c.row()
                    r.prop(mx, 'emitter_color', text="", )
                    r.prop(mx, 'emitter_color_black_body_enabled', text="", )
                    r.prop(mx, 'emitter_color_black_body')
                    sub.separator()
                    sub.prop(mx, 'emitter_luminance')
                    if(mx.emitter_luminance == '0'):
                        # Power & Efficacy
                        c = sub.column(align=True)
                        c.prop(mx, 'emitter_luminance_power')
                        c.prop(mx, 'emitter_luminance_efficacy')
                        sub.label("Output: {} lm".format(round(mx.emitter_luminance_power * mx.emitter_luminance_efficacy, 1)))
                    elif(mx.emitter_luminance == '1'):
                        # Lumen
                        sub.prop(mx, 'emitter_luminance_output', text="Output (lm)")
                    elif(mx.emitter_luminance == '2'):
                        # Lux
                        sub.prop(mx, 'emitter_luminance_output', text="Output (lm/m)")
                    elif(mx.emitter_luminance == '3'):
                        # Candela
                        sub.prop(mx, 'emitter_luminance_output', text="Output (cd)")
                    elif(mx.emitter_luminance == '4'):
                        # Luminance
                        sub.prop(mx, 'emitter_luminance_output', text="Output (cd/m)")
                elif(mx.emitter_emission == '1'):
                    # Temperature
                    sub.prop(mx, 'emitter_temperature_value')
                elif(mx.emitter_emission == '2'):
                    # HDR Image
                    sub.prop_search(mx, 'emitter_hdr_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                    sub.separator()
                    sub.prop(mx, 'emitter_hdr_intensity')
            
        elif(m.use == 'AGS'):
            r = sub.row()
            s = r.split(percentage=0.33)
            c = s.column()
            c.label("Color:")
            c = s.column()
            c.prop(mx, 'ags_color', text="", )
            
            sub.prop(mx, 'ags_reflection')
            sub.prop(mx, 'ags_type')
            
        elif(m.use == 'OPAQUE'):
            sub.menu("Opaque_presets", text=bpy.types.Opaque_presets.bl_label)
            sub.separator()
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'opaque_color', text="", )
            r.prop(mx, 'opaque_color_type', text="", )
            r.prop_search(mx, 'opaque_color_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Shininess:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'opaque_shininess', text="", )
            r.prop(mx, 'opaque_shininess_type', text="", )
            r.prop_search(mx, 'opaque_shininess_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Roughness:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'opaque_roughness', text="", )
            r.prop(mx, 'opaque_roughness_type', text="", )
            r.prop_search(mx, 'opaque_roughness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            sub.prop(mx, 'opaque_clearcoat')
            
        elif(m.use == 'TRANSPARENT'):
            sub.menu("Transparent_presets", text=bpy.types.Transparent_presets.bl_label)
            sub.separator()
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'transparent_color', text="", )
            r.prop(mx, 'transparent_color_type', text="", )
            r.prop_search(mx, 'transparent_color_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            sub.prop(mx, 'transparent_ior')
            sub.prop(mx, 'transparent_transparency')
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Roughness:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'transparent_roughness', text="", )
            r.prop(mx, 'transparent_roughness_type', text="", )
            r.prop_search(mx, 'transparent_roughness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            sub.prop(mx, 'transparent_specular_tint')
            sub.prop(mx, 'transparent_dispersion')
            sub.prop(mx, 'transparent_clearcoat')
            
        elif(m.use == 'METAL'):
            sub.menu("Metal_presets", text=bpy.types.Metal_presets.bl_label)
            sub.separator()
            
            sub.prop(mx, 'metal_ior')
            sub.prop(mx, 'metal_tint')
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'metal_color', text="", )
            r.prop(mx, 'metal_color_type', text="", )
            r.prop_search(mx, 'metal_color_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Roughness:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'metal_roughness', text="", )
            r.prop(mx, 'metal_roughness_type', text="", )
            r.prop_search(mx, 'metal_roughness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Anisotropy:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'metal_anisotropy', text="", )
            r.prop(mx, 'metal_anisotropy_type', text="", )
            r.prop_search(mx, 'metal_anisotropy_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Angle:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'metal_angle', text="", )
            r.prop(mx, 'metal_angle_type', text="", )
            r.prop_search(mx, 'metal_angle_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Dust & Dirt:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'metal_dust', text="", )
            r.prop(mx, 'metal_dust_type', text="", )
            r.prop_search(mx, 'metal_dust_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Perforation:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'metal_perforation_enabled', text="", )
            r.prop_search(mx, 'metal_perforation_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
        elif(m.use == 'TRANSLUCENT'):
            sub.menu("Translucent_presets", text=bpy.types.Translucent_presets.bl_label)
            sub.separator()
            
            sub.prop(mx, 'translucent_scale')
            sub.prop(mx, 'translucent_ior')
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'translucent_color', text="", )
            r.prop(mx, 'translucent_color_type', text="", )
            r.prop_search(mx, 'translucent_color_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            sub.prop(mx, 'translucent_hue_shift')
            sub.prop(mx, 'translucent_invert_hue')
            sub.prop(mx, 'translucent_vibrance')
            sub.prop(mx, 'translucent_density')
            sub.prop(mx, 'translucent_opacity')
            
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Roughness:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'translucent_roughness', text="", )
            r.prop(mx, 'translucent_roughness_type', text="", )
            r.prop_search(mx, 'translucent_roughness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            sub.prop(mx, 'translucent_specular_tint')
            sub.prop(mx, 'translucent_clearcoat')
            sub.prop(mx, 'translucent_clearcoat_ior')
            
        elif(m.use == 'CARPAINT'):
            sub.menu("Carpaint_presets", text=bpy.types.Carpaint_presets.bl_label)
            sub.separator()
            
            r = sub.row()
            s = r.split(percentage=0.33)
            c = s.column()
            c.label("Color:")
            c = s.column()
            c.prop(mx, 'carpaint_color', text="", )
            
            sub.prop(mx, 'carpaint_metallic')
            sub.prop(mx, 'carpaint_topcoat')
            
        # elif(m.use == 'HAIR'):
        #     sub.menu("Hair_presets", text=bpy.types.Hair_presets.bl_label)
        #     sub.separator()
        #
        #     r = sub.row()
        #     s = r.split(percentage=0.2)
        #     c = s.column()
        #     c.label("Color:")
        #     c = s.column()
        #     r = c.row()
        #     r.prop(mx, 'hair_color', text="", )
        #     r.prop(mx, 'hair_color_type', text="", )
        #     r.prop_search(mx, 'hair_color_map', mat, 'texture_slots', icon='TEXTURE', text="", )
        #
        #     sub.prop_search(mx, 'hair_root_tip_map', mat, 'texture_slots', icon='TEXTURE', )
        #
        #     r = sub.row()
        #     s = r.split(percentage=0.2)
        #     c = s.column()
        #     c.label("Root-Tip Weight:")
        #     c = s.column()
        #     r = c.row()
        #     r.prop(mx, 'hair_root_tip_weight', text="", )
        #     r.prop(mx, 'hair_root_tip_weight_type', text="", )
        #     r.prop_search(mx, 'hair_root_tip_weight_map', mat, 'texture_slots', icon='TEXTURE', text="", )
        #
        #     sub.label('Primary Highlight:')
        #     r = sub.row(align=True)
        #     r.prop(mx, 'hair_primary_highlight_strength')
        #     r.prop(mx, 'hair_primary_highlight_spread')
        #     r = sub.row()
        #     r.prop(mx, 'hair_primary_highlight_tint')
        #
        #     sub.label('Secondary Highlight:')
        #     r = sub.row(align=True)
        #     r.prop(mx, 'hair_secondary_highlight_strength')
        #     r.prop(mx, 'hair_secondary_highlight_spread')
        #     r = sub.row()
        #     r.prop(mx, 'hair_secondary_highlight_tint')
        #
        else:
            # 'CUSTOM'
            sub.prop(m, 'mxm_file')
            sub.prop(m, 'embed')
            r = sub.row()
            r.prop(context.material, 'diffuse_color', text="Blender Viewport Color", )
            r = sub.row(align=True)
            if(m.mxm_file == ''):
                r.operator('maxwell_render.create_material').backface = False
            else:
                r.operator('maxwell_render.edit_material').backface = False


class MaterialBackfacePanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Backface Material"
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
        if(not super().poll(context)):
            return False
        if(context.space_data.texture_context not in ['MATERIAL', 'PARTICLES']):
            return False
        return True
    
    def draw(self, context):
        l = self.layout
        m = context.texture.maxwell_render
        
        tex = None
        ts = context.texture_slot
        if(ts.texture is not None):
            if(ts.texture.type == 'IMAGE'):
                tex = ts.texture
        if(tex is None):
            l.active = False
        
        c = l.column()
        if(tex is not None and tex.image):
            image = tex.image
            c.active = False
            c.enabled = False
            c.prop(image, 'filepath', text="Path:")
            c.prop(tex, 'image')
        else:
            c.label("Load an image", icon='ERROR', )
        
        l.label("Projection Properties:")
        l.prop(m, 'use_global_map')
        
        sub = l.column()
        sub.active = not m.use_global_map
        
        tex = context.texture
        ob = context.object
        
        r = sub.row()
        s = r.split(percentage=0.25)
        s.label(text="Channel:")
        if(len(ob.data.uv_textures) == 0):
            s.label("No UV Maps", icon='ERROR', )
        else:
            s.prop_search(ts, "uv_layer", ob.data, "uv_textures", text="")
        sub.separator()
        
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
        
        r = sub.row()
        r.prop(m, 'offset')
        
        sub.prop(m, 'rotation')
        
        # l.separator()
        l.label("Image Properties:")
        
        sub = l.column()
        r = sub.row()
        r.prop(m, 'invert')
        r.prop(m, 'use_alpha')
        r.prop(m, 'interpolation')
        
        sub = l.column()
        sub.label("Nothing to see here, move along..", icon='ERROR', )
        sub.prop(m, 'brightness')
        sub.prop(m, 'contrast')
        sub.prop(m, 'saturation')
        sub.prop(m, 'hue')
        
        r = sub.row()
        r.prop(m, 'clamp')
        
        sub.enabled = False


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
        # sub.label("Particle system will be skipped.", icon='ERROR', )


class ExtGrassPanel(ParticleButtonsPanel, Panel):
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
        sub.separator()
        
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
        r = sub.row(align=True)
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
        c = sub.column(align=True)
        c.prop(m, 'display_percent')
        c.prop(m, 'display_max_blades')


class ExtParticlesObjectPanel(ParticleButtonsPanel, Panel):
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
        sub.separator()
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


class ExtHairPanel(ParticleButtonsPanel, Panel):
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
        
        r = sub.row()
        if(len(o.data.uv_textures) == 0):
            r.label("No UV Maps", icon='ERROR', )
        else:
            r.prop_search(m, "uv_layer", o.data, "uv_textures", )
        r.enabled = False
        sub.label("UVs needs to be fixed..", icon='ERROR', )
        
        sub.separator()
        # sub.prop(m, 'display_percent')
        # if(m.hair_type == 'GRASS'):
        #     sub.prop(m, 'display_max_blades')
        # else:
        #     sub.prop(m, 'display_max_hairs')
        
        # sub.label("Display:")
        c = sub.column(align=True)
        c.prop(m, 'display_percent')
        if(m.hair_type == 'GRASS'):
            c.prop(m, 'display_max_blades')
        else:
            c.prop(m, 'display_max_hairs')


class ExtParticlesPanel(ParticleButtonsPanel, Panel):
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
        
        r = sub.row()
        r.prop(m, 'source', expand=True)
        if(m.source == 'EXTERNAL_BIN'):
            sub.prop(m, 'bin_filename')
            
            # r = sub.row()
            # r.prop(m, 'bin_type', expand=True, )
            sub.prop(m, 'bin_type')
            if(m.bin_type == 'SEQUENCE'):
                sub.prop(m, 'seq_limit')
                r = sub.row(align=True)
                if(not m.seq_limit):
                    r.active = False
                r.prop(m, 'seq_start')
                r.prop(m, 'seq_end')
        else:
            sub.prop(m, 'bl_use_velocity')
            r = sub.row()
            r.prop(m, 'bl_size')
            if(m.bl_use_size):
                r.active = False
            sub.prop(m, 'bl_use_size')
            sub.prop(m, 'bin_directory')
            sub.prop(m, 'bin_overwrite')
        
        sub.separator()
        # sub.label("Sequence:")
        
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


class ExtClonerPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Cloner"
    
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
        if(m.use != 'CLONER'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_cloner_extension
        
        ps = p.settings
        r = sub.row()
        r.prop(ps, "dupli_object")
        r = sub.row()
        r.prop(ps, "use_render_emitter", text="Render Emitter", )
        sub.separator()
        
        sub = l.column()
        if(ps.dupli_object is None):
            sub.active = False
        
        r = sub.row()
        r.prop(m, 'source', expand=True)
        if(m.source == 'EXTERNAL_BIN'):
            sub.prop(m, 'filename')
        else:
            sub.prop(m, 'bl_use_velocity')
            r = sub.row()
            r.prop(m, 'bl_size')
            if(m.bl_use_size):
                r.active = False
            sub.prop(m, 'bl_use_size')
            sub.prop(m, 'directory')
            sub.prop(m, 'overwrite')
        sub.separator()
        
        c = sub.column()
        c.label("Particles:")
        c.prop(m, 'radius')
        c.prop(m, 'mb_factor')
        r = c.row()
        r.prop(m, 'load_percent')
        r.prop(m, 'start_offset')
        c.separator()
        
        c = sub.column()
        c.label("Multipoint:")
        c.prop(m, 'extra_npp')
        c.prop(m, 'extra_p_dispersion')
        c.prop(m, 'extra_p_deformation')
        c.separator()
        
        c = sub.column()
        c.label("Instance control:")
        c.prop(m, 'align_to_velocity')
        c.prop(m, 'scale_with_radius')
        c.prop(m, 'inherit_obj_id')
        c.separator()
        
        sub.label("Display:")
        c = sub.column(align=True)
        c.prop(m, 'display_percent')
        c.prop(m, 'display_max')


class Render_presets(Menu):
    '''Presets for render options.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Render Presets"
    bl_idname = "Render_presets"
    preset_subdir = "maxwell_render/render"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Channels_presets(Menu):
    '''Presets for channels settings.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Channels Presets"
    bl_idname = "Channels_presets"
    preset_subdir = "maxwell_render/channels"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Environment_presets(Menu):
    '''Presets for environment settings.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Environment Presets"
    bl_idname = "Environment_presets"
    preset_subdir = "maxwell_render/environment"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Camera_presets(Menu):
    '''Presets for camera settings.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Camera Presets"
    bl_idname = "Camera_presets"
    preset_subdir = "maxwell_render/camera"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Opaque_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Opaque Presets"
    bl_idname = "Opaque_presets"
    preset_subdir = "maxwell_render/material/opaque"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Transparent_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Transparent Presets"
    bl_idname = "Transparent_presets"
    preset_subdir = "maxwell_render/material/transparent"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Metal_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Metal Presets"
    bl_idname = "Metal_presets"
    preset_subdir = "maxwell_render/material/metal"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Translucent_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Translucent Presets"
    bl_idname = "Translucent_presets"
    preset_subdir = "maxwell_render/material/translucent"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Carpaint_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Car Paint Presets"
    bl_idname = "Carpaint_presets"
    preset_subdir = "maxwell_render/material/carpaint"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Hair_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Hair Presets"
    bl_idname = "Hair_presets"
    preset_subdir = "maxwell_render/material/hair"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Emitter_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Emitter Presets"
    bl_idname = "Emitter_presets"
    preset_subdir = "maxwell_render/material/emitter"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset
