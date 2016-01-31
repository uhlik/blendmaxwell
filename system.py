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
import uuid
import json
import shutil

import bpy

from .log import log, LogStyles, LOG_FILE_PATH
from . import mxs
from . import tmpio


PLATFORM = platform.system()
REQUIRED = (3, 2, 0, 0, )


def prefs():
    a = os.path.split(os.path.split(os.path.realpath(__file__))[0])[1]
    p = bpy.context.user_preferences.addons[a].preferences
    return p


def check_for_template():
    TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "write_mxs.py")
    if(not os.path.exists(TEMPLATE)):
        log("support directory is missing..", 1, LogStyles.ERROR, )
        raise OSError("support directory is missing..")
    return TEMPLATE


def check_for_export_mxm_template():
    TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "write_mxm.py")
    if(not os.path.exists(TEMPLATE)):
        log("support directory is missing..", 1, LogStyles.ERROR, )
        raise OSError("support directory is missing..")
    return TEMPLATE


def check_for_import_template():
    TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "read_mxs.py")
    if(not os.path.exists(TEMPLATE)):
        log("support directory is missing..", 1, LogStyles.ERROR, )
        raise OSError("support directory is missing..")
    return TEMPLATE


def check_for_import_mxm_template():
    TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "read_mxm.py")
    if(not os.path.exists(TEMPLATE)):
        log("support directory is missing..", 1, LogStyles.ERROR, )
        raise OSError("support directory is missing..")
    return TEMPLATE


def open_file_in_default_application(path):
    if(PLATFORM == 'Darwin'):
        os.system("open {}".format(shlex.quote(path)))
    elif(PLATFORM == 'Linux'):
        subprocess.call(["xdg-open", shlex.quote(path)])
    elif(PLATFORM == 'Windows'):
        os.system("start {}".format(shlex.quote(path)))


def mxed_create_material_helper(path, force_preview=False, force_preview_scene="", ):
    mp = bpy.path.abspath(prefs().maxwell_path)
    if(PLATFORM == 'Darwin'):
        app = os.path.abspath(os.path.join(mp, 'Mxed.app', 'Contents', 'MacOS', 'Mxed', ))
    elif(PLATFORM == 'Linux'):
        app = os.path.abspath(os.path.join(mp, 'mxed', ))
    elif(PLATFORM == 'Windows'):
        app = os.path.abspath(os.path.join(mp, 'mxed.exe', ))
    f = ""
    if(force_preview):
        f = " -force"
    fs = ""
    if(force_preview_scene != '' and force_preview):
        fs = " -mxsprv:{}".format(shlex.quote(force_preview_scene))
    command_line = '{}{}{} -new:{}'.format(shlex.quote(app), f, fs, shlex.quote(path))
    if(PLATFORM == 'Linux'):
        command_line = 'nohup {}'.format(command_line)
    
    log("command: {0}".format(command_line), 0, LogStyles.MESSAGE, )
    
    args = shlex.split(command_line, )
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )


def mxed_edit_material_helper(path, force_preview=False, force_preview_scene="", ):
    mp = bpy.path.abspath(prefs().maxwell_path)
    if(PLATFORM == 'Darwin'):
        app = os.path.abspath(os.path.join(mp, 'Mxed.app', 'Contents', 'MacOS', 'Mxed', ))
    elif(PLATFORM == 'Linux'):
        app = os.path.abspath(os.path.join(mp, 'mxed', ))
    elif(PLATFORM == 'Windows'):
        app = os.path.abspath(os.path.join(mp, 'mxed.exe', ))
    f = ""
    if(force_preview):
        f = " -force"
    fs = ""
    if(force_preview_scene != '' and force_preview):
        fs = " -mxsprv:{}".format(shlex.quote(force_preview_scene))
    command_line = '{}{}{} -mxm:{}'.format(shlex.quote(app), f, fs, shlex.quote(path))
    if(PLATFORM == 'Linux'):
        command_line = 'nohup {}'.format(command_line)
    
    log("command: {0}".format(command_line), 0, LogStyles.MESSAGE, )
    
    args = shlex.split(command_line, )
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )


