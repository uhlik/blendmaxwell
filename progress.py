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
import time

from .log import log, LogStyles

__all__ = ("IndeterminateProgress", "ProgressBase", "ProgressPercent", "ProgressFloat", "ProgressBar",
           "PROGRESS_PERCENT", "PROGRESS_FLOAT", "PROGRESS_BAR",
           "set_default_progress_reporting", "get_default_progress_reporting", "get_progress", )


ENABLED = True


class IndeterminateProgress():
    def __init__(self, prefix="> ", indent=0, seconds_per_step=0.1, ):
        self.prefix = prefix
        self.indent = indent
        self.seconds_per_step = seconds_per_step
        #
        self.ch = ("-", "\\", "|", "/")
        self.n = 0
        self.l = len(self.ch)
        self.pt = 0
        self.ct = time.perf_counter()
    
    def step(self):
        self.ct = time.perf_counter()
        if(self.pt + self.seconds_per_step > self.ct):
            # skip when print time + seconds_per_step is still more than current time
            return
        # update print time
        self.pt = self.ct
        #
        sys.stdout.write("\r")
        sys.stdout.write("{0}{1}{2}".format("    " * self.indent, self.prefix, self.ch[self.n]))
        sys.stdout.write("\b")
        sys.stdout.flush()
        self.n = (self.n + 1) % self.l
    
    def finish(self):
        # sys.stdout.write("\r")
        # sys.stdout.write("{0}{1}\n".format("    " * self.indent, self.prefix))
        # sys.stdout.flush()
        
        # log using normal logging utility, otherwise will be omitted in log file
        # \n not needed, will be added..
        m = "{0}{1}".format("    " * self.indent, self.prefix)
        log(m, indent=0, style=LogStyles.NORMAL, instance=None, prefix="", )


class ProgressBase():
    PERCENTAGE = 'Percentage'
    CLOSED_UNIT_INTERVAL = 'Closed Unit Interval'
    
    def __init__(self, start=0.0, end=100.0, type=PERCENTAGE, decimals=0, prefix="> ", indent=0, precision=10, ):
        self._start = start
        self._end = end
        self._total = self._end - self._start
        self._type = type
        self._prefix = prefix
        self._indent = int(indent)
        self._precision = int(precision)
        self._decimals = int(decimals)
        self._tab = "    "
        self._current = 0.0
        self._progress = 0.0
        self._tcount = 0
        self._tlast = 0.0
        # print time step: 1 second = 1000 ms, 25 fps, 1000 / 25 = 40 ms per frame, add 25% safe zone == 30 mspf
        self._tstep = 30
        
        self._enabled = True
        
        # print progress 0
        # not a good idea, better to report upon first step call
        # self._report(True, 0.0)
        # and ensure there will be only one print (for example when step(0.0) will be called many times..)
        self._once = False
    
    def _milliseconds(self):
        return int(round(time.time() * 1000))
    
    def _normalize(self, v, vmin, vmax):
        return (v - vmin) / (vmax - vmin)
    
    def _interpolate(self, nv, vmin, vmax):
        return vmin + (vmax - vmin) * nv
    
    def _map(self, v, min1, max1, min2, max2):
        return self._interpolate(self._normalize(v, min1, max1), min2, max2)
    
    def step(self, done=1.0):
        """next step in progress
        done: number to add to current progress"""
        if(not self._enabled):
            return
        if(ENABLED is False):
            self._enabled = False
            f = "{0}{1}{2}{3}{4}"
            m = "[pretend to see a progress bar here..]"
            sys.stdout.write("{0}\n".format(f).format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, m, LogStyles.END))
            return
        
        if(self._progress == 0.0 and self._once is False):
            # first call
            self._once = True
            self._report(True, 0.0)
        
        if(self._current >= self._total or self._progress >= 1.0):
            # we are done with it.. skip
            return
        
        self._current += done
        self._progress = round(self._map(self._current, 0, self._total, 0, 1), self._precision)
        
        self._report()
        if(self._current >= self._total or self._progress >= 1.0):
            self._progress = 1.0
            self._report(True, 1.0)
    
    def _report(self, force=False, value=None):
        """decide if report (print) progress or not
        force True: always print
        value None: print self.progress
        value number: print number"""
        # limit value to [0, 1] range
        if(value is not None):
            value = max(min(value, 1.0), 0.0)
        
        ms = self._milliseconds()
        if(force is True):
            if(value is not None):
                if(value >= 1.0):
                    self._print(value, True)
                else:
                    self._print(value)
                self._tlast = ms
            else:
                self._print(self._progress)
                self._tlast = ms
        else:
            if(ms >= self._tlast + self._tstep):
                self._print(self._progress)
                self._tlast = ms
    
    def _print(self, value, finish=False):
        """print value in correct format and style"""
        self._tcount += 1
        sys.stdout.write("\r")
        
        progress = self._progress
        if(self._type == self.PERCENTAGE):
            progress = progress * 100
        
        if(self._type == self.PERCENTAGE):
            # add percent sign
            f = "{0}{1}{2}{3:.{4}f}%{5}"
        else:
            f = "{0}{1}{2}{3:.{4}f}{5}"
        if(finish):
            # last print should contain end of line or next print will be appended to it
            # sys.stdout.write("{0}\n".format(f).format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, progress, self._decimals, LogStyles.END))
            
            # log using normal logging utility, otherwise will be omitted in log file
            # \n not needed, will be added..
            m = "{0}".format(f).format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, progress, self._decimals, LogStyles.END)
            log(m, indent=0, style=LogStyles.NORMAL, instance=None, prefix="", )
        else:
            sys.stdout.write(f.format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, progress, self._decimals, LogStyles.END))
    
    def __str__(self):
        if(self._type == self.PERCENTAGE):
            s = ("ProgressBase({0:.{1}f}%)")
        else:
            s = ("ProgressBase({0:.{1}f})")
        p = self._progress
        if(self._type == self.PERCENTAGE):
            p = p * 100
        return s.format(p, self._decimals)
    
    def __repr__(self):
        s = "ProgressBase(start={0}, end={1}, type='{2}', decimals={3}, prefix='{4}', indent={5}, precision={6}, )"
        return s.format(self._start, self._end, self._type, self._decimals, self._prefix, self._indent, self._precision)


