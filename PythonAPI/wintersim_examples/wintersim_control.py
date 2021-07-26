#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Welcome to CARLA WinterSim control.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    A/D          : steer left/right
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down

    L            : toggle next light type
    SHIFT + L    : toggle high beam
    Z/X          : toggle right/left blinker
    I            : toggle interior light

    TAB          : change sensor position
    ` or N       : next sensor
    [1-9]        : change to sensor [1-9]
    G            : toggle radar visualization
    C            : change weather (Shift+C reverse)
    Backspace    : change vehicle

    V            : Select next map layer (Shift+V reverse)
    B            : Load current selected map layer (Shift+B to unload)

    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    F1           : toggle HUD
    F8           : spawn separate front and back camera windows
    F9           : spawn separate Open3D lidar window
    F10          : spawn separate radar window
    F12          : toggle server window rendering
    H/?          : toggle help
    ESC          : quit;
"""

# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================

from __future__ import print_function

import glob
import os
import re
import sys
import time
import subprocess

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import argparse
import logging
import random
import re


import carla
from carla import ColorConverter as cc

from hud import wintersim_hud
from sensors import wintersim_sensors
from sensors import open3d_lidar_window
from camera.wintersim_camera_manager import CameraManager
from camera.wintersim_camera_windows import CameraWindows
from keyboard.wintersim_keyboard_control import KeyboardControl

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

import glob
import os
import sys
import argparse
import time
from datetime import datetime
import random
import numpy as np
from matplotlib import cm
import open3d as o3d

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name

# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================

class World(object):
    def __init__(self, carla_world, hud_wintersim, args):
        self.world = carla_world
        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)
        self.client = None
        self.record_data = False
        self.original_settings = None
        self.settings = None
        self.isResumed = False
        self.args = args
        self.multiple_windows_enabled = args.windows
        self.cv2_windows = None
        self.open3d_lidar = None
        self.open3d_lidar_enabled = False
        self.hud_wintersim = hud_wintersim
        self.sync_mode = False
        self.ud_friction = True
        self.preset = None
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.imu_sensor = None
        self.radar_sensor = None
        self.camera_manager = None
        self._weather_presets = []
        self._weather_presets_all = find_weather_presets()
        for preset in self._weather_presets_all:
            if preset[0].temperature <= 0: # get only presets what are for wintersim
                self._weather_presets.append(preset)
        self._weather_index = 0
        self._actor_filter = args.filter
        self._gamma = args.gamma
        self.restart()
        preset = self._weather_presets[0]  # set weather preset
        self.world.set_weather(preset[0])
        self.player.gud_frictiong_enabled = False
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.current_map_layer = 0
        self.world.on_tick(self.hud_wintersim.on_world_tick)
        self.map_layer_names = [
            carla.MapLayer.NONE,
            carla.MapLayer.Buildings,
            carla.MapLayer.Decals,
            carla.MapLayer.Foliage,
            carla.MapLayer.Ground,
            carla.MapLayer.ParkedVehicles,
            carla.MapLayer.Particles,
            carla.MapLayer.Props,
            carla.MapLayer.StreetLights,
            carla.MapLayer.Walls,
            carla.MapLayer.All
        ]

    def restart(self):
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a vehicle according to arg parameter.
        blueprint = random.choice(self.world.get_blueprint_library().filter(self._actor_filter))

        # Spawn player
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            if not self.map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)

            # if --spawnpoint [number] argument given then try to spawn there
            # else spawn in random spawn location
            spawn_points = self.map.get_spawn_points()
            if self.args.spawnpoint == 0 or self.args.spawnpoint > len(spawn_points):
                spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            else:
                spawn_point = spawn_points[self.args.spawnpoint]

            self.player = self.world.try_spawn_actor(blueprint, spawn_point)

        # Set up the sensors
        self.collision_sensor = wintersim_sensors.CollisionSensor(self.player, self.hud_wintersim)
        self.lane_invasion_sensor = wintersim_sensors.LaneInvasionSensor(self.player, self.hud_wintersim)
        self.gnss_sensor = wintersim_sensors.GnssSensor(self.player)
        self.imu_sensor = wintersim_sensors.IMUSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud_wintersim, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud_wintersim.notification(actor_type)
        self.multiple_window_setup = False

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        self.preset = self._weather_presets[self._weather_index]
        self.hud_wintersim.notification('Weather: %s' % self.preset[1])
        self.player.get_world().set_weather(self.preset[0])

    def next_map_layer(self, reverse=False):
        self.current_map_layer += -1 if reverse else 1
        self.current_map_layer %= len(self.map_layer_names)
        selected = self.map_layer_names[self.current_map_layer]
        self.hud_wintersim.notification('LayerMap selected: %s' % selected)

    def load_map_layer(self, unload=False):
        selected = self.map_layer_names[self.current_map_layer]
        if unload:
            self.hud_wintersim.notification('Unloading map layer: %s' % selected)
            self.world.unload_map_layer(selected)
        else:
            self.hud_wintersim.notification('Loading map layer: %s' % selected)
            self.world.load_map_layer(selected)

    def tick(self, clock, hud_wintersim):
        '''Tick WinterSim hud'''
        self.hud_wintersim.tick(self, clock, hud_wintersim)

    def render_camera_windows(self):
        '''Render camera windows if enabled'''
        if not self.multiple_windows_enabled:
            return

        if self.multiple_windows_enabled and self.multiple_window_setup:
            self.cv2_windows.resume()
            
        if not self.multiple_window_setup and self.multiple_windows_enabled:
            self.cv2_windows = CameraWindows(self.player, self.camera_manager.sensor, self.world)
            self.multiple_window_setup = True
            self.cv2_windows.start()
            self.cv2_windows.pause()

    def block_camera_windows_thread(self):
        '''if camera windows enabled, you can block CameraWindows thread flag'''
        if self.multiple_windows_enabled and self.cv2_windows is not None:
            self.cv2_windows.pause()

    def render(self, world, client, hud_wintersim, display):
        '''Render everything to screen'''
        self.render_camera_windows()
        self.camera_manager.render(display)
        self.hud_wintersim.render(display, world)

        if self.open3d_lidar_enabled and self.open3d_lidar is not None:
            self.open3d_lidar.render_open3d_lidar()

        if self.sync_mode:    
            self.world.tick()

    def toggle_cv2_windows(self):
        '''toggle separate camera windows'''
        self.multiple_windows_enabled = not self.multiple_windows_enabled
        if self.multiple_windows_enabled == False and self.cv2_windows is not None:
            self.cv2_windows.destroy()
            self.multiple_window_setup = False

    def toggle_open3d_lidar(self):
        '''toggle separate open3d lidar window'''
        if not self.open3d_lidar_enabled:
            self.open3d_lidar = open3d_lidar_window.Open3DLidarWindow()
            self.open3d_lidar.setup(self.world, self.player, True, True)
            self.open3d_lidar_enabled = True
            self.sync_mode = True
           
            self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False, synchronous_mode=True,
            fixed_delta_seconds=0.05))

            traffic_manager = self.client.get_trafficmanager(8000)
            traffic_manager.set_synchronous_mode(True)

        else:
            self.open3d_lidar.destroy()
            self.open3d_lidar_enabled = False
            self.sync_mode = False

            self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False, synchronous_mode=False,
            fixed_delta_seconds=0.00))

            traffic_manager = self.client.get_trafficmanager(8000)
            traffic_manager.set_synchronous_mode(False)

    def toggle_radar(self, window):
        if self.radar_sensor is None:
            self.radar_sensor = wintersim_sensors.RadarSensor(self.player, window)
        elif self.radar_sensor.sensor is not None:
            self.radar_sensor.sensor.destroy()
            self.radar_sensor = None

    def update_friction(self, iciness):
        '''Update all vehicle wheel frictions.
        This will stop vehicles if they are moving while changing the value.'''
        actors = self.world.get_actors()
        friction = 5
        friction -= iciness / 100 * 4
        for actor in actors:
            if 'vehicle' in actor.type_id:
                vehicle = actor
                front_left_wheel  = carla.WheelPhysicsControl(tire_friction=friction, damping_rate=1.3, max_steer_angle=70.0, radius=20.0)
                front_right_wheel = carla.WheelPhysicsControl(tire_friction=friction, damping_rate=1.3, max_steer_angle=70.0, radius=20.0)
                rear_left_wheel   = carla.WheelPhysicsControl(tire_friction=friction, damping_rate=1.3, max_steer_angle=0.0,  radius=20.0)
                rear_right_wheel  = carla.WheelPhysicsControl(tire_friction=friction, damping_rate=1.3, max_steer_angle=0.0,  radius=20.0)
                wheels = [front_left_wheel, front_right_wheel, rear_left_wheel, rear_right_wheel]

                physics_control = vehicle.get_physics_control()
                physics_control.wheels = wheels
                vehicle.apply_physics_control(physics_control)

    def destroy_sensors(self):
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def destroy(self):
        if self.cv2_windows is not None:
            self.cv2_windows.destroy()

        if self.radar_sensor is not None:
            self.toggle_radar()
        sensors = [self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
            self.imu_sensor.sensor]
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.player is not None:
            self.player.destroy()

# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

def game_loop(args):
    # position offset for pygame window
    x = 10
    y = 100
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
    pygame.init()
    pygame.font.init()
    world = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        display = pygame.display.set_mode((args.width, args.height),pygame.HWSURFACE | pygame.DOUBLEBUF)
        display.fill((0,0,0))
        pygame.display.flip()

        hud_wintersim = wintersim_hud.WinterSimHud(args.width, args.height, display)
        world = World(client.get_world(), hud_wintersim, args)
        world.client = client
        world.preset = world._weather_presets[0]
        world.original_settings = world.world.get_settings()
        controller = KeyboardControl(world, args.autopilot)
        clock = pygame.time.Clock()

        # open another terminal window and launch wintersim weather_hud.py script
        try:
            w_control = subprocess.Popen('python weather_control.py')
        except:
            print("Couldn't launch weather_control.py")

        # loop that runs every frame
        while True:

            if world.open3d_lidar_enabled: 
                clock.tick_busy_loop(30)    # if open3d lidar window open, cap frame rate
                #world.world.tick()
            else:
                clock.tick_busy_loop(60)

            if controller.parse_events(client, world, clock, hud_wintersim):
                return
            world.tick(clock, hud_wintersim)
            world.render(world, client, hud_wintersim, display)
            pygame.display.flip()

    finally:
        if world is not None:
            # turn server window rendering back on quit
            game_world = client.get_world()                 
            settings = game_world.get_settings()
            settings.no_rendering_mode = False
            game_world.apply_settings(settings)
            world.destroy()

        # stop weather control
        w_control.kill()
        pygame.quit()

# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================

def main():
    argparser = argparse.ArgumentParser(
        description='WinterSim')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='model3',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--rolename',
        metavar='NAME',
        default='hero',
        help='actor role name (default: "hero")')
    argparser.add_argument(
        '--gamma',
        default=2.2,
        type=float,
        help='Gamma correction of the camera (default: 2.2)')
    argparser.add_argument(
        '--windows',
        default=False,
        type=bool,
        help='Enable multiple camera view on startup')
    argparser.add_argument(
        '--spawnpoint',
        default=0,
        type=int,
        help='Specify spawn point')
    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.res.split('x')]
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)
    logging.info('listening to server %s:%s', args.host, args.port)
    print(__doc__)

    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

if __name__ == '__main__':
    main()