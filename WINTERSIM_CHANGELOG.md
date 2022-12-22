
## WinterSim Release 1.20
 * Upgraded to CARLA version 0.9.13
 * Added new Rovaniemi map
 * Added Muonio_Extended map (10 km long road!) 
 * Added retroreflective materials on traffic signs, poles ect. 
   Based on https://github.com/RDTG/UnrealEngineRetroreflections. Copyrights notice on in carla root folder.
 * Added glittering snow effect
 * Added dirty snow
 * Added lidar noise formula for intensity
 * Added lidar noise formula for distance measurement
 * Updated lidar noise model formula for snowflake detection
 * Moved from custom/manual sun position system to Unreal Engine Sun Position Calculate plugin which calculates geographically accurate       sun position by providing time, day, month and year 
 * Fixed issue where Wind didn’t affect tree rotations properly 
 * New ‘ice’ camera lens effect (not enabled by default)
 * Performance and visual imporvements 
 * WinterSim specific Python API extensions: 
   New camera attributes: 
   blueprintref.set_attribute(‘camera_ice_effect’), str(bool), default False 
   blueprintref.set_attribute(‘camera_ice_effect_rotation’), string (right, left, top, down), default “up” 
   blueprintref.set_attribute(‘camera_ice_effect_strength’), float (0.0 - 20.0), default 1.2 
 * Expanded weather parameters to include: Time, Day, Month, Road snowiness, snow dirtyness, Timezone  
 * Wintersim Control.py changes: 
 * Adjusted multisensorview camera sensors fov’s 
 * Added more multisensorview angles/views 
 * Removed many unneeded imports 
 * Fixed issue where wintersim_control separate Open3DLidar window (F9 key) fall/lagged behind. 
 * Fixed issue where multisensorview lidars used wrong lidar class 
 * Added new launch argument to switch map (-m, --m, -map, --map) 
 * Added ability to change multi sensor view sensors when multi sensor view is enabled (keys: 1-3) 
 * Weather_control.py changes: 
 * Fixed issue where changing tire friction modified other vehicle physics values 
 * Changed wind direction from angles to compass names 
 * Added sliders for: 
 * Day, Month, road snowiness, snow dirtyness and cloudiness 

## WinterSim Release 1.10
 * Upgraded to CARLA version 0.9.12 
 * Added new vehicles (van, pickup, wagon, bus)
 * Added winter clothes to NPC’s 
 * Added more snowbanks variations 
 * Added and improved weather controlling (weather_control.py) 
 * Added relative humidity and dewpoint to weather parameters 
 * Added new tiretrack system 
 * Added new Weather, Sky and Fog system 
 * Added new snow displacement system 
 * Added new configurable sleet camera effect 
	- When temperature is between –1.5°C and 1.5°C and there is precipitation, camera effect gets enabled if ‘camera_sleet_effect’ attribute has been set to True (default: False) 
 * Improved lights, fog, snow and weather effects and systems 
 * Improved vehicle lights (WinterSim vehicles only) 
 * Fixed Lidar sensor visibility issues (all meshes are now properly visible) 
 * Fixed issue where multiple precipitation particle systems were spawned on hero/ego vehicle when multiple camera sensors were spawned 
 * Performance and visual improvements 
 * WinterSim specific Python API extensions: 
	- ‘world.set_static_tiretracks (bool)’ hide/show generated static road tiretracks 
	- ‘world.clear_dynamic_tiretracks’  clear dynamic tiretracks on snowy roads 
	- ‘world.toggle_camera’ to “hide” server camera. Use this instead of ‘world.toggle_server_rendering()’ because disabling server rendering completely stops all Unreal Engine Niagara particle systems due Unreal Engine stopping them if there’s no active camera in the scene. 
 * New camera blueprint attributes: 
	 - blueprintref.set_attribute(‘camera_sleet_effect’), str(bool), default False 
   - blueprintref.set_attribute(‘camera_sleet_effect_rotation’), string (right, left, top, down), default “up” 
   - blueprintref.set_attribute(‘camera_sleet_effect_strength’), float (0.0 - 20.0), default 1.2 

 * Changes to wintersim_control.py:
	- Moved all weather controls to weather_control.py 
	- Removed unneeded keybindings  
	- Removed manual transmission mode 
	- Added ability to change between WinterSim vehicles (Key: Backspace) 
	- Added ability to teleport/reset vehicle (Key: R) 
	- Added ability to take screenshot (Key: F11)  
	- screenshot will be saved to same location as wintersim_control.py script 
	- Added separate Open3D lidar sensor window (Key: F9) 
	- Added multi sensor view (Key: F4) 
	- Added new launch arguments:  
		 -  --spawnpoint (int) (select spawnpoint to spawn ego vehicle) 
		 -  --open3dlidar (opens open3D Lidar on startup) 
		 -  --multisensorview (opens multisensorview on startup) 
		 -  --camerawindows (opens separate camera windows on startup) 

Download [WinterSim Release 1.10 here](https://a3s.fi/swift/v1/AUTH_8811c563a60e4395828a2393f44e064b/Builds/wintersim_1.10.zip)

## WinterSim Release 1.0.1

 * Improved snow particle systems 
 * Added snow (frost) to vehicle materials 
 * Improved weather controls (wind control, UI) 
 * Improved Lidar simulation (custom dropoff rate for lidar hits) 
 * Improved Radar simulation (rain amount & fog affects Radar distance) 
 * Performance and visual improvements 
 * Changed snow textures 
 * Snow particles are now visible when server rendering is disabled 
 * New tire mark system

Download [WinterSim Release 1.0.1 here](https://a3s.fi/swift/v1/AUTH_8811c563a60e4395828a2393f44e064b/Builds/wintersim_1.0.1.zip)

## WinterSim Release 1.0.0

 * First version of Muonio map
 * Added snowfall and snow effects
 * Snowfall and rain visibility in other camera modes
 * Added tire tracks on snowy roads
 * Added weather control (see wintersim_control.py or weather_control.py)
 * Changed lidar sensor behaviour

Download [WinterSim Release 1.0.0 here](https://a3s.fi/swift/v1/AUTH_8811c563a60e4395828a2393f44e064b/Builds/wintersim_1.00.zip)
