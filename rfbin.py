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
import re
import struct
import shutil
import string
import time
import datetime

from .log import log, LogStyles


class RFBinWriter():
    """RealFlow particle .bin writer"""
    def __init__(self, directory, name, frame, particles, fps=24, size=0.001, log_indent=0, ):
        """
        directory   string (path)
        name        string ascii
        frame       int >= 0
        particles   list of (id int, x float, y float, z float, normal x float, normal y float, normal z float, velocity x float, velocity y float, velocity z float, radius float)
        fps         int > 0
        size        float > 0
        """
        cn = self.__class__.__name__
        self.log_indent = log_indent
        log("{}:".format(cn), 0 + self.log_indent, LogStyles.MESSAGE)
        
        if(not os.path.exists(directory)):
            raise OSError("{}: did you point me to an imaginary directory? ({})".format(cn, directory))
        if(not os.path.isdir(directory)):
            raise OSError("{}: not a directory. ({})".format(cn, directory))
        if(not os.access(directory, os.W_OK)):
            raise OSError("{}: no write access. ({})".format(cn, directory))
        self.directory = directory
        
        if(name == ""):
            raise ValueError("{}: name is an empty string".format(cn))
        ch = "-_.() {0}{1}".format(string.ascii_letters, string.digits)
        valid = "".join(c for c in name if c in ch)
        if(name != valid):
            log("invalid name.. changed to {0}".format(valid), 1 + self.log_indent, LogStyles.WARNING)
        self.name = valid
        
        if(int(frame) < 0):
            raise ValueError("{}: frame is less than zero".format(cn))
        self.frame = int(frame)
        
        self.extension = ".bin"
        self.path = os.path.join(self.directory, "{0}-{1}{2}".format(self.name, str(self.frame).zfill(5), self.extension))
        
        particle_length = 11 + 3
        if(all(len(v) == particle_length for v in particles) is False):
            raise ValueError("{}: bad particle data.".format(cn))
        self.particles = particles
        
        if(int(fps) < 0):
            raise ValueError("{}: fps is less than zero".format(cn))
        self.fps = int(fps)
        
        if(size <= 0):
            raise ValueError("{}: size is less than/or zero".format(cn))
        self.size = size
        
        self.version = 11
        
        self._write()
    
    def _write(self):
        self._t = time.time()
        p = self.path
        log("writing particles to: {0}".format(p), 1 + self.log_indent, )
        with open("{0}.tmp".format(p), 'wb') as f:
            log("writing header..", 1 + self.log_indent, )
            self._header(f)
            log("writing particles..", 1 + self.log_indent, )
            self._particles(f)
            log("writing appendix..", 1 + self.log_indent, )
            self._appendix(f)
        if(os.path.exists(p)):
            os.remove(p)
        shutil.move("{0}.tmp".format(p), p)
        log("done.", 1 + self.log_indent, )
        _d = datetime.timedelta(seconds=time.time() - self._t)
        log("completed in {0}".format(_d), 1 + self.log_indent, )
    
    def _header(self, f, ):
        p = struct.pack
        fw = f.write
        # magic
        fw(p("=i", 0xFABADA))
        # name, should match with name
        fw(p("=250s", self.name.encode('utf-8')))
        # version, scale, fluid type, simulation time
        fw(p("=hfif", self.version, 1.0, 9, 1.0))
        # frame number
        fw(p("=i", self.frame))
        # fps
        fw(p("=i", self.fps))
        # number of particles
        fw(p("=i", len(self.particles)))
        # particle size
        fw(p("=f", self.size))
        # pressure (max,min,average), speed (max,min,average), temperature (max,min,average)
        fw(p("=9f", 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0))
        # emitter_position (x,y,z), emitter_rotation (x,y,z), emitter_scale (x,y,z)
        fw(p("=9f", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0))
    
    def _particles(self, f, ):
        p = struct.pack
        fw = f.write
        for v in self.particles:
            # 3 position
            fw(p("=3f", *v[1:4]))
            # 3 velocity
            fw(p("=3f", *v[7:10]))
            # 3 force, 3 vorticity
            fw(p("=ffffff", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            # 3 normal
            fw(p("=3f", *v[4:7]))
            # neighbors
            fw(p("=i", 0, ))
            # 3 texture
            fw(p("=fff", *v[11:14]))
            # infobits, age, isolationtime, viscosity, density, pressure, mass, temperature
            fw(p("=hfffffff", 7, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0))
            # id
            fw(p("=i", v[0]))
    
    def _appendix(self, f, ):
        p = struct.pack
        fw = f.write
        # number of additional data per particle
        fw(p("=i", 1))
        # id of the data
        fw(p("=i", 2))
        # type of the data
        fw(p("=i", 4))
        # size of the data
        fw(p("=i", 4))
        # owner of the particle id
        fw(p("=i", 0))
        
        for v in self.particles:
            # additional data?
            fw(p("=?", True))
            # additional data
            fw(p("=f", v[10]))
        
        # RF4 internal data
        fw(p("=?", False))
        # RF5 internal data
        fw(p("=?", False))
