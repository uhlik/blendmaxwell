#!/Library/Frameworks/Python.framework/Versions/3.4/bin/python3
# -*- coding: utf-8 -*-

# The MIT License (MIT)
#
# Copyright (c) 2015 Jakub Uhlík
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import sys
import traceback
import argparse
import textwrap
import json
import os


LOG_FILE_PATH = None


def log(msg, indent=0):
    m = "{0}> {1}".format("    " * indent, msg)
    print(m)
    if(LOG_FILE_PATH is not None):
        with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
            f.write("{}{}".format(m, "\n"))


def main(args):
    mgr = CextensionManager.instance()
    mgr.loadAllExtensions()
    
    s = Cmaxwell(mwcallback)
    ok = s.readMXS(args.scene)
    
    def get_material_names(s):
        it = CmaxwellMaterialIterator()
        o = it.first(s)
        l = []
        while not o.isNull():
            name = o.getName()
            l.append(name)
            o = it.next()
        return l
    
    names = get_material_names(s)
    for n in names:
        if(n.lower() == 'preview'):
            break
    
    material = s.getMaterial(n)
    material.read(args.mxm)
    material.forceToWriteIntoScene()
    
    # if draft engine is selected, no mxi will be created.. now what..
    s.setRenderParameter('ENGINE', args.quality)
    
    h, t = os.path.split(args.result)
    n, e = os.path.splitext(t)
    exr = os.path.join(h, "{}.exr".format(n))
    
    s.setPath('RENDER', exr, 32)
    s.setRenderParameter('DO NOT SAVE MXI FILE', True)
    s.setRenderParameter('DO NOT SAVE IMAGE FILE', True)
    
    src_dir, _ = os.path.split(args.scene)
    ok = s.addSearchingPath(src_dir)
    
    ok = s.writeMXS(args.scene_render)
    
    p = []
    p.append('-mxs:{}'.format(args.scene_render))
    p.append('-mxi:{}'.format(args.result))
    p.append('-o:{}'.format(exr))
    p.append('-res:{0}x{0}'.format(args.size))
    p.append('-time:{}'.format(args.time))
    p.append('-sl:{}'.format(args.sl))
    p.append('-dep:{}'.format(src_dir))
    p.append('-nowait')
    p.append('-nogui')
    p.append('-hide')
    p.append('-verbose:{}'.format(args.verbosity))
    
    runMaxwell(p)
    
    if(os.path.exists(args.result) or os.path.exists(exr)):
        if(args.quality == 'RS0'):
            # draft engine: render exr, load to mxi and then save
            mxi = CmaxwellMxi()
            mxi.readImage(exr)
            mxi.write(args.result)
            os.remove(exr)
    
        mxi = CmaxwellMxi()
        mxi.read(args.result)
        
        a, _ = mxi.getRenderBuffer(32)
    else:
        a = numpy.zeros((1, 1, 3), dtype=numpy.float, )
    
    np = os.path.join(h, "preview.npy")
    numpy.save(np, a)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''Make Maxwell Material from serialized data'''), epilog='',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('pymaxwell_path', type=str, help='path to directory containing pymaxwell')
    parser.add_argument('numpy_path', type=str, help='path to directory containing numpy')
    parser.add_argument('log_file', type=str, help='path to log file')
    parser.add_argument('scene', type=str, help='path to source scene')
    parser.add_argument('scene_render', type=str, help='path to scene.mxs')
    parser.add_argument('mxm', type=str, help='path to material.mxs')
    parser.add_argument('size', type=int, help='preview size in pixels')
    parser.add_argument('sl', type=int, help='desired sl')
    parser.add_argument('time', type=int, help='desired time in seconds')
    parser.add_argument('scale', type=int, help='scale (currently unused)')
    parser.add_argument('quality', type=str, help='quality')
    parser.add_argument('verbosity', type=int, help='verbosity')
    parser.add_argument('result', type=str, help='path to render.mxi')
    args = parser.parse_args()
    
    PYMAXWELL_PATH = args.pymaxwell_path
    NUMPY_PATH = args.numpy_path
    
    try:
        from pymaxwell import *
    except ImportError:
        if(not os.path.exists(PYMAXWELL_PATH)):
            raise OSError("pymaxwell for python 3.4 does not exist ({})".format(PYMAXWELL_PATH))
        sys.path.insert(0, PYMAXWELL_PATH)
        from pymaxwell import *
    
    try:
        import numpy
    except ImportError:
        sys.path.insert(0, NUMPY_PATH)
        import numpy
    
    LOG_FILE_PATH = args.log_file
    
    try:
        main(args)
    except Exception as e:
        import traceback
        m = traceback.format_exc()
        log(m)
        sys.exit(1)
    sys.exit(0)
