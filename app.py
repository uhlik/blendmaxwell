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
import platform

import bpy


def prefs():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    return p


def _check_extension(check_path, check_ext):
    if(check_ext.startswith(".") is False):
        check_ext = ".{0}".format(check_ext)
    head, tail = os.path.split(check_path)
    name, ext = os.path.splitext(tail)
    if(ext == check_ext):
        return True
    return False


def _check_file_path(check_path):
    if(os.path.isdir(check_path)):
        return False
    # head, tail = os.path.split(check_path)
    # if(tail==""):
    #     return False
    return True


def _open_in_application(application, file_path):
    path = os.path.realpath(file_path)
    s = platform.system()
    if(s == 'Darwin'):
        app = shlex.quote(application)
        command_line = 'open -a {0} {1}'.format(app, path)
        args = shlex.split(command_line)
        p = subprocess.Popen(args)
    elif(s == 'Linux'):
        # subprocess.Popen(['xdg-open', d], )
        
        app = shlex.quote(application)
        command_line = 'nohup {0} {1}'.format(app, path)
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
        
    elif(s == 'Windows'):
        # os.startfile(os.path.normpath(d))
        pass
    else:
        raise OSError("Unknown platform: {}.".format(s))


def open_mxs_in_studio(file_path):
    if(type(file_path) is str):
        if(file_path != ""):
            if(_check_file_path(file_path)):
                if(_check_extension(file_path, ".mxs")):
                    p = os.path.realpath(file_path)
                else:
                    raise ValueError("open_mxs_in_studio: file_path must end with .mxs")
            else:
                raise ValueError("open_mxs_in_studio: file_path seems to be a directory")
        else:
            raise ValueError("open_mxs_in_studio: file_path in an empty string")
    else:
        raise TypeError("open_mxs_in_studio: file_path is not a string")
    
    s = platform.system()
    if(s == 'Darwin'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Studio.app', ))
    elif(s == 'Linux'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio', ))
    elif(s == 'Windows'):
        # app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio.exe', ))
        pass
    else:
        raise OSError("Unknown platform: {}.".format(s))
    
    _open_in_application(app, p)


def open_mxs_in_maxwell(file_path):
    if(type(file_path) is str):
        if(file_path != ""):
            if(_check_file_path(file_path)):
                if(_check_extension(file_path, ".mxs")):
                    p = os.path.realpath(file_path)
                else:
                    raise ValueError("open_mxs_in_studio: file_path must end with .mxs")
            else:
                raise ValueError("open_mxs_in_studio: file_path seems to be a directory")
        else:
            raise ValueError("open_mxs_in_studio: file_path in an empty string")
    else:
        raise TypeError("open_mxs_in_studio: file_path is not a string")
    
    s = platform.system()
    if(s == 'Darwin'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Maxwell.app', ))
    elif(s == 'Linux'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'maxwell', ))
    elif(s == 'Windows'):
        # app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'maxwell.exe', ))
        pass
    else:
        raise OSError("Unknown platform: {}.".format(s))
    
    _open_in_application(app, p)


def open_mxm_in_mxed(file_path):
    if(type(file_path) is str):
        if(file_path != ""):
            if(_check_file_path(file_path)):
                if(_check_extension(file_path, ".mxm")):
                    p = os.path.realpath(file_path)
                else:
                    raise ValueError("file_path must end with .mxm")
            else:
                raise ValueError("file_path seems to be a directory")
        else:
            raise ValueError("file_path in an empty string")
    else:
        raise TypeError("file_path is not a string")
    
    s = platform.system()
    if(s == 'Darwin'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Mxed.app', 'Contents', 'MacOS', 'Mxed', )))
        command_line = "{0} -mxm:'{1}'".format(app, p, )
        args = shlex.split(command_line, )
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(s == 'Linux'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'mxed', )))
        command_line = "nohup {0} -mxm:'{1}'".format(app, p, )
        args = shlex.split(command_line, )
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(s == 'Windows'):
        pass
    else:
        raise OSError("Unknown platform: {}.".format(s))


def create_mxm_in_mxed(file_path):
    if(type(file_path) is str):
        if(file_path != ""):
            if(_check_file_path(file_path)):
                if(_check_extension(file_path, ".mxm")):
                    p = os.path.realpath(file_path)
                else:
                    raise ValueError("file_path must end with .mxm")
            else:
                raise ValueError("file_path seems to be a directory")
        else:
            raise ValueError("file_path in an empty string")
    else:
        raise TypeError("file_path is not a string")
    
    s = platform.system()
    if(s == 'Darwin'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Mxed.app', 'Contents', 'MacOS', 'Mxed', )))
        command_line = "{0} -new:'{1}'".format(app, p, )
        args = shlex.split(command_line, )
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(s == 'Linux'):
        app = shlex.quote(os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'mxed', )))
        command_line = "nohup {0} -new:'{1}'".format(app, p, )
        args = shlex.split(command_line, )
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(s == 'Windows'):
        pass
    else:
        raise OSError("Unknown platform: {}.".format(s))
