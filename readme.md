# **Maxwell Render integration for Blender**

![teaser](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr2.jpg)

### important notice:

* **currently it works only on Mac OS X**
* it might work with a little effort on Linux, this is currently on TODO list
* Windows support is planned in the not so distant future, as time allows and some windows machine appears in my neighbourhood..

### features:

* Compatible with Maxwell Render 3.1.0.0 and Blender 2.74
* UI as close to Maxwell Studio as possible
* All renderable geometry (except Metaballs)
* Object hierarchy (not renderable objects are removed unless they have renderable child objects)
* Mesh objects using the same mesh data are exported as instances (optional)
* Dupli verts and faces
* Multiple UV channels
* Material assignment (including backface materials) and multiple materials per object
* Material creation and editing with Mxed
* Cameras
* Render parameters
* All render channels including Custom Alphas
* Environment parameters (Sun can be optionally set by Sun lamp)
* Object parameters
* Maxwell Extensions: Particles, Grass, Hair, Scatter, Subdivision
* Wireframe scene export (all edges are converted to instanced cylinder of user defined radius)

![ui](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr.png)

### addon installation - Mac OS X:

* Download Maxwell Render 3.1.0 from [http://maxwellrender.com/](http://maxwellrender.com/) and install to ```/Applications```
* Download python 3.4.1 from [https://www.python.org/downloads/release/python-341/](https://www.python.org/downloads/release/python-341/) and install
* Copy ```_pymaxwell.so``` and ```pymaxwell.py``` from ```/Applications/Maxwell 3/Libs/pymaxwell/python3.4/``` to ```/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/```
* Download this repository clicking 'Download ZIP', extract, rename directory to ```render_maxwell``` and put to ```~/Library/Application Support/Blender/2.74/scripts/addons/```
* Start Blender, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

### to update addon - Mac OS X:

* Start Blender, disable addon in User Preferences, hit 'Save User Settings' and quit
* Remove ```~/Library/Application Support/Blender/2.74/scripts/addons/render_maxwell```
* Download this repository clicking 'Download ZIP', extract, rename directory to ```render_maxwell``` and put to ```~/Library/Application Support/Blender/2.74/scripts/addons/```
* Start Blender again, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

***

changelog:

* 0.1.7 added: presets, texture panel, basic material preview, RFBin export with size per particle, lots of refactoring, Linux and Windows ports are working without extensions
* 0.1.6 added: maxwell hair, subdivision, scatter and particles export as realflow bin, fixed: render shortcuts, ui spaceing
* 0.1.5 added: maxwell grass modifier, incremental export, minor ui tweaks and additions, launch multiple instances of maxwell and studio, fixed: material placeholders on triangle groups, maxwell particles transformation, error reporting
* 0.1.4 added: render layers panel, fixed: path handling, instance bases on hidden layers and many more
* 0.1.3 first release

***

links:

[blenderartist.org thread](http://blenderartists.org/forum/showthread.php?366067-Maxwell-Render-integration-for-Blender-%28different-one%29)

[maxwellrender.com/forum thread](http://www.maxwellrender.com/forum/viewtopic.php?f=138&t=43385)
