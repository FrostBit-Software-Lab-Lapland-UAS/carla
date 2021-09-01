# WinterSim Project - CARLA Simulator

-------

The vision of WinterSim project is to renew the services and products of smart and autonomous vehicles. The main goal is to produce research and data about the functionality of the most common sensors in vehicles in winter conditions by utilizing game engine technologies.

![Thumbnail](https://github.com/FrostBit-Software-Lab-Lapland-UAS/carla/blob/wintersim/master/Docs/wintersim/WinterSim_Thumbnail.gif)

[Learn more about WinterSim Project](https://wintersim.fi/)

## What is Carla Simulator?

-------

CARLA is an open-source simulator for autonomous driving research. CARLA has been developed from the ground up to support development, training, and validation of autonomous driving systems. In addition to open-source code and protocols, CARLA provides open digital assets (urban layouts, buildings, vehicles) that were created for this purpose and can be used freely. The simulation platform supports flexible specification of sensor suites and environmental conditions.

[Learn more about CARLA Simulator](http://carla.org/) 

[Carla GitHub](https://github.com/carla-simulator/carla)

## WinterSim Releases

-------

WinterSim Release Installation Guide:

1. Download [wintersim.zip](https://a3s.fi/swift/v1/AUTH_8811c563a60e4395828a2393f44e064b/Releases/wintersim.zip)

2. Download and install [Python 3.7](https://www.python.org/downloads/release/python-370/) (tick checkbox “add Python 3.7 to PATH”)

3. Unzip wintersim.zip

4. Open Terminal and locate to wintersim/WindowsNoEditor/PythonAPI/wintersim_examples folder and install all necessary packages with following command

  ```
    pip install -r requirements.txt
  ```
  
5. Inside wintersim/WindowsNoEditor folder double click CarlaUE4.exe to start simulation

6. Inside wintersim/WindowsNoEditor/PythonAPI/wintersim_examples folder there are few example scripts. Run following script in Terminal to join simulation.

  ```
    python wintersim_control.py
  ```

### Recommended system


 - Intel i7 gen 9th - 11th / Intel i9 gen 9th - 11th / AMD ryzen 7 / AMD ryzen 9

 - +16 GB RAM memory

 - NVIDIA RTX 2070 / NVIDIA RTX 2080 / NVIDIA RTX 3070, NVIDIA RTX 3080

 - Windows 10 / Windows 11


Licenses
-------
#### FrostBit Software Lab license

FrostBit Software Lab specific code is distributed under MIT License.

#### CARLA licenses

CARLA specific code is distributed under MIT License.

CARLA specific assets are distributed under CC-BY License.

#### CARLA Dependency and Integration licenses

The ad-rss-lib library compiled and linked by the [RSS Integration build variant](Docs/adv_rss.md) introduces [LGPL-2.1-only License](https://opensource.org/licenses/LGPL-2.1).

Unreal Engine 4 follows its [own license terms](https://www.unrealengine.com/en-US/faq).

CARLA uses three dependencies as part of the SUMO integration:
- [PROJ](https://proj.org/), a generic coordinate transformation software which uses the [X/MIT open source license](https://proj.org/about.html#license).
- [SQLite](https://www.sqlite.org), part of the PROJ dependencies, which is [in the public domain](https://www.sqlite.org/purchase/license).
- [Xerces-C](https://xerces.apache.org/xerces-c/), a validating XML parser, which is made available under the [Apache Software License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html).

CARLA uses one dependency as part of the Chrono integration:
- [Eigen](https://eigen.tuxfamily.org/index.php?title=Main_Page), a C++ template library for linear algebra which uses the [MPL2 license](https://www.mozilla.org/en-US/MPL/2.0/).

CARLA uses the Autodesk FBX SDK for converting FBX to OBJ in the import process of maps. This step is optional, and the SDK is located [here](https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-0)

This software contains Autodesk® FBX® code developed by Autodesk, Inc. Copyright 2020 Autodesk, Inc. All rights, reserved. Such code is provided "as is" and Autodesk, Inc. disclaims any and all warranties, whether express or implied, including without limitation the implied warranties of merchantability, fitness for a particular purpose or non-infringement of third party rights. In no event shall Autodesk, Inc. be liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including, but not limited to, procurement of substitute goods or services; loss of use, data, or profits; or business interruption) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of such code."