class ProgressPercent(ProgressBase):
    def __init__(self, start=0.0, end=100.0, decimals=0, prefix="> ", indent=0, precision=10, ):
        super(ProgressPercent, self).__init__(start=start, end=end, decimals=decimals, prefix=prefix, indent=indent, precision=precision, )
    
    def __str__(self):
        if(self._type == self.PERCENTAGE):
            s = ("ProgressPercent({0:.{1}f}%)")
        else:
            s = ("ProgressPercent({0:.{1}f})")
        p = self._progress
        if(self._type == self.PERCENTAGE):
            p = p * 100
        return s.format(p, self._decimals)
    
    def __repr__(self):
        s = "ProgressPercent(start={0}, end={1}, decimals={2}, prefix='{3}', indent={4}, precision={5}, )"
        return s.format(self._start, self._end, self._decimals, self._prefix, self._indent, self._precision)


class ProgressFloat(ProgressBase):
    def __init__(self, start=0.0, end=100.0, decimals=2, prefix="> ", indent=0, precision=10, ):
        super(ProgressFloat, self).__init__(start=start, end=end, type=ProgressBase.CLOSED_UNIT_INTERVAL, decimals=decimals, prefix=prefix, indent=indent, precision=precision, )
    
    def __str__(self):
        if(self._type == self.PERCENTAGE):
            s = ("ProgressFloat({0:.{1}f}%)")
        else:
            s = ("ProgressFloat({0:.{1}f})")
        p = self._progress
        if(self._type == self.PERCENTAGE):
            p = p * 100
        return s.format(p, self._decimals)
    
    def __repr__(self):
        s = "ProgressFloat(start={0}, end={1}, decimals={2}, prefix='{3}', indent={4}, precision={5}, )"
        return s.format(self._start, self._end, self._decimals, self._prefix, self._indent, self._precision)


