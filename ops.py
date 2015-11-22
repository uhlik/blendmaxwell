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
from bpy.props import PointerProperty, FloatProperty, IntProperty, BoolProperty, StringProperty, EnumProperty, FloatVectorProperty, IntVectorProperty
from bpy.types import Operator
from mathutils import Vector
from bl_operators.presets import AddPresetBase
from bpy_extras.io_utils import ImportHelper, ExportHelper

from . import maths
from . import system
from . import import_mxs
from . import export
from .log import LOG_FILE_PATH


class ImportMXS(Operator, ImportHelper):
    bl_idname = "maxwell_render.import_mxs"
    bl_label = 'Import MXS'
    bl_description = 'Import Maxwell Render Scene (.MXS)'
    
    filename_ext = ".mxs"
    filter_glob = StringProperty(default="*.mxs", options={'HIDDEN'}, )
    keep_intermediates = BoolProperty(name="Keep Intermediates", description="Keep intermediate products", default=False, )
    check_extension = True
    
    emitters = BoolProperty(name="Emitters", default=True, )
    objects = BoolProperty(name="Objects", default=True, )
    cameras = BoolProperty(name="Cameras", default=True, )
    sun = BoolProperty(name="Sun (as Sun Lamp)", default=True, )
    
    def draw(self, context):
        l = self.layout
        
        sub = l.column()
        r = sub.row()
        r.prop(self, 'emitters')
        if(self.objects):
            r.active = False
        sub.prop(self, 'objects')
        sub.prop(self, 'cameras')
        sub.prop(self, 'sun')
        
        if(system.PLATFORM == 'Darwin'):
            l.separator()
            l.prop(self, 'keep_intermediates')
    
    def execute(self, context):
        if(not self.objects and not self.cameras and not self.sun and not self.emitters):
            return {'CANCELLED'}
        
        d = {'mxs_path': os.path.realpath(bpy.path.abspath(self.filepath)),
             'emitters': self.emitters,
             'objects': self.objects,
             'cameras': self.cameras,
             'sun': self.sun, }
        if(system.PLATFORM == 'Darwin'):
            d['keep_intermediates'] = self.keep_intermediates
            im = import_mxs.MXSImportMacOSX(**d)
        elif(system.PLATFORM == 'Linux' or system.PLATFORM == 'Windows'):
            im = import_mxs.MXSImportWinLin(**d)
        else:
            pass
        
        return {'FINISHED'}
    
    @classmethod
    def register(cls):
        bpy.types.INFO_MT_file_import.append(menu_func_import)
    
    @classmethod
    def unregister(cls):
        bpy.types.INFO_MT_file_import.remove(menu_func_import)


class ExportMXS(Operator, ExportHelper):
    bl_idname = "maxwell_render.export_mxs"
    bl_label = 'Export MXS'
    bl_description = 'Export Maxwell Render Scene (.MXS)'
    
    filename_ext = ".mxs"
    filter_glob = StringProperty(default="*.mxs", options={'HIDDEN'}, )
    check_extension = True
    
    open_with = EnumProperty(name="Open With", items=[('STUDIO', "Studio", ""), ('MAXWELL', "Maxwell", ""), ('NONE', "None", "")], default='STUDIO', description="After export, open in ...", )
    open_log = BoolProperty(name="Open Log", default=False, description="Open export log in text editor when finished", )
    use_instances = BoolProperty(name="Instances", description="Export multi-user meshes and dupliverts as instances.", default=True, )
    keep_intermediates = BoolProperty(name="Keep Intermediates", description="Keep intermediate products", default=False, )
    
    def draw(self, context):
        l = self.layout
        
        sub = l.column()
        sub.prop(self, 'open_with')
        sub.prop(self, 'open_log')
        sub.prop(self, 'use_instances')
        
        if(system.PLATFORM == 'Darwin'):
            sub.separator()
            sub.prop(self, 'keep_intermediates')
    
    def execute(self, context):
        p = bpy.path.abspath(self.filepath)
        ex = export.MXSExport(mxs_path=p, )
        
        from .log import NUMBER_OF_WARNINGS, copy_paste_log
        if(NUMBER_OF_WARNINGS > 0):
            self.report({'ERROR'}, "There was {} warnings during export. Check log file for details.".format(NUMBER_OF_WARNINGS))
        if(self.open_log):
            h, t = os.path.split(p)
            n, e = os.path.splitext(t)
            u = ex.uuid
            log_file_path = os.path.join(h, '{}-export_log-{}.txt'.format(n, u))
            copy_paste_log(log_file_path)
            system.open_file_in_default_application(log_file_path)
        
        if(ex is not None):
            bpy.ops.maxwell_render.open_mxs(filepath=ex.mxs_path, application=self.open_with, instance_app=False, )
        
        return {'FINISHED'}
    
    @classmethod
    def register(cls):
        bpy.types.INFO_MT_file_export.append(menu_func_export)
    
    @classmethod
    def unregister(cls):
        bpy.types.INFO_MT_file_export.remove(menu_func_export)


