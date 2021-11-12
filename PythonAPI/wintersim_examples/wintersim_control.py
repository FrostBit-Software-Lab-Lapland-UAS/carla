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

import carla

# WinterSim imports
from hud import wintersim_hud
from sensors import wintersim_sensors
from sensors import open3d_lidar_window
from sensors.wintersim_camera_manager import CameraManager
from sensors.wintersim_camera_windows import CameraWindows
from keyboard.wintersim_keyboard_control import KeyboardControl
from sensors import multi_sensor_view
import time

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

def findweather_presets():
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
        self.actor_role_name = args.rolename
        self.fps = 60
        self.client = None
        self.original_settings = None
        self.settings = None
        self.args = args
        self.multiple_windows_enabled = args.camerawindows
        self.multi_sensor_view_enabled = False
        self.no_server_rendering = False
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
        self.camera_manager = None
        self.sensors = []
        self.wintersim_vehicles = ['pickup', 'wagon', 'van', 'bus']
        self.current_vehicle_index = 0
        self.weather_presets = []
        self.weather_presets_all = findweather_presets()
        for preset in self.weather_presets_all:
            if preset[0].temperature <= 0: # only get winter presets
                self.weather_presets.append(preset)
        self._weather_index = 0
        self._actor_filter = args.filter
        self._gamma = args.gamma
        self.map_name = ""
        self.filtered_map_name = ""
        self.restart()
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.current_map_layer = 0
        self.world.on_tick(self.hud_wintersim.on_world_tick)
       
        # disable server window rendering (UE4 window) if launch argument '--no_server_rendering' given
        # this improves performance as less things need to be rendered
        if not args.no_server_rendering:
            self.toggle_server_rendering()

    def restart(self):
        self.map_name = self.map.name
        self.filtered_map_name = self.map_name.rsplit('/', 1)[1]
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a vehicle according to arg parameter.
        blueprint = random.choice(self.world.get_blueprint_library().filter(self._actor_filter))
        blueprint.set_attribute('role_name', self.actor_role_name)

        # needed for large maps
        blueprint.set_attribute('role_name', self.actor_role_name) 

        # notify user if streaming distance changed from default value (2000)
        if self.args.streaming_distance != 2000:
            print("Large map tile streaming distance is set to: " + str(self.args.streaming_distance))

        settings = self.world.get_settings()
        settings.tile_stream_distance = self.args.streaming_distance
        self.world.apply_settings(settings)

        # Spawn player
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.spawn_actor(blueprint, spawn_point)
        
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

            self.player = self.world.spawn_actor(blueprint, spawn_point)

        self.camera_manager = CameraManager(self.player, self.hud_wintersim, self._gamma)
        self.setup_basic_sensors()
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud_wintersim.notification(actor_type)

    def setup_basic_sensors(self):
        '''Setup Collision, LaneInvasion, gnss and IMU sensors'''
        self.sensors.clear()
        self.collision_sensor = wintersim_sensors.CollisionSensor(self.player, self.hud_wintersim)
        self.lane_invasion_sensor = wintersim_sensors.LaneInvasionSensor(self.player, self.hud_wintersim)
        self.gnss_sensor = wintersim_sensors.GnssSensor(self.player)
        self.imu_sensor = wintersim_sensors.IMUSensor(self.player)
        self.camera_manager.update_parent_actor(self.player)
        self.sensors.clear()
        self.sensors.extend((self.collision_sensor.sensor, self.lane_invasion_sensor.sensor,
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
        self._weather_index %= len(self.weather_presets)
        self.preset = self.weather_presets[self._weather_index]
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
            self.hud_wintersim.notification(text)
            self.static_tiretracks_enabled ^= True
        except AttributeError:
            print("'set_static_tiretracks(bool)' has not been implemented. This is WinterSim specific Python API command.")

    def clear_dynamic_tiretracks(self):
        '''Clear dynamic tiretracks on snowy roads
        This is wrapped around try - expect block
        just in case someone runs this script elsewhere
        world.clear_dynamic_tiretracks() is WinterSim project specific Python API command 
        and does not work on default Carla simulator'''
        try:
            self.world.clear_dynamic_tiretracks()
            self.hud_wintersim.notification("Dynamic Tiretracks Cleared")
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
            self.cv2_windows = CameraWindows(self.player, self.camera_manager.sensor, self.world, self._actor_filter)
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

        if self.open3d_lidar_enabled:
            self.open3d_lidar.render()

        if not self.multi_sensor_view_enabled:
            self.camera_manager.render(display)
        else:
            self.multi_sensor_view.render()

        self.hud_wintersim.render(display)

        if self.sync_mode:
            self.world.tick()

    def toggle_server_rendering(self):
        '''Move server camera out of view so rendering load can be reduced. 
        It's recommend to use this over CARLA default no-server-rendering mode because otherwise 
        snowfall effect will stop due UE4 automatically stopping all Niagara particle systems
        if there's no camera.'''
        self.no_server_rendering ^= True
        self.world.toggle_camera()
        text = "Server rendering disabled" if self.no_server_rendering else "Server rendering enabled"
        self.hud_wintersim.notification(text)

    def toggle_camera_windows(self):
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
            self.open3d_lidar.setup(self.world, self.player, True, self._actor_filter, semantic=False)
            self.world.apply_settings(carla.WorldSettings(synchronous_mode=True, fixed_delta_seconds=0.05))
        else:
            self.open3d_lidar.destroy()
            self.world.apply_settings(carla.WorldSettings(synchronous_mode=False, fixed_delta_seconds=0.00))

        self.open3d_lidar_enabled ^= True
        self.sync_mode ^= True
        self.fps = 20 if self.open3d_lidar_enabled else 60
        text = "Open3D Lidar disabled" if not self.open3d_lidar_enabled else "Open3D Lidar enabled"
        self.hud_wintersim.notification(text, 6)
        
    def toggle_multi_sensor_view(self):
        if not self.multi_sensor_view_enabled:
            if self.camera_manager.sensor is None:
                return

            self.camera_manager.destroy()
            self.multi_sensor_view = multi_sensor_view.MultiSensorView()
            self.multi_sensor_view.setup(self.world, self.player, self.display, self.args.width, self.args.height, self._actor_filter)
            self.hud_wintersim.set_hud(False)
        else:
            self.multi_sensor_view.destroy()
            self.multi_sensor_view = None
            self.camera_manager.set_sensor(0, notify=False, force_respawn=True)
            self.hud_wintersim.set_hud(True)

        self.multi_sensor_view_enabled ^= True
        self.fps = 30 if self.multi_sensor_view_enabled else 60
        text = "Multi sensor view enabled" if self.multi_sensor_view_enabled else "Multi sensor view disabled"
        self.hud_wintersim.notification(text)
 
    def toggle_radar(self):
        if self.radar_sensor is None:
            self.radar_sensor = wintersim_sensors.RadarSensor(self.player)
            self.radar_sensor.spawn_radar()
        else:
            self.radar_sensor.destroy_radar()
            self.radar_sensor = None

        text = "Radar visualization enabled"  if self.radar_sensor != None else "Radar visualization disabled"
        self.hud_wintersim.notification(text)
        
    def take_fullscreen_screenshot(self):
        '''Take fullscreen screenshot of window and save it as png. 
        This should not be called every frame.'''
        date = str(int(time.time()))
        filename = "pygame" + date + ".png"
        pygame.image.save(self.display, filename)

        if self.open3d_lidar_enabled and self.open3d_lidar is not None:
            self.open3d_lidar.take_screenshot()

        self.hud_wintersim.notification('Screenshot saved')
        print('Screenshot saved to: ' + os.path.dirname(os.path.realpath(__file__)))

    def teleport_vehicle(self, position = -1):
        '''Teleport vehicle to random or given spawn location'''
        spawn_point = 0
        if position == -1: # if no argument given for position then teleport to random location 
            spawn_points = self.map.get_spawn_points()
            spawn_point = random.choice(spawn_points)
        else:
            spawn_point = position

        control = carla.VehicleControl()
        control.gear = 0
        control.brake = 1
        control.throttle = 0.0
        self.player.apply_control(control)
        self.player.set_target_velocity(carla.Vector3D(0, 0, 0))
        self.player.set_transform(spawn_point)

    def change_vehicle(self):
        '''Spawn next WinterSim vehicle'''

        # if camera windows, open3d lidar or multisensorview is enabled
        # close all of them
        if self.multiple_windows_enabled:
            self.toggle_camera_windows()

        if self.open3d_lidar_enabled:
            self.toggle_open3d_lidar()

        if self.multi_sensor_view_enabled:
            self.toggle_multi_sensor_view()

        # get current vehicle position and destroy current vehicle
        current_location = self.player.get_transform()
        current_location.location.z += 2.0
        if self.player is not None:
            self.player.destroy()
            self.player = None

        # get next WinterSim vehicle
        self.current_vehicle_index += 1
        if self.current_vehicle_index >= len(self.wintersim_vehicles):
            self.current_vehicle_index = 0
        next_vehicle = self.wintersim_vehicles[self.current_vehicle_index]
        self._actor_filter = next_vehicle

        # spawn new vehicle and reset camera
        blueprint = random.choice(self.world.get_blueprint_library().filter(self._actor_filter))
        self.player = self.world.spawn_actor(blueprint, current_location)

        copy = self.sensors.copy()

        self.setup_basic_sensors()
        self.camera_manager.reset_camera(self.player)

        for sensor in copy:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
                sensor = None

        self.hud_wintersim.notification('Changed vehicle to: ' + str(self.wintersim_vehicles[self.current_vehicle_index]))

    def destroy(self):
        '''Destroy all current sensors on quit'''

        if self.no_server_rendering:
            self.toggle_server_rendering()

        if not self.static_tiretracks_enabled:
            self.toggle_static_tiretracks(force_toggle=True)

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
       
        if self.camera_manager.sensor is not None:
            self.camera_manager.sensor.stop()
            self.camera_manager.sensor.destroy()

        if self.player is not None:
            self.player.destroy()

# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

def game_loop(args):
    # position offset for pygame window
    x = 10
    y = 50
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
        world.preset = world.weather_presets[0]
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
        except subprocess.SubprocessError:
            print("Couldn't launch weather_control.py")

        while True:
            clock.tick_busy_loop(world.fps)

            if controller.parse_events(world, clock):
                return

            world.tick(clock)
            world.render(display)
            pygame.display.flip()

    except Exception as e:
        print(e)

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
    argparser.add_argument(
        '--streaming_distance',
        default=2000,
        type=int,
        help='Specify tile streaming distance in large maps')
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