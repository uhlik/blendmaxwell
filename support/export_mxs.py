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
import json
import struct
import shutil
import math
import datetime
# import logging
import os

from pymaxwell import *


# logger = None
quiet = False
LOG_FILE_PATH = None


def log(msg, indent=0):
    if(quiet):
        return
    # print("{0}> {1}".format("    " * indent, msg))
    # logger.info("{0}> {1}".format("    " * indent, msg))
    m = "{0}> {1}".format("    " * indent, msg)
    print(m)
    if(LOG_FILE_PATH is not None):
        with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
            f.write("{}{}".format(m, "\n"))


class MXSBinMeshReader():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        # signature = 0x004853454D4E4942
        signature = 20357755437992258
        l = r("<q")[0]
        self.offset = 0
        b = r(">q")[0]
        self.offset = 0
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            self.order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            self.order = ">"
        else:
            raise AssertionError("{}: not a MXSBinMesh file".format(self.__class__.__name__))
        o = self.order
        
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINMESH'):
            raise RuntimeError()
        _ = r(o + "?")
        # mesh name
        self.name = r(o + "250s")[0].decode(encoding="utf-8").replace('\x00', '')
        # number of steps
        self.steps = r(o + "i")[0]
        # number of vertices
        self.num_vertices = r(o + "i")[0]
        # vertices
        self.vertices = []
        for i in range(self.num_vertices * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.vertices.append(v)
        # vertex normals
        self.vertices_normals = []
        for i in range(self.num_vertices * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.vertices_normals.append(v)
        # number of triangles
        self.num_triangles = r(o + "i")[0]
        # number of uv channels
        self.num_channels = r(o + "i")[0]
        # uv channels ids
        self.uv_channels = []
        for i in range(self.num_channels):
            self.uv_channels.append(r(o + "i")[0])
        # triangles
        self.triangles = []
        for i in range(self.num_triangles):
            # triangles (int id, (int v1, int v2, int v3), (int n1, int n2, int n3))
            v = (r(o + "i")[0], r(o + "3i"), r(o + "3i"))
            self.triangles.append(v)
        # triangle normals (int id, int step, (float x, float y, float z))
        self.triangles_normals = []
        for i in range(self.num_triangles * self.steps):
            # int id, int step, (float x, float y, float z)
            v = (r(o + "i")[0], r(o + "i")[0], r(o + "3d"))
            self.triangles_normals.append(v)
        # triangle material assigment
        self.triangles_materials = []
        for i in range(self.num_triangles):
            # int id, int material slot/id
            v = (r(o + "i")[0], r(o + "i")[0])
            self.triangles_materials.append(v)
        # uvs
        self.triangles_uvs = []
        for i in range(self.num_triangles * self.num_channels):
            # (int id, int channel id, float u1, float v1, float w1, float u2, float v2, float w3, float u3, float v3, float w3)
            v = (r(o + "i")[0], r(o + "i")[0]) + r(o + "9d")
            self.triangles_uvs.append(v)
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")
        
        self.data = {'channel_uvw': self.uv_channels[:],
                     'f_setNormal': self.triangles_normals[:],
                     'f_setTriangle': self.triangles[:],
                     'f_setTriangleMaterial': self.triangles_materials[:],
                     'f_setTriangleUVW': self.triangles_uvs[:],
                     'name': str(self.name),
                     'v_setNormal': self.vertices_normals[:],
                     'v_setVertex': self.vertices[:], }


class MXSBinHairReader():
    def __init__(self, path):
        self.offset = 0
        with open(path, "rb") as bf:
            self.bindata = bf.read()
        
        def r(f):
            d = struct.unpack_from(f, self.bindata, self.offset)
            self.offset += struct.calcsize(f)
            return d
        
        # endianness?
        signature = 23161492825065794
        l = r("<q")[0]
        self.offset = 0
        b = r(">q")[0]
        self.offset = 0
        if(l == signature):
            if(sys.byteorder != "little"):
                raise RuntimeError()
            self.order = "<"
        elif(b == signature):
            if(sys.byteorder != "big"):
                raise RuntimeError()
            self.order = ">"
        else:
            raise AssertionError("{}: not a MXSBinHair file".format(self.__class__.__name__))
        o = self.order
        # magic
        self.magic = r(o + "7s")[0].decode(encoding="utf-8")
        if(self.magic != 'BINHAIR'):
            raise RuntimeError()
        _ = r(o + "?")
        # number floats
        self.num = r(o + "i")[0]
        self.data = r(o + "{}d".format(self.num))
        e = r(o + "?")
        if(self.offset != len(self.bindata)):
            raise RuntimeError("expected EOF")


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
            # sys.stdout.write("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n))
            # logger.info("{0}{1}{2}%".format(self.t * self.indent, self.prefix, 100))
            sys.stdout.write("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n))
            if(LOG_FILE_PATH is not None):
                with open(LOG_FILE_PATH, mode='a', encoding='utf-8', ) as f:
                    f.write("{}".format("{0}{1}{2}%{3}".format(self.t * self.indent, self.prefix, 100, self.n)))


class Materials():
    db = []


def material_placeholder(s):
    n = 'MATERIAL_PLACEHOLDER'
    # return clone if already loaded
    for p, m, e in Materials.db:
        if(p == n):
            c = m.createCopy()
            cm = s.addMaterial(c)
            return cm
    
    # load binary mxm file from base64
    import base64
    import os
    checker = b'TVhNCtcDQAdjaGVja2VyAAAAyAAAAMgAAAACAQEBwNQBAAAAAQC9GAEAGAAAAHSPAABYjwAAJUA9\nPEA9O2AFAjxBPiALQAUQQT09QT89QDw7Qj8+QT08PzwgICACIBpAFCARIA4gLKAIYBcAQkA7QC+g\nCCAOQCkgNSApAD0gI2ARAjpCPyApgERgOCAyQEcgCwE7QUBuIClAESAj4AAXAEIgGiAFICZgUEAL\nYE0AQSBNIGUBOzkgBUAjATw6IAIBQz5AKQJCPTpAIyA1YAJAFCCkoBQgGiACIBEBO0JALwM8Qjw5\nIDhACwA9IAIgFyAFQCBgCyAjADmABSAOIEcAQyAIIAICPjtEYBogCCAsQAICPDlEQBTACyBBIBHA\nDiAdAkM8OCAOAkU+OiAFA0Q9OURAHUAFIBoCRDw4gAWAFEApQBQBOUVAIAE4RmAFIAgARSACAD0g\nBUAXBUU8N0Y8NyAgAkU7NyAaAkQ7N0AdICAgFAA7IBoAOEAdQAUDOEc8NiALBUY7NkQ7NiARAEcg\nCwA9QB0gFEALgAgAOyAjAzZIPDYgLCAUYAUgCEARgBQASSAICT03SDw1ST03ST1gDiAUATs0IAsG\nRzs1STw1SiAgIBFgGgVKPTZKPDVCLWInIAgiCSAFQksiCQQ+PUNAPyAOQj8hxCACICBAJiInIA4i\nAEAOIAViDCAFIlFAFCAdQAhgBUAIIX9ASgA+QhUCPjxDIlRgRCHoQg9gJkA+IBqCVEAXIDggKSAU\ngAiABSAOYiqAGiBBgAggjEHxADxB9yK0IBcAPYA7gCMiDGAIgCOAJiHuIJIigUAUATtEYCAgCGJR\nQB0iY4AaIA4iLSAOIAUgC2AgIjkgC0AFIiFACKAdIAgiEmJLICwgCyH0IFwiRQA+IBogBQA7Iiog\nJiARAUM7YkhACyJUIpABOkVACyAaIjBCNiAIQi0gGiIqIAtAFyAOImOABSAmYBdgBSAUIA6ACyAs\nIAsBRj0iMCAgQBcgEaI8IBTgAAuiPEAIID4iEkACAD1ADiAUQAgBOzUgCEJaIkjCMCALIoEASIJI\nQkIiZiA4ADcgCwFKPSJaQBRAC0AIADUiIWI8QgkiVwJCQD4knSIAQBQiJEIDQAsAQ2S4ICaB62AF\nAD0iS0AjQdkiV0BBoAggR2AdQejAFGALIA4gAoA+ICwiliGsICwgEeACAiIegA4gVuACJiRVIC8i\nEmR5YkUgJmAjIA4gHSJFIAgiPKAIIEeADiBiQAhABSAIIB0h3yA7QiFgFEAOJLsh8SALIBciA0Aj\nIBcgL2AUIAVAFCAyAjpCOySmQC8iCSAOIAIkuyAFYkuADkALIBQiDyARIEpCIUIeQBeEsmAFIhhA\nF0JUZLIiEiAUgA4iD0ACgAiABSA1YldAFyAdJJoiQiAOIDiCQmIkQkUiP0ARQAVgIESvQBcgCAA9\nRLJiYyJ+IAsANiALYAUgCyJRQidCP2JFQmwgCCACIAtiYCALQksgDgA8Im8ANCJCQnVgF4TNIBEi\nVCS+Ju8iLSIPIh4iJyJF4AAOQAggBSARIV4nFiJdAEBklCAUIDJgLyARICAgHSIw4AEIICAgNSAF\nIAIgHSApQB0AOycHIBFAC0AFQAggESBWICMgHSAXQglCeCRMIE1CRSAmQBRgRCHxIA4gMmIbIDIB\nPEQgvIAjIh5gIEAjIBFB6IIhYA6AFyI5Ii2ACyAjIhggtiInAz07RT9gEUKcATlAJ1gfPTtpZmVo\nZWNva2lhXVxlYF5nY2JlYV9AOjg/Ojc+OTYCPjg2IAgCPzk2ICwLWFFOXVZTTEdFSkRBQkUiLYJL\nIkUgCEACRMcidUALQAXAC0InYAsiGCTTATs3ICNCIScrIi0gRwA8RuMiPCAUQCNADiAgADkm6SAU\nIjwgF2AORuAgCEI2IBegCyAIIA4gAgA2Ij8gCCI2IDJACAE9OSI2IA4gAoAmIieCVyAXIAtAAiAI\nIjkgF0JIQA6gCEJ4RJQiXSAXIlEgCESjIAUDPDZLPUACglohnUHl4gBRIesiACAUZKYgGiARoALg\nAQ5AHSGsIgCAC+ADBSJjIC+AGiAFJOigKSG1IpkgHSAjgEEgEWAjQA4iMAA7okggNSARIgAgICJR\nIDggEeAAOEAU4AIFIoFAEUAIIDJACyApICBgDiBKJGFAHWSjYAgiTiAXICYfPTpHQ0FNSUg/Ojg8\nNzU3MzEyLixEQUFfXl2RkJDAvr4fw8LBxsTExcTEycfHwb++vr29UE5OHRgWHhoZGxkXHxwfHB4b\nGSspKGtnZYqGhaGdm5uVk4N8enBqaGNbWFlRTU0BR0QgcSJFIgxEsiIGItViZkARYlEpSiIPIAIg\nCCJLImkgAiSXIB0gI0AIIkJACyAmIBciWiAIIBdCbCAUQhUiM2ARQAVgHSARIAhABSALIiogGiAF\nIkJCJCAaIksiHkAFIBRErAA7QjOAEQBIJLVHFqJRQktAGiAUgkJCYCARoAhiWiJRIk5gFAI2Sj4g\nOEAOAUs9qV8AQabRIlQCPD87JENB8SALIgNB8ScZYmYh3yAjIAugAmIeIAVAIGALICBAAib1IAhh\n3yReIhggHYAOIDiB9yHxgAsieCAIIehAJiHuIBFAGiIJQCmAGiIVIA4gAkTEADygIyAyIHcgBSAC\nIBcgBSA7ICOCNkAOIAskiGApH0ZAPk5KSVpXVWFeXX57enh2dmdlZU5MS0RDQhwaGQ8OHw4GBQMi\nIiKBgYHU0tPW1dXY19fV1NXX1tbc2trU09PVCNPTzcvLXFxcAOALAB1NSUeVkpHHw8LAu7q/u7m3\nsbCmoaCdmJeEf31bV1YrwAVAOTZBOjaHGSIwZJdACCJFIAJCMwE+O0SmIAtJayI5ADoiG0AFJKkg\nDmJFYBciTkAOIkUgFyAFKaogBWJFIj8gAiTKIkJAFCIhIBEgO0AOQAUgJiAdRu8gJiIqYAUiMyAR\nJyVACCJdImwgBSACQjxgCCSgAkc8NSJsIA4gKSSyIjzpAGUknSAOIl2gAiccICAAPElfYfRB3ABA\nIbhADkHN4gFpa8wgI0AXwAViPCAyIjAhykAC4AALICMgESAFQjBgCyAIYCwiFSIAIiEgEUAyQfFC\nOSARQAgkmkAIYniAFCIYICBABWAaIqsgCyA7IAJgKUA4AUM/LhhCRSbRIB1gBSBKIA5AAiJvF1xY\nV3BubZOSkqqpqcnIybu7u52dnUA/P+IGIQ8gICB5eHnQ0NDa2dnb29vcIAMG2tvZ2NjY1yACCdfU\n1NTNzMxXV1fgBjXgAAAaQ0JBoJ2cxMC/xcLCw7++x8TCwby7wLu4saupImAUYlxaLy0sKyclRUA+\nUkpHW1NPSEA9IkVAAiIzIiQiLSI/JUIpjCJUQBoAOSSsIBcgCEAaICZCJOACCCAXQBFCKicZAUY+\nJJ1CQmAUIkhCNiJIIjagCwA8Ry5CXWJFwBRCLS4tImYgKSI2IERgCGJOIBQgCKAFJxkgAkSgYAhC\nXYJCQlpgDiJOIBEASyAFKV8hsmcEhJ0hr0AIIhhCBiAIQAJgIEliIhIh6GAFRt0gFCAsIBFgKUH0\nQC8gNSHQIAsgGiAvIAJAICIDQAsgF2IkYAhAEUAmYB2AFzDTa1EgIGJgICwAQSSsQEogL4AIJIhC\nWkAFIlcgF0BcIBQgCwA9KTIiSyvDGkRAPmpnZp6dnbe1tt7d3uzr6+Hg4cHBwVBQUOIBDeACAAKS\nkpIiSwvf3t7d3d7d3N3g4OAgDiJUA9ra2tsgAwfZ2tHQ0FVUVeADMuAGAAVMS0uVk5IiUAbGw8PD\nwL7AIlcBvLwkvgW/ubewqqgkuwI0MzMgMwU3MzJXUEwpswhfVlJXUU5MQz/iADwiUSJFJIIARESX\nQiEgDiIJIidCRSAI4AQOQBQki2AUQjAiY4AsgA4gCyIkQDsgFyACQA6CPCALIAIAOSIwJuMgI4I/\nIlQiLSARwA5CWiAjIAhEuyAOQlEiQiACQBcASYJjIAhnDSJRIAIgCyAdICMiD8IeAj4+O1JfZF4h\n9yACIdMgHSH3IjwkfCGygAhAF6AOIAsgFCIhIgMgAiHlId8gLEA1QopABSAsQCNAGoAFhHAkZyAd\nIgNgBUKKgB0gDiAIIAUgJiItIAsgAiAIQBEgCAA/IAugF8ARQA4gFCb1Cz87OVFOTYyKirCvryR5\nCOzs7O7t7uXl5SSIApybnCHW4AwAAk5OTSJCAuLh4iJOCN/e3+Hh4ePi4iAICNbV1tnZ2dTT1CS9\nAtPS0+cPB+AAAAVFREOvra0iVyJdBcPAwMC9vCJdEb66ub24t7y3taSgn2tqaiYlJYAwDjUwLl9Y\nVGhhXmlfW2RcWGTBRLgiFeIAaScWIgAgDiI8IAIibEACIiFiTiIzIB0gCwFGPSAmIAWAESJIIi1C\nSyJRIAuEfyAFIBogAillQAtCJ0AjIjYgCyAFIA5iUSIqUHkgFEAIIntAESJyIA4iM0SRRwRCQkAU\nBEo9N0s8UsgpU0JRICNACwA2Ih4iOSJaIhUgCyIAJw0CQj4+MHAgDiISIBriAUhAGkAFICYh00AF\nJLViEiAINU1ARCAaIAsgKUJmIEEgTSAXQAUgMiBNRHxAGmAFIm+ACyAyIBpABSI5QBcgDiAIIqJg\nBTC7pMdAIy3ZIFAgIEJOGDxIREJWUlFLSEdOTEx7enq1tbXp6enx8PEgAkJXBe7uwsHCVuYRwgsp\nKSmzsrLe3t7j4+Mk00AAB9/g39/g4eDgIlQC19bXIAUnBxHQz9BSUlM3Nzc2NTUqKiomJiaCHuAG\nAAxoZ2fHxcXBv7/DwcDFRLgVv7+8u8G+vL67u725t7Swr4qIhwcHB+AANhI3NjZXUk+Lgn+Kf3ty\nZmBYTUhLJMFCQkIkQAUiMwA+QAUiIScHJNMiGyJdQA5iSEAFIl0uFUAOIkggOEIqImYgKSSOICkB\nSD4iSyI2RKMiQiIzIAXgAA4iZiIzIBEgFyIVIk5CXUlWIAsiVwE1SDK2YBciOSARQAUuFSSXQB0k\npkJRJv4gOyAaiWIiVCHZIkJACCGmJGoiAEH0ZHMwXkI2Ic0gAiItIhsihCAIIDVgICARIBdgRCBH\nICYgCyISIB0gOCH6IA5AF4AsIBdARyReQDUgCCBTNX0gBUAmYBEmvyALIi0iS2ARIj8gGiAyIAVi\nUSAIYEcgCAdlY2JycHBkYiuMB11YWVisq6vtRKAS7/Lx8fPy8/Hx8vHw8M7Nzj4+PoHHHysqKjw7\nO0lJSVFQUGNjY4SEhIB/gH18fLKysq2sramoH6mbm5ugn5+dnp6SkpGIiIh9fX1ubW1kY2NsbGxr\na2q2H7W1v76/wsLCvby8uLi4rq2uoqGinp2emZmZlpWVlJOULkgelJOTqqqppqSksK+wube2t7W1\nt7S0vry7v7y8u7e2vyvVBLKycG9ugI/gAAAs3Q53b2ueko2dkIuMgX1fVFBJXCInYAIiRSIhIAWE\nviIwIBcko2AFQkViSyJCLjwAOiI/IksgLyACIjAm8iAFIAIgIAFFOkSFIAsgKSAFIjZCSyIbYBEi\nJCAUZJciNkJmIAgiJyAXIjyCTiI5IAsgBSAXQB0gCGSdJwEgFySyKWskrCAIIcRCG4H3Qe4h8SAC\nQAsiDCHQQAUh4iALIAJADoI5ADwk0IAORIIgFyAyQEph/SJ7RF4kbSA4YAUgIEAIYmwkamAsQh5C\nIQA8IksgBUAjIk6ANUAgIpMgICAXQAIiRSSmIAsgUx9GQkFraGdzcXGAf39dXFwkJCR/f4DRz9Dy\n8vP29vb19An18vHy7e3t5OTkJHYFl5aXn56fIeUgAALExMUm7wrd3Nzh4eLn5ubm5SADBOaZmJkA\n4BoACDExMdHQ0dbW1icTAtXU1SAALicA0SAABNDQzMvLIAUCy8rKIAgIyMfIsK6uGhoaLl0dODg3\nS0pKRUNCYWFhaWdmg4GAj4yMlZORkI2MWllZMIcFKikpGBcX4AB9FFNLRpKHg62el6WXkIZ2bmlb\nVUdAPCSyQlGCGEJFYmBCV2JRInU08yALIBEkcEAIIksiOUAFYjYgFyALTh5CNiS4YjNgLCALK5wg\nBSJRUtQiGyJFIpkiaSAaIAUgDiSvIAsiSCAFJvVAEUlQIBdALyAIIlQiXSJRIAgwaiJUIlpEfCZr\nAUA/Ik4gCyG4IhVCQiJFIkIgDiJmYjBgCyAaIfQgEQA7IAuAFyAOVR0gBWAaQCAgO8AdQCNGsEA1\nICAgDiAgImAgMoA4IBSAHSAyIAsgBYJs4AELIl0gFCAaAD1G8iuNLd8FkZGQT09PIZELODg4sbCx\n8PDw6+rqK28WzczNs7Ozp6inf35/dnV11NPU7+/v7ewiZQPt7+7vICYC6unqIAsgESAvBunp6d7d\n3jNrTuAYAA4wMDDMzMvW1NXS0tLX1tcpvBHW1dbPzs/Ozs7LysvOzs7S0NEuMyACBcTDxFlZWeAV\nUQU9PDyWlJQpcQiQi4l9eXdsaGg1WRc7NzVGQj9za2ilmZSun5elk4yKfHVnXVgiGCJOYjlJXCbm\nIAuAAkJyIjYgHVU1QBciJCJFQjYgFyJgIAsiJCIGQAsiLUI2IB0gEWALIBpgAkARYAUiQiAaYAtg\nCEAFQAhgFyJLIkggDmACIAsib0JFIAgnDSACIlFiYIu3IhsgAoIP4gFLIh4iACIJhJGACyI/QAJA\nCCH6V59AMia5QksgGiAOJKwAOyAOIhggFyJUgBRABSAsYkUgFCAdICkgMiAFgA5gBSJsYBSCSyA+\nYB0gCCA4GmpoZoaEhIuLizc3ODAvL2RkZF5eXqKhorm5uiaJB2ppaSwtLCUmqxUm7ALKyckkuADz\nJMUB8/MnEAnw7+/s6+zv7u7qgAAA6UAHBcrKyhkZGeIVA4AABS4uLtTU1IJOJK0D19fX0yAABdLS\n0tHS0SS0BM/Qz8/PJ3MgdAXIyMiGhYagNuARAB9QT06uq6q1sbC1sK60rqyknpyim5iNhYKJgX6F\nfnuglg+SopWPrJ2XopKKhXRsY1dRlTsiRWJLIi1AAiAOIAIiMGACSXpADkJagodCQiAFRI4iLUAL\nqUogESJpIj8wdmb1JJ0gFEAjIBdAC0AIIAtgAmJUYksgGkApIk4gAiTKQBSEqUJyQlcrxiJ7QlQh\n4gE/PyJFiU0gESHNgA6ACCALJF6gCyIVIetCD0IJIjlgPiAjYiEgOGAXIA5AC0AUICYgFCACIAhA\nF4AUgipiXWAXIplEwUcTwC8iqyTKBjxJRUN7eXgmXAvAv8F0dHSLioqkpKQkJgTFxcVVVe8N+AY2\nNTa/v7/zIlNpYgPx8fHvZKwC7u3uIAIkrCvMJK8r1QKko6ThEvrgAwACNTQ0IkQyywLX1tckqQLY\n2NgiUQHT0kJaANEkqSAAAMxgAAHLzCJaAZ2c7hB74AMACGhmZbKvrrezsiJaArOurDLsH66npa2m\no6uinqifnHx0cWdcV4B1b5GBep+QiXlrZDs0AzE9NTIkqaJUIjwiV0IbRKlgF0ARQB0gESAaQAsA\nOCv2IAVCQsAFIjkAR2IeIBQiPyJOIBogFCJgIkJCS0AFIAggHSAFQlonB0JCZKCACyI8IAiEnSAI\nxKkgF0JdfmVB62HWYAVCEiHxIkgiKkAaIAgh60ACYlEiHkAIIi1AGiH9oCkgCyAUgEcgCEA7ID5A\nAkALIiQgL8AOIBFAOCAUIAIgCySgIFZACIApQD4APDlnHW5ra5+dnt3c3cTExLW0tNfX1/n4+fv6\n+9/f319fYOEEpOACACcZCfX19fTz9PTz8/Am/ScLAe/vIAgkr0S3Ae7vIlogEQTn5udQT/INzuAJ\nAAIvLy8iSDLUCNra2tjY2NbV1ilfAtbW1iAUJLAkrScKAtDOzyliBc3MzcHBwSlZ4ApF4AgADoOB\ngbazsrOvrrKura+qqTLpH62lo6yloq6loqKalmxlYhUVFTo0MmlfW3ptZnBhWVFIBkQxLChBOTVi\nRSI/ADgiEkAIgAUwQy48gBQwo0IzIkIiHiI8QCNwZCALIAgkkWAFIAsgAiAOIlcgGiJaIAVAEUAO\nIkuibEcWRvUgEUAIQAVAGiJFYktAFEALImkksgE9NSRqIg8kryAFAEBiDyJFgBQAQMIkJtcgHSIV\ngi0gBSAOIj9CEiToIAsgGkAFRGogF2ApIidgJkI2ICYiPEACgA4gHWA1RP0kkWAagCkgCyACICkg\nBQM8jYyMO5UL9PT04uLi9vX2////IlQgAiHWAlFRUuEJo4AABUlISO7t7SA1IlQiXSSyIAUiYyJX\nIksC6urqLjMgCwjq6enIyMgfICCgNuAXAAIVFRQm7AXZ2Nnc29w3hyJXJw0nBycEAdHQJwsG0tDQ\n0M7NziSwJLgFx8fHhYSF4BhTIAA1LBifnJuzsbCzsLCxraqzrq2tqKWvqKarpKKsKX4HlpNqY2AJ\nCgpAKhMAADszMEtCPTAlH1ZIQUI4NElAOyJdIkUgAiJaIjkpZSI2ImMgCyJUoAhADkbvQAggBSJO\ngkIgKX//AxCCSESdAD6ksiAaIiogFyI8IAIgCCACJu9ABUJdgmBCQkJLYAUgFGAIS7oATHK/YfRy\nsCIVIiEkQyvGZDEiYEAdQAUifiI8IAIiLUARIhtACEALIi1HKCAIQBRAOGAXID4gCEAdIBcgC6Jy\nIAggAiAUQAIgNUBQLe5AKUAvAD4t7glAdXNylZOUra2tPfYiTgL9+/xABQH8/SACBd7e3k1NTSFk\n4AwALYU0jwL39veHBCAAAvHw8SJXIkhpYiS7Ql0gBSS7AoyMjOANReALAAIrKysnAQHc3DwwANol\nNkcQA9fY1NNAACSsAtLS0iAFA8/Oz80ruQfLy8vKy62srOAMR+AJAA94dnWwrq2zr6+vq6qwrKux\nMPIDqKaqpSJXDKGqoZ2hl5RtaGYeHR3gADkMMyolXlFJf29obl5XSSbjJJciNmcBIjABRjxCXSAO\nQj8gHaALKWVgEUAXIlEiYCAFQCYiKib1IA4iVyAIIALiAUiOD4JRYBeCSyAgQj8iQiACQk5AIyAF\nJKYgIEcQLg8kiyHQIjlCM4AIIkIh9yInIAIiSEHrIBEgAiAjIBEiDCA1QAsgDiAUYCZGuUJsRwog\nI4ACIjkgI2BKQAhALCAOYAhATSApID5gDmAIQDsiVAhPTU16enqGhYUkGQL9/f0iUYAAAvz8/CQi\nAlNSU+EAYeAJAAZlZGXy8fH3YlcC9vX1IlQk6CSsJKkpZSJsIlUkzSS1MGECRUVG4ApC4A4AAi8u\nLjBMJwcA2XUsANZnBwHR0UlcIk4iVwLOzc4gAiJUIAIwbQXGxcZaW1rgD03gAwAdKScnk5GPsq+u\nsK2ssq6srqmoqqakqqWjq6SjqKKfIl0IoJeTbmdkHR0c4AM2DlZKQ4VyaId0a3RgV1VIQiSvgAIi\nM0JUIjmgC0JaIjZgESJLQlEiKiALIjYiSyAaIAsgAiALIjwgGiAIIjlgCGAFIBRHBCAvIAJVGkAI\nIk4APiAOADcgBSJFIlQkuCJUiW4gDiI2IAJCEkAIIe4gCyIAQBRCPCALJIsiOSAXYBRCOWALYBow\nmo3ZQB1gBUKQIk4gSiAOIAggAiI/IA5ACMAFIFMgHSAOIAUgF2ACIBEk0A8/LCopLCwro6Ok7+7v\n+vn6IlIB/fxErCAAImYCQ0ND4QNb4AYAAiIiISaMBfz7/PLy8iJOAvX19iAAIAsiXSJsJKMiWiBW\nAe7uThgCvby94Ac/4BQAPpgi1QLZ2NknBCAFJK0C1NPURwsgAAHU1CcOIlopYySrS8MBzc0iWgKS\nkpLgFVPgAAAIVlVVsK2tr6yrJLIJramoramnrainqyJaEKajqqOgp6CdnZWTcmxqBgYG4AEzEQAA\nQDUudmVcnIV5iXJlaVdOSTKbJwokuCJLYl1CRSAIQjkiaUJyICAiLSAFRxBADiJLQnUgCCIVIl0i\nKiAgQksgBUACQnsgWSAdIA4nCiJFIAsgJiI8IAtEo0JpQBEAS2ARQBcBPDVB0CH6IdZkbSAFIA5C\nOSAOIehgBSALwAIiV2b+IAhCGCIbJL4pmyARxwqANSJLIE2CqCAFZ2EgI6AIIDWALyA4QC8RPVNQ\nUDIvLRYVFRsaGr++vv/+QkiAAAL8/P0gCQbb2tpBQkIA4BQAC5eWl/X19fj39/j3+CAAAvf29iJR\nAfX0KVwrwQD0LgkiXQDtK7EB7u8nEwKAgIDgFU3gBgACHBwcJvsE2dnZ2tknBwXY19bW1dRQbQjX\n1tfT0tPR0NAnASACThQDy8zKyVBtPvLgB0XgEQAIiYeGsq+vsrCvMHwiYAyrpqSppKOmoaCpoqCp\nIloGn5yel5RdWP8H/wFRESYhH29hWpuEepmAc4JtYlVIQyJXZvJkoIcZwBEiPIACIiFiWiccIAiC\nV0AFQBdAEUAgIloiPCACMEwgFyAIgAIiMyJFIlEASimMIB0AOyJpTgAgESJjIlpAHQA+XB9iFSR5\nIj9gCyHrIgCCTmALIA4gGmALIlcrzylEICNAESAOQAgAPz3zIDsiSEAIIiqAAkKEYlEgBSAjIBQi\nQiACQHFgIyAgB05KSX9+fm9uWNo7LAK2tbYiReAHAAT+/3d4eOESlCAABT49PeXl5SSsIAIkpyJa\nAPUruVK7JvsA8CJIAvHw8TBeIAgI6+vr6urqU1NUQDbgIAA3GwXS0tLf3t8i4USvANZekiJRAdXV\nS70ku0leAM5HBwjOzc3LysvIyMg58QBC4xcL4AAACzs6OqOioa6sq62pqSJXJLUXrqqop6OhqqSi\np6CeqKGfp6CcmpKPPjg04AEzYAAUFw4AaFpTm4J1noN0i3BjZlVNSUA8IhsiOSJRK9IgCyR2IAUp\njESmQj8ickJRRKxAHUbpIBQiJyAXgj8gCyAdIAsgESJaJKkgESAOYAJku2AFIl0gESJUJLViYCAp\nIAiiVyQ9IeuCGGAIIioiSzT2hJ0gCyIJQBQiIWAdIA4gCCInJKZr5CAjICAiLUAaIClgU0clQDsi\nSyAaIAVADiBuLksHPj1JRkRubGs7UAJwcHAhIgUhISHBwcHiA1IpUIAOAKzrFwMILSwtxsXF+/r7\nIk4C+fn5IAUD9fT09mcHNRcB9vUgAAH27zLCAe/wImYH7+3u5eTkGxzoBK7gAwACKCcnOhswWCur\nCzIxMSoqKjo5OTs7Oi4PIkUB2NdODCcNImYC1tXWIAUB1NMuFy4ZQAIpXCJgJLUCycjJJwoCa2ts\n4ARa4BQABWFfX6+trSSyCq+rq62qqaqmpamlRLUkuw6moZ+ln5ylnZuLhYQgGhbgBkcgERFgTkSb\ng3ifh3uZfGxvXVRBNzEiPyJXIjZgBSveQmYiJCARK8+koIRzIBQAPicfIB0nFivDImYgBSA7IjxA\nAiA1QAhiMAJIPDRklEARPmIgCCTBJvsiZkAgWcdCVyIVQhIh/UIMIAgh9CbXJHBCG2AF4AEaIAsi\nGCAdAkRAQCAFIB0iYyIkIAgiNmAFICNgCwE/Plv1IAskqSAaIDggKSAOIF8gC2AIApCOjSz6AkpL\nSyElBSUlJbSzs4JF4AYABdzb3Ds7PCAj4BIACXR0c/j4+fr6+vlnASb4JwQF9/f37OvsPn08CgXo\n5+fa2toh/CRhEb+/wMTDw6ampqqpqaupqq6uriUkBMPDw87NKR0AzCkpIjwD09PT1kJCS58t6B/T\n09TKycppaWlQT09RUVBTU1NSUlJKSUlfX15bWltiYR9hcXFxdHNyenl5h4eHjIuMkJCQlpWVkpKS\ngYGBenl6dApzc3FwcWhoZ0dGRzp4I0Ek/eAJzwodHBuTkZGtqqqsqiSyA6yqp6ZCWkJUD6CnoZ+h\nnJqjnZqkm5hrZWLgCTsUHBQQb15VnIN2nYJ0l3lpdFpMRTo0IiqHEyI/gic3XSJXIBRABUSgQkhA\nBSI8JNAgBeABDiALJLVAFCIzIjmE1ku6S6tCjSAFJJokpmAFQAsiWgBLIB0APCJXIicAPd5EJKAk\nhUH9IgAgCCACImYgF4JFIBSCOYAOJI4iMyAyIBcgKSAmQAIgCGACIjwAQzLdIBpgJiJOIAsgL2AX\nCT2enJ2mpaVEREUhIjkiAquqquIHT2AAKR3/GP8E9gs1NDW8vLzr6uvh4eErNgLBwcEiKhGrq6uF\nhIRubW5cXFs4NzgjIyMgaOAAAAKvrq8paCJ1IAIuGAXq6erp6OggAiJ+DObm5+bl5uHg4ePi499/\n/wWMCd3c3ODg4Nva20LmINTgAAAJdXR0xsbGxcTFxT7zCsXFvLu8ubi4s7KyMUIFoqKilpWWLvYF\nfn19YF9fP0AIQ0JCbWxsq6moOFwgBSJXBaajoqWhoCACBaijoaSenZnrBJ+YlVNQXRvgBgAUJB4b\nb2Vel4B1nYBwlXpsf2dbQjk0IjwiMOAAAiInIAsrwyuKJMQgC0I/YBdCVMJLIkIiPyS1Im8iVCAa\nIAIiPCA+IA4iQmAOKWhgCKSjADcibwFMPiAdJLUAOEHrQjZABSH0YiSCAEIqQBcgGiACIh5ABSAj\nQAsgBSAOYl1ihyAUIAIiSKS7QBoiPCc0gAtAJkALQBQgESEwJCIiTiEaJsICqampgkXgCQACoaGh\nICPgAAAmmwVYV1eUlJQkbQi/vb7DwsPR0dI1NSRJJPECGxwb4AEq4BQABMbGxu7tOdNegDnNAujn\n6CJUAOkgACAHIloH5eXk4+Th4OAiWgLg398iXSAABdra2js7O+AVVuAJADzEAsfGxyJUBr+/v8PB\nwsAgBgK+v70jBgq8vLm3uLa2trq5uiJpBba1tbKwsCEWC6moqGRjY19eXXNyciTlN40ZjYqJnpqZ\noZ6do56doJuZop2boJmWjYaEIB7nCscULCgmcmNbmIB0moBzmHpqf2hbRDgzNSwnEyI8JH9ABSJO\nQlQgCESRIAggHSI/IAIiJyAFRxZiUaJXKUEAPGJaZwciNiAXICkm7yJjIAIpUyJUIl0gICAUIm8g\nIwBBcq0iEkIzIgmCJ0JpQBRCDEAaQgwgBSAOYBdAKSI2RI4iQiIwICBADkAXQBEgLCA+S7FHDSAp\ngB0gCAhPTEunpaWzs7OBgyIMApGRkeIKT2AAAsDAwSRqCFxbW5WVlbW0tCixJF4B/fxpdAH+/iAj\nBf7+/v38/StFgE3gHgAHMjIx5eTl7OskrQPs6ejpIAggACJOIAsA5yAABObn5eXlIAUN4uHi4+Pj\n4ODg3t3d4d9ErwI9PT3gH2PAAAIzMzIw0ADFOoUAwyACBsPBwMHAwMAiWiJLIl0Bu7qiVCJXJMQC\nsa+vKVsCgH5+4AA+gAAXMzEwRkNBa2loeHRzh4OBmpSSopqXf3l3oB7gBQAWLiQfeGdemoJ2mX9x\n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\nWCyJVi5UNhpJOzNCVGcERxMBPTY8CiJaRKwkuAFDQSCGKycAI/UC0QJTU1OiFuAFACbLLUsFycjJ\nzMvMIdbgBh3gCQAwNwA4/yD/T07gAwA0GCSjAPVCWQPz8fDxIlQiWgLu7e4iYwLv7u4kmgLt6+si\nP0JRIAUgAHmyAOUgAAHk5CACBOHg4Jyb/x8W4BUAhKYksgDIIlEHwsLFxMTFw8OCVCSoJJ0Bv75C\nUSSpIk4ksgK5t7cnEAWzsrK1s7MwWDBeN2YAj+c4ByXwBIqJiY6MJPkAiiJUIAIiVACEIAIBgoIg\nCCJUBXx6eX17eyACAnNxcSACIlEHd3V0cm5tKyrkEIWAABckHxsvKihDNzFFOjVDNC08MiwUDAAR\nDAigHmAAFx8TCnNONH1SNIRVMIhWK5BcLF87HUI2MGJXIloksiJaXnckrCJUJK8nBzXmL1AAKv8C\n/xcpJ7XiACUM2djZvr6+q6qqX19eLH//BI0xeOAAHeAQAEubAP8iFQAl/w7/jvzgFQACoaChIlcA\n8H//IXMiSCAAJKYiySACAu3s7USwAerrJKMkokAFAeXlIAUC5ePkIAgypwLj4uMgBS1Y4BZj4B0A\nAcjGQlQiVSuuJv4gCAbEw8TGxcTBa64iWicEJKwiVCuwArm3uCSdIk4EuLe3s7E5tQCuJwonBya5\n4B5u4A8AMnwtWwKNi4siWguJh4aIhoaBgH+EgYEkrwiHhoV+fHx/fn0iXSSyD3d1dXt6eHRycXNw\nb3FubDf/F/8Qe+AAABpQRD1mU0lqVEdiTUNeSDxXQTNFNComHhkDAgMgJAVrSC19US43eAuGVCiM\nWS5bPSc4LihiUVdyJLUksiJRaV8pXCJaAD8oGwHHx/8B/wVNCDU0NKKhos7Ozjq2AlJSUiBT4AYA\nIUsA/+APAAD+Yk+AAAH9/iID4Ac84B0AAqurqySaAfHxRKkgRCALIlciZiJOAu7t7iSmAuvq6uIB\nXUSnAOUksiAIIAIF4+Li4uDhKdTgHmvgFQAsXwLLysskpiJUAsPBwib8hKwpXAK+vb4iV4SpBb27\nu7a1tilRBba1tbi2tiJOIAgCsrGwJLgCrKur5DmvAm5tbou0BYmHh4eFhClcIAgChYSDIlcCfn18\nIlcnFiAFKV8IeXh3eXZ2dnNzMOMDcW9vOf8g/1z4H0k9OGRTSmlTSGxURm1URnBWR3BSQGhLN1xA\n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\nC0S1BJqam5iYKVwgCzdgAouJhySsApCOjSALAVdW/i50BAUGBWxpS6UroibyAmllYy4ABWZiYWto\nZicQIloAZTddAV1bNRQCX1tZMrMiYCAF/x7/FD4MPTYyUEVAUUZATkA5UzwcB0E2Uz80WEU6N2kD\nUDwvDP8B/wXHCAAvIRV6UDFlRyJFRKMm+CI/Il1gDiJUJwoBNVFktSl6IjYgAib4IkUgAiALglEg\nCyu6IAsNSEA9RT47KiYkmZiY3dwiLQDeIioiWiZxAjMyMiBu4AkAAjo5OiRSICkrsCI/Jv0C2tnZ\nIA4uVwTb2trY2EAFIAAC2djYKtjgCj/gFAAzIpT8IuckqYSmJwCG/ilWAMJ//xWmMFsIw8LDvry9\nu7q6Il05xzJx4BVZ4BUABRoaGqKhoCcBMFUgAgGjoUlQIAgAnkb+JKQAlCSvLfoCkZCPIlQwagCP\nJKYiUQGNjScHf/8fFQOJU1JS4BZj4A4AAjc2NTdjJKMnASb4AHInUANraWdjXlwyszwHJLgpWSSm\nAF8gBQFbWiACAEzwHWEUEA8OT0VATkM+UUU/Sjw1UD4zTzwxQlcGQjNcRTZAMP8E/wsgBVc4IHdP\nMSI5gkgiUSACIk6EoEALThUgHSJgUGcm9UJOQlEBPkc3dQBAJwEpaCJpAD5gBSAdCT06NTNNTUzM\ny8siUQHf3kItBdfW1mtra+EPCiYQA9vb291LpEb7AtvZ2zmBANwgDGJOAtnY2SAIAtfW1yHx4A9B\n4A8ABI6NjsXFK58CyMfFVO1N9wHFxSACAsXDxCSpAsTDwyALIFYkuwa/vb25uLe6f/8fCSJdArSz\ns+AQVOAaAAIdHBwkkVdnAaOiME9EtTdmAZ2cIAUgDgCaVQUAlSuuApaVlEJLAZGRKWUkoyligAIF\njouKNzY24Bto4AkAAk5KSS4MK6gCaGRiObUCZ2NhObUCaGVjIAsFYl5dYl5cJKkCZGFfIAsFV1JR\nW1ZUImAAN/8d/wMcBjYvK0pAPEwpEQRAOVFCOjK8AldGPTwZCFlEN1U/MRYRD+AAjQgdFA5uSCtl\nRCkklFmpQjwm9WJaZL4nEEJXImAAPSvGJK8kmgA8QAUAQSJFSVBQcABBIAViaSTHIAsEQD1EPTk1\nIxGfnp/X19fd3NzZ19jc3Nyvrq7gAHfgBgACWFdXJJcgKSbsIkIB3t0pXESgJLIL2djZ1NPT29na\n0tHRIAgCVlZW4Ac84BQABGZmZcvJS64AxmSdImAiWiACAMLf/xECJxMCwcDAJxAkshC8u7u8uru3\ntbW4t7e4trY7OvscLOAMACZWSV8Bn58pXylZIksiZiulJvUAmmACJKwCl5WUKV8AlyuxA46Oj40m\n+wCNJL4iUQeOi4uKh4YXFvQEXeAhAAJYVVQwUgVva2pua2oksgBtPBNJVgBjIl0m8ilZLgACXllX\nKYMCXFhVOb4CVlFQLr3gGGAICAUERz04ST46JKwUTUE8UkM7Tz0zVEM5V0Q7XEg8RDEk4ANBBU80\nIHpTODeERKwBPTQm6WSpIlQnFocKQlEgBQBOYAVCOQBAMqpJTSJaYAtOGIAIIB0ASjB8QngKP0A7\nOXh3d83MzdZkeSbFBM/Pz1VU6A0zAiEhISQoIkUA2iAABNnZ1dTVIlMgDiTlImkgOwLS0dIgACAX\n6RKn4AwAAjw7OyJFIAIklyACRwEBwsMkqSlQJKwpSiJgIlQm+CARAL0kqQS7urW0tCTBBbm4uFlY\nWOANVOAaADQbIktLokcHAJ0iWlBRwksrsSSsKUpLsQOQj5KQJKYDj46MjCJgCIqIh42Kin98e+Ab\nZeAJACIhK5km+AFsaU33Lf0BaGZSqiJURKkBYF4nBylcJwELX1pZYl9dWFJQQz894ApI4AgACCcg\nHExBPEk/OjBhO9QBUEFCNhxTQDZZQzVWQDIjGBINBwAUDAAXEg8gFQxmRCpjRjBGADliSCI8Ik5E\nryJdQmNHAQY2Tz0yTj0zJMQ3dSI5IkIiUUJaLgOADiARhxBgFyAaIAgFVE9Mq6qqOMsYe3p6dHR0\nhYWFjIuLf39/q6qrrKuspKOkozQkCqOkpaSlnZydnp2eIc0ofVsyAZycJjEgCwOYmJieKuIFnZ2l\npaWfJkMBnZwhmgKPjo8m2gWQj5CKiYkgCwGLiiPZBoaKiYp+fn4ycQKBgICAAgt9fHx+fX13dnV2\ndHU28QSnpqampSACAqWppzDzAKcgCCAROnIggyARAaWkIAADo6WjpDABAJ0yXCAXAaGhICA8YQVj\nYWJaWVkgAiJjCVtaWVtaWllYV1ggAAdXWF5dXEpJSSAUKQgCVVVVIAUCXFtaPFUIUVBQVlVUTUxM\nJtEAkibcEIyMk5GRi4qJjIuLhoSDiIaGNPAFhoSEgYB/IA4AgiCwAX9/KVAOe3h3h4WFeXd1gH19\nfnx8PiwYTk1MRUNDQkA/TEtLREFAPTs6TUtLRkVFR0ACGEQ7OjlMSkpDQUBAPz5BPz5LSUlKSEc/\nPTwgGgJaVlUgAgNYVFNZIIcBT00wcx9QTU1ST01UUE9OS0pPS0lLR0ZNS0pJRkRHQ0JHQ0FBPgQ9\nMSwpOymWHzIwPTk4OTY2Pjs5ODU0NzMxNjAuNzIwOjQxNS4rMCooHzgzMDguKTgsJTgvKzMqJTYn\nHz4uJD0sIk03KVA6LVE6DytbQjRdQS5aOyU/LB5KOTBkmiSdIlQiUYJdQkVCVyJmIBc+d0AOADUi\nP0I2IjkiS0SXhwFkviAOAUA8riQMQT5LREKbmZi7u7sxMf8B/xdHBVZVVdHR0SbvAtTU1CSOSUEK\n29vW1tbd3N3R0NAhvuMJJuAGAAUvLi7ExMQgLCACAM908y3oKcgJz87Pzs3OysjJyzmacqEBysky\noEuoAoqKiuAHReAdACK6Iu0VsrGwsrGxrKursK+vraurtLO0qqiorCMeAampIA40+SAOMqQAqSvo\nIyUAo1v+B6upqJ+dnB8e/w3/EdTgGwAGXVxbg39+hSJ4H39+iYeHg4CAfnt6f3x8fHl4dnNxenh3\nfXp6fHp4eHV0BXt3dnd1dCulME8wWwJSUE/gHGDAAB8KCQlWUlBVUE9VUE5STEpUTktOSUZPSUZQ\nSkhJQT1ORwtETEVCS0I9SUA8GxjnDZcCDAoJKVwRYkg3ZEYyaEgxcU00SjEfMigiJKMpiSk+JJQA\nTCJXQkggDjnBJxMgCCJXIBQAM+cDBySgIjkiSABJqVYpU0SsQBciWmS7IAsCY19dKKgCkpCR4ADF\nAiIiIiGQJukD2tna2CboB9bW1tXW1dTUKU0gCwGamv8c/xMGCK6src7OztPS0iJRIksyoQDLYl0g\nDiJLAMdZoADJIBEBysk5pjBMAMMkoeAAgOAkAAh8e3y1s7Oxr68iVwSwra2ysEJgAq6trCJOImYA\nqET0AKUlkyucJQAiWgKjoaArnwKjoKCLnAEXF/8Q/xUE4BgACGJgYIB8e4N/fiTZAoWDgiJUCIKA\nf4F+fXx6eSTQBnh1c3t5eHgmBgJxcHI8BwF1dSJgOawypDaU4Bld4AIABT06OFdSUCJREVJOS1NP\nTlBLSE1FQk5IRVFKRyAFNvoCS0M/IeUBOzb/EP8JoBcvIhteSDthRDBmSDRrSjNgRDAoHBNGNy8i\n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\nOzlCPz49OThGQkFLR0VAOzlBPjxIINsZPz5DPz08NjQrKCcoJiQjIB8bGBccHBwTEhIligIJCQmA\nmSCAAkU7NyliAkg9NyQuAEsmZQE/OCIMLgOAIAkVEhJLNihaQzZKIiogGiIYAD4gAkJUIjlkuCAI\nATVNQBcgDkACICBAJib+AD9CbyJOYA5CeCAFAU8/IB0inyJ1ADQkiySUKeYiMyIeIAgiVCALIjAA\nTTgFIBEBREAgESAIAU5FoA4gC0A1AEMgLABAIB1CZkmYJzpHNCBEIDsJQTs4goGCr6+vtSAABLS1\nj46PJIKAzuAAAAJRUFAmyCboLekkmiAmJJQBtrUiZwC1JwEiZQSdnZ0NDf8Q/0pc4AMAK4oijjnZ\nIAUAqiKRAainN0UrjQGfnik7BZ2fnZ2enTKaA5qVlJQnASbpAoOCgiJdBTc2Nj4+PSxECzg4Nz49\nPj8/Pj89PTDoAjQ0MyAFIAIGOjo6PTw8PiezCjs7Tk1Me3p5fXt7NNgHg4KBend3gH407AB4JItG\n4AVxcHJwb3s0+QR6enx4dylHPjggESLeIfkwNAsjIiIcGxsREBAdHR0h/AMDAwMXQAAAFuAExgAA\nVzYCX1taJLgFYl1cW1ZUQnILW1ldWFZaVlVXUU9Zf/9N2gFTTDv+AUg0/xT/HycFEQ4NQjs4XBYH\nRUFKPjhMPjghpiawATgtv/8hcAgHBQQ/KhtbQC4iMyTBBUw/OEs+OCJCBk1AOU1AOk0iHiJUBD84\nT0E5Il0gIyACJNAgHSAIIkIITkA4TkA5Szw1JKYgNWBBADcgRCALRLUgCAFFQSB6Ih4ATEInAUFO\nIkUgDiACQBEAPyACIB0BTkQgCGSUAEQkrCJRAj9ORiKHQBEgJkACIDtALEJ+AEwiWiTWBEE+REA9\nIb4Bs7IiIAaytLS0hoaG+QnHL/IEsbCxsrFAIAC0IksBs7IihwKysbEiZiA4ArGwsC9/IW3gGAAC\nPj09IkgFpKOjp6WmgAUwRjKbIlQBoqE0/UJhJuAFoqGgnZycS50Bk5Mh3+AZV+ACAAISERAslQKL\niIclMAKFgoI5lAV8enmHhIQgCACBf/9GwzTwAoB9fCACBX59fHd1dCSgNPAgmOADROAVADP3C2Bc\nWl9bWWJfXlxWUyJUAl1XVSACBVhTUVtUUTv4CFhST1JLSVdSUCS1IpbgD04CCAUAJvghxCPgKvQv\n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\nCzwsIj8uJTsrIT4uJCACIkUiWgA+Ik4BLCFCSAQvJT4vJSAyAUAwIAIHJj0sIj4wJzwgGgQsIz0u\nJCIzIfdCEiI8AUxJJYQiGCARQAs140JyJuxEtSI5IAtgKUAvIo0gJoARYAUkeUItIAsiM2AFQlok\nl0AyIBpgICAmoBcASCAsKYkkxCJ7RNNCgQdLSE5LSUJBQTnoCHd3d4mJiYqJiiH6EXx8fH9/f3Z1\ndXZ2doKBgYeHhybLCIuKioyLjFNTU+EE/uAFAAJYV1eAKQiNjIyHhoeDgoIkoyKlA4OBgYYgAAKE\nhIA5lAF9ff4b1wUbGxpvbGwiVCSXAnd0cyJjC2xpaHBubW1qaWhkYyurMrMFY19eYl9d5xgEBRcX\nF0xJRyJOBVVPTFlUUiJLJKMyoTQ2AEs7Ah9IRUdBPyEfHhYRDxkWFR8aGCUhICkkITApJicjIigk\nIQ0qIyAeGxoVExImIR47MSRqBi0+Khw6KyFEKAMyKj4vRGEktQA+IioELyZCMysh5QI9LSMiTgI8\nLiYgCCAgBT4vKD0tIiJaBT4uJTwtJEI/By8lPCsgOSsiIBEFOywkPCoeIkggUyAUIDIGOiohPy4i\nPCIwAiwgOyAmBCkeOSkfgBoIPCogOiofOSgdIB0LPCsfOSccPi0iOiogJtcu0gBUJIhiKoJXIfEi\nVII5YAUh8SIboAsgLCI2IiEgFyAUQjBiLQFTTIJgIBQiMwBFIEEAUCTEAEtJfSIzIDIiQiApID4g\nTYALIA4pdGAyIAtEzQhYUU5dWVdVU1MkbQVpaGiHh4grciJIBYaFhlpaWiaMP/cRKCkpODc3Ozw8\nTEtLQUFBW1tbId4aZWRkY2NjXVxcWllZU1JTSklJR0ZHRERDdHNzIjwiSyI/AoKCgilQJwcDh4aH\ngX//L0EChoWFJwoAN/8a/z+yBxAPDmlmZm9taU0CbWxuTfkDZmhlZCAColQBYWAgCANbVlUM/wX/\nJB8DDAsKDSADAQgIIgkFGBgXIB4eLgMCS0VDIAIUSENBQz47QTo4Qz88QDw6Ozc2OTY0f/9nhAM7\nR0E+JJQQSEA9RD05SEE+QzkzPTUxGRiwbQUVDQUtJSEm0SQ3ATQoQfEAPiQ9AS4mJDcJPC4lPy4k\nQjIpOSHxASkeIBEEOiohPCkh7gEjOiI2AS0jJH8IOywhOysiNygeICMCPSwhIgYFOyoeOykeIhgi\nUQU7LCI7KR8iPAs8KyE4Jxw4Jhg7KBsgSiALBjclGDooHjogDgQoGjspHCJOAjclFyAIETonGzko\nHDkmGTcmGjooHDwoGyIAIAIiAyACUT9CMEIYIAgiCSAUJENAESIbAkxIVSNZYhiCBiJRIAggFyAp\nIAIiMGTrIAgpgyAaAEQpfSzUIF8gKSALICNiTgBHIDJABUA1JQYr8EApQmAASSALAEUgKQtaVVJQ\nTEo6ODhGRkYkuAuLiouNjY2DgoNhYWH/Cf8HkAssLCxycXKIiIiKiYoiMyAIJJ0FiYmJgoKCJNMg\nNTmvHSYlJDs7Oz09PTMyMkJCQUhIR01MTFVUVFBPT05NTTd4E1dWVVdVVl5eXk1LS1taWllXWF9e\nKSgiogJSVlQkUQxLUE5OVFRTUlBQTUtKIs8FUE5NU1FQYA4ASTUCH0pIR0dFRERCQUVDQk9MS05L\nSkdDQlFPTlZSUVJOTFlWAFUykgNXUlFUPjsJTUwpKSgTExMLCfkKlAUhGxhIPzw5silfEUlCP0Y+\nOkM6NUU+OzozMBIRESWNCAoGACUfHDctKCQWBTYpIzIkGyQuAjgoHiIYIh4APSISASwkIBEFPy4j\nOCgfIBQDPSofOyRGBCgcPiwgIfQiAwU7Jxo5JhgiJBI5Jxk7KR05KBs2JBg6Jxg4JRc4IjYBJxci\nQiI2IkICOSUWIioFOicZNiUaIB0LOSQVNyQUNiQWOCQVIAIJNSQYNiITNiIUNyAOASUVIEQBNCMg\nIAYYNyMRMyAOIfEiGyHNhKmB8Tg+QA4nB0IAIjknECAaQA4k1iACQjkiFWJIIBeAIyBEICYgUCAO\nIFMgCyAgIAvABQBJKaSCTkAdQCMgL0ARIlFiXSclRLIgMiAgJLgFYFtZR0RCIl0CZWVlJHMAhSRa\nBIKCfXx9IcMAHP8F/xVzJHACdHR0JvIAhjA8AYSFIlQCfXx8hvIFhYWEcG5v/xX/HKsFQ0JBdnV0\nJNlSmAN3dnNyLeQDbXRyciACK6sAdSb1BW5tamhoIf8O/2084AMAB0tJSF5aWV9bIAIAWiACBVlW\nVFpWVSuZKUoEWFRSUUv/EP8MQAsKCgslIB5IQDxMRkMgBS3oAEd//yMLBUA5NyslI4BjERMODCwj\nHjwxK0ExJzQnHjknGyIqIdYCOycZIAsFOScYNSUZIgkFOSYXOigdIjwOOygaNiMUNyMVOCYXNSMV\n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\nFQBWYlogFCACQCYATUAmIAggHUIkAExJQQBWIEQgHSJmAVFOQAgATkJ4IrRAHSJXIWoiQkK9AkxS\nSySsRKkgOyAaIHQiriKlICkgPiJLQlEkrAFJRjZ5Ik4CTkdDRwEBSEQiTghNRUBORUFMREE2lwtK\nQDxLQz9KQT1KQTsvlSicBUhCP1dUUyIML9kSRERFICAgFhUVNTU1U1NSZmVmZDlkKSZgADVEAkBA\nQOcDOoAAAjw7OyI/IkQEYmFgYV9CSyBNJKwCXVtaJ0MBGhn/Df89wDB/AkA+PjTkJKIPSERDSURC\nSUZESkZEOTMwHfECDySjDhQRECgiHzYwLTwyLjcvKyuuCiUhHxgPBCEUCzEfJHMiISH3Js5ETykm\nKKgkT2ZfIgAgHSJFIgMiQiSUIdMgHUHTIdwBOiMh6yItAAwtnSAmIBpCSEAvIlEibAEKN0AIJtdA\nMit4ATMeJLUgFyA1ICAiYCBZIC8iuiBWIl0gfQAMJzQgFCB9Kb8sL0B6Ik4gLCBNItIgHUBZIoEn\nQDCaR6kgvyAIAjQhEUIDAU9MIe4BV1ElukIbIfdCAAJQTlZkxytpRyg6wGJ7ImwAUyJgIoQiDEJ7\nJOtCliJjIBQgBSACAFYoVCJLYDsiLSAmIAsAUSSOYAIgZTRnIBEgDiAIAFErtES+IAgASCJLJ20g\nDiB0AE4nAUSvA0ZNRUI0JARMRUJMRUAFAEoiSwBDJKYBO0hCUQY+R0A9Rj47KKIvniiiAUI6KK4A\nOiaSDk1KSU1NTD08PCYmJgkJCTVNC0VFRV1dXWZlZmNiYiIyBWJhYkVERP8D/wE/gAACKSkpNS8B\nYGAzPARZXFtbXiAzAVxcIAIiVwAq/wv/hBAFEA8PPTk3MEICTEhHIk4pUwpEPz1HQD46ODYTEb//\nAIsuKgUVEhAmIiArogI8NDAt6wwtJB8oHxgfEwgrGww1KMYAISsJIe4tTCHWIAIDCTcgBiQcKwlg\nDiIMQAIm4CAaZoAh4kH9ICMknSAOYCkiAyAmIEcgHS2pIBcicgANJFgiOSIkIkJALycNRQwiVyUM\nIDIykiKxAA+AgyTEJ3kAN0IhABAi3iAmATkjIm8ADyK3MLIBOiQpvCApABAyoQIyHxEwqQA2QlEw\nzS6fABEnuzUUBjokETgjFFMiLQBPIgkATCHuYAIiEiSpAE4gCyH0AFRkXkALAE5gHQFQTibXIfSA\n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\nCGmZIAoAJzmvAiMiISlZAyMiIioiggEkIiTmDickIiYjISgkISciICgkIjT5CCciHykkISkiIDdX\nCy0lISsiHS0kIC4mISAFFzEmITMoIjAkHTAjHTAlHjMmHzMlHTQoIT5cJB8LOCkhNykgNiceNykh\nIksh/QQ5KiI5KyIGAB8gCwA4JpUHLCQ5KyQ4KiIgKQI5KiBACCA1ASohKNgDOiwlOUabACUgCCIY\nATosRqRgEQAkIAsgOCRMIjkiFQg8Lyc9LSU9LydgDgMpPS8oYjMiPwApIkILQDMrQjIpPjIrQTIq\nIjMgDgJAMy0gBSALA0IzKkAgFwQzKkEzLCAOIkIAQmACAEAiSw00LUM1LUI1LkE0LkI1LSJOJJoB\nS0tEQ0HiYAUgESG+IfoktwFPTkIDIAgiJyHoAVNSK5IkeUlrIBEATiIMIClCh0Aa4AARIBcr9SAv\nAE1CmCAOIAogA0SvIHEgBCAOIBogBSBNAE0sB0AjQAAgGiAXIswgAGAQQlogFCAPIGUgBSAaAEsg\nriABIAUDTExJSUcoIAAgCCJgQl0GREVGRkVCQiJpAEUiZoTKYmkAPiALAD4iaSAAATs8ImUr6iAA\nAjc3NyAGJM4DNTQ1MsAAAzEwMDNADAAxIn4poQAvLlgGLSwvLi4wLyACAy8vLS1HTQMrKi0qTg8M\nLispLywrLSknLyspLCAFECooLiknMConLSckMSonMCkmIAsdMSklMisnMiolMyokNCkjNi0oNCkk\nOTArNywmNysjIAUOOSwlOCwmOi4nOCskPC8oIgYiTgA7JD0CLiY5IiomfSAUAS4nJDcgFAI7LSYi\nGyARADlI0iALBCg+MSo7Ii0KLyg9MSo9MCo8MCkh9yAsIBcCQDMsIAVCPwAxQA4BPjAiLSAjAyk9\nMisgFwVBNCxANC5AI0JCRG0iFSAUIicAQH//EYYiVCARBUA1L0M2MEAXATUvQjxiPyALA0Q3MENA\nAgIxQjYgIAkvQjYvQTYxQzcwAJ06Cj1shkM+nzsuPggAAAAAAAAAAD5AA3JnYgAAAD8AAAA/AAAA\nPwp0ZXh0dXJlbWFwAAAAAAAAAPA/AAAAAAAA8D8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAQAA\nAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIA/AAAAAAAAAAAAAAAAAPA/AAAAAAAA8D8A\n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\nPnsUrkfheoQ/AAAA\n'
    # save it do working directory
    loc, _ = os.path.split(os.path.realpath(__file__))
    p = os.path.join(loc, "checker.mxm")
    with open(p, "wb") as bf:
        b = base64.decodebytes(checker)
        d = bf.write(b)
    # load it
    t = s.readMaterial(p)
    t.setName(n)
    m = s.addMaterial(t)
    Materials.db.append((n, m, True))
    # and erase it
    os.remove(p)
    
    return m


def material(path, s, embed, ):
    r = None
    for p, m, e in Materials.db:
        if(p == path):
            r = m
    if(r is None):
        t = s.readMaterial(path)
        r = s.addMaterial(t)
        Materials.db.append((path, r, embed))
        if(embed is False):
            # set as external
            r.setReference(1, path)
    return r


def texture(d, s):
    t = CtextureMap()
    t.setPath(d['path'])
    
    t.uvwChannelID = d['channel']
    
    t.brightness = d['brightness']
    t.contrast = d['contrast']
    t.saturation = d['saturation']
    t.hue = d['hue']
    
    t.useGlobalMap = d['use_override_map']
    t.useAbsoluteUnits = d['tile_method_units']
    
    t.uIsTiled = d['tile_method_type'][0]
    t.vIsTiled = d['tile_method_type'][1]
    
    t.uIsMirrored = d['mirror'][0]
    t.vIsMirrored = d['mirror'][1]
    
    vec = Cvector2D()
    vec.assign(d['offset'][0], d['offset'][1])
    t.offset = vec
    t.rotation = d['rotation']
    t.invert = d['invert']
    t.useAlpha = d['alpha_only']
    if(d['interpolation']):
        t.typeInterpolation = 1
    else:
        t.typeInterpolation = 0
    t.clampMin = d['rgb_clamp'][0]
    t.clampMax = d['rgb_clamp'][1]
    
    vec = Cvector2D()
    vec.assign(d['repeat'][0], d['repeat'][1])
    t.scale = vec
    
    # t.cosA
    # t.doGammaCorrection
    # t.normalMappingFlipGreen
    # t.normalMappingFlipRed
    # t.normalMappingFullRangeBlue
    # t.sinA
    # t.theTextureExtensions
    
    return t


def base_and_pivot(o, d):
    b = d['base']
    p = d['pivot']
    bb = Cbase()
    bb.origin = Cvector(*b[0])
    bb.xAxis = Cvector(*b[1])
    bb.yAxis = Cvector(*b[2])
    bb.zAxis = Cvector(*b[3])
    pp = Cbase()
    pp.origin = Cvector(*p[0])
    pp.xAxis = Cvector(*p[1])
    pp.yAxis = Cvector(*p[2])
    pp.zAxis = Cvector(*p[3])
    o.setBaseAndPivot(bb, pp)


def object_props(o, d):
    if(d['hidden_camera']):
        o.setHideToCamera(True)
    if(d['hidden_camera_in_shadow_channel']):
        o.setHideToCameraInShadowsPass(True)
    if(d['hidden_global_illumination']):
        o.setHideToGI(True)
    if(d['hidden_reflections_refractions']):
        o.setHideToReflectionsRefractions(True)
    if(d['hidden_zclip_planes']):
        o.excludeOfCutPlanes(True)
    if(d['opacity'] != 100.0):
        o.setOpacity(d['opacity'])
    if(d['hide']):
        o.setHide(d['hide'])
    c = Crgb()
    cc = [c / 255 for c in d['object_id']]
    c.assign(*cc)
    o.setColorID(c)


def camera(d, s):
    c = s.addCamera(d['name'], d['number_of_steps'], d['shutter'], d['film_width'], d['film_height'], d['iso'],
                    d['aperture'], d['diaphragm_angle'], d['diaphragm_blades'], d['frame_rate'],
                    d['resolution_x'], d['resolution_y'], d['pixel_aspect'], d['lens'], )
    
    # shutter_angle !!!!!!!!!!!!!!!!!!!!
    
    # will crash, just set it without asking for the list
    # l, _ = c.getCameraResponsePresetsList()
    # if(d['response'] in l):
    #     c.setCameraResponsePreset(d['response'])
    c.setCameraResponsePreset(d['response'])
    
    if(d['custom_bokeh']):
        c.setCustomBokeh(d['bokeh_ratio'], d['bokeh_angle'], True)
    
    o = Cvector()
    o.assign(*d['origin'])
    f = Cvector()
    f.assign(*d['focal_point'])
    u = Cvector()
    u.assign(*d['up'])
    # hard coded: (step: 0, _, _, _, _, _, stepTime: 1, focalLengthNeedCorrection: 1, )
    c.setStep(0, o, f, u, d['focal_length'], d['fstop'], 1, 1, )
    if(d['lens'] == 3):
        c.setFishLensProperties(d['fov'])
    if(d['lens'] == 4):
        c.setSphericalLensProperties(d['azimuth'])
    if(d['lens'] == 5):
        c.setCylindricalLensProperties(d['angle'])
    # c.setShutter(d['shutter'])
    c.setCutPlanes(d['set_cut_planes'][0], d['set_cut_planes'][1], d['set_cut_planes'][2], )
    c.setShiftLens(d['set_shift_lens'][0], d['set_shift_lens'][1], )
    if(d['screen_region'] != 'NONE'):
        r = d['screen_region_xywh']
        c.setScreenRegion(r[0], r[1], r[2], r[3], d['screen_region'])
    if(d['active']):
        c.setActive()
    return c


def empty(d, s):
    o = s.createMesh(d['name'], 0, 0, 0, 0,)
    base_and_pivot(o, d)
    object_props(o, d)
    return o


def mesh(d, s):
    r = MXSBinMeshReader(d['mesh_data_path'])
    m = r.data
    o = s.createMesh(d['name'], d['num_vertexes'], d['num_normals'], d['num_triangles'], d['num_positions_per_vertex'], )
    for i in m['channel_uvw']:
        o.addChannelUVW(i)
    for i in range(len(m['v_setVertex'])):
        mv = Cvector()
        v = m['v_setVertex'][i]
        mv.assign(v[2][0], v[2][1], v[2][2])
        o.setVertex(v[0], v[1], mv)
        n = m['v_setNormal'][i]
        mn = Cvector()
        mn.assign(n[2][0], n[2][1], n[2][2])
        o.setNormal(n[0], n[1], mn)
    for n in m['f_setNormal']:
        mn = Cvector()
        mn.assign(n[2][0], n[2][1], n[2][2])
        o.setNormal(n[0], n[1], mn)
    for t in m['f_setTriangle']:
        o.setTriangle(t[0], t[1][0], t[1][1], t[1][2], t[2][0], t[2][1], t[2][2], )
    
    if(d['num_materials'] > 1):
        # multi material
        mats = []
        for mi in range(d['num_materials']):
            if(d['materials'][mi][1] == ""):
                # multi material, but none assigned.. to keep triangle group, create and assign blank material
                mat = material_placeholder(s)
            else:
                mat = material(d['materials'][mi][1], s, d['materials'][mi][0])
            mats.append(mat)
        for t, ma in m['f_setTriangleMaterial']:
            o.setTriangleMaterial(t, mats[ma])
    elif(d['num_materials'] == 1):
        # # single material
        # if(d['materials'][0][1] == ""):
        #     mat = material_placeholder(s)
        # else:
        #     mat = material(d['materials'][0][1], s, d['materials'][0][0])
        if(d['materials'][0][1] == ""):
            mat = None
        else:
            mat = material(d['materials'][0][1], s, d['materials'][0][0])
        # # this is causing error: Object [...] is not an emitter but has triangles with an emitter material applied to it
        # # details here: http://support.nextlimit.com/display/knfaq/Render+error+messages
        # # what is probably happening is, if setTriangleMaterial is used even with the same material on all triangles
        # # somewhere it is flagged as multi material mesh..
        # for t, ma in m['f_setTriangleMaterial']:
        #     o.setTriangleMaterial(t, mat)
        # # fix
        if(mat is not None):
            o.setMaterial(mat)
    else:
        # no material
        pass
    
    if(len(d['backface_material']) > 0):
        if(d['backface_material'][0] != ""):
            bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
            o.setBackfaceMaterial(bm)
    
    for t in m['f_setTriangleUVW']:
        o.setTriangleUVW(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], )
    base_and_pivot(o, d)
    object_props(o, d)
    
    if(d['subdiv_ext'] is not None):
        # 0: ('Subdivision Level', [2], 0, 99, '1 UINT', 4, 1, True)
        # 1: ('Subdivision Scheme', [0], 0, 2, '1 UINT', 4, 1, True)
        # 2: ('Interpolation', [2], 0, 3, '1 UINT', 4, 1, True)
        # 3: ('Crease', [0.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 4: ('Smooth Angle', [90.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 5: ('EXTENSION_NAME', 'SubdivisionModifier', '', '', '5 STRING', 1, 20, True)
        # 6: ('EXTENSION_VERSION', [1], 0, 1000000, '1 UINT', 4, 1, True)
        # 7: ('EXTENSION_ISENABLED', [1], 0, 1, '0 UCHAR', 1, 1, True)
        m = CextensionManager.instance()
        m.loadAllExtensions()
        e = m.createDefaultGeometryModifierExtension('SubdivisionModifier')
        p = e.getExtensionData()
        e = d['subdiv_ext']
        p.setUInt('Subdivision Level', e[0])
        p.setUInt('Subdivision Scheme', e[1])
        p.setUInt('Interpolation', e[2])
        p.setFloat('Crease', e[3])
        p.setFloat('Smooth Angle', e[4])
        o.applyGeometryModifierExtension(p)
    
    if(d['scatter_ext'] is not None):
        # 0: ('Object', '', '', '', '5 STRING', 1, 1, True)
        # 1: ('Inherit ObjectID', [0], 0, 1, '0 UCHAR', 1, 1, True)
        # 2: ('Density', [100.0], 9.999999747378752e-05, 10000000000.0, '3 FLOAT', 4, 1, True)
        # 3: ('Density Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 4: ('Scale X', [1.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 5: ('Scale Y', [1.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 6: ('Scale Z', [1.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 7: ('Scale Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 8: ('Scale X Variation', [20.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 9: ('Scale Y Variation', [20.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 10: ('Scale Z Variation', [20.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 11: ('Rotation X', [0.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 12: ('Rotation Y', [0.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 13: ('Rotation Z', [0.0], 0.0, 360.0, '3 FLOAT', 4, 1, True)
        # 14: ('Rotation Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 15: ('Rotation X Variation', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 16: ('Rotation Y Variation', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 17: ('Rotation Z Variation', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 18: ('Direction Type', [0], 0, 1, '1 UINT', 4, 1, True)
        # 19: ('Initial Angle', [90.0], 0.0, 90.0, '3 FLOAT', 4, 1, True)
        # 20: ('Initial Angle Variation', [0.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 21: ('Initial Angle Map', <pymaxwell.MXparamList; proxy of <Swig Object of type 'MXparamList *' at 0x10107c390> >, 0, 0, '10 MXPARAMLIST', 0, 1, True)
        # 22: ('Seed', [0], 0, 16383, '1 UINT', 4, 1, True)
        # 23: ('Enable LOD', [0], 0, 1, '0 UCHAR', 1, 1, True)
        # 24: ('LOD Min Distance', [10.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 25: ('LOD Max Distance', [50.0], 0.0, 100000.0, '3 FLOAT', 4, 1, True)
        # 26: ('LOD Max Distance Density', [10.0], 0.0, 100.0, '3 FLOAT', 4, 1, True)
        # 27: ('Display Percent', [10], 0, 100, '1 UINT', 4, 1, True)
        # 28: ('Display Max. Instances', [1000], 0, 100000, '1 UINT', 4, 1, True)
        # 29: ('TRIANGLES_WITH_CLONES', [0], 0, 0, '8 BYTEARRAY', 1, 1, True)
        # 30: ('EXTENSION_NAME', 'MaxwellScatter', '', '', '5 STRING', 1, 15, True)
        # 31: ('EXTENSION_VERSION', [1], 0, 1000000, '1 UINT', 4, 1, True)
        # 32: ('EXTENSION_ISENABLED', [1], 0, 1, '0 UCHAR', 1, 1, True)
        
        def texture_data_to_mxparams(d, mp):
            if(d is None):
                return
            # mp.setString('CtextureMap.FileName', d['path'])
            # hey, seriously.. WTF?
            mp.setString('CtextureMap.FileName', ''.join(d['path']))
            mp.setByte('CtextureMap.uvwChannel', d['channel'])
            mp.setByte('CtextureMap.uIsTiled', d['tile_method_type'][0])
            mp.setByte('CtextureMap.vIsTiled', d['tile_method_type'][1])
            mp.setByte('CtextureMap.uIsMirrored', d['mirror'][0])
            mp.setByte('CtextureMap.vIsMirrored', d['mirror'][1])
            mp.setFloat('CtextureMap.scale.x', d['repeat'][0])
            mp.setFloat('CtextureMap.scale.y', d['repeat'][1])
            mp.setFloat('CtextureMap.offset.x', d['offset'][0])
            mp.setFloat('CtextureMap.offset.y', d['offset'][1])
            mp.setFloat('CtextureMap.rotation', d['rotation'])
            mp.setByte('CtextureMap.invert', d['invert'])
            mp.setByte('CtextureMap.useAbsoluteUnits', d['tile_method_units'])
            mp.setByte('CtextureMap.useAlpha', d['alpha_only'])
            mp.setByte('CtextureMap.typeInterpolation', d['interpolation'])
            mp.setFloat('CtextureMap.saturation', d['saturation'])
            mp.setFloat('CtextureMap.contrast', d['contrast'])
            mp.setFloat('CtextureMap.brightness', d['brightness'])
            mp.setFloat('CtextureMap.hue', d['hue'])
            mp.setFloat('CtextureMap.clampMin', d['rgb_clamp'][0])
            mp.setFloat('CtextureMap.clampMax', d['rgb_clamp'][1])
            mp.setFloat('CtextureMap.useGlobalMap', d['use_override_map'])
        
        m = CextensionManager.instance()
        m.loadAllExtensions()
        e = m.createDefaultGeometryModifierExtension('MaxwellScatter')
        p = e.getExtensionData()
        e = d['scatter_ext']
        
        p.setString('Object', e['scatter_object'])
        p.setByte('Inherit ObjectID', e['inherit_objectid'])
        p.setFloat('Density', e['density'])
        texture_data_to_mxparams(e['density_map'], p.getByName('Density Map')[0])
        p.setUInt('Seed', e['seed'])
        p.setFloat('Scale X', e['scale_x'])
        p.setFloat('Scale Y', e['scale_y'])
        p.setFloat('Scale Z', e['scale_z'])
        texture_data_to_mxparams(e['scale_map'], p.getByName('Scale Map')[0])
        p.setFloat('Scale X Variation', e['scale_variation_x'])
        p.setFloat('Scale Y Variation', e['scale_variation_y'])
        p.setFloat('Scale Z Variation', e['scale_variation_z'])
        p.setFloat('Rotation X', e['rotation_x'])
        p.setFloat('Rotation Y', e['rotation_y'])
        p.setFloat('Rotation Z', e['rotation_z'])
        texture_data_to_mxparams(e['rotation_map'], p.getByName('Rotation Map')[0])
        p.setFloat('Rotation X Variation', e['rotation_variation_x'])
        p.setFloat('Rotation Y Variation', e['rotation_variation_y'])
        p.setFloat('Rotation Z Variation', e['rotation_variation_z'])
        p.setUInt('Direction Type', e['rotation_direction'])
        p.setByte('Enable LOD', e['lod'])
        p.setFloat('LOD Min Distance', e['lod_min_distance'])
        p.setFloat('LOD Max Distance', e['lod_max_distance'])
        p.setFloat('LOD Max Distance Density', e['lod_max_distance_density'])
        p.setUInt('Display Percent', e['display_percent'])
        p.setUInt('Display Max. Blades', e['display_max_blades'])
        o.applyGeometryModifierExtension(p)
    
    return o


def instance(d, s):
    bo = s.getObject(d['instanced'])
    o = s.createInstancement(d['name'], bo)
    if(d['num_materials'] == 1):
        # instance with different material is possible
        m = material(d['materials'][0][1], s, d['materials'][0][0])
        o.setMaterial(m)
    else:
        # multi material instances cannot be changed (i think)
        # and just skip instances without material
        pass
    if(len(d['backface_material']) > 0):
        if(d['backface_material'][0] != ""):
            bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
            o.setBackfaceMaterial(bm)
    
    base_and_pivot(o, d)
    object_props(o, d)
    return o


def scene(d, s):
    s.setRenderParameter('ENGINE', d["scene_quality"])
    s.setRenderParameter('NUM THREADS', d["scene_cpu_threads"])
    s.setRenderParameter('STOP TIME', d["scene_time"] * 60)
    s.setRenderParameter('SAMPLING LEVEL', d["scene_sampling_level"])
    s.setRenderParameter('USE MULTILIGHT', d["scene_multilight"])
    s.setRenderParameter('SAVE LIGHTS IN SEPARATE FILES', d["scene_multilight_type"])
    s.setRenderParameter('MXI FULLNAME', d["output_mxi"])
    s.setRenderParameter('DO NOT SAVE MXI FILE', not d["output_mxi_enabled"])
    s.setRenderParameter('DO NOT SAVE IMAGE FILE', not d["output_image_enabled"])
    # s.setRenderParameter('RENAME AFTER SAVING', d[""])
    s.setRenderParameter('COPY MXI AFTER RENDER', d["output_mxi"])
    s.setRenderParameter('COPY IMAGE AFTER RENDER', d["output_image"])
    # s.setRenderParameter('REMOVE FILES AFTER COPY', d[""])
    s.setRenderParameter('DO MOTION BLUR', d["globals_motion_blur"])
    s.setRenderParameter('DO DISPLACEMENT', d["globals_diplacement"])
    s.setRenderParameter('DO DISPERSION', d["globals_dispersion"])
    
    if(d['channels_render_type'] == 2):
        s.setRenderParameter('DO DIFFUSE LAYER', 0)
        s.setRenderParameter('DO REFLECTION LAYER', 1)
    elif(d['channels_render_type'] == 1):
        s.setRenderParameter('DO DIFFUSE LAYER', 1)
        s.setRenderParameter('DO REFLECTION LAYER', 0)
    else:
        s.setRenderParameter('DO DIFFUSE LAYER', 1)
        s.setRenderParameter('DO REFLECTION LAYER', 1)
    
    v = d['illum_caustics_illumination']
    if(v == 3):
        s.setRenderParameter('DO DIRECT LAYER', 0)
        s.setRenderParameter('DO INDIRECT LAYER', 0)
    elif(v == 2):
        s.setRenderParameter('DO DIRECT LAYER', 0)
        s.setRenderParameter('DO INDIRECT LAYER', 1)
    elif(v == 1):
        s.setRenderParameter('DO DIRECT LAYER', 1)
        s.setRenderParameter('DO INDIRECT LAYER', 0)
    else:
        s.setRenderParameter('DO DIRECT LAYER', 1)
        s.setRenderParameter('DO INDIRECT LAYER', 1)
    
    v = d['illum_caustics_refl_caustics']
    if(v == 3):
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 0)
    elif(v == 2):
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 1)
    elif(v == 1):
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 0)
    else:
        s.setRenderParameter('DO DIRECT REFLECTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFLECTION CAUSTIC LAYER', 1)
    
    v = d['illum_caustics_refr_caustics']
    if(v == 3):
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 0)
    elif(v == 2):
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 0)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 1)
    elif(v == 1):
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 0)
    else:
        s.setRenderParameter('DO DIRECT REFRACTION CAUSTIC LAYER', 1)
        s.setRenderParameter('DO INDIRECT REFRACTION CAUSTIC LAYER', 1)
    
    h, t = os.path.split(d["output_mxi"])
    n, e = os.path.splitext(t)
    base_path = os.path.join(h, n)
    
    def get_ext_depth(t, e=None):
        if(e is not None):
            t = "{}{}".format(e[1:].upper(), int(t[3:]))
        
        if(t == 'PNG8'):
            return ('.png', 8)
        elif(t == 'PNG16'):
            return ('.png', 16)
        elif(t == 'TGA'):
            return ('.tga', 8)
        elif(t == 'TIF8'):
            return ('.tif', 8)
        elif(t == 'TIF16'):
            return ('.tif', 16)
        elif(t == 'TIF32'):
            return ('.tif', 32)
        elif(t == 'EXR16'):
            return ('.exr', 16)
        elif(t == 'EXR32'):
            return ('.exr', 32)
        elif(t == 'EXR_DEEP'):
            return ('.exr', 32)
        elif(t == 'JPG'):
            return ('.jpg', 8)
        elif(t == 'JP2'):
            return ('.jp2', 8)
        elif(t == 'HDR'):
            return ('.hdr', 32)
        elif(t == 'DTEX'):
            return ('.dtex', 32)
        else:
            return ('.tif', 8)
    
    _, depth = get_ext_depth(d["output_depth"], os.path.splitext(os.path.split(d["output_image"])[1])[1])
    s.setPath('RENDER', d["output_image"], depth)
    
    e, depth = get_ext_depth(d["channels_alpha_file"])
    s.setPath('ALPHA', "{}_alpha.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_shadow_file"])
    s.setPath('SHADOW', "{}_shadow.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_object_id_file"])
    s.setPath('OBJECT', "{}_object_id.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_material_id_file"])
    s.setPath('MATERIAL', "{}_material_id.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_motion_vector_file"])
    s.setPath('MOTION', "{}_motion_vector.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_z_buffer_file"])
    s.setPath('Z', "{}_z_buffer.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_roughness_file"])
    s.setPath('ROUGHNESS', "{}_roughness.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_fresnel_file"])
    s.setPath('FRESNEL', "{}_fresnel.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_normals_file"])
    s.setPath('NORMALS', "{}_normals.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_position_file"])
    s.setPath('POSITION', "{}_position.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_deep_file"])
    s.setPath('DEEP', "{}_deep.{}".format(base_path, e), depth)
    e, depth = get_ext_depth(d["channels_uv_file"])
    s.setPath('UV', "{}_uv.{}".format(base_path, e), depth)
    
    e, depth = get_ext_depth(d["channels_custom_alpha_file"])
    s.setPath('ALPHA_CUSTOM', "{}_custom_alpha.{}".format(base_path, e), depth)
    
    s.setRenderParameter('DO RENDER CHANNEL', int(d["channels_render"]))
    s.setRenderParameter('DO ALPHA CHANNEL', int(d["channels_alpha"]))
    s.setRenderParameter('OPAQUE ALPHA', int(d["channels_alpha_opaque"]))
    s.setRenderParameter('EMBED CHANNELS', d["channels_output_mode"])
    s.setRenderParameter('DO IDOBJECT CHANNEL', int(d["channels_object_id"]))
    s.setRenderParameter('DO IDMATERIAL CHANNEL', int(d["channels_material_id"]))
    s.setRenderParameter('DO SHADOW PASS CHANNEL', int(d["channels_shadow"]))
    s.setRenderParameter('DO MOTION CHANNEL', int(d["channels_motion_vector"]))
    s.setRenderParameter('DO ROUGHNESS CHANNEL', int(d["channels_roughness"]))
    s.setRenderParameter('DO FRESNEL CHANNEL', int(d["channels_fresnel"]))
    s.setRenderParameter('DO NORMALS CHANNEL', int(d["channels_normals"]))
    s.setRenderParameter('NORMALS CHANNEL SPACE', d["channels_normals_space"])
    s.setRenderParameter('POSITION CHANNEL SPACE', d["channels_position_space"])
    s.setRenderParameter('DO POSITION CHANNEL', int(d["channels_position"]))
    s.setRenderParameter('DO ZBUFFER CHANNEL', int(d["channels_z_buffer"]))
    s.setRenderParameter('ZBUFFER RANGE', (d["channels_z_buffer_near"], d["channels_z_buffer_far"]))
    s.setRenderParameter('DO DEEP CHANNEL', int(d["channels_deep"]))
    s.setRenderParameter('DEEP CHANNEL TYPE', d["channels_deep_type"])
    s.setRenderParameter('DEEP MIN DISTANCE', d["channels_deep_min_dist"])
    s.setRenderParameter('DEEP MAX SAMPLES', d["channels_deep_max_samples"])
    s.setRenderParameter('DO UV CHANNEL', int(d["channels_uv"]))
    
    # s.setRenderParameter('MOTION CHANNEL TYPE', ?)
    s.setRenderParameter('DO ALPHA CUSTOM CHANNEL', int(d["channels_custom_alpha"]))
    
    s.setRenderParameter('DO DEVIGNETTING', d["simulens_devignetting"])
    s.setRenderParameter('DEVIGNETTING', d["simulens_devignetting_value"])
    s.setRenderParameter('DO SCATTERING_LENS', d["simulens_scattering"])
    s.setRenderParameter('SCATTERING_LENS', d["simulens_scattering_value"])
    
    s.setRenderParameter('DO SHARPNESS', d["tone_sharpness"])
    s.setRenderParameter('SHARPNESS', d["tone_sharpness_value"])
    s.setToneMapping(d["tone_gamma"], d["tone_burn"])
    
    if(d["materials_override"]):
        s.setOverrideMaterial(True)
    if(d["materials_override_path"] != ""):
        s.setOverrideMaterial(d["materials_override_path"])
    
    if(d["simulens_diffraction"]):
        s.enableDiffraction()
        s.setDiffraction(d["simulens_diffraction_value"], d["simulens_frequency"], d["simulens_aperture_map"], d["simulens_obstacle_map"])
    
    s.setColorSpace(d["tone_color_space"])
    s.setWhitePoint(d["tone_whitepoint"], d["tone_tint"])
    
    if(d["materials_search_path"] != ""):
        s.addSearchingPath(d["materials_search_path"])


