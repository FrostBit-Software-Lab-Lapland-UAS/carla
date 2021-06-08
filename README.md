# WinterSim Project - CARLA Simulator

-------

The vision of WinterSim project is to renew the services and products of smart and autonomous vehicles. The main goal is to produce research and data about the functionality of the most common sensors in vehicles in winter conditions by utilizing game engine technologies.

[Learn more about WinterSim Project](https://wintersim.fi/)

## What is Carla Simulator?

-------

CARLA is an open-source simulator for autonomous driving research. CARLA has been developed from the ground up to support development, training, and validation of autonomous driving systems. In addition to open-source code and protocols, CARLA provides open digital assets (urban layouts, buildings, vehicles) that were created for this purpose and can be used freely. The simulation platform supports flexible specification of sensor suites and environmental conditions.

[Learn more about CARLA Simulator](http://carla.org/)


## WinterSim Releases

-------

WinterSim Release 1.0.0 installation guide

1. Download [wintersim.zip](https://a3s.fi/swift/v1/AUTH_8811c563a60e4395828a2393f44e064b/Releases/wintersim.zip)

2. Download and install [Python 3.7](https://www.python.org/downloads/release/python-370/) (tick checkbox “add Python 3.7 to PATH”)

3. Unzip wintersim_muonio_1.0.0.zip

4. Open Terminal and locate to Muonio/WindowsNoEditor/PythonAPI/wintersim_examples folder and install all necessary packages with following command

  ```
    pip install -r requirements.txt
  ```
  
5. Inside Muonio/WindowsNoEditor folder double click CarlaUE4.exe to start simulation

6. Inside Muonio/WindowsNoEditor/PythonAPI/wintersim_examples folder there are few example scripts. Run either script to join simulation. Each script should be run in one Terminal window.

  ```
    python wintersim_control.py
  ```
  
  ```
    python weather_control.py
  ```

### Recommended system


 - Intel i7 gen 9th - 11th / Intel i9 gen 9th - 11th / AMD ryzen 7 / AMD ryzen 9

 - +16 GB RAM memory

 - NVIDIA RTX 2070 / NVIDIA RTX 2080 / NVIDIA RTX 3070, NVIDIA RTX 3080

 - Windows 10


License
-------

CARLA and WinterSim specific code is distributed under MIT License.

CARLA specific assets are distributed under CC-BY License.

Note that UE4 itself follows its own license terms.
