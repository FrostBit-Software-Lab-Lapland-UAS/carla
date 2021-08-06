#!/usr/bin/env python

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from __future__ import print_function
import glob
import os
import sys
import re
import argparse
import math
from hud import weather_hud

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import requests
from fmiopendata.wfs import download_stored_query

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_q
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_c
    from pygame.locals import K_m
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================

class World(object):
    def __init__(self, carla_world, hud, args):
        self.world = carla_world
        self.hud = hud
        self.preset = None
        self._weather_presets = []
        self._weather_presets_all = find_weather_presets()
        for preset in self._weather_presets_all:
            if preset[0].temperature <= 0: # get only presets what are for wintersim
                self._weather_presets.append(preset)
        self._weather_index = 0
        self._gamma = args.gamma

    def next_weather(self, world, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        self.preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % self.preset[1])
        self.hud.update_sliders(self.preset[0])
        self.world.set_weather(self.preset[0])

    def muonio_weather(self, world):
        weather = weather_hud.Weather(world.world.get_weather())
        r = requests.get('https://tie.digitraffic.fi/api/v1/data/weather-data/14047')
        data = r.json() # weather data

        x = str(data['dataUpdatedTime']).split('T') #split date and time

        date = x[0].split("-")

        #year = int(date[0])
        month = int(date[1]) - 1        
        #day = int(date[2])

        clock = x[1].split(":")
        clock[0] = int(clock[0]) + 3    # add 3 hours to get correct timezone
        clock[0] = str(clock[0])
        clock.pop(2)
        clock = float(".".join(clock))
        
        temp = data['weatherStations'][0]['sensorValues'][0]['sensorValue']

        precipitation = data['weatherStations'][0]['sensorValues'][17]['sensorValue']
        precipitation = 0 if math.isnan(precipitation) or precipitation is -1 else precipitation # this can be nan or -1 so that would give as error later so let make it 0 in this situation
        precipitation = 10 if precipitation > 10 else precipitation # max precipitation value is 10
        precipitation *= 10 # max precipitation is 10mm multiply by it 10 to get in range of 0-100
                    
        wind = data['weatherStations'][0]['sensorValues'][11]['sensorValue']
        wind = 0 if math.isnan(wind) else wind
        wind = 10 if wind > 10 else wind # Lets make 10m/s max wind value.
        wind *= 10 # Multiply wind by 10 to get it into range of 0-100

        snow = data['weatherStations'][0]['sensorValues'][49]['sensorValue']
        snow = 100 if snow > 100 else snow # lets set max number of snow to 1meter
        snow = 0 if math.isnan(snow) else snow
        
        weather.muonio_update(self.hud, temp, precipitation, wind, 0, snow, clock, month) # update weather object with our new data
        
        self.hud.notification('Weather: Muonio Realtime')
        self.hud.update_sliders(weather.weather, month=month, clock=clock)  # update sliders positions
        self.world.set_weather(weather.weather)                             # update weather

    def update_friction(self, iciness):
        '''Update all vehicle tire friction values'''
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

    def tick(self, clock, hud):
        self.hud.tick(self, clock, hud)

    def render(self, world, client, hud, display, weather):
        self.hud.render(display)
        self.render_sliders(world, client, hud, display, weather)

    def render_sliders(self, world, client, hud, display, weather):
        for slider in hud.sliders:
                if slider.hit:                                      # if slider is being touched
                    slider.move()                                   # move slider
                    weather.tick(hud, world._weather_presets[0])    # update weather object
                    client.get_world().set_weather(weather.weather) # send weather to server
        for slider in hud.sliders:
            slider.draw(display, slider)                            # move sliders

# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================

class KeyboardControl(object):
    """Class that handles keyboard input."""
    def parse_events(self, client, world, clock, hud):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for slider in hud.sliders:
                    if slider.button_rect.collidepoint(pos):            # get slider what mouse is touching
                        slider.hit = True                               # slider is being moved
            elif event.type == pygame.MOUSEBUTTONUP:
                if hud.ice_slider.hit:                                  # if road iciness slider is moved
                    world.update_friction(hud.ice_slider.val)
                for slider in hud.sliders:
                    slider.hit = False                                  # slider moving stopped
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                if event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(world, reverse=True)
                elif event.key == K_c:
                    world.next_weather(world, reverse=False)
                elif event.key == K_m:
                    world.muonio_weather(world)

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

def game_loop(args):
    # position offset for pygame window
    x = 1290
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

        hud = weather_hud.INFO_HUD(args.width, args.height, display)
        hud.make_sliders()                                                  # create sliders
        world = World(client.get_world(), hud, args)                        # instantiate our world object
        controller = KeyboardControl()                                      # controller for changing weather presets
        weather = weather_hud.Weather(client.get_world().get_weather())     # weather object to update carla weather with sliders
        hud.update_sliders(weather.weather)                                 # update sliders according to preset parameters
        clock = pygame.time.Clock()

        while True:
            clock.tick_busy_loop(30)
            if controller.parse_events(client, world, clock, hud): 
                return
            world.tick(clock, hud)
            world.render(world, client, hud, display, weather)
            pygame.display.flip()

    finally:
        pygame.quit()

# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================

def main():
    argparser = argparse.ArgumentParser(
        description='WinterSim')
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
        '--res',
        metavar='WIDTHxHEIGHT',
        default='550x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--gamma',
        default=2.2,
        type=float,
        help='Gamma correction of the camera (default: 2.2)')
    args = argparser.parse_args()
    args.width, args.height = [int(x) for x in args.res.split('x')]
    try:
        game_loop(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()