def environment(d, s):
    env = s.getEnvironment()
    if(d["env_type"] == 'PHYSICAL_SKY'):
        env.setActiveSky(d["sky_type"])
        if(d["sky_type"] == 'PHYSICAL'):
            if(not d["sky_use_preset"]):
                env.setPhysicalSkyAtmosphere(d["sky_intensity"], d["sky_ozone"], d["sky_water"], d["sky_turbidity_coeff"], d["sky_wavelength_exp"], d["sky_reflectance"], d["sky_asymmetry"], d["sky_planet_refl"], )
            else:
                env.loadSkyFromPreset(d["sky_preset"])
            
            sc = Crgb()
            scc = [c / 255 for c in d['sun_color']]
            sc.assign(*scc)
            if(d["sun_type"] == 'PHYSICAL'):
                env.setSunProperties(SUN_PHYSICAL, d["sun_temp"], d["sun_power"], d["sun_radius_factor"], sc)
            elif(d["sun_type"] == 'CUSTOM'):
                env.setSunProperties(SUN_CONSTANT, d["sun_temp"], d["sun_power"], d["sun_radius_factor"], sc)
            elif(d["sun_type"] == 'DISABLED'):
                env.setSunProperties(SUN_DISABLED, d["sun_temp"], d["sun_power"], d["sun_radius_factor"], sc)
            if(d["sun_location_type"] == 'LATLONG'):
                env.setSunPositionType(0)
                l = d["sun_date"].split(".")
                date = datetime.date(int(l[2]), int(l[1]), int(l[0]))
                day = int(date.timetuple().tm_yday)
                l = d["sun_time"].split(":")
                hour = int(l[0])
                minute = int(l[1])
                time = hour + (minute / 60)
                env.setSunLongitudeAndLatitude(d["sun_latlong_lon"], d["sun_latlong_lat"], d["sun_latlong_gmt"], day, time)
                env.setSunRotation(d["sun_latlong_ground_rotation"])
            elif(d["sun_location_type"] == 'ANGLES'):
                env.setSunPositionType(1)
                env.setSunAngles(d["sun_angles_zenith"], d["sun_angles_azimuth"])
            elif(d["sun_location_type"] == 'DIRECTION'):
                env.setSunPositionType(2)
                env.setSunDirection(Cvector(d["sun_dir_x"], d["sun_dir_y"], d["sun_dir_z"]))
        if(d["sky_type"] == 'CONSTANT'):
            hc = Crgb()
            hcc = [c / 255 for c in d['dome_horizon']]
            hc.assign(*hcc)
            zc = Crgb()
            zcc = [c / 255 for c in d['dome_zenith']]
            zc.assign(*zcc)
            env.setSkyConstant(d["dome_intensity"], hc, zc, d['dome_mid_point'])
    elif(d["env_type"] == 'IMAGE_BASED'):
        env.enableEnvironment(True)
        
        def state(s):
            if(s == 'HDR_IMAGE'):
                return 1
            if(s == 'SAME_AS_BG'):
                return 2
            return 0
        
        env.setEnvironmentWeight(d["ibl_intensity"])
        env.setEnvironmentLayer(IBL_LAYER_BACKGROUND,
                                d["ibl_bg_map"],
                                state("ibl_bg_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_bg_intensity"],
                                d["ibl_bg_scale_x"],
                                d["ibl_bg_scale_y"],
                                d["ibl_bg_offset_x"],
                                d["ibl_bg_offset_y"], )
        env.setEnvironmentLayer(IBL_LAYER_REFLECTION,
                                d["ibl_refl_map"],
                                state("ibl_refl_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_refl_intensity"],
                                d["ibl_refl_scale_x"],
                                d["ibl_refl_scale_y"],
                                d["ibl_refl_offset_x"],
                                d["ibl_refl_offset_y"], )
        env.setEnvironmentLayer(IBL_LAYER_REFRACTION,
                                d["ibl_refr_map"],
                                state("ibl_refr_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_refr_intensity"],
                                d["ibl_refr_scale_x"],
                                d["ibl_refr_scale_y"],
                                d["ibl_refr_offset_x"],
                                d["ibl_refr_offset_y"], )
        env.setEnvironmentLayer(IBL_LAYER_ILLUMINATION,
                                d["ibl_illum_map"],
                                state("ibl_illum_type"),
                                not d["ibl_screen_mapping"],
                                not d["ibl_interpolation"],
                                d["ibl_illum_intensity"],
                                d["ibl_illum_scale_x"],
                                d["ibl_illum_scale_y"],
                                d["ibl_illum_offset_x"],
                                d["ibl_illum_offset_y"], )
    else:
        env.setActiveSky('')


