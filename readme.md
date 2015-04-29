# **Maxwell Render integration for Blender**

![teaser](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr2.jpg)

### features:

* Works on Mac OS X. Linux and Windows is in testing and debugging stage..
* Compatible with Maxwell Render 3.1.0.0 and Blender 2.74
* UI as close to Maxwell Studio as possible
* All renderable geometry (except Metaballs)
* Object hierarchy (not renderable objects are removed unless they have renderable child objects)
* Mesh objects using the same mesh data are exported as instances (optional)
* MXS references
* Dupli verts and faces
* Multiple UV channels
* Material assignment (including backface materials) and multiple materials per object
* Material creation and editing with Mxed
* Cameras
* Render parameters
* All render channels including Custom Alphas
* Environment parameters (Sun can be optionally set by Sun lamp)
* Object parameters
* Maxwell Extensions: Particles, Grass, Hair, Scatter, Subdivision, Sea, Cloner
* Wireframe scene export (all edges are converted to instanced cylinder of user defined radius)

![ui](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr.png)

### addon installation - Mac OS X:

* Download Maxwell Render 3.1.0 from [http://maxwellrender.com/](http://maxwellrender.com/) and install to ```/Applications```
* Download python 3.4.1 from [https://www.python.org/downloads/release/python-341/](https://www.python.org/downloads/release/python-341/) and install
* Copy ```_pymaxwell.so``` and ```pymaxwell.py``` from ```/Applications/Maxwell 3/Libs/pymaxwell/python3.4/``` to ```/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/```
* Download this repository clicking 'Download ZIP', extract, rename directory to ```render_maxwell``` and put to ```~/Library/Application Support/Blender/2.74/scripts/addons/```
* Start Blender, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

### addon installation - Windows:

**WARNING: still highly experimental, expect bugs** (tested on Windows 8.1 64)

* Install Maxwell Render
* Download this repository clicking 'Download ZIP', extract, rename directory to ```render_maxwell``` and put to ```C:\Users\USERNAME\AppData\Roaming\Blender Foundation\Blender\2.74\scripts\addons\```
* Start Blender, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

### addon installation - Linux:

**WARNING: still highly experimental, expect bugs** (tested on Ubuntu 14.04.2 LTS 64)

* Install Maxwell Render
* append this ```export LD_LIBRARY_PATH=$MAXWELL3_ROOT:$LD_LIBRARY_PATH``` to your .bashrc AFTER generated stuff from Maxwell installation, after MAXWELL3_ROOT is exported
* to fix complains of some extensions, install ```libtbb-dev```, but this step might be optional, it is used by extension not supported in addon
* Download this repository clicking 'Download ZIP', extract, rename directory to ```render_maxwell``` and put to ```~/.config/blender/2.74/scripts/addons/```
* Start Blender from terminal, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header


***

changelog:

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
