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
import datetime
import struct
import math
import sys

from .log import log, LogStyles

s = platform.system()
if(s == 'Darwin'):
    pass
elif(s == 'Linux'):
    # mp = os.environ.get("MAXWELL3_ROOT")
    # pymxp = os.path.abspath(os.path.join(mp, 'python', 'pymaxwell', 'python3.4'))
    # sys.path.append(pmp)
    # lib = "libmxcommon.so"
    # libp = os.path.join(mp, lib)
    # linkp = os.path.join(pymxp, lib)
    # if(os.path.islink(linkp)):
    #     if(os.path.realpath(linkp) != libp):
    #         os.unlink(linkp)
    # os.symlink(libp, linkp)
    # mgr = CextensionManager.instance()
    # mgr.loadAllExtensions()
    # os.unlink(linkp)
    
    # mp = os.environ.get("MAXWELL3_ROOT")
    # pymxp = os.path.abspath(os.path.join(mp, 'python', 'pymaxwell', 'python3.4'))
    # sys.path.append(pymxp)
    # os.environ['LD_LIBRARY_PATH'] = mp
    # from pymaxwell import *
    # mgr = CextensionManager.instance()
    # mgr.loadAllExtensions()
    
    # install libtbb-dev
    # before starting blender (from terminal of course) do: export LD_LIBRARY_PATH=$MAXWELL3_ROOT
    # or add this to profile: export LD_LIBRARY_PATH=$MAXWELL3_ROOT:$LD_LIBRARY_PATH
    # manipulating LD_LIBRARY_PATH from blender itself will not work because it is already running..
    
    try:
        from pymaxwell import *
    except ImportError:
        mp = os.environ.get("MAXWELL3_ROOT")
        sys.path.append(os.path.abspath(os.path.join(mp, 'python', 'pymaxwell', 'python3.4')))
        from pymaxwell import *
elif(s == 'Windows'):
    from pymaxwell import *


