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
import shlex
import subprocess
import platform
import uuid
import shutil
import struct
import json
import sys

import bpy
from mathutils import Matrix, Vector
from bpy_extras import io_utils
import bmesh

from .log import log, LogStyles, LOG_FILE_PATH
from . import progress
from . import utils
from . import maths
from . import rfbin


def prefs():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    return p


class MXSExport():
    """Maxwell Render (.mxs) scene export
    Docs:
    """
    def __init__(self, context, mxs_path, use_instances=True, keep_intermediates=False, ):
        """
        context: bpy.context
        mxs_path: path where .mxs should be saved
        use_instances: if True all multi user meshes and duplis are exported as instances
        keep_intermediates: if True, temp files and directory will not be removed
        """
        s = platform.system()
        if(s == 'Darwin'):
            self.PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'bin', 'python3.4', ))
            self.PYMAXWELL_SO = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'lib', 'python3.4', 'site-packages', '_pymaxwell.so', ))
            self.PYMAXWELL_PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'lib', 'python3.4', 'site-packages', 'pymaxwell.py', ))
        elif(s == 'Linux'):
            # import site
            # site.getsitepackages()
            self.PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'python3.4', ))
            self.PYMAXWELL_SO = os.path.join('/usr/local/lib/python3.4/site-packages', '_pymaxwell.so', )
            self.PYMAXWELL_PY = os.path.join('/usr/local/lib/python3.4/site-packages', 'pymaxwell.py', )
        elif(s == 'Windows'):
            pass
        else:
            raise OSError("Unknown platform: {}.".format(s))
        
        # export template
        self.TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "export_mxs.py")
        
        # lets check for it
        ok = (os.path.exists(self.PY) and os.path.exists(self.PYMAXWELL_SO) and os.path.exists(self.PYMAXWELL_PY) and os.path.exists(self.TEMPLATE))
        if(not ok):
            log("{}: ERROR: python 3.4 with pymaxwell seems not to be installed, or support directory is missing..".format(self.__class__.__name__), 1, LogStyles.ERROR, )
            return
        
        self.context = context
        self.mxs_path = os.path.realpath(mxs_path)
        self.use_instances = use_instances
        self.keep_intermediates = keep_intermediates
        self._prepare()
        self._export()
    
    def _prepare(self):
        log("{0} {1} {0}".format("-" * 30, self.__class__.__name__), 0, LogStyles.MESSAGE, prefix="", )
        if(os.path.exists(self.mxs_path)):
            log("mxs file exists at {0}, will be overwritten..".format(self.mxs_path), 1, LogStyles.WARNING, )
    
    def _export(self):
        log("collecting objects..", 1)
        self.tree = self._collect()
        
        self.uuid = uuid.uuid1()
        h, t = os.path.split(self.mxs_path)
        n, e = os.path.splitext(t)
        self.tmp_dir = os.path.join(h, "{0}-tmp-{1}".format(n, self.uuid))
        if(os.path.exists(self.tmp_dir) is False):
            os.makedirs(self.tmp_dir)
        
        self.mesh_data_paths = []
        self.hair_data_paths = []
        self.scene_data_name = "{0}-{1}.json".format(n, self.uuid)
        self.script_name = "{0}-{1}.py".format(n, self.uuid)
        
        # coordinate conversion matrix
        # m = io_utils.axis_conversion(from_forward='Y', to_forward='-Z', from_up='Z', to_up='Y').to_4x4()
        # print(repr(m))
        self.matrix = Matrix(((1.0, 0.0, 0.0, 0.0),
                              (0.0, 0.0, 1.0, 0.0),
                              (0.0, -1.0, 0.0, 0.0),
                              (0.0, 0.0, 0.0, 1.0)))
        
        # process scene data
        self.data = []
        self._export_data()
        self._scene_properties()
        
        log("writing serialized scene data..", 1, LogStyles.MESSAGE)
        p = self._serialize(self.data, self.scene_data_name)
        self.scene_data_path = p
        
        # generate and execute py32 script
        log("executing script..", 1, LogStyles.MESSAGE)
        self._pymaxwell()
        
        # remove all generated files
        log("cleanup..", 1, LogStyles.MESSAGE)
        self._cleanup()
        
        log("mxs saved in:", 1)
        log("{0}".format(self.mxs_path), 0, LogStyles.MESSAGE, prefix="")
        log("done.", 1, LogStyles.MESSAGE)
    
    def _collect(self):
        """Collect scene objects.
        what it does (unordered):
            - Filter all scene objects and collect only objects needed for scene export. Meshes (and instances), empties, cameras and sun.
            - Remove all objects on hidden layers and with hide_render: True, substitute with an empty if needed for correct hierarchy.
            - Sort all objects by type, determine base meshes for instanced objects (if use_instances: True).
            - Try to convert non-mesh objects to mesh and if result is renderable, include them as well.
            - Covert dupli-objects to real meshes or instances.
        Return filtered scene hierarchy.
        """
        objs = self.context.scene.objects
        
        # sort objects
        def sort_objects():
            meshes = []
            empties = []
            cameras = []
            bases = []
            instances = []
            convertibles = []
            others = []
            
            might_be_renderable = ['CURVE', 'SURFACE', 'FONT', ]
            for o in objs:
                if(o.type == 'MESH'):
                    if(self.use_instances):
                        if(o.data.users > 1):
                            instances.append(o)
                        else:
                            meshes.append(o)
                    else:
                        meshes.append(o)
                elif(o.type == 'EMPTY'):
                    empties.append(o)
                elif(o.type == 'CAMERA'):
                    cameras.append(o)
                elif(o.type in might_be_renderable):
                    convertibles.append(o)
                else:
                    others.append(o)
            instance_groups = {}
            for o in instances:
                if(o.data.name not in instance_groups):
                    instance_groups[o.data.name] = [o, ]
                else:
                    instance_groups[o.data.name].append(o)
            bases_names = []
            for n, g in instance_groups.items():
                nms = [o.name for o in g]
                ls = sorted(nms)
                bases_names.append(ls[0])
            insts = instances[:]
            instances = []
            for o in insts:
                if(o.name in bases_names):
                    bases.append(o)
                else:
                    instances.append(o)
            return {'meshes': meshes,
                    'empties': empties,
                    'cameras': cameras,
                    'bases': bases,
                    'instances': instances,
                    'convertibles': convertibles,
                    'others': others, }
        
        so = sort_objects()
        
        # visibility
        mx = self.context.scene.maxwell_render
        layers = self.context.scene.layers
        render_layers = self.context.scene.render.layers.active.layers
        
        def check_visibility(o):
            """Objects which are in visible layers and have hide_render: False are considered visible,
               objects which are only hidden from viewport are renderable, therefore visible."""
            # if(mx.render_use_layers == 'RENDER'):
            #     for i, l in enumerate(o.layers):
            #         if(render_layers[i] is True and l is True and o.hide_render is False):
            #             return True
            # else:
            #     for i, l in enumerate(o.layers):
            #         if(layers[i] is True and l is True and o.hide_render is False):
            #             return True
            
            if(o.hide_render is True):
                return False
            
            s = None
            r = None
            for i, l in enumerate(o.layers):
                if(layers[i] is True and l is True):
                    s = True
                    break
            for i, l in enumerate(o.layers):
                if(render_layers[i] is True and l is True):
                    r = True
                    break
            if(s and r):
                return True
            return False
        
        # export type
        might_be_renderable = ['CURVE', 'SURFACE', 'FONT', ]
        
        def export_type(o):
            """determine export type, if convertible, try convert to mesh and store result"""
            t = 'EMPTY'
            m = None
            c = False
            if(o.type == 'MESH'):
                m = o.data
                if(self.use_instances):
                    if(o.data.users > 1):
                        if(o in so['bases']):
                            t = 'BASE_INSTANCE'
                        else:
                            t = 'INSTANCE'
                    else:
                        if(len(o.data.polygons) > 0):
                            t = 'MESH'
                        else:
                            # case when object has no polygons, but with modifiers applied it will have..
                            me = o.to_mesh(self.context.scene, True, 'RENDER', )
                            if(len(me.polygons) > 0):
                                t = 'MESH'
                                # remove mesh, was created only for testing..
                                bpy.data.meshes.remove(me)
                        # else:
                        #     t = 'EMPTY'
                else:
                    if(len(o.data.polygons) > 0):
                        t = 'MESH'
                    else:
                        # case when object has no polygons, but with modifiers applied it will have..
                        me = o.to_mesh(self.context.scene, True, 'RENDER', )
                        if(len(me.polygons) > 0):
                            t = 'MESH'
                            # remove mesh, was created only for testing..
                            bpy.data.meshes.remove(me)
                    # else:
                    #     t = 'EMPTY'
            elif(o.type == 'EMPTY'):
                # t = 'EMPTY'
                pass
            elif(o.type == 'CAMERA'):
                t = 'CAMERA'
            elif(o.type in might_be_renderable):
                me = o.to_mesh(self.context.scene, True, 'RENDER', )
                if(me is not None):
                    if(len(me.polygons) > 0):
                        t = 'MESH'
                        m = me
                        c = True
                    # else:
                    #     t = 'EMPTY'
                # else:
                #     t = 'EMPTY'
            elif(o.type == 'LAMP'):
                if(o.data.type == 'SUN'):
                    t = 'SUN'
            # else:
            #     t = 'EMPTY'
            return t, m, c
        
        # object hierarchy
        def hierarchy():
            h = []
            
            def get_object_hiearchy(o):
                r = []
                for ch in o.children:
                    t, m, c = export_type(ch)
                    p = {'object': ch,
                         'children': get_object_hiearchy(ch),
                         'export': check_visibility(ch),
                         'export_type': t,
                         'mesh': m,
                         'converted': c,
                         'parent': o,
                         'type': ch.type, }
                    r.append(p)
                return r
            
            for ob in objs:
                if(ob.parent is None):
                    t, m, c = export_type(ob)
                    p = {'object': ob,
                         'children': get_object_hiearchy(ob),
                         'export': check_visibility(ob),
                         'export_type': t,
                         'mesh': m,
                         'converted': c,
                         'parent': None,
                         'type': ob.type, }
                    h.append(p)
            return h
        
        h = hierarchy()
        
        # if object is not visible and has renderable children, swap type to EMPTY and mark for export
        def renderable_children(o):
            r = False
            for c in o['children']:
                if(c['export'] is True):
                    r = True
            return r
        
        def walk(o):
            for c in o['children']:
                walk(c)
            ob = o['object']
            if(o['export'] is False and renderable_children(o)):
                o['export_type'] = 'EMPTY'
                o['export'] = True
        
        for o in h:
            walk(o)
        
        # mark to remove all redundant empties
        def check_renderables_in_tree(oo):
            ov = []
            
            def walk(o):
                for c in o['children']:
                    walk(c)
                if((o['export_type'] == 'MESH' or o['export_type'] == 'BASE_INSTANCE') or o['export_type'] == 'INSTANCE' and o['export'] is True):
                    # keep instances (Maxwell 3)
                    # keep: meshes, bases - both with export: True
                    # (export: False are hidden objects, and should be already swapped to empties if needed for hiearchy)
                    # > meshes..
                    # > bases can have children, bases are real meshes
                    ov.append(True)
                else:
                    # remove: empties, bases, instances, suns, meshes and bases with export: False (hidden objects)
                    # > empties can be removed
                    # > instances are moved to base level, because with instances hiearchy is irrelevant
                    # > suns are not objects
                    # > meshes and bases, see above
                    ov.append(False)
            for o in oo['children']:
                walk(o)
            
            if(len(ov) == 0):
                # nothing found, can be removed
                return False
            if(sum(ov) == 0):
                # found only object which can be removed
                return False
            # otherwise always True
            return True
        
        def walk(o):
            for c in o['children']:
                walk(c)
            # current object is empty
            if(o['export_type'] == 'EMPTY'):
                # check all children if there are some renderable one, if so, keep current empty
                keep = check_renderables_in_tree(o)
                if(keep is False):
                    # if not, do not export it
                    o['export'] = False
        
        for o in h:
            walk(o)
        
        # split objects to lists, instances already are
        # Maxwell 3, instances are not..
        instances = []
        meshes = []
        empties = []
        cameras = []
        bases = []
        suns = []
        
        def walk(o):
            for c in o['children']:
                walk(c)
            if(o['export'] is not False):
                # only object marked for export..
                if(o['export_type'] == 'MESH'):
                    meshes.append(o)
                elif(o['export_type'] == 'EMPTY'):
                    empties.append(o)
                elif(o['export_type'] == 'CAMERA'):
                    cameras.append(o)
                elif(o['export_type'] == 'BASE_INSTANCE'):
                    bases.append(o)
                elif(o['export_type'] == 'INSTANCE'):
                    instances.append(o)
                elif(o['export_type'] == 'SUN'):
                    suns.append(o)
        
        for o in h:
            walk(o)
        
        self.meshes = meshes
        self.bases = bases
        self.instances = instances
        self.empties = empties
        self.cameras = cameras
        
        # no visible camera, try to get active camera, if even that is missing, export no camera at all..
        if(len(self.cameras) == 0):
            log("No visible and active camera in scene!", 2, LogStyles.WARNING)
            log("Trying to find hidden active camera..", 3, LogStyles.WARNING)
            ac = self.context.scene.camera
            if(ac is not None):
                # there is one active in scene, try to find it
                def walk(o):
                    for c in o['children']:
                        walk(c)
                    ob = o['object']
                    if(ob == ac):
                        cam = o
                        cam['export'] = True
                        self.cameras.append(cam)
                        log("Found active camera: '{0}' and added to scene.".format(cam['object'].name), 3, LogStyles.WARNING)
                for o in h:
                    walk(o)
        
        # dupliverts / duplifaces
        self.duplicates = []
        
        def find_dupli_object(obj):
            for o in self.meshes:
                ob = o['object']
                if(ob == obj):
                    return o
            for o in self.bases:
                ob = o['object']
                if(ob == obj):
                    return o
            return None
        
        def put_to_bases(o):
            if(o not in self.bases and o in self.meshes):
                self.meshes.remove(o)
                self.bases.append(o)
        
        for o in self.meshes:
            ob = o['object']
            if(ob.dupli_type != 'NONE'):
                if(ob.dupli_type == 'FACES' or ob.dupli_type == 'VERTS'):
                    ob.dupli_list_create(self.context.scene, settings='RENDER')
                    for dli in ob.dupli_list:
                        do = dli.object
                        # i've just spent half an hour trying to understand why these lousy matrices does not work
                        # then suddenly i realized that calling dupli_list_clear might remove them from memory
                        # and i am just getting some garbage data..
                        # remember this in future, and do NOT use data after freeing them from memory
                        dm = dli.matrix.copy()
                        di = dli.index
                        io = find_dupli_object(do)
                        if(self.use_instances):
                            put_to_bases(io)
                        if(io is not None):
                            nm = "{0}-duplicator-{1}-{2}".format(ob.name, io['object'].name, di)
                            d = {'object': do,
                                 'dupli_name': nm,
                                 'dupli_matrix': dm,
                                 'children': [],
                                 'export': True,
                                 'export_type': 'INSTANCE',
                                 'mesh': io['mesh'],
                                 'converted': False,
                                 # 'parent': None,
                                 'parent': o,
                                 'type': 'MESH', }
                            self.duplicates.append(d)
                    ob.dupli_list_clear()
        
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(h)
        
        # print("-" * 100)
        # raise Exception()
        
        # find instances without base and change first one to base, quick and dirty..
        # this case happens when object (by name chosen as base) is on hidden layer and marked to be not exported
        # also, hope this is the last change of this nasty piece of code..
        def find_base_object_name(mnm):
            for bo in self.bases:
                if(bo['mesh'].name == mnm):
                    return bo['object'].name
        
        bdb = {}
        for o in self.instances:
            if(find_base_object_name(o['mesh'].name) is None):
                o['export_type'] = 'BASE_INSTANCE'
                self.bases.append(o)
                self.instances.remove(o)
        
        # ----------------------------------------------------------------------------------
        # everything above this line is pure magic, below is just standard code
        
        return h
    
    def _scene_properties(self):
        h, t = os.path.split(self.mxs_path)
        n, e = os.path.splitext(t)
        
        scene = {'scene_time': 60,
                 'scene_sampling_level': 12.0,
                 'scene_multilight': 0,
                 'scene_multilight_type': 0,
                 'scene_cpu_threads': 0,
                 'scene_quality': 'RS1',
                 # 'scene_priority': 'LOW',
                 # 'scene_command_line': "",
                 'output_depth': 'RGB16',
                 'output_image_enabled': True,
                 'output_image': os.path.join(h, "{}.png".format(n)),
                 'output_mxi_enabled': True,
                 'output_mxi': os.path.join(h, "{}.mxs".format(n)),
                 'materials_override': False,
                 'materials_override_path': "",
                 'materials_search_path': "",
                 'globals_motion_blur': True,
                 'globals_diplacement': True,
                 'globals_dispersion': True,
                 'channels_output_mode': 0,
                 'channels_render': True,
                 'channels_render_type': 0,
                 'channels_alpha': False,
                 'channels_alpha_file': 'PNG16',
                 'channels_alpha_opaque': False,
                 'channels_z_buffer': False,
                 'channels_z_buffer_file': 'PNG16',
                 'channels_z_buffer_near': 0.0,
                 'channels_z_buffer_far': 0.0,
                 'channels_shadow': False,
                 'channels_shadow_file': 'PNG16',
                 'channels_material_id': False,
                 'channels_material_id_file': 'PNG16',
                 'channels_object_id': False,
                 'channels_object_id_file': 'PNG16',
                 'channels_motion_vector': False,
                 'channels_motion_vector_file': 'PNG16',
                 'channels_roughness': False,
                 'channels_roughness_file': 'PNG16',
                 'channels_fresnel': False,
                 'channels_fresnel_file': 'PNG16',
                 'channels_normals': False,
                 'channels_normals_file': 'PNG16',
                 'channels_normals_space': 0,
                 'channels_position': False,
                 'channels_position_file': 'PNG16',
                 'channels_position_space': 0,
                 'channels_deep': False,
                 'channels_deep_file': 'EXR_DEEP',
                 'channels_deep_type': 0,
                 'channels_deep_min_dist': 0.2,
                 'channels_deep_max_samples': 20,
                 'channels_uv': False,
                 'channels_uv_file': 'PNG16',
                 'channels_custom_alpha': False,
                 'channels_custom_alpha_file': 'PNG16',
                 'channels_custom_alpha_groups': [],
                 'tone_color_space': 0,
                 'tone_whitepoint': 6500.0,
                 'tone_tint': 0.0,
                 'tone_burn': 0.8,
                 'tone_gamma': 2.20,
                 'tone_sharpness': False,
                 'tone_sharpness_value': 60.0,
                 'simulens_aperture_map': "",
                 'simulens_obstacle_map': "",
                 'simulens_diffraction': False,
                 'simulens_diffraction_value': 50.0,
                 'simulens_frequency': False,
                 'simulens_scattering': False,
                 'simulens_scattering_value': 50.0,
                 'simulens_devignetting': False,
                 'simulens_devignetting_value': 0.0,
                 'illum_caustics_illumination': 0,
                 'illum_caustics_refl_caustics': 0,
                 'illum_caustics_refr_caustics': 0,
                 # 'overlay_enabled': False,
                 # 'overlay_text': "",
                 # 'overlay_position': 'BOTTOM',
                 # 'overlay_color': (25, 25, 25),
                 # 'overlay_background': False,
                 # 'overlay_background_color': (176, 176, 176),
                 }
        
        try:
            mx = self.context.scene.maxwell_render
        except:
            mx = None
        
        if(mx is not None):
            scene['scene_time'] = mx.scene_time
            scene['scene_sampling_level'] = mx.scene_sampling_level
            scene['scene_multilight'] = int(mx.scene_multilight[-1:])
            scene['scene_multilight_type'] = int(mx.scene_multilight_type[-1:])
            scene['scene_cpu_threads'] = mx.scene_cpu_threads
            # scene['scene_priority'] = mx.scene_priority
            scene['scene_quality'] = mx.scene_quality
            # scene['scene_command_line'] = mx.scene_command_line
            scene['output_depth'] = mx.output_depth
            scene['output_image_enabled'] = mx.output_image_enabled
            if(mx.output_image != ''):
                scene['output_image'] = bpy.path.abspath(mx.output_image)
            scene['output_mxi_enabled'] = mx.output_mxi_enabled
            if(mx.output_mxi != ''):
                scene['output_mxi'] = bpy.path.abspath(mx.output_mxi)
            scene['materials_override'] = mx.materials_override
            scene['materials_override_path'] = bpy.path.abspath(mx.materials_override_path)
            scene['materials_search_path'] = bpy.path.abspath(mx.materials_search_path)
            scene['globals_motion_blur'] = mx.globals_motion_blur
            scene['globals_diplacement'] = mx.globals_diplacement
            scene['globals_dispersion'] = mx.globals_dispersion
            scene['channels_output_mode'] = int(mx.channels_output_mode[-1:])
            scene['channels_render'] = mx.channels_render
            scene['channels_render_type'] = int(mx.channels_render_type[-1:])
            scene['channels_alpha'] = mx.channels_alpha
            scene['channels_alpha_file'] = mx.channels_alpha_file
            scene['channels_alpha_opaque'] = mx.channels_alpha_opaque
            scene['channels_z_buffer'] = mx.channels_z_buffer
            scene['channels_z_buffer_file'] = mx.channels_z_buffer_file
            scene['channels_z_buffer_near'] = mx.channels_z_buffer_near
            scene['channels_z_buffer_far'] = mx.channels_z_buffer_far
            scene['channels_shadow'] = mx.channels_shadow
            scene['channels_shadow_file'] = mx.channels_shadow_file
            scene['channels_material_id'] = mx.channels_material_id
            scene['channels_material_id_file'] = mx.channels_material_id_file
            scene['channels_object_id'] = mx.channels_object_id
            scene['channels_object_id_file'] = mx.channels_object_id_file
            scene['channels_motion_vector'] = mx.channels_motion_vector
            scene['channels_motion_vector_file'] = mx.channels_motion_vector_file
            scene['channels_roughness'] = mx.channels_roughness
            scene['channels_roughness_file'] = mx.channels_roughness_file
            scene['channels_fresnel'] = mx.channels_fresnel
            scene['channels_fresnel_file'] = mx.channels_fresnel_file
            scene['channels_normals'] = mx.channels_normals
            scene['channels_normals_file'] = mx.channels_normals_file
            scene['channels_normals_space'] = int(mx.channels_normals_space[-1:])
            scene['channels_position'] = mx.channels_position
            scene['channels_position_file'] = mx.channels_position_file
            scene['channels_position_space'] = int(mx.channels_position_space[-1:])
            scene['channels_deep'] = mx.channels_deep
            scene['channels_deep_file'] = mx.channels_deep_file
            scene['channels_deep_type'] = int(mx.channels_deep_type[-1:])
            scene['channels_deep_min_dist'] = mx.channels_deep_min_dist
            scene['channels_deep_max_samples'] = mx.channels_deep_max_samples
            scene['channels_uv'] = mx.channels_uv
            scene['channels_uv_file'] = mx.channels_uv_file
            
            scene['channels_custom_alpha'] = mx.channels_custom_alpha
            scene['channels_custom_alpha_file'] = mx.channels_custom_alpha_file
            
            scene['channels_custom_alpha_groups'] = []
            for g in bpy.data.groups:
                gmx = g.maxwell_render
                if(gmx.custom_alpha_use):
                    a = {'name': g.name, 'objects': [], 'opaque': gmx.custom_alpha_opaque, }
                    for o in g.objects:
                        for mo in self.data:
                            if(o.name == mo['name'] and (mo['type'] == 'MESH' or mo['type'] == 'INSTANCE')):
                                a['objects'].append(o.name)
                    scene['channels_custom_alpha_groups'].append(a)
            
            # scene['tone_color_space'] = int(mx.tone_color_space[-1:])
            scene['tone_color_space'] = int(mx.tone_color_space.split('_')[1])
            scene['tone_whitepoint'] = mx.tone_whitepoint
            scene['tone_tint'] = mx.tone_tint
            scene['tone_burn'] = mx.tone_burn
            scene['tone_gamma'] = mx.tone_gamma
            scene['tone_sharpness'] = mx.tone_sharpness
            scene['tone_sharpness_value'] = mx.tone_sharpness_value / 100.0
            scene['simulens_aperture_map'] = bpy.path.abspath(mx.simulens_aperture_map)
            scene['simulens_obstacle_map'] = bpy.path.abspath(mx.simulens_obstacle_map)
            scene['simulens_diffraction'] = mx.simulens_diffraction
            scene['simulens_diffraction_value'] = maths.remap(mx.simulens_diffraction_value, 0.0, 2500.0, 0.0, 1.0)
            scene['simulens_frequency'] = maths.remap(mx.simulens_frequency, 0.0, 2500.0, 0.0, 1.0)
            scene['simulens_scattering'] = mx.simulens_scattering
            scene['simulens_scattering_value'] = maths.remap(mx.simulens_scattering_value, 0.0, 2500.0, 0.0, 1.0)
            scene['simulens_devignetting'] = mx.simulens_devignetting
            scene['simulens_devignetting_value'] = mx.simulens_devignetting_value / 100.0
            scene['illum_caustics_illumination'] = int(mx.illum_caustics_illumination[-1:])
            scene['illum_caustics_refl_caustics'] = int(mx.illum_caustics_refl_caustics[-1:])
            scene['illum_caustics_refr_caustics'] = int(mx.illum_caustics_refr_caustics[-1:])
            # scene['overlay_enabled'] = mx.overlay_enabled
            # scene['overlay_text'] = mx.overlay_text
            # scene['overlay_position'] = mx.overlay_position
            # scene['overlay_color'] = self._color_to_rgb8(mx.overlay_color)
            # scene['overlay_background'] = mx.overlay_background
            # scene['overlay_background_color'] = self._color_to_rgb8(mx.overlay_background_color)
        
        scene['type'] = 'SCENE'
        self.data.append(scene)
        
        v = Vector((0.0, 0.0, 1.0))
        v = self.matrix * v
        
        env = {'env_type': 'PHYSICAL_SKY',
               'sky_type': 'PHYSICAL',
               'sky_use_preset': False,
               'sky_preset': "",
               'sky_intensity': 1.0,
               'sky_planet_refl': 25.0,
               'sky_ozone': 0.4,
               'sky_water': 2.0,
               'sky_turbidity_coeff': 0.040,
               'sky_wavelength_exp': 1.200,
               'sky_reflectance': 80.0,
               'sky_asymmetry': 0.7,
               'dome_intensity': 10000.0,
               'dome_zenith': (255, 255, 255),
               'dome_horizon': (255, 255, 255),
               'dome_mid_point': 45.0,
               'sun_lamp_priority': True,
               'sun_type': 'PHYSICAL',
               'sun_power': 1.0,
               'sun_radius_factor': 1.0,
               'sun_temp': 5776.0,
               'sun_color': (255, 255, 255),
               'sun_location_type': 'DIRECTION',
               'sun_latlong_lat': 40.000,
               'sun_latlong_lon': -3.000,
               'sun_date': "DD.MM.YYYY",
               'sun_time': "HH:MM",
               'sun_latlong_gmt': 0.000,
               # 'sun_latlong_gmt_auto': False,
               'sun_latlong_ground_rotation': 0.0,
               'sun_angles_zenith': 45.0,
               'sun_angles_azimuth': 45.0,
               # 'sun_dir_x': 0.0,
               # 'sun_dir_y': 0.0,
               # 'sun_dir_z': 1.0,
               
               'sun_dir_x': v.x,
               'sun_dir_y': v.y,
               'sun_dir_z': v.z,
               
               'ibl_intensity': 1.0,
               'ibl_interpolation': False,
               'ibl_screen_mapping': False,
               'ibl_bg_type': 'HDR_IMAGE',
               'ibl_bg_map': "",
               'ibl_bg_intensity': 1.0,
               'ibl_bg_scale_x': 1.0,
               'ibl_bg_scale_y': 1.0,
               'ibl_bg_offset_x': 0.0,
               'ibl_bg_offset_y': 0.0,
               'ibl_refl_type': 'SAME_AS_BG',
               'ibl_refl_map': "",
               'ibl_refl_intensity': 1.0,
               'ibl_refl_scale_x': 1.0,
               'ibl_refl_scale_y': 1.0,
               'ibl_refl_offset_x': 0.0,
               'ibl_refl_offset_y': 0.0,
               'ibl_refr_type': 'SAME_AS_BG',
               'ibl_refr_map': "",
               'ibl_refr_intensity': 1.0,
               'ibl_refr_scale_x': 1.0,
               'ibl_refr_scale_y': 1.0,
               'ibl_refr_offset_x': 0.0,
               'ibl_refr_offset_y': 0.0,
               'ibl_illum_type': 'SAME_AS_BG',
               'ibl_illum_map': "",
               'ibl_illum_intensity': 1.0,
               'ibl_illum_scale_x': 1.0,
               'ibl_illum_scale_y': 1.0,
               'ibl_illum_offset_x': 0.0,
               'ibl_illum_offset_y': 0.0, }
        
        try:
            mx = self.context.scene.world.maxwell_render
        except:
            mx = None
        
        if(mx is not None):
            env['env_type'] = mx.env_type
            env['sky_type'] = mx.sky_type
            env['sky_use_preset'] = mx.sky_use_preset
            env['sky_preset'] = bpy.path.abspath(mx.sky_preset)
            env['sky_intensity'] = mx.sky_intensity
            env['sky_planet_refl'] = mx.sky_planet_refl / 100.0
            env['sky_ozone'] = mx.sky_ozone
            env['sky_water'] = mx.sky_water
            env['sky_turbidity_coeff'] = mx.sky_turbidity_coeff
            env['sky_wavelength_exp'] = mx.sky_wavelength_exp
            env['sky_reflectance'] = mx.sky_reflectance / 100.0
            env['sky_asymmetry'] = mx.sky_asymmetry
            env['dome_intensity'] = mx.dome_intensity
            env['dome_zenith'] = self._color_to_rgb8(mx.dome_zenith)
            env['dome_horizon'] = self._color_to_rgb8(mx.dome_horizon)
            env['dome_mid_point'] = math.degrees(mx.dome_mid_point)
            env['sun_lamp_priority'] = mx.sun_lamp_priority
            env['sun_type'] = mx.sun_type
            env['sun_power'] = mx.sun_power
            env['sun_radius_factor'] = mx.sun_radius_factor
            env['sun_temp'] = mx.sun_temp
            env['sun_color'] = self._color_to_rgb8(mx.sun_color)
            env['sun_location_type'] = mx.sun_location_type
            env['sun_latlong_lat'] = mx.sun_latlong_lat
            env['sun_latlong_lon'] = mx.sun_latlong_lon
            env['sun_date'] = mx.sun_date
            env['sun_time'] = mx.sun_time
            env['sun_latlong_gmt'] = mx.sun_latlong_gmt
            # env['sun_latlong_gmt_auto'] = mx.sun_latlong_gmt_auto
            env['sun_latlong_ground_rotation'] = mx.sun_latlong_ground_rotation
            env['sun_angles_zenith'] = mx.sun_angles_zenith
            env['sun_angles_azimuth'] = mx.sun_angles_azimuth
            # env['sun_dir_x'] = mx.sun_dir_x
            # env['sun_dir_y'] = mx.sun_dir_y
            # env['sun_dir_z'] = mx.sun_dir_z
            
            v = Vector((mx.sun_dir_x, mx.sun_dir_y, mx.sun_dir_z))
            v = self.matrix * v
            env['sun_dir_x'] = v.x
            env['sun_dir_y'] = v.y
            env['sun_dir_z'] = v.z
            
            env['ibl_intensity'] = mx.ibl_intensity
            env['ibl_interpolation'] = mx.ibl_interpolation
            env['ibl_screen_mapping'] = mx.ibl_screen_mapping
            env['ibl_bg_type'] = mx.ibl_bg_type
            env['ibl_bg_map'] = bpy.path.abspath(mx.ibl_bg_map)
            env['ibl_bg_intensity'] = mx.ibl_bg_intensity
            env['ibl_bg_scale_x'] = mx.ibl_bg_scale_x
            env['ibl_bg_scale_y'] = mx.ibl_bg_scale_y
            env['ibl_bg_offset_x'] = mx.ibl_bg_offset_x
            env['ibl_bg_offset_y'] = mx.ibl_bg_offset_y
            env['ibl_refl_type'] = mx.ibl_refl_type
            env['ibl_refl_map'] = bpy.path.abspath(mx.ibl_refl_map)
            env['ibl_refl_intensity'] = mx.ibl_refl_intensity
            env['ibl_refl_scale_x'] = mx.ibl_refl_scale_x
            env['ibl_refl_scale_y'] = mx.ibl_refl_scale_y
            env['ibl_refl_offset_x'] = mx.ibl_refl_offset_x
            env['ibl_refl_offset_y'] = mx.ibl_refl_offset_y
            env['ibl_refr_type'] = mx.ibl_refr_type
            env['ibl_refr_map'] = bpy.path.abspath(mx.ibl_refr_map)
            env['ibl_refr_intensity'] = mx.ibl_refr_intensity
            env['ibl_refr_scale_x'] = mx.ibl_refr_scale_x
            env['ibl_refr_scale_y'] = mx.ibl_refr_scale_y
            env['ibl_refr_offset_x'] = mx.ibl_refr_offset_x
            env['ibl_refr_offset_y'] = mx.ibl_refr_offset_y
            env['ibl_illum_type'] = mx.ibl_illum_type
            env['ibl_illum_map'] = bpy.path.abspath(mx.ibl_illum_map)
            env['ibl_illum_intensity'] = mx.ibl_illum_intensity
            env['ibl_illum_scale_x'] = mx.ibl_illum_scale_x
            env['ibl_illum_scale_y'] = mx.ibl_illum_scale_y
            env['ibl_illum_offset_x'] = mx.ibl_illum_offset_x
            env['ibl_illum_offset_y'] = mx.ibl_illum_offset_y
        
        env['type'] = 'ENVIRONMENT'
        
        if(mx is not None):
            if(mx.sun_lamp_priority):
                # extract suns from objects
                objs = self.context.scene.objects
                suns = []
                for o in objs:
                    if(o.type == 'LAMP'):
                        if(o.data.type == 'SUN'):
                            suns.append(o)
                
                # use just one sun. decide which one here..
                def get_sun(suns):
                    if(len(suns) == 0):
                        return None
                    if(len(suns) == 1):
                        return suns[0]
                    else:
                        log("more than one sun in scene", 1, LogStyles.WARNING)
                        nm = []
                        for o in suns:
                            nm.append(o['object'].name)
                        snm = sorted(nm)
                        n = snm[0]
                        for o in suns:
                            if(o['object'].name == n):
                                log("using {0} as sun".format(n), 1, LogStyles.WARNING)
                                return o
                
                sun = get_sun(suns)
                if(suns is None):
                    log("'Sun Lamp Priority' is True, but there is not Sun object in scene. Using World settings..", 1, LogStyles.WARNING)
                    env['sun_lamp_priority'] = False
                else:
                    # direction from matrix
                    mw = sun.matrix_world
                    loc, rot, sca = mw.decompose()
                    v = Vector((0.0, 0.0, 1.0))
                    v.rotate(rot)
                    v = self.matrix * v
                    mx.sun_dir_x = v.x
                    mx.sun_dir_y = v.y
                    mx.sun_dir_z = v.z
                    env['sun_location_type'] = 'DIRECTION'
                    env['sun_dir_x'] = v.x
                    env['sun_dir_y'] = v.y
                    env['sun_dir_z'] = v.z
            else:
                # sun_lamp_priority is false, use already processed environment options
                pass
        else:
            # no props, use defaults (already processed)
            pass
        
        # and change this, just in case..
        import datetime
        n = datetime.datetime.now()
        if(env['sun_date'] == "DD.MM.YYYY"):
            if(mx is not None):
                mx.sun_date = n.strftime('%d.%m.%Y')
                env['sun_date'] = mx.sun_date
            else:
                env['sun_date'] = n.strftime('%d.%m.%Y')
        if(env['sun_time'] == "HH:MM"):
            if(mx is not None):
                mx.sun_time = n.strftime('%H:%M')
                env['sun_time'] = mx.sun_time
            else:
                env['sun_time'] = n.strftime('%H:%M')
        
        self.data.append(env)
    
    def _export_data(self):
        # cameras
        log("processing cameras..", 1, LogStyles.MESSAGE)
        self._cameras()
        # if no active camera, set active the first found..
        active = False
        for o in self.data:
            if(o['type'] == 'CAMERA'):
                if(o['active']):
                    active = True
        
        # and, if there is no camera, nothing will happen..
        if(not active):
            for o in self.data:
                if(o['type'] == 'CAMERA'):
                    o['active'] = True
                    break
        
        # empties
        log("processing empties..", 1, LogStyles.MESSAGE)
        self._empties()
        
        # meshes
        log("processing meshes..", 1, LogStyles.MESSAGE)
        self._meshes()
        
        if(self.use_instances):
            # base instances
            log("processing instance base meshes..", 1, LogStyles.MESSAGE)
            self._instance_bases()
            # instances
            log("processing instances..", 1, LogStyles.MESSAGE)
            self._instances()
        
        log("processing duplicates..", 1, LogStyles.MESSAGE)
        self._duplicates()
        
        # log("processing sun..", 1, LogStyles.MESSAGE)
        # self._sun()
        
        log("processing particles..", 1, LogStyles.MESSAGE)
        self._particles()
        
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.tree)
    
    def _serialize(self, d, n):
        if(not n.endswith(".json")):
            n = "{}.json".format(n)
        p = os.path.join(self.tmp_dir, n)
        with open("{0}.tmp".format(p), 'w', encoding='utf-8', ) as f:
            json.dump(d, f, skipkeys=False, ensure_ascii=False, indent=4, )
        if(os.path.exists(p)):
            os.remove(p)
        shutil.move("{0}.tmp".format(p), p)
        return p
    
    def _cameras(self):
        """Loop over all cameras and prepare data for pymaxwell."""
        for o in self.cameras:
            log("{0}".format(o['object'].name), 2)
            
            ob = o['object']
            cd = ob.data
            rp = self.context.scene.render
            try:
                mx = ob.data.maxwell_render
            except:
                mx = None
            
            d = {'name': ob.name,
                 'type': 'CAMERA',
                 'parent': None,
                 'active': (self.context.scene.camera == ob),
                 
                 'focal_length': cd.lens / 1000.0,
                 'number_of_steps': 1,
                 'origin': None,
                 'focal_point': None,
                 'up': None,
                 'set_step': None,
                 
                 'resolution_x': None,
                 'resolution_y': None,
                 'film_width': None,
                 'film_height': None,
                 'dof_distance': None,
                 'pixel_aspect': 1.0,
                 'set_cut_planes': None,
                 'set_shift_lens': None,
                 'screen_region': 'NONE',
                 'screen_region_xywh': (),
                 
                 # 'lens': 'TYPE_THIN_LENS',
                 'lens': 0,
                 'shutter': 1 / 250.0,
                 'fstop': 8.0,
                 'fov': 180.0,
                 'azimuth': 180.0,
                 'angle': 180.0,
                 'iso': 100.0,
                 'aperture': 'CIRCULAR',
                 'diaphragm_blades': 6,
                 'diaphragm_angle': 60,
                 
                 'custom_bokeh': False,
                 'bokeh_ratio': 1.0,
                 'bokeh_angle': 0.0,
                 
                 'shutter_angle': 17.280,
                 'frame_rate': 24.0,
                 
                 'response': 'Maxwell',
                 
                 'hide': False,
                 # 'projection_type': 'TYPE_PERSPECTIVE',
                 }
            
            if(mx is not None):
                d['lens'] = int(mx.lens[-1:])
                d['shutter'] = 1 / mx.shutter
                d['fstop'] = mx.fstop
                d['fov'] = mx.fov
                # d['azimuth'] = math.degrees(mx.azimuth)
                d['azimuth'] = mx.azimuth
                # d['angle'] = math.degrees(mx.angle)
                d['angle'] = mx.angle
                d['iso'] = mx.iso
                d['aperture'] = mx.aperture
                d['diaphragm_blades'] = mx.diaphragm_blades
                d['diaphragm_angle'] = mx.diaphragm_angle
                # d['shutter_angle'] = math.degrees(mx.shutter_angle)
                d['shutter_angle'] = mx.shutter_angle
                d['frame_rate'] = mx.frame_rate
                d['set_cut_planes'] = (cd.clip_start, cd.clip_end, int(mx.zclip))
                d['custom_bokeh'] = mx.custom_bokeh
                d['bokeh_ratio'] = mx.bokeh_ratio
                d['bokeh_angle'] = mx.bokeh_angle
                
                d['response'] = mx.response
                
                d['hide'] = mx.hide
            
            d['resolution_x'] = int(rp.resolution_x * rp.resolution_percentage / 100.0)
            d['resolution_y'] = int(rp.resolution_y * rp.resolution_percentage / 100.0)
            d['pixel_aspect'] = rp.pixel_aspect_x / rp.pixel_aspect_y
            
            if(mx is not None):
                d['screen_region'] = mx.screen_region
                d['screen_region_xywh'] = ()
                if(mx.screen_region != 'NONE'):
                    x = int(d['resolution_x'] * rp.border_min_x)
                    h = d['resolution_y'] - int(d['resolution_y'] * rp.border_min_y)
                    w = int(d['resolution_x'] * rp.border_max_x)
                    y = d['resolution_y'] - int(d['resolution_y'] * rp.border_max_y)
                    d['screen_region_xywh'] = (x, y, w, h)
            
            # film width / height: width / height ratio a ==  x_res / y_res ratio
            # x_res / y_res is more important than sensor size, depending on sensor fit the other one is calculated
            sf = cd.sensor_fit
            film_height = cd.sensor_height / 1000.0
            film_width = cd.sensor_width / 1000.0
            if(sf == 'AUTO'):
                if(d['resolution_x'] > d['resolution_y']):
                    # horizontal
                    film_width = cd.sensor_width / 1000.0
                    sf = 'HORIZONTAL'
                else:
                    # vertical
                    film_height = cd.sensor_width / 1000.0
                    sf = 'VERTICAL'
            if(sf == 'VERTICAL'):
                film_width = (film_height * d['resolution_x']) / d['resolution_y']
            else:
                film_height = (film_width * d['resolution_y']) / d['resolution_x']
            d['film_width'] = film_width
            d['film_height'] = film_height
            
            mw_loc, mw_rot, _ = ob.matrix_world.decompose()
            mw_location = Matrix.Translation(mw_loc).to_4x4()
            mw_rotation = mw_rot.to_matrix().to_4x4()
            mw_scale = Matrix.Identity(4)
            mw = mw_location * mw_rotation * mw_scale
            origin = mw.to_translation()
            if(ob.data.dof_object):
                dof_distance = (origin - ob.data.dof_object.matrix_world.to_translation()).length
            else:
                dof_distance = ob.data.dof_distance
                if(dof_distance == 0.0):
                    dof_distance = 1.0
            focal_point = mw * Vector((0.0, 0.0, -dof_distance))
            up = mw * Vector((0.0, 1.0, 0.0)) - origin
            d['origin'] = Vector(self.matrix * origin).to_tuple()
            d['focal_point'] = Vector(self.matrix * focal_point).to_tuple()
            d['up'] = Vector(self.matrix * up).to_tuple()
            d['dof_distance'] = dof_distance
            
            d['set_step'] = (0, d['origin'], d['focal_point'], d['up'], d['focal_length'], d['fstop'], 1)
            
            d['set_shift_lens'] = (cd.shift_x * 10.0, cd.shift_y * 10.0)
            
            self.data.append(d)
            
            # for k, v in d.items():
            #     print("{0}: {1}".format(k, v))
            # print()
    
    def _matrix_to_base_and_pivot(self, m):
        """Convert Matrix to Base and Pivot"""
        b = ((m[0][3], m[2][3], m[1][3] * -1),
             (m[0][0], m[2][0], m[1][0] * -1),
             (m[0][2], m[2][2], m[1][2] * -1),
             (m[0][1] * -1, m[2][1] * -1, m[1][1]), )
        p = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), )
        return (b, p, )
    
    def _color_to_rgb8(self, c):
        return tuple([int(255 * v) for v in c])
    
    def _object_properties(self, ob, d):
        try:
            mx = ob.maxwell_render
        except:
            mx = None
        
        if(mx is not None):
            d['hide'] = mx.hide
            d['opacity'] = mx.opacity
            d['hidden_camera'] = mx.hidden_camera
            d['hidden_camera_in_shadow_channel'] = mx.hidden_camera_in_shadow_channel
            d['hidden_global_illumination'] = mx.hidden_global_illumination
            d['hidden_reflections_refractions'] = mx.hidden_reflections_refractions
            d['hidden_zclip_planes'] = mx.hidden_zclip_planes
            d['object_id'] = self._color_to_rgb8(mx.object_id)
        
        return d
    
    def _object_materials(self, ob, d, instance=False, ):
        def check_path(p):
            if(p is not ""):
                if(p.startswith('//')):
                    p = bpy.path.abspath(p)
                if(os.path.exists(p)):
                    h, t = os.path.split(p)
                    n, e = os.path.splitext(t)
                    if(e == '.mxm'):
                        return True
                log("{1}: mxm ('{0}') does not exist.".format(p, self.__class__.__name__), 2, LogStyles.WARNING, )
            return False
        
        if(instance is True):
            # is instance
            def find_base_name(mnm):
                for ib in self.data:
                    try:
                        if(ib['instance_base'] is True):
                            if(ib['mesh_name'] == mnm):
                                return ib['name']
                    except KeyError:
                        pass
            
            # so find base object
            original = self.context.scene.objects[find_base_name(ob.data.name)]
            # check if instance has the same materials as originals
            if(len(ob.material_slots) != 0):
                for i, s in enumerate(ob.material_slots):
                    if(s.material is not None):
                        # double silly check, for maxwell_render in instance's material and original's material
                        try:
                            mmx = s.material.maxwell_render
                        except:
                            mmx = None
                        if(mmx is not None):
                            im = mmx.mxm_file
                        else:
                            im = ""
                        try:
                            ommx = original.material_slots[i].maxwell_render
                        except:
                            ommx = None
                        if(ommx is not None):
                            om = ommx.mxm_file
                        else:
                            om = ""
                        if((im != om) and (mmx is not None and ommx is not None)):
                            log("{1}: {0}: multi material instances with different materials than original are not supported".format(ob.name, self.__class__.__name__), 2, LogStyles.WARNING, )
                            break
            for i, s in enumerate(ob.material_slots):
                if(s.material is not None):
                    try:
                        mmx = s.material.maxwell_render
                    except:
                        mmx = None
                    if(mmx is not None):
                        # there is material with data
                        fm = bpy.path.abspath(mmx.mxm_file)
                        if(not check_path(fm)):
                            fm = ""
                        if(fm != ""):
                            a = (mmx.embed, fm)
                        else:
                            a = (False, "", )
                    else:
                        # there isn't, put blank
                        a = (False, "", )
                else:
                    a = (False, "", )
                d['materials'].append(a)
        else:
            # not instance
            for s in ob.material_slots:
                # check all slots
                if(s.material is not None):
                    # and if there is a material, store props
                    try:
                        mmx = s.material.maxwell_render
                    except:
                        mmx = None
                    if(mmx is not None):
                        # there is material with data
                        fm = bpy.path.abspath(mmx.mxm_file)
                        if(not check_path(fm)):
                            fm = ""
                        if(fm != ""):
                            a = (mmx.embed, fm)
                        else:
                            a = (False, "", )
                    else:
                        # there isn't, put blank
                        a = (False, "", )
                else:
                    # else put blank material
                    a = (False, "", )
                    if(len(ob.material_slots) > 1):
                        # if it is a multi material object, create dummy material
                        # but this should be handled in pymaxwell..
                        pass
                d['materials'].append(a)
        
        try:
            obm = ob.maxwell_render
        except:
            obm = None
        
        if(obm is not None):
            bm = bpy.path.abspath(obm.backface_material_file)
            if(not check_path(bm)):
                bm = ""
            d['backface_material'] = (bm, obm.backface_material_embed)
        else:
            d['backface_material'] = []
        
        # and i don't want you to complain about this function.. understand?
        # it is much better then it was, believe me. previous version was horrid.
        # don't you even try to look for it in repository, you've been warned..
        
        return d
    
    def _empties(self):
        """Loop over all empties and prepare data for pymaxwell."""
        for o in self.empties:
            log("{0}".format(o['object'].name), 2)
            ob = o['object']
            
            # template
            d = {'name': ob.name,
                 'parent': None,
                 
                 'base': None,
                 'pivot': None,
                 
                 'opacity': 100.0,
                 'hidden_camera': False,
                 'hidden_camera_in_shadow_channel': False,
                 'hidden_global_illumination': False,
                 'hidden_reflections_refractions': False,
                 'hidden_zclip_planes': False,
                 'object_id': (255, 255, 255),
                 
                 'type': 'EMPTY', }
            
            d = self._object_properties(ob, d)
            
            if(ob.parent):
                d['parent'] = ob.parent.name
            
            if(ob.parent_type == 'BONE'):
                oamw = ob.matrix_world.copy()
                apmw = ob.parent.matrix_world.copy()
                apmw.invert()
                amw = apmw * oamw
                b, p = self._matrix_to_base_and_pivot(amw)
            else:
                b, p = self._matrix_to_base_and_pivot(ob.matrix_local)
            d['base'] = b
            d['pivot'] = p
            
            self.data.append(d)
            
            # for k, v in d.items():
            #     print("{0}: {1}".format(k, v))
            # print()
    
    def _mesh_to_data(self, o):
        """Mesh to pymaxwell data."""
        ob = o['object']
        
        if(o['converted'] is True):
            # get to-mesh-conversion result, will be removed at the end..
            me = o['mesh']
        else:
            # or make new flattened mesh
            me = ob.to_mesh(self.context.scene, True, 'RENDER', )
        # mesh will be removed at the end of this..
        
        # rotate x -90
        mr90 = Matrix.Rotation(math.radians(-90.0), 4, 'X')
        me.transform(mr90)
        
        # here, in triangulating, i experienced crash from not so well mesh, validating before prevents it..
        me.validate()
        
        # triangulate in advance :)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        
        me.calc_tessface()
        me.calc_normals()
        
        nm = ob.data.name
        if(self.use_instances is False):
            nm = ob.name
        
        md = {'name': nm,
              'channel_uvw': [],
              'v_setVertex': [],
              'v_setNormal': [],
              'f_setNormal': [],
              'f_setTriangle': [],
              'f_setTriangleUVW': [],
              'f_setTriangleMaterial': [], }
        
        d = {'name': ob.name,
             'num_vertexes': len(me.vertices),
             'num_normals': len(me.vertices) + len(me.tessfaces),
             'num_triangles': len(me.tessfaces),
             'num_positions_per_vertex': 1,
             'mesh_data': md['name'],
             'matrix': None,
             'parent': None,
             
             'opacity': 100.0,
             'hidden_camera': False,
             'hidden_camera_in_shadow_channel': False,
             'hidden_global_illumination': False,
             'hidden_reflections_refractions': False,
             'hidden_zclip_planes': False,
             'object_id': (255, 255, 255),
             
             'num_materials': len(ob.material_slots),
             'materials': [],
             
             'hide': False,
             
             'type': 'MESH', }
        
        d = self._object_properties(ob, d)
        d = self._object_materials(ob, d)
        
        if(ob.parent):
            d['parent'] = ob.parent.name
        
        # d = self._object_transform(ob, d)
        # b, p = self._matrix_to_base_and_pivot(ob.matrix_local)
        if(ob.parent_type == 'BONE'):
            oamw = ob.matrix_world.copy()
            apmw = ob.parent.matrix_world.copy()
            apmw.invert()
            amw = apmw * oamw
            b, p = self._matrix_to_base_and_pivot(amw)
        else:
            b, p = self._matrix_to_base_and_pivot(ob.matrix_local)
        
        d['base'] = b
        d['pivot'] = p
        
        # mesh data
        for ti, uvt in enumerate(me.uv_textures):
            md['channel_uvw'].append(ti)
        
        # vertices and faces joined progress
        prgr = progress.get_progress(len(me.vertices) + len(me.tessfaces), 2)
        
        # vertices, vertex normals
        for i, v in enumerate(me.vertices):
            # index, position index, vector
            md['v_setVertex'].append((i, 0, v.co.to_tuple(), ))
            # index, position index, vector
            md['v_setNormal'].append((i, 0, v.normal.to_tuple(), ))
            #
            prgr.step()
        
        # faces, face normals, uvs
        ni = len(me.vertices) - 1
        ti = 0
        
        for fi, f in enumerate(me.tessfaces):
            ni = ni + 1
            # normal
            md['f_setNormal'].append((ni, 0, f.normal.to_tuple(), ))
            fv = f.vertices
            # smoothing
            if(f.use_smooth):
                # vertex normals
                nix = [fv[0], fv[1], fv[2]]
            else:
                # face normal
                nix = [ni, ni, ni, ]
            # geometry
            md['f_setTriangle'].append((ti, (fv[0], fv[1], fv[2]), (nix[0], nix[1], nix[2]), ))
            md['f_setTriangleMaterial'].append((ti, f.material_index, ))
            # uv
            for tix, uvtex in enumerate(me.tessface_uv_textures):
                uv = uvtex.data[fi].uv
                md['f_setTriangleUVW'].append((ti, tix,
                                               uv[0][0], 1.0 - uv[0][1], 0.0,
                                               uv[1][0], 1.0 - uv[1][1], 0.0,
                                               uv[2][0], 1.0 - uv[2][1], 0.0, ))
            ti = ti + 1
            #
            prgr.step()
        
        # cleanup
        bpy.data.meshes.remove(me)
        
        # print(d)
        # print(md)
        # raise Exception()
        
        def texture_to_data(name):
            tex = None
            for t in bpy.data.textures:
                if(t.type == 'IMAGE'):
                    if(t.name == name):
                        tex = t
            
            d = {'type': 'IMAGE',
                 'path': "",
                 'channel': 0,
                 'use_override_map': False,
                 'tile_method_type': [True, True],
                 'tile_method_units': 0,
                 'repeat': [1.0, 1.0],
                 'mirror': [False, False],
                 'offset': [0.0, 0.0],
                 'rotation': 0.0,
                 'invert': False,
                 'alpha_only': False,
                 'interpolation': False,
                 'brightness': 0.0,
                 'contrast': 0.0,
                 'saturation': 0.0,
                 'hue': 0.0,
                 'rgb_clamp': [0.0, 255.0], }
            if(tex is not None):
                d['path'] = bpy.path.abspath(tex.image.filepath),
                return d
            return None
        
        sd = ob.maxwell_subdivision_extension
        if(sd.enabled):
            d['subdiv_ext'] = [int(sd.level), int(sd.scheme), int(sd.interpolation), sd.crease, math.degrees(sd.smooth), ]
        else:
            d['subdiv_ext'] = None
        
        sc = ob.maxwell_scatter_extension
        if(sc.enabled):
            d['scatter_ext'] = {'scatter_object': sc.scatter_object,
                                'inherit_objectid': sc.inherit_objectid,
                                'density': sc.density,
                                'density_map': texture_to_data(sc.density_map),
                                'seed': int(sc.seed),
                                'scale_x': sc.scale_x,
                                'scale_y': sc.scale_y,
                                'scale_z': sc.scale_z,
                                'scale_map': texture_to_data(sc.scale_map),
                                'scale_variation_x': sc.scale_variation_x,
                                'scale_variation_y': sc.scale_variation_y,
                                'scale_variation_z': sc.scale_variation_z,
                                'rotation_x': math.degrees(sc.rotation_x),
                                'rotation_y': math.degrees(sc.rotation_y),
                                'rotation_z': math.degrees(sc.rotation_z),
                                'rotation_map': texture_to_data(sc.rotation_map),
                                'rotation_variation_x': sc.rotation_variation_x,
                                'rotation_variation_y': sc.rotation_variation_y,
                                'rotation_variation_z': sc.rotation_variation_z,
                                'rotation_direction': int(sc.rotation_direction),
                                'lod': sc.lod,
                                'lod_min_distance': sc.lod_min_distance,
                                'lod_max_distance': sc.lod_max_distance,
                                'lod_max_distance_density': sc.lod_max_distance_density,
                                'display_percent': int(sc.display_percent),
                                'display_max_blades': int(sc.display_max_blades), }
        else:
            d['scatter_ext'] = None
        
        return d, md
    
    def _meshes(self):
        """Loop over all mesh objects and prepare data for pymaxwell."""
        for o in self.meshes:
            log("{0}".format(o['object'].name), 2)
            d, md = self._mesh_to_data(o)
            
            p = os.path.join(self.tmp_dir, "{0}.binmesh".format(md['name']))
            w = MXSBinMeshWriter(p, md, d['num_positions_per_vertex'])
            
            self.mesh_data_paths.append(p)
            d['mesh_data_path'] = p
            self.data.append(d)
    
    def _instance_bases(self):
        """Loop over all instance base mesh objects and prepare data for pymaxwell."""
        for o in self.bases:
            log("{0}".format(o['object'].name), 2)
            ob = o['object']
            d, md = self._mesh_to_data(o)
            d['instance_base'] = True
            d['mesh_name'] = ob.data.name
            
            p = os.path.join(self.tmp_dir, "{0}.binmesh".format(md['name']))
            w = MXSBinMeshWriter(p, md, d['num_positions_per_vertex'])
            
            self.mesh_data_paths.append(p)
            d['mesh_data_path'] = p
            self.data.append(d)
    
    def _instances(self):
        """Loop over all instances and prepare data for pymaxwell."""
        for o in self.instances:
            log("{0}".format(o['object'].name), 2)
            
            ob = o['object']
            
            d = {'name': ob.name,
                 'matrix': None,
                 'parent': None,
                 
                 'opacity': 100.0,
                 'hidden_camera': False,
                 'hidden_camera_in_shadow_channel': False,
                 'hidden_global_illumination': False,
                 'hidden_reflections_refractions': False,
                 'hidden_zclip_planes': False,
                 'object_id': (255, 255, 255),
                 
                 'num_materials': len(ob.material_slots),
                 'materials': [],
                 
                 'hide': False,
                 
                 'instanced': None,
                 'type': 'INSTANCE', }
            
            d = self._object_properties(ob, d)
            
            if(ob.parent):
                d['parent'] = ob.parent.name
            
            # there is a bug in pymaxwell (i think)
            # negative scaled instances will be transformed in a weird way
            # currently i have no solution, so just warn about it.
            _, _, ms = ob.matrix_world.decompose()
            if(ms.x < 0.0 or ms.y < 0.0 or ms.z < 0.0):
                log("{1}: WARNING: instance {0} is negative scaled. Weird transformation will occur..".format(ob.name, self.__class__.__name__), 1, LogStyles.WARNING, )
            
            # instances in Maxwell are some sort of children of main object, so when you have instance parented to an empty
            # and then moved away, matrix_local will will provide different matrix than the real one is.. (makes sense?)
            # anyway, use matrix_world and everything will be ok..
            
            # d = self._object_transform(ob, d)
            # b, p = self._matrix_to_base_and_pivot(ob.matrix_local)
            if(ob.parent_type == 'BONE'):
                oamw = ob.matrix_world.copy()
                apmw = ob.parent.matrix_world.copy()
                apmw.invert()
                amw = apmw * oamw
                b, p = self._matrix_to_base_and_pivot(amw)
            else:
                b, p = self._matrix_to_base_and_pivot(ob.matrix_local)
            
            d['base'] = b
            d['pivot'] = p
            
            def find_base_object_name(mnm):
                for o in self.bases:
                    if(o['mesh'].name == mnm):
                        return o['object'].name
            
            d['instanced'] = find_base_object_name(ob.data.name)
            d = self._object_materials(ob, d, True, )
            
            self.data.append(d)
            
            # for k, v in d.items():
            #     print("{0}: {1}".format(k, v))
            # print()
    
    def _duplicates(self):
        """Loop over all duplis and prepare data for pymaxwell."""
        if(len(self.duplicates) == 0):
            # skip when no duplis
            return
        
        duplis = {}
        for o in self.duplicates:
            n = o['object'].name
            if(n not in duplis.keys()):
                duplis[n] = 1
            else:
                duplis[n] += 1
        
        m = ""
        for k, v in duplis.items():
            m += "{0}: {1} duplicates, ".format(k, v)
        log(m, 2)
        
        prgr = progress.get_progress(len(self.duplicates), 2)
        
        for o in self.duplicates:
            prgr.step()
            if(self.use_instances):
                ob = o['object']
                
                d = {'name': o['dupli_name'],
                     'matrix': None,
                     'parent': ob.name,
                     
                     'opacity': 100.0,
                     'hidden_camera': False,
                     'hidden_camera_in_shadow_channel': False,
                     'hidden_global_illumination': False,
                     'hidden_reflections_refractions': False,
                     'hidden_zclip_planes': False,
                     'object_id': (255, 255, 255),
                     
                     'num_materials': len(ob.material_slots),
                     'materials': [],
                     
                     'hide': False,
                     
                     'instanced': None,
                     'type': 'INSTANCE', }
                
                def find_base_object_name(mnm):
                    for o in self.bases:
                        if(o['mesh'].name == mnm):
                            return o['object'].name
                
                d['instanced'] = find_base_object_name(o['mesh'].name)
                
                d = self._object_properties(ob, d)
                d = self._object_materials(ob, d, True)
                
                def find_base_object_matrix(mnm):
                    for o in self.bases:
                        if(o['mesh'].name == mnm):
                            return o['object'].matrix_world
                
                # mwi = find_base_object_matrix(o['mesh'].name).inverted()
                # d = self._object_transform(ob, d, mwi * o['dupli_matrix'])
                
                mwi = find_base_object_matrix(o['mesh'].name).inverted()
                b, p = self._matrix_to_base_and_pivot(mwi * o['dupli_matrix'])
                d['base'] = b
                d['pivot'] = p
                
                self.data.append(d)
            else:
                od = None
                for d in self.data:
                    if(d['name'] == o['object'].name):
                        od = d
                if(od is not None):
                    d = {}
                    for k, v in od.items():
                        d[k] = v
                    d['name'] = o['dupli_name']
                    
                    # # dupli world matrix to local matrix when parented
                    # dmw = o['dupli_matrix'].copy()
                    # pmw = bpy.context.scene.objects[d['parent']].matrix_world.copy()
                    # pmw.invert()
                    # m = pmw * dmw
                    # d = self._object_transform(od, d, m)
                    dmw = o['dupli_matrix'].copy()
                    pmw = bpy.context.scene.objects[d['parent']].matrix_world.copy()
                    pmw.invert()
                    m = pmw * dmw
                    b, p = self._matrix_to_base_and_pivot(m)
                    d['base'] = b
                    d['pivot'] = p
                    
                    self.data.append(d)
                else:
                    log("cannot find exported mesh data for object: {0}".format(o['object'].name), 2, LogStyles.ERROR)
    
    def _particles(self):
        scene = self.context.scene
        
        def verify_parent(name):
            for d in self.data:
                if(d['name'] == name):
                    return True
            return False
        
        self.particles = []
        for o in scene.objects:
            if(len(o.particle_systems) != 0):
                for ps in o.particle_systems:
                    if(ps.settings.maxwell_render.use == 'PARTICLES'):
                        parent = o.name
                        p = verify_parent(parent)
                        if(not p):
                            log("Particles '{0}' container object '{1}' is not renderable and thus not exported. Particles will not be parented.".format(ps.name, o.name), 1, LogStyles.WARNING, )
                            parent = None
                        
                        try:
                            mx = ps.settings.maxwell_render
                        except:
                            log("Particles cannot be exported without 'Maxwell Render' addon enabled..", 1, LogStyles.WARNING, )
                            continue
                        
                        renderable = False
                        for om in self.meshes:
                            if(om['object'] == o):
                                if(om['export']):
                                    renderable = True
                                    break
                        show_render = False
                        for mo in o.modifiers:
                            if(mo.type == 'PARTICLE_SYSTEM'):
                                if(mo.particle_system == ps):
                                    if(mo.show_render is True):
                                        show_render = True
                        
                        if(renderable and show_render):
                            d = {'props': ps.settings.maxwell_particles_extension,
                                 'matrix': Matrix(),
                                 'type': ps.settings.maxwell_render.use,
                                 'ps': ps,
                                 'name': "{}-{}".format(o.name, ps.name),
                                 'pmatrix': o.matrix_local,
                                 'parent': parent, }
                            self.particles.append(d)
                    elif(ps.settings.maxwell_render.use == 'GRASS'):
                        try:
                            mx = ps.settings.maxwell_render
                        except:
                            log("Particles cannot be exported without 'Maxwell Render' addon enabled..", 1, LogStyles.WARNING, )
                            continue
                        
                        renderable = False
                        for om in self.meshes:
                            if(om['object'] == o):
                                if(om['export']):
                                    renderable = True
                                    break
                        show_render = False
                        for mo in o.modifiers:
                            if(mo.type == 'PARTICLE_SYSTEM'):
                                if(mo.particle_system == ps):
                                    if(mo.show_render is True):
                                        show_render = True
                        
                        if(renderable and show_render):
                            d = {'props': ps.settings.maxwell_grass_extension,
                                 'matrix': o.matrix_local,
                                 'type': ps.settings.maxwell_render.use,
                                 'ps': ps,
                                 'name': "{}-{}".format(o.name, ps.name),
                                 'parent': o.name, }
                            self.particles.append(d)
                    elif(ps.settings.maxwell_render.use == 'HAIR'):
                        parent = o.name
                        p = verify_parent(parent)
                        if(not p):
                            log("Hair '{0}' container object '{1}' is not renderable and thus not exported. Hair will not be parented.".format(ps.name, o.name), 1, LogStyles.WARNING, )
                            parent = None
                        
                        try:
                            mx = ps.settings.maxwell_render
                        except:
                            log("Particles cannot be exported without 'Maxwell Render' addon enabled..", 1, LogStyles.WARNING, )
                            continue
                        
                        renderable = False
                        for om in self.meshes:
                            if(om['object'] == o):
                                if(om['export']):
                                    renderable = True
                                    break
                        show_render = False
                        for mo in o.modifiers:
                            if(mo.type == 'PARTICLE_SYSTEM'):
                                if(mo.particle_system == ps):
                                    if(mo.show_render is True):
                                        show_render = True
                        
                        if(renderable and show_render):
                            d = {'props': ps.settings.maxwell_hair_extension,
                                 'matrix': Matrix(),
                                 'type': ps.settings.maxwell_render.use,
                                 'ps': ps,
                                 'name': "{}-{}".format(o.name, ps.name),
                                 'parent': parent, }
                            self.particles.append(d)
                    else:
                        pass
        
        def texture_to_data(name, ps):
            tex = None
            for ts in ps.settings.texture_slots:
                if(ts is not None):
                    if(ts.texture is not None):
                        if(ts.texture.type == 'IMAGE'):
                            if(ts.texture.name == name):
                                tex = ts.texture
            
            d = {'type': 'IMAGE',
                 'path': "",
                 'channel': 0,
                 'use_override_map': False,
                 'tile_method_type': [True, True],
                 'tile_method_units': 0,
                 'repeat': [1.0, 1.0],
                 'mirror': [False, False],
                 'offset': [0.0, 0.0],
                 'rotation': 0.0,
                 'invert': False,
                 'alpha_only': False,
                 'interpolation': False,
                 'brightness': 0.0,
                 'contrast': 0.0,
                 'saturation': 0.0,
                 'hue': 0.0,
                 'rgb_clamp': [0.0, 255.0], }
            if(tex is not None):
                d['path'] = bpy.path.abspath(tex.image.filepath),
                return d
            return None
        
        for dp in self.particles:
            q = None
            log("{0} ({1})".format(dp['name'], dp['type']), 2)
            b, p = self._matrix_to_base_and_pivot(dp['matrix'])
            m = dp['props']
            ps = dp['ps']
            
            if(dp['type'] == 'PARTICLES'):
                material = bpy.path.abspath(m.material)
                if(material != "" and not os.path.exists(material)):
                    log("{1}: mxm ('{0}') does not exist.".format(material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                backface_material = bpy.path.abspath(m.backface_material)
                if(backface_material != "" and not os.path.exists(backface_material)):
                    log("{1}: backface mxm ('{0}') does not exist.".format(backface_material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                
                if(m.source == 'BLENDER_PARTICLES'):
                    if(len(ps.particles) == 0):
                        msg = "particle system {} has no particles".format(ps.name)
                        raise ValueError(msg)
                    ok = False
                    for part in ps.particles:
                        if(part.alive_state == "ALIVE"):
                            ok = True
                            break
                    if(ok is False):
                        msg = "particle system {} has no 'ALIVE' particles".format(ps.name)
                        raise ValueError(msg)
                    locs = []
                    vels = []
                    mat = dp['pmatrix'].copy()
                    mat.invert()
                    for part in ps.particles:
                        if(part.alive_state == "ALIVE"):
                            l = part.location.copy()
                            l = mat * l
                            locs.append(l.to_tuple() + (0.0, 0.0, 0.0, 0, 0, 0))
                            if(m.bl_use_velocity):
                                v = part.velocity.copy()
                                v = mat * v
                                vels.append(v.to_tuple() + (0.0, 0.0, 0.0, 0, 0, 0))
                            else:
                                vels.append((0.0, 0.0, 0.0) + (0.0, 0.0, 0.0, 0, 0, 0))
                    locs = maths.apply_matrix_for_realflow_bin_export(locs)
                    vels = maths.apply_matrix_for_realflow_bin_export(vels)
                    particles = []
                    for i, ploc in enumerate(locs):
                        particles.append(rfbin.RFBinParticle(pid=i, position=ploc[:3], velocity=vels[i][:3]))
                    
                    if(os.path.exists(bpy.path.abspath(m.bin_directory)) and not m.bin_overwrite):
                        raise OSError("file: {} exists".format(bpy.path.abspath(m.bin_directory)))
                    
                    cf = self.context.scene.frame_current
                    prms = {'directory': bpy.path.abspath(m.bin_directory),
                            'name': "{}".format(dp['name']),
                            'frame': cf,
                            'particles': particles,
                            'fps': self.context.scene.render.fps,
                            'size': m.bl_size, }
                    rfbw = rfbin.RFBinWriter(**prms)
                    m.bin_filename = rfbw.path
                else:
                    pass
                
                q = {'bin_filename': bpy.path.abspath(m.bin_filename),
                     'bin_radius_multiplier': m.bin_radius_multiplier, 'bin_motion_blur_multiplier': m.bin_motion_blur_multiplier, 'bin_shutter_speed': m.bin_shutter_speed,
                     'bin_load_particles': m.bin_load_particles, 'bin_axis_system': int(m.bin_axis_system[-1:]), 'bin_frame_number': m.bin_frame_number, 'bin_fps': m.bin_fps,
                     'bin_extra_create_np_pp': m.bin_extra_create_np_pp, 'bin_extra_dispersion': m.bin_extra_dispersion, 'bin_extra_deformation': m.bin_extra_deformation,
                     'bin_load_force': int(m.bin_load_force), 'bin_load_vorticity': int(m.bin_load_vorticity), 'bin_load_normal': int(m.bin_load_normal),
                     'bin_load_neighbors_num': int(m.bin_load_neighbors_num), 'bin_load_uv': int(m.bin_load_uv), 'bin_load_age': int(m.bin_load_age),
                     'bin_load_isolation_time': int(m.bin_load_isolation_time), 'bin_load_viscosity': int(m.bin_load_viscosity),
                     'bin_load_density': int(m.bin_load_density), 'bin_load_pressure': int(m.bin_load_pressure), 'bin_load_mass': int(m.bin_load_mass),
                     'bin_load_temperature': int(m.bin_load_temperature), 'bin_load_id': int(m.bin_load_id),
                     'bin_min_force': m.bin_min_force, 'bin_max_force': m.bin_max_force, 'bin_min_vorticity': m.bin_min_vorticity, 'bin_max_vorticity': m.bin_max_vorticity,
                     'bin_min_nneighbors': m.bin_min_nneighbors, 'bin_max_nneighbors': m.bin_max_nneighbors, 'bin_min_age': m.bin_min_age, 'bin_max_age': m.bin_max_age,
                     'bin_min_isolation_time': m.bin_min_isolation_time, 'bin_max_isolation_time': m.bin_max_isolation_time, 'bin_min_viscosity': m.bin_min_viscosity,
                     'bin_max_viscosity': m.bin_max_viscosity, 'bin_min_density': m.bin_min_density, 'bin_max_density': m.bin_max_density, 'bin_min_pressure': m.bin_min_pressure,
                     'bin_max_pressure': m.bin_max_pressure, 'bin_min_mass': m.bin_min_mass, 'bin_max_mass': m.bin_max_mass, 'bin_min_temperature': m.bin_min_temperature,
                     'bin_max_temperature': m.bin_max_temperature, 'bin_min_velocity': m.bin_min_velocity, 'bin_max_velocity': m.bin_max_velocity,
                     'opacity': m.opacity, 'hidden_camera': m.hidden_camera, 'hidden_camera_in_shadow_channel': m.hidden_camera_in_shadow_channel,
                     'hidden_global_illumination': m.hidden_global_illumination, 'hidden_reflections_refractions': m.hidden_reflections_refractions,
                     'hidden_zclip_planes': m.hidden_zclip_planes, 'object_id': self._color_to_rgb8(m.object_id),
                     'name': dp['name'], 'parent': dp['parent'],
                     
                     'material': material,
                     'material_embed': m.material_embed,
                     'backface_material': backface_material,
                     'backface_material_embed': m.backface_material_embed,
                     
                     'base': b, 'pivot': p, 'matrix': None, 'hide': m.hide, 'hide_parent': m.hide_parent, 'type': 'PARTICLES', }
            elif(dp['type'] == 'GRASS'):
                material = bpy.path.abspath(m.material)
                if(material != "" and not os.path.exists(material)):
                    log("{1}: mxm ('{0}') does not exist.".format(material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                backface_material = bpy.path.abspath(m.backface_material)
                if(backface_material != "" and not os.path.exists(backface_material)):
                    log("{1}: backface mxm ('{0}') does not exist.".format(backface_material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                
                q = {'material': material,
                     'material_embed': m.material_embed,
                     'backface_material': backface_material,
                     'backface_material_embed': m.backface_material_embed,
                     
                     'density': int(m.density), 'density_map': texture_to_data(m.density_map, ps),
                     'length': m.length, 'length_map': texture_to_data(m.length_map, ps), 'length_variation': m.length_variation,
                     'root_width': m.root_width, 'tip_width': m.tip_width,
                     'direction_type': int(m.direction_type),
                     'initial_angle': math.degrees(m.initial_angle), 'initial_angle_variation': m.initial_angle_variation, 'initial_angle_map': texture_to_data(m.initial_angle_map, ps),
                     'start_bend': m.start_bend, 'start_bend_variation': m.start_bend_variation, 'start_bend_map': texture_to_data(m.start_bend_map, ps),
                     'bend_radius': m.bend_radius, 'bend_radius_variation': m.bend_radius_variation, 'bend_radius_map': texture_to_data(m.bend_radius_map, ps),
                     'bend_angle': math.degrees(m.bend_angle), 'bend_angle_variation': m.bend_angle_variation, 'bend_angle_map': texture_to_data(m.bend_angle_map, ps),
                     'cut_off': m.cut_off, 'cut_off_variation': m.cut_off_variation, 'cut_off_map': texture_to_data(m.cut_off_map, ps),
                     'points_per_blade': int(m.points_per_blade), 'primitive_type': int(m.primitive_type), 'seed': m.seed,
                     'lod': m.lod, 'lod_min_distance': m.lod_min_distance, 'lod_max_distance': m.lod_max_distance, 'lod_max_distance_density': m.lod_max_distance_density,
                     'display_percent': int(m.display_percent), 'display_max_blades': int(m.display_max_blades),
                     
                     # pass some default to skip checks this time..
                     'opacity': 100,
                     'hidden_camera': False,
                     'hidden_camera_in_shadow_channel': False,
                     'hidden_global_illumination': False,
                     'hidden_reflections_refractions': False,
                     'hidden_zclip_planes': False,
                     'object_id': [255, 255, 255],
                     'name': dp['name'],
                     'parent': None,
                     'base': None,
                     'pivot': None,
                     'matrix': None,
                     'hide': False,
                     
                     'object': dp['parent'],
                     'type': 'GRASS', }
            elif(dp['type'] == 'HAIR'):
                material = bpy.path.abspath(m.material)
                if(material != "" and not os.path.exists(material)):
                    log("{1}: mxm ('{0}') does not exist.".format(material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                backface_material = bpy.path.abspath(m.backface_material)
                if(backface_material != "" and not os.path.exists(backface_material)):
                    log("{1}: backface mxm ('{0}') does not exist.".format(backface_material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                
                b, p = self._matrix_to_base_and_pivot(Matrix())
                
                q = {'material': material, 'material_embed': m.material_embed,
                     'backface_material': backface_material, 'backface_material_embed': m.backface_material_embed,
                     'opacity': m.opacity, 'hidden_camera': m.hidden_camera, 'hidden_camera_in_shadow_channel': m.hidden_camera_in_shadow_channel,
                     'hidden_global_illumination': m.hidden_global_illumination, 'hidden_reflections_refractions': m.hidden_reflections_refractions,
                     'hidden_zclip_planes': m.hidden_zclip_planes, 'object_id': self._color_to_rgb8(m.object_id), 'hide': m.hide,
                     'hide_parent': m.hide_parent, 'name': dp['name'], 'parent': dp['parent'], 'base': b, 'pivot': p, 'matrix': None,
                     
                     'display_percent': int(m.display_percent),
                     
                     'type': 'HAIR', }
                if(m.hair_type == 'GRASS'):
                    q['extension'] = 'MGrassP'
                    q['grass_root_width'] = maths.real_length_to_relative(o.matrix_world, m.grass_root_width) / 1000
                    q['grass_tip_width'] = maths.real_length_to_relative(o.matrix_world, m.grass_tip_width) / 1000
                    q['display_max_blades'] = m.display_max_blades
                else:
                    q['extension'] = 'MaxwellHair'
                    q['hair_root_radius'] = maths.real_length_to_relative(o.matrix_world, m.hair_root_radius) / 1000
                    q['hair_tip_radius'] = maths.real_length_to_relative(o.matrix_world, m.hair_tip_radius) / 1000
                    q['display_max_hairs'] = m.display_max_hairs
                
                '''
                o = bpy.data.objects[q['parent']]
                ps.set_resolution(self.context.scene, o, 'RENDER')
                
                mat = Matrix.Rotation(math.radians(-90.0), 4, 'X')
                transform = o.matrix_world.inverted()
                
                steps = 2 ** ps.settings.render_step
                num_curves = len(ps.particles) if len(ps.child_particles) == 0 else len(ps.child_particles)
                locs = []
                for p in range(0, num_curves):
                    for step in range(0, steps):
                        co = ps.co_hair(o, p, step)
                        v = transform * co
                        v = mat * v
                        locs.extend([v.x, v.y, v.z])
                
                ps.set_resolution(self.context.scene, o, 'PREVIEW')
                '''
                
                # get fresh object reference
                # FIXME why the it has been somewhere lost??? remove this line will result in segmentation fault
                o = bpy.data.objects[q['parent']]
                ps.set_resolution(self.context.scene, o, 'RENDER')
                
                mat = Matrix.Rotation(math.radians(-90.0), 4, 'X')
                transform = o.matrix_world.inverted()
                omw = o.matrix_world
                
                steps = 2 ** ps.settings.render_step
                num_curves = len(ps.particles) if len(ps.child_particles) == 0 else len(ps.child_particles)
                points = []
                for p in range(0, num_curves):
                    seg_length = 1.0
                    curve = []
                    
                    for step in range(0, steps):
                        co = ps.co_hair(o, p, step)
                        
                        # get distance between last and this point
                        if(step > 0):
                            seg_length = (co - omw * curve[len(curve) - 1]).length_squared
                        
                        if not (co.length_squared == 0 or seg_length == 0):
                            # if it is not zero append as new point
                            v = transform * co
                            v = mat * v
                            curve.append(v)
                    
                    points.append(curve)
                
                ps.set_resolution(self.context.scene, o, 'PREVIEW')
                
                # fill gaps with last location, confirm it has no negative effect in rendering..
                for l in points:
                    if(len(l) < steps):
                        e = [l[-1]] * (steps - len(l))
                        l.extend(e)
                # flatten curves
                points = [v for l in points for v in l]
                # 3 float tuples from vectors
                points = [v.to_tuple() for v in points]
                # just list of floats
                locs = [v for l in points for v in l]
                
                p = os.path.join(self.tmp_dir, "{0}.binhair".format(q['name']))
                w = MXSBinHairWriter(p, locs)
                q['hair_data_path'] = p
                self.hair_data_paths.append(p)
                
                data = {'HAIR_MAJOR_VER': [1, 0, 0, 0],
                        'HAIR_MINOR_VER': [0, 0, 0, 0],
                        'HAIR_FLAG_ROOT_UVS': [0],
                        'HAIR_GUIDES_COUNT': [num_curves],
                        'HAIR_GUIDES_POINT_COUNT': [steps],
                        # 'HAIR_POINTS': locs,
                        'HAIR_NORMALS': [1.0], }
                
                # print(data['HAIR_GUIDES_COUNT'])
                # print(data['HAIR_GUIDES_POINT_COUNT'])
                # print(len(data['HAIR_POINTS']))
                # print(len(data['HAIR_POINTS']) == (num_curves * steps * 3))
                
                q['data'] = data
                
            else:
                raise TypeError("Unsupported particles type: {}".format(dp['type']))
            
            if(q is not None):
                self.data.append(q)
    
    def _pymaxwell(self, append=False, instancer=False, wireframe=False, ):
        """Generate pymaxwell script in temp directory and execute it."""
        # generate script
        self.script_path = os.path.join(self.tmp_dir, self.script_name)
        with open(self.script_path, mode='w', encoding='utf-8') as f:
            # read template
            with open(self.TEMPLATE, encoding='utf-8') as t:
                code = "".join(t.readlines())
            # write template to a new file
            f.write(code)
        
        s = platform.system()
        if(s == 'Darwin' or s == 'Linux'):
            switches = ''
            if(append):
                switches += '-a'
            # if(particles):
            #     if(switches != ''):
            #         switches += ' '
            #     switches += '-p'
            if(instancer):
                if(switches != ''):
                    switches += ' '
                switches += '-i'
            if(wireframe):
                if(switches != ''):
                    switches += ' '
                switches += '-w'
            
            # if(QUIET):
            #     if(switches != ''):
            #         switches += ' '
            #     switches += '-q'
            
            if(switches != ''):
                command_line = "{0} {1} {2} {3} {4} {5}".format(shlex.quote(self.PY),
                                                                shlex.quote(self.script_path),
                                                                switches,
                                                                shlex.quote(LOG_FILE_PATH),
                                                                shlex.quote(self.scene_data_path),
                                                                shlex.quote(self.mxs_path), )
            else:
                command_line = "{0} {1} {2} {3} {4}".format(shlex.quote(self.PY),
                                                            shlex.quote(self.script_path),
                                                            shlex.quote(LOG_FILE_PATH),
                                                            shlex.quote(self.scene_data_path),
                                                            shlex.quote(self.mxs_path), )
            
            log("command:", 2)
            log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
            args = shlex.split(command_line, )
            o = subprocess.call(args, )
            if(o != 0):
                log("error in {0}".format(self.script_path), 0, LogStyles.ERROR, )
                raise Exception("error in {0}".format(self.script_path))
        elif(s == 'Windows'):
            pass
        else:
            raise OSError("Unknown platform: {}.".format(s))
    
    def _cleanup(self):
        """Remove all intermediate products."""
        if(self.keep_intermediates):
            return
        
        # remove script, data files and temp directory
        def rm(p):
            if(os.path.exists(p)):
                os.remove(p)
            else:
                log("{1}: WARNING: _cleanup(): {0} does not exist?".format(p, self.__class__.__name__), 1, LogStyles.WARNING, )
        
        rm(self.script_path)
        rm(self.scene_data_path)
        
        if(hasattr(self, 'mesh_data_paths')):
            for p in self.mesh_data_paths:
                rm(p)
        
        if(hasattr(self, 'wire_base_data')):
            rm(self.wire_base_data)
            for p in self.wire_data_paths:
                rm(p)
        
        if(hasattr(self, 'hair_data_paths')):
            for p in self.hair_data_paths:
                rm(p)
        
        if(os.path.exists(self.tmp_dir)):
            os.rmdir(self.tmp_dir)
        else:
            log("{1}: WARNING: _cleanup(): {0} does not exist?".format(self.tmp_dir, self.__class__.__name__), 1, LogStyles.WARNING, )


class MXSExportWireframe(MXSExport):
    """Maxwell Render (.mxs) wireframe scene export
    Docs:
    """
    # TODO (very low priority) support for various clay and wire materials on objects
    
    def __init__(self, context, mxs_path, use_instances=True, keep_intermediates=False, edge_radius=0.00025, edge_resolution=32, wire_mat={}, clay_mat={}, ):
        """
        context: bpy.context
        mxs_path: path where .mxs should be saved
        use_instances: if True all multi user meshes and duplis are exported as instances
        keep_intermediates: if True, temp files and directory will not be removed
        edge_radius: wire edge (cylinder) radius in meters
        edge_radius: wire edge (cylinder) resolution
        wire_mat: wireframe material, format: {'reflectance_0': (r, g, b), 'reflectance_90': (r, g, b), 'id': (r, g, b), }, r, g, b in 8bit 0-255 values
        clay_mat: clay material, format: {'reflectance_0': (r, g, b), 'reflectance_90': (r, g, b), 'id': (r, g, b), }, r, g, b in 8bit 0-255 values
        """
        self.edge_radius = edge_radius
        self.edge_resolution = edge_resolution
        try:
            v = wire_mat['reflectance_0']
            v = wire_mat['reflectance_90']
            v = wire_mat['roughness']
            v = wire_mat['id']
        except KeyError:
            r0 = 20
            r90 = 45
            wire_mat = {'reflectance_0': (r0, r0, r0, ), 'reflectance_90': (r90, r90, r90, ), 'id': (0, 255, 0), 'roughness': 97.0, }
        try:
            v = clay_mat['reflectance_0']
            v = clay_mat['reflectance_90']
            v = clay_mat['roughness']
            v = clay_mat['id']
        except KeyError:
            r0 = 210
            r90 = 230
            clay_mat = {'reflectance_0': (r0, r0, r0, ), 'reflectance_90': (r90, r90, r90, ), 'id': (255, 0, 0), 'roughness': 97.0, }
        self.wire_mat = wire_mat
        self.clay_mat = clay_mat
        
        super(MXSExportWireframe, self).__init__(context, mxs_path, use_instances, keep_intermediates, )
    
    def _export(self):
        log("collecting objects..", 1)
        self.tree = self._collect()
        
        self.uuid = uuid.uuid1()
        h, t = os.path.split(self.mxs_path)
        n, e = os.path.splitext(t)
        self.tmp_dir = os.path.join(h, "{0}-tmp-{1}".format(n, self.uuid))
        if(os.path.exists(self.tmp_dir) is False):
            os.makedirs(self.tmp_dir)
        
        self.mesh_data_paths = []
        self.wire_data_paths = []
        self.scene_data_name = "{0}-{1}.json".format(n, self.uuid)
        self.script_name = "{0}-{1}.py".format(n, self.uuid)
        
        # coordinate conversion matrix
        # m = io_utils.axis_conversion(from_forward='Y', to_forward='-Z', from_up='Z', to_up='Y').to_4x4()
        # print(repr(m))
        self.matrix = Matrix(((1.0, 0.0, 0.0, 0.0),
                              (0.0, 0.0, 1.0, 0.0),
                              (0.0, -1.0, 0.0, 0.0),
                              (0.0, 0.0, 0.0, 1.0)))
        
        # process:
        self.data = []
        
        # add materials before anything else, this way they will be later available to be used
        d = {'name': 'wire',
             'type': 'WIREFRAME_MATERIAL',
             'data': self.wire_mat, }
        self.data.append(d)
        d = {'name': 'clay',
             'type': 'WIREFRAME_MATERIAL',
             'data': self.clay_mat, }
        self.data.append(d)
        
        # write regular scene objects
        self._export_data()
        
        # rewrite material data to none and add material property
        for d in self.data:
            try:
                mps = d['mxm_paths']
                nmps = []
                for i, mp in enumerate(mps):
                    nmps.append((i, '', ))
                d['mxm_paths'] = nmps
                # d['material'] = self.clay_mat
            except KeyError:
                pass
        
        # wireframe
        log("making wire base mesh..", 1, LogStyles.MESSAGE)
        self._wire_base()
        log("processing wires..", 1, LogStyles.MESSAGE)
        self._wire_objects()
        
        self._scene_properties()
        
        # save main data, meshes are already saved
        p = self._serialize(self.data, self.scene_data_name)
        self.scene_data_path = p
        
        # generate and execute py32 script
        log("executing script..", 1, LogStyles.MESSAGE)
        self._pymaxwell(wireframe=True)
        
        # remove all generated files
        log("cleanup..", 1, LogStyles.MESSAGE)
        self._cleanup()
        
        log("mxs saved in:", 1)
        log("{0}".format(self.mxs_path), 0, LogStyles.MESSAGE, prefix="")
        log("done.", 1, LogStyles.MESSAGE)
        
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.tree)
    
    def _wire_base(self):
        """Create and set to export base wire edge cylinder."""
        gen = utils.CylinderMeshGenerator(height=1, radius=self.edge_radius, sides=self.edge_resolution, )
        n = "wireframe_edge_{0}".format(self.uuid)
        me = bpy.data.meshes.new(n)
        v, e, f = gen.generate()
        me.from_pydata(v, [], f)
        log("{0}".format(n), 2)
        ob = utils.add_object(n, me)
        o = {'object': ob,
             'children': [],
             'export': True,
             'export_type': 'MESH',
             'mesh': ob.data,
             'converted': False,
             'parent': None,
             'hide': False,
             'type': ob.type, }
        d, md = self._mesh_to_data(o)
        d['type'] = 'WIREFRAME_EDGE'
        
        p = os.path.join(self.tmp_dir, "{0}.binmesh".format(md['name']))
        w = MXSBinMeshWriter(p, md, d['num_positions_per_vertex'])
        
        self.wire_base_data = p
        d['mesh_data_path'] = p
        self.data.append(d)
        self.wireframe_edge_name = ob.name
        utils.wipe_out_object(ob, and_data=True)
    
    def _wire_objects(self):
        """Loop over all renderable objects and prepare wire data for pymaxwell."""
        eo = self.meshes[:] + self.bases[:] + self.instances[:] + self.duplicates[:]
        for o in eo:
            log("{0}".format(o['object'].name), 2)
            d, md = self._wire_to_data(o)
            nm = md['name']
            try:
                # duplicates are handled differently
                nm = o['dupli_name']
            except KeyError:
                pass
            p = self._serialize(md, "{0}.json".format(nm))
            self.mesh_data_paths.append(p)
            d['matrices_path'] = p
            self.data.append(d)
    
    def _wire_to_data(self, o):
        """Make wire data from object data."""
        ob = o['object']
        me = ob.to_mesh(self.context.scene, True, 'RENDER', )
        mw = ob.matrix_world
        try:
            # duplicates are handled differently
            mw = o['dupli_matrix']
        except KeyError:
            pass
        me.transform(mw)
        
        vs = tuple([v.co.copy() for v in me.vertices])
        es = tuple([tuple([i for i in e.vertices]) for e in me.edges])
        
        prgr = progress.get_progress(len(es), 2)
        
        ms = self._calc_marices(vs=vs, es=es, prgr=prgr, )
        
        dt = []
        for m in ms:
            b, p = self._matrix_to_base_and_pivot(m)
            dt.append((b, p, ))
        
        d = {'name': ob.name,
             'matrix': None,
             'parent': None,
             
             'opacity': 100.0,
             'hidden_camera': False,
             'hidden_camera_in_shadow_channel': False,
             'hidden_global_illumination': False,
             'hidden_reflections_refractions': False,
             'hidden_zclip_planes': False,
             'object_id': (255, 255, 255),
             
             'num_materials': len(ob.material_slots),
             'materials': [],
             
             'hide': False,
             
             'instanced': None,
             'type': 'INSTANCE', }
        
        d['name'] = "{0}-wire".format(ob.name)
        d['instanced'] = self.wireframe_edge_name
        d['object_id'] = self.wire_mat['id']
        d['type'] = 'WIREFRAME'
        
        md = {'name': "{0}-wire".format(ob.name),
              'matrices': dt, }
        
        bpy.data.meshes.remove(me)
        return d, md
    
    def _calc_marices(self, vs, es, prgr, ):
        """Calculate wire matrices."""
        
        def distance(a, b):
            return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
        
        matrices = []
        up = Vector((0, 0, 1))
        for i, e in enumerate(es):
            a = vs[e[0]]
            b = vs[e[1]]
            d = distance(a, b)
            
            # v1
            quat = maths.rotation_to(Vector((0, 0, 1)), b - a)
            mr = quat.to_matrix().to_4x4()
            mt = Matrix.Translation(a)
            mtr = mt * mr
            
            # # v2
            # mtr = maths.look_at_matrix(a, Vector(maths.shift_vert_along_normal(a, b-a, -1.0)), up, )
            
            # add scale as well
            ms = Matrix.Scale(d, 4, up)
            m = mtr * ms
            matrices.append(m)
            #
            prgr.step()
        return matrices


class MXSBinMeshWriter():
    def __init__(self, path, mesh, steps):
        m = mesh
        o = "@"
        with open("{0}.tmp".format(path), 'wb') as f:
            p = struct.pack
            fw = f.write
            # header
            fw(p(o + "7s", 'BINMESH'.encode('utf-8')))
            fw(p(o + "?", False))
            # name 250 max length
            fw(p(o + "250s", m['name'].encode('utf-8')))
            # number of steps
            fw(p(o + "i", steps))
            # number of vertices
            vn = len(m['v_setVertex'])
            fw(p(o + "i", vn))
            # vertex (int id, int step, (float x, float y, float z))
            for i in range(vn):
                v = m['v_setVertex'][i]
                fw(p(o + "2i", v[0], v[1]))
                fw(p(o + "3d", v[2][0], v[2][1], v[2][2]))
            # vertex normal (int id, int step, (float x, float y, float z))
            for i in range(vn):
                v = m['v_setNormal'][i]
                fw(p(o + "2i", v[0], v[1]))
                fw(p(o + "3d", v[2][0], v[2][1], v[2][2]))
            # number of triangles
            tn = len(m['f_setTriangle'])
            fw(p(o + "i", tn))
            # number of uv channels
            un = len(m['channel_uvw'])
            fw(p(o + "i", un))
            # uv channel ids
            for i in range(len(m['channel_uvw'])):
                fw(p(o + "i", m['channel_uvw'][i]))
            # triangles (int id, (int v1, int v2, int v3), (int n1, int n2, int n3))
            for i in range(tn):
                t = m['f_setTriangle'][i]
                fw(p(o + "i", t[0]))
                fw(p(o + "3i", t[1][0], t[1][1], t[1][2]))
                fw(p(o + "3i", t[2][0], t[2][1], t[2][2]))
            # triangle normals (int id, int step, (float x, float y, float z))
            for i in range(tn):
                v = m['f_setNormal'][i]
                fw(p(o + "2i", v[0], v[1]))
                fw(p(o + "3d", v[2][0], v[2][1], v[2][2]))
            # triangle materials (int id, int material)
            for i in range(tn):
                v = m['f_setTriangleMaterial'][i]
                fw(p(o + "2i", v[0], v[1]))
            # uvs
            for i in range(un * tn):
                # (int id, int channel id, float u1, float v1, float w1, float u2, float v2, float w3, float u3, float v3, float w3)
                u = m['f_setTriangleUVW'][i]
                fw(p(o + "2i", u[0], u[1]))
                fw(p(o + "3d", u[2], u[3], u[4]))
                fw(p(o + "3d", u[5], u[6], u[7]))
                fw(p(o + "3d", u[8], u[9], u[10]))
            # end
            fw(p(o + "?", False))
        
        if(os.path.exists(path)):
            os.remove(path)
        shutil.move("{0}.tmp".format(path), path)
        self.path = path


class MXSBinMeshReader():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        # signature = 0x004853454D4E4942
        signature = 20357755437992258
        l = r("<q")[0]
        self.offset = 0
        b = r(">q")[0]
        self.offset = 0
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            self.order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            self.order = ">"
        else:
            raise AssertionError("{}: not a MXSBinMesh file".format(self.__class__.__name__))
        o = self.order
        
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINMESH'):
            raise RuntimeError()
        _ = r(o + "?")
        # mesh name
        self.name = r(o + "250s")[0].decode(encoding="utf-8").replace('\x00', '')
        # number of steps
        self.steps = r(o + "i")[0]
        # number of vertices
        self.num_vertices = r(o + "i")[0]
        # vertices
        self.vertices = []
        for i in range(self.num_vertices * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.vertices.append(v)
        # vertex normals
        self.vertices_normals = []
        for i in range(self.num_vertices * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.vertices_normals.append(v)
        # number of triangles
        self.num_triangles = r(o + "i")[0]
        # number of uv channels
        self.num_channels = r(o + "i")[0]
        # uv channels ids
        self.uv_channels = []
        for i in range(self.num_channels):
            self.uv_channels.append(r(o + "i")[0])
        # triangles
        self.triangles = []
        for i in range(self.num_triangles):
            # triangles (int id, (int v1, int v2, int v3), (int n1, int n2, int n3))
            v = (r(o + "i")[0], r(o + "3i"), r(o + "3i"))
            self.triangles.append(v)
        # triangle normals (int id, int step, (float x, float y, float z))
        self.triangles_normals = []
        for i in range(self.num_triangles * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.triangles_normals.append(v)
        # triangle material assigment
        self.triangles_materials = []
        for i in range(self.num_triangles):
            # int id, int material slot/id
            v = (r(o + "i")[0], r(o + "i")[0])
            self.triangles_materials.append(v)
        # uvs
        self.triangles_uvs = []
        for i in range(self.num_triangles * self.num_channels):
            # (int id, int channel id, float u1, float v1, float w1, float u2, float v2, float w3, float u3, float v3, float w3)
            v = (r(o + "i")[0], r(o + "i")[0]) + r(o + "9d")
            self.triangles_uvs.append(v)
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")
        
        self.data = {'channel_uvw': self.uv_channels[:],
                     'f_setNormal': self.triangles_normals[:],
                     'f_setTriangle': self.triangles[:],
                     'f_setTriangleMaterial': self.triangles_materials[:],
                     'f_setTriangleUVW': self.triangles_uvs[:],
                     'name': str(self.name),
                     'v_setNormal': self.vertices_normals[:],
                     'v_setVertex': self.vertices[:], }


class MXSBinHairWriter():
    def __init__(self, path, data):
        d = data
        o = "@"
        with open("{0}.tmp".format(path), 'wb') as f:
            p = struct.pack
            fw = f.write
            # header
            fw(p(o + "7s", 'BINHAIR'.encode('utf-8')))
            fw(p(o + "?", False))
            # number of floats
            n = len(d)
            fw(p(o + "i", n))
            # floats
            fw(p(o + "{}d".format(n), *d))
            # end
            fw(p(o + "?", False))
        if(os.path.exists(path)):
            os.remove(path)
        shutil.move("{0}.tmp".format(path), path)
        self.path = path


class MXSBinHairReader():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        signature = 23161492825065794
        l = r("<q")[0]
        self.offset = 0
        b = r(">q")[0]
        self.offset = 0
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            self.order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            self.order = ">"
        else:
            raise AssertionError("{}: not a MXSBinHair file".format(self.__class__.__name__))
        o = self.order
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINHAIR'):
            raise RuntimeError()
        _ = r(o + "?")
        # number floats
        self.num = r(o + "i")[0]
        self.data = r(o + "{}d".format(self.num))
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")