class ProgressBar(ProgressBase):
    def __init__(self, start=0.0, end=100.0, prefix="", indent=0, width=30, open_char="[", progress_char='\u2022', space_char=" ", close_char="]", percentage=False, decimals=0, ):
        self._width = int(width)
        self._o = str(open_char)
        self._p = str(progress_char)
        self._s = str(space_char)
        self._c = str(close_char)
        self._percentage = percentage
        super(ProgressBar, self).__init__(start=start, end=end, prefix=prefix, indent=indent, decimals=decimals, )
    
    def _print(self, value, finish=False):
        """print value in correct format and style"""
        self._tcount += 1
        sys.stdout.write("\r")
        
        pos = int(self._width * self._progress)
        per = ""
        if(self._percentage):
            p = self._progress * 100
            per = " {0:.{1}f}%".format(p, self._decimals)
        
        if(finish):
            # last print should contain end of line or next print will be appended to it
            bar = "{0}{1}{2}".format(self._o, self._p * self._width, self._c)
            # m = "{0}{1}{2}{3}{4}{5}\n".format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, bar, per, LogStyles.END)
            # sys.stdout.write(m)
            
            # log using normal logging utility, otherwise will be omitted in log file
            # \n not needed, will be added..
            m = "{0}{1}{2}{3}{4}{5}".format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, bar, per, LogStyles.END)
            log(m, indent=0, style=LogStyles.NORMAL, instance=None, prefix="", )
        else:
            bar = "{0}{1}{2}{3}".format(self._o, self._p * pos, self._s * (self._width - pos), self._c)
            sys.stdout.write("{0}{1}{2}{3}{4}{5}".format(self._tab * self._indent, LogStyles.NORMAL, self._prefix, bar, per, LogStyles.END))
    
    def __str__(self):
        if(self._type == self.PERCENTAGE):
            s = ("ProgressBar({0:.{1}f}%)")
        else:
            s = ("ProgressBar({0:.{1}f})")
        p = self._progress
        if(self._type == self.PERCENTAGE):
            p = p * 100
        return s.format(p, self._decimals)
    
    def __repr__(self):
        s = "ProgressBar(start={0}, end={1}, prefix={2}, indent={3}, width={4}, open_char='{5}', progress_char='{6}', space_char='{7}', close_char='{8}', percentage={9}, )"
        return s.format(self._start, self._end, self._prefix, self._indent, self._width, self._o, self._p, self._s, self._c, self._percentage, )


# default progress reporting factory, style and options
PROGRESS_PERCENT = "Percent Progress Reporting"
PROGRESS_PERCENT_CLASS = ProgressPercent
PROGRESS_PERCENT_OPTIONS = {'start': 0.0, 'end': 100.0, 'decimals': 1, 'prefix': "> ", 'indent': 0, 'precision': 10, }
PROGRESS_FLOAT = "Float Progress Reporting"
PROGRESS_FLOAT_CLASS = ProgressFloat
PROGRESS_FLOAT_OPTIONS = {'start': 0.0, 'end': 100.0, 'decimals': 3, 'prefix': "> ", 'indent': 0, 'precision': 10, }
PROGRESS_BAR = "Bar Progress Reporting"
PROGRESS_BAR_CLASS = ProgressBar
PROGRESS_BAR_OPTIONS = {'start': 0.0, 'end': 100.0, 'prefix': "", 'indent': 0, 'width': 50, 'open_char': "[", 'progress_char': '\u2022', 'space_char': " ", 'close_char': "]", 'percentage': True, 'decimals': 1, }


class _DefaultProgressReporting():
    progress = None
    cls = None
    options = None


def set_default_progress_reporting(progress):
    if(progress == PROGRESS_PERCENT):
        _DefaultProgressReporting.progress = PROGRESS_PERCENT
        _DefaultProgressReporting.cls = PROGRESS_PERCENT_CLASS
        _DefaultProgressReporting.options = PROGRESS_PERCENT_OPTIONS
    elif(progress == PROGRESS_FLOAT):
        _DefaultProgressReporting.progress = PROGRESS_FLOAT
        _DefaultProgressReporting.cls = PROGRESS_FLOAT_CLASS
        _DefaultProgressReporting.options = PROGRESS_FLOAT_OPTIONS
    elif(progress == PROGRESS_BAR):
        _DefaultProgressReporting.progress = PROGRESS_BAR
        _DefaultProgressReporting.cls = PROGRESS_BAR_CLASS
        _DefaultProgressReporting.options = PROGRESS_BAR_OPTIONS
    else:
        raise TypeError("teoplib.utils.set_default_progress_reporting: type is not known")


def get_default_progress_reporting():
    p = _DefaultProgressReporting.progress
    if(p is None):
        raise Exception("teoplib.utils.get_default_progress_reporting: default progress reporting was not set.")
    return (p, _DefaultProgressReporting.cls, _DefaultProgressReporting.options, )


def get_progress(end, indent=0, **kwargs):
    _, c, o = get_default_progress_reporting()
    opts = dict(list(o.items()) + list(kwargs.items()))
    opts['end'] = end
    opts['indent'] = indent
    return c(**opts)
