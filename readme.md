# **blendmaxwell**
#### Maxwell Render exporter for Blender

![teaser](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr2.jpg)

### features:

* Works on Mac OS X, Linux and Windows
* Compatible with Maxwell Render 3.2 (more precisely current beta 3.1.99.10) and Blender 2.76
* UI as close to Maxwell Studio as possible
* All renderable geometry (except Metaballs)
* Object hierarchy (not renderable objects are removed unless they have renderable child objects)
* Mesh objects using the same mesh data (and renderable Curves) are exported as instances (optional)
* MXS references
* Dupli verts, faces and group
* Multiple UV channels
* Material assignment (including backface materials) and multiple materials per object
* Extension Materials creation and editing inside Blender
* Custom Material creation and editing with Mxed
* Cameras
* Render parameters
* All render channels including Custom Alphas
* Environment parameters (Sun can be optionally set by Sun lamp)
* Object parameters
* Maxwell Extensions: Particles, Grass, Hair, Scatter, Subdivision, Sea, Cloner, Volumetrics
* Export Subdivision modifiers if their type is Catmull-Clark and they are at the end of modifier stack on regular mesh objects (optional)
* Wireframe scene export (all edges are converted to instanced cylinder of user defined radius)
* Scene import (objects, emitters, cameras and sun selectively)

![ui](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr.png)

### addon installation - Mac OS X:

* Maxwell must be installed in usual place i.e. ```/Applications/Maxwell 3```
* Download python 3.4.1 from [https://www.python.org/downloads/release/python-341/](https://www.python.org/downloads/release/python-341/) and install
* Download this repository clicking 'Download ZIP', extract, rename directory to ```blendmaxwell``` and put to ```~/Library/Application Support/Blender/2.76/scripts/addons/```
* Start Blender, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header
* if you are updating from version before 0.3.3, please remove ```_pymaxwell.so``` and ```pymaxwell.py``` from ```/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages``` it is no longer necessary and it might cause conflicts

### addon installation - Windows:

* Download this repository clicking 'Download ZIP', extract, rename directory to ```blendmaxwell``` and put to ```C:\Users\USERNAME\AppData\Roaming\Blender Foundation\Blender\2.76\scripts\addons\```
* Start Blender, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

### addon installation - Linux:

* append this ```export LD_LIBRARY_PATH=$MAXWELL3_ROOT:$LD_LIBRARY_PATH``` to your .bashrc AFTER generated stuff from Maxwell installation, after MAXWELL3_ROOT is exported
* to fix complains of some extensions, install ```libtbb-dev```, but this step might be optional, it is used by extension not supported in addon
* Download this repository clicking 'Download ZIP', extract, rename directory to ```blendmaxwell``` and put to ```~/.config/blender/2.76/scripts/addons/```
* Start Blender from terminal, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header


***

changelog:

* 0.3.4 hair with children particles root uvs (requires blender 2.76), wire export faster and with smaller files, fixes here and there
* 0.3.3 simplified installation procedure on Mac OS X, pymaxwell is now imported directly from ```/Applications/Maxwell 3```, also fixed some bugs..
* 0.3.2 Maxwell 3.2 update, includes majority of new features: material priority, saving to psd, reflection and refraction channels, reflectance channel, scatter and grass updates. also wireframe and auto-subdivision export is restored, added basic progress reporting, hair uvs, hair extension material and many more small fixes and tweaks
* 0.3.1 last version working with Maxwell 3.1: [ddbad692a25c6e6e72d11092d8f063f6ed1d048e](https://github.com/uhlik/blendmaxwell/tree/ddbad692a25c6e6e72d11092d8f063f6ed1d048e)
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

links:

[blenderartist.org thread](http://blenderartists.org/forum/showthread.php?366067-Maxwell-Render-integration-for-Blender-%28different-one%29)

[maxwellrender.com/forum thread](http://www.maxwellrender.com/forum/viewtopic.php?f=138&t=43385)