def menu_func_import(self, context):
    self.layout.operator(ImportMXS.bl_idname, text="Maxwell Render Scene (.mxs)")


def menu_func_export(self, context):
    self.layout.operator(ExportMXS.bl_idname, text="Maxwell Render Scene (.mxs)")


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
    bl_description = "Create new .MXM and open it in Mxed material editor"
    
    filepath = StringProperty(subtype='FILE_PATH', )
    filename_ext = ".mxm"
    check_extension = True
    check_existing = BoolProperty(name="", default=True, options={'HIDDEN'}, )
    remove_dots = True
    
    filter_folder = BoolProperty(name="Filter folders", default=True, options={'HIDDEN'}, )
    filter_glob = StringProperty(default="*.mxm", options={'HIDDEN'}, )
    
    backface = BoolProperty(name="", default=False, options={'HIDDEN'}, )
    
    force_preview = BoolProperty(name="Force Preview", default=True, )
    force_preview_scene = StringProperty(name="Force Preview Scene", default="", )
    
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
        self.force_preview = context.material.maxwell_render.force_preview
        self.force_preview_scene = context.material.maxwell_render.force_preview_scene
        if(self.force_preview_scene == ' '):
            self.force_preview_scene = ''
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
        
        system.mxed_create_material_helper(p, self.force_preview, self.force_preview_scene, )
        
        rp = bpy.path.relpath(self.filepath)
        if(system.PLATFORM == 'Windows'):
            rp = os.path.abspath(self.filepath)
        
        if(self.backface):
            context.object.maxwell_render.backface_material_file = rp
        else:
            context.material.maxwell_render.mxm_file = rp
        return {'FINISHED'}


class BrowseMaterial(Operator):
    bl_idname = "maxwell_render.browse_material"
    bl_label = "Browse With Mxed"
    bl_description = "Open Mxed in browser mode to select material"
    
    @classmethod
    def poll(cls, context):
        return (context.material or context.object)
    
    def execute(self, context):
        p = system.mxed_browse_material_helper()
        m = context.material
        mx = m.maxwell_render
        
        if(p is not None):
            ok = False
            if(os.path.exists(p)):
                h, t = os.path.split(p)
                n, e = os.path.splitext(t)
                if(e.lower() == '.mxm'):
                    ok = True
                else:
                    self.report({'ERROR'}, "Not a .MXM file: '{}'".format(p))
            else:
                self.report({'ERROR'}, "File does not exist: '{}'".format(p))
            
            if(not ok):
                return {'CANCELLED'}
            
            mx.use = 'REFERENCE'
            
            rp = bpy.path.relpath(p)
            if(system.PLATFORM == 'Windows'):
                rp = os.path.abspath(p)
            
            mx.mxm_file = rp
            
            # change something to force preview redraw
            m.preview_render_type = 'FLAT'
            m.preview_render_type = 'SPHERE'
            
            return {'FINISHED'}
        else:
            return {'CANCELLED'}


class EditMaterial(Operator):
    bl_idname = "maxwell_render.edit_material"
    bl_label = "Edit Material"
    bl_description = "Edit current material in Mxed material editor"
    
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
        
        f = context.material.maxwell_render.force_preview
        fs = context.material.maxwell_render.force_preview_scene
        if(fs == ' '):
            fs = ''
        system.mxed_edit_material_helper(p, f, fs, )
        
        return {'FINISHED'}


