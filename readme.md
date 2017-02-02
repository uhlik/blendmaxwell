# **blendmaxwell**
#### Maxwell Render 3 exporter for Blender

![teaser](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr2.jpg)

### notice

This exporter addon is for **Maxwell Render 3** series only, compatible with version 3.2.1.3 and later

### features:

* Works on Mac OS X, Linux and Windows
* Compatible with Maxwell Render 3 version 3.2.1.3+ and Blender 2.77a+
* UI as close to Maxwell Studio as possible
* All renderable geometry (except Metaballs)
* Object hierarchy (not renderable objects are removed unless they have renderable child objects)
* Mesh objects using the same mesh data (and renderable Curves) are exported as instances (optional)
* MXS references with viewport preview
* Dupli verts, faces and group
* Multiple UV channels
* Custom and Extension Material creation and editing inside Blender or with Mxed
* Save and load Custom and Extension Materials from or to Blender material editor
* Material assignment (including backface materials) and multiple materials per object
* Extension Materials creation and editing inside Blender
* Maxwell procedural textures
* Material preview rendering
* Viewport rendering (not interactive)
* Cameras
* Render parameters
* All render channels including Custom Alphas
* Environment parameters (Sun can be optionally set by Sun lamp)
* Object parameters
* Export objects and cameras for movement and deformation blur
* Maxwell Extensions: Particles, Grass, Hair, Scatter, Subdivision, Sea, Cloner, Volumetrics
* Export Subdivision modifiers if their type is Catmull-Clark and they are at the end of modifier stack on regular mesh objects (optional)
* Scene import (objects, emitters, cameras and sun selectively)

![ui](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr.png)

### addon installation - Mac OS X:

