### WinterSim Python API reference
This reference only contains WinterSim specific Python API commands that we have added, modified or removed.

For CARLA version 0.9.12 Python API reference see [Python API reference](https://carla.readthedocs.io/en/0.9.12/python_api/)

## carla.World<a name="carla.World"></a>
World objects are created by the client to have a place for the simulation to happen. The world contains the map we can see, meaning the asset, not the navigation map. Navigation maps are part of the [carla.Map](https://carla.readthedocs.io/en/latest/python_api/#carlamap) class. It also manages the weather and actors present in it. There can only be one world per simulation, but it can be changed anytime.  

### Methods

- <a name="carla.World.clear_dynamic_tiretracks"></a>**<font color="#7fb800">clear_dynamic_tiretracks</font>**(<font color="#00a6ed">**self**</font>)  
This method clears dynamic tiretracks that are left by vehicles on snowy roads.
</font>

- <a name="carla.set_static_tiretracks"></a>**<font color="#7fb800">set_static_tiretracks</font>**(<font color="#00a6ed">**self**</font>, <font color="#00a6ed">**bool**</font>)    
This method enables/disables static tiretracks on snowy roads.
    - **Parameters:**
        - enabled (bool)
        
- <a name="carla.World.toggle_cameras"></a>**<font color="#7fb800">toggle_camera</font>**(<font color="#00a6ed">**self**</font>)  
This method moves server camera out of view so rendering load is reduced. It's recommend to use this over CARLA default no-server-rendering mode because otherwise snowfall effect will stop due UE4 automaically stopping all Niagara particle systems if there's no camera.
</font>

## carla.ActorBlueprint<a name="carla.ActorBlueprint"></a>
CARLA provides a blueprint library for actors that can be consulted through [carla.BlueprintLibrary](#carla.BlueprintLibrary). Each of these consists of an identifier for the blueprint and a series of attributes that may be modifiable or not. This class is the intermediate step between the library and the actor creation. Actors need an actor blueprint to be spawned. These store the information for said blueprint in an object with its attributes and some tags to categorize them. The user can then customize some attributes and eventually spawn the actors through [carla.World](#carla.World).  


##### Setters
- <a name="carla.ActorBlueprint.set_attribute"></a>**<font color="#7fb800">set_attribute</font>**(<font color="#00a6ed">**self**</font>, <font color="#00a6ed">**id**</font>, <font color="#00a6ed">**value**</font>)<button class="SnipetButton" id="carla.ActorBlueprint.set_attribute-snipet_button">snippet &rarr;</button>  
If the `id` attribute is modifiable, changes its value to `value`.  
    - **Parameters:**
        - `id` (_str_) – The identifier for the attribute that is intended to be changed.  
        - `value` (_str_) – The new value for said attribute.  
    - **WinterSim added camera attributtes**
        - `id` ("camera_sleet_effect") – whether this camera should show camera sleet effect when weather conditions are optimal (Default: False)
        - `value` (boolean as string) – False/True as string
        -
        - `id` ("camera_sleet_effect_rotation") – Camera sleet effect rotation (Default: up)
        - `value` (str) – Rotations: "up", "left", "right", "down"
        -
        - `id` ("camera_sleet_effect_strength") – Camera sleet effect strength (Default: 1.2)
        - `value` (float as string) – Float value as string. Range 0.0 - 20.0
