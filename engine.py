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
import re

import bpy
from bpy.types import RenderEngine

from .log import log, LOG_FILE_PATH
from . import progress
from . import export
from . import ops


class MaxwellRenderExportEngine(RenderEngine):
    bl_idname = 'MAXWELL_RENDER'
    bl_label = 'Maxwell Render'
    bl_use_preview = True
    
    def render(self, scene):
        m = scene.maxwell_render
        
        bp = bpy.path.abspath(bpy.context.blend_data.filepath)
        # check if file is saved, if not raise error
        if(bp == ""):
            self.report({'ERROR'}, "Save file first.")
            return
        
        # other checks, like for camera (if not present, blender will raise error anyway)
        cams = [o for o in scene.objects if o.type == 'CAMERA']
        if(len(cams) == 0):
            self.report({'ERROR'}, "No Camera found in scene.")
            return
        
        ed = bpy.path.abspath(m.export_output_directory)
        # check if directory exists else error
        if(not os.path.exists(ed)):
            self.report({'ERROR'}, "Export directory does not exist.")
            return
        # check if directory if writeable else error
        if(not os.access(ed, os.W_OK)):
            self.report({'ERROR'}, "Export directory is not writeable.")
            return
        
        # set some workflow stuff..
        if(self.is_animation):
            m.exporting_animation_now = True
        else:
            m.exporting_animation_now = False
        if(scene.frame_start == scene.frame_current):
            m.exporting_animation_first_frame = True
        else:
            m.exporting_animation_first_frame = False
        m.private_image = m.output_image
        m.private_mxi = m.output_mxi
        m.exporting_animation_frame_number = scene.frame_current
        
        h, t = os.path.split(bp)
        n, e = os.path.splitext(t)
        if(m.exporting_animation_now and not m.exporting_animation_first_frame):
            mxs_name = m.private_name
            mxs_increment = m.private_increment
            mxs_suffix = m.private_suffix
        else:
            mxs_name = n
            mxs_increment = ""
            mxs_suffix = ""
        
        def walk_dir(p):
            """gets directory contents in format: {files:[...], dirs:[...]}"""
            r = {'files': [], 'dirs': [], }
            for (root, dirs, files) in os.walk(p):
                r['files'].extend(files)
                r['dirs'].extend(dirs)
                break
            return r
        
        if(m.exporting_animation_now):
            mxs_suffix = '_{:06d}'.format(m.exporting_animation_frame_number)
            if(m.export_incremental):
                # add or increment mxs number
                if(m.exporting_animation_first_frame):
                    # do this just once for a first frame
                    m.exporting_animation_first_frame = False
                    
                    dc = walk_dir(ed)
                    # get files from destination and filter all files starting with mxs_name and with .mxs extension
                    older = [f for f in dc['files'] if(f.startswith(mxs_name) and f.endswith(".mxs"))]
                    nn = 0
                    if(len(older) > 0):
                        older.sort()
                        pat = re.compile(str('^{0}.\d\d\d_\d\d\d\d\d\d.mxs$'.format(mxs_name)))
                        for ofn in older:
                            if(re.search(pat, ofn)):
                                # get increment number from each, if there is some of course
                                num = int(ofn[len(mxs_name) + 1:-len("_000000.mxs")])
                                if(nn < num):
                                    nn = num
                        nn += 1
                    if(nn != 0):
                        # there were some already incremented files, lets make nes increment from highest
                        mxs_increment = '.{:0>3}'.format(nn)
            elif(m.export_overwrite):
                # overwrite, no error reporting, no path changing
                pass
            else:
                # check and raise error if mxs exists, if not continue
                p = os.path.join(ed, "{}{}{}.mxs".format(mxs_name, mxs_increment, mxs_suffix))
                if(os.path.exists(p) and not m.export_overwrite):
                    # # reset animation flags
                    # m.exporting_animation_now = False
                    # m.exporting_animation_frame_number = 1
                    # m.exporting_animation_first_frame = True
                    self.reset_workflow(scene)
                    self.report({'ERROR'}, "Scene file already exist in Output directory.")
                    return
        else:
            if(m.export_incremental):
                # add or increment mxs number
                dc = walk_dir(ed)
                # get files from destination and filter all files starting with mxs_name and with .mxs extension
                older = [f for f in dc['files'] if(f.startswith(mxs_name) and f.endswith(".mxs"))]
                nn = 0
                if(len(older) > 0):
                    older.sort()
                    pat = re.compile(str('^{0}.\d\d\d.mxs$'.format(mxs_name)))
                    for ofn in older:
                        if(re.search(pat, ofn)):
                            # get increment number from each, if there is some of course
                            num = int(ofn[len(mxs_name) + 1:-len(".mxs")])
                            if(nn < num):
                                nn = num
                    nn += 1
                if(nn != 0):
                    # there were some already incremented files, lets make nes increment from highest
                    mxs_increment = '.{:0>3}'.format(nn)
            elif(m.export_overwrite):
                # overwrite, no error reporting, no path changing
                pass
            else:
                # check and raise error if mxs exists, if not continue
                p = os.path.join(ed, "{}{}{}.mxs".format(mxs_name, mxs_increment, mxs_suffix))
                if(os.path.exists(p) and not m.export_overwrite):
                    self.reset_workflow(scene)
                    self.report({'ERROR'}, "Scene file already exist in Output directory.")
                    return
        
        # store it to use it render_scene (is this needed? it was in example.. i can do whole work here)
        # but the problem is, when exporting animation, this is called for each frame, so i got to store these props
        # maybe.. maybe not
        m.private_name = mxs_name
        m.private_increment = mxs_increment
        m.private_suffix = mxs_suffix
        m.private_path = os.path.join(ed, "{}{}{}.mxs".format(mxs_name, mxs_increment, mxs_suffix))
        m.private_basepath = os.path.join(ed, "{}{}.mxs".format(mxs_name, mxs_increment))
        
        try:
            s = scene.render.resolution_percentage / 100.0
            self.size_x = int(scene.render.resolution_x * s)
            self.size_y = int(scene.render.resolution_y * s)
            if(scene.name == 'preview'):
                pass
            else:
                self.render_scene(scene)
                m.output_image = m.private_image
                m.output_mxi = m.private_mxi
        except Exception as ex:
            import traceback
            m = traceback.format_exc()
            log(m)
            
            # import sys
            # import traceback
            # exc_type, exc_value, exc_traceback = sys.exc_info()
            # lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            # log("".join(lines))
            
            # self.report({'ERROR'}, '{}'.format(ex))
            self.reset_workflow(scene)
            self.report({'ERROR'}, m)
    
    def render_scene(self, scene):
        progress.set_default_progress_reporting(progress.PROGRESS_BAR)
        
        m = scene.maxwell_render
        p = m.private_path
        bp = m.private_basepath
        
        # write default one if not set, do not care if enabled, this is more usable when i change my mind later
        h, t = os.path.split(bp)
        n, e = os.path.splitext(t)
        if(m.output_image == ""):
            m.output_image = os.path.join(h, "{}.png".format(n))
            m.private_image = m.output_image
        if(m.output_mxi == ""):
            m.output_mxi = os.path.join(h, "{}.mxi".format(n))
            m.private_mxi = m.output_mxi
        
        def remove_increment(path):
            h, t = os.path.split(bpy.path.abspath(path))
            n, e = os.path.splitext(t)
            pat = re.compile(str('.\d\d\d{}$'.format(e)))
            if(re.search(pat, t)):
                n = t[:-len(".000{}".format(e))]
            return h, n, e
        
        if(m.export_incremental):
            # increment also both image files, and also do not care if enabled
            if(m.private_increment != ""):
                h, n, e = remove_increment(m.output_image)
                m.output_image = os.path.join(h, "{}{}{}".format(n, m.private_increment, e))
                h, n, e = remove_increment(m.output_mxi)
                m.output_mxi = os.path.join(h, "{}{}{}".format(n, m.private_increment, e))
        
        if(m.output_image_enabled):
            # if exporting animation add correct frame number
            if(m.exporting_animation_now):
                # frame number from image paths will be removed after export is finished in animation operator
                h, t = os.path.split(bpy.path.abspath(m.output_image))
                n, e = os.path.splitext(t)
                m.output_image = os.path.join(h, "{}{}{}".format(n, m.private_suffix, e))
        
        if(m.output_mxi_enabled):
            # if exporting animation add correct frame number
            if(m.exporting_animation_now):
                # frame number from image paths will be removed after export is finished in animation operator
                h, t = os.path.split(bpy.path.abspath(m.output_mxi))
                n, e = os.path.splitext(t)
                m.output_mxi = os.path.join(h, "{}{}{}".format(n, m.private_suffix, e))
        
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
            ex = export.MXSExportWireframe(**d)
        else:
            d = {'context': bpy.context,
                 'mxs_path': p,
                 'use_instances': m.export_use_instances,
                 'keep_intermediates': m.export_keep_intermediates, }
            ex = export.MXSExport(**d)
        
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
            bpy.ops.maxwell_render.open_mxs(filepath=ex.mxs_path, application=m.export_open_with, instance_app=m.instance_app, )
        
        # and make black rectangle as a render result
        c = self.size_x * self.size_y
        b = [[0.0, 0.0, 0.0, 1.0]] * c
        r = self.begin_result(0, 0, self.size_x, self.size_y)
        l = r.layers[0]
        l.rect = b
        self.end_result(r)
    
    def reset_workflow(self, scene):
        m = scene.maxwell_render
        m.exporting_animation_now = False
        m.exporting_animation_frame_number = 1
        m.exporting_animation_first_frame = True
        m.private_name = ""
        m.private_increment = ""
        m.private_suffix = ""
        m.private_path = ""
        m.private_basepath = ""
        m.private_image = ""
        m.private_mxi = ""
