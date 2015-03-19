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

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator
from mathutils import Vector

from . import app
from . import maths


class RenderExport(Operator):
    bl_idname = "maxwell_render.render_export"
    bl_label = "Render (Export)"
    bl_description = "Export scene as Maxwell Render (.MXS) file"
    
    def execute(self, context):
        scene = context.scene
        m = scene.maxwell_render
        
        m.exporting_animation_now = False
        
        bp = bpy.path.abspath(bpy.context.blend_data.filepath)
        if(bp == ""):
            self.report({'ERROR'}, "Save file first.")
            return {'CANCELLED'}
        
        cams = [o for o in scene.objects if o.type == 'CAMERA']
        if(len(cams) == 0):
            self.report({'ERROR'}, "No Camera found in scene.")
            return {'CANCELLED'}
        
        ed = bpy.path.abspath(m.export_output_directory)
        h, t = os.path.split(bp)
        n, e = os.path.splitext(t)
        p = os.path.join(ed, "{}.mxs".format(n))
        
        if(not m.export_overwrite and os.path.exists(p)):
            self.report({'ERROR'}, "Scene file already exist in Output directory.")
            return {'CANCELLED'}
        
        bpy.ops.render.render(animation=False, write_still=False, use_viewport=False, layer="", scene="", )
        return {'FINISHED'}


class AnimationExport(Operator):
    bl_idname = "maxwell_render.animation_export"
    bl_label = "Animation (Export)"
    bl_description = "Export animation frames as Maxwell Render (.MXS) files"
    
    def execute(self, context):
        scene = context.scene
        m = scene.maxwell_render
        bp = bpy.path.abspath(bpy.context.blend_data.filepath)
        if(bp == ""):
            self.report({'ERROR'}, "Save file first.")
            return {'CANCELLED'}
        
        cams = [o for o in scene.objects if o.type == 'CAMERA']
        if(len(cams) == 0):
            self.report({'ERROR'}, "No Camera found in scene.")
            return {'CANCELLED'}
        
        m.exporting_animation_now = True
        orig_frame = scene.frame_current
        scene_frames = range(scene.frame_start, scene.frame_end + 1)
        for frame in scene_frames:
            scene.frame_set(frame, 0.0)
            m.exporting_animation_frame_number = frame
            
            ed = bpy.path.abspath(m.export_output_directory)
            h, t = os.path.split(bp)
            n, e = os.path.splitext(t)
            p = os.path.join(ed, "{0}_{1:06d}.mxs".format(n, frame))
            
            if(not m.export_overwrite and os.path.exists(p)):
                m.exporting_animation_now = False
                m.exporting_animation_frame_number = 1
                self.report({'ERROR'}, "Scene file already exist in Output directory.")
                return {'CANCELLED'}
            
            bpy.ops.render.render(animation=False, write_still=False, use_viewport=False, layer="", scene="", )
        
        scene.frame_set(orig_frame, 0.0)
        m.exporting_animation_now = False
        m.exporting_animation_frame_number = 1
        
        return {'FINISHED'}


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
        app.create_mxm_in_mxed(bpy.path.abspath(self.filepath))
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
            app.open_mxm_in_mxed(bpy.path.abspath(context.object.maxwell_render.backface_material_file))
        else:
            app.open_mxm_in_mxed(bpy.path.abspath(context.material.maxwell_render.mxm_file))
        return {'FINISHED'}
