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


def log(msg, indent=0):
    m = "{0}> {1}".format("    " * indent, msg)
    print(m)


def main(args):
    p = args.mxm_path
    s = Cmaxwell(mwcallback)
    m = s.readMaterial(p)
    # m = s.addMaterial(m)
    for i in range(m.getNumLayers()[0]):
        l = m.getLayer(i)
        e = l.getEmitter()
        if(e.isNull()):
            # no emitter layer
            return False
        if(not e.getState()[0]):
            # there is, but is disabled
            return False
        # is emitter
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''Read MXM file and check is there is an emitter layer'''), epilog='',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('pymaxwell_path', type=str, help='path to directory containing pymaxwell')
    parser.add_argument('mxm_path', type=str, help='path to .mxm')
    args = parser.parse_args()
    
    PYMAXWELL_PATH = args.pymaxwell_path
    
    try:
        from pymaxwell import *
    except ImportError:
        if(not os.path.exists(PYMAXWELL_PATH)):
            raise OSError("pymaxwell for python 3.4 does not exist ({})".format(PYMAXWELL_PATH))
        sys.path.insert(0, PYMAXWELL_PATH)
        from pymaxwell import *
    
    found = False
    try:
        found = main(args)
    except Exception as e:
        m = traceback.format_exc()
        log(m)
        sys.exit(1)
    if(found):
        # lets communicate with exit code
        sys.exit(100)
    sys.exit(0)
