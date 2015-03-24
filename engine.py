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
from bpy.types import RenderEngine

from .log import LOG_FILE_PATH
from . import progress
from . import app
from . import io


class MaxwellRenderExportEngine(RenderEngine):
    bl_idname = 'MAXWELL_RENDER'
    bl_label = 'Maxwell Render'
    bl_use_preview = True
    
    def render(self, scene):
        m = scene.maxwell_render
        bp = bpy.path.abspath(bpy.context.blend_data.filepath)
        if(bp == ""):
            self.report({'ERROR'}, "Save file first.")
            return
        
        cams = [o for o in scene.objects if o.type == 'CAMERA']
        if(len(cams) == 0):
            self.report({'ERROR'}, "No Camera found in scene.")
            return
        
        ed = bpy.path.abspath(m.export_output_directory)
        h, t = os.path.split(bp)
        n, e = os.path.splitext(t)
        p = os.path.join(ed, "{}.mxs".format(n))
        
        if(not m.export_overwrite and os.path.exists(p)):
            if(m.exporting_animation_now):
                m.exporting_animation_now = False
                m.exporting_animation_frame_number = 1
            self.report({'ERROR'}, "Scene file already exist in Output directory.")
            return
        
        s = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * s)
        self.size_y = int(scene.render.resolution_y * s)
        if(scene.name == 'preview'):
            pass
        else:
            self.render_scene(scene)
    
    def render_scene(self, scene):
        progress.set_default_progress_reporting(progress.PROGRESS_BAR)
        
        m = scene.maxwell_render
        bp = bpy.path.abspath(bpy.context.blend_data.filepath)
        
        ed = bpy.path.abspath(m.export_output_directory)
        h, t = os.path.split(bp)
        n, e = os.path.splitext(t)
        p = os.path.join(ed, "{}.mxs".format(n))
        
        if(m.exporting_animation_now):
            p = os.path.join(ed, "{0}_{1:06d}.mxs".format(n, m.exporting_animation_frame_number))
        
        if(m.output_image == "" and m.output_image_enabled):
            m.output_image = os.path.join(ed, "{}.png".format(n))
        if(m.output_mxi == "" and m.output_mxi_enabled):
            m.output_mxi = os.path.join(ed, "{}.mxi".format(n))
        
        ex = None
        if(m.export_wireframe):
            wire_mat = {'reflectance_0': [int(255 * v) for v in m.export_wire_mat_reflectance_0],
                        'reflectance_90': [int(255 * v) for v in m.export_wire_mat_reflectance_90],
                        'roughness': m.export_wire_mat_roughness,
                        'id': [int(255 * v) for v in m.export_wire_mat_color_id], }
            clay_mat = {'reflectance_0': [int(255 * v) for v in m.export_clay_mat_reflectance_0],
                        'reflectance_90': [int(255 * v) for v in m.export_clay_mat_reflectance_90],
                        'roughness': m.export_clay_mat_roughness,
                        'id': [int(255 * v) for v in m.export_clay_mat_color_id], }
            d = {'context': bpy.context,
                 'mxs_path': p,
                 'use_instances': m.export_use_instances,
                 'edge_radius': m.export_edge_radius,
                 'edge_resolution': m.export_edge_resolution,
                 'wire_mat': wire_mat,
                 'clay_mat': clay_mat,
                 'keep_intermediates': m.export_keep_intermediates, }
            ex = io.MXSExportWireframe(**d)
        else:
            d = {'context': bpy.context,
                 'mxs_path': p,
                 'use_instances': m.export_use_instances,
                 'keep_intermediates': m.export_keep_intermediates, }
            ex = io.MXSExport(**d)
        
        if((m.exporting_animation_now and scene.frame_current == scene.frame_end) or not m.exporting_animation_now):
            ls = []
            with open(LOG_FILE_PATH, 'r', encoding='utf-8', ) as f:
                ls = f.readlines()
            m.export_log = "".join(ls)
            if(m.export_log_open):
                import platform
                import subprocess
                import shlex
                pl = platform.system()
                if(pl == 'Darwin'):
                    os.system("open {}".format(shlex.quote(LOG_FILE_PATH)))
                elif(pl == 'Linux'):
                    subprocess.call(["xdg-open", shlex.quote(LOG_FILE_PATH)])
                elif(pl == 'Windows'):
                    os.system("start {}".format(shlex.quote(LOG_FILE_PATH)))
                else:
                    pass
        
        # open in..
        if(ex is not None and not m.exporting_animation_now):
            if(m.export_open_with == 'STUDIO'):
                app.open_mxs_in_studio(ex.mxs_path)
            if(m.export_open_with == 'MAXWELL'):
                app.open_mxs_in_maxwell(ex.mxs_path)
        
        # and make black rectangle as a render result
        c = self.size_x * self.size_y
        b = [[0.0, 0.0, 0.0, 1.0]] * c
        r = self.begin_result(0, 0, self.size_x, self.size_y)
        l = r.layers[0]
        l.rect = b
        self.end_result(r)