def mxed_create_and_edit_ext_material_helper(path, material_data, force_preview=False, force_preview_scene="", ):
    log("Extension Material to MXM: {} > {}".format(material_data['name'], path), 1)
    log(material_data, 2)
    
    if(PLATFORM == 'Darwin'):
        TEMPLATE = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "write_mxm.py")
        
        uid = uuid.uuid1()
        h, t = os.path.split(path)
        n, e = os.path.splitext(t)
        tmp_dir = os.path.join(h, "{0}-tmp-{1}".format(n, uid))
        
        if(prefs().osx_tmp_use == 'SPECIFIC_DIRECTORY'):
            tmpd = os.path.realpath(bpy.path.abspath(prefs().osx_tmp_use_directory))
            if(os.path.exists(tmpd)):
                if(os.path.isdir(tmpd)):
                    if(os.access(tmpd, os.W_OK)):
                        tmp_dir = os.path.join(tmpd, "{0}-tmp-{1}".format(n, uid))
                    else:
                        log("tmp directory ('{}') is not writeable, using default".format(tmpd), 2, LogStyles.WARNING)
                else:
                    log("tmp directory ('{}') is not a directory, using default".format(tmpd), 2, LogStyles.WARNING)
            else:
                log("tmp directory ('{}') does not exist, using default".format(tmpd), 2, LogStyles.WARNING)
        else:
            pass
        
        log("creating temp directory.. ({})".format(tmp_dir), 2, LogStyles.MESSAGE, )
        if(os.path.exists(tmp_dir) is False):
            os.makedirs(tmp_dir)
        
        mxm_data_name = "{0}-{1}.json".format(n, uid)
        script_name = "{0}-{1}.py".format(n, uid)
        
        def serialize(t, d, n):
            if(not n.endswith(".json")):
                n = "{}.json".format(n)
            p = os.path.join(t, n)
            with open("{0}.tmp".format(p), 'w', encoding='utf-8', ) as f:
                json.dump(d, f, skipkeys=False, ensure_ascii=False, indent=4, )
            if(os.path.exists(p)):
                os.remove(p)
            shutil.move("{0}.tmp".format(p), p)
            return p
        
        mxm_data_path = serialize(tmp_dir, material_data, mxm_data_name)
        
        script_path = os.path.join(tmp_dir, script_name)
        with open(script_path, mode='w', encoding='utf-8') as f:
            # read template
            with open(TEMPLATE, encoding='utf-8') as t:
                code = "".join(t.readlines())
            # write template to a new file
            f.write(code)
        
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        command_line = "{0} {1} {2} {3} {4} {5}".format(shlex.quote(PY),
                                                        shlex.quote(script_path),
                                                        shlex.quote(PYMAXWELL_PATH),
                                                        shlex.quote(LOG_FILE_PATH),
                                                        shlex.quote(mxm_data_path),
                                                        shlex.quote(path), )
        log("command:", 2)
        log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
            raise Exception("error in {0}".format(script_path))
        
        def rm(p):
            if(os.path.exists(p)):
                os.remove(p)
            else:
                log("cleanup: {0} does not exist?".format(p), 1, LogStyles.WARNING, )
        
        rm(script_path)
        rm(mxm_data_path)
        
        if(os.path.exists(tmp_dir)):
            os.rmdir(tmp_dir)
        else:
            log("cleanup: {0} does not exist?".format(tmp_dir), 1, LogStyles.WARNING, )
        
        mxed_edit_material_helper(path, force_preview, force_preview_scene, )
        return path
    elif(PLATFORM == 'Linux'):
        w = mxs.MXMWriter(path, material_data)
        mxed_edit_material_helper(path, force_preview, force_preview_scene, )
        return path
    elif(PLATFORM == 'Windows'):
        w = mxs.MXMWriter(path, material_data)
        mxed_edit_material_helper(path, force_preview, force_preview_scene, )
        return path


