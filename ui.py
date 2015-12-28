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
import os

import bpy
from bpy.types import Panel, Menu, UIList
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
from . import system
from . import mxs


class BMPanel():
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "BMPanel"
    
    # extend Panel to test drawing..
    
    # regular use:
    # class ExportPanel(BMPanel, RenderButtonsPanel, Panel): BMPanel for drawing functions, RenderButtonsPanel for placement and poll, Panel for the rest..
    
    # bl_space_type = 'PROPERTIES'
    # bl_region_type = 'WINDOW'
    # bl_context = "render"
    
    # @classmethod
    # def poll(cls, context):
    #     # r = context.scene.render
    #     # return (not r.use_game_engine) and (r.engine in cls.COMPAT_ENGINES)
    #     scene = context.scene
    #     return scene and (scene.render.engine in cls.COMPAT_ENGINES)
    
    def prop_name(self, cls, prop, colon=False, ):
        """find property name"""
        for p in cls.bl_rna.properties:
            if(p.identifier == prop):
                if(colon):
                    return "{}:".format(p.name)
                return p.name
        return ''
    
    def tab_single(self, layout, cls, prop, label=True, text=False, ):
        """single property in a row, property name as label, then property value
        if label is True, label will be property name, if False, label will be omitted, if something else, it will be used as string
        if text is True, text will be added to property control, otherwise only value will be drawn
        returns whole ui element that can be enabled/disabled
        0         1/3                1
        | Name:   [*********   xx% ] |
        """
        r = layout.row()
        s = r.split(percentage=0.333)
        if(type(label) is bool):
            if(label):
                s.label(self.prop_name(cls, prop, True, ))
            else:
                s.label("")
        else:
            s.label("{}:".format(label))
        s = s.split(percentage=1.0)
        if(text):
            s.prop(cls, prop, )
        else:
            s.prop(cls, prop, text="", )
        return r
    
    def tab_singles_multi(self, layout, classes, props, align=False, label=True, text=False, ):
        """multiple property in a row of columns, property name as label, then property value, optionally aligned.
        if classes contains just one element, that class will be used for all, otherwise length of classes and names must be equal
        if label is True, label will be property name, if False, label will be omitted
        if text is True, text will be added to property control, otherwise only value will be drawn
        returns whole ui element that can be enabled/disabled
        0         1/3                1
        | Name:   [*********   xx% ] |
        | Name:   [*********   xx% ] |
        | Name:   [*********   xx% ] |
        ...
        """
        r = layout.row()
        s = r.split(percentage=0.333)
        c = s.column(align=align)
        if(len(classes) == 1):
            for i in range(len(props)):
                if(label):
                    c.label(self.prop_name(classes[0], props[i], True, ))
                else:
                    c.label("")
        else:
            for i in range(len(classes)):
                if(label):
                    c.label(self.prop_name(classes[i], props[i], True, ))
                else:
                    c.label("")
        s = s.split(percentage=1.0)
        c = s.column(align=align)
        if(len(classes) == 1):
            for i in range(len(props)):
                if(text):
                    c.prop(classes[0], props[i], )
                else:
                    c.prop(classes[0], props[i], text="", )
        else:
            for i in range(len(classes)):
                if(text):
                    c.prop(classes[i], props[i], )
                else:
                    c.prop(classes[i], props[i], text="", )
        return r
    
    def tab_double_one_third_split(self, layout, cls, name, props, align=False, label=True, text=False, ):
        """label and two properties in a row, split in one third, optionally aligned
        if label is True, label will be name argument, if False, label will be omitted, if something else, it will be used as string
        if text is True, text will be added to property control, otherwise only value will be drawn
        returns whole ui element that can be enabled/disabled
        0         1/3                1
                  0    1/3           1
        | Name:   [1st] [  second  ] |
        """
        r = layout.row()
        s = r.split(percentage=0.333)
        # s.label("{}:".format(name))
        if(type(label) is bool):
            if(label):
                s.label("{}:".format(name))
            else:
                s.label("")
        else:
            s.label("{}:".format(label))
        s = s.split(percentage=0.333, align=align, )
        if(text):
            s.prop(cls, props[0], )
        else:
            s.prop(cls, props[0], text="", )
        s = s.split(percentage=1.0, align=align, )
        if(text):
            s.prop(cls, props[1], )
        else:
            s.prop(cls, props[1], text="", )
        return r
    
    def tab_double_half_split(self, layout, cls, name, props, align=False, label=True, text=False, ):
        """label and two properties in a row, split in half, optionally aligned
        if label is True, label will be name argument, if False, label will be omitted, if something else, it will be used as string
        if text is True, text will be added to property control, otherwise only value will be drawn
        returns whole ui element that can be enabled/disabled
        0         1/3                1
                  0        1/2       1
        | Name:   [ first ] [second] |
        """
        r = layout.row()
        s = r.split(percentage=0.333)
        # s.label("{}:".format(name))
        if(type(label) is bool):
            if(label):
                s.label("{}:".format(name))
            else:
                s.label("")
        else:
            s.label("{}:".format(label))
        s = s.split(percentage=0.5, align=align, )
        if(text):
            s.prop(cls, props[0], )
        else:
            s.prop(cls, props[0], text="", )
        s = s.split(percentage=1.0, align=align, )
        if(text):
            s.prop(cls, props[1], )
        else:
            s.prop(cls, props[1], text="", )
        return r
    
    def tab_double_two_thirds_split(self, layout, cls, name, props, align=False, label=True, text=False, ):
        """label and two properties in a row, split in two thirds, optionally aligned
        if label is True, label will be name argument, if False, label will be omitted, if something else, it will be used as string
        if text is True, text will be added to property control, otherwise only value will be drawn
        returns whole ui element that can be enabled/disabled
        0         1/3                1
                  0           2/3    1
        | Name:   [   first   ][2nd] |
        """
        r = layout.row()
        s = r.split(percentage=0.333)
        # s.label("{}:".format(name))
        if(type(label) is bool):
            if(label):
                s.label("{}:".format(name))
            else:
                s.label("")
        else:
            s.label("{}:".format(label))
        s = s.split(percentage=0.666, align=align, )
        if(text):
            s.prop(cls, props[0], )
        else:
            s.prop(cls, props[0], text="", )
        s = s.split(percentage=1.0, align=align, )
        if(text):
            s.prop(cls, props[1], )
        else:
            s.prop(cls, props[1], text="", )
        return r
    
    def tab_triple(self, layout, cls, name, props, align=False, label=True, text=False, ):
        """label and three properties in a row, split in thirds, optionally aligned
        if label is True, label will be name argument, if False, label will be omitted, if something else, it will be used as string
        if text is True, text will be added to property control, otherwise only value will be drawn
        returns whole ui element that can be enabled/disabled
        0          1/3               1
                   0    1/3    2/3   1
        | Name:    [1st] [2nd] [3rd] |
        """
        r = layout.row()
        s = r.split(percentage=0.333)
        # s.label("{}:".format(name))
        if(type(label) is bool):
            if(label):
                s.label("{}:".format(name))
            else:
                s.label("")
        else:
            s.label("{}:".format(label))
        s = s.split(percentage=0.333, align=align, )
        if(text):
            s.prop(cls, props[0], )
        else:
            s.prop(cls, props[0], text="", )
        s = s.split(percentage=0.5, align=align, )
        if(text):
            s.prop(cls, props[1], )
        else:
            s.prop(cls, props[1], text="", )
        s = s.split(percentage=1.0, align=align, )
        if(text):
            s.prop(cls, props[2], )
        else:
            s.prop(cls, props[2], text="", )
    
    def tab_value_and_map(self, layout, cls, name, value, enabled, texture, search, ):
        """label and map value/color, texture enabled and texture map name
        if name is None label is taken from value property
        returns whole ui element that can be enabled/disabled
        0          1/3                   1
        | Name:    [value] [x] [texture] |
        """
        if(name is None):
            name = self.prop_name(cls, value, True, )
        r = layout.row()
        elm = r
        s = r.split(percentage=0.333)
        s.label(name)
        s = s.split(percentage=0.333)
        c = s.column()
        c.prop(cls, value, text="", )
        s = s.split(percentage=0.15, align=True, )
        r = s.row()
        r.alignment = 'RIGHT'
        r.prop(cls, enabled, text="", )
        s = s.split(percentage=1.0, align=True, )
        s.prop_search(cls, texture, search, 'texture_slots', icon='TEXTURE', text="", )
        return elm
    
    def tab_bump_value_and_map(self, layout, cls, name, value, enabled, texture, search, normal, normal_value, use_normal, ):
        """label and bump map value, texture enabled, texture map name and use normal
        if name is None label is taken from value property
        returns whole ui element that can be enabled/disabled and column with value to be disabled when no map is present
        0          1/3                    1
        | Name:    [value][x][texture][n] |
        
        usage:
        _, elm = self.tab_bump_value_and_map(sub, m, prop_name(m, 'global_bump', True, ), 'global_bump', 'global_bump_map_enabled', 'global_bump_map', mat, 'global_bump_map_use_normal', 'global_bump_normal', m.global_bump_map_use_normal, )
        if(not m.global_bump_map_enabled or m.global_bump_map == ''):
            elm.enabled = False
        """
        if(name is None):
            name = self.prop_name(cls, value, True, )
        r = layout.row()
        elm = r
        s = r.split(percentage=0.333)
        s.label(name)
        s = s.split(percentage=0.333)
        c = s.column()
        if(use_normal):
            c.prop(cls, normal_value, text="", )
        else:
            c.prop(cls, value, text="", )
        # if(not m.global_bump_map_enabled or m.global_bump_map == ''):
        #     c.enabled = False
        s = s.split(percentage=0.15, align=True, )
        r = s.row()
        r.alignment = 'RIGHT'
        r.prop(cls, enabled, text="", )
        s = s.split(percentage=0.85, align=True, )
        s.prop_search(cls, texture, search, 'texture_slots', icon='TEXTURE', text="", )
        s = s.split(percentage=1.0, align=True, )
        s.prop(cls, normal, text="N", toggle=True, )
        return elm, c
    
    '''
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        sub.label("BMPanel ui drawing tests:")
        
        m = context.scene.maxwell_render
        
        sub.label(">>> tab_single")
        sub.separator()
        self.tab_single(sub, m, 'scene_time')
        self.tab_single(sub, m, 'tone_sharpness_value')
        self.tab_single(sub, m, 'globals_diplacement')
        self.tab_single(sub, m, 'tone_color_space')
        
        self.tab_single(sub, m, 'scene_time', label=True, )
        self.tab_single(sub, m, 'tone_sharpness_value', label=False, )
        self.tab_single(sub, m, 'globals_diplacement', label="Globals: Displacement", )
        self.tab_single(sub, m, 'tone_color_space', label=False, text=True, )
        sub.separator()
        
        sub.label(">>> tab_singles_multi")
        sub.separator()
        self.tab_singles_multi(sub, [m, m, m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=False)
        self.tab_singles_multi(sub, [m, m, m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True)
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=False)
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True)
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=False, label=False)
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True, label=False)
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=False, label=False, text=True, )
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_sharpness_value'], align=True, label=False, text=True, )
        # two columns of multi singles..
        r = sub.row()
        s = r.split()
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True)
        s = r.split()
        self.tab_singles_multi(sub, [m], ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True)
        sub.separator()
        
        
        sub.label(">>> tab_double_one_third_split")
        sub.separator()
        self.tab_double_one_third_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=False, )
        self.tab_double_one_third_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=True, )
        self.tab_double_one_third_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=True, label=False, )
        self.tab_double_one_third_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=True, label="Something", )
        self.tab_double_one_third_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=True, label="Something", text=True, )
        sub.separator()
        
        sub.label(">>> tab_double_half_split")
        sub.separator()
        self.tab_double_half_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=False, )
        self.tab_double_half_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=True, )
        self.tab_double_half_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=True, label=False, )
        self.tab_double_half_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=True, label="Something", )
        self.tab_double_half_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=True, label="Something", text=True, )
        sub.separator()
        
        sub.label(">>> tab_double_two_thirds_split")
        sub.separator()
        self.tab_double_two_thirds_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=False, )
        self.tab_double_two_thirds_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=True, )
        self.tab_double_two_thirds_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=True, label=False, )
        self.tab_double_two_thirds_split(sub, m, 'Properties', ['scene_time', 'tone_color_space'], align=True, label="Something", )
        self.tab_double_two_thirds_split(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value'], align=True, label="Something", text=True, )
        sub.separator()
        
        sub.label("tab_triple")
        sub.separator()
        self.tab_triple(sub, m, 'Properties', ['scene_time', 'tone_color_space', 'tone_sharpness_value'], align=False, )
        self.tab_triple(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True, )
        self.tab_triple(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True, label=False, )
        self.tab_triple(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value', 'tone_color_space'], align=True, label="Something", )
        self.tab_triple(sub, m, 'Properties', ['scene_time', 'tone_sharpness_value', 'tone_sharpness_value'], align=True, label="Something", text=True, )
        sub.separator()
        
        sub.separator()
        mat = bpy.data.materials['custom 4']
        mx = mat.maxwell_render
        
        self.tab_single(sub, mx, 'global_id')
        self.tab_double_half_split(sub, mx, 'Properties', ['global_id', 'global_bump'], align=False, )
        self.tab_double_half_split(sub, mx, 'Properties', ['global_id', 'global_bump'], align=True, )
        
        sub.label(">>> tab_value_and_map")
        elm = self.tab_value_and_map(sub, mx, self.prop_name(mx, 'global_bump', colon=True, ), 'global_bump', 'global_bump_map_enabled', 'global_bump_map', mat, )
        elm = self.tab_value_and_map(sub, mx, self.prop_name(mx, 'global_bump', colon=True, ), 'global_bump', 'global_bump_map_enabled', 'global_bump_map', mat, )
        elm.enabled = False
        
        sub.label(">>> tab_bump_value_and_map")
        _, elm = self.tab_bump_value_and_map(sub, mx, prop_name(mx, 'global_bump', True, ), 'global_bump', 'global_bump_map_enabled', 'global_bump_map', mat, 'global_bump_map_use_normal', 'global_bump_normal', mx.global_bump_map_use_normal )
        if(not mx.global_bump_map_enabled or mx.global_bump_map == ''):
            elm.enabled = False
        
        elm = self.tab_value_and_map(sub, mx, None, 'global_bump', 'global_bump_map_enabled', 'global_bump_map', mat, )
        
        _, elm = self.tab_bump_value_and_map(sub, mx, None, 'global_bump', 'global_bump_map_enabled', 'global_bump_map', mat, 'global_bump_map_use_normal', 'global_bump_normal', mx.global_bump_map_use_normal, )
        if(not mx.global_bump_map_enabled or mx.global_bump_map == ''):
            elm.enabled = False
    '''


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
        r.prop(m, 'export_use_instances')
        r.prop(m, 'export_use_subdivision')
        
        sub.separator()
        
        r = sub.row()
        r.prop(m, 'export_log_open')
        r.prop(m, 'export_warning_log_write')
        
        r = sub.row()
        r.prop(m, 'export_remove_unused_materials')
        r.prop(m, 'export_protect_mxs')
        
        r = sub.row()
        r.prop(m, 'export_suppress_warning_popups')
        c = r.column()
        c.prop(m, 'export_keep_intermediates')
        if(platform.system() != 'Darwin'):
            c.enabled = False