class EditExtensionMaterial(Operator):
    bl_idname = "maxwell_render.edit_extension_material"
    bl_label = "Edit Extension Material in Mxed"
    bl_description = "Create new extension .MXM and open it in Mxed material editor"
    
    filepath = StringProperty(subtype='FILE_PATH', )
    filename_ext = ".mxm"
    check_extension = True
    check_existing = BoolProperty(name="", default=True, options={'HIDDEN'}, )
    remove_dots = True
    
    filter_folder = BoolProperty(name="Filter folders", default=True, options={'HIDDEN'}, )
    filter_glob = StringProperty(default="*.mxm", options={'HIDDEN'}, )
    
    backface = BoolProperty(name="", default=False, options={'HIDDEN'}, )
    
    force_preview = BoolProperty(name="Force Preview", default=True, )
    force_preview_scene = StringProperty(name="Force Preview Scene", default="", )
    
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
        self.force_preview = context.material.maxwell_render.force_preview
        self.force_preview_scene = context.material.maxwell_render.force_preview_scene
        if(self.force_preview_scene == ' '):
            force_preview_scene = ''
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
        
        mat = export.MXSMaterialExtension(context.material.name)
        d = mat._repr()
        
        path = system.mxed_create_and_edit_ext_material_helper(p, d, self.force_preview, self.force_preview_scene, )
        
        m = context.material.maxwell_render
        m.use = 'REFERENCE'
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


class CopyActiveObjectPropertiesToSelected(Operator):
    bl_idname = "maxwell_render.copy_active_object_properties_to_selected"
    bl_label = "Copy Active Object Properties To Selected"
    bl_description = "Copy active object properties from active object to selected."
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        allowed = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'LAMP', 'SPEAKER', ]
        if(ob.type not in allowed):
            return False
        obs = context.selected_objects
        return (ob and len(obs) > 0)
    
    def execute(self, context):
        allowed = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'LAMP', 'SPEAKER', ]
        obs = context.selected_objects
        src = context.active_object.maxwell_render
        for o in obs:
            if(o.type in allowed):
                m = o.maxwell_render
                m.opacity = src.opacity
                m.object_id = src.object_id
                m.backface_material = src.backface_material
                m.hidden_camera = src.hidden_camera
                m.hidden_camera_in_shadow_channel = src.hidden_camera_in_shadow_channel
                m.hidden_global_illumination = src.hidden_global_illumination
                m.hidden_reflections_refractions = src.hidden_reflections_refractions
                m.hidden_zclip_planes = src.hidden_zclip_planes
        
        return {'FINISHED'}


class SetObjectIdColor(Operator):
    bl_idname = "maxwell_render.set_object_id_color"
    bl_label = "Set Object ID Color"
    bl_description = "Set Object ID to red/green/blue/white/black to all selected objects."
    bl_options = {'REGISTER', 'UNDO'}
    
    color = EnumProperty(name="Color", items=[('0', "Red", ""), ('1', "Green", ""), ('2', "Blue", ""), ('3', "White", ""), ('4', "Black", "")], default='0', description="", )
    
    @classmethod
    def poll(cls, context):
        obs = context.selected_objects
        return (len(obs) > 0)
    
    def execute(self, context):
        allowed = ['MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY', 'LAMP', 'SPEAKER', ]
        obs = context.selected_objects
        src = context.active_object.maxwell_render
        for o in obs:
            if(o.type in allowed):
                m = o.maxwell_render
                if(self.color == '0'):
                    c = (1.0, 0.0, 0.0, )
                elif(self.color == '1'):
                    c = (0.0, 1.0, 0.0, )
                elif(self.color == '2'):
                    c = (0.0, 0.0, 1.0, )
                elif(self.color == '3'):
                    c = (1.0, 1.0, 1.0, )
                else:
                    c = (0.0, 0.0, 0.0, )
                m.object_id = c
        return {'FINISHED'}


class BlockedEmitterAdd(Operator):
    bl_idname = "maxwell_render.blocked_emitter_add"
    bl_label = "Blocked Emitter Add"
    bl_options = {'INTERNAL', 'UNDO'}
    
    name = StringProperty(name="Name", )
    remove = BoolProperty(name="Remove", )
    
    def execute(self, context):
        o = context.object
        be = o.maxwell_render.blocked_emitters
        es = be.emitters
        i = be.index
        if(self.remove):
            try:
                es.remove(i)
                if(i >= len(es)):
                    be.index = i - 1
            except Exception as e:
                self.report(type={'WARNING'}, message=str(e), )
        else:
            i = len(es)
            e = es.add()
            e.name = self.name
            be.index = i
        return {'FINISHED'}


class MaterialEditorAddLayer(Operator):
    bl_idname = "maxwell_render.material_editor_add_layer"
    bl_label = "Add New Layer"
    bl_description = "Add new layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        cl = mx.custom_layers
        ls = cl.layers
        idx = cl.index
        
        item = ls.add()
        item.id = len(ls)
        item.name = 'Layer {}'.format(len(ls))
        cl.index = (len(ls) - 1)
        b = item.layer.bsdfs.bsdfs.add()
        b.id = len(ls)
        b.name = 'BSDF'
        item.layer.bsdfs.index = 0
        
        return {'FINISHED'}