def mxed_create_and_edit_custom_material_helper(path, material_data, force_preview=False, force_preview_scene="", open_in_mxed=True, ):
    log("Custom Material to MXM: {} > {}".format(material_data['name'], path), 1)
    # log(material_data, 2)
    
    if(PLATFORM == 'Darwin'):
        TEMPLATE = check_for_export_mxm_template()
        
        uid = uuid.uuid1()
        h, t = os.path.split(path)
        n, e = os.path.splitext(t)
        tmp_dir = os.path.join(h, "{0}-tmp-{1}".format(n, uid))
        
        if(prefs().osx_tmp_use == 'SPECIFIC_DIRECTORY'):
            tmpd = os.path.realpath(bpy.path.abspath(prefs().osx_tmp_use_directory))
            if(os.path.exists(tmpd)):
                if(os.path.isdir(tmpd)):
                    if(os.access(tmpd, os.W_OK)):
                        tmp_dir = os.path.join(tmpd, "{0}-tmp-{1}".format(n, uid))
                    else:
                        log("tmp directory ('{}') is not writeable, using default".format(tmpd), 2, LogStyles.WARNING)
                else:
                    log("tmp directory ('{}') is not a directory, using default".format(tmpd), 2, LogStyles.WARNING)
            else:
                log("tmp directory ('{}') does not exist, using default".format(tmpd), 2, LogStyles.WARNING)
        else:
            pass
        
        log("creating temp directory.. ({})".format(tmp_dir), 2, LogStyles.MESSAGE, )
        
        if(os.path.exists(tmp_dir) is False):
            os.makedirs(tmp_dir)
        
        mxm_data_name = "{0}-{1}.json".format(n, uid)
        script_name = "{0}-{1}.py".format(n, uid)
        
        def serialize(t, d, n):
            if(not n.endswith(".json")):
                n = "{}.json".format(n)
            p = os.path.join(t, n)
            with open("{0}.tmp".format(p), 'w', encoding='utf-8', ) as f:
                json.dump(d, f, skipkeys=False, ensure_ascii=False, indent=4, )
            if(os.path.exists(p)):
                os.remove(p)
            shutil.move("{0}.tmp".format(p), p)
            return p
        
        mxm_data_path = serialize(tmp_dir, material_data, mxm_data_name)
        
        script_path = os.path.join(tmp_dir, script_name)
        with open(script_path, mode='w', encoding='utf-8') as f:
            # read template
            with open(TEMPLATE, encoding='utf-8') as t:
                code = "".join(t.readlines())
            # write template to a new file
            f.write(code)
        
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        command_line = "{0} {1} {2} {3} {4} {5}".format(shlex.quote(PY),
                                                        shlex.quote(script_path),
                                                        shlex.quote(PYMAXWELL_PATH),
                                                        shlex.quote(LOG_FILE_PATH),
                                                        shlex.quote(mxm_data_path),
                                                        shlex.quote(path), )
        log("command:", 2)
        log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
            raise Exception("error in {0}".format(script_path))
        
        def rm(p):
            if(os.path.exists(p)):
                os.remove(p)
            else:
                log("cleanup: {0} does not exist?".format(p), 1, LogStyles.WARNING, )
        
        rm(script_path)
        rm(mxm_data_path)
        
        if(os.path.exists(tmp_dir)):
            os.rmdir(tmp_dir)
        else:
            log("cleanup: {0} does not exist?".format(tmp_dir), 1, LogStyles.WARNING, )
        
        if(open_in_mxed):
            mxed_edit_material_helper(path, force_preview, force_preview_scene, )
        return path
    elif(PLATFORM == 'Linux'):
        w = mxs.MXMWriter(path, material_data)
        mxed_edit_material_helper(path, force_preview, force_preview_scene, )
        return path
    elif(PLATFORM == 'Windows'):
        w = mxs.MXMWriter(path, material_data)
        mxed_edit_material_helper(path, force_preview, force_preview_scene, )
        return path


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
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'studio.exe', ))
        command_line = '{0} -mxs:{1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )


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
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'maxwell', ))
        command_line = 'nohup {0} {1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
    elif(PLATFORM == 'Windows'):
        app = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'maxwell.exe', ))
        command_line = '{0} -mxs:{1}'.format(shlex.quote(app), shlex.quote(path))
        args = shlex.split(command_line)
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )


def python34_run_script_helper(script_path, scene_data_path, mxs_path, append, wireframe, ):
    if(PLATFORM == 'Darwin' or PLATFORM == 'Linux'):
        switches = ''
        if(append):
            switches += '-a'
        # if(instancer):
        #     if(switches != ''):
        #         switches += ' '
        #     switches += '-i'
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
            PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        if(PLATFORM == 'Linux'):
            PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'python3.4', ))
        if(PY == ""):
            raise Exception("huh?")
        
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        
        if(switches != ''):
            command_line = "{0} {1} {2} {3} {4} {5} {6}".format(shlex.quote(PY),
                                                                shlex.quote(script_path),
                                                                switches,
                                                                shlex.quote(PYMAXWELL_PATH),
                                                                shlex.quote(LOG_FILE_PATH),
                                                                shlex.quote(scene_data_path),
                                                                shlex.quote(mxs_path), )
        else:
            command_line = "{0} {1} {2} {3} {4} {5}".format(shlex.quote(PY),
                                                            shlex.quote(script_path),
                                                            shlex.quote(PYMAXWELL_PATH),
                                                            shlex.quote(LOG_FILE_PATH),
                                                            shlex.quote(scene_data_path),
                                                            shlex.quote(mxs_path), )
        
        log("command:", 2)
        log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
            raise Exception("error in {0}".format(script_path))
    elif(s == 'Windows'):
        pass
    else:
        raise OSError("Unknown platform: {}.".format(PLATFORM))


def python34_run_script_helper_import(script_path, mxs_path, scene_data_path, import_emitters, import_objects, import_cameras, import_sun, ):
    if(PLATFORM == 'Darwin'):
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        if(PY == ""):
            raise Exception("huh?")
        
        switches = ''
        if(import_emitters):
            switches += '-e'
        if(import_objects):
            if(switches != ''):
                switches += ' '
            switches += '-o'
        if(import_cameras):
            if(switches != ''):
                switches += ' '
            switches += '-c'
        if(import_sun):
            if(switches != ''):
                switches += ' '
            switches += '-s'
        
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        
        # execute the script
        command_line = "{0} {1} {2} {3} {4} {5} {6}".format(shlex.quote(PY),
                                                            shlex.quote(script_path),
                                                            switches,
                                                            shlex.quote(PYMAXWELL_PATH),
                                                            shlex.quote(LOG_FILE_PATH),
                                                            shlex.quote(mxs_path),
                                                            shlex.quote(scene_data_path), )
        log("command:", 2)
        log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
        args = shlex.split(command_line, )
        
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
    else:
        raise Exception("This is meant to be called on Mac OS X")


def python34_run_mxm_preview(mxm_path):
    if(PLATFORM == 'Darwin'):
        script_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "read_mxm_preview.py", )
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        import numpy
        NUMPY_PATH = os.path.split(os.path.split(numpy.__file__)[0])[0]
        command_line = "{} {} {} {} {}".format(shlex.quote(PY),
                                               shlex.quote(script_path),
                                               shlex.quote(PYMAXWELL_PATH),
                                               shlex.quote(NUMPY_PATH),
                                               shlex.quote(mxm_path), )
        
        # log("read material preview from mxm:", 1)
        # log("command:", 2)
        # log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
        log("read material preview from: {}".format(mxm_path), 1)
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
            raise Exception("error in {0}".format(script_path))
        
    else:
        raise OSError("Unknown platform: {}.".format(PLATFORM))