def custom_alphas(d, s):
    ags = d['channels_custom_alpha_groups']
    for a in ags:
        s.createCustomAlphaChannel(a['name'], a['opaque'])
        for n in a['objects']:
            o = s.getObject(n)
            o.addToCustomAlpha(a['name'])


def particles(d, s):
    mgr = CextensionManager.instance()
    mgr.loadAllExtensions()
    
    ext = mgr.createDefaultGeometryProceduralExtension('MaxwellParticles')
    params = ext.getExtensionData()
    
    params.setString('FileName', d['bin_filename'])
    params.setFloat('Radius Factor', d['bin_radius_multiplier'])
    params.setFloat('MB Factor', d['bin_motion_blur_multiplier'])
    params.setFloat('Shutter 1/', d['bin_shutter_speed'])
    params.setFloat('Load particles %', d['bin_load_particles'])
    params.setUInt('Axis', d['bin_axis_system'])
    params.setInt('Frame#', d['bin_frame_number'])
    params.setFloat('fps', d['bin_fps'])
    params.setInt('Create N particles per particle', d['bin_extra_create_np_pp'])
    params.setFloat('Extra particles dispersion', d['bin_extra_dispersion'])
    params.setFloat('Extra particles deformation', d['bin_extra_deformation'])
    params.setByte('Load particle Force', d['bin_load_force'])
    params.setByte('Load particle Vorticity', d['bin_load_vorticity'])
    params.setByte('Load particle Normal', d['bin_load_normal'])
    params.setByte('Load particle neighbors no.', d['bin_load_neighbors_num'])
    params.setByte('Load particle UV', d['bin_load_uv'])
    params.setByte('Load particle Age', d['bin_load_age'])
    params.setByte('Load particle Isolation Time', d['bin_load_isolation_time'])
    params.setByte('Load particle Viscosity', d['bin_load_viscosity'])
    params.setByte('Load particle Density', d['bin_load_density'])
    params.setByte('Load particle Pressure', d['bin_load_pressure'])
    params.setByte('Load particle Mass', d['bin_load_mass'])
    params.setByte('Load particle Temperature', d['bin_load_temperature'])
    params.setByte('Load particle ID', d['bin_load_id'])
    params.setFloat('Min Force', d['bin_min_force'])
    params.setFloat('Max Force', d['bin_max_force'])
    params.setFloat('Min Vorticity', d['bin_min_vorticity'])
    params.setFloat('Max Vorticity', d['bin_max_vorticity'])
    params.setInt('Min Nneighbors', d['bin_min_nneighbors'])
    params.setInt('Max Nneighbors', d['bin_max_nneighbors'])
    params.setFloat('Min Age', d['bin_min_age'])
    params.setFloat('Max Age', d['bin_max_age'])
    params.setFloat('Min Isolation Time', d['bin_min_isolation_time'])
    params.setFloat('Max Isolation Time', d['bin_max_isolation_time'])
    params.setFloat('Min Viscosity', d['bin_min_viscosity'])
    params.setFloat('Max Viscosity', d['bin_max_viscosity'])
    params.setFloat('Min Density', d['bin_min_density'])
    params.setFloat('Max Density', d['bin_max_density'])
    params.setFloat('Min Pressure', d['bin_min_pressure'])
    params.setFloat('Max Pressure', d['bin_max_pressure'])
    params.setFloat('Min Mass', d['bin_min_mass'])
    params.setFloat('Max Mass', d['bin_max_mass'])
    params.setFloat('Min Temperature', d['bin_min_temperature'])
    params.setFloat('Max Temperature', d['bin_max_temperature'])
    params.setFloat('Min Velocity', d['bin_min_velocity'])
    params.setFloat('Max Velocity', d['bin_max_velocity'])
    
    o = s.createGeometryProceduralObject(d['name'], params)
    
    # mat = material(d['material'], s, d['material_embed'])
    # o.setMaterial(mat)
    
    if(d['material'] != ""):
        mat = material(d['material'], s, d['material_embed'])
        o.setMaterial(mat)
    if(d['backface_material'] != ""):
        bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
        o.setBackfaceMaterial(bm)
    
    base_and_pivot(o, d)
    object_props(o, d)