class MaterialEditorRemoveLayer(Operator):
    bl_idname = "maxwell_render.material_editor_remove_layer"
    bl_label = "Remove Selected Layer"
    bl_description = "Remove selected layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        cl = mx.custom_layers
        ls = cl.layers
        idx = cl.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        cl.index -= 1
        ls.remove(idx)
        if(idx == 0):
            cl.index = idx
        if(len(ls) == 0):
            cl.index = -1
        
        return {'FINISHED'}


class MaterialEditorMoveLayerUp(Operator):
    bl_idname = "maxwell_render.material_editor_move_layer_up"
    bl_label = "Move Selected Layer Up"
    bl_description = "Move selected layer up"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        cl = mx.custom_layers
        ls = cl.layers
        idx = cl.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        if(idx >= 1):
            mv = idx - 1
            ls.move(mv, idx, )
            cl.index = mv
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}


class MaterialEditorMoveLayerDown(Operator):
    bl_idname = "maxwell_render.material_editor_move_layer_down"
    bl_label = "Move Selected Layer Down"
    bl_description = "Move selected layer down"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        cl = mx.custom_layers
        ls = cl.layers
        idx = cl.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        if(idx < len(ls) - 1):
            mv = idx + 1
            ls.move(idx, mv, )
            cl.index = mv
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}


class MaterialEditorCloneLayer(Operator):
    bl_idname = "maxwell_render.material_editor_clone_layer"
    bl_label = "Clone Selected Layer"
    bl_description = "Clone selected layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        cl = mx.custom_layers
        ls = cl.layers
        idx = cl.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        d = cl['layers'][cl.index].to_dict()
        bpy.ops.maxwell_render.material_editor_add_layer()
        cl['layers'][cl.index].update(d)
        n = cl['layers'][cl.index]['name']
        cl['layers'][cl.index]['name'] = 'Clone of {}'.format(n)
        
        return {'FINISHED'}


class MaterialEditorAddBSDF(Operator):
    bl_idname = "maxwell_render.material_editor_add_bsdf"
    bl_label = "Add New BSDF"
    bl_description = "Add new BSDF"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        l = mx.custom_layers.layers[mx.custom_layers.index]
        cl = l.layer.bsdfs
        ls = l.layer.bsdfs.bsdfs
        idx = l.layer.bsdfs.index
        
        item = ls.add()
        item.id = len(ls)
        item.name = 'BSDF'
        cl.index = (len(ls) - 1)
        
        return {'FINISHED'}


class MaterialEditorRemoveBSDF(Operator):
    bl_idname = "maxwell_render.material_editor_remove_bsdf"
    bl_label = "Remove Selected BSDF"
    bl_description = "Remove selected BSDF"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        l = mx.custom_layers.layers[mx.custom_layers.index]
        cl = l.layer.bsdfs
        ls = l.layer.bsdfs.bsdfs
        idx = l.layer.bsdfs.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        cl.index -= 1
        ls.remove(idx)
        if(idx == 0):
            cl.index = idx
        if(len(ls) == 0):
            cl.index = -1
        
        return {'FINISHED'}


class MaterialEditorMoveBSDFUp(Operator):
    bl_idname = "maxwell_render.material_editor_move_bsdf_up"
    bl_label = "Move Selected BSDF Up"
    bl_description = "Move selected BSDF up"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        l = mx.custom_layers.layers[mx.custom_layers.index]
        cl = l.layer.bsdfs
        ls = l.layer.bsdfs.bsdfs
        idx = l.layer.bsdfs.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        if(idx >= 1):
            mv = idx - 1
            ls.move(mv, idx, )
            cl.index = mv
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}


class MaterialEditorMoveBSDFDown(Operator):
    bl_idname = "maxwell_render.material_editor_move_bsdf_down"
    bl_label = "Move Selected BSDF Down"
    bl_description = "Move selected BSDF down"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        l = mx.custom_layers.layers[mx.custom_layers.index]
        cl = l.layer.bsdfs
        ls = l.layer.bsdfs.bsdfs
        idx = l.layer.bsdfs.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        if(idx < len(ls) - 1):
            mv = idx + 1
            ls.move(idx, mv, )
            cl.index = mv
            return {'FINISHED'}
        
        return {'PASS_THROUGH'}