class ExportSpecialsPanel(RenderButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Export Specials"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # NOTE: disabling wireframe until fixed, also remove this panel and move settings to operator
        return False
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.scene.maxwell_render
        b = sub.box()
        
        b.prop(m, 'export_use_wireframe')
        if(m.export_use_wireframe):
            b.label("Current implementation is not quite standard.", icon='ERROR', )
            b.label("Because of this Blender might crash..", icon='ERROR', )
            b.label("Save your work before hitting F12!", icon='ERROR', )
            
            c = b.column()
            c.label("Wireframe Options:")
            sc = c.column(align=True)
            sc.prop(m, 'export_wire_edge_radius')
            sc.prop(m, 'export_wire_edge_resolution')
            c.separator()
            
            c.prop_search(m, 'export_wire_wire_material', bpy.data, 'materials', icon='MATERIAL')
            c.prop(m, 'export_clay_override_object_material')
            
            sub = c.column()
            sub.prop_search(m, 'export_wire_clay_material', bpy.data, 'materials', icon='MATERIAL')
            if(not m.export_clay_override_object_material):
                sub.enabled = False
            
            # NOT TO DO: use UILayout.alert = True if missing values? prop_search does not support this..


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
        
        scene = context.scene
        rd = scene.render
        rl = rd.layers.active
        
        s = sub.split()
        c = s.column()
        c.prop(scene, "layers", text="Scene")
        c = s.column()
        c.prop(rl, "layers", text="Layer")
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
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_render')
        c = s.column()
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
        c = s.column(align=True)
        c.prop(m, 'channels_z_buffer_near', text="Near (m)")
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
        
        r = l.row()
        s = r.split(percentage=0.33)
        c = s.column()
        c.prop(m, 'channels_reflectance')
        c = s.column()
        c.prop(m, 'channels_reflectance_file', text="", )


class ManualCustomAlphasList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = 'IMAGE_ALPHA'
        if(self.layout_type in {'DEFAULT', 'COMPACT'}):
            # layout.prop(item, "name", text="", emboss=False, icon=icon, )
            # layout.prop(item, "opaque")
            
            # s = layout.split(percentage=0.7)
            c = layout.column()
            c.prop(item, "name", text="", emboss=False, icon=icon, )
            c = layout.column()
            r = c.row()
            r.alignment = 'RIGHT'
            # r.label("Opaque")
            # r.prop(item, "opaque", text="", )
            r.prop(item, "opaque")
        elif(self.layout_type in {'GRID'}):
            layout.alignment = 'CENTER'
            layout.prop(item, "name", text="", emboss=False, icon=icon, )


class ManualCustomAlphasObjectList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = 'OBJECT_DATA'
        if(self.layout_type in {'DEFAULT', 'COMPACT'}):
            layout.prop(item, "name", text="", emboss=False, icon=icon, )
        
        elif(self.layout_type in {'GRID'}):
            layout.alignment = 'CENTER'
            layout.prop(item, "name", text="", emboss=False, icon=icon, )


class ManualCustomAlphasMaterialList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon = 'MATERIAL_DATA'
        if(self.layout_type in {'DEFAULT', 'COMPACT'}):
            layout.prop(item, "name", text="", emboss=False, icon=icon, )
        
        elif(self.layout_type in {'GRID'}):
            layout.alignment = 'CENTER'
            layout.prop(item, "name", text="", emboss=False, icon=icon, )


class ManualCustomAlphasObjectMenuAdd(Menu):
    bl_label = "Add Object"
    bl_idname = "ManualCustomAlphasObjectMenuAdd"
    
    @classmethod
    def poll(cls, context):
        return (len(context.objects) > 0)
    
    def draw(self, context):
        l = self.layout
        
        allowed = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        obs = []
        for o in bpy.context.scene.objects:
            if(o.type in allowed):
                obs.append(o.name)
        
        mx = context.scene.maxwell_render
        alpha = mx.custom_alphas_manual.alphas[mx.custom_alphas_manual.index]
        
        num = 0
        obs.sort(key=str.lower)
        
        for n in obs:
            if(n not in alpha.objects):
                op = l.operator("maxwell_render.custom_alphas_object_add", text=n, )
                op.name = n
                num += 1
        
        if(num == 0):
            l.label("No objects to add..")


class ManualCustomAlphasMaterialMenuAdd(Menu):
    bl_label = "Add Material"
    bl_idname = "ManualCustomAlphasMaterialMenuAdd"
    
    @classmethod
    def poll(cls, context):
        return (len(bpy.data.materials) > 0)
    
    def draw(self, context):
        l = self.layout
        
        mats = []
        for m in bpy.data.materials:
            mats.append(m.name)
        
        mx = context.scene.maxwell_render
        alpha = mx.custom_alphas_manual.alphas[mx.custom_alphas_manual.index]
        
        num = 0
        mats.sort(key=str.lower)
        
        for n in mats:
            if(n not in alpha.materials):
                op = l.operator("maxwell_render.custom_alphas_material_add", text=n, )
                op.name = n
                num += 1
        
        if(num == 0):
            l.label("No materials to add..")


class ChannelsCustomAlphasPanel(RenderLayerButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Custom Alphas"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        smx = context.scene.maxwell_render
        r = sub.row()
        r.prop(smx, 'custom_alphas_use_groups', )
        
        if(smx.custom_alphas_use_groups):
            sub.label("Custom Alphas defined by Object groups.")
            
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
        else:
            # 'MANUAL_SELECTION'
            m = context.scene.maxwell_render
            cam = m.custom_alphas_manual
            
            sub.separator()
            r = sub.row()
            r.template_list("ManualCustomAlphasList", "", cam, "alphas", cam, "index", rows=3, maxrows=6, )
            c = r.column(align=True)
            c.operator("maxwell_render.custom_alphas_add", icon='ZOOMIN', text="", )
            c.operator("maxwell_render.custom_alphas_remove", icon='ZOOMOUT', text="", )
            
            try:
                alpha = cam.alphas[cam.index]
            except:
                return
            
            sub.label("'{}' Objects:".format(alpha.name))
            r = sub.row()
            r.template_list("ManualCustomAlphasObjectList", "", alpha, "objects", alpha, "o_index", rows=4, maxrows=6, )
            c = r.column(align=True)
            c.menu("ManualCustomAlphasObjectMenuAdd", text="", icon='ZOOMIN', )
            c.operator("maxwell_render.custom_alphas_object_remove", icon='ZOOMOUT', text="", )
            c.separator()
            c.operator("maxwell_render.custom_alphas_add_selected_objects", icon='GROUP_VERTEX', text="", )
            c.operator("maxwell_render.custom_alphas_object_clear", icon='X', text="", )
            sub.label("'{}' Materials:".format(alpha.name))
            r = sub.row()
            r.template_list("ManualCustomAlphasMaterialList", "", alpha, "materials", alpha, "m_index", rows=3, maxrows=6, )
            c = r.column(align=True)
            c.menu("ManualCustomAlphasMaterialMenuAdd", text="", icon='ZOOMIN', )
            c.operator("maxwell_render.custom_alphas_material_remove", icon='ZOOMOUT', text="", )
            c.separator()
            c.operator("maxwell_render.custom_alphas_material_clear", icon='X', text="", )


class WorldContextPanel(WorldButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_options = {'HIDE_HEADER'}
    bl_label = ""
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (not rd.use_game_engine) and (rd.engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        layout = self.layout
        
        scene = context.scene
        world = context.world
        space = context.space_data
        
        texture_count = world and len(world.texture_slots.keys())
        
        split = layout.split(percentage=0.85)
        if scene:
            # split.template_ID(scene, "world", new="world.new")
            split.template_ID(scene, "world", new="maxwell_render.world_new_override")
        elif world:
            split.template_ID(space, "pin_id")
        
        if texture_count:
            split.label(text=str(texture_count), icon='TEXTURE')


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
        if(context.world is None):
            return False
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
            r = sub.row()
            r.prop(m, 'dome_zenith')
            r = sub.row()
            r.prop(m, 'dome_horizon')
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
        if(context.world is None):
            return False
        m = context.world.maxwell_render
        e = context.scene.render.engine
        return (m.env_type != 'NONE') and (e in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.world.maxwell_render
        
        # sub.prop(m, 'sun_lamp_priority')
        # sub.separator()
        
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
            # sub.separator()
            
            sub.label("Location:")
            r = sub.row()
            r.prop(m, 'sun_location_type', expand=True, )
            sub.separator()
            
            if(m.sun_location_type == 'ANGLES'):
                sub.prop(m, 'sun_angles_zenith')
                sub.prop(m, 'sun_angles_azimuth')
            elif(m.sun_location_type == 'DIRECTION'):
                
                r = sub.row()
                s = r.split(percentage=0.333)
                s.prop(m, 'use_sun_lamp', )
                s = s.split(percentage=1.0, align=True, )
                s.prop_search(m, 'sun_lamp', bpy.data, 'lamps', icon='LAMP_SUN', text="", )
                if(not m.use_sun_lamp):
                    s.enabled = False
                
                sub.separator()
                
                r = sub.row()
                r.operator('maxwell_render.set_sun')
                if(m.sun_lamp != '' and m.use_sun_lamp is True):
                    r.enabled = False
                
                c = sub.column(align=True)
                c.prop(m, 'sun_dir_x')
                c.prop(m, 'sun_dir_y')
                c.prop(m, 'sun_dir_z')
                
                if(m.sun_lamp != '' and m.use_sun_lamp is True):
                    c.enabled = False
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
        if(context.world is None):
            return False
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
        
        # sub.prop(m, 'override')
        sub.label("See Sun Panel in World Settings")


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
        
        if(m.lens == 'TYPE_ORTHO_2'):
            sub.prop(o, 'ortho_scale', )
        else:
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
        
        sub.menu("Exposure_presets", text=bpy.types.Exposure_presets.bl_label)
        
        sub.prop(m, 'lock_exposure')
        sub.prop(m, 'shutter')
        sub.prop(m, 'fstop')
        sub.prop(m, 'ev')
        
        if(m.lens == 'TYPE_FISHEYE_3'):
            sub.prop(m, 'fov')
        if(m.lens == 'TYPE_SPHERICAL_4'):
            sub.prop(m, 'azimuth')
        if(m.lens == 'TYPE_CYLINDRICAL_5'):
            sub.prop(m, 'angle')
        if(m.lens == 'TYPE_LAT_LONG_STEREO_6'):
            sub.separator()
            sub.label('Lat-Long Stereo:')
            sub.prop(m, 'lls_type')
            r = sub.row(align=True)
            r.prop(m, 'lls_fovv')
            r.prop(m, 'lls_fovh')
            r = sub.row()
            r.prop(m, 'lls_flip_ray_x')
            r.prop(m, 'lls_flip_ray_y')
            sub.prop(m, 'lls_parallax_distance')
            sub.prop(m, 'lls_zenith_mode')
            sub.prop(m, 'lls_separation')
            sub.prop_search(m, 'lls_separation_map', bpy.data, 'textures', icon='TEXTURE')
        if(m.lens == 'TYPE_FISH_STEREO_7'):
            sub.separator()
            sub.label('Fish Stereo:')
            sub.prop(m, 'fs_type')
            sub.prop(m, 'fs_fov')
            sub.prop(m, 'fs_separation')
            sub.prop_search(m, 'fs_separation_map', bpy.data, 'textures', icon='TEXTURE')
            sub.prop(m, 'fs_vertical_mode')
            sub.prop(m, 'fs_dome_radius')
            sub.prop_search(m, 'fs_head_turn_map', bpy.data, 'textures', icon='TEXTURE')
            sub.prop(m, 'fs_dome_tilt_compensation')
            sub.prop(m, 'fs_dome_tilt')
            sub.prop_search(m, 'fs_head_tilt_map', bpy.data, 'textures', icon='TEXTURE')


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
        
        col = split.column()
        sub = col.column(align=True)
        sub.label(text="Frame Range:")
        sub.prop(scene, "frame_start")
        sub.prop(scene, "frame_end")
        sub.prop(scene, "frame_step")
        
        sub.label(text="Frame Rate:")
        
        CameraSensorPanel.draw_framerate(sub, rd)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.camera.maxwell_render
        o = context.camera
        rp = context.scene.render
        
        r = sub.row(align=True)
        r.menu("CAMERA_MT_presets", text=bpy.types.CAMERA_MT_presets.bl_label)
        
        self.draw_blender_part(context, sub)
        
        r = sub.row(align=True)
        r.label("Filmback (mm):")
        r.prop(o, 'sensor_width', text="", )
        r.prop(o, 'sensor_height', text="", )
        sub.prop(o, 'sensor_fit')
        
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
        # warn user when particles have render emitter False
        ob = context.active_object
        if(len(ob.particle_systems) > 0):
            for ps in ob.particle_systems:
                pset = ps.settings
                if((pset.use_render_emitter is True and m.hide is True) or (pset.use_render_emitter is False and m.hide is False)):
                    sub.label("Overrided by particle system ('{}') settings".format(ps.name), icon='ERROR', )
        sub.separator()
        
        sub.prop(m, 'opacity')
        sub.separator()
        r = sub.row()
        r.prop(m, 'object_id')
        
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface Material', )
        
        sub.label("Hidden from:")
        s = sub.split(percentage=0.5)
        c = s.column()
        c.prop(m, 'hidden_camera')
        c.prop(m, 'hidden_camera_in_shadow_channel')
        c.prop(m, 'hidden_global_illumination')
        c = s.column()
        c.prop(m, 'hidden_reflections_refractions')
        c.prop(m, 'hidden_zclip_planes')
        
        l.label("Blocked Emitters:")
        r = l.row()
        
        be = m.blocked_emitters
        r.template_list("ObjectPanelBlockedEmitters", "maxwell_render.blocked_emitters", be, "emitters", be, "index", rows=2, maxrows=3, )
        c = r.column(align=True)
        c.menu("ObjectPanelBlockedEmittersMenu", text="", icon='ZOOMIN', )
        c.operator('maxwell_render.blocked_emitter_add', icon='ZOOMOUT', text="", ).remove = True
        c.prop(context.scene.maxwell_render, 'blocked_emitters_deep_check', icon='ZOOM_ALL', text="", )
        
        l.separator()
        
        l.label("Set object properties to multiple objects:")
        l.operator('maxwell_render.copy_active_object_properties_to_selected')
        l.label("Set Object ID color to multiple objects:")
        r = l.row(align=True)
        p = r.operator('maxwell_render.set_object_id_color', text="R", )
        p.color = '0'
        p = r.operator('maxwell_render.set_object_id_color', text="G", )
        p.color = '1'
        p = r.operator('maxwell_render.set_object_id_color', text="B", )
        p.color = '2'
        p = r.operator('maxwell_render.set_object_id_color', text="White", )
        p.color = '3'
        p = r.operator('maxwell_render.set_object_id_color', text="Black", )
        p.color = '4'


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
        # aref = context.object.maxwell_assetref_extension.enabled
        if((o and o.type in ts) and (e in cls.COMPAT_ENGINES)):
            # if(vol or aref):
            if(vol):
                return False
            return True
        return False
    
    def draw_header(self, context):
        m = context.object.maxwell_render_reference
        self.layout.prop(m, 'enabled', text="")
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.maxwell_render_reference
        
        sub.prop(m, 'path')
        
        sub.prop_search(m, 'material', bpy.data, 'materials', icon='MATERIAL')
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        
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
        # aref = context.object.maxwell_assetref_extension.enabled
        if((o and o.type in ts) and (e in cls.COMPAT_ENGINES)):
            # if(ref or aref):
            if(ref):
                return False
            return True
        return False
    
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
        
        sub.prop_search(m, 'material', bpy.data, 'materials', icon='MATERIAL')
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        
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
        c.prop(m, 'remove_overlapped')
        c = sub.column()
        c.prop(m, 'seed')
        
        c = sub.column()
        sub.label("Angle:")
        sub.prop(m, 'direction_type')
        sub.prop(m, 'initial_angle')
        r = sub.row()
        r.prop_search(m, 'initial_angle_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
        r.prop(m, 'initial_angle_variation')
        
        c = sub.column(align=True)
        c.label("Scale:")
        c.prop(m, 'scale_x')
        c.prop(m, 'scale_y')
        c.prop(m, 'scale_z')
        c = sub.column(align=True)
        c.prop(m, 'scale_uniform')
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
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw_header(self, context):
        m = context.object.maxwell_sea_extension
        self.layout.prop(m, "enabled", text="")
    
    def draw(self, context):
        l = self.layout
        m = context.object.maxwell_sea_extension
        sub = l.column()
        if(not m.enabled):
            sub.active = False
        
        sub.prop_search(m, 'material', bpy.data, 'materials', icon='MATERIAL')
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        
        sub.separator()
        
        sub.prop(m, 'hide')
        # sub.prop(m, 'hide_parent')
        o = context.object
        sub.prop(o.maxwell_render, 'hide', text="Hide Parent Object", )
        
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


class ExtObjectGrassPanel(ObjectButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Grass Modifier"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        e = context.scene.render.engine
        o = context.active_object
        ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        return (o and o.type in ts) and (e in cls.COMPAT_ENGINES)
    
    def draw_header(self, context):
        m = context.object.maxwell_grass_extension
        self.layout.prop(m, "enabled", text="")
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        m = context.object.maxwell_grass_extension
        
        sub.menu("Grass_Modifier_presets", text=bpy.types.Grass_Modifier_presets.bl_label)
        
        sub.label("Primitive:")
        
        sub.prop_search(m, 'material', bpy.data, 'materials', icon='MATERIAL', )
        
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        sub.separator()
        
        r = sub.row()
        r.label("Primitive Type:")
        r.prop(m, 'primitive_type', expand=True, )
        sub.prop(m, 'points_per_blade')
        sub.separator()
        
        sub.label("Grass Density:")
        sub.prop(m, 'density')
        r = sub.row()
        r.prop_search(m, 'density_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
        r.prop(m, 'seed')
        sub.separator()
        
        sub.label("Blade Length:")
        sub.prop(m, 'length')
        r = sub.row()
        r.prop_search(m, 'length_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
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
        r.prop_search(m, 'initial_angle_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
        r.prop(m, 'initial_angle_variation')
        sub.separator()
        
        sub.label("Bend:")
        sub.prop(m, 'start_bend')
        r = sub.row()
        r.prop_search(m, 'start_bend_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
        r.prop(m, 'start_bend_variation')
        
        sub.prop(m, 'bend_radius')
        r = sub.row()
        r.prop_search(m, 'bend_radius_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
        r.prop(m, 'bend_radius_variation')
        
        sub.prop(m, 'bend_angle')
        r = sub.row()
        r.prop_search(m, 'bend_angle_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
        r.prop(m, 'bend_angle_variation')
        sub.separator()
        
        sub.label("Cut Off:")
        sub.prop(m, 'cut_off')
        r = sub.row()
        r.prop_search(m, 'cut_off_map', bpy.data, 'textures', icon='TEXTURE', text="Map", )
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


class MaterialContextPanel(MaterialButtonsPanel, Panel):
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
            # split.template_ID(ob, "active_material", new="material.new")
            split.template_ID(ob, "active_material", new="maxwell_render.material_new_override")
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
        # l.prop(m, 'flag', toggle=True, text="Refresh Preview", )
        # l.prop(bpy.context.scene.maxwell_render_private, 'material')


class MaterialTypePanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Material Type"
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        
        sub.prop(m, 'use', text="", )


class MaterialGlobalsPanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Global Properties"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        
        # sub.prop(m, 'use', text="Material Type", )
        # sub.separator()
        
        if(m.use == 'REFERENCE'):
            r = sub.row()
            r.prop(m, 'override_global_properties')
        
        if(m.use == 'REFERENCE' and not m.override_global_properties):
            sub = sub.column()
            sub.enabled = False
        
        sub.prop_search(m, 'global_override_map', mat, 'texture_slots', icon='TEXTURE', )
        
        r = sub.row()
        s = r.split(percentage=0.333)
        c = s.column()
        c.label("Global Bump:")
        c = s.column()
        r = c.row()
        c = r.column()
        if(m.global_bump_map_use_normal):
            c.prop(m, 'global_bump_normal', text="", )
        else:
            c.prop(m, 'global_bump', text="", )
        
        if(not m.global_bump_map_enabled or m.global_bump_map == ''):
            c.enabled = False
        r.prop(m, 'global_bump_map_enabled', text="", )
        r.prop_search(m, 'global_bump_map', mat, 'texture_slots', icon='TEXTURE', text="", )
        
        r = sub.row()
        s = r.split(percentage=0.333)
        c = s.column()
        c = s.column()
        r = c.row()
        if(not m.global_bump_map_enabled or m.global_bump_map == ''):
            c.enabled = False
        r.prop(m, 'global_bump_map_use_normal', text="Normal Mapping", )
        
        r = sub.row()
        r.prop(m, 'global_dispersion')
        r.prop(m, 'global_shadow')
        r.prop(m, 'global_matte')
        
        sub.prop(m, 'global_priority')
        
        r = sub.row()
        r.prop(m, 'global_id')
        
        if(m.use == 'CUSTOM'):
            sub.prop_search(m, 'custom_active_display_map', mat, 'texture_slots', icon='TEXTURE', )
        
        sub.separator()
        r = sub.row()
        r.prop(context.material, 'diffuse_color', text="Blender Viewport Color", )


class ExtMaterialDisplacement(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Displacement"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        d = context.material.maxwell_material_extension.displacement
        self.layout.prop(d, "enabled", text="", )
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        dtypes = ['AGS', 'OPAQUE', 'TRANSPARENT', 'METAL', 'TRANSLUCENT', 'CARPAINT', 'HAIR', ]
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use in dtypes)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        cd = mx.displacement
        
        if(not cd.enabled):
            l.enabled = False
        
        l.label("Common Properties:")
        l.prop_search(cd, 'map', mat, 'texture_slots', icon='TEXTURE', )
        l.prop(cd, 'type')
        
        r = l.row()
        s = r.split(percentage=0.333)
        c = s.column()
        c.label("Subdivision:")
        c = s.column()
        r = c.row()
        r.prop(cd, 'subdivision', text="", )
        r.prop(cd, 'adaptive', )
        l.prop(cd, 'subdivision_method')
        tab_single(l, "Offset:", cd, 'offset')
        tab_single(l, "Smoothing:", cd, 'smoothing')
        l.prop(cd, 'uv_interpolation')
        
        l.separator()
        l.label("HeightMap Properties:")
        tab_double(l, "Height:", cd, 'height', 'height_units', )
        
        if(cd.type == '2'):
            # Vector displacement
            l.separator()
            l.label("Vector 3D Properties:")
            l.prop(cd, 'v3d_preset')
            l.prop(cd, 'v3d_transform')
            l.prop(cd, 'v3d_rgb_mapping')
            r = l.row()
            r.prop(cd, 'v3d_scale')


class MaterialPanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Material"
    
    # def draw_header(self, context):
    #     try:
    #         m = context.material.maxwell_render
    #         self.bl_label = "'{}' Material".format(m.use)
    #     except:
    #         self.bl_label = "Material"
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        return (m or o) and (e in cls.COMPAT_ENGINES) and (m.maxwell_render.use != 'CUSTOM')
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        l = self.layout
        sub = l.column()
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        
        if(m.use == 'EMITTER'):
            self.bl_label = "Emitter"
            
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
                    sub.menu("ExtEmitter_presets", text=bpy.types.ExtEmitter_presets.bl_label)
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
            self.bl_label = "AGS"
            
            r = sub.row()
            s = r.split(percentage=0.33)
            c = s.column()
            c.label("Color:")
            c = s.column()
            c.prop(mx, 'ags_color', text="", )
            
            sub.prop(mx, 'ags_reflection')
            sub.prop(mx, 'ags_type')
            
        elif(m.use == 'OPAQUE'):
            self.bl_label = "Opaque"
            
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
            self.bl_label = "Transparent"
            
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
            self.bl_label = "Metal"
            
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
            self.bl_label = "Translucent"
            
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
            self.bl_label = "Carpaint"
            
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
            
        elif(m.use == 'HAIR'):
            self.bl_label = "Hair"
            
            sub.menu("Hair_presets", text=bpy.types.Hair_presets.bl_label)
            sub.separator()

            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'hair_color', text="", )
            r.prop(mx, 'hair_color_type', text="", )
            r.prop_search(mx, 'hair_color_map', mat, 'texture_slots', icon='TEXTURE', text="", )

            sub.prop_search(mx, 'hair_root_tip_map', mat, 'texture_slots', icon='TEXTURE', )

            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Root-Tip Weight:")
            c = s.column()
            r = c.row()
            r.prop(mx, 'hair_root_tip_weight', text="", )
            r.prop(mx, 'hair_root_tip_weight_type', text="", )
            r.prop_search(mx, 'hair_root_tip_weight_map', mat, 'texture_slots', icon='TEXTURE', text="", )

            sub.label('Primary Highlight:')
            r = sub.row(align=True)
            r.prop(mx, 'hair_primary_highlight_strength')
            r.prop(mx, 'hair_primary_highlight_spread')
            r = sub.row()
            r.prop(mx, 'hair_primary_highlight_tint')

            sub.label('Secondary Highlight:')
            r = sub.row(align=True)
            r.prop(mx, 'hair_secondary_highlight_strength')
            r.prop(mx, 'hair_secondary_highlight_spread')
            r = sub.row()
            r.prop(mx, 'hair_secondary_highlight_tint')
        
        elif(m.use == 'REFERENCE'):
            self.bl_label = "Reference"
            
            sub.prop(m, 'mxm_file')
            sub.prop(m, 'embed')
            r = sub.row(align=True)
            if(m.mxm_file == ''):
                s = sub.split(percentage=0.7, align=True)
                r = s.row(align=True)
                r.operator('maxwell_render.create_material').backface = False
                r = s.row(align=True)
                r.prop(m, 'force_preview_scene', toggle=True, text="", icon='SCENE_DATA', )
                r.prop(m, 'force_preview', toggle=True, text="", icon='SMOOTH', )
                if(not m.force_preview):
                    r.active = False
            else:
                s = sub.split(percentage=0.7, align=True)
                r = s.row(align=True)
                r.operator('maxwell_render.edit_material').backface = False
                r = s.row(align=True)
                r.prop(m, 'force_preview_scene', toggle=True, text="", icon='SCENE_DATA', )
                r.prop(m, 'force_preview', toggle=True, text="", icon='SMOOTH', )
                if(not m.force_preview):
                    r.active = False
        else:
            # 'CUSTOM'
            pass
        
        if(m.use != 'REFERENCE' and m.use != 'CUSTOM'):
            sub.separator()
            
            s = sub.split(percentage=0.7, align=True)
            r = s.row(align=True)
            if(m.use == 'EMITTER'):
                r.operator('maxwell_render.edit_extension_material', text="Edit Material in Mxed")
            else:
                r.operator('maxwell_render.edit_extension_material')
            r = s.row(align=True)
            r.prop(m, 'force_preview_scene', toggle=True, text="", icon='SCENE_DATA', )
            r.prop(m, 'force_preview', toggle=True, text="", icon='SMOOTH', )
            if(not m.force_preview):
                r.active = False
            if(m.use != 'EMITTER'):
                sub.operator('maxwell_render.load_material_from_mxm')
        
        if(m.use == 'REFERENCE'):
            # sub.separator()
            sub.operator('maxwell_render.browse_material')
            sub.operator('maxwell_render.load_material_from_mxm')
        
        if(m.use == 'CUSTOM'):
            # sometimes little details cause big problems..
            l = sub
            
            cd = m.custom_displacement
            b = l.box()
            r = b.row()
            r.prop(cd, 'expanded', icon='TRIA_DOWN' if cd.expanded else 'TRIA_RIGHT', icon_only=True, emboss=False, )
            r.prop(cd, 'enabled', text="", )
            r.label(text="Displacement", )
            ll = l
            if(cd.expanded):
                l = b.column()
                if(not cd.enabled):
                    l.enabled = False
                
                l.label("Global Properties:")
                l.prop_search(cd, 'map', mat, 'texture_slots', icon='TEXTURE', )
                l.prop(cd, 'type')
                
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Subdivision:")
                c = s.column()
                r = c.row()
                r.prop(cd, 'subdivision', text="", )
                r.prop(cd, 'adaptive', )
                
                l.prop(cd, 'subdivision_method')
                # l.prop(cd, 'offset')
                # l.prop(cd, 'smoothing')
                
                # r = l.row()
                # s = r.split(percentage=0.333)
                # c = s.column()
                # c.label("Offset:")
                # c = s.column()
                # r = c.row()
                # r.prop(cd, 'offset', text="", )
                
                tab_single(l, "Offset:", cd, 'offset')
                
                # r = l.row()
                # s = r.split(percentage=0.333)
                # c = s.column()
                # c.label("Smoothing:")
                # c = s.column()
                # r = c.row()
                # r.prop(cd, 'smoothing', text="", )
                
                tab_single(l, "Smoothing:", cd, 'smoothing')
                
                l.prop(cd, 'uv_interpolation')
                
                l.separator()
                l.label("HeightMap Properties:")
                
                # r = l.row()
                # s = r.split(percentage=0.333)
                # c = s.column()
                # c.label("Height:")
                # c = s.column()
                # r = c.row()
                # r.prop(cd, 'height', text="", )
                # r.prop(cd, 'height_units', text="", )
                
                tab_double(l, "Height:", cd, 'height', 'height_units', )
                
                l.separator()
                l.label("Vector 3D Properties:")
                l.prop(cd, 'v3d_preset')
                l.prop(cd, 'v3d_transform')
                l.prop(cd, 'v3d_rgb_mapping')
                r = l.row()
                r.prop(cd, 'v3d_scale')
            
            l = ll
            
            l.label("Layers:")
            
            r = l.row()
            cl = m.custom_layers
            r.template_list("MaterialPanelCustomEditorLayers", "", cl, "layers", cl, "index", rows=4, maxrows=6, )
            c = r.column(align=True)
            c.operator("maxwell_render.material_editor_add_layer", icon='ZOOMIN', text="", )
            c.operator("maxwell_render.material_editor_remove_layer", icon='ZOOMOUT', text="", )
            c.separator()
            c.operator("maxwell_render.material_editor_move_layer_up", icon='TRIA_UP', text="", )
            c.operator("maxwell_render.material_editor_move_layer_down", icon='TRIA_DOWN', text="", )
            c.operator("maxwell_render.material_editor_clone_layer", icon='GHOST', text="", )
            
            if(cl.index >= 0):
                l.separator()
                
                layer = cl.layers[cl.index].layer
                
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Layer Opacity:")
                c = s.column()
                r = c.row()
                r.prop(layer, 'opacity', text="", )
                r.prop(layer, 'opacity_map_enabled', text="", )
                r.prop_search(layer, 'opacity_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                
                l.separator()
                em = cl.layers[cl.index].emitter
                b = l.box()
                r = b.row()
                r.prop(em, 'expanded', icon='TRIA_DOWN' if em.expanded else 'TRIA_RIGHT', icon_only=True, emboss=False, )
                r.prop(em, 'enabled', text="", )
                r.label(text="Emitter", )
                ll = l
                if(em.expanded):
                    l = b.column()
                    if(not em.enabled):
                        l.enabled = False
                    sub = l
                    
                    sub.prop(em, 'type')
                    sub.separator()
                    if(em.type == '0'):
                        # Area
                        pass
                    elif(em.type == '1'):
                        # IES
                        sub.prop(em, 'ies_data')
                        sub.separator()
                        sub.prop(em, 'ies_intensity')
                        sub.separator()
                    elif(em.type == '2'):
                        # Spot
                        r = sub.row()
                        s = r.split(percentage=0.2)
                        c = s.column()
                        c.label("Spot Map:")
                        c = s.column()
                        r = c.row()
                        r.prop(em, 'spot_map_enabled', text="", )
                        r.prop_search(em, 'spot_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                        
                        sub.prop(em, 'spot_cone_angle')
                        sub.prop(em, 'spot_falloff_angle')
                        sub.prop(em, 'spot_falloff_type')
                        sub.prop(em, 'spot_blur')
                        sub.separator()
                    
                    if(em.type == '1'):
                        # IES
                        r = sub.row()
                        s = r.split(percentage=0.2)
                        c = s.column()
                        c.label("Color:")
                        c = s.column()
                        r = c.row()
                        r.prop(em, 'color', text="", )
                        r.prop(em, 'color_black_body_enabled', text="", )
                        r.prop(em, 'color_black_body')
                    elif(em.type == '2'):
                        # Spot
                        r = sub.row()
                        s = r.split(percentage=0.2)
                        c = s.column()
                        c.label("Color:")
                        c = s.column()
                        r = c.row()
                        r.prop(em, 'color', text="", )
                        r.prop(em, 'color_black_body_enabled', text="", )
                        r.prop(em, 'color_black_body')
                        sub.separator()
                        sub.prop(em, 'luminance')
                        if(em.luminance == '0'):
                            # Power & Efficacy
                            sub.prop(em, 'luminance_power')
                            sub.prop(em, 'luminance_efficacy')
                            # r = sub.row()
                            # r.prop(em, 'luminance_output', text="Output (lm)")
                            # r.enabled = False
                        elif(em.luminance == '1'):
                            # Lumen
                            sub.prop(em, 'luminance_output', text="Output (lm)")
                        elif(em.luminance == '2'):
                            # Lux
                            sub.prop(em, 'luminance_output', text="Output (lm/m)")
                        elif(em.luminance == '3'):
                            # Candela
                            sub.prop(em, 'luminance_output', text="Output (cd)")
                        elif(em.luminance == '4'):
                            # Luminance
                            sub.prop(em, 'luminance_output', text="Output (cd/m)")
                    else:
                        sub.prop(em, 'emission')
                        sub.separator()
                        
                        if(em.emission == '0'):
                            sub.menu("Emitter_presets", text=bpy.types.Emitter_presets.bl_label)
                            sub.separator()
                            # Color
                            r = sub.row()
                            s = r.split(percentage=0.2)
                            c = s.column()
                            c.label("Color:")
                            c = s.column()
                            r = c.row()
                            r.prop(em, 'color', text="", )
                            r.prop(em, 'color_black_body_enabled', text="", )
                            r.prop(em, 'color_black_body')
                            sub.separator()
                            sub.prop(em, 'luminance')
                            if(em.luminance == '0'):
                                # Power & Efficacy
                                c = sub.column(align=True)
                                c.prop(em, 'luminance_power')
                                c.prop(em, 'luminance_efficacy')
                                sub.label("Output: {} lm".format(round(em.luminance_power * em.luminance_efficacy, 1)))
                            elif(em.luminance == '1'):
                                # Lumen
                                sub.prop(em, 'luminance_output', text="Output (lm)")
                            elif(em.luminance == '2'):
                                # Lux
                                sub.prop(em, 'luminance_output', text="Output (lm/m)")
                            elif(em.luminance == '3'):
                                # Candela
                                sub.prop(em, 'luminance_output', text="Output (cd)")
                            elif(em.luminance == '4'):
                                # Luminance
                                sub.prop(em, 'luminance_output', text="Output (cd/m)")
                        elif(em.emission == '1'):
                            # Temperature
                            sub.prop(em, 'temperature_value')
                        elif(em.emission == '2'):
                            # HDR Image
                            sub.prop_search(em, 'hdr_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            sub.separator()
                            sub.prop(em, 'hdr_intensity')
                
                l = ll
                
                l.separator()
                l.label("'{}' BSDFs:".format(cl.layers[cl.index].name))
                
                clbs = cl.layers[cl.index].layer.bsdfs
                r = l.row()
                r.template_list("MaterialPanelCustomEditorLayerBSDFs", "", clbs, "bsdfs", clbs, "index", rows=4, maxrows=6, )
                c = r.column(align=True)
                c.operator("maxwell_render.material_editor_add_bsdf", icon='ZOOMIN', text="", )
                c.operator("maxwell_render.material_editor_remove_bsdf", icon='ZOOMOUT', text="", )
                c.separator()
                c.operator("maxwell_render.material_editor_move_bsdf_up", icon='TRIA_UP', text="", )
                c.operator("maxwell_render.material_editor_move_bsdf_down", icon='TRIA_DOWN', text="", )
                c.operator("maxwell_render.material_editor_clone_bsdf", icon='GHOST', text="", )
                
                if(clbs.index >= 0):
                    l.separator()
                    
                    try:
                        bsdf = clbs.bsdfs[clbs.index].bsdf
                    except IndexError:
                        # there is no such index > bsdf is not created yet, skip drawing of everything past this point..
                        return
                    
                    r = l.row()
                    s = r.split(percentage=0.333)
                    c = s.column()
                    c.label("Weight:")
                    c = s.column()
                    r = c.row()
                    r.prop(bsdf, 'weight', text="", )
                    r.prop(bsdf, 'weight_map_enabled', text="", )
                    r.prop_search(bsdf, 'weight_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                    
                    l.separator()
                    
                    b = l.box()
                    r = b.row()
                    r.prop(bsdf, "expanded_ior", icon="TRIA_DOWN" if bsdf.expanded_ior else "TRIA_RIGHT", icon_only=True, emboss=False, )
                    # r.label(text="BSDF", icon='MATERIAL', )
                    r.label(text="BSDF")
                    ll = l
                    if(bsdf.expanded_ior):
                        l = b.column()
                        l.prop(bsdf, 'ior')
                        
                        if(bsdf.ior == '1'):
                            l.prop(bsdf, 'complex_ior')
                        else:
                            # r = l.row()
                            # s = r.split(percentage=0.333)
                            # c = s.column()
                            # c.label("Reflectance 0:")
                            # c = s.column()
                            # r = c.row()
                            # r.prop(bsdf, 'reflectance_0', text="", )
                            # r.prop(bsdf, 'reflectance_0_map_enabled', text="", )
                            # r.prop_search(bsdf, 'reflectance_0_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            
                            tab_color_and_map(l, "Reflectance 0:", bsdf, 'reflectance_0', 'reflectance_0_map_enabled', 'reflectance_0_map', )
                            
                            # r = l.row()
                            # s = r.split(percentage=0.333)
                            # c = s.column()
                            # c.label("Reflectance 90:")
                            # c = s.column()
                            # r = c.row()
                            # r.prop(bsdf, 'reflectance_90', text="", )
                            # r.prop(bsdf, 'reflectance_90_map_enabled', text="", )
                            # r.prop_search(bsdf, 'reflectance_90_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            
                            tab_color_and_map(l, "Reflectance 90:", bsdf, 'reflectance_90', 'reflectance_90_map_enabled', 'reflectance_90_map', )
                            
                            # r = l.row()
                            # s = r.split(percentage=0.333)
                            # c = s.column()
                            # c.label("Transmittance:")
                            # c = s.column()
                            # r = c.row()
                            # r.prop(bsdf, 'transmittance', text="", )
                            # r.prop(bsdf, 'transmittance_map_enabled', text="", )
                            # r.prop_search(bsdf, 'transmittance_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            
                            tab_color_and_map(l, "Transmittance:", bsdf, 'transmittance', 'transmittance_map_enabled', 'transmittance_map', )
                            
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.label("Attenuation:")
                            c = s.column()
                            r = c.row()
                            r.prop(bsdf, 'attenuation', text="", )
                            r.prop(bsdf, 'attenuation_units', text="", )
                            
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.label("Nd:")
                            c = s.column()
                            r = c.row()
                            r.prop(bsdf, 'nd', text="", )
                            c = r.column()
                            c.prop(bsdf, 'force_fresnel')
                            if(bsdf.roughness == 100.0):
                                c.enabled = False
                            
                            r = l.row()
                            s = r.split(percentage=0.5)
                            c = s.column()
                            c.prop(bsdf, 'k')
                            if(bsdf.roughness == 100.0):
                                c.enabled = False
                            c = s.column()
                            c.prop(bsdf, 'abbe')
                            if(not m.global_dispersion):
                                c.enabled = False
                            
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.prop(bsdf, 'r2_enabled', text="R2", )
                            c = s.column()
                            r = c.row()
                            r.prop(bsdf, 'r2_falloff_angle', text="", )
                            r.prop(bsdf, 'r2_influence', text="", )
                            if(not bsdf.r2_enabled):
                                r.enabled = False
                    
                    l = ll
                    
                    b = l.box()
                    r = b.row()
                    r.prop(bsdf, "expanded_surface", icon="TRIA_DOWN" if bsdf.expanded_surface else "TRIA_RIGHT", icon_only=True, emboss=False, )
                    # r.label(text="Surface", icon='SOLID', )
                    r.label(text="Surface")
                    ll = l
                    if(bsdf.expanded_surface):
                        l = b.column()
                        
                        r = l.row()
                        s = r.split(percentage=0.333)
                        c = s.column()
                        c.label("Roughness:")
                        c = s.column()
                        r = c.row()
                        r.prop(bsdf, 'roughness', text="", )
                        r.prop(bsdf, 'roughness_map_enabled', text="", )
                        r.prop_search(bsdf, 'roughness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                        
                        r = l.row()
                        s = r.split(percentage=0.333)
                        c = s.column()
                        c.label("Bump:")
                        c = s.column()
                        r = c.row()
                        c = r.column()
                        
                        if(bsdf.bump_map_use_normal):
                            c.prop(bsdf, 'bump_normal', text="", )
                        else:
                            c.prop(bsdf, 'bump', text="", )
                        
                        if(not bsdf.bump_map_enabled or bsdf.bump_map == ''):
                            c.enabled = False
                        r.prop(bsdf, 'bump_map_enabled', text="", )
                        r.prop_search(bsdf, 'bump_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                        
                        r = l.row()
                        s = r.split(percentage=0.333)
                        c = s.column()
                        c = s.column()
                        r = c.row()
                        r.prop(bsdf, 'bump_map_use_normal', text="Normal Mapping", )
                        
                        r = l.row()
                        s = r.split(percentage=0.333)
                        c = s.column()
                        c.label("Anisotropy:")
                        c = s.column()
                        r = c.row()
                        r.prop(bsdf, 'anisotropy', text="", )
                        r.prop(bsdf, 'anisotropy_map_enabled', text="", )
                        r.prop_search(bsdf, 'anisotropy_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                        
                        r = l.row()
                        s = r.split(percentage=0.333)
                        c = s.column()
                        c.label("Angle:")
                        c = s.column()
                        r = c.row()
                        r.prop(bsdf, 'anisotropy_angle', text="", )
                        r.prop(bsdf, 'anisotropy_angle_map_enabled', text="", )
                        r.prop_search(bsdf, 'anisotropy_angle_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                    
                    l = ll
                    
                    b = l.box()
                    r = b.row()
                    r.prop(bsdf, "expanded_subsurface", icon="TRIA_DOWN" if bsdf.expanded_subsurface else "TRIA_RIGHT", icon_only=True, emboss=False, )
                    # r.label(text="Subsurface", icon='SMOOTH', )
                    r.label(text="Subsurface")
                    ll = l
                    if(bsdf.expanded_subsurface):
                        l = b.column()
                        
                        r = l.row()
                        r.prop(bsdf, 'scattering')
                        
                        r = l.row()
                        r.prop(bsdf, 'coef')
                        r.prop(bsdf, 'asymmetry')
                        
                        # l.prop(bsdf, 'single_sided')
                        if(bsdf.single_sided):
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            # c.label("Single Sided:")
                            c.prop(bsdf, 'single_sided')
                            c = s.column()
                            r = c.row()
                            r.prop(bsdf, 'single_sided_value', text="", )
                            r.prop(bsdf, 'single_sided_map_enabled', text="", )
                            r.prop_search(bsdf, 'single_sided_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            r = l.row(align=True)
                            r.prop(bsdf, 'single_sided_min', )
                            r.prop(bsdf, 'single_sided_max', )
                        else:
                            l.prop(bsdf, 'single_sided')
                    
                    l = ll
                    
                    coat = clbs.bsdfs[clbs.index].coating
                    b = l.box()
                    r = b.row()
                    r.prop(coat, "expanded", icon="TRIA_DOWN" if coat.expanded else "TRIA_RIGHT", icon_only=True, emboss=False, )
                    r.prop(coat, 'enabled', text='', )
                    # r.label(text="Coating", icon='TEXTURE_SHADED', )
                    r.label(text="Coating")
                    ll = l
                    if(coat.expanded):
                        l = b.column()
                        if(not coat.enabled):
                            l.enabled = False
                        
                        r = l.row()
                        s = r.split(percentage=0.333)
                        c = s.column()
                        c.label("Thickness (nm):")
                        c = s.column()
                        r = c.row()
                        r.prop(coat, 'thickness', text="", )
                        r.prop(coat, 'thickness_map_enabled', text="", )
                        r.prop_search(coat, 'thickness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                        
                        r = l.row(align=True)
                        r.prop(coat, 'thickness_map_min', text="Min", )
                        r.prop(coat, 'thickness_map_max', text="Max", )
                        
                        l.prop(coat, 'ior')
                        if(coat.ior == '1'):
                            l.prop(coat, 'complex_ior')
                        else:
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.label("Reflectance 0:")
                            c = s.column()
                            r = c.row()
                            r.prop(coat, 'reflectance_0', text="", )
                            r.prop(coat, 'reflectance_0_map_enabled', text="", )
                            r.prop_search(coat, 'reflectance_0_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.label("Reflectance 90:")
                            c = s.column()
                            r = c.row()
                            r.prop(coat, 'reflectance_90', text="", )
                            r.prop(coat, 'reflectance_90_map_enabled', text="", )
                            r.prop_search(coat, 'reflectance_90_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                            
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.label("Nd:")
                            c = s.column()
                            r = c.row()
                            r.prop(coat, 'nd', text="", )
                            r.prop(coat, 'force_fresnel')
                            
                            l.prop(coat, 'k')
                            
                            r = l.row()
                            s = r.split(percentage=0.333)
                            c = s.column()
                            c.prop(coat, 'r2_enabled', text="R2", )
                            c = s.column()
                            r = c.row()
                            r.prop(coat, 'r2_falloff_angle', text="", )
                            if(not coat.r2_enabled):
                                r.enabled = False
                    
                    l = ll
            
            l.separator()
            sub = l
            # s = sub.split(percentage=0.7, align=True)
            s = sub.split(percentage=0.6, align=True)
            r = s.row(align=True)
            r.operator('maxwell_render.save_material_as_mxm')
            r = s.row(align=True)
            # r.prop(m, 'custom_open_in_mxed_after_save', toggle=True, text="", icon='FILE_PARENT', )
            r.prop(m, 'custom_open_in_mxed_after_save', toggle=True, text="", icon='LIBRARY_DATA_DIRECT', )
            # r.prop(m, 'custom_open_in_mxed_after_save', toggle=True, text="Mxed", )
            r.prop(m, 'force_preview_scene', toggle=True, text="", icon='SCENE_DATA', )
            r.prop(m, 'force_preview', toggle=True, text="", icon='SMOOTH', )
            if(not m.force_preview):
                r.active = False
            sub.operator('maxwell_render.load_material_from_mxm')


class MaterialPanelCustomEditorLayers(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = False
        
        icon = 'FILE_FOLDER'
        if(self.layout_type in {'DEFAULT', 'COMPACT'}):
            l = item.layer
            
            s = layout.split(percentage=0.4, )
            c = s.column()
            c.prop(item, "name", text="", emboss=False, icon=icon, )
            c = s.column()
            r = c.row()
            
            s = r.split(percentage=0.333, )
            c = s.column()
            r = c.row()
            # r.prop(l, 'opacity', text="", )
            r.prop(l, 'blending', expand=True, )
            
            c = s.column()
            r = c.row()
            if(l.opacity_map_enabled):
                r.label('T')
            else:
                r.prop(l, 'opacity', text="", )
            # r.prop(l, 'visible', text="", )
            r.prop(l, 'visible', text="", icon='RESTRICT_VIEW_OFF' if l.visible else 'RESTRICT_VIEW_ON', emboss=False, )
            
            if(not l.visible):
                layout.active = False
        
        elif(self.layout_type in {'GRID'}):
            layout.alignment = 'CENTER'
            layout.prop(item, "name", text="", emboss=False, icon=icon, )


class MaterialPanelCustomEditorLayerBSDFs(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = False
        
        icon = 'FCURVE'
        if(self.layout_type in {'DEFAULT', 'COMPACT'}):
            # layout.prop(item, "name", text="", emboss=False, icon=icon, )
            l = item.bsdf
            
            s = layout.split(percentage=0.4, )
            c = s.column()
            c.prop(item, "name", text="", emboss=False, icon=icon, )
            c = s.column()
            r = c.row()
            
            s = r.split(percentage=0.333, )
            c = s.column()
            r = c.row()
            # r.prop(l, 'weight', text="", )
            c = s.column()
            r = c.row()
            if(l.weight_map_enabled):
                r.label('T')
            else:
                r.prop(l, 'weight', text="", )
            # r.prop(l, 'blending', expand=True, )
            # r.prop(l, 'visible', text="", )
            r.prop(l, 'visible', text="", icon='RESTRICT_VIEW_OFF' if l.visible else 'RESTRICT_VIEW_ON', emboss=False, )
            
            if(not l.visible):
                layout.active = False
        
        elif(self.layout_type in {'GRID'}):
            layout.alignment = 'CENTER'
            layout.prop(item, "name", text="", emboss=False, icon=icon, )


class CustomMaterialLayers(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Layers"
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        return (m or o) and (e in cls.COMPAT_ENGINES) and (m.maxwell_render.use == 'CUSTOM')
    
    def draw(self, context):
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        
        l = self.layout.column()
        
        r = l.row()
        cl = m.custom_layers
        r.template_list("MaterialPanelCustomEditorLayers", "", cl, "layers", cl, "index", rows=4, maxrows=6, )
        c = r.column(align=True)
        c.operator("maxwell_render.material_editor_add_layer", icon='ZOOMIN', text="", )
        c.operator("maxwell_render.material_editor_remove_layer", icon='ZOOMOUT', text="", )
        c.separator()
        c.operator("maxwell_render.material_editor_move_layer_up", icon='TRIA_UP', text="", )
        c.operator("maxwell_render.material_editor_move_layer_down", icon='TRIA_DOWN', text="", )
        c.operator("maxwell_render.material_editor_clone_layer", icon='GHOST', text="", )
        
        if(cl.index >= 0):
            l.separator()
            
            layer = cl.layers[cl.index].layer
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Layer Opacity:")
            c = s.column()
            r = c.row()
            r.prop(layer, 'opacity', text="", )
            r.prop(layer, 'opacity_map_enabled', text="", )
            r.prop_search(layer, 'opacity_map', mat, 'texture_slots', icon='TEXTURE', text="", )


class CustomMaterialDisplacement(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Displacement"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        d = context.material.maxwell_render.custom_displacement
        self.layout.prop(d, "enabled", text="", )
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        ls = mx.custom_layers.layers
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        cd = m.custom_displacement
        
        if(not cd.enabled):
            l.enabled = False
        
        l.label("Common Properties:")
        l.prop_search(cd, 'map', mat, 'texture_slots', icon='TEXTURE', )
        l.prop(cd, 'type')
        
        r = l.row()
        s = r.split(percentage=0.333)
        c = s.column()
        c.label("Subdivision:")
        c = s.column()
        r = c.row()
        r.prop(cd, 'subdivision', text="", )
        r.prop(cd, 'adaptive', )
        l.prop(cd, 'subdivision_method')
        tab_single(l, "Offset:", cd, 'offset')
        tab_single(l, "Smoothing:", cd, 'smoothing')
        l.prop(cd, 'uv_interpolation')
        
        l.separator()
        l.label("HeightMap Properties:")
        tab_double(l, "Height:", cd, 'height', 'height_units', )
        
        if(cd.type == '2'):
            # Vector displacement
            l.separator()
            l.label("Vector 3D Properties:")
            l.prop(cd, 'v3d_preset')
            l.prop(cd, 'v3d_transform')
            l.prop(cd, 'v3d_rgb_mapping')
            r = l.row()
            r.prop(cd, 'v3d_scale')


class CustomMaterialEmitter(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Emitter"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        mx = context.material.maxwell_render
        e = mx.custom_layers.layers[mx.custom_layers.index].emitter
        self.layout.prop(e, "enabled", text="", )
        
        cl = context.material.maxwell_render.custom_layers
        self.bl_label = "'{}' Emitter".format(cl.layers[cl.index].name)
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        ls = mx.custom_layers.layers
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        cl = m.custom_layers
        em = cl.layers[cl.index].emitter
        
        if(not em.enabled):
            l.enabled = False
        sub = l
        
        sub.prop(em, 'type')
        sub.separator()
        if(em.type == '0'):
            # Area
            pass
        elif(em.type == '1'):
            # IES
            sub.prop(em, 'ies_data')
            sub.separator()
            sub.prop(em, 'ies_intensity')
            sub.separator()
        elif(em.type == '2'):
            # Spot
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Spot Map:")
            c = s.column()
            r = c.row()
            r.prop(em, 'spot_map_enabled', text="", )
            r.prop_search(em, 'spot_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            sub.prop(em, 'spot_cone_angle')
            sub.prop(em, 'spot_falloff_angle')
            sub.prop(em, 'spot_falloff_type')
            sub.prop(em, 'spot_blur')
            sub.separator()
        if(em.type == '1'):
            # IES
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(em, 'color', text="", )
            r.prop(em, 'color_black_body_enabled', text="", )
            r.prop(em, 'color_black_body')
        elif(em.type == '2'):
            # Spot
            r = sub.row()
            s = r.split(percentage=0.2)
            c = s.column()
            c.label("Color:")
            c = s.column()
            r = c.row()
            r.prop(em, 'color', text="", )
            r.prop(em, 'color_black_body_enabled', text="", )
            r.prop(em, 'color_black_body')
            sub.separator()
            sub.prop(em, 'luminance')
            if(em.luminance == '0'):
                # Power & Efficacy
                sub.prop(em, 'luminance_power')
                sub.prop(em, 'luminance_efficacy')
            elif(em.luminance == '1'):
                # Lumen
                sub.prop(em, 'luminance_output', text="Output (lm)")
            elif(em.luminance == '2'):
                # Lux
                sub.prop(em, 'luminance_output', text="Output (lm/m)")
            elif(em.luminance == '3'):
                # Candela
                sub.prop(em, 'luminance_output', text="Output (cd)")
            elif(em.luminance == '4'):
                # Luminance
                sub.prop(em, 'luminance_output', text="Output (cd/m)")
        else:
            sub.prop(em, 'emission')
            sub.separator()
            if(em.emission == '0'):
                sub.menu("Emitter_presets", text=bpy.types.Emitter_presets.bl_label)
                sub.separator()
                # Color
                r = sub.row()
                s = r.split(percentage=0.2)
                c = s.column()
                c.label("Color:")
                c = s.column()
                r = c.row()
                r.prop(em, 'color', text="", )
                r.prop(em, 'color_black_body_enabled', text="", )
                r.prop(em, 'color_black_body')
                sub.separator()
                sub.prop(em, 'luminance')
                if(em.luminance == '0'):
                    # Power & Efficacy
                    c = sub.column(align=True)
                    c.prop(em, 'luminance_power')
                    c.prop(em, 'luminance_efficacy')
                    sub.label("Output: {} lm".format(round(em.luminance_power * em.luminance_efficacy, 1)))
                elif(em.luminance == '1'):
                    # Lumen
                    sub.prop(em, 'luminance_output', text="Output (lm)")
                elif(em.luminance == '2'):
                    # Lux
                    sub.prop(em, 'luminance_output', text="Output (lm/m)")
                elif(em.luminance == '3'):
                    # Candela
                    sub.prop(em, 'luminance_output', text="Output (cd)")
                elif(em.luminance == '4'):
                    # Luminance
                    sub.prop(em, 'luminance_output', text="Output (cd/m)")
            elif(em.emission == '1'):
                # Temperature
                sub.prop(em, 'temperature_value')
            elif(em.emission == '2'):
                # HDR Image
                sub.prop_search(em, 'hdr_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                sub.separator()
                sub.prop(em, 'hdr_intensity')


class CustomMaterialBSDFs(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "BSDFs"
    
    def draw_header(self, context):
        cl = context.material.maxwell_render.custom_layers
        self.bl_label = "'{}' BSDFs".format(cl.layers[cl.index].name)
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        ls = mx.custom_layers.layers
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        cl = m.custom_layers
        
        # l.label("'{}' BSDFs:".format(cl.layers[cl.index].name))
        # self.bl_label = "'{}' BSDFs".format(cl.layers[cl.index].name)
        
        clbs = cl.layers[cl.index].layer.bsdfs
        r = l.row()
        r.template_list("MaterialPanelCustomEditorLayerBSDFs", "", clbs, "bsdfs", clbs, "index", rows=4, maxrows=6, )
        c = r.column(align=True)
        c.operator("maxwell_render.material_editor_add_bsdf", icon='ZOOMIN', text="", )
        c.operator("maxwell_render.material_editor_remove_bsdf", icon='ZOOMOUT', text="", )
        c.separator()
        c.operator("maxwell_render.material_editor_move_bsdf_up", icon='TRIA_UP', text="", )
        c.operator("maxwell_render.material_editor_move_bsdf_down", icon='TRIA_DOWN', text="", )
        c.operator("maxwell_render.material_editor_clone_bsdf", icon='GHOST', text="", )
        
        if(clbs.index >= 0):
            l.separator()
            
            try:
                bsdf = clbs.bsdfs[clbs.index].bsdf
            except IndexError:
                # there is no such index > bsdf is not created yet, skip drawing of everything past this point..
                return
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Weight:")
            c = s.column()
            r = c.row()
            r.prop(bsdf, 'weight', text="", )
            r.prop(bsdf, 'weight_map_enabled', text="", )
            r.prop_search(bsdf, 'weight_map', mat, 'texture_slots', icon='TEXTURE', text="", )


class CustomMaterialBSDF(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "BSDF"
    
    def draw_header(self, context):
        m = context.material.maxwell_render
        cl = m.custom_layers
        clbs = cl.layers[cl.index].layer.bsdfs
        if(clbs.index >= 0):
            try:
                bsdfitem = clbs.bsdfs[clbs.index]
                self.bl_label = "'{}' BSDF".format(bsdfitem.name)
            except IndexError:
                self.bl_label = "BSDF"
        else:
            self.bl_label = "BSDF"
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        cs = mx.custom_layers
        ls = cs.layers
        if(cs.index < 0):
            return False
        bs = ls[cs.index].layer.bsdfs.bsdfs
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0) and (len(bs) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        
        cl = m.custom_layers
        clbs = cl.layers[cl.index].layer.bsdfs
        if(clbs.index >= 0):
            try:
                bsdf = clbs.bsdfs[clbs.index].bsdf
            except IndexError:
                # there is no such index > bsdf is not created yet, skip drawing of everything past this point..
                return
            
            l.prop(bsdf, 'ior')
        
            if(bsdf.ior == '1'):
                l.prop(bsdf, 'complex_ior')
            else:
                tab_color_and_map(l, "Reflectance 0:", bsdf, 'reflectance_0', 'reflectance_0_map_enabled', 'reflectance_0_map', )
                tab_color_and_map(l, "Reflectance 90:", bsdf, 'reflectance_90', 'reflectance_90_map_enabled', 'reflectance_90_map', )
                tab_color_and_map(l, "Transmittance:", bsdf, 'transmittance', 'transmittance_map_enabled', 'transmittance_map', )
            
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Attenuation:")
                c = s.column()
                r = c.row()
                r.prop(bsdf, 'attenuation', text="", )
                r.prop(bsdf, 'attenuation_units', text="", )
            
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Nd:")
                c = s.column()
                r = c.row()
                r.prop(bsdf, 'nd', text="", )
                c = r.column()
                c.prop(bsdf, 'force_fresnel')
                if(bsdf.roughness == 100.0):
                    c.enabled = False
            
                r = l.row()
                s = r.split(percentage=0.5)
                c = s.column()
                c.prop(bsdf, 'k')
                if(bsdf.roughness == 100.0):
                    c.enabled = False
                c = s.column()
                c.prop(bsdf, 'abbe')
                if(not m.global_dispersion):
                    c.enabled = False
            
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.prop(bsdf, 'r2_enabled', text="R2", )
                c = s.column()
                r = c.row()
                r.prop(bsdf, 'r2_falloff_angle', text="", )
                r.prop(bsdf, 'r2_influence', text="", )
                if(not bsdf.r2_enabled):
                    r.enabled = False


class CustomMaterialSurface(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Surface"
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        cs = mx.custom_layers
        ls = cs.layers
        if(cs.index < 0):
            return False
        bs = ls[cs.index].layer.bsdfs.bsdfs
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0) and (len(bs) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        
        cl = m.custom_layers
        clbs = cl.layers[cl.index].layer.bsdfs
        if(clbs.index >= 0):
            try:
                bsdf = clbs.bsdfs[clbs.index].bsdf
            except IndexError:
                # there is no such index > bsdf is not created yet, skip drawing of everything past this point..
                return
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Roughness:")
            c = s.column()
            r = c.row()
            r.prop(bsdf, 'roughness', text="", )
            r.prop(bsdf, 'roughness_map_enabled', text="", )
            r.prop_search(bsdf, 'roughness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Bump:")
            c = s.column()
            r = c.row()
            c = r.column()
            
            if(bsdf.bump_map_use_normal):
                c.prop(bsdf, 'bump_normal', text="", )
            else:
                c.prop(bsdf, 'bump', text="", )
            
            if(not bsdf.bump_map_enabled or bsdf.bump_map == ''):
                c.enabled = False
            r.prop(bsdf, 'bump_map_enabled', text="", )
            r.prop_search(bsdf, 'bump_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c = s.column()
            r = c.row()
            if(not bsdf.bump_map_enabled or bsdf.bump_map == ''):
                c.enabled = False
            r.prop(bsdf, 'bump_map_use_normal', text="Normal Mapping", )
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Anisotropy:")
            c = s.column()
            r = c.row()
            r.prop(bsdf, 'anisotropy', text="", )
            r.prop(bsdf, 'anisotropy_map_enabled', text="", )
            r.prop_search(bsdf, 'anisotropy_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Angle:")
            c = s.column()
            r = c.row()
            r.prop(bsdf, 'anisotropy_angle', text="", )
            r.prop(bsdf, 'anisotropy_angle_map_enabled', text="", )
            r.prop_search(bsdf, 'anisotropy_angle_map', mat, 'texture_slots', icon='TEXTURE', text="", )


class CustomMaterialSubsurface(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Subsurface"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        cs = mx.custom_layers
        ls = cs.layers
        if(cs.index < 0):
            return False
        bs = ls[cs.index].layer.bsdfs.bsdfs
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0) and (len(bs) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        cl = m.custom_layers
        clbs = cl.layers[cl.index].layer.bsdfs
        if(clbs.index >= 0):
            try:
                bsdf = clbs.bsdfs[clbs.index].bsdf
            except IndexError:
                # there is no such index > bsdf is not created yet, skip drawing of everything past this point..
                return
            
            r = l.row()
            r.prop(bsdf, 'scattering')
        
            r = l.row()
            r.prop(bsdf, 'coef')
            r.prop(bsdf, 'asymmetry')
        
            if(bsdf.single_sided):
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.prop(bsdf, 'single_sided')
                c = s.column()
                r = c.row()
                r.prop(bsdf, 'single_sided_value', text="", )
                r.prop(bsdf, 'single_sided_map_enabled', text="", )
                r.prop_search(bsdf, 'single_sided_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                r = l.row(align=True)
                r.prop(bsdf, 'single_sided_min', )
                r.prop(bsdf, 'single_sided_max', )
            else:
                l.prop(bsdf, 'single_sided')


class CustomMaterialCoating(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Coating"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        mx = context.material.maxwell_render
        l = mx.custom_layers.layers[mx.custom_layers.index].layer
        c = l.bsdfs.bsdfs[l.bsdfs.index].coating
        self.layout.prop(c, "enabled", text="", )
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        cs = mx.custom_layers
        ls = cs.layers
        if(cs.index < 0):
            return False
        bs = ls[cs.index].layer.bsdfs.bsdfs
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM') and (len(ls) > 0) and (len(bs) > 0)
    
    def draw(self, context):
        def tab_single(l, t, o, pn):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn, text="", )
        
        def tab_double(l, t, o, pn0, pn1):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, pn0, text="", )
            r.prop(o, pn1, text="", )
        
        def tab_color_and_map(l, t, o, p, pe, pm, ):
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label(t)
            c = s.column()
            r = c.row()
            r.prop(o, p, text="", )
            r.prop(o, pe, text="", )
            r.prop_search(o, pm, mat, 'texture_slots', icon='TEXTURE', text="", )
        
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        
        cl = m.custom_layers
        clbs = cl.layers[cl.index].layer.bsdfs
        if(clbs.index >= 0):
            try:
                bsdf = clbs.bsdfs[clbs.index].bsdf
            except IndexError:
                # there is no such index > bsdf is not created yet, skip drawing of everything past this point..
                return
            
            coat = clbs.bsdfs[clbs.index].coating
            
            r = l.row()
            s = r.split(percentage=0.333)
            c = s.column()
            c.label("Thickness (nm):")
            c = s.column()
            r = c.row()
            r.prop(coat, 'thickness', text="", )
            r.prop(coat, 'thickness_map_enabled', text="", )
            r.prop_search(coat, 'thickness_map', mat, 'texture_slots', icon='TEXTURE', text="", )
            
            r = l.row(align=True)
            r.prop(coat, 'thickness_map_min', text="Min (nm)", )
            r.prop(coat, 'thickness_map_max', text="Max (nm)", )
            
            l.prop(coat, 'ior')
            if(coat.ior == '1'):
                l.prop(coat, 'complex_ior')
            else:
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Reflectance 0:")
                c = s.column()
                r = c.row()
                r.prop(coat, 'reflectance_0', text="", )
                r.prop(coat, 'reflectance_0_map_enabled', text="", )
                r.prop_search(coat, 'reflectance_0_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Reflectance 90:")
                c = s.column()
                r = c.row()
                r.prop(coat, 'reflectance_90', text="", )
                r.prop(coat, 'reflectance_90_map_enabled', text="", )
                r.prop_search(coat, 'reflectance_90_map', mat, 'texture_slots', icon='TEXTURE', text="", )
                
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.label("Nd:")
                c = s.column()
                r = c.row()
                r.prop(coat, 'nd', text="", )
                r.prop(coat, 'force_fresnel')
                
                l.prop(coat, 'k')
                
                r = l.row()
                s = r.split(percentage=0.333)
                c = s.column()
                c.prop(coat, 'r2_enabled', text="R2", )
                c = s.column()
                r = c.row()
                r.prop(coat, 'r2_falloff_angle', text="", )
                if(not coat.r2_enabled):
                    r.enabled = False


class CustomMaterialUtilities(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Utilities"
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM')
    
    def draw(self, context):
        m = context.material.maxwell_render
        mx = context.material.maxwell_material_extension
        mat = context.material
        l = self.layout.column()
        
        s = l.split(percentage=0.6, align=True)
        r = s.row(align=True)
        r.operator('maxwell_render.save_material_as_mxm')
        r = s.row(align=True)
        r.prop(m, 'custom_open_in_mxed_after_save', toggle=True, text="", icon='LIBRARY_DATA_DIRECT', )
        r.prop(m, 'force_preview_scene', toggle=True, text="", icon='SCENE_DATA', )
        r.prop(m, 'force_preview', toggle=True, text="", icon='SMOOTH', )
        if(not m.force_preview):
            r.active = False
        l.operator('maxwell_render.load_material_from_mxm')


class MaterialBackfacePanel(MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Backface Material"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return False
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        m = context.object.maxwell_render
        
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        
        r = sub.row(align=True)
        if(m.backface_material_file == ''):
            r.operator('maxwell_render.create_material').backface = True
        else:
            r.operator('maxwell_render.edit_material').backface = True


class MaterialWizardPanel(BMPanel, MaterialButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Material Wizards"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        o = context.object
        e = context.scene.render.engine
        m = context.material
        if(m is None):
            return False
        mx = m.maxwell_render
        return (m or o) and (e in cls.COMPAT_ENGINES) and (mx.use == 'CUSTOM')
    
    def draw(self, context):
        mat = context.material
        mx = mat.maxwell_render
        w = mx.wizards
        l = self.layout.column()
        
        l.prop(w, 'types')
        l.separator()
        
        if(w.types == 'GREASY'):
            self.tab_single(l, w, 'greasy_color')
            l.separator()
            l.operator('maxwell_render.material_wizard_greasy', text="Execute! (material will be replaced)", )
        # elif(w.types == 'PLASTIC'):
        #     # Plastic wizard is the same as Opaque extension..
        #     self.tab_single(l, w, 'plastic_shininess')
        #     self.tab_single(l, w, 'plastic_roughness')
        #     self.tab_single(l, w, 'plastic_color')
        #     l.separator()
        #     l.operator('maxwell_render.material_wizard_plastic', text="Execute! (material will be replaced)", )
        elif(w.types == 'TEXTURED'):
            self.tab_single(l, w, 'textured_diffuse')
            self.tab_single(l, w, 'textured_specular')
            self.tab_single(l, w, 'textured_bump')
            self.tab_single(l, w, 'textured_bump_strength')
            self.tab_single(l, w, 'textured_normal')
            self.tab_single(l, w, 'textured_alpha')
            l.separator()
            l.operator('maxwell_render.material_wizard_textured', text="Execute! (material will be replaced)", )
        elif(w.types == 'VELVET'):
            self.tab_single(l, w, 'velvet_color')
            l.separator()
            l.operator('maxwell_render.material_wizard_velvet', text="Execute! (material will be replaced)", )
        else:
            pass


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
        
        ts = context.texture_slot
        
        # l.label("Texture Type:")
        # l.prop(m, 'use', text="")
        
        if(m.use == 'IMAGE'):
            tex = None
            if(ts.texture is not None):
                if(ts.texture.type == 'IMAGE'):
                    tex = ts.texture
            if(tex is None):
                l.active = False
            
            # c = l.column()
            if(tex is not None and tex.image):
                # image = tex.image
                # c.active = False
                # c.enabled = False
                # c.prop(image, 'filepath', text="Path:")
                # c.prop(tex, 'image')
                pass
            else:
                # c = l.column()
                # c.label("Load an image", icon='ERROR', )
                l.label("Load an image", icon='ERROR', )
        
        l.label("Projection Properties:")
        
        def is_override_map(tex, mat):
            mmx = mat.maxwell_render
            if(mmx.global_override_map is not ""):
                if(mmx.global_override_map == tex.name):
                    return True
            return False
        
        if(not is_override_map(tex, context.material)):
            l.prop(m, 'use_global_map')
        
        sub = l.column()
        sub.active = not m.use_global_map
        
        tex = context.texture
        ob = context.object
        
        sub.prop(m, 'channel')
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
        
        l.label("Image Properties:")
        
        sub = l.column()
        r = sub.row()
        r.prop(m, 'invert')
        r.prop(m, 'use_alpha')
        r.prop(m, 'interpolation')
        
        sub = l.column()
        sub.prop(m, 'brightness')
        sub.prop(m, 'contrast')
        sub.prop(m, 'saturation')
        sub.prop(m, 'hue')
        
        r = sub.row()
        r.prop(m, 'clamp')
        
        l.label("Normal Mapping:")
        sub = l.column()
        r = sub.row()
        r.prop(m, 'normal_mapping_flip_red')
        r.prop(m, 'normal_mapping_flip_green')
        r.prop(m, 'normal_mapping_full_range_blue')


class TextureProceduralPanel(TextureButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Procedural Texture"
    
    @classmethod
    def poll(cls, context):
        if(not super().poll(context)):
            return False
        if(context.space_data.texture_context not in ['MATERIAL', 'PARTICLES']):
            return False
        m = context.texture.maxwell_render
        if(m.use == 'IMAGE'):
            return False
        return True
    
    def draw(self, context):
        l = self.layout
        m = context.texture.maxwell_render
        
        use = [('IMAGE', "Image"), ('BRICK', "Brick"), ('CHECKER', "Checker"), ('CIRCLE', "Circle"), ('GRADIENT3', "Gradient3"),
               ('GRADIENT', "Gradient"), ('GRID', "Grid"), ('MARBLE', "Marble"), ('NOISE', "Noise"), ('VORONOI', "Voronoi"),
               ('TILEDTEXTURE', "Tiled"), ('WIREFRAMETEXTURE', "Wireframe"), ]
        for i, t in enumerate(use):
            if(t[0] == m.use):
                self.bl_label = "Maxwell {} Texture".format(t[1])
                break
        
        if(m.use == 'BRICK'):
            sub = l.column()
            sub.prop(m, 'brick_blend_procedural')
            sub.label("Brick:")
            sub.prop(m, 'brick_brick_width')
            sub.prop(m, 'brick_brick_height')
            sub.prop(m, 'brick_brick_offset')
            sub.prop(m, 'brick_random_offset')
            sub.prop(m, 'brick_double_brick')
            sub.prop(m, 'brick_small_brick_width')
            sub.prop(m, 'brick_round_corners')
            r = sub.row(align=True)
            r.prop(m, 'brick_boundary_sharpness_u')
            r.prop(m, 'brick_boundary_sharpness_v')
            sub.prop(m, 'brick_boundary_noise_detail')
            r = sub.row(align=True)
            r.prop(m, 'brick_boundary_noise_region_u')
            r.prop(m, 'brick_boundary_noise_region_v')
            sub.prop(m, 'brick_seed')
            sub.prop(m, 'brick_random_rotation')
            sub.prop(m, 'brick_color_variation')
            r = sub.row()
            r.prop(m, 'brick_brick_color_0')
            sub.prop_search(m, 'brick_brick_texture_0', bpy.data, 'textures', icon='TEXTURE')
            sub.prop(m, 'brick_sampling_factor_0')
            sub.prop(m, 'brick_weight_0')
            r = sub.row()
            r.prop(m, 'brick_brick_color_1')
            sub.prop_search(m, 'brick_brick_texture_1', bpy.data, 'textures', icon='TEXTURE')
            sub.prop(m, 'brick_sampling_factor_1')
            sub.prop(m, 'brick_weight_1')
            r = sub.row()
            r.prop(m, 'brick_brick_color_2')
            sub.prop_search(m, 'brick_brick_texture_2', bpy.data, 'textures', icon='TEXTURE')
            sub.prop(m, 'brick_sampling_factor_2')
            sub.prop(m, 'brick_weight_2')
            sub.label("Mortar:")
            sub.prop(m, 'brick_mortar_thickness')
            r = sub.row()
            r.prop(m, 'brick_mortar_color')
            sub.prop_search(m, 'brick_mortar_texture', bpy.data, 'textures', icon='TEXTURE')
        elif(m.use == 'CHECKER'):
            sub = l.column()
            sub.prop(m, 'checker_blend_procedural')
            sub.prop(m, 'checker_number_of_elements_u')
            sub.prop(m, 'checker_number_of_elements_v')
            r = sub.row()
            r.prop(m, 'checker_color_0')
            r = sub.row()
            r.prop(m, 'checker_color_1')
            sub.prop(m, 'checker_transition_sharpness')
            sub.prop(m, 'checker_falloff')
        elif(m.use == 'CIRCLE'):
            sub = l.column()
            sub.prop(m, 'circle_blend_procedural')
            r = sub.row()
            r.prop(m, 'circle_background_color')
            r = sub.row()
            r.prop(m, 'circle_circle_color')
            sub.prop(m, 'circle_radius_u')
            sub.prop(m, 'circle_radius_v')
            sub.prop(m, 'circle_transition_factor')
            sub.prop(m, 'circle_falloff')
        elif(m.use == 'GRADIENT3'):
            sub = l.column()
            sub.prop(m, 'gradient3_blend_procedural')
            sub.prop(m, 'gradient3_gradient_u', text="U Direction")
            sc = sub.column()
            sc.active = m.gradient3_gradient_u
            r = sc.row()
            r.prop(m, 'gradient3_color0_u')
            r = sc.row()
            r.prop(m, 'gradient3_color1_u')
            r = sc.row()
            r.prop(m, 'gradient3_color2_u')
            sc.prop(m, 'gradient3_gradient_type_u')
            sc.prop(m, 'gradient3_color1_u_position')
            sub.prop(m, 'gradient3_gradient_v', text="V Direction")
            sc = sub.column()
            sc.active = m.gradient3_gradient_v
            r = sc.row()
            r.prop(m, 'gradient3_color0_v')
            r = sc.row()
            r.prop(m, 'gradient3_color1_v')
            r = sc.row()
            r.prop(m, 'gradient3_color2_v')
            sc.prop(m, 'gradient3_gradient_type_v')
            sc.prop(m, 'gradient3_color1_v_position')
        elif(m.use == 'GRADIENT'):
            sub = l.column()
            sub.prop(m, 'gradient_blend_procedural')
            sub.prop(m, 'gradient_gradient_u', text="U Direction")
            sc = sub.column()
            sc.active = m.gradient_gradient_u
            r = sc.row()
            r.prop(m, 'gradient_color0_u')
            r = sc.row()
            r.prop(m, 'gradient_color1_u')
            sc.prop(m, 'gradient_gradient_type_u')
            sc.prop(m, 'gradient_transition_factor_u')
            sub.prop(m, 'gradient_gradient_v', text="V Direction")
            sc = sub.column()
            sc.active = m.gradient_gradient_v
            r = sc.row()
            r.prop(m, 'gradient_color0_v')
            r = sc.row()
            r.prop(m, 'gradient_color1_v')
            sc.prop(m, 'gradient_gradient_type_v')
            sc.prop(m, 'gradient_transition_factor_v')
        elif(m.use == 'GRID'):
            sub = l.column()
            sub.prop(m, 'grid_blend_procedural')
            r = sub.row()
            r.prop(m, 'grid_cell_color')
            r = sub.row()
            r.prop(m, 'grid_boundary_color')
            # r = sub.row()
            # r.prop(m, 'grid_horizontal_lines')
            # r.prop(m, 'grid_vertical_lines')
            c = sub.column(align=True)
            c.prop(m, 'grid_cell_width')
            c.prop(m, 'grid_cell_height')
            c = sub.column(align=True)
            c.prop(m, 'grid_boundary_thickness_u')
            c.prop(m, 'grid_boundary_thickness_v')
            sub.prop(m, 'grid_transition_sharpness')
            sub.prop(m, 'grid_falloff')
        elif(m.use == 'MARBLE'):
            sub = l.column()
            sub.prop(m, 'marble_blend_procedural')
            sub.prop(m, 'marble_coordinates_type')
            r = sub.row()
            r.prop(m, 'marble_color0')
            r = sub.row()
            r.prop(m, 'marble_color1')
            r = sub.row()
            r.prop(m, 'marble_color2')
            sub.prop(m, 'marble_frequency')
            sub.prop(m, 'marble_detail')
            sub.prop(m, 'marble_octaves')
            sub.prop(m, 'marble_seed')
        elif(m.use == 'NOISE'):
            sub = l.column()
            sub.prop(m, 'noise_blend_procedural')
            sub.prop(m, 'noise_coordinates_type')
            r = sub.row()
            r.prop(m, 'noise_noise_color')
            r = sub.row()
            r.prop(m, 'noise_background_color')
            sub.prop(m, 'noise_detail')
            sub.prop(m, 'noise_persistance')
            sub.prop(m, 'noise_octaves')
            c = sub.column(align=True)
            c.prop(m, 'noise_low_value')
            c.prop(m, 'noise_high_value')
            sub.prop(m, 'noise_seed')
        elif(m.use == 'VORONOI'):
            sub = l.column()
            sub.prop(m, 'voronoi_blend_procedural')
            sub.prop(m, 'voronoi_coordinates_type')
            r = sub.row()
            r.prop(m, 'voronoi_color0')
            r = sub.row()
            r.prop(m, 'voronoi_color1')
            sub.prop(m, 'voronoi_detail')
            sub.prop(m, 'voronoi_distance')
            sub.prop(m, 'voronoi_combination')
            c = sub.column(align=True)
            c.prop(m, 'voronoi_low_value')
            c.prop(m, 'voronoi_high_value')
            sub.prop(m, 'voronoi_seed')
        elif(m.use == 'TILEDTEXTURE'):
            sub = l.column()
            sub.prop(m, 'tiled_blend_procedural')
            sub.prop(m, 'tiled_filename')
            sub.prop(m, 'tiled_token_mask')
            r = sub.row()
            r.prop(m, 'tiled_base_color')
            sub.prop(m, 'tiled_use_base_color')
        elif(m.use == 'WIREFRAMETEXTURE'):
            sub = l.column()
            r = sub.row()
            r.prop(m, 'wireframe_fill_color')
            r = sub.row()
            r.prop(m, 'wireframe_edge_color')
            r = sub.row()
            r.prop(m, 'wireframe_coplanar_edge_color')
            sub.prop(m, 'wireframe_edge_width')
            sub.prop(m, 'wireframe_coplanar_edge_width')
            sub.prop(m, 'wireframe_coplanar_threshold')


class ParticleContextPanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_options = {'HIDE_HEADER'}
    bl_label = ""
    
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.particle_system or context.object or context.space_data.pin_id) and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        def particle_panel_enabled(context, psys):
            if psys is None:
                return True
            phystype = psys.settings.physics_type
            if psys.settings.type in {'EMITTER', 'REACTOR'} and phystype in {'NO', 'KEYED'}:
                return True
            else:
                return (psys.point_cache.is_baked is False) and (not psys.is_edited) and (not context.particle_system_editable)
        
        def particle_get_settings(context):
            if context.particle_system:
                return context.particle_system.settings
            elif isinstance(context.space_data.pin_id, bpy.types.ParticleSettings):
                return context.space_data.pin_id
            return None
        
        layout = self.layout
        
        if context.scene.render.engine == 'BLENDER_GAME':
            layout.label("Not available in the Game Engine")
            return
        
        ob = context.object
        psys = context.particle_system
        part = 0
        
        if ob:
            row = layout.row()
            
            row.template_list("PARTICLE_UL_particle_systems", "particle_systems", ob, "particle_systems",
                              ob.particle_systems, "active_index", rows=1)
            
            col = row.column(align=True)
            # col.operator("object.particle_system_add", icon='ZOOMIN', text="")
            col.operator("maxwell_render.particle_system_add_override", icon='ZOOMIN', text="")
            col.operator("object.particle_system_remove", icon='ZOOMOUT', text="")
            col.menu("PARTICLE_MT_specials", icon='DOWNARROW_HLT', text="")
        
        if psys is None:
            part = particle_get_settings(context)
            
            # layout.operator("object.particle_system_add", icon='ZOOMIN', text="New")
            layout.operator("maxwell_render.particle_system_add_override", icon='ZOOMIN', text="New")
            
            if part is None:
                return
            
            layout.template_ID(context.space_data, "pin_id")
            
            if part.is_fluid:
                layout.label(text="Settings used for fluid")
                return
            
            layout.prop(part, "type", text="Type")
        
        elif not psys.settings:
            split = layout.split(percentage=0.32)
            
            col = split.column()
            col.label(text="Settings:")
            
            col = split.column()
            col.template_ID(psys, "settings", new="particle.new")
        else:
            part = psys.settings
            
            split = layout.split(percentage=0.32)
            col = split.column()
            if part.is_fluid is False:
                col.label(text="Settings:")
                col.label(text="Type:")
            
            col = split.column()
            if part.is_fluid is False:
                row = col.row()
                row.enabled = particle_panel_enabled(context, psys)
                row.template_ID(psys, "settings", new="particle.new")
            
            if part.is_fluid:
                layout.label(text=iface_("%d fluid particles for this frame") % part.count, translate=False)
                return
            
            row = col.row()
            row.enabled = particle_panel_enabled(context, psys)
            row.prop(part, "type", text="")
            row.prop(psys, "seed")
        
        if part:
            split = layout.split(percentage=0.65)
            if part.type == 'HAIR':
                if psys is not None and psys.is_edited:
                    split.operator("particle.edited_clear", text="Free Edit")
                else:
                    row = split.row()
                    row.enabled = particle_panel_enabled(context, psys)
                    row.prop(part, "regrow_hair")
                    row.prop(part, "use_advanced_hair")
                row = split.row()
                row.enabled = particle_panel_enabled(context, psys)
                row.prop(part, "hair_step")
                if psys is not None and psys.is_edited:
                    if psys.is_global_hair:
                        layout.operator("particle.connect_hair")
                    else:
                        layout.operator("particle.disconnect_hair")
            elif psys is not None and part.type == 'REACTOR':
                split.enabled = particle_panel_enabled(context, psys)
                split.prop(psys, "reactor_target_object")
                split.prop(psys, "reactor_target_particle_system", text="Particle System")


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
        
        sub.prop_search(m, 'material', bpy.data, 'materials', icon='MATERIAL')
        sub.prop_search(m, 'backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        
        sub.separator()
        
        sub.prop(context.particle_system.settings, 'use_render_emitter', text="Render Emitter", )
        sub.prop(m, 'hide')
        # sub.prop(m, 'hide_parent')
        # sub.prop(o.maxwell_render, 'hide', text="Hide Parent Object (Emitter)", )
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
        
        r = sub.row()
        r.prop(m, 'hair_type', expand=True, )
        sub.separator()
        
        if(m.hair_type == 'GRASS'):
            c = sub.column(align=True)
            c.prop(m, 'grass_root_width')
            c.prop(m, 'grass_tip_width')
        else:
            c = sub.column(align=True)
            c.prop(m, 'hair_root_radius', text="Root Diameter (mm)", )
            c.prop(m, 'hair_tip_radius', text="Tip Diameter (mm)", )
        
        sub.separator()
        r = sub.row()
        if(len(o.data.uv_textures) == 0):
            r.label("No UV Maps", icon='ERROR', )
        else:
            r.prop_search(m, "uv_layer", o.data, "uv_textures", )
        
        # if(m.uv_layer != "" and p.settings.child_type != 'NONE'):
        #     # NOT TO DO: check hair children particles again, seems to be crashing when exporting with uvs. put there warning at least
        #     sub.label("Particle hair with children + UVs!", icon='ERROR', )
        #     sub.label("Blender may crash during .mxs export!", icon='ERROR', )
        #     sub.label("Save your work before hitting F12!", icon='ERROR', )
        
        sub.separator()
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
        
        r = sub.row()
        r.prop(m, 'source', expand=True)
        if(m.source == 'EXTERNAL_BIN'):
            sub.prop(m, 'bin_filename')
            
            sub.prop(m, 'bin_type')
            if(m.bin_type == 'SEQUENCE'):
                sub.prop(m, 'seq_limit')
                r = sub.row(align=True)
                if(not m.seq_limit):
                    r.active = False
                r.prop(m, 'seq_start')
                r.prop(m, 'seq_end')
        else:
            r = sub.row()
            r.prop(m, 'bl_use_velocity')
            r.prop(m, 'bl_use_size')
            r = sub.row()
            r.prop(m, 'bl_size')
            if(m.bl_use_size):
                r.active = False
            
            sub.separator()
            sub.prop(m, 'embed')
            if(not m.embed):
                sub.prop(m, 'bin_directory')
                sub.prop(m, 'bin_overwrite')
        
        sub.separator()
        
        sub.prop(m, 'bin_radius_multiplier')
        sub.prop(m, 'bin_motion_blur_multiplier')
        sub.prop(m, 'bin_shutter_speed')
        sub.prop(m, 'bin_load_particles')
        sub.prop(m, 'bin_axis_system')
        sub.prop(m, 'bin_frame_number')
        sub.prop(m, 'bin_fps')
        sub.separator()
        
        if(m.source == 'EXTERNAL_BIN'):
            pass
        else:
            # sub.separator()
            r = sub.row()
            if(len(o.data.uv_textures) == 0):
                r.label("No UV Maps", icon='ERROR', )
            else:
                r.prop_search(m, "uv_layer", o.data, "uv_textures", )
            if(not m.embed):
                r.enabled = False
        
        sub.prop(m, 'bin_advanced')
        
        if(m.bin_advanced):
            sub.label("Multipoint:")
            c = sub.column(align=True)
            c.prop(m, 'bin_extra_create_np_pp')
            c.prop(m, 'bin_extra_dispersion')
            c.prop(m, 'bin_extra_deformation')
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
            r = sub.row()
            r.prop(m, 'bl_use_velocity')
            r.prop(m, 'bl_use_size')
            r = sub.row()
            r.prop(m, 'bl_size')
            if(m.bl_use_size):
                r.active = False
            
            sub.separator()
            sub.prop(m, 'embed')
            if(not m.embed):
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


class ParticlesInstancePanel(ParticleButtonsPanel, Panel):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Particle Instances"
    
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
        if(m.use != 'PARTICLE_INSTANCES'):
            return False
        
        return settings.is_fluid is False and (engine in cls.COMPAT_ENGINES)
    
    def draw(self, context):
        l = self.layout
        sub = l.column()
        
        o = context.object
        p = context.particle_system
        if(p is None):
            return
        
        m = context.particle_system.settings.maxwell_particle_instances
        
        # sub.label("See 'Render' panel for settings.")
        # sub.label("'Object' and 'Group' types are supported.")
        
        # sub.prop(m, 'inherit_objectid')
        
        if(p.settings.render_type not in ['OBJECT', 'GROUP', ]):
            sub.label("See 'Render' panel for settings.", icon='ERROR', )
            sub.label("'Object' and 'Group' types are supported.", icon='ERROR', )
            return
        
        # sub.prop_search(m, 'override_material', bpy.data, 'materials', icon='MATERIAL')
        # sub.prop_search(m, 'override_backface_material', bpy.data, 'materials', icon='MATERIAL', text='Backface', )
        #
        # sub.separator()
        
        sub.prop(m, 'hide')
        sub.prop(o.maxwell_render, 'hide', text="Hide Parent Object (Emitter)", )
        
        # sub.prop(m, 'hide_parent')
        # sub.prop(m, 'opacity')
        # sub.separator()
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


class ObjectPanelBlockedEmitters(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'RADIO'
        if(self.layout_type in {'DEFAULT', 'COMPACT'}):
            layout.label(item.name, icon=custom_icon, )
            # layout.label(item.name)
        elif(self.layout_type in {'GRID'}):
            layout.alignment = 'CENTER'
            layout.label("", icon=custom_icon, )


class ObjectPanelBlockedEmittersMenu(Menu):
    bl_label = "Blocked Emitters"
    bl_idname = "ObjectPanelBlockedEmittersMenu"
    
    @classmethod
    def poll(cls, context):
        return context.object
    
    def draw(self, context):
        l = self.layout
        
        ts = ['MESH', 'CURVE', 'SURFACE', 'FONT', ]
        # es = set([o.name for o in context.scene.objects if o.type in ts])
        es = set()
        for o in context.scene.objects:
            # skip non-mesh objects
            if(o.type in ts):
                for s in o.material_slots:
                    # skip empty material slots
                    if(s.material is not None):
                        m = s.material
                        mx = m.maxwell_render
                        mxe = m.maxwell_material_extension
                        if(context.scene.maxwell_render.blocked_emitters_deep_check):
                            if(mx.use == 'EMITTER'):
                                # emitter extension material, this one should always be emitter, no need for further checks
                                es.add(o.name)
                            elif(mx.use == 'REFERENCE'):
                                # now check if referenced material has emitter layer
                                p = bpy.path.abspath(mx.mxm_file)
                                if(os.path.exists(p)):
                                    if(system.PLATFORM == 'Darwin'):
                                        a = system.python34_run_mxm_is_emitter(p)
                                        if(a):
                                            es.add(o.name)
                                    elif(system.PLATFORM == 'Linux' or system.PLATFORM == 'Windows'):
                                        mxmec = mxs.MXMEmitterCheck(p)
                                        if(mxmec.emitter):
                                            es.add(o.name)
                            elif(mx.use == 'CUSTOM'):
                                for ilayer, layer in enumerate(mx.custom_layers.layers):
                                    if(layer.emitter.enabled):
                                        es.add(o.name)
                        else:
                            es.add(o.name)
        
        # remove current object
        o = context.object
        es.discard(o.name)
        # remove already blocked
        be = [e.name for e in o.maxwell_render.blocked_emitters.emitters]
        es = es.difference(be)
        eso = list(es)
        eso.sort()
        
        for n in eso:
            op = l.operator("maxwell_render.blocked_emitter_add", text=n, )
            op.name = n
            op.remove = False


class Render_presets(Menu):
    '''Presets for render options.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Render Presets"
    bl_idname = "Render_presets"
    preset_subdir = "blendmaxwell/render"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Channels_presets(Menu):
    '''Presets for channels settings.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Channels Presets"
    bl_idname = "Channels_presets"
    preset_subdir = "blendmaxwell/channels"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Environment_presets(Menu):
    '''Presets for environment settings.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Environment Presets"
    bl_idname = "Environment_presets"
    preset_subdir = "blendmaxwell/environment"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Camera_presets(Menu):
    '''Presets for camera settings.'''
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Maxwell Camera Presets"
    bl_idname = "Camera_presets"
    preset_subdir = "blendmaxwell/camera"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Opaque_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Opaque Presets"
    bl_idname = "Opaque_presets"
    preset_subdir = "blendmaxwell/material/opaque"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Transparent_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Transparent Presets"
    bl_idname = "Transparent_presets"
    preset_subdir = "blendmaxwell/material/transparent"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Metal_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Metal Presets"
    bl_idname = "Metal_presets"
    preset_subdir = "blendmaxwell/material/metal"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Translucent_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Translucent Presets"
    bl_idname = "Translucent_presets"
    preset_subdir = "blendmaxwell/material/translucent"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Carpaint_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Car Paint Presets"
    bl_idname = "Carpaint_presets"
    preset_subdir = "blendmaxwell/material/carpaint"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Hair_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Hair Presets"
    bl_idname = "Hair_presets"
    preset_subdir = "blendmaxwell/material/hair"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Emitter_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Emitter Presets"
    bl_idname = "Emitter_presets"
    preset_subdir = "blendmaxwell/emitter"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class ExtEmitter_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Emitter Presets"
    bl_idname = "ExtEmitter_presets"
    preset_subdir = "blendmaxwell/material/emitter"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Exposure_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Exposure Presets"
    bl_idname = "Exposure_presets"
    preset_subdir = "blendmaxwell/exposure"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class Grass_Modifier_presets(Menu):
    COMPAT_ENGINES = {MaxwellRenderExportEngine.bl_idname}
    bl_label = "Grass Modifier Presets"
    bl_idname = "Grass_Modifier_presets"
    preset_subdir = "blendmaxwell/grass_modifier"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset
