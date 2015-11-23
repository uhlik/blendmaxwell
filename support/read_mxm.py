#!/Library/Frameworks/Python.framework/Versions/3.4/bin/python3
# -*- coding: utf-8 -*-

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

import sys
import traceback
import argparse
import textwrap
import os
import json
import shutil


quiet = False
LOG_FILE_PATH = None


def log(msg, indent=0):
    if(quiet):
        return
    m = "{0}> {1}".format("    " * indent, msg)
    print(m)
    if(LOG_FILE_PATH is not None):
        with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
            f.write("{}{}".format(m, "\n"))


def main(args):
    log("mxm to dict:", 1)
    p = args.mxm_path
    s = Cmaxwell(mwcallback)
    log("reading mxm from: {0}".format(p), 2)
    m = s.readMaterial(p)
    
    data = {}
    
    # TODO: finish material import
    
    log("serializing..", 2)
    p = args.data_path
    with open("{0}.tmp".format(p), 'w', encoding='utf-8', ) as f:
        json.dump(data, f, skipkeys=False, ensure_ascii=False, indent=4, )
    if(os.path.exists(p)):
        os.remove(p)
    shutil.move("{0}.tmp".format(p), p)
    log("done.", 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''mxm to dict'''), epilog='',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('pymaxwell_path', type=str, help='path to directory containing pymaxwell')
    parser.add_argument('log_file', type=str, help='path to log file')
    parser.add_argument('mxm_path', type=str, help='path to .mxm')
    parser.add_argument('data_path', type=str, help='path to serialized data')
    args = parser.parse_args()
    
    PYMAXWELL_PATH = args.pymaxwell_path
    
    try:
        from pymaxwell import *
    except ImportError:
        sys.path.insert(0, PYMAXWELL_PATH)
        # sys.path.append(PYMAXWELL_PATH)
        from pymaxwell import *
    
    LOG_FILE_PATH = args.log_file
    
    try:
        main(args)
    except Exception as e:
        m = traceback.format_exc()
        log(m)
        sys.exit(1)
    sys.exit(0)