class MaterialEditorCloneBSDF(Operator):
    bl_idname = "maxwell_render.material_editor_clone_bsdf"
    bl_label = "Clone Selected BSDF"
    bl_description = "Clone selected BSDF"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mx = context.material.maxwell_render
        l = mx.custom_layers.layers[mx.custom_layers.index]
        cl = l.layer.bsdfs
        ls = l.layer.bsdfs.bsdfs
        idx = l.layer.bsdfs.index
        try:
            item = ls[idx]
        except IndexError:
            return {'CANCELLED'}
        
        d = l.layer.bsdfs['bsdfs'][l.layer.bsdfs.index].to_dict()
        bpy.ops.maxwell_render.material_editor_add_bsdf()
        l.layer.bsdfs['bsdfs'][l.layer.bsdfs.index].update(d)
        n = l.layer.bsdfs['bsdfs'][l.layer.bsdfs.index]['name']
        l.layer.bsdfs['bsdfs'][l.layer.bsdfs.index]['name'] = 'Clone of {}'.format(n)
        
        return {'FINISHED'}


class SaveMaterialAsMXM(Operator):
    bl_idname = "maxwell_render.save_material_as_mxm"
    bl_label = "Save Material As MXM"
    bl_description = "Save material as .MXM and open it in Mxed material editor"
    
    filepath = StringProperty(subtype='FILE_PATH', )
    filename_ext = ".mxm"
    check_extension = True
    check_existing = BoolProperty(name="", default=True, options={'HIDDEN'}, )
    remove_dots = True
    
    filter_folder = BoolProperty(name="Filter folders", default=True, options={'HIDDEN'}, )
    filter_glob = StringProperty(default="*.mxm", options={'HIDDEN'}, )
    
    force_preview = BoolProperty(name="Force Preview", default=True, )
    force_preview_scene = StringProperty(name="Force Preview Scene", default="", )
    open_in_mxed = BoolProperty(name="Open In Mxed", default=True, )
    
    @classmethod
    def poll(cls, context):
        return (context.material or context.object)
    
    def draw(self, context):
        l = self.layout
        l.prop(self, 'open_in_mxed')
        l.prop(self, 'force_preview')
    
    def invoke(self, context, event):
        n = context.material.name
        if(self.remove_dots):
            # remove dots, Maxwell doesn't like it - material name is messed up..
            n = n.replace(".", "_")
        self.filepath = os.path.join(context.scene.maxwell_render.materials_directory, "{}.mxm".format(n))
        self.force_preview = context.material.maxwell_render.force_preview
        self.force_preview_scene = context.material.maxwell_render.force_preview_scene
        self.open_in_mxed = context.material.maxwell_render.custom_open_in_mxed_after_save
        if(self.force_preview_scene == ' '):
            self.force_preview_scene = ''
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
        
        mat = export.MXSMaterialCustom(context.material.name)
        d = mat._repr()
        
        system.mxed_create_and_edit_custom_material_helper(p, d, self.force_preview, self.force_preview_scene, self.open_in_mxed, )
        
        rp = bpy.path.relpath(self.filepath)
        if(system.PLATFORM == 'Windows'):
            rp = os.path.abspath(self.filepath)
        
        context.material.maxwell_render.use = 'REFERENCE'
        context.material.maxwell_render.mxm_file = rp
        
        return {'FINISHED'}


class LoadMaterialFromMXM(Operator, ImportHelper):
    bl_idname = "maxwell_render.load_material_from_mxm"
    # bl_label = "Load Material From MXM"
    bl_label = "Load Material From MXM (not implemented yet)"
    bl_description = "Load material from existing .MXM"
    
    filename_ext = ".mxm"
    check_extension = True
    filepath = StringProperty(subtype='FILE_PATH', )
    filter_folder = BoolProperty(name="Filter folders", default=True, options={'HIDDEN'}, )
    filter_glob = StringProperty(default="*.mxm", options={'HIDDEN'}, )
    
    @classmethod
    def poll(cls, context):
        # TODO: finish material import
        return False
        
        return (context.material or context.object)
    
    def draw(self, context):
        l = self.layout
    
    def execute(self, context):
        d = {'mxm_path': os.path.realpath(bpy.path.abspath(self.filepath)), }
        if(system.PLATFORM == 'Darwin'):
            im = import_mxs.MXMImportMacOSX(**d)
        elif(system.PLATFORM == 'Linux' or system.PLATFORM == 'Windows'):
            im = import_mxs.MXMImportWinLin(**d)
        else:
            pass
        
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
