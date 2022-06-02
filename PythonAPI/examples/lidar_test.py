#!/usr/bin/env python
#Lidar testing script
from dataclasses import dataclass
import glob
import os
import sys
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import tqdm
import carla
import random
import time


def main():
    actor_list = []
    record = False
    try:
        # Connecting to the server
        client = carla.Client('localhost', 2000)
        world = client.get_world()
        client.set_timeout(10.0)

        # Getting all required blueprints
        blueprint_library = world.get_blueprint_library()
        ego_bp = blueprint_library.filter('wagon')[0]
        lidar_bp = blueprint_library.find('sensor.lidar.custom_ray_cast')

        # Getting spawnpoints and spawning vehicles
        transform = world.get_map().get_spawn_points()
        #vehicleMain = world.spawn_actor(model3_bp, transform[59])
        vehicleMain = world.spawn_actor(ego_bp, transform[102])
        #vehicleMain.apply_control(carla.VehicleControl(hand_brake=True))
        vehicleMain.set_autopilot(True)
        # Adding vehicle to the actor list
        actor_list.append(vehicleMain)
        print('Created %s as the main vehicle' % vehicleMain.type_id)
        
        # Setting spectator
        spectator = world.get_spectator()
        transform = vehicleMain.get_transform()

        # Weather settings
        weather = world.get_weather()
        weather.precipitation = 15
        weather.particle_size = 1
        weather.temperature = -0.8
        weather.dew_point = -0.8
        weather.humidity = 100
        world.set_weather(weather)
    
        # Lidar config (Ouster OS1-32)
        lidar_bp.set_attribute('channels',str(32))
        lidar_bp.set_attribute('points_per_second',str(655360))
        lidar_bp.set_attribute('rotation_frequency',str(10))
        lidar_bp.set_attribute('range',str(120))
        lidar_bp.set_attribute('upper_fov', str(22.5))
        lidar_bp.set_attribute('lower_fov', str(-22.5))
        spectator.set_transform(carla.Transform(transform.location + carla.Location(z=50),carla.Rotation(pitch=-90)))
        lidar_location = carla.Transform(carla.Location(x = 0, z = 2.5))
        lidar = world.spawn_actor(lidar_bp,lidar_location,attach_to=vehicleMain)
        actor_list.append(lidar)
        time.sleep(4)
        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 1/10
        world.apply_settings(settings)

        #Save sensor data
        record = True
        recordlidar(record, lidar)
        with tqdm.trange(20) as t:
            for _ in t:
                world.tick()
                time.sleep(5)
                spectator.set_transform(carla.Transform(transform.location + carla.Location(z=50),carla.Rotation(pitch=-90)))
        record = False
        recordlidar(record, lidar)
        settings = world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        world.apply_settings(settings)
        time.sleep(5)

    finally:

        print('destroying all actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')

def recordlidar(record, lidar):
    if record:
        lidar.listen(lambda point_cloud: point_cloud.save_to_disk('syntheticdata/Lidar/%.2d.ply' % point_cloud.frame))

if __name__ == '__main__':

    main()