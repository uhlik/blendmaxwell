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
import platform
import subprocess
import shlex

import bpy

from .log import log, LogStyles, LOG_FILE_PATH


PLATFORM = platform.system()


def prefs():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    return p


def check_for_pymaxwell():
    if(PLATFORM == 'Darwin'):
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'bin', 'python3.4', ))
        PYMAXWELL_SO = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'lib', 'python3.4', 'site-packages', '_pymaxwell.so', ))
        PYMAXWELL_PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'lib', 'python3.4', 'site-packages', 'pymaxwell.py', ))
    elif(PLATFORM == 'Linux'):
        # # import site
        # # site.getsitepackages()
        # self.PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'python3.4', ))
        # self.PYMAXWELL_SO = os.path.join('/usr/local/lib/python3.4/site-packages', '_pymaxwell.so', )
        # self.PYMAXWELL_PY = os.path.join('/usr/local/lib/python3.4/site-packages', 'pymaxwell.py', )
        pass
    elif(PLATFORM == 'Windows'):
        pass
    else:
        raise OSError("Unknown platform: {}.".format(PLATFORM))
    
    ok = (os.path.exists(PY) and os.path.exists(PYMAXWELL_SO) and os.path.exists(PYMAXWELL_PY))
    if(ok):
        return True
    
    log("{}: ERROR: python 3.4 with pymaxwell seems not to be installed..".format(self.__class__.__name__), 1, LogStyles.ERROR, )
    raise OSError("python 3.4 with pymaxwell seems not to be installed..")
    return False


def check_for_template():
    # check for template
    TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "export_mxs.py")
    if(not os.path.exists(TEMPLATE)):
        log("{}: ERROR: support directory is missing..".format(self.__class__.__name__), 1, LogStyles.ERROR, )
        raise OSError("support directory is missing..")
    return TEMPLATE


def open_file_in_default_application(path):
    if(PLATFORM == 'Darwin'):
        os.system("open {}".format(shlex.quote(path)))
    elif(PLATFORM == 'Linux'):
        subprocess.call(["xdg-open", shlex.quote(path)])
    elif(PLATFORM == 'Windows'):
        os.system("start {}".format(shlex.quote(path)))
    else:
        pass


def mxed_create_material_helper(path):
    if(PLATFORM == 'Darwin'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Mxed.app', 'Contents', 'MacOS', 'Mxed', )))
        command_line = "{0} -new:'{1}'".format(app, path, )
        args = shlex.split(command_line, )
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Linux'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'mxed', )))
        command_line = "nohup {0} -new:'{1}'".format(app, path, )
        args = shlex.split(command_line, )
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Windows'):
        pass
    else:
        pass


def mxed_edit_material_helper(path):
    if(PLATFORM == 'Darwin'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Mxed.app', 'Contents', 'MacOS', 'Mxed', )))
        command_line = "{0} -mxm:'{1}'".format(app, path, )
        args = shlex.split(command_line, )
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Linux'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'mxed', )))
        command_line = "nohup {0} -mxm:'{1}'".format(app, path, )
        args = shlex.split(command_line, )
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Windows'):
        pass
    else:
        pass


def studio_open_mxs_helper(path, instance):
    if(PLATFORM == 'Darwin'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Studio.app', ))
        if(instance):
            app = os.path.join(app, "Contents/MacOS/Studio")
            command_line = '{0} -mxs:{1}'.format(shlex.quote(app), shlex.quote(path))
        else:
            command_line = 'open -a {0} {1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args)
    elif(PLATFORM == 'Linux'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio', ))
        command_line = 'nohup {0} {1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Windows'):
        # app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio.exe', ))
        # os.startfile(os.path.normpath(path))
        pass
    else:
        pass


def maxwell_open_mxs_helper(path, instance):
    if(PLATFORM == 'Darwin'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Maxwell.app', ))
        if(instance):
            app = os.path.join(app, "Contents/MacOS/Maxwell")
            command_line = '{0} -mxs:{1}'.format(shlex.quote(app), shlex.quote(path))
        else:
            command_line = 'open -a {0} {1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args)
    elif(PLATFORM == 'Linux'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio', ))
        command_line = 'nohup {0} {1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Windows'):
        # app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio.exe', ))
        # os.startfile(os.path.normpath(path))
        pass
    else:
        pass


def python34_run_script_helper(script_path, scene_data_path, mxs_path, append, instancer, wireframe, ):
    if(PLATFORM == 'Darwin' or PLATFORM == 'Linux'):
        switches = ''
        if(append):
            switches += '-a'
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
        
        PY = ""
        if(PLATFORM == 'Darwin'):
            PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'bin', 'python3.4', ))
        if(PLATFORM == 'Linux'):
            PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python34_path), 'python3.4', ))
        if(PY == ""):
            raise Exception("huh?")
        
        if(switches != ''):
            command_line = "{0} {1} {2} {3} {4} {5}".format(shlex.quote(PY),
                                                            shlex.quote(script_path),
                                                            switches,
                                                            shlex.quote(LOG_FILE_PATH),
                                                            shlex.quote(scene_data_path),
                                                            shlex.quote(mxs_path), )
        else:
            command_line = "{0} {1} {2} {3} {4}".format(shlex.quote(PY),
                                                        shlex.quote(script_path),
                                                        shlex.quote(LOG_FILE_PATH),
                                                        shlex.quote(scene_data_path),
                                                        shlex.quote(mxs_path), )
        
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
        raise OSError("Unknown platform: {}.".format(PLATFORM))