def python34_run_mxm_is_emitter(mxm_path):
    if(PLATFORM == 'Darwin'):
        script_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "read_mxm_emitter.py", )
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        command_line = "{0} {1} {2} {3}".format(shlex.quote(PY),
                                                shlex.quote(script_path),
                                                shlex.quote(PYMAXWELL_PATH),
                                                shlex.quote(mxm_path), )
        log("check material for emitters: {}".format(mxm_path), 1)
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o == 100):
            return True
        elif(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
            raise Exception("error in {0}".format(script_path))
        return False
    else:
        raise OSError("Unknown platform: {}.".format(PLATFORM))


def python34_run_read_mxs_reference(mxs_path):
    if(PLATFORM == 'Darwin'):
        script_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "read_mxs_ref.py", )
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        n = os.path.split(mxs_path)[1]
        scene_data_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "{}.binrefv".format(n), )
        
        command_line = "{} {} {} {} {} {}".format(shlex.quote(PY),
                                                  shlex.quote(script_path),
                                                  shlex.quote(PYMAXWELL_PATH),
                                                  shlex.quote(LOG_FILE_PATH),
                                                  shlex.quote(mxs_path),
                                                  shlex.quote(scene_data_path), )
        
        log("read vertices from: {}".format(mxs_path), 1)
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
            raise Exception("error in {0}".format(script_path))
        
        r = tmpio.MXSBinRefVertsReader(scene_data_path)
        data = r.data
        
        if(os.path.exists(scene_data_path)):
            os.remove(scene_data_path)
        
        return data
    else:
        raise OSError("Unknown platform: {}.".format(PLATFORM))


def python34_run_script_helper_import_mxm(script_path, mxm_path, data_path, ):
    if(PLATFORM == 'Darwin'):
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        if(PY == ""):
            raise Exception("huh?")
        
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        
        # execute the script
        command_line = "{0} {1} {2} {3} {4} {5}".format(shlex.quote(PY),
                                                        shlex.quote(script_path),
                                                        shlex.quote(PYMAXWELL_PATH),
                                                        shlex.quote(LOG_FILE_PATH),
                                                        shlex.quote(mxm_path),
                                                        shlex.quote(data_path), )
        log("command:", 2)
        log("{0}".format(command_line), 0, LogStyles.MESSAGE, prefix="")
        args = shlex.split(command_line, )
        
        o = subprocess.call(args, )
        if(o != 0):
            log("error in {0}".format(script_path), 0, LogStyles.ERROR, )
    else:
        raise Exception("This is meant to be called on Mac OS X")


def check_pymaxwell_version():
    if(PLATFORM == 'Darwin'):
        script_path = os.path.join(os.path.split(os.path.realpath(__file__))[0], "support", "version.py", )
        PY = os.path.abspath(os.path.join(bpy.path.abspath(prefs().python_path), 'bin', 'python3.4', ))
        req = ".".join(str(i) for i in REQUIRED)
        PYMAXWELL_PATH = os.path.abspath(os.path.join(bpy.path.abspath(prefs().maxwell_path), 'Libs', 'pymaxwell', 'python3.4', ))
        command_line = "{0} {1} {2} {3}".format(shlex.quote(PY),
                                                shlex.quote(script_path),
                                                shlex.quote(PYMAXWELL_PATH),
                                                shlex.quote(req), )
        args = shlex.split(command_line, )
        o = subprocess.call(args, )
        if(o == 1):
            raise Exception("Unexpected error in version check, please contact developer..")
        elif(o == 2):
            raise Exception("Cannot import pymaxwell, not found at path: '{}'".format(PYMAXWELL_PATH))
        elif(o == 3):
            raise Exception("Found old pymaxwell, required version is: {}".format(REQUIRED))
        else:
            return True
        
    elif(PLATFORM == 'Linux' or PLATFORM == 'Windows'):
        try:
            import pymaxwell
        except ImportError:
            mp = os.environ.get("MAXWELL3_ROOT")
            pp = os.path.abspath(os.path.join(mp, 'python', 'pymaxwell', 'python3.4'))
            if(not os.path.exists(pp)):
                raise OSError("pymaxwell for python 3.4 does not exist ({})".format(pp))
            sys.path.insert(0, pp)
            # sys.path.append(pp)
            if(PLATFORM == 'Windows'):
                os.environ['PATH'] = ';'.join([mp, os.environ['PATH']])
            import pymaxwell
            v = pymaxwell.getPyMaxwellVersion()
            v = tuple([int(i) for i in v.split('.')])
            if(v < REQUIRED):
                raise Exception("Found old pymaxwell {}, required version is: {}".format(v, REQUIRED))
    else:
        raise OSError("Unknown platform: {}.".format(PLATFORM))
    
    return True