def grass(d, s):
    m = CextensionManager.instance()
    m.loadAllExtensions()
    
    e = m.createDefaultGeometryModifierExtension('MaxwellGrass')
    p = e.getExtensionData()
    
    # data = [(0, 'UCHAR'), (1, 'UINT'), (2, 'INT'), (3, 'FLOAT'), (4, 'DOUBLE'), (5, 'STRING'), (6, 'FLOATARRAY'), (7, 'DOUBLEARRAY'),
    #         (8, 'BYTEARRAY'), (9, 'INTARRAY'), (10, 'MXPARAMLIST'), (11, 'MXPARAMLISTARRAY'), (12, 'RGB'), ]
    # mp = p.getByIndex(3)[1]
    # for i in range(mp.getNumItems()):
    #     s = list(mp.getByIndex(i))
    #     for di, dt in data:
    #         if(di == s[4]):
    #             s[4] = "{} ({})".format(di, dt)
    #     print(str(tuple(s)))
    
    def texture_data_to_mxparams(d, mp):
        if(d is None):
            return
        # mp.setString('CtextureMap.FileName', d['path'])
        # hey, seriously.. WTF?
        mp.setString('CtextureMap.FileName', ''.join(d['path']))
        mp.setByte('CtextureMap.uvwChannel', d['channel'])
        mp.setByte('CtextureMap.uIsTiled', d['tile_method_type'][0])
        mp.setByte('CtextureMap.vIsTiled', d['tile_method_type'][1])
        mp.setByte('CtextureMap.uIsMirrored', d['mirror'][0])
        mp.setByte('CtextureMap.vIsMirrored', d['mirror'][1])
        mp.setFloat('CtextureMap.scale.x', d['repeat'][0])
        mp.setFloat('CtextureMap.scale.y', d['repeat'][1])
        mp.setFloat('CtextureMap.offset.x', d['offset'][0])
        mp.setFloat('CtextureMap.offset.y', d['offset'][1])
        mp.setFloat('CtextureMap.rotation', d['rotation'])
        mp.setByte('CtextureMap.invert', d['invert'])
        mp.setByte('CtextureMap.useAbsoluteUnits', d['tile_method_units'])
        mp.setByte('CtextureMap.useAlpha', d['alpha_only'])
        mp.setByte('CtextureMap.typeInterpolation', d['interpolation'])
        mp.setFloat('CtextureMap.saturation', d['saturation'])
        mp.setFloat('CtextureMap.contrast', d['contrast'])
        mp.setFloat('CtextureMap.brightness', d['brightness'])
        mp.setFloat('CtextureMap.hue', d['hue'])
        mp.setFloat('CtextureMap.clampMin', d['rgb_clamp'][0])
        mp.setFloat('CtextureMap.clampMax', d['rgb_clamp'][1])
        mp.setFloat('CtextureMap.useGlobalMap', d['use_override_map'])
    
    if(d['material'] != ""):
        mat = material(d['material'], s, d['material_embed'])
        p.setString('Material', mat.getName())
    
    if(d['backface_material'] != ""):
        bmat = material(d['backface_material'], s, d['backface_material_embed'])
        p.setString('Double Sided Material', bmat.getName())
    
    p.setUInt('Density', d['density'])
    
    mxp = p.getByName('Density Map')[0]
    texture_data_to_mxparams(d['density_map'], p.getByName('Density Map')[0])
    
    p.setFloat('Length', d['length'])
    texture_data_to_mxparams(d['length_map'], p.getByName('Length Map')[0])
    p.setFloat('Length Variation', d['length_variation'])
    
    p.setFloat('Root Width', d['root_width'])
    p.setFloat('Tip Width', d['tip_width'])
    
    p.setUInt('Direction Type', d['direction_type'])
    
    p.setFloat('Initial Angle', d['initial_angle'])
    p.setFloat('Initial Angle Variation', d['initial_angle_variation'])
    texture_data_to_mxparams(d['initial_angle_map'], p.getByName('Initial Angle Map')[0])
    
    p.setFloat('Start Bend', d['start_bend'])
    p.setFloat('Start Bend Variation', d['start_bend_variation'])
    texture_data_to_mxparams(d['start_bend_map'], p.getByName('Start Bend Map')[0])
    
    p.setFloat('Bend Radius', d['bend_radius'])
    p.setFloat('Bend Radius Variation', d['bend_radius_variation'])
    texture_data_to_mxparams(d['bend_radius_map'], p.getByName('Bend Radius Map')[0])
    
    p.setFloat('Bend Angle', d['bend_angle'])
    p.setFloat('Bend Angle Variation', d['bend_angle_variation'])
    texture_data_to_mxparams(d['bend_angle_map'], p.getByName('Bend Angle Map')[0])
    
    p.setFloat('Cut Off', d['cut_off'])
    p.setFloat('Cut Off Variation', d['cut_off_variation'])
    texture_data_to_mxparams(d['cut_off_map'], p.getByName('Cut Off Map')[0])
    
    p.setUInt('Points per Blade', d['points_per_blade'])
    p.setUInt('Primitive Type', d['primitive_type'])
    
    p.setUInt('Seed', d['seed'])
    
    p.setByte('Enable LOD', d['lod'])
    p.setFloat('LOD Min Distance', d['lod_min_distance'])
    p.setFloat('LOD Max Distance', d['lod_max_distance'])
    p.setFloat('LOD Max Distance Density', d['lod_max_distance_density'])
    
    p.setUInt('Display Percent', d['display_percent'])
    p.setUInt('Display Max. Blades', d['display_max_blades'])
    
    o = s.getObject(d['object'])
    o.applyGeometryModifierExtension(p)


