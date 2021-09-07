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

    R            : toggle recording images to disk

    F1           : toggle HUD
    F2           : toggle NPC's
    F4           : toggle multi sensor view
    F5           : toggle winter road static tiretracks
    F6           : clear all dynamic tiretracks on snowy roads
    F8           : toggle separate front and back camera windows
    F9           : toggle separate Open3D lidar window
    F11          : take fullscreen screenshot
    F12          : toggle server window rendering
    H            : toggle help
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
import subprocess
from numpy.core.numeric import True_

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

# WinterSim imports
from hud import wintersim_hud
from sensors import wintersim_sensors
from sensors import open3d_lidar_window
from sensors.wintersim_camera_manager import CameraManager
from sensors.wintersim_camera_windows import CameraWindows
from keyboard.wintersim_keyboard_control import KeyboardControl
from sensors import multi_sensor_view
from utils.spawn_npc import SpawnNPC
import time

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

try:
    import open3d as o3d
except ImportError:
    raise RuntimeError('cannot import open3d, make sure open3d package is installed')

import glob
import os
import sys
import argparse
import random

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
        self.fps = 60
        self.client = None
        self.original_settings = None
        self.settings = None
        self.args = args
        self.multiple_windows_enabled = args.camerawindows
        self.multi_sensor_view_enabled = False
        self.cv2_windows = None
        self.open3d_lidar = None
        self.multi_sensor_view = None
        self.open3d_lidar_enabled = False
        self.hud_wintersim = hud_wintersim
        self.sync_mode = False
        self.static_tiretracks_enabled = True
        self.multiple_window_setup = False
        self.preset = None
        self.player = None
        self.display = None
        self.w_control = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.show_vehicle_telemetry = False
        self.gnss_sensor = None
        self.imu_sensor = None
        self.radar_sensor = None
        self.spawn_npc = None
        self.camera_manager = None
        self.sensors = []
        self._weather_presets = []
        self._weather_presets_all = find_weather_presets()
        for preset in self._weather_presets_all:
            if preset[0].temperature <= 0: # only get winter presets
                self._weather_presets.append(preset)
        self._weather_index = 0
        self._actor_filter = args.filter
        self._gamma = args.gamma
        self.restart()
        preset = self._weather_presets[0]
        self.world.set_weather(preset[0])
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.current_map_layer = 0
        self.world.on_tick(self.hud_wintersim.on_world_tick)

        # disable server window rendering (UE4 window) if launch argument '--no_server_rendering' given
        # this improves performance as less things need to be rendered
        if not args.no_server_rendering:
            self.toggle_server_rendering()

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
        
        spawn_attempts = 0
        while self.player is None:
            if not self.map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)

            # if --spawnpoint [number] argument given then try to spawn there
            # else spawn in random spawn location
            spawn_points = self.map.get_spawn_points()
            if self.args.spawnpoint == -1 or self.args.spawnpoint > len(spawn_points):
                spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            else:
                spawn_point = spawn_points[self.args.spawnpoint]

            #self.player = self.world.spawn_actor(blueprint, spawn_point)
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)

            if spawn_attempts == 5:
                print('Tried to spawn vehicle 5 times without success. Something is wrong!')
                sys.exit(1)
            spawn_attempts += 1

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

        self.sensors.extend((self.camera_manager.sensor,
            self.collision_sensor.sensor, self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,self.imu_sensor.sensor))

    def is_process_alive(self):
        '''Check if w_control subprocess.Popen is still alive'''
        if self.w_control is not None:
            poll = self.w_control.poll()
            if poll is not None:
                self.w_control = None
                return False
            else:
                return True

    def next_weather(self, reverse=False):
        ''''Change weather preset'''
        if self.is_process_alive():
            return

        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        self.preset = self._weather_presets[self._weather_index]
        self.hud_wintersim.notification('Weather: %s' % self.preset[1])
        self.player.get_world().set_weather(self.preset[0])

    def toggle_static_tiretracks(self, force_toggle=False):
        '''Toggle static tiretracks on snowy roads on/off
        This is wrapped around try - expect block
        just in case someone runs this script elsewhere
        world.set_static_tiretracks(bool) is WinterSim project specific Python API command 
        and does not work on default Carla simulator'''
        if self.is_process_alive() and not force_toggle:
            return

        try:
            self.world.set_static_tiretracks(self.static_tiretracks_enabled)
            text = "Static tiretracks enabled" if self.static_tiretracks_enabled else "Static tiretracks disabled"
            self.hud.notification(text)
            self.static_tiretracks_enabled ^= True
        except AttributeError:
            print("'set_static_tiretracks(bool)' has not been implemented. This is WinterSim specific Python API command.")

    def clear_dynamic_tiretracks(self, force_toggle=False):
        '''Clear dynamic tiretracks on snowy roads
        This is wrapped around try - expect block
        just in case someone runs this script elsewhere
        world.clear_dynamic_tiretracks() is WinterSim project specific Python API command 
        and does not work on default Carla simulator'''
        try:
            self.world.clear_dynamic_tiretracks()
            text = "Dynamic tiretracks cleared"
            self.hud.notification(text)
        except AttributeError:
            print("'clear_dynamic_tiretracks()' has not been implemented. This is WinterSim specific Python API command.")

    def tick(self, clock):
        '''Tick WinterSim hud'''
        self.hud_wintersim.tick(self, clock)

    def render_camera_windows(self):
        '''Render separate camera windows if enabled'''
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

    def render(self, display):
        '''Render everything to screen'''
        self.render_camera_windows()

        if not self.multi_sensor_view_enabled:
            self.camera_manager.render(display)
        else:
            self.multi_sensor_view.render()

        self.hud_wintersim.render(display)

        if self.open3d_lidar_enabled:
            self.open3d_lidar.render()

        if self.sync_mode:
            self.world.tick()

    def toggle_server_rendering(self):
        settings = self.world.get_settings()
        settings.no_rendering_mode = not settings.no_rendering_mode
        self.world.apply_settings(settings)
        text = "Server rendering disabled" if settings.no_rendering_mode else "Server rendering enabled"
        self.hud_wintersim.notification(text)

    def toggle_cv2_windows(self):
        '''toggle separate camera windows'''
        self.multiple_windows_enabled = not self.multiple_windows_enabled
        if self.multiple_windows_enabled == False and self.cv2_windows is not None:
            self.cv2_windows.destroy()
            self.multiple_window_setup = False

        text = "Multiple cameras enabled" if self.multiple_windows_enabled else "Multiple cameras disabled"
        self.hud_wintersim.notification(text)

    def toggle_open3d_lidar(self):
        '''toggle separate open3d lidar window'''
        if not self.open3d_lidar_enabled:
            self.open3d_lidar = open3d_lidar_window.Open3DLidarWindow()
            self.open3d_lidar.setup(self.world, self.player, True, True)
            self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False, synchronous_mode=True,
            fixed_delta_seconds=0.05))
            traffic_manager = self.client.get_trafficmanager(8000)
            traffic_manager.set_synchronous_mode(True)
        else:
            self.open3d_lidar.destroy()
            self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False, synchronous_mode=False,
            fixed_delta_seconds=0.00))
            traffic_manager = self.client.get_trafficmanager(8000)
            traffic_manager.set_synchronous_mode(False)

        self.open3d_lidar_enabled ^= True
        self.sync_mode ^= True
        self.fps = 30 if self.open3d_lidar_enabled else 60
        text = "Destroyed Open3D Lidar" if not self.open3d_lidar_enabled else "Spawned Open3D Lidar"
        self.hud_wintersim.notification(text, 6)
        
    def toggle_multi_sensor_view(self):
        if not self.multi_sensor_view_enabled:
            if self.camera_manager.sensor is None:
                return

            self.sensors.remove(self.camera_manager.sensor)
            self.camera_manager.destroy()
            self.multi_sensor_view = multi_sensor_view.MultiSensorView()
            self.multi_sensor_view.setup(self.world, self.player, self.display, self.args.width, self.args.height)
            self.hud_wintersim.set_hud(False)
        else:
            self.multi_sensor_view.destroy()
            self.multi_sensor_view = None
            self.camera_manager.set_sensor(0, notify=False, force_respawn=True)
            self.hud_wintersim.set_hud(True)
            self.sensors.append(self.camera_manager.sensor)
        
        self.multi_sensor_view_enabled ^= True
        self.fps = 30 if self.multi_sensor_view_enabled else 60
        text = "Multi sensor view enabled" if self.multi_sensor_view_enabled else "Multi sensor view disabled"
        self.hud_wintersim.notification(text)
 
    def toggle_radar(self):
        if self.radar_sensor is None:
            self.radar_sensor = wintersim_sensors.RadarSensor(self.player)
        else:
            self.radar_sensor.destroy_radar()
            #self.radar_sensor.sensor.destroy()
            self.radar_sensor = None

        text = "Radar visualization enabled"  if self.radar_sensor != None else "Radar visualization disabled"
        self.hud_wintersim.notification(text)

    def toggle_npcs(self):
        if self.spawn_npc is None:
            self.spawn_npc = SpawnNPC()
            self.spawn_npc.spawn_npc(self.world, self.client, self.player, 10, 10)
            self.hud_wintersim.notification('Spawned NPCs, Press F2 to destroy all NPCs', 6)
        else:
            self.spawn_npc.destroy_all_npcs()
            self.spawn_npc = None
            self.hud_wintersim.notification('Destroyed all NPCs')
       
    def destroy_sensors(self):
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def take_fullscreen_screenshot(self):
        '''Take fullscreen screenshot of pygame window
        and save it as png'''
        date = str(int(time.time()))
        filename = "screenshot" + date + ".png"
        pygame.image.save(self.display, filename)

    def destroy(self):
        '''Destroy all current sensors on quit'''
        if not self.static_tiretracks_enabled:
            self.toggle_static_tiretracks(force_toggle=True)

        if self.spawn_npc is not None:
            self.toggle_npcs()

        if self.open3d_lidar_enabled:
            self.world.apply_settings(carla.WorldSettings(
            no_rendering_mode=False, synchronous_mode=False,
            fixed_delta_seconds=0.00))
            self.open3d_lidar.destroy()

        if self.cv2_windows is not None:
            self.cv2_windows.destroy()

        if self.radar_sensor is not None:
            self.toggle_radar()

        if self.multi_sensor_view_enabled and self.multi_sensor_view is not None:
            self.multi_sensor_view.destroy()

        for sensor in self.sensors:
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

        display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        display.fill((0,0,0))
        pygame.display.flip()

        hud_wintersim = wintersim_hud.WinterSimHud(args.width, args.height, display)
        world = World(client.get_world(), hud_wintersim, args)
        world.client = client
        world.preset = world._weather_presets[0]
        world.original_settings = world.world.get_settings()
        hud_wintersim.setup(world)
        controller = KeyboardControl(world, args.autopilot)
        clock = pygame.time.Clock()
        world.display = display

        # enable open 3d lidar if launch argument '--open3dlidar' given
        if world.args.open3dlidar:
            world.toggle_open3d_lidar()

        # enable multi sensor view if launch argument '--multisensorview' given
        if world.args.multisensorview:
            world.toggle_multi_sensor_view()

        # open another terminal window and launch wintersim weather_hud.py script
        try:
            world.w_control = subprocess.Popen('python weather_control.py')
        except:
            print("Couldn't launch weather_control.py")

        while True:
            clock.tick_busy_loop(world.fps)

            if controller.parse_events(world, clock):
                return

            world.tick(clock)
            world.render(display)
            pygame.display.flip()

    finally:
        if world is not None:
            game_world = client.get_world()                 
            settings = game_world.get_settings()
            settings.no_rendering_mode = False
            game_world.apply_settings(settings)     # turn server window rendering back on quit
          
            if world.w_control is not None:
                world.w_control.kill()              # stop weather control

            world.destroy()
                
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
        default='pickup',
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
        '--camerawindows',
        default=-False,
        dest='camerawindows', 
        action='store_true',
        help='Enable multiple camera view on startup')
    argparser.add_argument(
        '--multisensorview',
        default=-False,
        dest='multisensorview',
        action='store_true',
        help='Enable multi sensor view on startup')
    argparser.add_argument(
        '--open3dlidar',
        default=-False,
        dest='open3dlidar', 
        action='store_true',
        help='Enable open3d lidar window on startup')
    argparser.add_argument(
        '--spawnpoint',
        default=-1,
        type=int,
        help='Specify spawn point')
    argparser.add_argument(
        '--no_server_rendering',
        default=-True,
        dest='no_server_rendering', 
        action='store_false',
        help='Disable server rendering on startup')
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