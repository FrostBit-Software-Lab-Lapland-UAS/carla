### WinterSim Python API reference
This reference contains WinterSim specific Python API commands.

For CARLA Python API reference see [Python API reference](https://carla.readthedocs.io/en/latest/python_api/)

## carla.World<a name="carla.World"></a>
World objects are created by the client to have a place for the simulation to happen. The world contains the map we can see, meaning the asset, not the navigation map. Navigation maps are part of the [carla.Map](https://carla.readthedocs.io/en/latest/python_api/#carlamap) class. It also manages the weather and actors present in it. There can only be one world per simulation, but it can be changed anytime.  

### Methods

- <a name="carla.World.clear_dynamic_tiretracks"></a>**<font color="#7fb800">clear_dynamic_tiretracks</font>**(<font color="#00a6ed">**self**</font>)  
This method clears dynamic tiretracks that are left by vehicles on snowy roads.
</font>

- <a name="carla.set_static_tiretracks"></a>**<font color="#7fb800">set_static_tiretracks</font>**(<font color="#00a6ed">**self**</font>, <font color="#00a6ed">**bool**</font>)    
This method enables or disables static tiretracks on snowy roads.
    - **Parameters:**
        - enabled (bool) 