def hair(d, s):
    m = CextensionManager.instance()
    m.loadAllExtensions()
    
    if(d['extension'] == 'MaxwellHair'):
        e = m.createDefaultGeometryProceduralExtension('MaxwellHair')
    if(d['extension'] == 'MGrassP'):
        e = m.createDefaultGeometryProceduralExtension('MGrassP')
    
    p = e.getExtensionData()
    p.setByteArray('HAIR_MAJOR_VER', d['data']['HAIR_MAJOR_VER'])
    p.setByteArray('HAIR_MINOR_VER', d['data']['HAIR_MINOR_VER'])
    p.setByteArray('HAIR_FLAG_ROOT_UVS', d['data']['HAIR_FLAG_ROOT_UVS'])
    
    # p.setByteArray('HAIR_GUIDES_COUNT', d['data']['HAIR_GUIDES_COUNT'])
    m = memoryview(struct.pack("I", d['data']['HAIR_GUIDES_COUNT'][0])).tolist()
    p.setByteArray('HAIR_GUIDES_COUNT', m)
    
    # p.setByteArray('HAIR_GUIDES_POINT_COUNT', d['data']['HAIR_GUIDES_POINT_COUNT'])
    m = memoryview(struct.pack("I", d['data']['HAIR_GUIDES_POINT_COUNT'][0])).tolist()
    p.setByteArray('HAIR_GUIDES_POINT_COUNT', m)
    
    c = Cbase()
    c.origin = Cvector(0.0, 0.0, 0.0)
    c.xAxis = Cvector(1.0, 0.0, 0.0)
    c.yAxis = Cvector(0.0, 1.0, 0.0)
    c.zAxis = Cvector(0.0, 0.0, 1.0)
    
    bhp = d['hair_data_path']
    r = MXSBinHairReader(bhp)
    p.setFloatArray('HAIR_POINTS', list(r.data), c)
    
    # p.setFloatArray('HAIR_POINTS', d['data']['HAIR_POINTS'], c)
    p.setFloatArray('HAIR_NORMALS', d['data']['HAIR_NORMALS'], c)
    
    p.setUInt('Display Percent', d['display_percent'])
    if(d['extension'] == 'MaxwellHair'):
        p.setUInt('Display Max. Hairs', d['display_max_hairs'])
        p.setDouble('Root Radius', d['hair_root_radius'])
        p.setDouble('Tip Radius', d['hair_tip_radius'])
    if(d['extension'] == 'MGrassP'):
        p.setUInt('Display Max. Hairs', d['display_max_blades'])
        p.setDouble('Root Radius', d['grass_root_width'])
        p.setDouble('Tip Radius', d['grass_tip_width'])
    
    # # for i in range(p.getNumItems()):
    # #     print(p.getByIndex(i))
    #
    # # print(p.getByName('HAIR_GUIDES_COUNT')[0])
    # # print(p.getByName('HAIR_GUIDES_POINT_COUNT')[0])
    # print()
    # print(d['data']['HAIR_GUIDES_COUNT'][0])
    # print(d['data']['HAIR_GUIDES_COUNT'][0] * d['data']['HAIR_GUIDES_POINT_COUNT'][0] * 3)
    # print(p.getByName('HAIR_GUIDES_COUNT'))
    # print(p.getByName('HAIR_GUIDES_POINT_COUNT'))
    # # print(p.getByName('HAIR_GUIDES_COUNT')[0][0] * p.getByName('HAIR_GUIDES_POINT_COUNT')[0][0] * 3)
    # print(len(p.getByName('HAIR_POINTS')[0]))
    # # print(p.getByName('HAIR_NORMALS')[0])
    # print()
    
    o = s.createGeometryProceduralObject(d['name'], p)
    
    if(d['material'] != ""):
        mat = material(d['material'], s, d['material_embed'])
        o.setMaterial(mat)
    if(d['backface_material'] != ""):
        bm = material(d['backface_material'][0], s, d['backface_material_embed'][1])
        o.setBackfaceMaterial(bm)
    
    base_and_pivot(o, d)
    object_props(o, d)


