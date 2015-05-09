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
import uuid
import shutil
import struct
import json
import sys
import re

import bpy
from mathutils import Matrix, Vector
from bpy_extras import io_utils
import bmesh

from .log import log, LogStyles
from . import utils
from . import maths
from . import system
from . import rfbin
from . import mxs


class MXSExportLegacy():
    def __init__(self, context, mxs_path, use_instances=True, keep_intermediates=False, ):
        """
        context: bpy.context
        mxs_path: path where .mxs should be saved
        use_instances: if True all multi user meshes and duplis are exported as instances
        keep_intermediates: if True, temp files and directory will not be removed
        """
        # # check for pymaxwell
        # system.check_for_pymaxwell()
        
        # # check for template
        # self.TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "write_mxs.py")
        # if(not os.path.exists(self.TEMPLATE)):
        #     log("{}: ERROR: support directory is missing..".format(self.__class__.__name__), 1, LogStyles.ERROR, )
        #     raise OSError("support directory is missing..")
        self.TEMPLATE = system.check_for_template()
        
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
        self.part_data_paths = []
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
                if(o.maxwell_render_reference.enabled):
                    t = 'REFERENCE'
                elif(o.maxwell_volumetrics_extension.enabled):
                    t = 'VOLUMETRICS'
                else:
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
        append_types = ['MESH', 'BASE_INSTANCE', 'INSTANCE', 'REFERENCE', 'VOLUMETRICS', ]
        
        def check_renderables_in_tree(oo):
            ov = []
            
            def walk(o):
                for c in o['children']:
                    walk(c)
                if((o['export_type'] in append_types) and o['export'] is True):
                    # keep instances (Maxwell 3)
                    # keep: meshes, bases - both with export: True
                    # (export: False are hidden objects, and should be already swapped to empties if needed for hiearchy)
                    # > meshes..
                    # > bases can have children, bases are real meshes
                    ov.append(True)
                else:
                    # remove: empties, bases, instances, suns, meshes and bases with export: False (hidden objects) and reference enabled: False
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
        references = []
        volumetrics = []
        
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
                elif(o['export_type'] == 'REFERENCE'):
                    references.append(o)
                elif(o['export_type'] == 'VOLUMETRICS'):
                    volumetrics.append(o)
        
        for o in h:
            walk(o)
        
        self.meshes = meshes
        self.bases = bases
        self.instances = instances
        self.empties = empties
        self.cameras = cameras
        self.references = references
        self.volumetrics = volumetrics
        
        # no visible camera
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
        
        # find instances without base and change first one to base, quick and dirty..
        # this case happens when object (by name chosen as base) is on hidden layer and marked to be not exported
        # also, hope this is the last change of this nasty piece of code..
        def find_base_object_name(mnm):
            for bo in self.bases:
                if(bo['mesh'].name == mnm):
                    return bo['object'].name
        
        instances2 = self.instances[:]
        for o in instances2:
            if(find_base_object_name(o['mesh'].name) is None):
                o['export_type'] = 'BASE_INSTANCE'
                self.bases.append(o)
                self.instances.remove(o)
        
        # overriden instances
        instances2 = self.instances[:]
        for o in instances2:
            m = o['object'].maxwell_render
            if(m.override_instance):
                o['export_type'] = 'MESH'
                o['override_instance'] = o['object'].data
                self.meshes.append(o)
                self.instances.remove(o)
        
        # ----------------------------------------------------------------------------------
        # (everything above this line is pure magic, below is just standard code)
        
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(h)
        
        # print("-" * 100)
        # raise Exception()
        
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
                 'export_protect_mxs': False,
                 
                 'extra_sampling_enabled': False,
                 'extra_sampling_sl': 14.0,
                 'extra_sampling_mask': '',
                 'extra_sampling_custom_alpha': '',
                 'extra_sampling_user_bitmap': '',
                 'extra_sampling_invert': False,
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
            
            scene['export_protect_mxs'] = mx.export_protect_mxs
            
            scene['extra_sampling_enabled'] = mx.extra_sampling_enabled
            scene['extra_sampling_sl'] = mx.extra_sampling_sl
            scene['extra_sampling_mask'] = int(mx.extra_sampling_mask[-1:])
            scene['extra_sampling_custom_alpha'] = mx.extra_sampling_custom_alpha
            scene['extra_sampling_user_bitmap'] = bpy.path.abspath(mx.extra_sampling_user_bitmap)
            scene['extra_sampling_invert'] = mx.extra_sampling_invert
        
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
                if(sun is None):
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
        
        log("processing references..", 1, LogStyles.MESSAGE)
        self._references()
        
        log("processing volumetrics..", 1, LogStyles.MESSAGE)
        self._volumetrics()
        
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
                        if(mmx.use == 'CUSTOM'):
                            fm = bpy.path.abspath(mmx.mxm_file)
                            if(not check_path(fm)):
                                fm = ""
                            if(fm != ""):
                                a = (mmx.embed, fm)
                            else:
                                a = (False, "", )
                        else:
                            a = self._ext_material(s.material, ob)
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
                        if(mmx.use == 'CUSTOM'):
                            fm = bpy.path.abspath(mmx.mxm_file)
                            if(not check_path(fm)):
                                fm = ""
                            if(fm != ""):
                                a = (mmx.embed, fm)
                            else:
                                a = (False, "", )
                        else:
                            a = self._ext_material(s.material, ob)
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
        
        # nm = ob.data.name
        nm = "{}-{}".format(ob.data.name, uuid.uuid1())
        if(self.use_instances is False):
            # nm = ob.name
            nm = "{}-{}".format(ob.name, uuid.uuid1())
        
        # md = {'name': nm,
        #       'channel_uvw': [],
        #       'v_setVertex': [],
        #       'v_setNormal': [],
        #       'f_setNormal': [],
        #       'f_setTriangle': [],
        #       'f_setTriangleUVW': [],
        #       'f_setTriangleMaterial': [], }
        
        d = {'name': ob.name,
             'num_vertexes': len(me.vertices),
             'num_normals': len(me.vertices) + len(me.tessfaces),
             'num_triangles': len(me.tessfaces),
             'num_positions_per_vertex': 1,
             'mesh_data': nm,
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
        
        # # mesh data
        # for ti, uvt in enumerate(me.uv_textures):
        #     md['channel_uvw'].append(ti)
        #
        # # vertices, vertex normals
        # for i, v in enumerate(me.vertices):
        #     # index, position index, vector
        #     md['v_setVertex'].append((i, 0, v.co.to_tuple(), ))
        #     # index, position index, vector
        #     md['v_setNormal'].append((i, 0, v.normal.to_tuple(), ))
        #
        # # faces, face normals, uvs
        # ni = len(me.vertices) - 1
        # ti = 0
        #
        # for fi, f in enumerate(me.tessfaces):
        #     ni = ni + 1
        #     # normal
        #     md['f_setNormal'].append((ni, 0, f.normal.to_tuple(), ))
        #     fv = f.vertices
        #     # smoothing
        #     if(f.use_smooth):
        #         # vertex normals
        #         nix = [fv[0], fv[1], fv[2]]
        #     else:
        #         # face normal
        #         nix = [ni, ni, ni, ]
        #     # geometry
        #     md['f_setTriangle'].append((ti, (fv[0], fv[1], fv[2]), (nix[0], nix[1], nix[2]), ))
        #     md['f_setTriangleMaterial'].append((ti, f.material_index, ))
        #     # uv
        #     for tix, uvtex in enumerate(me.tessface_uv_textures):
        #         uv = uvtex.data[fi].uv
        #         md['f_setTriangleUVW'].append((ti, tix,
        #                                        uv[0][0], 1.0 - uv[0][1], 0.0,
        #                                        uv[1][0], 1.0 - uv[1][1], 0.0,
        #                                        uv[2][0], 1.0 - uv[2][1], 0.0, ))
        #     ti = ti + 1
        
        vertices = [[v.co.to_tuple() for v in me.vertices], ]
        normals = [[v.normal.to_tuple() for v in me.vertices], ]
        
        triangles = []
        triangle_normals = []
        ni = len(me.vertices) - 1
        tns = []
        for fi, f in enumerate(me.tessfaces):
            ni = ni + 1
            tns.append(f.normal.to_tuple())
            fv = f.vertices
            # smoothing
            if(f.use_smooth):
                # vertex normals
                nix = (fv[0], fv[1], fv[2], )
            else:
                # face normal
                nix = (ni, ni, ni, )
            t = tuple(fv) + nix
            triangles.append(t)
        
        triangle_normals.append(tns)
        
        uv_channels = []
        for tix, uvtex in enumerate(me.tessface_uv_textures):
            uv = []
            for fi, f in enumerate(me.tessfaces):
                duv = uvtex.data[fi].uv
                uv.append((duv[0][0], 1.0 - duv[0][1], 0.0, duv[1][0], 1.0 - duv[1][1], 0.0, duv[2][0], 1.0 - duv[2][1], 0.0, ))
            uv_channels.append(uv)
        
        num_materials = len(ob.material_slots)
        
        triangle_materials = []
        for fi, f in enumerate(me.tessfaces):
            triangle_materials.append((fi, f.material_index, ))
        
        md = {'name': nm,
              'num_positions': 1,
              'vertices': vertices,
              'normals': normals,
              'triangles': triangles,
              'triangle_normals': triangle_normals,
              'uv_channels': uv_channels,
              'num_materials': num_materials,
              'triangle_materials': triangle_materials, }
        
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
            if(sc.scatter_object is ''):
                log("{}: no scatter object, skipping Maxwell Scatter modifier..".format(ob.name), 3, LogStyles.WARNING, )
                d['scatter_ext'] = None
            else:
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
        
        ms = ob.maxwell_sea_extension
        if(ms.enabled):
            name = "{}-MaxwellSea".format(ob.name)
            d['sea_ext'] = [name, ms.hide_parent, ms.reference_time, int(ms.resolution), ms.ocean_depth, ms.vertical_scale, ms.ocean_dim,
                            ms.ocean_seed, ms.enable_choppyness, ms.choppy_factor, ms.ocean_wind_mod, math.degrees(ms.ocean_wind_dir),
                            ms.ocean_wind_alignment, ms.ocean_min_wave_length, ms.damp_factor_against_wind, ms.enable_white_caps, ]
        else:
            d['sea_ext'] = None
        
        return d, md
    
    def _meshes(self):
        """Loop over all mesh objects and prepare data for pymaxwell."""
        for o in self.meshes:
            log("{0}".format(o['object'].name), 2)
            
            is_overriden_instance = False
            try:
                o['override_instance']
                is_overriden_instance = True
            except:
                pass
            
            if(is_overriden_instance):
                o['object'].data = o['object'].data.copy()
                d, md = self._mesh_to_data(o)
                p = os.path.join(self.tmp_dir, "{0}.binmesh".format(md['name']))
                # w = MXSBinMeshWriterLegacy(p, md, d['num_positions_per_vertex'])
                w = MXSBinMeshWriterLegacy(p, **md)
                rm = o['object'].data
                o['object'].data = o['override_instance']
                bpy.data.meshes.remove(rm)
            else:
                d, md = self._mesh_to_data(o)
                p = os.path.join(self.tmp_dir, "{0}.binmesh".format(md['name']))
                # w = MXSBinMeshWriterLegacy(p, md, d['num_positions_per_vertex'])
                w = MXSBinMeshWriterLegacy(p, **md)
            
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
            # w = MXSBinMeshWriterLegacy(p, md, d['num_positions_per_vertex'])
            w = MXSBinMeshWriterLegacy(p, **md)
            
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
        
        for o in self.duplicates:
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
                                 'object': o.name,
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
                                 'object': o.name,
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
                                 'object': o.name,
                                 'parent': parent, }
                            self.particles.append(d)
                    elif(ps.settings.maxwell_render.use == 'CLONER'):
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
                            d = {'props': ps.settings.maxwell_cloner_extension,
                                 # 'matrix': o.matrix_local,
                                 'matrix': Matrix(),
                                 'type': ps.settings.maxwell_render.use,
                                 'ps': ps,
                                 'name': "{}-{}".format(o.name, ps.name),
                                 # 'pmatrix': o.matrix_local,
                                 'pmatrix': Matrix(),
                                 'object': o.name,
                                 'parent': o.name, }
                            self.particles.append(d)
                    else:
                        pass
        
        def texture_to_data(name, ps, ob=None, ):
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
            if(tex is not None and ob is not None and ps is not None):
                m = tex.maxwell_render
                d['type'] = 'IMAGE'
                d['path'] = bpy.path.abspath(tex.image.filepath)
                
                d['channel'] = 0
                
                ts = None
                for i, t in enumerate(ps.settings.texture_slots):
                    if(t.texture == tex):
                        ts = t
                        break
                
                for i, uv in enumerate(ob.data.uv_textures):
                    if(uv.name == ts.uv_layer):
                        d['channel'] = i
                        break
                
                d['use_override_map'] = m.use_global_map
                if(m.tiling_method == 'NO_TILING'):
                    tm = [False, False]
                elif(m.tiling_method == 'TILE_X'):
                    tm = [True, False]
                elif(m.tiling_method == 'TILE_Y'):
                    tm = [False, True]
                else:
                    tm = [True, True]
                d['tile_method_type'] = tm
                d['tile_method_units'] = int(m.tiling_units[-1:])
                d['repeat'] = [m.repeat[0], m.repeat[1]]
                d['mirror'] = [m.mirror_x, m.mirror_y]
                d['offset'] = [m.offset[0], m.offset[1]]
                d['rotation'] = m.rotation
                d['invert'] = m.invert
                d['alpha_only'] = m.use_alpha
                d['interpolation'] = m.interpolation
                d['brightness'] = m.brightness
                d['contrast'] = m.contrast
                d['saturation'] = m.saturation
                d['hue'] = m.hue
                d['rgb_clamp'] = [m.clamp[0], m.clamp[1]]
                return d
            return None
        
        for dp in self.particles:
            skip = False
            
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
                
                pdata = {}
                
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
                    sizes = []
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
                            # size per particle
                            if(m.bl_use_size):
                                sizes.append(part.size / 2)
                            else:
                                sizes.append(m.bl_size / 2)
                    locs = maths.apply_matrix_for_realflow_bin_export(locs)
                    vels = maths.apply_matrix_for_realflow_bin_export(vels)
                    particles = []
                    for i, ploc in enumerate(locs):
                        # # v1
                        # particles.append(rfbin.RFBinParticleLegacy(pid=i, position=ploc[:3], velocity=vels[i][:3]))
                        # # v2
                        # particles.append((i, ) + tuple(ploc[:3]) + (0.0, 0.0, 0.0) + tuple(vels[i][:3]) + (sizes[i], ))
                        # v3
                        # normal from velocity
                        pnor = Vector(vels[i][:3])
                        pnor.normalize()
                        particles.append((i, ) + tuple(ploc[:3]) + pnor.to_tuple() + tuple(vels[i][:3]) + (sizes[i], ))
                    
                    if(m.embed):
                        plocs = [v[:3] for v in locs]
                        pvels = [v[3:6] for v in vels]
                        pnors = []
                        for i, v in enumerate(pvels):
                            n = Vector(v)
                            n.normalize()
                            pnors.append(n)
                        
                        pdata = {'PARTICLE_POSITIONS': [v for l in plocs for v in l],
                                 'PARTICLE_SPEEDS': [v for l in pvels for v in l],
                                 'PARTICLE_RADII': [v for v in sizes],
                                 'PARTICLE_IDS': [i for i in range(len(locs))],
                                 'PARTICLE_NORMALS': [v for l in pnors for v in l],
                                 # 'PARTICLE_FLAG_COLORS', [0], 0, 0, '8 BYTEARRAY', 1, 1, True)
                                 # 'PARTICLE_COLORS', [0.0], 0.0, 0.0, '6 FLOATARRAY', 4, 1, True)
                                 }
                        
                    else:
                        if(os.path.exists(bpy.path.abspath(m.bin_directory)) and not m.bin_overwrite):
                            raise OSError("file: {} exists".format(bpy.path.abspath(m.bin_directory)))
                    
                        cf = self.context.scene.frame_current
                        prms = {'directory': bpy.path.abspath(m.bin_directory),
                                'name': "{}".format(dp['name']),
                                'frame': cf,
                                'particles': particles,
                                'fps': self.context.scene.render.fps,
                                'size': 1.0 if m.bl_use_size else m.bl_size / 2, }
                        # # v1
                        # rfbw = rfbin.RFBinWriterLegacy(**prms)
                        # v2, v3
                        rfbw = rfbin.RFBinWriter(**prms)
                        m.bin_filename = rfbw.path
                        
                else:
                    # external particles
                    if(m.bin_type == 'SEQUENCE'):
                        # sequence
                        cf = self.context.scene.frame_current
                        if(m.seq_limit):
                            # get frame number from defined range
                            rng = [i for i in range(m.seq_start, m.seq_end + 1)]
                            try:
                                gf = rng[cf - 1]
                            except IndexError:
                                # current frame is out of limits, skip
                                skip = True
                                gf = -1
                        else:
                            gf = cf
                        if(gf >= 0):
                            # try to find correct bin
                            m.private_bin_filename = m.bin_filename
                            sqpath = bpy.path.abspath(m.bin_filename)
                            fnm_re = r'^.*\d{5}\.bin$'
                            dnm, fnm = os.path.split(sqpath)
                            if(re.match(fnm_re, fnm)):
                                bnm = fnm[:-10]
                                sqbp = os.path.join(dnm, "{}-{}.bin".format(bnm, str(gf).zfill(5)))
                                if(os.path.exists(sqbp)):
                                    m.bin_filename = sqbp
                                else:
                                    # skip if not found
                                    log("cannot find .bin file for frame: {} at path: '{}'. skipping..".format(gf, sqbp), 3, LogStyles.WARNING, )
                                    skip = True
                            else:
                                # skip if not found
                                log("cannot find .bin file for frame: {} at path: '{}'. skipping..".format(gf, sqpath), 3, LogStyles.WARNING, )
                                skip = True
                        else:
                            skip = True
                    else:
                        # static particles, just take what is on path
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
                     
                     'embed': m.embed,
                     'pdata': pdata,
                     
                     'material': material,
                     'material_embed': m.material_embed,
                     'backface_material': backface_material,
                     'backface_material_embed': m.backface_material_embed,
                     
                     'base': b, 'pivot': p, 'matrix': None, 'hide': m.hide, 'hide_parent': m.hide_parent, 'type': 'PARTICLES', }
                
                if(m.source == 'EXTERNAL_BIN'):
                    q['embed'] = False
                else:
                    p = os.path.join(self.tmp_dir, "{0}.binpart".format(q['name']))
                    w = MXSBinParticlesWriterLegacy(p, q['pdata'])
                    q['pdata'] = p
                    self.part_data_paths.append(p)
                
                if(m.private_bin_filename != ''):
                    m.bin_filename = m.private_bin_filename
                    m.private_bin_filename = ''
                
            elif(dp['type'] == 'GRASS'):
                material = bpy.path.abspath(m.material)
                if(material != "" and not os.path.exists(material)):
                    log("{1}: mxm ('{0}') does not exist.".format(material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                backface_material = bpy.path.abspath(m.backface_material)
                if(backface_material != "" and not os.path.exists(backface_material)):
                    log("{1}: backface mxm ('{0}') does not exist.".format(backface_material, self.__class__.__name__), 2, LogStyles.WARNING, )
                    material = ""
                
                o = bpy.data.objects[dp['object']]
                
                q = {'material': material,
                     'material_embed': m.material_embed,
                     'backface_material': backface_material,
                     'backface_material_embed': m.backface_material_embed,
                     
                     'density': int(m.density), 'density_map': texture_to_data(m.density_map, ps, o, ),
                     'length': m.length, 'length_map': texture_to_data(m.length_map, ps, o, ), 'length_variation': m.length_variation,
                     'root_width': m.root_width, 'tip_width': m.tip_width,
                     'direction_type': int(m.direction_type),
                     'initial_angle': math.degrees(m.initial_angle), 'initial_angle_variation': m.initial_angle_variation, 'initial_angle_map': texture_to_data(m.initial_angle_map, ps, o, ),
                     'start_bend': m.start_bend, 'start_bend_variation': m.start_bend_variation, 'start_bend_map': texture_to_data(m.start_bend_map, ps, o, ),
                     'bend_radius': m.bend_radius, 'bend_radius_variation': m.bend_radius_variation, 'bend_radius_map': texture_to_data(m.bend_radius_map, ps, o, ),
                     'bend_angle': math.degrees(m.bend_angle), 'bend_angle_variation': m.bend_angle_variation, 'bend_angle_map': texture_to_data(m.bend_angle_map, ps, o, ),
                     'cut_off': m.cut_off, 'cut_off_variation': m.cut_off_variation, 'cut_off_map': texture_to_data(m.cut_off_map, ps, o, ),
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
                # TODO
                # steps = 2 ** ps.settings.render_step + 1
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
                        if(len(curve) == 0 and co.length_squared == 0):
                            # in case the first curve part is exactly in 0,0,0
                            co = Vector((0.000001, 0.000001, 0.000001))
                        if not (co.length_squared == 0 or seg_length == 0):
                            # if it is not zero append as new point
                            v = transform * co
                            v = mat * v
                            curve.append(v)
                    
                    points.append(curve)
                
                '''
                steps = 2 ** ps.settings.render_step
                num_curves = len(ps.particles) if len(ps.child_particles) == 0 else len(ps.child_particles)
                nc0 = len(ps.particles)
                nc1 = len(ps.child_particles) - nc0
                
                points = []
                for p in range(0, nc0):
                    seg_length = 1.0
                    curve = []
                    for step in range(0, steps):
                        co = ps.co_hair(o, p, step)
                        # get distance between last and this point
                        if(step > 0):
                            seg_length = (co - omw * curve[len(curve) - 1]).length_squared
                        if(len(curve) == 0 and co.length_squared == 0):
                            # in case the first curve part is exactly in 0,0,0
                            co = Vector((0.000001, 0.000001, 0.000001))
                        if not (co.length_squared == 0 or seg_length == 0):
                            # if it is not zero append as new point
                            v = transform * co
                            v = mat * v
                            curve.append(v)
                    points.append(curve)
                for p in range(0, nc1):
                    seg_length = 1.0
                    curve = []
                    for step in range(0, steps):
                        co = ps.co_hair(o, nc0 + p, step)
                        # get distance between last and this point
                        if(step > 0):
                            seg_length = (co - omw * curve[len(curve) - 1]).length_squared
                        if(len(curve) == 0 and co.length_squared == 0):
                            # in case the first curve part is exactly in 0,0,0
                            co = Vector((0.000001, 0.000001, 0.000001))
                        if not (co.length_squared == 0 or seg_length == 0):
                            # if it is not zero append as new point
                            v = transform * co
                            v = mat * v
                            curve.append(v)
                    points.append(curve)
                '''
                # for p in range(0, num_curves):
                #     seg_length = 1.0
                #     curve = []
                #
                #     for step in range(0, steps):
                #         co = ps.co_hair(o, p, step)
                #
                #         # get distance between last and this point
                #         if(step > 0):
                #             seg_length = (co - omw * curve[len(curve) - 1]).length_squared
                #
                #         if not (co.length_squared == 0 or seg_length == 0):
                #             # if it is not zero append as new point
                #             v = transform * co
                #             v = mat * v
                #             curve.append(v)
                #
                #     points.append(curve)
                
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
                # TODO
                # locs = [round(v, 6) for v in locs]
                
                p = os.path.join(self.tmp_dir, "{0}.binhair".format(q['name']))
                w = MXSBinHairWriterLegacy(p, locs)
                q['hair_data_path'] = p
                self.hair_data_paths.append(p)
                
                data = {'HAIR_MAJOR_VER': [1, 0, 0, 0],
                        'HAIR_MINOR_VER': [0, 0, 0, 0],
                        'HAIR_FLAG_ROOT_UVS': [0],
                        'HAIR_GUIDES_COUNT': [num_curves],
                        'HAIR_GUIDES_POINT_COUNT': [steps],
                        # 'HAIR_POINTS': locs,
                        'HAIR_NORMALS': [1.0], }
                
                '''
                if(m.uv_layer is not ""):
                    uv_no = 0
                    for i, uv in enumerate(o.data.uv_textures):
                        if(m.uv_layer == uv.name):
                            uv_no = i
                            break
                    mod = None
                    for m in o.modifiers:
                        if(m.type == 'PARTICLE_SYSTEM'):
                            if(m.particle_system == ps):
                                mod = m
                                break
                    uv_locs = tuple()
                    for i, p in enumerate(ps.particles):
                        co = ps.uv_on_emitter(mod, p, particle_no=i, uv_no=uv_no, )
                        uv_locs += co.to_tuple()
                    # for i, p in enumerate(ps.child_particles):
                    #     co = ps.uv_on_emitter(mod, p, particle_no=i, uv_no=uv_no, )
                    #     uv_locs += co.to_tuple()
                    if(nc1 != 0):
                        ex = int(nc1 / nc0)
                    for i in range(ex):
                        uv_locs += uv_locs
                    
                    # print(len(uv_locs))
                    # print(num_curves * 2)
                    
                    data['HAIR_FLAG_ROOT_UVS'] = [1]
                    data['HAIR_ROOT_UVS'] = uv_locs
                '''
                
                # print(data['HAIR_GUIDES_COUNT'])
                # print(data['HAIR_GUIDES_POINT_COUNT'])
                # print(len(data['HAIR_POINTS']))
                # print(len(data['HAIR_POINTS']) == (num_curves * steps * 3))
                
                q['data'] = data
            
            elif(dp['type'] == 'CLONER'):
                o = bpy.data.objects[dp['object']]
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
                    sizes = []
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
                            # size per particle
                            if(m.bl_use_size):
                                sizes.append(part.size)
                            else:
                                sizes.append(m.bl_size)
                    locs = maths.apply_matrix_for_realflow_bin_export(locs)
                    vels = maths.apply_matrix_for_realflow_bin_export(vels)
                    particles = []
                    for i, ploc in enumerate(locs):
                        pnor = Vector(vels[i][:3])
                        pnor.normalize()
                        particles.append((i, ) + tuple(ploc[:3]) + pnor.to_tuple() + tuple(vels[i][:3]) + (sizes[i], ))
                    
                    if(os.path.exists(bpy.path.abspath(m.directory)) and not m.overwrite):
                        raise OSError("file: {} exists".format(bpy.path.abspath(m.directory)))
                    
                    cf = self.context.scene.frame_current
                    prms = {'directory': bpy.path.abspath(m.directory),
                            'name': "{}".format(dp['name']),
                            'frame': cf,
                            'particles': particles,
                            'fps': self.context.scene.render.fps,
                            'size': 1.0 if m.bl_use_size else m.bl_size / 2, }
                    rfbw = rfbin.RFBinWriter(**prms)
                    m.filename = rfbw.path
                
                cloned = None
                try:
                    cloned = ps.settings.dupli_object.name
                except AttributeError:
                    log("{}: {}: Maxwell Cloner: cloned object is not available. Skipping..".format(o.name, ps.name), 1, LogStyles.WARNING, )
                
                if(cloned is not None):
                    q = {'filename': bpy.path.abspath(m.filename),
                         'radius': m.radius,
                         'mb_factor': m.mb_factor,
                         'load_percent': m.load_percent,
                         'start_offset': m.start_offset,
                         'extra_npp': m.extra_npp,
                         'extra_p_dispersion': m.extra_p_dispersion,
                         'extra_p_deformation': m.extra_p_deformation,
                         'align_to_velocity': m.align_to_velocity,
                         'scale_with_radius': m.scale_with_radius,
                         'inherit_obj_id': m.inherit_obj_id,
                         'frame': self.context.scene.frame_current,
                         'fps': self.context.scene.render.fps,
                         'display_percent': int(m.display_percent),
                         'display_max': int(m.display_max),
                     
                         'cloned_object': ps.settings.dupli_object.name,
                         'render_emitter': ps.settings.use_render_emitter,
                     
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
                         'type': 'CLONER', }
            else:
                raise TypeError("Unsupported particles type: {}".format(dp['type']))
            
            if(q is not None and not skip):
                self.data.append(q)
    
    def _references(self):
        for o in self.references:
            ob = o['object']
            m = ob.maxwell_render_reference
            
            log("{0} -> {1}".format(o['object'].name, bpy.path.abspath(m.path)), 2)
            if(not os.path.exists(bpy.path.abspath(m.path))):
                log("mxs file: '{}' does not exist, skipping..".format(bpy.path.abspath(m.path)), 3, LogStyles.WARNING)
                return
            
            # template
            d = {'name': ob.name,
                 'parent': None,
                 
                 'base': None,
                 'pivot': None,
                 
                 'path': bpy.path.abspath(m.path),
                 'flag_override_hide': m.flag_override_hide,
                 'flag_override_hide_to_camera': m.flag_override_hide_to_camera,
                 'flag_override_hide_to_refl_refr': m.flag_override_hide_to_refl_refr,
                 'flag_override_hide_to_gi': m.flag_override_hide_to_gi,
                 
                 'opacity': 100.0,
                 'hidden_camera': False,
                 'hidden_camera_in_shadow_channel': False,
                 'hidden_global_illumination': False,
                 'hidden_reflections_refractions': False,
                 'hidden_zclip_planes': False,
                 'object_id': (255, 255, 255),
                 
                 'type': 'REFERENCE', }
            
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
    
    def _volumetrics(self):
        for o in self.volumetrics:
            ob = o['object']
            m = ob.maxwell_volumetrics_extension
            
            log("{0} ({1})".format(ob.name, o['export_type']), 2)
            
            material = bpy.path.abspath(m.material)
            if(material != "" and not os.path.exists(material)):
                log("{1}: mxm ('{0}') does not exist.".format(material, self.__class__.__name__), 2, LogStyles.WARNING, )
                material = ""
            backface_material = bpy.path.abspath(m.backface_material)
            if(backface_material != "" and not os.path.exists(backface_material)):
                log("{1}: backface mxm ('{0}') does not exist.".format(backface_material, self.__class__.__name__), 2, LogStyles.WARNING, )
                material = ""
            
            d = {'name': ob.name,
                 'parent': None,
                 
                 'base': None,
                 'pivot': None,
                 
                 'vtype': int(m.vtype[-1:]),
                 'density': m.density,
                 'noise_seed': m.noise_seed,
                 'noise_low': m.noise_low,
                 'noise_high': m.noise_high,
                 'noise_detail': m.noise_detail,
                 'noise_octaves': m.noise_octaves,
                 'noise_persistence': m.noise_persistence,
                 
                 'material': material,
                 'material_embed': m.material_embed,
                 'backface_material': backface_material,
                 'backface_material_embed': m.backface_material_embed,
                 
                 'opacity': 100.0,
                 'hidden_camera': False,
                 'hidden_camera_in_shadow_channel': False,
                 'hidden_global_illumination': False,
                 'hidden_reflections_refractions': False,
                 'hidden_zclip_planes': False,
                 'object_id': (255, 255, 255),
                 
                 'type': 'VOLUMETRICS', }
            
            d = self._object_properties(ob, d)
            
            if(ob.parent):
                d['parent'] = ob.parent.name
            
            mat = Matrix()
            if(ob.parent_type == 'BONE'):
                oamw = ob.matrix_world.copy()
                apmw = ob.parent.matrix_world.copy()
                apmw.invert()
                amw = apmw * oamw
                mat = amw.copy()
            else:
                mat = ob.matrix_local.copy()
            
            f = 2
            mat = mat * Matrix.Scale(f, 4)
            
            f = ob.empty_draw_size
            mat = mat * Matrix.Scale(f, 4)
            
            b, p = self._matrix_to_base_and_pivot(mat)
            
            d['base'] = b
            d['pivot'] = p
            
            self.data.append(d)
    
    def _ext_material(self, mat, ob):
        m = mat.maxwell_render
        mx = mat.maxwell_material_extension
        
        def texture_to_data(name):
            if(name == ""):
                return None
            tex = bpy.data.textures[name]
            if(tex.type != 'IMAGE'):
                return None
            
            m = tex.maxwell_render
            d = {'type': 'IMAGE',
                 'path': bpy.path.abspath(tex.image.filepath),
                 'channel': 0,
                 'use_override_map': m.use_global_map,
                 'tile_method_type': [True, True],
                 'tile_method_units': int(m.tiling_units[-1:]),
                 'repeat': [m.repeat[0], m.repeat[1]],
                 'mirror': [m.mirror_x, m.mirror_y],
                 'offset': [m.offset[0], m.offset[1]],
                 'rotation': m.rotation,
                 'invert': m.invert,
                 'alpha_only': m.use_alpha,
                 'interpolation': m.interpolation,
                 'brightness': m.brightness,
                 'contrast': m.contrast,
                 'saturation': m.saturation,
                 'hue': m.hue,
                 'rgb_clamp': [m.clamp[0], m.clamp[1]], }
            
            if(m.tiling_method == 'NO_TILING'):
                tm = [False, False]
            elif(m.tiling_method == 'TILE_X'):
                tm = [True, False]
            elif(m.tiling_method == 'TILE_Y'):
                tm = [False, True]
            else:
                tm = [True, True]
            d['tile_method_type'] = tm
            
            slot = None
            for ts in mat.texture_slots:
                if(ts is not None):
                    if(ts.texture is not None):
                        if(ts.texture.name == name):
                            slot = ts
                            break
            
            for i, uv in enumerate(ob.data.uv_textures):
                if(uv.name == slot.uv_layer):
                    d['channel'] = i
                    break
            
            return d
        
        if(m.use == 'EMITTER'):
            d = {'type': 'EMITTER',
                 'name': mat.name,
                 'emitter_type': int(mx.emitter_type),
                 'emitter_ies_data': bpy.path.abspath(mx.emitter_ies_data),
                 'emitter_ies_intensity': mx.emitter_ies_intensity,
                 'emitter_spot_map_enabled': mx.emitter_spot_map_enabled,
                 'emitter_spot_map': texture_to_data(mx.emitter_spot_map),
                 'emitter_spot_cone_angle': math.degrees(mx.emitter_spot_cone_angle),
                 'emitter_spot_falloff_angle': math.degrees(mx.emitter_spot_falloff_angle),
                 'emitter_spot_falloff_type': int(mx.emitter_spot_falloff_type),
                 'emitter_spot_blur': mx.emitter_spot_blur,
                 'emitter_emission': int(mx.emitter_emission),
                 'emitter_color': self._color_to_rgb8(mx.emitter_color),
                 'emitter_color_black_body_enabled': mx.emitter_color_black_body_enabled,
                 'emitter_color_black_body': mx.emitter_color_black_body,
                 'emitter_luminance': int(mx.emitter_luminance),
                 'emitter_luminance_power': mx.emitter_luminance_power,
                 'emitter_luminance_efficacy': mx.emitter_luminance_efficacy,
                 'emitter_luminance_output': mx.emitter_luminance_output,
                 'emitter_temperature_value': mx.emitter_temperature_value,
                 'emitter_hdr_map': texture_to_data(mx.emitter_hdr_map),
                 'emitter_hdr_intensity': mx.emitter_hdr_intensity, }
        elif(m.use == 'AGS'):
            d = {'type': 'AGS',
                 'name': mat.name,
                 'ags_color': self._color_to_rgb8(mx.ags_color),
                 'ags_reflection': mx.ags_reflection,
                 'ags_type': int(mx.ags_type), }
        elif(m.use == 'OPAQUE'):
            d = {'type': 'OPAQUE',
                 'name': mat.name,
                 'opaque_color_type': mx.opaque_color_type,
                 'opaque_color': self._color_to_rgb8(mx.opaque_color),
                 'opaque_color_map': texture_to_data(mx.opaque_color_map),
                 'opaque_shininess_type': mx.opaque_shininess_type,
                 'opaque_shininess': mx.opaque_shininess,
                 'opaque_shininess_map': texture_to_data(mx.opaque_shininess_map),
                 'opaque_roughness_type': mx.opaque_roughness_type,
                 'opaque_roughness': mx.opaque_roughness,
                 'opaque_roughness_map': texture_to_data(mx.opaque_roughness_map),
                 'opaque_clearcoat': mx.opaque_clearcoat, }
        elif(m.use == 'TRANSPARENT'):
            d = {'type': 'TRANSPARENT',
                 'name': mat.name,
                 'transparent_color_type': mx.transparent_color_type,
                 'transparent_color': self._color_to_rgb8(mx.transparent_color),
                 'transparent_color_map': texture_to_data(mx.transparent_color_map),
                 'transparent_ior': mx.transparent_ior,
                 'transparent_transparency': mx.transparent_transparency,
                 'transparent_roughness_type': mx.transparent_roughness_type,
                 'transparent_roughness': mx.transparent_roughness,
                 'transparent_roughness_map': texture_to_data(mx.transparent_roughness_map),
                 'transparent_specular_tint': mx.transparent_specular_tint,
                 'transparent_dispersion': mx.transparent_dispersion,
                 'transparent_clearcoat': mx.transparent_clearcoat, }
        elif(m.use == 'METAL'):
            d = {'type': 'METAL',
                 'name': mat.name,
                 'metal_ior': int(mx.metal_ior),
                 'metal_tint': mx.metal_tint,
                 'metal_color_type': mx.metal_color_type,
                 'metal_color': self._color_to_rgb8(mx.metal_color),
                 'metal_color_map': texture_to_data(mx.metal_color_map),
                 'metal_roughness_type': mx.metal_roughness_type,
                 'metal_roughness': mx.metal_roughness,
                 'metal_roughness_map': texture_to_data(mx.metal_roughness_map),
                 'metal_anisotropy_type': mx.metal_anisotropy_type,
                 'metal_anisotropy': mx.metal_anisotropy,
                 'metal_anisotropy_map': texture_to_data(mx.metal_anisotropy_map),
                 'metal_angle_type': mx.metal_angle_type,
                 'metal_angle': mx.metal_angle,
                 'metal_angle_map': texture_to_data(mx.metal_angle_map),
                 'metal_dust_type': mx.metal_dust_type,
                 'metal_dust': mx.metal_dust,
                 'metal_dust_map': texture_to_data(mx.metal_dust_map),
                 'metal_perforation_enabled': mx.metal_perforation_enabled,
                 'metal_perforation_map': texture_to_data(mx.metal_perforation_map), }
        elif(m.use == 'TRANSLUCENT'):
            d = {'type': 'TRANSLUCENT',
                 'name': mat.name,
                 'translucent_scale': mx.translucent_scale,
                 'translucent_ior': mx.translucent_ior,
                 'translucent_color_type': mx.translucent_color_type,
                 'translucent_color': self._color_to_rgb8(mx.translucent_color),
                 'translucent_color_map': texture_to_data(mx.translucent_color_map),
                 'translucent_hue_shift': mx.translucent_hue_shift,
                 'translucent_invert_hue': mx.translucent_invert_hue,
                 'translucent_vibrance': mx.translucent_vibrance,
                 'translucent_density': mx.translucent_density,
                 'translucent_opacity': mx.translucent_opacity,
                 'translucent_roughness_type': mx.translucent_roughness_type,
                 'translucent_roughness': mx.translucent_roughness,
                 'translucent_roughness_map': texture_to_data(mx.translucent_roughness_map),
                 'translucent_specular_tint': mx.translucent_specular_tint,
                 'translucent_clearcoat': mx.translucent_clearcoat,
                 'translucent_clearcoat_ior': mx.translucent_clearcoat_ior, }
        elif(m.use == 'CARPAINT'):
            d = {'type': 'CARPAINT',
                 'name': mat.name,
                 'carpaint_color': self._color_to_rgb8(mx.carpaint_color),
                 'carpaint_metallic': mx.carpaint_metallic,
                 'carpaint_topcoat': mx.carpaint_topcoat, }
        # elif(m.use == 'HAIR'):
        #     pass
        else:
            # CUSTOM
            raise ValueError('materials of type CUSTOM should be handled somewhere else..')
        
        return (True, d, )
    
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
        
        if(system.PLATFORM == 'Darwin'):
            system.python34_run_script_helper(self.script_path, self.scene_data_path, self.mxs_path, append, instancer, wireframe, )
        elif(system.PLATFORM == 'Linux'):
            pass
        elif(system.PLATFORM == 'Windows'):
            pass
        else:
            pass
    
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
        
        if(hasattr(self, 'part_data_paths')):
            for p in self.part_data_paths:
                rm(p)
        
        if(os.path.exists(self.tmp_dir)):
            os.rmdir(self.tmp_dir)
        else:
            log("{1}: WARNING: _cleanup(): {0} does not exist?".format(self.tmp_dir, self.__class__.__name__), 1, LogStyles.WARNING, )


class MXSExportWireframeLegacy(MXSExportLegacy):
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
        
        super(MXSExportWireframeLegacy, self).__init__(context, mxs_path, use_instances, keep_intermediates, )
    
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
        # w = MXSBinMeshWriterLegacy(p, md, d['num_positions_per_vertex'])
        w = MXSBinMeshWriterLegacy(p, **md)
        
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
        
        ms = self._calc_marices(vs=vs, es=es, )
        
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
    
    def _calc_marices(self, vs, es, ):
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
        
        return matrices


class MXSBinMeshWriterLegacy():
    def __init__(self, path, name, num_positions, vertices, normals, triangles, triangle_normals, uv_channels, num_materials, triangle_materials, ):
        """
        name                sting
        num_positions       int
        vertices            [[(float x, float y, float z), ..., ], [...], ]
        normals             [[(float x, float y, float z), ..., ], [...], ]
        triangles           [(int iv0, int iv1, int iv2, int in0, int in1, int in2, ), ..., ], ]   # (3x vertex index, 3x normal index)
        triangle_normals    [[(float x, float y, float z), ..., ], [...], ]
        uv_channels         [[(float u1, float v1, float w1, float u2, float v2, float w2, float u3, float v3, float w3, ), ..., ], ..., ] or None      # ordered by uv index and ordered by triangle index
        num_materials       int
        triangle_materials  [(int tri_id, int mat_id), ..., ] or None
        """
        o = "@"
        with open("{0}.tmp".format(path), 'wb') as f:
            p = struct.pack
            fw = f.write
            # header
            fw(p(o + "7s", 'BINMESH'.encode('utf-8')))
            fw(p(o + "?", False))
            # name 250 max length
            fw(p(o + "250s", name.encode('utf-8')))
            # number of steps
            fw(p(o + "i", num_positions))
            # number of vertices
            lv = len(vertices[0])
            fw(p(o + "i", lv))
            # vertex positions
            for i in range(num_positions):
                fw(p(o + "{}d".format(lv * 3), *[f for v in vertices[i] for f in v]))
            # vertex normals
            for i in range(num_positions):
                fw(p(o + "{}d".format(lv * 3), *[f for v in normals[i] for f in v]))
            # number triangle normals
            ltn = len(triangle_normals[0])
            fw(p(o + "i", ltn))
            # triangle normals
            for i in range(num_positions):
                fw(p(o + "{}d".format(ltn * 3), *[f for v in triangle_normals[i] for f in v]))
            # number of triangles
            lt = len(triangles)
            fw(p(o + "i", lt))
            # triangles
            fw(p(o + "{}i".format(lt * 6), *[f for v in triangles for f in v]))
            # number of uv channels
            luc = len(uv_channels)
            fw(p(o + "i", luc))
            # uv channels
            for i in range(luc):
                fw(p(o + "{}d".format(lt * 9), *[f for v in uv_channels[i] for f in v]))
            # number of materials
            fw(p(o + "i", num_materials))
            # triangle materials
            fw(p(o + "{}i".format(lt * 2), *[f for v in triangle_materials for f in v]))
            # end
            fw(p(o + "?", False))
        # swap files
        if(os.path.exists(path)):
            os.remove(path)
        shutil.move("{0}.tmp".format(path), path)
        self.path = path


class MXSBinMeshReaderLegacy():
    def __init__(self, path):
        def r(f, b, o):
            d = struct.unpack_from(f, b, o)
            o += struct.calcsize(f)
            return d, o
        
        def r0(f, b, o):
            d = struct.unpack_from(f, b, o)[0]
            o += struct.calcsize(f)
            return d, o
        
        offset = 0
        with open(path, "rb") as bf:
            buff = bf.read()
        # endianness?
        signature = 20357755437992258
        l, _ = r0("<q", buff, 0)
        b, _ = r0(">q", buff, 0)
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            order = ">"
        else:
            raise AssertionError("{}: not a MXSBinMesh file".format(self.__class__.__name__))
        o = order
        # magic
        magic, offset = r0(o + "7s", buff, offset)
        magic = magic.decode(encoding="utf-8")
        if(magic != 'BINMESH'):
            raise RuntimeError()
        # throwaway
        _, offset = r(o + "?", buff, offset)
        # name
        name, offset = r0(o + "250s", buff, offset)
        name = name.decode(encoding="utf-8").replace('\x00', '')
        # number of steps
        num_positions, offset = r0(o + "i", buff, offset)
        # number of vertices
        lv, offset = r0(o + "i", buff, offset)
        # vertex positions
        vertices = []
        for i in range(num_positions):
            vs, offset = r(o + "{}d".format(lv * 3), buff, offset)
            vs3 = [vs[i:i + 3] for i in range(0, len(vs), 3)]
            vertices.append(vs3)
        # vertex normals
        normals = []
        for i in range(num_positions):
            ns, offset = r(o + "{}d".format(lv * 3), buff, offset)
            ns3 = [ns[i:i + 3] for i in range(0, len(ns), 3)]
            normals.append(ns3)
        # number of triangle normals
        ltn, offset = r0(o + "i", buff, offset)
        # triangle normals
        triangle_normals = []
        for i in range(num_positions):
            tns, offset = r(o + "{}d".format(ltn * 3), buff, offset)
            tns3 = [tns[i:i + 3] for i in range(0, len(tns), 3)]
            triangle_normals.append(tns3)
        # number of triangles
        lt, offset = r0(o + "i", buff, offset)
        # triangles
        ts, offset = r(o + "{}i".format(lt * 6), buff, offset)
        triangles = [ts[i:i + 6] for i in range(0, len(ts), 6)]
        # number uv channels
        num_channels, offset = r0(o + "i", buff, offset)
        # uv channels
        uv_channels = []
        for i in range(num_channels):
            uvc, offset = r(o + "{}d".format(lt * 9), buff, offset)
            uv9 = [uvc[i:i + 9] for i in range(0, len(uvc), 9)]
            uv_channels.append(uv9)
        # number of materials
        num_materials, offset = r0(o + "i", buff, offset)
        # triangle materials
        tms, offset = r(o + "{}i".format(2 * lt), buff, offset)
        triangle_materials = [tms[i:i + 2] for i in range(0, len(tms), 2)]
        # throwaway
        _, offset = r(o + "?", buff, offset)
        # and now.. eof
        if(offset != len(buff)):
            raise RuntimeError("expected EOF")
        # collect data
        self.data = {'name': name,
                     'num_positions': num_positions,
                     'vertices': vertices,
                     'normals': normals,
                     'triangles': triangles,
                     'triangle_normals': triangle_normals,
                     'uv_channels': uv_channels,
                     'num_materials': num_materials,
                     'triangle_materials': triangle_materials, }


class MXSBinHairWriterLegacy():
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


class MXSBinHairReaderLegacy():
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


class MXSBinParticlesWriterLegacy():
    def __init__(self, path, data):
        d = data
        o = "@"
        with open("{0}.tmp".format(path), 'wb') as f:
            p = struct.pack
            fw = f.write
            # header
            fw(p(o + "7s", 'BINPART'.encode('utf-8')))
            fw(p(o + "?", False))
            # 'PARTICLE_POSITIONS'
            n = len(d['PARTICLE_POSITIONS'])
            fw(p(o + "i", n))
            fw(p(o + "{}d".format(n), *d['PARTICLE_POSITIONS']))
            # 'PARTICLE_SPEEDS'
            n = len(d['PARTICLE_SPEEDS'])
            fw(p(o + "i", n))
            fw(p(o + "{}d".format(n), *d['PARTICLE_SPEEDS']))
            # 'PARTICLE_RADII'
            n = len(d['PARTICLE_RADII'])
            fw(p(o + "i", n))
            fw(p(o + "{}d".format(n), *d['PARTICLE_RADII']))
            # 'PARTICLE_NORMALS'
            n = len(d['PARTICLE_NORMALS'])
            fw(p(o + "i", n))
            fw(p(o + "{}d".format(n), *d['PARTICLE_NORMALS']))
            # 'PARTICLE_IDS'
            n = len(d['PARTICLE_IDS'])
            fw(p(o + "i", n))
            fw(p(o + "{}i".format(n), *d['PARTICLE_IDS']))
            # end
            fw(p(o + "?", False))
        if(os.path.exists(path)):
            os.remove(path)
        shutil.move("{0}.tmp".format(path), path)
        self.path = path


class MXSBinParticlesReaderLegacy():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        signature = 23734338517354818
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
            raise AssertionError("{}: not a MXSBinParticles file".format(self.__class__.__name__))
        o = self.order
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINPART'):
            raise RuntimeError()
        _ = r(o + "?")
        # 'PARTICLE_POSITIONS'
        n = r(o + "i")[0]
        self.PARTICLE_POSITIONS = r(o + "{}d".format(n))
        # 'PARTICLE_SPEEDS'
        n = r(o + "i")[0]
        self.PARTICLE_SPEEDS = r(o + "{}d".format(n))
        # 'PARTICLE_RADII'
        n = r(o + "i")[0]
        self.PARTICLE_RADII = r(o + "{}d".format(n))
        # 'PARTICLE_NORMALS'
        n = r(o + "i")[0]
        self.PARTICLE_NORMALS = r(o + "{}d".format(n))
        # 'PARTICLE_IDS'
        n = r(o + "i")[0]
        self.PARTICLE_IDS = r(o + "{}i".format(n))
        # eof
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")


class MXSExport():
    def __init__(self, context, mxs_path, use_instances=True, ):
        self.context = context
        self.mxs_path = os.path.realpath(mxs_path)
        self.use_instances = use_instances
        
        self.prepare()
        self.export()
    
    def prepare(self):
        log("{0} {1} {0}".format("-" * 30, self.__class__.__name__), 0, LogStyles.MESSAGE, prefix="", )
        if(os.path.exists(self.mxs_path)):
            log("mxs file exists at {0}, will be overwritten..".format(self.mxs_path), 1, LogStyles.WARNING, )
    
    def export(self):
        log("collecting objects..", 1)
        self.tree = self.collect()
        
        # conversion matrix
        self.matrix = Matrix(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
        
        self.mxs = mxs.MXSWriter(path=self.mxs_path, append=False, )
        
        # this is going to be filled with (child name, parent name) tuples
        self.hierarchy = []
        
        # prepare alpha groups, objects will be filled later when is clear they're exported..
        self.groups = []
        for g in bpy.data.groups:
            gmx = g.maxwell_render
            if(gmx.custom_alpha_use):
                self.groups.append({'name': g.name, 'objects': [], 'opaque': gmx.custom_alpha_opaque, })
        
        log("processing cameras..", 1, LogStyles.MESSAGE)
        for o in self.cameras:
            self.camera(o)
        
        log("processing empties..", 1, LogStyles.MESSAGE)
        for o in self.empties:
            self.empty(o)
        
        log("processing meshes..", 1, LogStyles.MESSAGE)
        for o in self.meshes:
            self.mesh(o)
        
        if(self.use_instances):
            # if self.use_instances is False those are already exported..
            log("processing instance base meshes..", 1, LogStyles.MESSAGE)
            for o in self.bases:
                self.mesh(o)
            
            log("processing instances..", 1, LogStyles.MESSAGE)
            for o in self.instances:
                self.instance(o)
        
        log("processing duplicates..", 1, LogStyles.MESSAGE)
        if(len(self.duplicates) != 0):
            for o in self.duplicates:
                if(self.use_instances):
                    self.instance(o, o['dupli_name'], )
                else:
                    self.mesh(o, o['dupli_name'], )
        
        log("processing particles..", 1, LogStyles.MESSAGE)
        
        def collect_particles():
            scene = self.context.scene
            
            def verify_parent(name):
                for c, p in self.hierarchy:
                    if(c == name):
                        return True
                return False
            
            particles = []
            for o in scene.objects:
                if(len(o.particle_systems) != 0):
                    for ps in o.particle_systems:
                        if(ps.settings.maxwell_render.use == 'PARTICLES'):
                            parent = o.name
                            p = verify_parent(parent)
                            if(not p):
                                log("Particles '{0}' container object '{1}' is not renderable and thus not exported. Particles will not be parented.".format(ps.name, o.name), 1, LogStyles.WARNING, )
                                parent = None
                            
                            mx = ps.settings.maxwell_render
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
                                     'object': o,
                                     'parent': parent, }
                                particles.append(d)
                        elif(ps.settings.maxwell_render.use == 'GRASS'):
                            mx = ps.settings.maxwell_render
                            
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
                                     'object': o,
                                     'parent': o.name, }
                                particles.append(d)
                        elif(ps.settings.maxwell_render.use == 'HAIR'):
                            parent = o.name
                            p = verify_parent(parent)
                            if(not p):
                                log("Hair '{0}' container object '{1}' is not renderable and thus not exported. Hair will not be parented.".format(ps.name, o.name), 1, LogStyles.WARNING, )
                                parent = None
                            
                            mx = ps.settings.maxwell_render
                            
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
                                     'object': o,
                                     'parent': parent, }
                                particles.append(d)
                        elif(ps.settings.maxwell_render.use == 'CLONER'):
                            mx = ps.settings.maxwell_render
                            
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
                                d = {'props': ps.settings.maxwell_cloner_extension,
                                     'matrix': Matrix(),
                                     'type': ps.settings.maxwell_render.use,
                                     'ps': ps,
                                     'name': "{}-{}".format(o.name, ps.name),
                                     'pmatrix': Matrix(),
                                     'object': o.name,
                                     'parent': o.name, }
                                particles.append(d)
                        else:
                            pass
            
            return particles
        
        self.particles = collect_particles()
        for o in self.particles:
            if(o['type'] == 'PARTICLES'):
                self.ext_particles(o)
            elif(o['type'] == 'GRASS'):
                self.grass(o)
            elif(o['type'] == 'HAIR'):
                self.hair(o)
            elif(o['type'] == 'CLONER'):
                self.cloner(o)
        
        for o in self.references:
            self.reference(o)
        
        for o in self.volumetrics:
            self.ext_volumetrics(o)
        
        # all objects are written, now set hierarchy
        self.mxs.hierarchy(self.hierarchy)
        
        log("processing environment..", 1, LogStyles.MESSAGE)
        self.environment()
        log("processing parameters..", 1, LogStyles.MESSAGE)
        self.parameters()
        log("processing channels..", 1, LogStyles.MESSAGE)
        self.channels()
        
        self.mxs.write()
        
        log("mxs saved in:", 1)
        log("{0}".format(self.mxs_path), 0, LogStyles.MESSAGE, prefix="")
        log("done.", 1, LogStyles.MESSAGE)
    
    def collect(self):
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
                if(o.maxwell_render_reference.enabled):
                    t = 'REFERENCE'
                elif(o.maxwell_volumetrics_extension.enabled):
                    t = 'VOLUMETRICS'
                else:
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
        append_types = ['MESH', 'BASE_INSTANCE', 'INSTANCE', 'REFERENCE', 'VOLUMETRICS', ]
        
        def check_renderables_in_tree(oo):
            ov = []
            
            def walk(o):
                for c in o['children']:
                    walk(c)
                if((o['export_type'] in append_types) and o['export'] is True):
                    # keep instances (Maxwell 3)
                    # keep: meshes, bases - both with export: True
                    # (export: False are hidden objects, and should be already swapped to empties if needed for hiearchy)
                    # > meshes..
                    # > bases can have children, bases are real meshes
                    ov.append(True)
                else:
                    # remove: empties, bases, instances, suns, meshes and bases with export: False (hidden objects) and reference enabled: False
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
        references = []
        volumetrics = []
        
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
                elif(o['export_type'] == 'REFERENCE'):
                    references.append(o)
                elif(o['export_type'] == 'VOLUMETRICS'):
                    volumetrics.append(o)
        
        for o in h:
            walk(o)
        
        self.meshes = meshes
        self.bases = bases
        self.instances = instances
        self.empties = empties
        self.cameras = cameras
        self.references = references
        self.volumetrics = volumetrics
        
        # no visible camera
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
        
        # find instances without base and change first one to base, quick and dirty..
        # this case happens when object (by name chosen as base) is on hidden layer and marked to be not exported
        # also, hope this is the last change of this nasty piece of code..
        def find_base_object_name(mnm):
            for bo in self.bases:
                if(bo['mesh'].name == mnm):
                    return bo['object'].name
        
        instances2 = self.instances[:]
        for o in instances2:
            if(find_base_object_name(o['mesh'].name) is None):
                o['export_type'] = 'BASE_INSTANCE'
                self.bases.append(o)
                self.instances.remove(o)
        
        # overriden instances
        instances2 = self.instances[:]
        for o in instances2:
            m = o['object'].maxwell_render
            if(m.override_instance):
                o['export_type'] = 'MESH'
                o['override_instance'] = o['object'].data
                self.meshes.append(o)
                self.instances.remove(o)
        
        # ----------------------------------------------------------------------------------
        # (everything above this line is pure magic, below is just standard code)
        
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(h)
        
        # print("-" * 100)
        # raise Exception()
        
        return h
    
    def matrix_to_base_and_pivot(self, m, ):
        b = ((m[0][3], m[2][3], m[1][3] * -1),
             (m[0][0], m[2][0], m[1][0] * -1),
             (m[0][2], m[2][2], m[1][2] * -1),
             (m[0][1] * -1, m[2][1] * -1, m[1][1]), )
        p = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), )
        return (b, p, )
    
    def get_object_props(self, o, ):
        try:
            m = o.maxwell_render
        except:
            m = None
        p = None
        if(m is not None):
            p = (m.hide, m.opacity, self.color_to_rgb8(m.object_id), m.hidden_camera, m.hidden_camera_in_shadow_channel,
                 m.hidden_global_illumination, m.hidden_reflections_refractions, m.hidden_zclip_planes)
        return p
    
    def object_materials(self, ob, d, instance=False, ):
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
            # def find_base_name(mnm):
            #     for ib in self.data:
            #         try:
            #             if(ib['instance_base'] is True):
            #                 if(ib['mesh_name'] == mnm):
            #                     return ib['name']
            #         except KeyError:
            #             pass
            def find_base_name(mnm):
                for o in self.bases:
                    if(o['mesh'].name == mnm):
                        return o['object'].name
            
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
                        if(mmx.use == 'CUSTOM'):
                            fm = bpy.path.abspath(mmx.mxm_file)
                            if(not check_path(fm)):
                                fm = ""
                            if(fm != ""):
                                a = (mmx.embed, fm)
                            else:
                                a = (False, "", )
                        else:
                            a = self.ext_material(s.material, ob)
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
                        if(mmx.use == 'CUSTOM'):
                            fm = bpy.path.abspath(mmx.mxm_file)
                            if(not check_path(fm)):
                                fm = ""
                            if(fm != ""):
                                a = (mmx.embed, fm)
                            else:
                                a = (False, "", )
                        else:
                            a = self.ext_material(s.material, ob)
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
    
    def color_to_rgb8(self, c, ):
        return tuple([int(255 * v) for v in c])
    
    def psys_texture_to_data(self, name, ps, ob=None, ):
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
        
        if(tex is not None and ob is not None and ps is not None):
            m = tex.maxwell_render
            d['type'] = 'IMAGE'
            d['path'] = bpy.path.abspath(tex.image.filepath)
            
            d['channel'] = 0
            ts = None
            for i, t in enumerate(ps.settings.texture_slots):
                if(t.texture == tex):
                    ts = t
                    break
            
            for i, uv in enumerate(ob.data.uv_textures):
                if(uv.name == ts.uv_layer):
                    d['channel'] = i
                    break
            
            d['use_override_map'] = m.use_global_map
            if(m.tiling_method == 'NO_TILING'):
                tm = [False, False]
            elif(m.tiling_method == 'TILE_X'):
                tm = [True, False]
            elif(m.tiling_method == 'TILE_Y'):
                tm = [False, True]
            else:
                tm = [True, True]
            d['tile_method_type'] = tm
            d['tile_method_units'] = int(m.tiling_units[-1:])
            d['repeat'] = [m.repeat[0], m.repeat[1]]
            d['mirror'] = [m.mirror_x, m.mirror_y]
            d['offset'] = [m.offset[0], m.offset[1]]
            d['rotation'] = m.rotation
            d['invert'] = m.invert
            d['alpha_only'] = m.use_alpha
            d['interpolation'] = m.interpolation
            d['brightness'] = m.brightness
            d['contrast'] = m.contrast
            d['saturation'] = m.saturation
            d['hue'] = m.hue
            d['rgb_clamp'] = [m.clamp[0], m.clamp[1]]
            return d
        return None
    
    def mod_texture_to_data(self, name, ob=None, ):
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
        
        '''
        tex = None
        for t in bpy.data.textures:
            if(t.name == name):
                if(t.type == 'IMAGE'):
                    tex = t
        
        # defaults
        d = {'type': 'IMAGE', 'path': "", 'channel': 0, 'use_override_map': False, 'tile_method_type': [True, True], 'tile_method_units': 0,
             'repeat': [1.0, 1.0], 'mirror': [False, False], 'offset': [0.0, 0.0], 'rotation': 0.0, 'invert': False, 'alpha_only': False,
             'interpolation': False, 'brightness': 0.0, 'contrast': 0.0, 'saturation': 0.0, 'hue': 0.0, 'rgb_clamp': [0.0, 255.0], }
        m = tex.maxwell_render
        if(tex is not None and ob is not None and m is not None):
            d['type'] = 'IMAGE'
            d['path'] = bpy.path.abspath(tex.image.filepath)
            d['channel'] = 0
            ts = None
            for i, t in enumerate(ob.texture_slots):
                if(t.texture == tex):
                    ts = t
                    break
            
            for i, uv in enumerate(ob.data.uv_textures):
                if(uv.name == ts.uv_layer):
                    d['channel'] = i
                    break
            
            d['use_override_map'] = m.use_global_map
            if(m.tiling_method == 'NO_TILING'):
                tm = [False, False]
            elif(m.tiling_method == 'TILE_X'):
                tm = [True, False]
            elif(m.tiling_method == 'TILE_Y'):
                tm = [False, True]
            else:
                tm = [True, True]
            d['tile_method_type'] = tm
            d['tile_method_units'] = int(m.tiling_units[-1:])
            d['repeat'] = [m.repeat[0], m.repeat[1]]
            d['mirror'] = [m.mirror_x, m.mirror_y]
            d['offset'] = [m.offset[0], m.offset[1]]
            d['rotation'] = m.rotation
            d['invert'] = m.invert
            d['alpha_only'] = m.use_alpha
            d['interpolation'] = m.interpolation
            d['brightness'] = m.brightness
            d['contrast'] = m.contrast
            d['saturation'] = m.saturation
            d['hue'] = m.hue
            d['rgb_clamp'] = [m.clamp[0], m.clamp[1]]
            return d
        return None
        '''
    
    def camera(self, o, ):
        log("{0}".format(o['object'].name), 2)
        
        ob = o['object']
        cd = ob.data
        rp = self.context.scene.render
        mx = ob.data.maxwell_render
        
        # film width / height: width / height ratio a ==  x_res / y_res ratio
        # x_res / y_res is more important than sensor size, depending on sensor fit the other one is calculated
        resolution_x = int(rp.resolution_x * rp.resolution_percentage / 100.0)
        resolution_y = int(rp.resolution_y * rp.resolution_percentage / 100.0)
        pixel_aspect = rp.pixel_aspect_x / rp.pixel_aspect_y
        sf = cd.sensor_fit
        film_height = cd.sensor_height / 1000.0
        film_width = cd.sensor_width / 1000.0
        if(sf == 'AUTO'):
            if(resolution_x > resolution_y):
                sf = 'HORIZONTAL'
                film_width = cd.sensor_width / 1000.0
            else:
                sf = 'VERTICAL'
                film_height = cd.sensor_width / 1000.0
        if(sf == 'VERTICAL'):
            film_width = (film_height * resolution_x) / resolution_y
        else:
            film_height = (film_width * resolution_y) / resolution_x
        
        props = (ob.name, 1, 1 / mx.shutter, film_width, film_height, mx.iso, mx.aperture, mx.diaphragm_angle, mx.diaphragm_blades,
                 mx.frame_rate, resolution_x, resolution_y, pixel_aspect, int(mx.lens[-1:]), )
        
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
        
        origin = Vector(self.matrix * origin).to_tuple()
        focal_point = Vector(self.matrix * focal_point).to_tuple()
        up = Vector(self.matrix * up).to_tuple()
        steps = ((0, origin, focal_point, up, cd.lens / 1000.0, mx.fstop, 1), )
        
        active = (self.context.scene.camera == ob)
        
        lens_extra = None
        if(int(mx.lens[-1:]) != 0):
            if(mx.lens == 'TYPE_FISHEYE_3'):
                lens_extra = mx.fov
            elif(mx.lens == 'TYPE_SPHERICAL_4'):
                lens_extra = mx.azimuth
            elif(mx.lens == 'TYPE_CYLINDRICAL_5'):
                lens_extra = mx.angle
        
        region = None
        if(mx.screen_region != 'NONE'):
            x = int(resolution_x * rp.border_min_x)
            h = resolution_y - int(resolution_y * rp.border_min_y)
            w = int(resolution_x * rp.border_max_x)
            y = resolution_y - int(resolution_y * rp.border_max_y)
            region = (x, y, w, h, mx.screen_region)
        
        custom_bokeh = None
        if(mx.custom_bokeh):
            custom_bokeh = (mx.bokeh_ratio, mx.bokeh_angle, mx.custom_bokeh)
        
        cut_planes = None
        if(mx.zclip):
            cut_planes = (cd.clip_start, cd.clip_end, mx.zclip)
        
        shift_lens = None
        if(cd.shift_x != 0 or cd.shift_y != 0):
            shift_lens = (cd.shift_x * 10.0, cd.shift_y * 10.0)
        
        self.mxs.camera(props, steps, active, lens_extra, mx.response, region, cut_planes, shift_lens, )
    
    def empty(self, o, ename=None, ):
        log("{0}".format(o['object'].name), 2)
        ob = o['object']
        
        if(ob.parent_type == 'BONE'):
            oamw = ob.matrix_world.copy()
            apmw = ob.parent.matrix_world.copy()
            apmw.invert()
            amw = apmw * oamw
            b, p = self.matrix_to_base_and_pivot(amw)
        else:
            b, p = self.matrix_to_base_and_pivot(ob.matrix_local)
        
        name = ob.name
        if(ename is not None):
            name = ename
        self.mxs.empty(name, b, p, self.get_object_props(ob), )
        
        parent = None
        if(ob.parent):
            parent = ob.parent.name
        self.hierarchy.append((name, parent))
    
    def mesh(self, o, mname=None, ):
        ob = o['object']
        log("{0}".format(ob.name), 2)
        
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
        
        if(ob.parent_type == 'BONE'):
            oamw = ob.matrix_world.copy()
            apmw = ob.parent.matrix_world.copy()
            apmw.invert()
            amw = apmw * oamw
            base, pivot = self.matrix_to_base_and_pivot(amw)
        else:
            base, pivot = self.matrix_to_base_and_pivot(ob.matrix_local)
        
        vertices = [[v.co.to_tuple() for v in me.vertices], ]
        normals = [[v.normal.to_tuple() for v in me.vertices], ]
        
        triangles = []
        triangle_normals = []
        ni = len(me.vertices) - 1
        tns = []
        for fi, f in enumerate(me.tessfaces):
            ni = ni + 1
            
            tns.append(f.normal.to_tuple())
            fv = f.vertices
            # smoothing
            if(f.use_smooth):
                # vertex normals
                nix = (fv[0], fv[1], fv[2], )
            else:
                # face normal
                nix = (ni, ni, ni, )
            
            t = tuple(fv) + nix
            triangles.append(t)
        
        triangle_normals.append(tns)
        
        uv_channels = None
        if(len(me.tessface_uv_textures) > 0):
            uv_channels = []
            for tix, uvtex in enumerate(me.tessface_uv_textures):
                uv = []
                for fi, f in enumerate(me.tessfaces):
                    d = uvtex.data[fi].uv
                    uv.append((d[0][0], 1.0 - d[0][1], 0.0, d[1][0], 1.0 - d[1][1], 0.0, d[2][0], 1.0 - d[2][1], 0.0, ))
            uv_channels.append(uv)
        
        d = {'num_materials': len(ob.material_slots),
             'materials': [], }
        d = self.object_materials(ob, d)
        
        num_materials = d['num_materials']
        materials = None
        if(num_materials != 0):
            materials = [(m[1], m[0]) for m in d['materials']]
        
        triangle_materials = None
        if(num_materials > 1):
            triangle_materials = []
            for fi, f in enumerate(me.tessfaces):
                triangle_materials.append((fi, f.material_index, ))
        
        backface_material = None
        if(len(d['backface_material']) != 0):
            backface_material = (d['backface_material'][0], d['backface_material'][1])
        
        name = ob.name
        if(mname is not None):
            name = mname
        
        self.mxs.mesh(name, base, pivot, 1, vertices, normals, triangles, triangle_normals, uv_channels,
                      self.get_object_props(ob), num_materials, materials, triangle_materials, backface_material, )
        
        # cleanup
        bpy.data.meshes.remove(me)
        
        parent = None
        if(ob.parent):
            parent = ob.parent.name
        self.hierarchy.append((name, parent))
        
        for g in bpy.data.groups:
            gmx = g.maxwell_render
            if(gmx.custom_alpha_use):
                for gob in g.objects:
                    if(gob.name == ob.name):
                        for gr in self.groups:
                            if(gr['name'] == g.name):
                                gr['objects'].append(name)
                                break
        
        self.object_extensions(o)
    
    def instance(self, o, iname=None, ):
        log("{0}".format(o['object'].name), 2)
        ob = o['object']
        
        # negative scaled instances will be transformed in a weird way
        # currently i have no solution, so just warn about it.
        _, _, ms = ob.matrix_world.decompose()
        if(ms.x < 0.0 or ms.y < 0.0 or ms.z < 0.0):
            log("{1}: WARNING: instance {0} is negative scaled. Weird transformation will occur..".format(ob.name, self.__class__.__name__), 1, LogStyles.WARNING, )
        
        name = ob.name
        if(iname is not None):
            name = iname
        
        def find_base_object_name(mnm):
            for o in self.bases:
                if(o['mesh'].name == mnm):
                    return o['object'].name
        
        instanced_name = find_base_object_name(ob.data.name)
        
        if(ob.parent_type == 'BONE'):
            oamw = ob.matrix_world.copy()
            apmw = ob.parent.matrix_world.copy()
            apmw.invert()
            amw = apmw * oamw
            base, pivot = self.matrix_to_base_and_pivot(amw)
        else:
            base, pivot = self.matrix_to_base_and_pivot(ob.matrix_local)
        
        object_props = self.get_object_props(ob)
        
        d = {'num_materials': len(ob.material_slots),
             'materials': [], }
        d = self.object_materials(ob, d, True, )
        
        num_materials = d['num_materials']
        materials = None
        if(num_materials != 0):
            materials = [(m[1], m[0]) for m in d['materials']]
        material = None
        if(material is not None):
            material = materials[0]
        
        backface_material = None
        if(len(d['backface_material']) != 0):
            backface_material = (d['backface_material'][0], d['backface_material'][1])
        
        self.mxs.instance(name, instanced_name, base, pivot, object_props, material, backface_material, )
        
        parent = None
        if(ob.parent):
            parent = ob.parent.name
        self.hierarchy.append((name, parent))
        
        for g in bpy.data.groups:
            gmx = g.maxwell_render
            if(gmx.custom_alpha_use):
                for gob in g.objects:
                    if(gob.name == ob.name):
                        for gr in self.groups:
                            if(gr['name'] == g.name):
                                gr['objects'].append(name)
                                break
    
    def reference(self, o, rname=None, ):
        ob = o['object']
        m = ob.maxwell_render_reference
        rp = bpy.path.abspath(m.path)
        log("{0} -> {1}".format(ob.name, rp), 2)
        
        if(ob.parent_type == 'BONE'):
            oamw = ob.matrix_world.copy()
            apmw = ob.parent.matrix_world.copy()
            apmw.invert()
            amw = apmw * oamw
            b, p = self.matrix_to_base_and_pivot(amw)
        else:
            b, p = self.matrix_to_base_and_pivot(ob.matrix_local)
        
        name = ob.name
        if(rname is not None):
            name = rname
        
        if(not os.path.exists(rp)):
            log("mxs file: '{}' does not exist, skipping..".format(rp), 3, LogStyles.WARNING)
            return
            
        flags = [m.flag_override_hide, m.flag_override_hide_to_camera, m.flag_override_hide_to_refl_refr, m.flag_override_hide_to_gi, ]
        
        self.mxs.reference(name, rp, flags, b, p, self.get_object_props(ob), )
        
        parent = None
        if(ob.parent):
            parent = ob.parent.name
        self.hierarchy.append((name, parent))
    
    def ext_volumetrics(self, o, vname=None, ):
        ob = o['object']
        
        name = ob.name
        if(vname is not None):
            name = vname
        
        log("{0} ({1})".format(name, o['export_type']), 2)
        
        m = ob.maxwell_volumetrics_extension
        
        mat = Matrix()
        if(ob.parent_type == 'BONE'):
            oamw = ob.matrix_world.copy()
            apmw = ob.parent.matrix_world.copy()
            apmw.invert()
            amw = apmw * oamw
            mat = amw.copy()
        else:
            mat = ob.matrix_local.copy()
        
        # scale 2x because blender empty of size 1.0 is 2 units big
        f = 2
        mat = mat * Matrix.Scale(f, 4)
        
        # scale by draw size, the result should be the same like in viewport.. if set to draw cube :)
        f = ob.empty_draw_size
        mat = mat * Matrix.Scale(f, 4)
        
        base, pivot = self.matrix_to_base_and_pivot(mat)
        
        vtype = int(m.vtype[-1:])
        if(vtype == 2):
            properties = (2, m.density, m.noise_seed, m.noise_low, m.noise_high, m.noise_detail, m.noise_octaves, m.noise_persistence, )
        else:
            properties = (1, m.density, )
        
        material = (bpy.path.abspath(m.material), m.material_embed, )
        if(material[0] != "" and not os.path.exists(material[0])):
            log("{1}: mxm ('{0}') does not exist.".format(material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            material = None
        backface_material = (bpy.path.abspath(m.backface_material), m.backface_material_embed, )
        if(backface_material[0] != "" and not os.path.exists(backface_material[0])):
            log("{1}: backface mxm ('{0}') does not exist.".format(backface_material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            backface_material = None
        
        self.mxs.ext_volumetrics(name, properties, base, pivot, self.get_object_props(ob), material, backface_material, )
        
        parent = None
        if(o['parent']):
            parent = o['parent']
        self.hierarchy.append((name, parent))
    
    def environment(self):
        mx = self.context.scene.world.maxwell_render
        
        env_type = mx.env_type
        if(env_type == 'NONE'):
            self.mxs.environment(None)
            return
        
        sky_type = mx.sky_type
        sky = {'sky_use_preset': mx.sky_use_preset,
               'sky_preset': bpy.path.abspath(mx.sky_preset),
               'sky_intensity': mx.sky_intensity,
               'sky_planet_refl': mx.sky_planet_refl / 100.0,
               'sky_ozone': mx.sky_ozone,
               'sky_water': mx.sky_water,
               'sky_turbidity_coeff': mx.sky_turbidity_coeff,
               'sky_wavelength_exp': mx.sky_wavelength_exp,
               'sky_reflectance': mx.sky_reflectance / 100.0,
               'sky_asymmetry': mx.sky_asymmetry, }
        dome = {'dome_intensity': mx.dome_intensity,
                'dome_zenith': self.color_to_rgb8(mx.dome_zenith),
                'dome_horizon': self.color_to_rgb8(mx.dome_horizon),
                'dome_mid_point': math.degrees(mx.dome_mid_point), }
        
        sun_type = mx.sun_type
        sun = None
        if(sun_type != 'DISABLED'):
            v = Vector((mx.sun_dir_x, mx.sun_dir_y, mx.sun_dir_z))
            v = self.matrix * v
            sun = {'sun_power': mx.sun_power,
                   'sun_radius_factor': mx.sun_radius_factor,
                   'sun_temp': mx.sun_temp,
                   'sun_color': self.color_to_rgb8(mx.sun_color),
                   'sun_location_type': mx.sun_location_type,
                   'sun_latlong_lat': mx.sun_latlong_lat,
                   'sun_latlong_lon': mx.sun_latlong_lon,
                   'sun_date': mx.sun_date,
                   'sun_time': mx.sun_time,
                   'sun_latlong_gmt': mx.sun_latlong_gmt,
                   'sun_latlong_gmt_auto': mx.sun_latlong_gmt_auto,
                   'sun_latlong_ground_rotation': mx.sun_latlong_ground_rotation,
                   'sun_angles_zenith': mx.sun_angles_zenith,
                   'sun_angles_azimuth': mx.sun_angles_azimuth,
                   'sun_dir_x': v.x,
                   'sun_dir_y': v.y,
                   'sun_dir_z': v.z, }
            
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
                if(sun is None):
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
                    sun['sun_location_type'] = 'DIRECTION'
                    sun['sun_dir_x'] = v.x
                    sun['sun_dir_y'] = v.y
                    sun['sun_dir_z'] = v.z
        
        # and change this, just in case..
        import datetime
        n = datetime.datetime.now()
        if(sun['sun_date'] == "DD.MM.YYYY"):
            mx.sun_date = n.strftime('%d.%m.%Y')
            sun['sun_date'] = mx.sun_date
        if(sun['sun_time'] == "HH:MM"):
            mx.sun_time = n.strftime('%H:%M')
            sun['sun_time'] = mx.sun_time
        
        ibl = None
        if(env_type == 'IMAGE_BASED'):
            ibl = {'ibl_intensity': mx.ibl_intensity,
                   'ibl_interpolation': mx.ibl_interpolation,
                   'ibl_screen_mapping': mx.ibl_screen_mapping,
                   'ibl_bg_type': mx.ibl_bg_type,
                   'ibl_bg_map': bpy.path.abspath(mx.ibl_bg_map),
                   'ibl_bg_intensity': mx.ibl_bg_intensity,
                   'ibl_bg_scale_x': mx.ibl_bg_scale_x,
                   'ibl_bg_scale_y': mx.ibl_bg_scale_y,
                   'ibl_bg_offset_x': mx.ibl_bg_offset_x,
                   'ibl_bg_offset_y': mx.ibl_bg_offset_y,
                   'ibl_refl_type': mx.ibl_refl_type,
                   'ibl_refl_map': bpy.path.abspath(mx.ibl_refl_map),
                   'ibl_refl_intensity': mx.ibl_refl_intensity,
                   'ibl_refl_scale_x': mx.ibl_refl_scale_x,
                   'ibl_refl_scale_y': mx.ibl_refl_scale_y,
                   'ibl_refl_offset_x': mx.ibl_refl_offset_x,
                   'ibl_refl_offset_y': mx.ibl_refl_offset_y,
                   'ibl_refr_type': mx.ibl_refr_type,
                   'ibl_refr_map': bpy.path.abspath(mx.ibl_refr_map),
                   'ibl_refr_intensity': mx.ibl_refr_intensity,
                   'ibl_refr_scale_x': mx.ibl_refr_scale_x,
                   'ibl_refr_scale_y': mx.ibl_refr_scale_y,
                   'ibl_refr_offset_x': mx.ibl_refr_offset_x,
                   'ibl_refr_offset_y': mx.ibl_refr_offset_y,
                   'ibl_illum_type': mx.ibl_illum_type,
                   'ibl_illum_map': bpy.path.abspath(mx.ibl_illum_map),
                   'ibl_illum_intensity': mx.ibl_illum_intensity,
                   'ibl_illum_scale_x': mx.ibl_illum_scale_x,
                   'ibl_illum_scale_y': mx.ibl_illum_scale_y,
                   'ibl_illum_offset_x': mx.ibl_illum_offset_x,
                   'ibl_illum_offset_y': mx.ibl_illum_offset_y, }
        
        self.mxs.environment(env_type, sky_type, sky, dome, sun_type, sun, ibl, )
    
    def parameters(self):
        mx = self.context.scene.maxwell_render
        
        scene = {'cpu_threads': mx.scene_cpu_threads,
                 'multilight': int(mx.scene_multilight[-1:]),
                 'multilight_type': int(mx.scene_multilight_type[-1:]),
                 'quality': mx.scene_quality,
                 'sampling_level': mx.scene_sampling_level,
                 'time': mx.scene_time, }
        
        materials = {'override': mx.materials_override,
                     'override_path': bpy.path.abspath(mx.materials_override_path),
                     'search_path': bpy.path.abspath(mx.materials_search_path), }
        
        generals = {'diplacement': mx.globals_diplacement,
                    'dispersion': mx.globals_dispersion,
                    'motion_blur': mx.globals_motion_blur, }
        
        tone = {'burn': mx.tone_burn,
                'color_space': int(mx.tone_color_space.split('_')[1]),
                'gamma': mx.tone_gamma,
                'sharpness': mx.tone_sharpness,
                'sharpness_value': mx.tone_sharpness_value / 100.0,
                'tint': mx.tone_tint,
                'whitepoint': mx.tone_whitepoint, }
        
        simulens = {'aperture_map': bpy.path.abspath(mx.simulens_aperture_map),
                    'devignetting': mx.simulens_devignetting,
                    'devignetting_value': mx.simulens_devignetting_value / 100.0,
                    'diffraction': mx.simulens_diffraction,
                    'diffraction_value': maths.remap(mx.simulens_diffraction_value, 0.0, 2500.0, 0.0, 1.0),
                    'frequency': maths.remap(mx.simulens_frequency, 0.0, 2500.0, 0.0, 1.0),
                    'obstacle_map': bpy.path.abspath(mx.simulens_obstacle_map),
                    'scattering': mx.simulens_scattering,
                    'scattering_value': maths.remap(mx.simulens_scattering_value, 0.0, 2500.0, 0.0, 1.0), }
        
        illum_caustics = {'illumination': int(mx.illum_caustics_illumination[-1:]),
                          'refl_caustics': int(mx.illum_caustics_refl_caustics[-1:]),
                          'refr_caustics': int(mx.illum_caustics_refr_caustics[-1:]), }
        
        other = {'protect': mx.export_protect_mxs,
                 'extra_sampling_enabled': mx.extra_sampling_enabled,
                 'extra_sampling_sl': mx.extra_sampling_sl,
                 'extra_sampling_mask': int(mx.extra_sampling_mask[-1:]),
                 'extra_sampling_custom_alpha': mx.extra_sampling_custom_alpha,
                 'extra_sampling_user_bitmap': bpy.path.abspath(mx.extra_sampling_user_bitmap),
                 'extra_sampling_invert': mx.extra_sampling_invert, }
        
        self.mxs.parameters(scene, materials, generals, tone, simulens, illum_caustics, other, )
    
    def channels(self):
        mx = self.context.scene.maxwell_render
        
        mxi = None
        if(mx.output_mxi_enabled):
            mxi = bpy.path.abspath(mx.output_mxi)
        
        image = None
        image_depth = None
        if(mx.output_image_enabled):
            image = bpy.path.abspath(mx.output_image)
            image_depth = mx.output_depth
        
        if(mxi is not None):
            h, t = os.path.split(mxi)
            n, e = os.path.splitext(t)
            base_path = os.path.join(h, n)
        elif(image is not None):
            h, t = os.path.split(image)
            n, e = os.path.splitext(t)
            base_path = os.path.join(h, n)
        else:
            h, t = os.path.split(self.mxs_path)
            n, e = os.path.splitext(t)
            base_path = os.path.join(h, n)
        
        channels_output_mode = int(mx.channels_output_mode[-1:])
        channels_render = mx.channels_render
        channels_render_type = int(mx.channels_render_type[-1:])
        
        channels = {'channels_alpha': mx.channels_alpha,
                    'channels_alpha_file': mx.channels_alpha_file,
                    'channels_alpha_opaque': mx.channels_alpha_opaque,
                    'channels_custom_alpha': mx.channels_custom_alpha,
                    'channels_custom_alpha_file': mx.channels_custom_alpha_file,
                    'channels_deep': mx.channels_deep,
                    'channels_deep_file': mx.channels_deep_file,
                    'channels_deep_max_samples': mx.channels_deep_max_samples,
                    'channels_deep_min_dist': mx.channels_deep_min_dist,
                    'channels_deep_type': int(mx.channels_deep_type[-1:]),
                    'channels_fresnel': mx.channels_fresnel,
                    'channels_fresnel_file': mx.channels_fresnel_file,
                    'channels_material_id': mx.channels_material_id,
                    'channels_material_id_file': mx.channels_material_id_file,
                    'channels_motion_vector': mx.channels_motion_vector,
                    'channels_motion_vector_file': mx.channels_motion_vector_file,
                    'channels_normals': mx.channels_normals,
                    'channels_normals_file': mx.channels_normals_file,
                    'channels_normals_space': int(mx.channels_normals_space[-1:]),
                    'channels_object_id': mx.channels_object_id,
                    'channels_object_id_file': mx.channels_object_id_file,
                    'channels_position': mx.channels_position,
                    'channels_position_file': mx.channels_position_file,
                    'channels_position_space': int(mx.channels_position_space[-1:]),
                    'channels_roughness': mx.channels_roughness,
                    'channels_roughness_file': mx.channels_roughness_file,
                    'channels_shadow': mx.channels_shadow,
                    'channels_shadow_file': mx.channels_shadow_file,
                    'channels_uv': mx.channels_uv,
                    'channels_uv_file': mx.channels_uv_file,
                    'channels_z_buffer': mx.channels_z_buffer,
                    'channels_z_buffer_far': mx.channels_z_buffer_far,
                    'channels_z_buffer_file': mx.channels_z_buffer_file,
                    'channels_z_buffer_near': mx.channels_z_buffer_near, }
        
        self.mxs.channels(base_path, mxi, image, image_depth, channels_output_mode, channels_render, channels_render_type, channels, )
        
        groups = self.groups[:]
        if(len(groups) > 0):
            self.mxs.custom_alphas(groups)
    
    def ext_particles(self, o, pname=None, ):
        log("{0} ({1})".format(o['name'], o['type']), 2)
        
        name = o['name']
        if(pname is not None):
            name = pname
        
        base, pivot = self.matrix_to_base_and_pivot(o['matrix'])
        
        m = o['props']
        ps = o['ps']
        psm = ps.settings.maxwell_particles_extension
        
        pdata = {}
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
            sizes = []
            mat = o['pmatrix'].copy()
            mat.invert()
            for part in ps.particles:
                if(part.alive_state == "ALIVE"):
                    l = part.location.copy()
                    l = mat * l
                    # in case somebody is reading this and wondering why all those zeros
                    # i wrote all of this for converting pointcloud ply to a bin and those
                    # files were structured 3 loc, 3 normal, rgb (0-255) and quite a lot
                    # of code relied on it.. and was too lazy to remove redundant code.
                    locs.append(l.to_tuple() + (0.0, 0.0, 0.0, 0, 0, 0))
                    if(m.bl_use_velocity):
                        v = part.velocity.copy()
                        v = mat * v
                        vels.append(v.to_tuple() + (0.0, 0.0, 0.0, 0, 0, 0))
                    else:
                        vels.append((0.0, 0.0, 0.0) + (0.0, 0.0, 0.0, 0, 0, 0))
                    # size per particle
                    if(m.bl_use_size):
                        sizes.append(part.size / 2)
                    else:
                        sizes.append(m.bl_size / 2)
            locs = maths.apply_matrix_for_realflow_bin_export(locs)
            vels = maths.apply_matrix_for_realflow_bin_export(vels)
            particles = []
            for i, ploc in enumerate(locs):
                # normal from velocity
                pnor = Vector(vels[i][:3])
                pnor.normalize()
                particles.append((i, ) + tuple(ploc[:3]) + pnor.to_tuple() + tuple(vels[i][:3]) + (sizes[i], ))
            
            # if(os.path.exists(bpy.path.abspath(m.bin_directory)) and not m.bin_overwrite):
            #     raise OSError("file: {} exists".format(bpy.path.abspath(m.bin_directory)))
            #
            # cf = self.context.scene.frame_current
            # prms = {'directory': bpy.path.abspath(m.bin_directory),
            #         'name': "{}".format(name),
            #         'frame': cf,
            #         'particles': particles,
            #         'fps': self.context.scene.render.fps,
            #         'size': 1.0 if m.bl_use_size else m.bl_size / 2, }
            # rfbw = rfbin.RFBinWriter(**prms)
            # m.bin_filename = rfbw.path
            
            if(m.embed):
                plocs = [v[:3] for v in locs]
                pvels = [v[3:6] for v in vels]
                pnors = []
                for i, v in enumerate(pvels):
                    n = Vector(v)
                    n.normalize()
                    pnors.append(n)
                
                pdata = {'PARTICLE_POSITIONS': [v for l in plocs for v in l],
                         'PARTICLE_SPEEDS': [v for l in pvels for v in l],
                         'PARTICLE_RADII': [v for v in sizes],
                         'PARTICLE_IDS': [i for i in range(len(locs))],
                         'PARTICLE_NORMALS': [v for l in pnors for v in l],
                         # 'PARTICLE_FLAG_COLORS', [0], 0, 0, '8 BYTEARRAY', 1, 1, True)
                         # 'PARTICLE_COLORS', [0.0], 0.0, 0.0, '6 FLOATARRAY', 4, 1, True)
                         }
            else:
                if(os.path.exists(bpy.path.abspath(m.bin_directory)) and not m.bin_overwrite):
                    raise OSError("file: {} exists".format(bpy.path.abspath(m.bin_directory)))
            
                cf = self.context.scene.frame_current
                prms = {'directory': bpy.path.abspath(m.bin_directory),
                        'name': "{}".format(name),
                        'frame': cf,
                        'particles': particles,
                        'fps': self.context.scene.render.fps,
                        'size': 1.0 if m.bl_use_size else m.bl_size / 2, }
                rfbw = rfbin.RFBinWriter(**prms)
                m.bin_filename = rfbw.path
            
        else:
            # external particles
            if(m.bin_type == 'SEQUENCE'):
                # sequence
                cf = self.context.scene.frame_current
                if(m.seq_limit):
                    # get frame number from defined range
                    rng = [i for i in range(m.seq_start, m.seq_end + 1)]
                    try:
                        gf = rng[cf - 1]
                    except IndexError:
                        # current frame is out of limits, skip
                        return
                else:
                    gf = cf
                if(gf >= 0):
                    # try to find correct bin
                    m.private_bin_filename = m.bin_filename
                    sqpath = bpy.path.abspath(m.bin_filename)
                    fnm_re = r'^.*\d{5}\.bin$'
                    dnm, fnm = os.path.split(sqpath)
                    if(re.match(fnm_re, fnm)):
                        bnm = fnm[:-10]
                        sqbp = os.path.join(dnm, "{}-{}.bin".format(bnm, str(gf).zfill(5)))
                        if(os.path.exists(sqbp)):
                            m.bin_filename = sqbp
                        else:
                            # skip if file not found
                            log("cannot find .bin file for frame: {} at path: '{}'. skipping..".format(gf, sqbp), 3, LogStyles.WARNING, )
                            return
                    else:
                        # skip if not valid sequence name
                        log("cannot find .bin file for frame: {} at path: '{}'. skipping..".format(gf, sqpath), 3, LogStyles.WARNING, )
                        return
                else:
                    # skip, frame is out of limits
                    return
            else:
                # static particles, just take what is on path
                pass
        
        properties = {'filename': bpy.path.abspath(m.bin_filename),
                      
                      'embed': m.embed,
                      'pdata': pdata,
                      
                      'radius_multiplier': m.bin_radius_multiplier, 'motion_blur_multiplier': m.bin_motion_blur_multiplier, 'shutter_speed': m.bin_shutter_speed,
                      'load_particles': m.bin_load_particles, 'axis_system': int(m.bin_axis_system[-1:]), 'frame_number': m.bin_frame_number, 'fps': m.bin_fps, 'extra_create_np_pp': m.bin_extra_create_np_pp,
                      'extra_dispersion': m.bin_extra_dispersion, 'extra_deformation': m.bin_extra_deformation, 'load_force': int(m.bin_load_force), 'load_vorticity': int(m.bin_load_vorticity),
                      'load_normal': int(m.bin_load_normal), 'load_neighbors_num': int(m.bin_load_neighbors_num), 'load_uv': int(m.bin_load_uv), 'load_age': int(m.bin_load_age),
                      'load_isolation_time': int(m.bin_load_isolation_time), 'load_viscosity': int(m.bin_load_viscosity), 'load_density': int(m.bin_load_density), 'load_pressure': int(m.bin_load_pressure),
                      'load_mass': int(m.bin_load_mass), 'load_temperature': int(m.bin_load_temperature), 'load_id': int(m.bin_load_id), 'min_force': m.bin_min_force, 'max_force': m.bin_max_force,
                      'min_vorticity': m.bin_min_vorticity, 'max_vorticity': m.bin_max_vorticity, 'min_nneighbors': m.bin_min_nneighbors, 'max_nneighbors': m.bin_max_nneighbors, 'min_age': m.bin_min_age,
                      'max_age': m.bin_max_age, 'min_isolation_time': m.bin_min_isolation_time, 'max_isolation_time': m.bin_max_isolation_time, 'min_viscosity': m.bin_min_viscosity,
                      'max_viscosity': m.bin_max_viscosity, 'min_density': m.bin_min_density, 'max_density': m.bin_max_density, 'min_pressure': m.bin_min_pressure, 'max_pressure': m.bin_max_pressure,
                      'min_mass': m.bin_min_mass, 'max_mass': m.bin_max_mass, 'min_temperature': m.bin_min_temperature, 'max_temperature': m.bin_max_temperature, 'min_velocity': m.bin_min_velocity,
                      'max_velocity': m.bin_max_velocity, }
        
        if(m.source == 'EXTERNAL_BIN'):
            properties['embed'] = False
        
        object_props = (psm.hide, psm.opacity, self.color_to_rgb8(psm.object_id), psm.hidden_camera, psm.hidden_camera_in_shadow_channel,
                        psm.hidden_global_illumination, psm.hidden_reflections_refractions, psm.hidden_zclip_planes, )
        
        material = (bpy.path.abspath(m.material), m.material_embed, )
        if(material[0] != "" and not os.path.exists(material[0])):
            log("{1}: mxm ('{0}') does not exist.".format(material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            material = None
        backface_material = (bpy.path.abspath(m.backface_material), m.backface_material_embed, )
        if(backface_material[0] != "" and not os.path.exists(backface_material[0])):
            log("{1}: backface mxm ('{0}') does not exist.".format(backface_material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            backface_material = None
        
        self.mxs.ext_particles(name, properties, base, pivot, object_props, material, backface_material, )
        
        parent = None
        if(o['parent']):
            parent = o['parent']
        self.hierarchy.append((name, parent))
    
    def grass(self, o, ):
        log("{0} ({1})".format(o['name'], o['type']), 2)
        
        object_name = o['parent']
        
        m = o['props']
        ps = o['ps']
        ob = o['object']
        
        properties = {'density': int(m.density),
                      'density_map': self.psys_texture_to_data(m.density_map, ps, ob, ),
                      'length': m.length,
                      'length_map': self.psys_texture_to_data(m.length_map, ps, ob, ),
                      'length_variation': m.length_variation,
                      'root_width': m.root_width,
                      'tip_width': m.tip_width,
                      'direction_type': int(m.direction_type),
                      'initial_angle': math.degrees(m.initial_angle),
                      'initial_angle_map': self.psys_texture_to_data(m.initial_angle_map, ps, ob, ),
                      'initial_angle_variation': m.initial_angle_variation,
                      'start_bend': m.start_bend,
                      'start_bend_map': self.psys_texture_to_data(m.start_bend_map, ps, ob, ),
                      'start_bend_variation': m.start_bend_variation,
                      'bend_radius': m.bend_radius,
                      'bend_radius_map': self.psys_texture_to_data(m.bend_radius_map, ps, ob, ),
                      'bend_radius_variation': m.bend_radius_variation,
                      'bend_angle': math.degrees(m.bend_angle),
                      'bend_angle_map': self.psys_texture_to_data(m.bend_angle_map, ps, ob, ),
                      'bend_angle_variation': m.bend_angle_variation,
                      'cut_off': m.cut_off,
                      'cut_off_map': self.psys_texture_to_data(m.cut_off_map, ps, ob, ),
                      'cut_off_variation': m.cut_off_variation,
                      'points_per_blade': int(m.points_per_blade),
                      'primitive_type': int(m.primitive_type),
                      'seed': m.seed,
                      'lod': m.lod,
                      'lod_max_distance': m.lod_max_distance,
                      'lod_max_distance_density': m.lod_max_distance_density,
                      'lod_min_distance': m.lod_min_distance,
                      'display_max_blades': int(m.display_max_blades),
                      'display_percent': int(m.display_percent), }
        
        material = (bpy.path.abspath(m.material), m.material_embed, )
        if(material[0] != "" and not os.path.exists(material[0])):
            log("{1}: mxm ('{0}') does not exist.".format(material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            material = None
        backface_material = (bpy.path.abspath(m.backface_material), m.backface_material_embed, )
        if(backface_material[0] != "" and not os.path.exists(backface_material[0])):
            log("{1}: backface mxm ('{0}') does not exist.".format(backface_material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            backface_material = None
        
        self.mxs.mod_grass(object_name, properties, material, backface_material, )
    
    def hair(self, o, pname=None, ):
        log("{0} ({1})".format(o['name'], o['type']), 2)
        
        name = o['name']
        if(pname is not None):
            name = pname
        
        base, pivot = self.matrix_to_base_and_pivot(o['matrix'])
        
        m = o['props']
        ps = o['ps']
        psm = ps.settings.maxwell_particles_extension
        
        ob = bpy.data.objects[o['object'].name]
        ps.set_resolution(self.context.scene, ob, 'RENDER')
        
        mat = Matrix.Rotation(math.radians(-90.0), 4, 'X')
        transform = ob.matrix_world.inverted()
        omw = ob.matrix_world
        
        steps = 2 ** ps.settings.render_step
        num_curves = len(ps.particles) if len(ps.child_particles) == 0 else len(ps.child_particles)
        points = []
        for p in range(0, num_curves):
            seg_length = 1.0
            curve = []
            
            for step in range(0, steps):
                co = ps.co_hair(ob, p, step)
                
                # get distance between last and this point
                if(step > 0):
                    seg_length = (co - omw * curve[len(curve) - 1]).length_squared
                
                if not (co.length_squared == 0 or seg_length == 0):
                    # if it is not zero append as new point
                    v = transform * co
                    v = mat * v
                    curve.append(v)
            
            points.append(curve)
        
        ps.set_resolution(self.context.scene, ob, 'PREVIEW')
        
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
        
        data = {'HAIR_MAJOR_VER': [1, 0, 0, 0],
                'HAIR_MINOR_VER': [0, 0, 0, 0],
                'HAIR_FLAG_ROOT_UVS': [0],
                'HAIR_GUIDES_COUNT': [num_curves],
                'HAIR_GUIDES_POINT_COUNT': [steps],
                'HAIR_POINTS': locs,
                'HAIR_NORMALS': [1.0], }
        
        if(m.hair_type == 'GRASS'):
            extension = 'MGrassP'
            if(o['parent'] is None):
                root_radius = maths.real_length_to_relative(o['matrix'], m.grass_root_width) / 1000
                tip_radius = maths.real_length_to_relative(o['matrix'], m.grass_tip_width) / 1000
            else:
                root_radius = maths.real_length_to_relative(ob.matrix_world, m.grass_root_width) / 1000
                tip_radius = maths.real_length_to_relative(ob.matrix_world, m.grass_tip_width) / 1000
            display_max = m.display_max_blades
        else:
            extension = 'MaxwellHair'
            if(o['parent'] is None):
                root_radius = maths.real_length_to_relative(o['matrix'], m.hair_root_radius) / 1000
                tip_radius = maths.real_length_to_relative(o['matrix'], m.hair_tip_radius) / 1000
            else:
                root_radius = maths.real_length_to_relative(ob.matrix_world, m.hair_root_radius) / 1000
                tip_radius = maths.real_length_to_relative(ob.matrix_world, m.hair_tip_radius) / 1000
            display_max = m.display_max_hairs
        display_percent = int(m.display_percent)
        
        object_props = (psm.hide, psm.opacity, self.color_to_rgb8(psm.object_id), psm.hidden_camera, psm.hidden_camera_in_shadow_channel,
                        psm.hidden_global_illumination, psm.hidden_reflections_refractions, psm.hidden_zclip_planes, )
        
        material = (bpy.path.abspath(m.material), m.material_embed, )
        if(material[0] != "" and not os.path.exists(material[0])):
            log("{1}: mxm ('{0}') does not exist.".format(material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            material = None
        backface_material = (bpy.path.abspath(m.backface_material), m.backface_material_embed, )
        if(backface_material[0] != "" and not os.path.exists(backface_material[0])):
            log("{1}: backface mxm ('{0}') does not exist.".format(backface_material[0], self.__class__.__name__), 2, LogStyles.WARNING, )
            backface_material = None
        
        self.mxs.ext_hair(name, extension, base, pivot, root_radius, tip_radius, data, object_props, display_percent, display_max, material, backface_material, )
        
        parent = None
        if(o['parent']):
            parent = o['parent']
        self.hierarchy.append((name, parent))
    
    def cloner(self, o, ):
        log("{0} ({1})".format(o['name'], o['type']), 2)
        
        m = o['props']
        ps = o['ps']
        psm = ps.settings.maxwell_cloner_extension
        
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
            sizes = []
            mat = o['pmatrix'].copy()
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
                    # size per particle
                    if(m.bl_use_size):
                        sizes.append(part.size)
                    else:
                        sizes.append(m.bl_size)
            locs = maths.apply_matrix_for_realflow_bin_export(locs)
            vels = maths.apply_matrix_for_realflow_bin_export(vels)
            particles = []
            for i, ploc in enumerate(locs):
                pnor = Vector(vels[i][:3])
                pnor.normalize()
                particles.append((i, ) + tuple(ploc[:3]) + pnor.to_tuple() + tuple(vels[i][:3]) + (sizes[i], ))
            
            if(os.path.exists(bpy.path.abspath(m.directory)) and not m.overwrite):
                raise OSError("file: {} exists".format(bpy.path.abspath(m.directory)))
            
            cf = self.context.scene.frame_current
            prms = {'directory': bpy.path.abspath(m.directory),
                    'name': "{}".format(o['name']),
                    'frame': cf,
                    'particles': particles,
                    'fps': self.context.scene.render.fps,
                    'size': 1.0 if m.bl_use_size else m.bl_size / 2, }
            rfbw = rfbin.RFBinWriter(**prms)
            m.filename = rfbw.path
        
        cloned = None
        try:
            cloned = ps.settings.dupli_object.name
        except AttributeError:
            log("{}: {}: Maxwell Cloner: cloned object is not available. Skipping..".format(o.name, ps.name), 1, LogStyles.WARNING, )
        
        if(cloned is not None):
            d = {'object_name': o['parent'],
                 'cloned_object': ps.settings.dupli_object.name,
                 'render_emitter': ps.settings.use_render_emitter,
                 'path': bpy.path.abspath(m.filename),
                 'radius': m.radius,
                 'mb_factor': m.mb_factor,
                 'load_percent': m.load_percent,
                 'start_offset': m.start_offset,
                 'ex_npp': m.extra_npp,
                 'ex_p_dispersion': m.extra_p_dispersion,
                 'ex_p_deformation': m.extra_p_deformation,
                 'align_to_velocity': m.align_to_velocity,
                 'scale_with_radius': m.scale_with_radius,
                 'inherit_obj_id': m.inherit_obj_id,
                 'frame': self.context.scene.frame_current,
                 'fps': self.context.scene.render.fps,
                 'display_percent': int(m.display_percent),
                 'display_max': int(m.display_max), }
            self.mxs.mod_cloner(**d)
    
    def object_extensions(self, o, ):
        ob = o['object']
        
        sd = ob.maxwell_subdivision_extension
        if(sd.enabled):
            log("{0}".format("Subdivision"), 3)
            self.mxs.mod_subdivision(ob.name, int(sd.level), int(sd.scheme), int(sd.interpolation), sd.crease, math.degrees(sd.smooth), )
        
        sc = ob.maxwell_scatter_extension
        if(sc.enabled):
            log("{0}".format("Scatter"), 3)
            if(sc.scatter_object == ''):
                log("{}: no scatter object, skipping Maxwell Scatter modifier..".format(ob.name), 3, LogStyles.WARNING, )
            else:
                density = (sc.density, self.mod_texture_to_data(sc.density_map), )
                scale = (sc.scale_x, sc.scale_y, sc.scale_z, self.mod_texture_to_data(sc.scale_map), sc.scale_variation_x, sc.scale_variation_y, sc.scale_variation_z, )
                rotation = (math.degrees(sc.rotation_x), math.degrees(sc.rotation_y), math.degrees(sc.rotation_z), self.mod_texture_to_data(sc.rotation_map), sc.rotation_variation_x, sc.rotation_variation_y, sc.rotation_variation_z, int(sc.rotation_direction), )
                lod = (int(sc.lod), sc.lod_min_distance, sc.lod_max_distance, sc.lod_max_distance_density, )
                self.mxs.mod_scatter(ob.name, sc.scatter_object, sc.inherit_objectid, density, int(sc.seed), scale, rotation, lod, int(sc.display_percent), int(sc.display_max_blades), )
        
        ms = ob.maxwell_sea_extension
        if(ms.enabled):
            log("{0}".format("Sea"), 3)
            name = "{}-MaxwellSea".format(ob.name)
            base, pivot = self.matrix_to_base_and_pivot(Matrix())
            geometry = (ms.reference_time, int(ms.resolution), ms.ocean_depth, ms.vertical_scale, ms.ocean_dim, ms.ocean_seed, ms.enable_choppyness, ms.choppy_factor, )
            wind = (ms.ocean_wind_mod, ms.ocean_wind_dir, ms.ocean_wind_alignment, ms.ocean_min_wave_length, ms.damp_factor_against_wind, )
            d = {'num_materials': len(ob.material_slots),
                 'materials': [], }
            d = self.object_materials(ob, d)
            material = None
            if(d['num_materials'] != 0):
                # take just the first one, no multimaterial possible
                material = (d['materials'][0][1], d['materials'][0][0])
            backface_material = None
            if(len(d['backface_material']) != 0):
                backface_material = (d['backface_material'][0], d['backface_material'][1])
            self.mxs.ext_sea(name, base, pivot, self.get_object_props(ob), geometry, wind, material, backface_material, )
    
    def ext_material(self, mat, o, ):
        m = mat.maxwell_render
        mx = mat.maxwell_material_extension
        
        def texture_to_data(name):
            if(name == ""):
                return None
            tex = bpy.data.textures[name]
            if(tex.type != 'IMAGE'):
                return None
            
            m = tex.maxwell_render
            d = {'type': 'IMAGE',
                 'path': bpy.path.abspath(tex.image.filepath),
                 'channel': 0,
                 'use_override_map': m.use_global_map,
                 'tile_method_type': [True, True],
                 'tile_method_units': int(m.tiling_units[-1:]),
                 'repeat': [m.repeat[0], m.repeat[1]],
                 'mirror': [m.mirror_x, m.mirror_y],
                 'offset': [m.offset[0], m.offset[1]],
                 'rotation': m.rotation,
                 'invert': m.invert,
                 'alpha_only': m.use_alpha,
                 'interpolation': m.interpolation,
                 'brightness': m.brightness,
                 'contrast': m.contrast,
                 'saturation': m.saturation,
                 'hue': m.hue,
                 'rgb_clamp': [m.clamp[0], m.clamp[1]], }
            
            if(m.tiling_method == 'NO_TILING'):
                tm = [False, False]
            elif(m.tiling_method == 'TILE_X'):
                tm = [True, False]
            elif(m.tiling_method == 'TILE_Y'):
                tm = [False, True]
            else:
                tm = [True, True]
            d['tile_method_type'] = tm
            
            slot = None
            for ts in mat.texture_slots:
                if(ts is not None):
                    if(ts.texture is not None):
                        if(ts.texture.name == name):
                            slot = ts
                            break
            
            for i, uv in enumerate(o.data.uv_textures):
                if(uv.name == slot.uv_layer):
                    d['channel'] = i
                    break
            
            return d
        
        if(m.use == 'EMITTER'):
            d = {'type': 'EMITTER',
                 'name': mat.name,
                 'emitter_type': int(mx.emitter_type),
                 'emitter_ies_data': bpy.path.abspath(mx.emitter_ies_data),
                 'emitter_ies_intensity': mx.emitter_ies_intensity,
                 'emitter_spot_map_enabled': mx.emitter_spot_map_enabled,
                 'emitter_spot_map': texture_to_data(mx.emitter_spot_map),
                 'emitter_spot_cone_angle': math.degrees(mx.emitter_spot_cone_angle),
                 'emitter_spot_falloff_angle': math.degrees(mx.emitter_spot_falloff_angle),
                 'emitter_spot_falloff_type': int(mx.emitter_spot_falloff_type),
                 'emitter_spot_blur': mx.emitter_spot_blur,
                 'emitter_emission': int(mx.emitter_emission),
                 'emitter_color': self.color_to_rgb8(mx.emitter_color),
                 'emitter_color_black_body_enabled': mx.emitter_color_black_body_enabled,
                 'emitter_color_black_body': mx.emitter_color_black_body,
                 'emitter_luminance': int(mx.emitter_luminance),
                 'emitter_luminance_power': mx.emitter_luminance_power,
                 'emitter_luminance_efficacy': mx.emitter_luminance_efficacy,
                 'emitter_luminance_output': mx.emitter_luminance_output,
                 'emitter_temperature_value': mx.emitter_temperature_value,
                 'emitter_hdr_map': texture_to_data(mx.emitter_hdr_map),
                 'emitter_hdr_intensity': mx.emitter_hdr_intensity, }
        elif(m.use == 'AGS'):
            d = {'type': 'AGS',
                 'name': mat.name,
                 'ags_color': self.color_to_rgb8(mx.ags_color),
                 'ags_reflection': mx.ags_reflection,
                 'ags_type': int(mx.ags_type), }
        elif(m.use == 'OPAQUE'):
            d = {'type': 'OPAQUE',
                 'name': mat.name,
                 'opaque_color_type': mx.opaque_color_type,
                 'opaque_color': self.color_to_rgb8(mx.opaque_color),
                 'opaque_color_map': texture_to_data(mx.opaque_color_map),
                 'opaque_shininess_type': mx.opaque_shininess_type,
                 'opaque_shininess': mx.opaque_shininess,
                 'opaque_shininess_map': texture_to_data(mx.opaque_shininess_map),
                 'opaque_roughness_type': mx.opaque_roughness_type,
                 'opaque_roughness': mx.opaque_roughness,
                 'opaque_roughness_map': texture_to_data(mx.opaque_roughness_map),
                 'opaque_clearcoat': mx.opaque_clearcoat, }
        elif(m.use == 'TRANSPARENT'):
            d = {'type': 'TRANSPARENT',
                 'name': mat.name,
                 'transparent_color_type': mx.transparent_color_type,
                 'transparent_color': self.color_to_rgb8(mx.transparent_color),
                 'transparent_color_map': texture_to_data(mx.transparent_color_map),
                 'transparent_ior': mx.transparent_ior,
                 'transparent_transparency': mx.transparent_transparency,
                 'transparent_roughness_type': mx.transparent_roughness_type,
                 'transparent_roughness': mx.transparent_roughness,
                 'transparent_roughness_map': texture_to_data(mx.transparent_roughness_map),
                 'transparent_specular_tint': mx.transparent_specular_tint,
                 'transparent_dispersion': mx.transparent_dispersion,
                 'transparent_clearcoat': mx.transparent_clearcoat, }
        elif(m.use == 'METAL'):
            d = {'type': 'METAL',
                 'name': mat.name,
                 'metal_ior': int(mx.metal_ior),
                 'metal_tint': mx.metal_tint,
                 'metal_color_type': mx.metal_color_type,
                 'metal_color': self.color_to_rgb8(mx.metal_color),
                 'metal_color_map': texture_to_data(mx.metal_color_map),
                 'metal_roughness_type': mx.metal_roughness_type,
                 'metal_roughness': mx.metal_roughness,
                 'metal_roughness_map': texture_to_data(mx.metal_roughness_map),
                 'metal_anisotropy_type': mx.metal_anisotropy_type,
                 'metal_anisotropy': mx.metal_anisotropy,
                 'metal_anisotropy_map': texture_to_data(mx.metal_anisotropy_map),
                 'metal_angle_type': mx.metal_angle_type,
                 'metal_angle': mx.metal_angle,
                 'metal_angle_map': texture_to_data(mx.metal_angle_map),
                 'metal_dust_type': mx.metal_dust_type,
                 'metal_dust': mx.metal_dust,
                 'metal_dust_map': texture_to_data(mx.metal_dust_map),
                 'metal_perforation_enabled': mx.metal_perforation_enabled,
                 'metal_perforation_map': texture_to_data(mx.metal_perforation_map), }
        elif(m.use == 'TRANSLUCENT'):
            d = {'type': 'TRANSLUCENT',
                 'name': mat.name,
                 'translucent_scale': mx.translucent_scale,
                 'translucent_ior': mx.translucent_ior,
                 'translucent_color_type': mx.translucent_color_type,
                 'translucent_color': self.color_to_rgb8(mx.translucent_color),
                 'translucent_color_map': texture_to_data(mx.translucent_color_map),
                 'translucent_hue_shift': mx.translucent_hue_shift,
                 'translucent_invert_hue': mx.translucent_invert_hue,
                 'translucent_vibrance': mx.translucent_vibrance,
                 'translucent_density': mx.translucent_density,
                 'translucent_opacity': mx.translucent_opacity,
                 'translucent_roughness_type': mx.translucent_roughness_type,
                 'translucent_roughness': mx.translucent_roughness,
                 'translucent_roughness_map': texture_to_data(mx.translucent_roughness_map),
                 'translucent_specular_tint': mx.translucent_specular_tint,
                 'translucent_clearcoat': mx.translucent_clearcoat,
                 'translucent_clearcoat_ior': mx.translucent_clearcoat_ior, }
        elif(m.use == 'CARPAINT'):
            d = {'type': 'CARPAINT',
                 'name': mat.name,
                 'carpaint_color': self.color_to_rgb8(mx.carpaint_color),
                 'carpaint_metallic': mx.carpaint_metallic,
                 'carpaint_topcoat': mx.carpaint_topcoat, }
        # elif(m.use == 'HAIR'):
        #     pass
        else:
            # CUSTOM
            raise ValueError('materials of type CUSTOM should be handled somewhere else..')
        
        return (True, d, )


class MXSExportWireframe(MXSExport):
    def __init__(self, context, mxs_path, use_instances=True, edge_radius=0.00025, edge_resolution=32, wire_mat={}, clay_mat={}, ):
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
        
        super(MXSExportWireframe, self).__init__(context, mxs_path, use_instances, )
    
    def export(self):
        super(MXSExportWireframe, self).export()
        
        # wireframe
        self.uuid = uuid.uuid1()
        log("making wire materials..", 1, LogStyles.MESSAGE)
        wm = self.mxs.wire_material("wire_material", wire_mat['reflectance_0'], wire_mat['reflectance_90'], wire_mat['id'], wire_mat['roughness'], )
        self.wm = wm.getName()
        cm = self.mxs.wire_material("clay_material", wire_mat['reflectance_0'], wire_mat['reflectance_90'], wire_mat['id'], wire_mat['roughness'], )
        self.cm = cm.getName()
        
        log("making wire base mesh..", 1, LogStyles.MESSAGE)
        self._wire_base()
        
        log("processing wires..", 1, LogStyles.MESSAGE)
        self._wire_objects()
        
        log("processing hierarchy..", 1, LogStyles.MESSAGE)
        self._wire_hierarchy(self.wireframe_edge_name)
        
        # save again..
        self.mxs.write()
    
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
             'type': ob.type, }
        self.mxs.mesh(o)
        self.wireframe_edge_name = ob.name
        utils.wipe_out_object(ob, and_data=True)
    
    def _wire_objects(self):
        """Loop over all renderable objects and prepare wire data for pymaxwell."""
        eo = self.meshes[:] + self.bases[:] + self.instances[:] + self.duplicates[:]
        
        for o in eo:
            log("{0}".format(o['object'].name), 2)
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
            ms = self._calc_marices(vs=vs, es=es, )
            
            self.mxs.wire_instances(self.wireframe_edge_name, ob.name, ms, None, self.wm, )
            
            bpy.data.meshes.remove(me)
    
    def _calc_marices(self, vs, es, ):
        """Calculate wire matrices."""
        
        def distance(a, b):
            return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5
        
        matrices = []
        up = Vector((0, 0, 1))
        for i, e in enumerate(es):
            a = vs[e[0]]
            b = vs[e[1]]
            d = distance(a, b)
            quat = maths.rotation_to(Vector((0, 0, 1)), b - a)
            mr = quat.to_matrix().to_4x4()
            mt = Matrix.Translation(a)
            mtr = mt * mr
            ms = Matrix.Scale(d, 4, up)
            m = mtr * ms
            matrices.append(m)
        
        return matrices
