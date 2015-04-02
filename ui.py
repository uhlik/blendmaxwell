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
        
        r = l.row(align=True)
        r.operator("maxwell_render.render_export")
        r.operator("maxwell_render.animation_export")
        
        l.label("Scene Export Directory:")
        l.prop(m, 'export_output_directory', text="")


class ExportOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export Options"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.label("Workflow:")
        l.prop(m, 'export_open_with')
        l.prop(m, 'instance_app')
        
        l.separator()
        r = l.row()
        r.prop(m, 'export_overwrite')
        if(m.export_incremental):
            r.enabled = False
        l.prop(m, 'export_incremental')
        
        l.label("Options:")
        l.prop(m, 'export_use_instances')
        l.prop(m, 'export_keep_intermediates')


class ExportSpecialsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export Specials"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        ll = self.layout
        
        b = l.box()
        l = b
        
        l.prop(m, 'export_wireframe')
        if(m.export_wireframe):
            
            c = l.column()
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


class ExportLogPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export Log"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        r = l.row()
        r.prop(m, 'export_log_display', )
        r.prop(m, 'export_log_open', )
        
        if(m.export_log_display):
            ls = m.export_log.split('\n')
            for i, s in enumerate(ls):
                l.label(s.rstrip('\n'))


class SceneOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Scene"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, 'scene_time')
        l.prop(m, 'scene_sampling_level')
        r = l.row()
        r.prop(m, 'scene_multilight')
        r.prop(m, 'scene_multilight_type', text="", )
        r = l.row()
        r.prop(m, 'scene_cpu_threads')
        # r.prop(m, 'scene_priority')
        l.prop(m, 'scene_quality')
        # l.prop(m, 'scene_command_line')


class OutputOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Output"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, 'output_depth')
        
        s = l.split(percentage=0.25)
        c = s.column()
        c.prop(m, 'output_image_enabled')
        c = s.column()
        c.prop(m, 'output_image', text="", )
        if(not m.output_image_enabled):
            c.enabled = False
        
        s = l.split(percentage=0.25)
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
        m = context.scene.maxwell_render
        
        s = l.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'materials_override')
        c = s.column()
        c.prop(m, 'materials_override_path', text="", )
        if(not m.materials_override):
            c.enabled = False
        
        l.prop(m, 'materials_search_path')
        l.separator()
        l.prop(m, 'materials_directory')


class GlobalsOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Globals"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, 'globals_motion_blur')
        l.prop(m, 'globals_diplacement')
        l.prop(m, 'globals_dispersion')


class ToneMappingOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Tone Mapping"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, 'tone_color_space')
        l.prop(m, 'tone_whitepoint')
        l.prop(m, 'tone_tint')
        r = l.row()
        r.prop(m, 'tone_burn')
        r.prop(m, 'tone_gamma')
        r = l.row()
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
        m = context.scene.maxwell_render
        
        l.prop(m, 'simulens_aperture_map')
        l.prop(m, 'simulens_obstacle_map')
        r = l.row()
        r.prop(m, 'simulens_diffraction')
        r.prop(m, 'simulens_diffraction_value', text="", )
        r = l.row()
        s = r.split(percentage=0.5)
        c = s.column()
        s2 = c.split(percentage=0.075)
        c2 = s2.column()
        c2 = s2.column()
        c2.label('Frequency')
        c = s.column()
        c.prop(m, 'simulens_frequency', text="", )
        r = l.row()
        r.prop(m, 'simulens_scattering')
        r.prop(m, 'simulens_scattering_value', text="", )
        r = l.row()
        r.prop(m, 'simulens_devignetting')
        r.prop(m, 'simulens_devignetting_value', text="", )


class IllumCausticsOptionsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Illumination & Caustics"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, 'illum_caustics_illumination')
        l.prop(m, 'illum_caustics_refl_caustics')
        l.prop(m, 'illum_caustics_refr_caustics')


class RenderLayersPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Layer"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, "render_use_layers")
        
        scene = context.scene
        rd = scene.render
        rl = rd.layers.active
        
        s = l.split()
        c = s.column()
        c.prop(scene, "layers", text="Viewport Layers")
        # if(m.render_use_layers == 'RENDER'):
        #     c.enabled = False
        c = s.column()
        c.prop(rl, "layers", text="Render Layers")
        # if(m.render_use_layers == 'VIEWPORT'):
        #     c.enabled = False


class ChannelsOptionsPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Channels"
    
    def draw(self, context):
        l = self.layout
        m = context.scene.maxwell_render
        
        l.prop(m, 'channels_output_mode')
        
        r = l.row()
        c = r.column()
        c.prop(m, 'channels_render')
        c = r.column()
        c.prop(m, 'channels_render_type', text="", )
        if(not m.channels_render):
            c.enabled = False
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_alpha')
        c = s.column()
        c.prop(m, 'channels_alpha_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_alpha_opaque')
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_z_buffer')
        c = s.column()
        c.prop(m, 'channels_z_buffer_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_z_buffer_near', text="Near (m)")
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_z_buffer_far', text="Far (m)")
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_shadow')
        c = s.column()
        c.prop(m, 'channels_shadow_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_material_id')
        c = s.column()
        c.prop(m, 'channels_material_id_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_object_id')
        c = s.column()
        c.prop(m, 'channels_object_id_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_motion_vector')
        c = s.column()
        c.prop(m, 'channels_motion_vector_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_roughness')
        c = s.column()
        c.prop(m, 'channels_roughness_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_fresnel')
        c = s.column()
        c.prop(m, 'channels_fresnel_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_normals')
        c = s.column()
        c.prop(m, 'channels_normals_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_normals_space', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_position')
        c = s.column()
        c.prop(m, 'channels_position_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_position_space', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_deep')
        c = s.column()
        c.prop(m, 'channels_deep_file', text="", )
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_deep_type')
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_deep_min_dist')
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c = s.column()
        c.prop(m, 'channels_deep_max_samples')
        
        r = l.row()
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
        
        l.label("Custom Alphas are defined by Object groups.")
        
        for g in bpy.data.groups:
            m = g.maxwell_render
            
            b = l.box()
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
        m = context.world.maxwell_render
        
        l.prop(m, 'env_type', text="", )


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
        m = context.world.maxwell_render
        
        l.prop(m, 'sky_type')
        if(m.sky_type == 'CONSTANT'):
            l.prop(m, 'dome_intensity')
            l.prop(m, 'dome_zenith')
            l.prop(m, 'dome_horizon')
            l.prop(m, 'dome_mid_point')
        else:
            l.prop(m, 'sky_use_preset')
            if(m.sky_use_preset):
                l.prop(m, 'sky_preset')
            else:
                l.prop(m, 'sky_intensity')
                l.prop(m, 'sky_planet_refl')
                l.prop(m, 'sky_ozone')
                l.prop(m, 'sky_water')
                l.prop(m, 'sky_turbidity_coeff')
                l.prop(m, 'sky_wavelength_exp')
                l.prop(m, 'sky_reflectance')
                l.prop(m, 'sky_asymmetry')


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
        m = context.world.maxwell_render
        
        l.prop(m, 'sun_lamp_priority')
        l.separator()
        
        l.prop(m, 'sun_type')
        if(m.sun_type != 'DISABLED'):
            l.prop(m, 'sun_power')
            l.prop(m, 'sun_radius_factor')
            r = l.row()
            r.prop(m, 'sun_temp')
            if(m.sun_type == 'CUSTOM'):
                r.enabled = False
            r = l.row()
            r.prop(m, 'sun_color')
            if(m.sun_type == 'PHYSICAL'):
                r.enabled = False
            l.separator()
            
            l.prop(m, 'sun_location_type')
            if(m.sun_location_type == 'ANGLES'):
                l.prop(m, 'sun_angles_zenith')
                l.prop(m, 'sun_angles_azimuth')
            elif(m.sun_location_type == 'DIRECTION'):
                l.operator('maxwell_render.set_sun', "Set Sun")
                c = l.column(align=True)
                c.prop(m, 'sun_dir_x')
                c.prop(m, 'sun_dir_y')
                c.prop(m, 'sun_dir_z')
            else:
                r = l.row(align=True)
                r.prop(m, 'sun_latlong_lat')
                r.prop(m, 'sun_latlong_lon')
                l.prop(m, 'sun_date')
                l.prop(m, 'sun_time')
                
                r = l.row()
                c = r.column()
                c.prop(m, 'sun_latlong_gmt')
                r.prop(m, 'sun_latlong_gmt_auto')
                if(m.sun_latlong_gmt_auto):
                    c.enabled = False
                
                l.operator('maxwell_render.now', "Now")
                
                l.prop(m, 'sun_latlong_ground_rotation')


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
        m = context.world.maxwell_render
        
        l.prop(m, 'ibl_intensity')
        r = l.row()
        r.prop(m, 'ibl_interpolation')
        r.prop(m, 'ibl_screen_mapping')
        
        b = l.box()
        b.label("Background:")
        b.prop(m, 'ibl_bg_type')
        b.prop(m, 'ibl_bg_map')
        b.prop(m, 'ibl_bg_intensity')
        r = b.row(align=True)
        r.prop(m, 'ibl_bg_scale_x')
        r.prop(m, 'ibl_bg_scale_y')
        r = b.row(align=True)
        r.prop(m, 'ibl_bg_offset_x')
        r.prop(m, 'ibl_bg_offset_y')
        
        b = l.box()
        b.label("Reflection:")
        b.prop(m, 'ibl_refl_type')
        if(m.ibl_refl_type == 'HDR_IMAGE'):
            b.prop(m, 'ibl_refl_map')
            b.prop(m, 'ibl_refl_intensity')
            r = b.row(align=True)
            r.prop(m, 'ibl_refl_scale_x')
            r.prop(m, 'ibl_refl_scale_y')
            r = b.row(align=True)
            r.prop(m, 'ibl_refl_offset_x')
            r.prop(m, 'ibl_refl_offset_y')
        
        b = l.box()
        b.label("Refraction:")
        b.prop(m, 'ibl_refr_type')
        if(m.ibl_refr_type == 'HDR_IMAGE'):
            b.prop(m, 'ibl_refr_map')
            b.prop(m, 'ibl_refr_intensity')
            r = b.row(align=True)
            r.prop(m, 'ibl_refr_scale_x')
            r.prop(m, 'ibl_refr_scale_y')
            r = b.row(align=True)
            r.prop(m, 'ibl_refr_offset_x')
            r.prop(m, 'ibl_refr_offset_y')
        
        b = l.box()
        b.label("Illumination:")
        b.prop(m, 'ibl_illum_type')
        if(m.ibl_illum_type == 'HDR_IMAGE'):
            b.prop(m, 'ibl_illum_map')
            b.prop(m, 'ibl_illum_intensity')
            r = b.row(align=True)
            r.prop(m, 'ibl_illum_scale_x')
            r.prop(m, 'ibl_illum_scale_y')
            r = b.row(align=True)
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
        m = context.object.data.maxwell_render
        
        l.prop(m, 'override')


class CameraOpticsPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Optics"
    
    def draw(self, context):
        l = self.layout
        m = context.camera.maxwell_render
        o = context.camera
        r = context.scene.render
        
        l.operator('maxwell_render.auto_focus', "Auto Focus")
        
        cam = context.camera
        l.prop(o, 'dof_object')
        
        r = l.row()
        r.enabled = cam.dof_object is None
        r.prop(o, 'dof_distance')
        
        l.prop(m, 'lens')
        r = l.row()
        r.prop(o, 'lens')
        if(m.lens == 'TYPE_ORTHO_2'):
            r.enabled = False
        l.prop(m, 'shutter')
        l.prop(m, 'fstop')
        if(m.lens == 'TYPE_FISHEYE_3'):
            l.prop(m, 'fov')
        if(m.lens == 'TYPE_SPHERICAL_4'):
            l.prop(m, 'azimuth')
        if(m.lens == 'TYPE_CYLINDRICAL_5'):
            l.prop(m, 'angle')


class CameraSensorPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Sensor"
    
    def draw(self, context):
        l = self.layout
        m = context.camera.maxwell_render
        o = context.camera
        rp = context.scene.render
        
        r = l.row(align=True)
        r.label("Resolution:")
        
        r.prop(rp, 'resolution_x', text="", )
        r.prop(rp, 'resolution_y', text="", )
        l.prop(rp, 'resolution_percentage')
        
        r = l.row(align=True)
        r.label("Filmback (mm):")
        r.prop(o, 'sensor_width', text="", )
        r.prop(o, 'sensor_height', text="", )
        l.prop(o, 'sensor_fit')
        
        c = l.column(align=True)
        c.prop(rp, 'pixel_aspect_x')
        c.prop(rp, 'pixel_aspect_y')
        
        l.prop(m, 'iso')
        l.prop(m, 'response')
        l.prop(m, 'screen_region')
        r = l.row()
        c = r.column(align=True)
        c.prop(m, 'screen_region_x')
        c.prop(m, 'screen_region_y')
        c.enabled = False
        c = r.column(align=True)
        c.prop(m, 'screen_region_w')
        c.prop(m, 'screen_region_h')
        c.enabled = False
        r = l.row(align=True)
        r.operator("maxwell_render.camera_set_region")
        r.operator("maxwell_render.camera_reset_region")


class CameraOptionsPanel(CameraButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Options"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        m = context.camera.maxwell_render
        o = context.camera
        r = context.scene.render
        
        l.label("Diaphragm:")
        l.prop(m, 'aperture')
        r = l.row()
        r.prop(m, 'diaphragm_blades')
        r.prop(m, 'diaphragm_angle')
        if(m.aperture == 'CIRCULAR'):
            r.enabled = False
        
        l.prop(m, 'custom_bokeh')
        r = l.row()
        r.prop(m, 'bokeh_ratio')
        r.prop(m, 'bokeh_angle')
        if(not m.custom_bokeh):
            r.enabled = False
        
        l.separator()
        l.label("Rotary Disc Shutter:")
        r = l.row()
        r.prop(m, 'shutter_angle')
        r.enabled = False
        l.prop(m, 'frame_rate')
        
        l.separator()
        l.label("Z-clip Planes:")
        l.prop(m, 'zclip')
        r = l.row(align=True)
        r.prop(o, 'clip_start')
        r.prop(o, 'clip_end')
        
        l.separator()
        l.label("Shift Lens:")
        r = l.row(align=True)
        r.prop(o, 'shift_x')
        r.prop(o, 'shift_y')
        
        l.prop(m, 'hide')


class ObjectPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Object"
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'LAMP', 'SPEAKER']
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        m = context.object.maxwell_render
        l.prop(m, 'hide')
        l.prop(m, 'opacity')
        l.prop(m, 'object_id')
        l.label("Hidden from:")
        s = l.split(percentage=0.5)
        c = s.column()
        c.prop(m, 'hidden_camera')
        c.prop(m, 'hidden_camera_in_shadow_channel')
        c.prop(m, 'hidden_global_illumination')
        c = s.column()
        c.prop(m, 'hidden_reflections_refractions')
        c.prop(m, 'hidden_zclip_planes')


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
        m = context.material.maxwell_render
        l.prop(m, 'mxm_file')
        l.prop(m, 'embed')
        
        r = l.row(align=True)
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
        m = context.object.maxwell_render
        l.prop(m, 'backface_material_file')
        l.prop(m, 'backface_material_embed')
        
        r = l.row(align=True)
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
        # l.prop(tex, 'image')
        
        # l.template_image(tex, "image", tex.image_user, )
        
        # l.separator()
        # l.label("Projection Properties:")
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
        s.prop_search(tex, "uv_layer", ob.data, "uv_textures", text="")
        
        r = sub.row()
        r.prop(m, 'tiling_method', expand=True, )
        r = sub.row()
        r.prop(m, 'tiling_units', expand=True, )
        r = sub.row()
        r.prop(m, 'repeat')
        
        r = sub.row()
        r.label("Mirror:")
        r.prop(m, 'mirror_x', text="X", )
        r.prop(m, 'mirror_y', text="Y", )
        
        r = sub.row()
        r.prop(m, 'offset')
        sub.prop(m, 'rotation')
        
        l.separator()
        # l.label("Image Properties:")
        
        sub = l.column()
        r = sub.row()
        r.prop(m, 'invert')
        r.prop(m, 'use_alpha')
        sub.prop(m, 'type_interpolation')
        r = sub.row()
        r.prop(m, 'brightness')
        r.prop(m, 'contrast')
        r = sub.row()
        r.prop(m, 'saturation')
        r.prop(m, 'hue')
        r = sub.row()
        r.prop(m, 'clamp')


class ParticlesPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Particles"
    
    def draw(self, context):
        l = self.layout
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_render
        
        l.prop(m, 'use', expand=True, )


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
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        ps = context.particle_system.settings
        m = context.particle_system.settings.maxwell_grass_extension
        
        l.label("Primitive:")
        s = l.split(percentage=0.8)
        c = s.column()
        c.prop(m, 'material')
        c = s.column()
        c.prop(m, 'material_embed', text='Embed', )
        
        s = l.split(percentage=0.8)
        c = s.column()
        c.prop(m, 'backface_material')
        c = s.column()
        c.prop(m, 'material_backface_embed', text='Embed', )
        
        l.prop(m, 'points_per_blade')
        r = l.row()
        r.label("Primitive Type:")
        r.prop(m, 'primitive_type', expand=True, )
        l.separator()
        
        l.label("Grass Density:")
        l.prop(m, 'density')
        r = l.row()
        r.prop_search(m, 'density_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'seed')
        l.separator()
        
        l.label("Blade Length:")
        l.prop(m, 'length')
        r = l.row()
        r.prop_search(m, 'length_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'length_variation')
        l.separator()
        
        l.label("Width:")
        l.prop(m, 'root_width')
        l.prop(m, 'tip_width')
        l.separator()
        
        l.label("Angle:")
        l.prop(m, 'direction_type')
        l.prop(m, 'initial_angle')
        r = l.row()
        r.prop_search(m, 'initial_angle_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'initial_angle_variation')
        l.separator()
        
        l.label("Bend:")
        l.prop(m, 'start_bend')
        r = l.row()
        r.prop_search(m, 'start_bend_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'start_bend_variation')
        
        l.prop(m, 'bend_radius')
        r = l.row()
        r.prop_search(m, 'bend_radius_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'bend_radius_variation')
        
        l.prop(m, 'bend_angle')
        r = l.row()
        r.prop_search(m, 'bend_angle_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'bend_angle_variation')
        l.separator()
        
        l.label("Cut Off:")
        l.prop(m, 'cut_off')
        r = l.row()
        r.prop_search(m, 'cut_off_map', ps, 'texture_slots', icon='TEXTURE', text="Map")
        r.prop(m, 'cut_off_variation')
        l.separator()
        
        l.prop(m, 'lod')
        r = l.row()
        r.prop(m, 'lod_min_distance')
        r.prop(m, 'lod_max_distance')
        if(not m.lod):
            r.enabled = False
        r = l.row()
        r.prop(m, 'lod_max_distance_density')
        if(not m.lod):
            r.enabled = False
        l.separator()
        
        l.label("Display:")
        l.prop(m, 'display_percent')
        l.prop(m, 'display_max_blades')


class HairExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Hair"
    
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
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        # m = context.particle_system.settings.maxwell_hair_extension
        
        l.label("Not implemented yet..", icon='ERROR', )


class ParticlesExtPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Particles"
    
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
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_particles_extension
        
        l.label("Object Properties:")
        s = l.split(percentage=0.7)
        c = s.column()
        c.prop(m, 'material_file')
        c = s.column()
        c.prop(m, 'material_embed', text='Embed', )
        l.separator()
        l.prop(m, 'hide')
        l.prop(m, 'hide_parent')
        l.prop(m, 'opacity')
        l.prop(m, 'object_id')
        l.separator()
        l.label("Hidden from:")
        s = l.split(percentage=0.5)
        c = s.column()
        c.prop(m, 'hidden_camera')
        c.prop(m, 'hidden_camera_in_shadow_channel')
        c.prop(m, 'hidden_global_illumination')
        c = s.column()
        c.prop(m, 'hidden_reflections_refractions')
        c.prop(m, 'hidden_zclip_planes')
        l.separator()
        
        l.label("Sequence:")
        l.prop(m, 'bin_filename')
        l.prop(m, 'bin_radius_multiplier')
        l.prop(m, 'bin_motion_blur_multiplier')
        l.prop(m, 'bin_shutter_speed')
        l.prop(m, 'bin_load_particles')
        l.prop(m, 'bin_axis_system')
        l.prop(m, 'bin_frame_number')
        l.prop(m, 'bin_fps')
        l.separator()
        
        l.prop(m, 'bin_advanced')
        
        if(m.bin_advanced):
            l.label("Multipoint:")
            l.prop(m, 'bin_extra_create_np_pp')
            l.prop(m, 'bin_extra_dispersion')
            l.prop(m, 'bin_extra_deformation')
            l.separator()
            
            l.label("Extra Arrays Loading:")
            s = l.split(percentage=0.5)
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
            l.separator()
            
            l.label("Magnitude Normalizing Values:")
            s = l.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_force')
            c.prop(m, 'bin_max_force')
            c = s.column(align=True)
            c.prop(m, 'bin_min_vorticity')
            c.prop(m, 'bin_max_vorticity')
            s = l.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_nneighbors')
            c.prop(m, 'bin_max_nneighbors')
            c = s.column(align=True)
            c.prop(m, 'bin_min_age')
            c.prop(m, 'bin_max_age')
            s = l.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_isolation_time')
            c.prop(m, 'bin_max_isolation_time')
            c = s.column(align=True)
            c.prop(m, 'bin_min_viscosity')
            c.prop(m, 'bin_max_viscosity')
            s = l.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_density')
            c.prop(m, 'bin_max_density')
            c = s.column(align=True)
            c.prop(m, 'bin_min_pressure')
            c.prop(m, 'bin_max_pressure')
            s = l.split(percentage=0.5)
            c = s.column(align=True)
            c.prop(m, 'bin_min_mass')
            c.prop(m, 'bin_max_mass')
            c = s.column(align=True)
            c.prop(m, 'bin_min_temperature')
            c.prop(m, 'bin_max_temperature')
            s = l.split(percentage=0.5)
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
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        # m = context.particle_system.settings.maxwell_mesher_extension
        
        l.label("Not implemented yet..", icon='ERROR', )


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
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        # m = context.particle_system.settings.maxwell_scatter_extension
        
        l.label("Not implemented yet..", icon='ERROR', )