def hierarchy(d, s):
    log("setting object hierarchy..", 2)
    object_types = ['EMPTY', 'MESH', 'INSTANCE', 'PARTICLES', 'HAIR', ]
    exclude = ['SCENE', 'ENVIRONMENT', 'GRASS', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types and d[i]['type'] not in exclude):
            if(d[i]['parent'] is not None):
                ch = s.getObject(d[i]['name'])
                p = s.getObject(d[i]['parent'])
                ch.setParent(p)
    
    object_types = ['PARTICLES', 'HAIR', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types):
            if(d[i]['parent'] is not None):
                if(d[i]['hide_parent']):
                    p = s.getObject(d[i]['parent'])
                    p.setHide(True)


def wireframe_hierarchy(d, s, ws):
    # wire and clay empties data
    ced = {'name': 'clay',
           'parent': None,
           'base': ((0.0, 0.0, -0.0), (1.0, 0.0, -0.0), (0.0, 1.0, -0.0), (-0.0, -0.0, 1.0)),
           'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
           'opacity': 100.0,
           'hidden_camera': False,
           'hidden_camera_in_shadow_channel': False,
           'hidden_global_illumination': False,
           'hidden_reflections_refractions': False,
           'hidden_zclip_planes': False,
           'object_id': (0, 0, 0),
           'hide': False,
           'type': 'EMPTY', }
    ce = empty(ced, s)
    wed = {'name': 'wire',
           'parent': None,
           'base': ((0.0, 0.0, -0.0), (1.0, 0.0, -0.0), (0.0, 1.0, -0.0), (-0.0, -0.0, 1.0)),
           'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
           'opacity': 100.0,
           'hidden_camera': False,
           'hidden_camera_in_shadow_channel': False,
           'hidden_global_illumination': False,
           'hidden_reflections_refractions': False,
           'hidden_zclip_planes': False,
           'object_id': (0, 0, 0),
           'hide': False,
           'type': 'EMPTY', }
    we = empty(wed, s)
    object_types = ['EMPTY', 'MESH', 'INSTANCE', 'WIREFRAME_EDGE', 'WIREFRAME', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types):
            if(d[i]['type'] == 'WIREFRAME'):
                pass
            elif(d[i]['type'] == 'WIREFRAME_EDGE'):
                ch = s.getObject(d[i]['name'])
                ch.setParent(we)
            else:
                if(d[i]['parent'] is None):
                    ch = s.getObject(d[i]['name'])
                    ch.setParent(ce)
    # group all wires..
    for w in ws:
        w.setParent(we)


