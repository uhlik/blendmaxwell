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

bl_info = {"name": "Maxwell Render",
           "description": "Maxwell Render integration",
           "author": "Jakub Uhlik",
           "version": (0, 1, 3),
           "blender": (2, 73, 0),
           "location": "Info header > render engine menu",
           "warning": "Currently only Mac OS X is fully supported",
           "wiki_url": "",
           "tracker_url": "",
           "category": "Render", }


if "bpy" in locals():
    import imp
    imp.reload(log)
    imp.reload(progress)
    imp.reload(app)
    imp.reload(maths)
    imp.reload(utils)
    imp.reload(engine)
    imp.reload(props)
    imp.reload(ops)
    imp.reload(ui)
    imp.reload(export)
else:
    from . import log
    from . import progress
    from . import app
    from . import maths
    from . import utils
    from . import engine
    from . import props
    from . import ops
    from . import ui
    from . import export


import os
import platform
import bpy
from bpy.props import StringProperty


class MaxwellRenderPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    python34_path = StringProperty(name="Python 3.4 Directory", default="", subtype='DIR_PATH', description="", )
    maxwell_path = StringProperty(name="Maxwell Render Directory", default="", subtype='DIR_PATH', description="", )
    
    def draw(self, context):
        l = self.layout
        l.prop(self, "python34_path")
        l.prop(self, "maxwell_path")


def get_selected_panels():
    l = ['DATA_PT_camera_display', 'bl_ui.properties_data_mesh', 'bl_ui.properties_particle',
         'bl_ui.properties_render_layer', 'bl_ui.properties_texture', ]
    e = ['DATA_PT_normals', 'DATA_PT_texture_space', 'DATA_PT_customdata', 'DATA_PT_custom_props_mesh',
         'RENDERLAYER_PT_layer_options', 'RENDERLAYER_PT_layer_passes', 'RENDERLAYER_UL_renderlayers', ]
    a = get_all_panels()
    r = []
    for p in a:
        if(p.__name__ in l or p.__module__ in l):
            if(p.__name__ not in e and p.__module__ not in e):
                r.append(p)
    return r


def get_all_panels():
    ts = dir(bpy.types)
    r = []
    for t in ts:
        o = getattr(bpy.types, t)
        if(hasattr(o, 'COMPAT_ENGINES')):
            if('BLENDER_RENDER' in o.COMPAT_ENGINES):
                r.append(o)
    return r


def register():
    s = platform.system()
    if(s == 'Windows'):
        raise OSError("Windows are not supported at the moment..")
    
    # bpy.utils.register_module(__name__, verbose=True)
    bpy.utils.register_module(__name__)
    
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    if(p.python34_path == '' or p.maxwell_path == ''):
        s = platform.system()
        if(s == 'Darwin'):
            p.python34_path = '/Library/Frameworks/Python.framework/Versions/3.4/'
            p.maxwell_path = '/Applications/Maxwell 3/'
        elif(s == 'Linux'):
            p.python34_path = '/usr/bin/'
            p.maxwell_path = os.environ.get("MAXWELL3_ROOT")
        elif(s == 'Windows'):
            pass
        else:
            raise OSError("Unknown platform: {}.".format(s))
    else:
        # user set something, leave it as it is
        pass
    
    # for p in get_all_panels():
    for p in get_selected_panels():
        p.COMPAT_ENGINES.add(engine.MaxwellRenderExportEngine.bl_idname)


def unregister():
    # bpy.utils.unregister_module(__name__, verbose=True)
    bpy.utils.unregister_module(__name__)
    
    # for p in get_all_panels():
    for p in get_selected_panels():
        p.COMPAT_ENGINES.remove(engine.MaxwellRenderExportEngine.bl_idname)


if __name__ == "__main__":
    register()
