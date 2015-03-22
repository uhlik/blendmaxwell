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
* Mesh objects using the same mesh data are exported as instances
* Dupli verts and faces
* Multiple UV channels
* Material assignment (including backface materials) and multiple materials per object
* Material creation and editing with Mxed
* Cameras
* Render parameters
* All render channels including Custom Alphas
* Environment parameters
* Object parameters
* Maxwell Particles with Realflow .bin, currently without animation support
* Wireframe scene export (all edges are converted to instanced cylinder of user defined radius)

![ui](https://raw.githubusercontent.com/uhlik/bpy/master/x/bmr.png)

### installation - Mac OS X:

* Download Maxwell Render 3.1.0 from [http://maxwellrender.com/](http://maxwellrender.com/) and install to ```/Applications```
* Download python 3.4.1 from [https://www.python.org/downloads/release/python-341/](https://www.python.org/downloads/release/python-341/) and install
* Copy ```_pymaxwell.so``` and ```pymaxwell.py``` from ```/Applications/Maxwell 3/Libs/pymaxwell/python3.4/``` to ```/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/site-packages/```
* Download this repository clicking 'Download ZIP', extract, rename directory to ```render_maxwell``` and put to ```~/Library/Application Support/Blender/2.74/scripts/addons/```
* Start Blender, go to User Preferences > Add-ons, search for 'Maxwell Render' in Render category and enable it, then choose 'Maxwell Render' from render engines list in Info panel header

***

changelog:

* 0.1.3 first release

***

footnotes:

* Maxwell Render python bindings, "pymaxwell", provided by Next Limit is not compatible with python used in Blender. It can't be loaded directly and this is why separate python 3 installation is needed and exporting is done in two steps. What happens internally is, blender scene is serialized to JSON and custom binary mesh format to temporary directory together with extra python script which is then run with system python and creates Maxwell scene file using pymaxwell. It's a bit slower, but what is a few minutes extra in unbiased rendering anyway..