def mxed_get_preview_scenes():
    if(PLATFORM == 'Darwin'):
        mp = bpy.path.abspath(prefs().maxwell_path)
    elif(PLATFORM == 'Linux' or PLATFORM == 'Windows'):
        mp = os.environ.get("MAXWELL3_ROOT")
    d = os.path.abspath(os.path.join(mp, 'preview', ))
    l = os.listdir(d)
    r = []
    for f in l:
        n, e = os.path.splitext(f)
        if(e == '.mxs'):
            # r.append((os.path.join(d, f), n.replace ("_", " ").capitalize(), ''))
            r.append((os.path.join(d, f), n, ''))
    r.sort()
    r.insert(0, (' ', '(default)', ''))
    return r


def mxed_browse_material_helper():
    mp = bpy.path.abspath(prefs().maxwell_path)
    if(PLATFORM == 'Darwin'):
        app = os.path.abspath(os.path.join(mp, 'Mxed.app', 'Contents', 'MacOS', 'Mxed', ))
    elif(PLATFORM == 'Linux'):
        app = os.path.abspath(os.path.join(mp, 'mxed', ))
    elif(PLATFORM == 'Windows'):
        app = os.path.abspath(os.path.join(mp, 'mxed.exe', ))
    
    command_line = '{} -brwclose'.format(shlex.quote(app))
    log("command: {0}".format(command_line), 0, LogStyles.MESSAGE, )
    
    args = shlex.split(command_line, )
    p = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, )
    o, e = p.communicate()
    
    # mp = o.decode("utf-8")[4:-1]
    mp = o.decode("utf-8").strip()[4:]
    if(mp == ''):
        return None
    return mp


def verify_installation():
    if(PLATFORM == 'Darwin'):
        # maxwell installation is on default path or path specified in preferences
        ump = prefs().maxwell_path
        dmp = '/Applications/Maxwell 3/'
        mp = ''
        if(ump == ''):
            mp = dmp
        else:
            mp = ump
        if(not os.path.exists(mp)):
            raise OSError("Maxwell instalation not found at '{}'".format(mp))
        # python 3.4 is installed
        upp = prefs().python_path
        dpp = '/Library/Frameworks/Python.framework/Versions/3.4/'
        pp = ''
        if(upp == ''):
            pp = dpp
        else:
            pp = upp
        if(not os.path.exists(pp)):
            raise OSError("Python 3.4 instalation not found at '{}'".format(mp))
        # pymaxwell imported from maxwell instalation is required version or above
        pym = check_pymaxwell_version()
        # check if there is pymaxwell in site-packages and complain
        psp = os.path.join(pp, 'lib', 'python3.4', 'site-packages')
        if(os.path.exists(os.path.join(psp), 'pymaxwell.py') or os.path.exists(os.path.join(psp), '_pymaxwell.so')):
            log("found different pymaxwell at '{}', please remove it if possible, may cause conflicts..".format(psp), 1, LogStyles.WARNING, )
    elif(PLATFORM == 'Linux'):
        # maxwell installation is on default path or path specified in preferences
        ump = prefs().maxwell_path
        dmp = os.environ.get("MAXWELL3_ROOT")
        mp = ''
        if(ump == ''):
            mp = dmp
        else:
            mp = ump
        if(not os.path.exists(mp)):
            raise OSError("Maxwell instalation not found at '{}'".format(mp))
        # pymaxwell imported from maxwell instalation is required version or above
        pym = check_pymaxwell_version()
        # there is LD_LIBRARY_PATH and its value
        ldlp = os.environ.get("LD_LIBRARY_PATH")
        if(dmp not in ldlp):
            raise OSError("LD_LIBRARY_PATH does not contain path to Maxwell")
    elif(PLATFORM == 'Windows'):
        # maxwell installation is on default path or path specified in preferences
        ump = prefs().maxwell_path
        dmp = os.environ.get("MAXWELL3_ROOT")
        mp = ''
        if(ump == ''):
            mp = dmp
        else:
            mp = ump
        if(not os.path.exists(mp)):
            raise OSError("Maxwell instalation not found at '{}'".format(mp))
        # pymaxwell imported from maxwell instalation is required version or above
        pym = check_pymaxwell_version()
    else:
        raise OSError("Unknown platform: {}".format(PLATFORM))