def wireframe_base(d, s):
    o = mesh(d, s)
    # zero scale wire instance source base mesh to be practically invisible :)
    o.setScale(Cvector(0, 0, 0))
    # o.setMaterial(mat)
    return o


def wireframe(d, s):
    r = []
    with open(d['matrices_path'], 'r') as f:
        md = json.load(f)
    bo = s.getObject(d['instanced'])
    for i, m in enumerate(md['matrices']):
        o = s.createInstancement("{0}-{1}".format(d['name'], i), bo)
        bp = {'base': m[0], 'pivot': m[1], }
        base_and_pivot(o, bp)
        object_props(o, d)
        r.append(o)
        # o.setMaterial(mat)
    return r


def wireframe_material(d, s):
    n = d['name']
    r0 = d['data']['reflectance_0']
    r90 = d['data']['reflectance_90']
    ci = d['data']['id']
    rough = d['data']['roughness']
    mat = s.createMaterial(n)
    l = mat.addLayer()
    l.setName(n)
    b = l.addBSDF()
    r = b.getReflectance()
    a = Cattribute()
    a.activeType = MAP_TYPE_RGB
    c = Crgb8()
    c.assign(*r0)
    a.rgb.assign(c.toRGB())
    r.setAttribute('color', a)
    a = Cattribute()
    a.activeType = MAP_TYPE_RGB
    c = Crgb8()
    c.assign(*r90)
    a.rgb.assign(c.toRGB())
    r.setAttribute('color.tangential', a)
    a = Cattribute()
    a.type = MAP_TYPE_VALUE
    a.value = rough
    b.setAttribute('roughness', a)
    c = Crgb8()
    c.assign(*ci)
    mat.setColorID(c.toRGB())
    return mat


