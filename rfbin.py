
import os
import re
import struct
import shutil

from .log import log, LogStyles
from . import progress


class RFBinParticle():
    def __init__(self, pid, position, normal=(0.0, 0.0, 0.0), velocity=(0.0, 0.0, 0.0), ):
        """
        pid:        particle id, int
        normal:     (x: float, y: float, z: float)
        position:   (x: float, y: float, z: float)
        velocity:   (x: float, y: float, z: float)
        """
        # some default values..
        self.age = 0.0
        self.density = 1.0
        self.force = (0.0, 0.0, 0.0)
        self.infobits = 7
        self.isolationtime = 1.0
        self.mass = 1.0
        self.neighbors = 0
        self.pressure = 1.0
        self.temperature = 1.0
        self.texture = (0.0, 0.0, 1.0)
        self.viscosity = 1.0
        self.vorticity = (0.0, 0.0, 0.0)
        
        # some more interesting values..
        if(pid < 0):
            raise ValueError("{}: pid is less than zero".format(self.__class__.__name__))
        self.pid = pid
        
        if(all(type(n) is float for n in position) is False or len(position) != 3):
            raise ValueError("{}: position must be list of 3 floats".format(self.__class__.__name__))
        self.position = tuple(position)
        
        if(all(type(n) is float for n in normal) is False or len(normal) != 3):
            raise ValueError("{}: normal must be list of 3 floats".format(self.__class__.__name__))
        self.normal = tuple(normal)
        
        if(all(type(n) is float for n in velocity) is False or len(velocity) != 3):
            raise ValueError("{}: velocity must be list of 3 floats".format(self.__class__.__name__))
        self.velocity = tuple(velocity)
    
    def __repr__(self):
        s = "{}(pid={}, position={}, normal={}, velocity={}, )"
        return s.format(self.__class__.__name__, self.pid, self.position, self.normal, self.velocity, )
    
    def __str__(self):
        return repr(self)


class RFBinWriter():
    """RealFlow particle .bin writer"""
    def __init__(self, directory, name, frame, particles, fps=24, size=0.001, ):
        cn = self.__class__.__name__
        log("{}:".format(cn), 0, LogStyles.MESSAGE)
        
        if(os.path.exists(directory) is False or os.path.isdir(directory) is False):
            raise OSError("{}: did you point me to an imaginary directory? ({})".format(cn, directory))
        self.directory = directory
        
        if(name == ""):
            raise ValueError("{}: name is an empty string".format(cn))
        import string
        ch = "-_.() {0}{1}".format(string.ascii_letters, string.digits)
        valid = "".join(c for c in name if c in ch)
        if(name != valid):
            log("invalid name.. changed to {0}".format(valid), 1, LogStyles.WARNING)
        self.name = valid
        
        if(int(frame) < 0):
            raise ValueError("{}: frame is less than zero".format(cn))
        self.frame = int(frame)
        
        self.extension = ".bin"
        
        self.path = os.path.join(self.directory, "{0}-{1}{2}".format(self.name, str(self.frame).zfill(5), self.extension))
        
        if(all(type(v) is RFBinParticle for v in particles) is False):
            raise ValueError("{}: particles must contain only instances of RFBinParticle".format(cn))
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
        p = self.path
        log("writing particles to: {0}".format(p), 1)
        with open("{0}.tmp".format(p), 'wb') as f:
            log("writing header..", 1)
            self._header(f)
            log("writing particles:", 1)
            self._particles(f)
            log("writing appendix..", 1)
            self._appendix(f)
        if(os.path.exists(p)):
            os.remove(p)
        shutil.move("{0}.tmp".format(p), p)
        log("done.", 1)
    
    def _header(self, f, ):
        p = struct.pack
        f.write(p("=i", 0xFABADA))                       # magic
        f.write(p("=250s", self.name.encode('utf-8')))   # name, should match with name
        f.write(p("=h", self.version))                   # version
        f.write(p("=f", 1.0))                            # scale
        f.write(p("=i", 9))                              # fluid type
        f.write(p("=f", 1.0))                            # simulation time
        f.write(p("=i", self.frame))                     # frame number
        f.write(p("=i", self.fps))                       # fps
        f.write(p("=i", len(self.particles)))            # number of particles
        f.write(p("=f", self.size))                      # particle size
        f.write(p("=3f", 1.0, 1.0, 1.0))                 # pressure (max,min,average)
        f.write(p("=3f", 1.0, 1.0, 1.0))                 # speed (max,min,average)
        f.write(p("=3f", 1.0, 1.0, 1.0))                 # temperature (max,min,average)
        for i in range(3):
            f.write(p("=f", 0.0))                        # emitter_position (x,y,z)
        for i in range(3):
            f.write(p("=f", 0.0))                        # emitter_rotation (x,y,z)
        for i in range(3):
            f.write(p("=f", 1.0))                        # emitter_scale (x,y,z)
    
    def _particles(self, f, ):
        prgs = progress.get_progress(len(self.particles), 1)
        p = struct.pack
        for v in self.particles:
            for i in v.position:
                f.write(p("=f", i))
            for i in v.velocity:
                f.write(p("=f", i))
            for i in v.force:
                f.write(p("=f", i))
            for i in v.vorticity:
                f.write(p("=f", i))
            for i in v.normal:
                f.write(p("=f", i))
            f.write(p("=i", v.neighbors))
            for i in v.texture:
                f.write(p("=f", i))
            f.write(p("=h", v.infobits))
            f.write(p("=f", v.age))
            f.write(p("=f", v.isolationtime))
            f.write(p("=f", v.viscosity))
            f.write(p("=f", v.density))
            f.write(p("=f", v.pressure))
            f.write(p("=f", v.mass))
            f.write(p("=f", v.temperature))
            f.write(p("=i", v.pid))
            prgs.step()
    
    def _appendix(self, f, ):
        p = struct.pack
        # number of additional data per particle
        f.write(p("=i", 0))
        # RF4 internal data
        f.write(p("=?", False))
        # RF5 internal data
        f.write(p("=?", False))
    
    def __repr__(self):
        s = "{}(directory='{}', name='{}', frame={}, particles={}, fps={}, size={}, )"
        return s.format(self.__class__.__name__, self.directory, self.name, self.frame, self.particles, self.fps, self.size, )
    
    def __str__(self):
        s = "{}(directory='{}', name='{}', frame={}, particles={}, fps={}, size={}, )"
        return s.format(self.__class__.__name__, self.directory, self.name, self.frame, "[{0} items..]".format(len(self.particles)), self.fps, self.size, )