* Maxwell must be installed in usual place i.e. ```/Applications/Maxwell 3```
* Download python 3.5.1 from [https://www.python.org/downloads/release/python-351/](https://www.python.org/downloads/release/python-351/) and install
* Download this repository clicking 'Download ZIP', extract, rename directory to ```blendmaxwell``` and put to ```~/Library/Application Support/Blender/*BLENDER_VERSION*/scripts/addons/```
* Start Blender, go to User Preferences > Add-ons, search for 'blendmaxwell' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

### addon installation - Windows:

* Download this repository clicking 'Download ZIP', extract, rename directory to ```blendmaxwell``` and put to ```C:\Users\USERNAME\AppData\Roaming\Blender Foundation\Blender\*BLENDER_VERSION*\scripts\addons\```
* Start Blender, go to User Preferences > Add-ons, search for 'blendmaxwell' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

### addon installation - Linux:

* Append this ```export LD_LIBRARY_PATH=$MAXWELL3_ROOT:$LD_LIBRARY_PATH``` to your .bashrc after generated stuff from Maxwell installation, i.e. after ```MAXWELL3_ROOT``` is exported
* To fix complains of some extensions, install ```libtbb-dev```, but this step might be optional, it is used by extension not supported in addon
* Download this repository clicking 'Download ZIP', extract, rename directory to ```blendmaxwell``` and put to ```~/.config/blender/*BLENDER_VERSION*/scripts/addons/```
* Start Blender from terminal, go to User Preferences > Add-ons, search for 'blendmaxwell' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

#### installation notes:

* In case of problem with presets (emitters, extension materials, ..., ), remove on **Mac OS X**: ```~/Library/Application Support/Blender/*BLENDER_VERSION*/scripts/presets/blendmaxwell```, on **Windows**: ```C:\Users\USERNAME\AppData\Roaming\Blender Foundation\Blender\*BLENDER_VERSION*\scripts\presets\blendmaxwell```, or on **Linux**: ```~/.config/blender/*BLENDER_VERSION*/scripts/presets/blendmaxwell``` and restart Blender. default presets will be recreated automatically.

#### known issues:
* Due to changes in Blender's triangulation operator, Maxwell Subdivision modifier is disabled.


***

**changelog:**

* 0.4.5 support for vertex-per-face normals, mesh auto-smooth, split normals etc., added text overlay, disabled subdivision modifier until fixed
* 0.4.4 material preview and viewport (not interactive) rendering, mxs import with mxs references
* 0.4.3 critical fix: smooth faces export, experimental feature: material preview rendering (currently Mac OS X only)
* 0.4.2 movement and deformation blur, faster mesh export
* 0.4.1 procedural textures, faster reading of mxs references
* 0.4.0 heavy refactoring, added mxs reference viewport preview
* 0.3.9 colors exported in 32 bits and as shown in blender (gamma correction), added grass modifier presets, added displacement in extension materials, added stereo cameras (maxwell 3.2), added realflow particles bin export operator (file > export menu), updated material presets (maxwell 3.2.1.0), fixed cleaning of mesh datablocks created during export, fixed exporting of fake user materials, fixed export of particles on meshes without polygons (and a lot of small fixes and ui tweaks)
* 0.3.8 custom alphas for objects and materials, many ui improvements, particle object/group instances now exports correctly when base objects are hidden, addon preferences for automatic type selection for new material, environment and particles, changed preset location, setting camera to ortho now changes viewport to ortho
* 0.3.7 custom material editor, custom material import/export
* 0.3.6 added: export particle uvs, camera lock exposure, choosing external materials with mxed in browser mode, choose scene for auto preview in mxed, fixed: import mxs: object transformation
* 0.3.5 particle object/group instances, quick setting object properties/object id to multiple objects, blocked emitters, many fixes (reading/drawing material previews, missing cloner objects, hair uvs, ...)
* 0.3.4 hair with children particles root uvs (requires blender 2.76), wire export faster and with smaller files, fixes here and there
* 0.3.3 simplified installation procedure on Mac OS X, pymaxwell is now imported directly from ```/Applications/Maxwell 3```, also fixed some bugs..
* 0.3.2 Maxwell 3.2 update, includes majority of new features: material priority, saving to psd, reflection and refraction channels, reflectance channel, scatter and grass updates. also wireframe and auto-subdivision export is restored, added basic progress reporting, hair uvs, hair extension material and many more small fixes and tweaks
* 0.3.1 last version working with Maxwell 3.1 (with a few bugs): [ddbad692a25c6e6e72d11092d8f063f6ed1d048e](https://github.com/uhlik/blendmaxwell/tree/ddbad692a25c6e6e72d11092d8f063f6ed1d048e)
* 0.3.0 refactored exporter part, added: hair uvs, curves instancing, material global properties, fixed: object transformations when opened and saved in Studio
* 0.2.4 added: automatic subdivision modifiers export to speed things up
* 0.2.3 added: mxs export menu operator, quad export when using subdivision modifier, 2.75 compatibility
* 0.2.2 added: mxs import (objects, emitters, cameras and sun selectively), save extension materials to mxm, embed particles in mxs (saving of external .bin files is now optional)
* 0.2.1 added: extension materials creation and editing inside blender
* 0.2.0 added: much faster large mesh export on Mac OS X, Extra Sampling panel, Volumetrics extension (constant and noise 3d), external particle bin works with animation export
* 0.1.9 added: MXS References, Windows installation simplified
* 0.1.8 added: Linux and Windows support, cloner extension, lots of refactoring
* 0.1.7 added: presets, texture panel, basic material preview, RFBin export with size per particle, lots of refactoring, Linux and Windows ports are working without extensions
* 0.1.6 added: maxwell hair, subdivision, scatter and particles export as realflow bin, fixed: render shortcuts, ui spaceing
* 0.1.5 added: maxwell grass modifier, incremental export, minor ui tweaks and additions, launch multiple instances of maxwell and studio, fixed: material placeholders on triangle groups, maxwell particles transformation, error reporting
* 0.1.4 added: render layers panel, fixed: path handling, instance bases on hidden layers and many more
* 0.1.3 first release

***

**links:**

[blenderartist.org forum thread](http://blenderartists.org/forum/showthread.php?366067-Maxwell-Render-integration-for-Blender-%28different-one%29)

[maxwellrender.com forum thread](http://www.maxwellrender.com/forum/viewtopic.php?f=138&t=43385)