def wireframe_assign_materials(d, s, ws, wm, cm):
    if(wm is None or cm is None):
        raise RuntimeError("wire or clay material is missing..")
    
    object_types = ['EMPTY', 'MESH', 'INSTANCE', 'WIREFRAME_EDGE', 'WIREFRAME', ]
    for i in range(len(d)):
        if(d[i]['type'] in object_types):
            if(d[i]['type'] == 'WIREFRAME'):
                pass
            elif(d[i]['type'] == 'WIREFRAME_EDGE'):
                o = s.getObject(d[i]['name'])
                o.setMaterial(wm)
            else:
                o = s.getObject(d[i]['name'])
                o.setMaterial(cm)
    # group all wires..
    for w in ws:
        w.setMaterial(wm)


def main(args):
    log("loading data..", 2)
    with open(args.scene_data_path, 'r') as f:
        data = json.load(f)
    # create scene
    mxs = Cmaxwell(mwcallback)
    if(args.append is True):
        log("appending to existing scene..", 2)
        mxs.readMXS(args.result_path)
    else:
        log("creating new scene..", 2)
    # loop over scene data and create things by type
    if(args.wireframe):
        w_material = None
        c_material = None
        all_wires = []
    progress = PercentDone(len(data), indent=2, )
    for d in data:
        if(d['type'] == 'CAMERA'):
            camera(d, mxs)
        elif(d['type'] == 'EMPTY'):
            empty(d, mxs)
        elif(d['type'] == 'MESH'):
            mesh(d, mxs)
            if(args.instancer):
                # there should be just one mesh which is base, scale it to zero to be invisible..
                name = d['name']
                ob = mxs.getObject(d['name'])
                ob.setScale(Cvector(0.0, 0.0, 0.0))
        elif(d['type'] == 'INSTANCE'):
            try:
                if(d['base']):
                    mesh(d, mxs)
            except KeyError:
                instance(d, mxs)
        elif(d['type'] == 'SCENE'):
            scene(d, mxs)
            custom_alphas(d, mxs)
        elif(d['type'] == 'ENVIRONMENT'):
            environment(d, mxs)
        elif(d['type'] == 'PARTICLES'):
            particles(d, mxs)
        elif(d['type'] == 'GRASS'):
            grass(d, mxs)
        elif(d['type'] == 'HAIR'):
            hair(d, mxs)
        elif(d['type'] == 'WIREFRAME_MATERIAL'):
            mat = wireframe_material(d, mxs)
            m = {'name': d['name'], 'data': mat, }
            if(d['name'] == 'wire'):
                w_material = mat
            elif(d['name'] == 'clay'):
                c_material = mat
            else:
                raise TypeError("'{0}' is unknown wireframe material".format(d['name']))
        elif(d['type'] == 'WIREFRAME_EDGE'):
            wireframe_base(d, mxs)
        elif(d['type'] == 'WIREFRAME'):
            ws = wireframe(d, mxs)
            all_wires.extend(ws)
        else:
            raise TypeError("{0} is unknown type".format(d['type']))
        progress.step()
    #
    hierarchy(data, mxs)
    #
    if(args.wireframe):
        wireframe_hierarchy(data, mxs, all_wires)
        wireframe_assign_materials(data, mxs, all_wires, w_material, c_material)
    #
    if(args.instancer):
        name = "instancer"
        
        def get_objects_names(mxs):
            it = CmaxwellObjectIterator()
            o = it.first(mxs)
            l = []
            while not o.isNull():
                name, _ = o.getName()
                l.append(name)
                o = it.next()
            return l
        
        ns = get_objects_names(mxs)
        ed = {'name': name,
              'parent': None,
              'base': ((0.0, 0.0, -0.0), (1.0, 0.0, -0.0), (0.0, 1.0, -0.0), (-0.0, -0.0, 1.0)),
              'pivot': ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
              'opacity': 100.0,
              'hidden_camera': False,
              'hidden_camera_in_shadow_channel': False,
              'hidden_global_illumination': False,
              'hidden_reflections_refractions': False,
              'hidden_zclip_planes': False,
              'object_id': (255, 255, 255),
              'hide': False,
              'type': 'EMPTY', }
        e = empty(ed, mxs)
        for n in ns:
            ch = mxs.getObject(n)
            ch.setParent(e)
    
    # set active camera, again.. for some reason it gets reset
    for d in data:
        if(d['type'] == 'CAMERA'):
            if(d['active']):
                c = mxs.getCamera(d['name'])
                c.setActive()
    # save mxs
    log("saving scene..", 2)
    ok = mxs.writeMXS(args.result_path)
    log("done.", 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=textwrap.dedent('''Make Maxwell scene from serialized data'''), epilog='',
                                     formatter_class=argparse.RawDescriptionHelpFormatter, add_help=True, )
    parser.add_argument('-a', '--append', action='store_true', help='append to existing mxs (result_path)')
    parser.add_argument('-w', '--wireframe', action='store_true', help='scene data contains wireframe scene')
    parser.add_argument('-i', '--instancer', action='store_true', help='scene data contains instancer (python only)')
    parser.add_argument('-q', '--quiet', action='store_true', help='no logging except errors')
    parser.add_argument('log_file', type=str, help='path to log file')
    parser.add_argument('scene_data_path', type=str, help='path to serialized scene data file')
    parser.add_argument('result_path', type=str, help='path to result .mxs')
    args = parser.parse_args()
    
    quiet = args.quiet
    
    # logger = logging.getLogger()
    # logger.setLevel(logging.NOTSET)
    # fh = logging.FileHandler(args.log_file)
    LOG_FILE_PATH = args.log_file
    # fh.setLevel(logging.NOTSET)
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.NOTSET)
    # ch.setFormatter(logging.Formatter(fmt='{message}', datefmt=None, style='{', ))
    # fh.setFormatter(logging.Formatter(fmt='{message}', datefmt=None, style='{', ))
    # logger.addHandler(ch)
    # logger.addHandler(fh)
    
    try:
        main(args)
    except Exception as e:
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # sys.stdout.write("".join(lines))
        
        import traceback
        m = traceback.format_exc()
        log(m)
        
        # log("".join(lines))
        sys.exit(1)
    sys.exit(0)
