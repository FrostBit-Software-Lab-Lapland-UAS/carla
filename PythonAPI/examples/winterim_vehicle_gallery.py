#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import math
import random
import time


def get_transform(vehicle_location, angle, d=6.4):
    a = math.radians(angle)
    location = carla.Location(d * math.cos(a), d * math.sin(a), 2.0) + vehicle_location
    return carla.Transform(location, carla.Rotation(yaw=180 + angle, pitch=-15))


def main():
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(2.0)
    world = client.get_world()
    spectator = world.get_spectator()

    spawn_points = world.get_map().get_spawn_points()
    x = 0
    while x <= 2:
        if x == 0:
            blueprint = random.choice(world.get_blueprint_library().filter('Van'))
        if x == 1:
            blueprint = random.choice(world.get_blueprint_library().filter('Pickup'))
        if x == 2:
            blueprint = random.choice(world.get_blueprint_library().filter('Wagon'))

        if x < 2:
            x += 1
        elif x > 0:
            x -= 1
        

        location = spawn_points[7].location
        location.z -= 0.0
        transform = carla.Transform(location, carla.Rotation(yaw=-45.0))
        vehicle = world.spawn_actor(blueprint, transform)

        try:
            print(vehicle.type_id)

            angle = 0
            while angle < 360:
                timestamp = world.wait_for_tick().timestamp
                angle += timestamp.delta_seconds * 30.0
                spectator.set_transform(get_transform(vehicle.get_location(), angle - 90))         

        finally:

            vehicle.destroy()


if __name__ == '__main__':

    main()
