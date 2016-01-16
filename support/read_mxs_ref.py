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
import json
import shutil
import argparse
import textwrap
import os


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


class PercentDone():
    def __init__(self, total, prefix="> ", indent=0):
        self.current = 0
        self.percent = -1
        self.last = -1
        self.total = total
        self.prefix = prefix
        self.indent = indent
        self.t = "    "
        self.r = "\r"
        self.n = "\n"
    
    def step(self, numdone=1):
        if(quiet):
            return
        self.current += numdone
        self.percent = int(self.current / (self.total / 100))
        if(self.percent > self.last):
            sys.stdout.write(self.r)
            sys.stdout.write("{0}{1}{2}%".format(self.t * self.indent, self.prefix, self.percent))
            self.last = self.percent
        if(self.percent >= 100 or self.total == self.current):
            sys.stdout.write(self.r)
            sys.stdout.write("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n))
            if(LOG_FILE_PATH is not None):
                with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
                    f.write("{}".format("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n)))


def get_objects_names(scene):
    it = CmaxwellObjectIterator()
    o = it.first(scene)
    l = []
    while not o.isNull():
        name, _ = o.getName()
        l.append(name)
        o = it.next()
    return l


def base_and_pivot(obj):
    b, p, _ = obj.getBaseAndPivot()
    o = b.origin
    x = b.xAxis
    y = b.yAxis
    z = b.zAxis
    rb = [[o.x(), o.y(), o.z()], [x.x(), x.y(), x.z()], [y.x(), y.y(), y.z()], [z.x(), z.y(), z.z()]]
    
    o = p.origin
    x = p.xAxis
    y = p.yAxis
    z = p.zAxis
    rp = [[o.x(), o.y(), o.z()], [x.x(), x.y(), x.z()], [y.x(), y.y(), y.z()], [z.x(), z.y(), z.z()]]
    
    l, _ = obj.getPosition()
    rl = (l.x(), l.y(), l.z())
    r, _ = obj.getRotation()
    rr = (r.x(), r.y(), r.z())
    s, _ = obj.getScale()
    rs = (s.x(), s.y(), s.z())
    
    return rb, rp, rl, rr, rs


def object(o):
    is_instance, _ = o.isInstance()
    is_mesh, _ = o.isMesh()
    if(is_instance == 0 and is_mesh == 0):
        # log("WARNING: only empties, meshes and instances are supported..", 2)
        return None
    
    def get_verts(o):
        vs = []
        nv, _ = o.getVerticesCount()
        for i in range(nv):
            v, _ = o.getVertex(i, 0)
            vs.append((v.x(), v.y(), v.z()))
        return vs
    
    b, p = global_transform(o)
    r = {'name': o.getName()[0],
         'base': b,
         'pivot': p,
         'vertices': [], }
    if(is_instance == 1):
        io = o.getInstanced()
        # TODO: this is called once for each instance, better to process all meshes and then instances just copy vertex data
        r['vertices'] = get_verts(io)
    else:
        r['vertices'] = get_verts(o)
    return r


def global_transform(o):
    cb, _ = o.getWorldTransform()
    o = cb.origin
    x = cb.xAxis
    y = cb.yAxis
    z = cb.zAxis
    rb = [[o.x(), o.y(), o.z()], [x.x(), x.y(), x.z()], [y.x(), y.y(), y.z()], [z.x(), z.y(), z.z()]]
    rp = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), )
    return rb, rp


def main(args):
    log("maxwell meshes to data:", 1)
    # scene
    mp = args.mxs_path
    log("reading mxs scene from: {0}".format(mp), 2)
    scene = Cmaxwell(mwcallback)
    ok = scene.readMXS(mp)
    if(not ok):
        if(not os.path.exists(mp)):
            raise RuntimeError("Error during reading scene {}, file not found..".format(mp))
        raise RuntimeError("Error during reading scene {}".format(mp))
    # if(scene.isProtectionEnabled()):
    #     raise RuntimeError("Protected MXS ({})".format(mp))
    # objects
    nms = get_objects_names(scene)
    data = []
    log("converting empties, objects and instances..", 2)
    progress = PercentDone(len(nms), prefix="> ", indent=2, )
    for n in nms:
        d = None
        o = scene.getObject(n)
        d = object(o)
        if(d is not None):
            data.append(d)
        progress.step()
    # save data
    log("serializing..", 2)
    p = args.scene_data_path
    with open("{0}.tmp".format(p), 'w', encoding='utf-8', ) as f:
        json.dump(data, f, skipkeys=False, ensure_ascii=False, indent=4, )
    if(os.path.exists(p)):
        os.remove(p)
    shutil.move("{0}.tmp".format(p), p)
    log("done.", 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''Read vertices locations for MXS reference viewport diplay'''),
                                     epilog='', formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('-q', '--quiet', action='store_true', help='no logging except errors')
    parser.add_argument('pymaxwell_path', type=str, help='path to directory containing pymaxwell')
    parser.add_argument('log_file', type=str, help='path to log file')
    parser.add_argument('mxs_path', type=str, help='path to source .mxs')
    parser.add_argument('scene_data_path', type=str, help='path to serialized data')
    args = parser.parse_args()
    
    PYMAXWELL_PATH = args.pymaxwell_path
    
    try:
        from pymaxwell import *
    except ImportError:
        if(not os.path.exists(PYMAXWELL_PATH)):
            raise OSError("pymaxwell for python 3.4 does not exist ({})".format(PYMAXWELL_PATH))
        sys.path.insert(0, PYMAXWELL_PATH)
        from pymaxwell import *
    
    quiet = args.quiet
    LOG_FILE_PATH = args.log_file
    
    try:
        # import cProfile, pstats, io
        # pr = cProfile.Profile()
        # pr.enable()
        
        main(args)
        
        # pr.disable()
        # s = io.StringIO()
        # sortby = 'cumulative'
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()
        # print(s.getvalue())
        
    except Exception as e:
        import traceback
        m = traceback.format_exc()
        log(m)
        sys.exit(1)
    sys.exit(0)