class MXSWriter():
    def __init__(self, path, append=False, ):
        """Create scene or load existing.
        path    string (path)
        append  bool
        """
        
        # if('Cmaxwell' not in locals()):
        #     raise ImportError("No pymaxwell..")
        #     return
        
        if(__name__ != "__main__"):
            if(platform.system() == 'Darwin'):
                raise ImportError("No pymaxwell for Mac OS X..")
        
        log(self.__class__.__name__, 1, LogStyles.MESSAGE, prefix="* ", )
        
        self.path = path
        self.mxs = Cmaxwell(mwcallback)
        if(append):
            log("appending to existing scene..", 2, prefix="* ", )
            self.mxs.readMXS(self.path)
        else:
            log("creating new scene..", 2, prefix="* ", )
        
        self.mgr = CextensionManager.instance()
        self.mgr.loadAllExtensions()
        
        self.matdb = []
    
    def set_base_and_pivot(self, o, base=None, pivot=None, ):
        """Convert float tuples to Cbases and set to object.
        o       CmaxwellObject
        base    ((3 float), (3 float), (3 float), (3 float)) or None
        pivot   ((3 float), (3 float), (3 float), (3 float)) or None
        """
        if(base is None):
            base = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        if(pivot is None):
            pivot = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        b = Cbase()
        b.origin = Cvector(*base[0])
        b.xAxis = Cvector(*base[1])
        b.yAxis = Cvector(*base[2])
        b.zAxis = Cvector(*base[3])
        p = Cbase()
        p.origin = Cvector(*pivot[0])
        p.xAxis = Cvector(*pivot[1])
        p.yAxis = Cvector(*pivot[2])
        p.zAxis = Cvector(*pivot[3])
        o.setBaseAndPivot(b, p)
    
    def set_object_props(self, o, hide=False, opacity=100, cid=(255, 255, 255), hcam=False, hcamsc=False, hgi=False, hrr=False, hzcp=False, ):
        """Set common object properties.
        o           CmaxwellObject
        hide        bool
        opacity     float
        cid         (int, int, int) 0-255 rgb
        hcam        bool
        hcamsc      bool
        hgi         bool
        hrr         bool
        hzcp        bool
        """
        if(hide):
            o.setHide(hide)
        if(opacity != 100.0):
            o.setOpacity(opacity)
        c = Crgb()
        c.assign(*[v / 255 for v in cid])
        o.setColorID(c)
        if(hcam):
            o.setHideToCamera(True)
        if(hcamsc):
            o.setHideToCameraInShadowsPass(True)
        if(hgi):
            o.setHideToGI(True)
        if(hrr):
            o.setHideToReflectionsRefractions(True)
        if(hzcp):
            o.excludeOfCutPlanes(True)
    
    def camera(self, props, steps, active=False, lens_extra=None, response=None, region=None, custom_bokeh=(1.0, 0.0, False), cut_planes=(0.0, 1e7, False), shift_lens=(0.0, 0.0), ):
        """Create camera.
        props           (string name, int nSteps, float shutter, float filmWidth, float filmHeight, float iso, int diaphragmType, float angle,
                         int nBlades, float fps, int xRes, int yRes, float pixelAspect, int lensType, int projectionType)
        steps           [(int iStep, [3 float] origin, [3 float] focalPoint, [3 float] up, float focalLength, float fStop, bool focalLengthNeedCorrection), ..., ]
        active          bool
        lens_extra      float or None
        response        string or None
        region          (float x1, float y1, float x2, float y2, string type) or None
        custom_bokeh    (float ratio, float angle, bool enabled) or None
        cut_planes      (float near, float far, bool enabled) or None
        shift_lens      (float x, float y) or None
        """
        
        # TODO how to set shutter_angle?
        
        s = self.mxs
        c = s.addCamera(*props)
        for step in steps:
            l = list(step[:])
            l[1] = Cvector(*l[1])
            l[2] = Cvector(*l[2])
            l[3] = Cvector(*l[3])
            c.setStep(*l)
        
        # TYPE_THIN_LENS, TYPE_PINHOLE, TYPE_ORTHO
        if(lens_extra is not None):
            if(props[13] == TYPE_FISHEYE):
                c.setFishLensProperties(lens_extra)
            if(props[13] == TYPE_SPHERICAL):
                c.setSphericalLensProperties(lens_extra)
            if(props[13] == TYPE_CYLINDRICAL):
                c.setCylindricalLensProperties(lens_extra)
        if(response is not None):
            c.setCameraResponsePreset(response)
        if(custom_bokeh is not None):
            c.setCustomBokeh(*custom_bokeh)
        if(cut_planes is not None):
            c.setCutPlanes(*cut_planes)
        if(shift_lens is not None):
            c.setShiftLens(*shift_lens)
        if(region is not None):
            c.setScreenRegion(*region)
        
        if(active):
            c.setActive()
        return c
    
    def load_material(self, path, embed, ):
        """Load material from mxm file.
        path    string or None
        embed   bool
        """
        s = self.mxs
        r = None
        for p, m, e in self.matdb:
            if(p == path):
                r = m
        pok = False
        if(path is not None):
            if(path is not ""):
                if(path.endswith('.mxm')):
                    if(os.path.exists(path)):
                        pok = True
        if(r is None and pok):
            t = s.readMaterial(path)
            r = s.addMaterial(t)
            self.matdb.append((path, r, embed))
            if(embed is False):
                r.setReference(1, path)
        return r
    
    def material_placeholder(self):
        """Create material placeholder when needed to keem trangle material groups.
        no parameters..
        """
        s = self.mxs
        n = 'MATERIAL_PLACEHOLDER'
        # return clone if already loaded
        for p, m, e in self.matdb:
            if(p == n):
                c = m.createCopy()
                cm = s.addMaterial(c)
                return cm
        
        m = s.createMaterial(n)
        l = m.addLayer()
        b = l.addBSDF()
        r = b.getReflectance()
        a = Cattribute()
        a.activeType = MAP_TYPE_BITMAP
        t = CtextureMap()
        mgr = CextensionManager.instance()
        mgr.loadAllExtensions()
        e = mgr.createDefaultTextureExtension('Checker')
        ch = e.getExtensionData()
        ch.setUInt('Number of elements U', 32)
        ch.setUInt('Number of elements V', 32)
        t.addProceduralTexture(ch)
        a.textureMap = t
        r.setAttribute('color', a)
        
        self.matdb.append((n, m, True))
        
        return m
    
    def empty(self, name, base, pivot, object_props=None, ):
        """Create empty object.
        name            string
        base            ((3 float), (3 float), (3 float), (3 float))
        pivot           ((3 float), (3 float), (3 float), (3 float))
        object_props    (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        """
        s = self.mxs
        o = s.createMesh(name, 0, 0, 0, 0, )
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        return o
    
    def mesh(self, name, base, pivot, num_positions, vertices, normals, triangles, triangle_normals, uv_channels, object_props=None, num_materials=0, materials=[], triangle_materials=None, backface_material=None, ):
        """Create mesh object.
        name                string
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        num_positions       int
        vertices            [[(float x, float y, float z), ..., ], [...], ]
        normals             [[(float x, float y, float z), ..., ], [...], ]
        triangles           [(int iv0, int iv1, int iv2, int in0, int in1, int in2, ), ..., ], ]   # (3x vertex index, 3x normal index)
        triangle_normals    [[(float x, float y, float z), ..., ], [...], ]
        uv_channels         [[(float u1, float v1, float w1, float u2, float v2, float w2, float u3, float v3, float w3, ), ..., ], ..., ] or None      # ordered by uv index and ordered by triangle index
        num_materials       int
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        materials           [(string path, bool embed), ..., ] or None
        triangle_materials  [(int tri_id, int mat_id), ..., ] or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        o = s.createMesh(name, len(vertices[0]), len(normals[0]) + len(triangle_normals[0]), len(triangles), num_positions)
        if(uv_channels is not None):
            for i in range(len(uv_channels)):
                o.addChannelUVW(i)
        an = 0
        for ip in range(num_positions):
            verts = vertices[ip]
            norms = normals[ip]
            for i, loc in enumerate(verts):
                o.setVertex(i, ip, Cvector(*loc), )
                o.setNormal(i, ip, Cvector(*norms[i]), )
                an += 1
        for ip in range(num_positions):
            trinorms = triangle_normals[ip]
            for i, nor in enumerate(trinorms):
                o.setNormal(an + i, ip, Cvector(*nor), )
        for i, tri in enumerate(triangles):
            o.setTriangle(i, *tri)
        if(uv_channels is not None):
            for iuv, uv in enumerate(uv_channels):
                for it, t in enumerate(uv):
                    o.setTriangleUVW(it, iuv, *t)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(materials is not None):
            if(num_materials > 1):
                # multi material
                mats = []
                for mi in range(num_materials):
                    mat = self.load_material(*materials[mi])
                    if(mat is None):
                        mat = self.material_placeholder()
                    mats.append(mat)
                for tid, mid in triangle_materials:
                    o.setTriangleMaterial(tid, mats[mid])
            elif(num_materials == 1):
                # single material
                mat = self.load_material(*materials[0])
                if(mat is not None):
                    # set for whole object, no need to care about triangles
                    o.setMaterial(mat)
        else:
            # no material
            pass
        
        if(backface_material is not None):
            # only single backface material
            mat = self.load_material(*backface_material)
            if(mat is not None):
                o.setBackfaceMaterial(mat)
        
        return o
    
    def instance(self, name, instanced_name, base, pivot, object_props=None, material=None, backface_material=None, ):
        """Create instance of mesh object. Instanced object must exist in scene.
        name                string
        instanced_name      string
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        bo = s.getObject(instanced_name)
        o = s.createInstancement(name, bo)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(material is not None):
            m = self.load_material(*material)
            if(m is not None):
                o.setMaterial(m)
        if(backface_material is not None):
            m = self.load_material(*backface_material)
            if(m is not None):
                o.setBackfaceMaterial(m)
        
        return o
    
    def hierarchy(self, tree, ):
        """Set hierarchy of all objects at once.
        tree    [(obj_name, parent_name or None, ), ..., ]
        """
        s = self.mxs
        for on, pn in tree:
            if(pn is not None):
                o = s.getObject(on)
                p = s.getObject(pn)
                o.setParent(p)
    
    def environment(self, env_type=None, sky_type=None, sky=None, dome=None, sun_type=None, sun=None, ibl=None, ):
        """Set Environment properties.
        env_type    string or None      PHYSICAL_SKY, IMAGE_BASED, NONE
        sky_type    string or None      PHYSICAL, CONSTANT
        sky         dict or None        {sky_use_preset         bool
                                         sky_preset             string (path)
                                         sky_intensity          float
                                         sky_planet_refl        float
                                         sky_ozone              float
                                         sky_water              float
                                         sky_turbidity_coeff    float
                                         sky_wavelength_exp     float
                                         sky_reflectance        float
                                         sky_asymmetry          float}
        dome        dict or None        {dome_intensity         float
                                         dome_zenith            [float, float, float]
                                         dome_horizon           [float, float, float]
                                         dome_mid_point         float}
        sun_type    string or None      DISABLED, PHYSICAL, CUSTOM
        sun         dict or None        {sun_power                      float
                                         sun_radius_factor              float
                                         sun_temp                       float
                                         sun_color                      [float, float, float]
                                         sun_location_type              string      LATLONG, ANGLES, DIRECTION
                                         sun_latlong_lat                float
                                         sun_latlong_lon                float
                                         sun_date                       string
                                         sun_time                       string
                                         sun_latlong_gmt                int
                                         sun_latlong_gmt_auto           bool
                                         sun_latlong_ground_rotation    float
                                         sun_angles_zenith              float
                                         sun_angles_azimuth             float
                                         sun_dir_x                      float
                                         sun_dir_y                      float
                                         sun_dir_z                      float}
        ibl         dict or None        {ibl_intensity          float
                                         ibl_interpolation      bool
                                         ibl_screen_mapping     bool
                                         ibl_bg_type            string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_bg_map             string (path)
                                         ibl_bg_intensity       float
                                         ibl_bg_scale_x         float
                                         ibl_bg_scale_y         float
                                         ibl_bg_offset_x        float
                                         ibl_bg_offset_y        float
                                         ibl_refl_type          string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_refl_map           string (path)
                                         ibl_refl_intensity     float
                                         ibl_refl_scale_x       float
                                         ibl_refl_scale_y       float
                                         ibl_refl_offset_x      float
                                         ibl_refl_offset_y      float
                                         ibl_refr_type          string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_refr_map           string (path)
                                         ibl_refr_intensity     float
                                         ibl_refr_scale_x       float
                                         ibl_refr_scale_y       float
                                         ibl_refr_offset_x      float
                                         ibl_refr_offset_y      float
                                         ibl_illum_type         string      HDR_IMAGE, ACTIVE_SKY, DISABLED
                                         ibl_illum_map          string (path)
                                         ibl_illum_intensity    float
                                         ibl_illum_scale_x      float
                                         ibl_illum_scale_y      float
                                         ibl_illum_offset_x     float
                                         ibl_illum_offset_y     float}
        """
        s = self.mxs
        env = s.getEnvironment()
        if(env_type == 'PHYSICAL_SKY'):
            if(sky_type is not None):
                env.setActiveSky(sky_type)
                if(sky_type == 'PHYSICAL'):
                    if(not sky["sky_use_preset"]):
                        env.setPhysicalSkyAtmosphere(sky["sky_intensity"],
                                                     sky["sky_ozone"],
                                                     sky["sky_water"],
                                                     sky["sky_turbidity_coeff"],
                                                     sky["sky_wavelength_exp"],
                                                     sky["sky_reflectance"],
                                                     sky["sky_asymmetry"],
                                                     sky["sky_planet_refl"], )
                    else:
                        env.loadSkyFromPreset(sky["sky_preset"])
                    
                    sc = Crgb()
                    sc.assign(*[c / 255 for c in sun['sun_color']])
                    if(sun_type == 'PHYSICAL'):
                        env.setSunProperties(SUN_PHYSICAL, sun["sun_temp"], sun["sun_power"], sun["sun_radius_factor"], sc)
                    elif(sun_type == 'CUSTOM'):
                        env.setSunProperties(SUN_CONSTANT, sun["sun_temp"], sun["sun_power"], sun["sun_radius_factor"], sc)
                    else:
                        # sun_type == 'DISABLED' or sun_type == None
                        env.setSunProperties(SUN_DISABLED, sun["sun_temp"], sun["sun_power"], sun["sun_radius_factor"], sc)
                    
                    if(sun['sun_location_type'] == 'LATLONG'):
                        env.setSunPositionType(0)
                        l = sun["sun_date"].split(".")
                        date = datetime.date(int(l[2]), int(l[1]), int(l[0]))
                        day = int(date.timetuple().tm_yday)
                        l = sun["sun_time"].split(":")
                        hour = int(l[0])
                        minute = int(l[1])
                        time = hour + (minute / 60)
                        env.setSunLongitudeAndLatitude(sun["sun_latlong_lon"], sun["sun_latlong_lat"], sun["sun_latlong_gmt"], day, time)
                        env.setSunRotation(sun["sun_latlong_ground_rotation"])
                    elif(sun['sun_location_type'] == 'ANGLES'):
                        env.setSunPositionType(1)
                        env.setSunAngles(sun["sun_angles_zenith"], sun["sun_angles_azimuth"])
                    elif(sun['sun_location_type'] == 'DIRECTION'):
                        env.setSunPositionType(2)
                        env.setSunDirection(Cvector(sun["sun_dir_x"], sun["sun_dir_y"], sun["sun_dir_z"]))
                
                elif(sky_type == 'CONSTANT'):
                    hc = Crgb()
                    hc.assign(*[c / 255 for c in dome['dome_horizon']])
                    zc = Crgb()
                    zc.assign(*[c / 255 for c in dome['dome_zenith']])
                    env.setSkyConstant(dome["dome_intensity"], hc, zc, dome['dome_mid_point'])
        elif(env_type == 'IMAGE_BASED'):
            env.enableEnvironment(True)
            
            def state(s):
                if(s == 'HDR_IMAGE'):
                    return 1
                if(s == 'SAME_AS_BG'):
                    return 2
                return 0
            
            env.setEnvironmentWeight(ibl["ibl_intensity"])
            env.setEnvironmentLayer(IBL_LAYER_BACKGROUND, ibl["ibl_bg_map"], state(ibl["ibl_bg_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_bg_intensity"], ibl["ibl_bg_scale_x"], ibl["ibl_bg_scale_y"], ibl["ibl_bg_offset_x"], ibl["ibl_bg_offset_y"], )
            env.setEnvironmentLayer(IBL_LAYER_REFLECTION, ibl["ibl_refl_map"], state(ibl["ibl_refl_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_refl_intensity"], ibl["ibl_refl_scale_x"], ibl["ibl_refl_scale_y"], ibl["ibl_refl_offset_x"], ibl["ibl_refl_offset_y"], )
            env.setEnvironmentLayer(IBL_LAYER_REFRACTION, ibl["ibl_refr_map"], state(ibl["ibl_refr_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_refr_intensity"], ibl["ibl_refr_scale_x"], ibl["ibl_refr_scale_y"], ibl["ibl_refr_offset_x"], ibl["ibl_refr_offset_y"], )
            env.setEnvironmentLayer(IBL_LAYER_ILLUMINATION, ibl["ibl_illum_map"], state(ibl["ibl_illum_type"]), not ibl["ibl_screen_mapping"], not ibl["ibl_interpolation"],
                                    ibl["ibl_illum_intensity"], ibl["ibl_illum_scale_x"], ibl["ibl_illum_scale_y"], ibl["ibl_illum_offset_x"], ibl["ibl_illum_offset_y"], )
        else:
            # env_type == 'NONE' or env_type == None
            env.setActiveSky('')
    
    def parameters(self, scene, materials=None, generals=None, tone=None, simulens=None, illum_caustics=None, ):
        """Set scene render parameters.
        scene           dict    {cpu_threads        int,
                                 multilight         int,
                                 multilight_type    int,
                                 quality            string      RS1, RS0
                                 sampling_level     float,
                                 time               int, },
        materials       dict    {override           bool,
                                 override_path      string (path),
                                 search_path        string (path), } or None
        generals        dict    {diplacement        bool,
                                 dispersion         bool,
                                 motion_blur        bool, } or None
        tone            dict    {burn               float,
                                 color_space        int,
                                 gamma              float,
                                 sharpness          bool,
                                 sharpness_value    float,
                                 tint               float,
                                 whitepoint         float, } or None
        simulens        dict    {aperture_map       string (path),
                                 devignetting       bool,
                                 devignetting_value float,
                                 diffraction        bool,
                                 diffraction_value  float,
                                 frequency          float,
                                 obstacle_map       string (path),
                                 scattering         bool,
                                 scattering_value   float, } or None
        illum_caustics  dict    {illumination       int,
                                 refl_caustics      int,
                                 refr_caustics      int, } or None
        """
        s = self.mxs
        # s.setRenderParameter('ENGINE', scene["quality"])
        s.setRenderParameter('ENGINE', bytes(scene["quality"], encoding='UTF-8'))
        s.setRenderParameter('NUM THREADS', scene["cpu_threads"])
        s.setRenderParameter('STOP TIME', scene["time"] * 60)
        s.setRenderParameter('SAMPLING LEVEL', scene["sampling_level"])
        s.setRenderParameter('USE MULTILIGHT', scene["multilight"])
        s.setRenderParameter('SAVE LIGHTS IN SEPARATE FILES', scene["multilight_type"])
        
        if(generals is not None):
            s.setRenderParameter('DO MOTION BLUR', generals["motion_blur"])
            s.setRenderParameter('DO DISPLACEMENT', generals["diplacement"])
            s.setRenderParameter('DO DISPERSION', generals["dispersion"])
        
        if(illum_caustics is not None):
            v = illum_caustics['illumination']
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
            v = illum_caustics['refl_caustics']
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
            v = illum_caustics['refr_caustics']
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
        
        if(simulens is not None):
            s.setRenderParameter('DO DEVIGNETTING', simulens["devignetting"])
            s.setRenderParameter('DEVIGNETTING', simulens["devignetting_value"])
            s.setRenderParameter('DO SCATTERING_LENS', simulens["scattering"])
            s.setRenderParameter('SCATTERING_LENS', simulens["scattering_value"])
            if(simulens["diffraction"]):
                s.enableDiffraction()
                s.setDiffraction(simulens["diffraction_value"], simulens["frequency"], simulens["aperture_map"], simulens["obstacle_map"])
        
        if(tone is not None):
            s.setRenderParameter('DO SHARPNESS', tone["sharpness"])
            s.setRenderParameter('SHARPNESS', tone["sharpness_value"])
            s.setToneMapping(tone["gamma"], tone["burn"])
            s.setColorSpace(tone["color_space"])
            s.setWhitePoint(tone["whitepoint"], tone["tint"])
        
        if(materials is not None):
            if(materials["override"]):
                s.setOverrideMaterial(True)
            if(materials["override_path"] != ""):
                s.setOverrideMaterial(materials["override_path"])
            if(materials["search_path"] != ""):
                s.addSearchingPath(materials["search_path"])
    
    def channels(self, base_path, mxi, image, image_depth='RGB8', channels_output_mode=0, channels_render=True, channels_render_type=0, channels=None, ):
        """Set scene render channels.
        base_path               string (path)
        mxi                     string (path)
        image                   string (path)
        image_depth             string              RGB8, RGB16, RGB32
        channels_output_mode    int
        channels_render         bool
        channels_render_type    int
        channels                dict     {channels_alpha                  bool
                                          channels_alpha_file             string
                                          channels_alpha_opaque           bool
                                          channels_custom_alpha           bool
                                          channels_custom_alpha_file      string
                                          channels_deep                   bool
                                          channels_deep_file              string
                                          channels_deep_max_samples       int
                                          channels_deep_min_dist          float
                                          channels_deep_type              int
                                          channels_fresnel                bool
                                          channels_fresnel_file           string
                                          channels_material_id            bool
                                          channels_material_id_file       string
                                          channels_motion_vector          bool
                                          channels_motion_vector_file     string
                                          channels_normals                bool
                                          channels_normals_file           string
                                          channels_normals_space          int
                                          channels_object_id              bool
                                          channels_object_id_file         string
                                          channels_position               bool
                                          channels_position_file          string
                                          channels_position_space         int
                                          channels_roughness              bool
                                          channels_roughness_file         string
                                          channels_shadow                 bool
                                          channels_shadow_file            string
                                          channels_uv                     bool
                                          channels_uv_file                string
                                          channels_z_buffer               bool
                                          channels_z_buffer_far           float
                                          channels_z_buffer_file          string
                                          channels_z_buffer_near          float} or None
        """
        def get_ext_depth(t, e=None):
            if(e is not None):
                t = "{}{}".format(e[1:].upper(), int(t[3:]))
            
            if(t == 'RGB8'):
                return ('.tif', 8)
            elif(t == 'RGB16'):
                return ('.tif', 16)
            elif(t == 'RGB32'):
                return ('.tif', 32)
            elif(t == 'PNG8'):
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
        
        s = self.mxs
        
        s.setRenderParameter('DO NOT SAVE MXI FILE', (mxi is None))
        s.setRenderParameter('DO NOT SAVE IMAGE FILE', (image is None))
        if(mxi is not None):
            # s.setRenderParameter('MXI FULLNAME', mxi)
            s.setRenderParameter('MXI FULLNAME', bytes(mxi, encoding='UTF-8'))
        if(image is not None):
            if(image_depth is None):
                image_depth = 'RGB8'
            _, depth = get_ext_depth(image_depth, os.path.splitext(os.path.split(image)[1])[1])
            s.setPath('RENDER', image, depth)
        
        s.setRenderParameter('DO RENDER CHANNEL', int(channels_render))
        s.setRenderParameter('EMBED CHANNELS', channels_output_mode)
        
        if(channels_render_type == 2):
            s.setRenderParameter('DO DIFFUSE LAYER', 0)
            s.setRenderParameter('DO REFLECTION LAYER', 1)
        elif(channels_render_type == 1):
            s.setRenderParameter('DO DIFFUSE LAYER', 1)
            s.setRenderParameter('DO REFLECTION LAYER', 0)
        else:
            s.setRenderParameter('DO DIFFUSE LAYER', 1)
            s.setRenderParameter('DO REFLECTION LAYER', 1)
        
        if(channels is not None):
            e, depth = get_ext_depth(channels["channels_alpha_file"])
            s.setPath('ALPHA', "{}_alpha{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_shadow_file"])
            s.setPath('SHADOW', "{}_shadow{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_object_id_file"])
            s.setPath('OBJECT', "{}_object_id{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_material_id_file"])
            s.setPath('MATERIAL', "{}_material_id{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_motion_vector_file"])
            s.setPath('MOTION', "{}_motion_vector{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_z_buffer_file"])
            s.setPath('Z', "{}_z_buffer{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_roughness_file"])
            s.setPath('ROUGHNESS', "{}_roughness{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_fresnel_file"])
            s.setPath('FRESNEL', "{}_fresnel{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_normals_file"])
            s.setPath('NORMALS', "{}_normals{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_position_file"])
            s.setPath('POSITION', "{}_position{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_deep_file"])
            s.setPath('DEEP', "{}_deep{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_uv_file"])
            s.setPath('UV', "{}_uv{}".format(base_path, e), depth)
            e, depth = get_ext_depth(channels["channels_custom_alpha_file"])
            s.setPath('ALPHA_CUSTOM', "{}_custom_alpha{}".format(base_path, e), depth)
            
            s.setRenderParameter('DO ALPHA CHANNEL', int(channels["channels_alpha"]))
            s.setRenderParameter('OPAQUE ALPHA', int(channels["channels_alpha_opaque"]))
            s.setRenderParameter('DO IDOBJECT CHANNEL', int(channels["channels_object_id"]))
            s.setRenderParameter('DO IDMATERIAL CHANNEL', int(channels["channels_material_id"]))
            s.setRenderParameter('DO SHADOW PASS CHANNEL', int(channels["channels_shadow"]))
            s.setRenderParameter('DO MOTION CHANNEL', int(channels["channels_motion_vector"]))
            s.setRenderParameter('DO ROUGHNESS CHANNEL', int(channels["channels_roughness"]))
            s.setRenderParameter('DO FRESNEL CHANNEL', int(channels["channels_fresnel"]))
            s.setRenderParameter('DO NORMALS CHANNEL', int(channels["channels_normals"]))
            s.setRenderParameter('NORMALS CHANNEL SPACE', channels["channels_normals_space"])
            s.setRenderParameter('POSITION CHANNEL SPACE', channels["channels_position_space"])
            s.setRenderParameter('DO POSITION CHANNEL', int(channels["channels_position"]))
            s.setRenderParameter('DO ZBUFFER CHANNEL', int(channels["channels_z_buffer"]))
            s.setRenderParameter('ZBUFFER RANGE', (channels["channels_z_buffer_near"], channels["channels_z_buffer_far"]))
            s.setRenderParameter('DO DEEP CHANNEL', int(channels["channels_deep"]))
            s.setRenderParameter('DEEP CHANNEL TYPE', channels["channels_deep_type"])
            s.setRenderParameter('DEEP MIN DISTANCE', channels["channels_deep_min_dist"])
            s.setRenderParameter('DEEP MAX SAMPLES', channels["channels_deep_max_samples"])
            s.setRenderParameter('DO UV CHANNEL', int(channels["channels_uv"]))
            # s.setRenderParameter('MOTION CHANNEL TYPE', ?)
            s.setRenderParameter('DO ALPHA CUSTOM CHANNEL', int(channels["channels_custom_alpha"]))
    
    def custom_alphas(self, groups, ):
        """Set custom alphas.
        groups      list of dicts: {'name': string, 'objects': list of strings, 'opaque': bool, }
        """
        s = self.mxs
        for a in groups:
            s.createCustomAlphaChannel(a['name'], a['opaque'])
            for n in a['objects']:
                o = s.getObject(n)
                o.addToCustomAlpha(a['name'])
    
    def hair(self, name, extension, base, pivot, root_radius, tip_radius, data, object_props=None, display_percent=10, display_max=1000, material=None, backface_material=None, ):
        """Create hair/grass object.
        name                string
        extension           string ('MaxwellHair' ,'MGrassP')
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        root_radius         float
        tip_radius          float
        data                dict of extension data
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        display_percent     int
        display_max         int
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryProceduralExtension(extension)
        p = e.getExtensionData()
        p.setByteArray('HAIR_MAJOR_VER', data['HAIR_MAJOR_VER'])
        p.setByteArray('HAIR_MINOR_VER', data['HAIR_MINOR_VER'])
        p.setByteArray('HAIR_FLAG_ROOT_UVS', data['HAIR_FLAG_ROOT_UVS'])
        
        m = memoryview(struct.pack("I", data['HAIR_GUIDES_COUNT'][0])).tolist()
        p.setByteArray('HAIR_GUIDES_COUNT', m)
        m = memoryview(struct.pack("I", data['HAIR_GUIDES_POINT_COUNT'][0])).tolist()
        p.setByteArray('HAIR_GUIDES_POINT_COUNT', m)
        
        c = Cbase()
        c.origin = Cvector(0.0, 0.0, 0.0)
        c.xAxis = Cvector(1.0, 0.0, 0.0)
        c.yAxis = Cvector(0.0, 1.0, 0.0)
        c.zAxis = Cvector(0.0, 0.0, 1.0)
        
        p.setFloatArray('HAIR_POINTS', list(data['HAIR_POINTS']), c)
        p.setFloatArray('HAIR_NORMALS', list(data['HAIR_NORMALS']), c)
        
        p.setUInt('Display Percent', display_percent)
        if(extension == 'MaxwellHair'):
            p.setUInt('Display Max. Hairs', display_max)
            p.setDouble('Root Radius', root_radius)
            p.setDouble('Tip Radius', tip_radius)
        if(extension == 'MGrassP'):
            p.setUInt('Display Max. Hairs', display_max)
            p.setDouble('Root Radius', root_radius)
            p.setDouble('Tip Radius', tip_radius)
        
        o = s.createGeometryProceduralObject(name, p)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(material is not None):
            mat = self.load_material(*material)
            if(mat is not None):
                o.setMaterial(mat)
        if(backface_material is not None):
            mat = self.load_material(*backface_material)
            if(mat is not None):
                o.setBackfaceMaterial(mat)
        
        return o
    
    def texture_data_to_mxparams(self, name, data, mxparams, ):
        d = data
        if(d is None):
            return
        
        # t = mxparams.getTextureMap(name)[0]
        t = CtextureMap()
        t.setPath(d['path'])
        v = Cvector2D()
        v.assign(*d['repeat'])
        t.scale = v
        v = Cvector2D()
        v.assign(*d['offset'])
        t.offset = v
        t.rotation = d['rotation']
        t.uvwChannelID = d['channel']
        t.uIsTiled = d['tile_method_type'][0]
        t.vIsTiled = d['tile_method_type'][1]
        t.uIsMirrored = d['mirror'][0]
        t.vIsMirrored = d['mirror'][1]
        t.invert = d['invert']
        # t.doGammaCorrection = 0
        t.useAbsoluteUnits = d['tile_method_units']
        # t.normalMappingFlipRed = 0
        # t.normalMappingFlipGreen = 0
        # t.normalMappingFullRangeBlue = 0
        t.useAlpha = d['alpha_only']
        t.typeInterpolation = d['interpolation']
        t.saturation = d['saturation']
        t.contrast = d['contrast']
        t.brightness = d['brightness']
        t.hue = d['hue']
        t.clampMin = d['rgb_clamp'][0]
        t.clampMax = d['rgb_clamp'][1]
        t.useGlobalMap = d['use_override_map']
        # t.cosA = 1.000000
        # t.sinA = 0.000000
        ok = mxparams.setTextureMap(name, t)
        return mxparams
    
    def grass(self, name, object_name, properties, material=None, backface_material=None, ):
        """Create grass object modifier extension.
        name                string
        object_name         string
        properties          dict of many, many properties, see code..
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryModifierExtension('MaxwellGrass')
        p = e.getExtensionData()
        
        if(material is not None):
            mat = self.load_material(*material)
            if(mat is not None):
                p.setString('Material', mat.getName())
        if(backface_material is not None):
            mat = self.load_material(*backface_material)
            if(mat is not None):
                p.setString('Double Sided Material', bmat.getName())
        
        p.setUInt('Density', properties['density'])
        self.texture_data_to_mxparams('Density Map', properties['density_map'], p, )
        
        p.setFloat('Length', properties['length'])
        self.texture_data_to_mxparams('Length Map', properties['length_map'], p, )
        p.setFloat('Length Variation', properties['length_variation'])
        
        p.setFloat('Root Width', properties['root_width'])
        p.setFloat('Tip Width', properties['tip_width'])
        
        p.setUInt('Direction Type', properties['direction_type'])
        
        p.setFloat('Initial Angle', properties['initial_angle'])
        p.setFloat('Initial Angle Variation', properties['initial_angle_variation'])
        self.texture_data_to_mxparams('Initial Angle Map', properties['initial_angle_map'], p, )
        
        p.setFloat('Start Bend', properties['start_bend'])
        p.setFloat('Start Bend Variation', properties['start_bend_variation'])
        self.texture_data_to_mxparams('Start Bend Map', properties['start_bend_map'], p, )
        
        p.setFloat('Bend Radius', properties['bend_radius'])
        p.setFloat('Bend Radius Variation', properties['bend_radius_variation'])
        self.texture_data_to_mxparams('Bend Radius Map', properties['bend_radius_map'], p, )
        
        p.setFloat('Bend Angle', properties['bend_angle'])
        p.setFloat('Bend Angle Variation', properties['bend_angle_variation'])
        self.texture_data_to_mxparams('Bend Angle Map', properties['bend_angle_map'], p, )
        
        p.setFloat('Cut Off', properties['cut_off'])
        p.setFloat('Cut Off Variation', properties['cut_off_variation'])
        self.texture_data_to_mxparams('Cut Off Map', properties['cut_off_map'], p, )
        
        p.setUInt('Points per Blade', properties['points_per_blade'])
        p.setUInt('Primitive Type', properties['primitive_type'])
        
        p.setUInt('Seed', properties['seed'])
        
        p.setByte('Enable LOD', properties['lod'])
        p.setFloat('LOD Min Distance', properties['lod_min_distance'])
        p.setFloat('LOD Max Distance', properties['lod_max_distance'])
        p.setFloat('LOD Max Distance Density', properties['lod_max_distance_density'])
        
        p.setUInt('Display Percent', properties['display_percent'])
        p.setUInt('Display Max. Blades', properties['display_max_blades'])
        
        o = s.getObject(object_name)
        o.applyGeometryModifierExtension(p)
        return o
    
    def particles(self, name, properties, base, pivot, object_props=None, material=None, backface_material=None, ):
        """Create particles object.
        name                string
        properties          dict
        base                ((3 float), (3 float), (3 float), (3 float))
        pivot               ((3 float), (3 float), (3 float), (3 float))
        object_props        (bool hide, float opacity, tuple cid=(int, int, int), bool hcam, bool hcamsc, bool hgi, bool hrr, bool hzcp, ) or None
        material            (string path, bool embed) or None
        backface_material   (string path, bool embed) or None
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryProceduralExtension('MaxwellParticles')
        p = e.getExtensionData()
        d = properties
        
        p.setString('FileName', d['filename'])
        p.setFloat('Radius Factor', d['radius_multiplier'])
        p.setFloat('MB Factor', d['motion_blur_multiplier'])
        p.setFloat('Shutter 1/', d['shutter_speed'])
        p.setFloat('Load particles %', d['load_particles'])
        p.setUInt('Axis', d['axis_system'])
        p.setInt('Frame#', d['frame_number'])
        p.setFloat('fps', d['fps'])
        p.setInt('Create N particles per particle', d['extra_create_np_pp'])
        p.setFloat('Extra particles dispersion', d['extra_dispersion'])
        p.setFloat('Extra particles deformation', d['extra_deformation'])
        p.setByte('Load particle Force', d['load_force'])
        p.setByte('Load particle Vorticity', d['load_vorticity'])
        p.setByte('Load particle Normal', d['load_normal'])
        p.setByte('Load particle neighbors no.', d['load_neighbors_num'])
        p.setByte('Load particle UV', d['load_uv'])
        p.setByte('Load particle Age', d['load_age'])
        p.setByte('Load particle Isolation Time', d['load_isolation_time'])
        p.setByte('Load particle Viscosity', d['load_viscosity'])
        p.setByte('Load particle Density', d['load_density'])
        p.setByte('Load particle Pressure', d['load_pressure'])
        p.setByte('Load particle Mass', d['load_mass'])
        p.setByte('Load particle Temperature', d['load_temperature'])
        p.setByte('Load particle ID', d['load_id'])
        p.setFloat('Min Force', d['min_force'])
        p.setFloat('Max Force', d['max_force'])
        p.setFloat('Min Vorticity', d['min_vorticity'])
        p.setFloat('Max Vorticity', d['max_vorticity'])
        p.setInt('Min Nneighbors', d['min_nneighbors'])
        p.setInt('Max Nneighbors', d['max_nneighbors'])
        p.setFloat('Min Age', d['min_age'])
        p.setFloat('Max Age', d['max_age'])
        p.setFloat('Min Isolation Time', d['min_isolation_time'])
        p.setFloat('Max Isolation Time', d['max_isolation_time'])
        p.setFloat('Min Viscosity', d['min_viscosity'])
        p.setFloat('Max Viscosity', d['max_viscosity'])
        p.setFloat('Min Density', d['min_density'])
        p.setFloat('Max Density', d['max_density'])
        p.setFloat('Min Pressure', d['min_pressure'])
        p.setFloat('Max Pressure', d['max_pressure'])
        p.setFloat('Min Mass', d['min_mass'])
        p.setFloat('Max Mass', d['max_mass'])
        p.setFloat('Min Temperature', d['min_temperature'])
        p.setFloat('Max Temperature', d['max_temperature'])
        p.setFloat('Min Velocity', d['min_velocity'])
        p.setFloat('Max Velocity', d['max_velocity'])
        
        o = s.createGeometryProceduralObject(name, p)
        
        self.set_base_and_pivot(o, base, pivot, )
        if(object_props is not None):
            self.set_object_props(o, *object_props)
        
        if(material is not None):
            mat = self.load_material(*material)
            if(mat is not None):
                o.setMaterial(mat)
        if(backface_material is not None):
            mat = self.load_material(*backface_material)
            if(mat is not None):
                o.setBackfaceMaterial(mat)
        
        return o
    
    def subdivision(self, object_name, level=2, scheme=0, interpolation=2, crease=0.0, smooth_angle=math.radians(90.0), ):
        """Create subdivision object modifier extension.
        object_name     string
        level           int
        scheme          int     (0, "Catmull-Clark"), (1, "Loop")
        interpolation   int     (0, "None"), (1, "Edges"), (2, "Edges And Corners"), (3, "Sharp")
        crease          float
        smooth          float
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryModifierExtension('SubdivisionModifier')
        p = e.getExtensionData()
        
        p.setUInt('Subdivision Level', level)
        p.setUInt('Subdivision Scheme', scheme)
        p.setUInt('Interpolation', interpolation)
        p.setFloat('Crease', crease)
        p.setFloat('Smooth Angle', smooth_angle)
        
        o = s.getObject(object_name)
        o.applyGeometryModifierExtension(p)
        return o
    
    def scatter(self, object_name, scatter_object, inherit_objectid=False, density=None, seed=0, scale=None, rotation=None, lod=None, display_percent=10, display_max=1000, ):
        """Create scatter object modifier extension.
        object_name                 string
        scatter_object              string
        inherit_objectid            bool
        density                     (float, density_map or None) or None
        seed                        int
        scale                       ((float, float, float), scale_map or None, scale_variation (float, float, float)) or None
        rotation                    ((float, float, float), rotation_map or None, rotation_variation (float, float, float), rotation_direction int (0, "Polygon Normal"), (1, "World Z")) or None
        lod                         (bool, lod_min_distance float, lod_max_distance float, lod_max_distance_density float) or None
        display_percent             int
        display_max                 int
        """
        s = self.mxs
        e = self.mgr.createDefaultGeometryModifierExtension('MaxwellScatter')
        p = e.getExtensionData()
        
        p.setString('Object', scatter_object)
        p.setByte('Inherit ObjectID', inherit_objectid)
        if(density is not None):
            p.setFloat('Density', density[0])
            self.texture_data_to_mxparams('Density Map', density[1], p, )
        p.setUInt('Seed', seed)
        if(scale is not None):
            p.setFloat('Scale X', scale[0][0])
            p.setFloat('Scale Y', scale[0][1])
            p.setFloat('Scale Z', scale[0][2])
            self.texture_data_to_mxparams('Scale Map', scale[1], p, )
            p.setFloat('Scale X Variation', scale[2][0])
            p.setFloat('Scale Y Variation', scale[2][1])
            p.setFloat('Scale Z Variation', scale[2][2])
        if(rotation is not None):
            p.setFloat('Rotation X', rotation[0][0])
            p.setFloat('Rotation Y', rotation[0][1])
            p.setFloat('Rotation Z', rotation[0][2])
            self.texture_data_to_mxparams('Rotation Map', rotation[1], p, )
            p.setFloat('Rotation X Variation', rotation[2][0])
            p.setFloat('Rotation Y Variation', rotation[2][1])
            p.setFloat('Rotation Z Variation', rotation[2][2])
            p.setUInt('Direction Type', rotation[3])
        if(lod is not None):
            p.setByte('Enable LOD', lod[0])
            p.setFloat('LOD Min Distance', lod[1])
            p.setFloat('LOD Max Distance', lod[2])
            p.setFloat('LOD Max Distance Density', lod[3])
        p.setUInt('Display Percent', display_percent)
        p.setUInt('Display Max. Blades', display_max)
        
        o = s.getObject(object_name)
        o.applyGeometryModifierExtension(p)
        return o
    
    def write(self):
        """Write scene fo file."""
        log("saving scene..", 2)
        ok = self.mxs.writeMXS(self.path)
        log("done.", 2)
        return ok


def read_mxm_preview(path):
    import numpy
    s = Cmaxwell(mwcallback)
    m = s.readMaterial(path)
    a = m.getPreview()[0]
    r = numpy.copy(a)
    return r
