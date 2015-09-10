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
import time
import datetime

import bpy
from bpy.types import RenderEngine

import numpy

from .log import log, LogStyles, LOG_FILE_PATH, copy_paste_log
from . import export
from . import ops
from . import system
from . import mxs


class MaxwellRenderExportEngine(RenderEngine):
    bl_idname = 'MAXWELL_RENDER'
    bl_label = 'Maxwell Render'
    bl_use_preview = True
    
    _t = None
    
    def render(self, scene):
        if(self.is_preview):
            self.material_preview(scene)
            return
        
        self._t = time.time()
        
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
        
        _d = datetime.timedelta(seconds=time.time() - self._t)
        log("export completed in {0}".format(_d), 1, LogStyles.MESSAGE)
    
    def material_preview(self, scene):
        def get_material(scene):
            objects_materials = {}
            
            def get_instance_materials(ob):
                obmats = []
                # Grab materials attached to object instances ...
                if hasattr(ob, 'material_slots'):
                    for ms in ob.material_slots:
                        obmats.append(ms.material)
                # ... and to the object's mesh data
                if hasattr(ob.data, 'materials'):
                    for m in ob.data.materials:
                        obmats.append(m)
                return obmats
            
            for object in [ob for ob in scene.objects if ob.is_visible(scene) and not ob.hide_render]:
                for mat in get_instance_materials(object):
                    if mat is not None:
                        if object.name not in objects_materials.keys():
                            objects_materials[object] = []
                        objects_materials[object].append(mat)
            # Find objects that are likely to be the preview objects.
            preview_objects = [o for o in objects_materials.keys() if o.name.startswith('preview')]
            if len(preview_objects) < 1:
                return
            # Find the materials attached to the likely preview object.
            likely_materials = objects_materials[preview_objects[0]]
            if len(likely_materials) < 1:
                return None
            return likely_materials
        
        likely_materials = get_material(scene)
        
        def fill_black():
            xr = int(scene.render.resolution_x * scene.render.resolution_percentage / 100.0)
            yr = int(scene.render.resolution_y * scene.render.resolution_percentage / 100.0)
            c = xr * yr
            b = [[0.0, 0.0, 0.0, 1.0]] * c
            r = self.begin_result(0, 0, xr, yr)
            l = r.layers[0] if bpy.app.version < (2, 74, 4) else r.layers[0].passes[0]
            l.rect = b
            self.end_result(r)
        
        if(likely_materials is not None):
            mat = likely_materials[0]
            m = mat.maxwell_render
            
            if(bpy.context.scene.maxwell_render_private.material != mat.name):
                bpy.context.scene.maxwell_render_private.material = mat.name
            else:
                if(not m.flag):
                    fill_black()
                    return
            
            w = int(scene.render.resolution_x * scene.render.resolution_percentage / 100.0)
            h = int(scene.render.resolution_y * scene.render.resolution_percentage / 100.0)
            if(w, h) == (32, 32):
                # skip icon rendering
                fill_black()
                return
            
            bpy.data.materials[mat.name].maxwell_render.flag = False
            
            p = m.mxm_file
            if(p is not ''):
                p = os.path.realpath(bpy.path.abspath(p))
                a = None
                
                if(system.PLATFORM == 'Darwin'):
                    system.python34_run_mxm_preview(p)
                    d = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", )
                    f = os.path.split(p)[1]
                    npy = os.path.join(d, "{}.npy".format(f))
                    if(os.path.exists(npy)):
                        a = numpy.load(npy)
                    # cleanup
                    if(os.path.exists(npy)):
                        os.remove(npy)
                else:
                    a = mxs.read_mxm_preview(p)
                
                if(a is not None):
                    w, h, _ = a.shape
                    
                    # flip
                    a = numpy.flipud(a)
                    
                    # gamma correct
                    a.astype(float)
                    g = 2.2
                    a = (a[:] / 255) ** g
                    a = numpy.reshape(a, (w * h, 3))
                    z = numpy.empty((w * h, 1))
                    z.fill(1.0)
                    a = numpy.append(a, z, axis=1, )
                    
                    # draw
                    xr = int(scene.render.resolution_x * scene.render.resolution_percentage / 100.0)
                    yr = int(scene.render.resolution_y * scene.render.resolution_percentage / 100.0)
                    x = int((xr - w) / 2)
                    y = int((yr - h) / 2)
                    
                    r = self.begin_result(x, y, w, h)
                    l = r.layers[0] if bpy.app.version < (2, 74, 4) else r.layers[0].passes[0]
                    l.rect = a.tolist()
                    self.end_result(r)
                else:
                    xr = int(scene.render.resolution_x * scene.render.resolution_percentage / 100.0)
                    yr = int(scene.render.resolution_y * scene.render.resolution_percentage / 100.0)
                    c = xr * yr
                    b = [[0.0, 0.0, 0.0, 1.0]] * c
                    r = self.begin_result(0, 0, xr, yr)
                    l = r.layers[0] if bpy.app.version < (2, 74, 4) else r.layers[0].passes[0]
                    l.rect = b
                    self.end_result(r)
            else:
                fill_black()
    
    def render_scene(self, scene):
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
        
        log_file_path = None
        ex = None
        """
        if(m.export_wireframe):
            raise Exception("Wire export disabled at this time..")
            
            wire_mat = {'reflectance_0': [int(255 * v) for v in m.export_wire_mat_reflectance_0],
                        'reflectance_90': [int(255 * v) for v in m.export_wire_mat_reflectance_90],
                        'roughness': m.export_wire_mat_roughness,
                        'id': [int(255 * v) for v in m.export_wire_mat_color_id], }
            clay_mat = {'reflectance_0': [int(255 * v) for v in m.export_clay_mat_reflectance_0],
                        'reflectance_90': [int(255 * v) for v in m.export_clay_mat_reflectance_90],
                        'roughness': m.export_clay_mat_roughness,
                        'id': [int(255 * v) for v in m.export_clay_mat_color_id], }
            if(system.PLATFORM == 'Darwin'):
                d = {'context': bpy.context,
                     'mxs_path': p,
                     'use_instances': m.export_use_instances,
                     'edge_radius': m.export_edge_radius,
                     'edge_resolution': m.export_edge_resolution,
                     'wire_mat': wire_mat,
                     'clay_mat': clay_mat,
                     'keep_intermediates': m.export_keep_intermediates, }
                ex = export.MXSExportWireframeLegacy(**d)
            elif(system.PLATFORM == 'Linux'):
                ex = export.MXSExportWireframe(bpy.context, p, m.export_use_instances, m.export_edge_radius, m.export_edge_resolution, wire_mat, clay_mat, )
            elif(system.PLATFORM == 'Windows'):
                ex = export.MXSExportWireframe(bpy.context, p, m.export_use_instances, m.export_edge_radius, m.export_edge_resolution, wire_mat, clay_mat, )
            else:
                pass
        else:
            '''
            if(system.PLATFORM == 'Darwin'):
                d = {'context': bpy.context,
                     'mxs_path': p,
                     'use_instances': m.export_use_instances,
                     'keep_intermediates': m.export_keep_intermediates, }
                
                # import cProfile, pstats, io
                # pr = cProfile.Profile()
                # pr.enable()
                
                ex = export.MXSExportLegacy(**d)
                
                # pr.disable()
                # s = io.StringIO()
                # sortby = 'cumulative'
                # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
                # ps.print_stats()
                # print(s.getvalue())
                
            elif(system.PLATFORM == 'Linux'):
                ex = export.MXSExport(bpy.context, p, m.export_use_instances, )
            elif(system.PLATFORM == 'Windows'):
                ex = export.MXSExport(bpy.context, p, m.export_use_instances, )
            else:
                pass
            '''
            
            # import cProfile, pstats, io
            # pr = cProfile.Profile()
            # pr.enable()
            
            ex = export.MXSExport(mxs_path=p, )
            
            from .log import NUMBER_OF_WARNINGS
            if(NUMBER_OF_WARNINGS > 0):
                self.report({'ERROR'}, "There was {} warnings during export. Check log file for details.".format(NUMBER_OF_WARNINGS))
                
                if(m.export_warning_log_write):
                    h, t = os.path.split(p)
                    n, e = os.path.splitext(t)
                    u = ex.uuid
                    log_file_path = os.path.join(h, '{}-export_log-{}.txt'.format(n, u))
                    copy_paste_log(log_file_path)
            
            # pr.disable()
            # s = io.StringIO()
            # sortby = 'cumulative'
            # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            # ps.print_stats()
            # print(s.getvalue())
        """
        
        # import cProfile, pstats, io
        # pr = cProfile.Profile()
        # pr.enable()
        
        ex = export.MXSExport(mxs_path=p, )
        
        from .log import NUMBER_OF_WARNINGS
        if(NUMBER_OF_WARNINGS > 0):
            self.report({'ERROR'}, "There was {} warnings during export. Check log file for details.".format(NUMBER_OF_WARNINGS))
            
            if(m.export_warning_log_write):
                h, t = os.path.split(p)
                n, e = os.path.splitext(t)
                u = ex.uuid
                log_file_path = os.path.join(h, '{}-export_log-{}.txt'.format(n, u))
                copy_paste_log(log_file_path)
        
        # pr.disable()
        # s = io.StringIO()
        # sortby = 'cumulative'
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()
        # print(s.getvalue())
        
        if((m.exporting_animation_now and scene.frame_current == scene.frame_end) or not m.exporting_animation_now):
            if(m.export_log_open):
                if(log_file_path is not None):
                    # open local, it gets written only when some warnigns are encountered
                    system.open_file_in_default_application(log_file_path)
                else:
                    # else open global log file from inside addon files
                    system.open_file_in_default_application(LOG_FILE_PATH)
        
        # open in..
        if(ex is not None and not m.exporting_animation_now):
            bpy.ops.maxwell_render.open_mxs(filepath=ex.mxs_path, application=m.export_open_with, instance_app=m.instance_app, )
        
        # # and make black rectangle as a render result
        # c = self.size_x * self.size_y
        # b = [[0.0, 0.0, 0.0, 1.0]] * c
        # r = self.begin_result(0, 0, self.size_x, self.size_y)
        # l = r.layers[0]
        # l.rect = b
        # self.end_result(r)
        
        # # leave it as it is
        # r = self.begin_result(0, 0, self.size_x, self.size_y)
        # self.end_result(r)
        
        # ehm, skip it completelly
    
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
