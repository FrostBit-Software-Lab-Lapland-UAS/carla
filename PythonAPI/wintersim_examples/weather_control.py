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
import json
import time
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

from tkinter import *
from tkinter.filedialog import askopenfilename 

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_q
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_c
    from pygame.locals import K_o
    from pygame.locals import K_s
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    from pynput import keyboard
except ImportError:
    raise RuntimeError('cannot import pynput, make sure pynput package is installed')

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
        self.set_current_weather()
        self._weather_index = 0
        self._gamma = args.gamma
        self.static_tiretracks_enabled = True
        self.muonio = False
        self.map_name = self.world.get_map().name
        self.filtered_map_name = self.map_name.rsplit('/', 1)[1]
        self.muonio = self.filtered_map_name == "Muonio"

    def set_current_weather(self):
        default_weather = self.world.get_weather()
        self._weather_index = len(self.hud.preset_names) -1
        self.hud.preset_slider.val = self._weather_index
        self.hud.update_sliders(default_weather)

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        self.preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % self.preset[1])
        self.hud.preset_slider.val = self._weather_index
        self.hud.update_sliders(self.preset[0])
        self.world.set_weather(self.preset[0])

    def set_weather(self, index):
        if not index < len(self._weather_presets):
            return

        self._weather_index = index
        self.preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % self.preset[1])
        self.hud.preset_slider.val = self._weather_index
        self.hud.update_sliders(self.preset[0])
        self.world.set_weather(self.preset[0])

    def realtime_weather(self):
        '''Get real time Muonio or Rovaniemi weather data from digitraffic API'''
        weather = weather_hud.Weather(self.world.get_weather())

        if self.muonio:
            url = 'https://tie.digitraffic.fi/api/v1/data/weather-data/14047'   # Muonio
        else:
            url = 'https://tie.digitraffic.fi/api/v1/data/weather-data/14031'   # Rovaniemi

        r = requests.get(url)
        data = r.json()

        x = str(data['dataUpdatedTime']).split('T') # split date and time
        date = x[0].split("-")
        #year = int(date[0])
        month = int(date[1]) - 1      
        day = int(date[2])

        clock = x[1].split(":")
        clock[0] = int(clock[0]) + 3 # add 3 hours to get correct timezone
        clock[0] = str(clock[0])
        clock.pop(2)
        clock = float(".".join(clock))

        temp = data['weatherStations'][0]['sensorValues'][0]['sensorValue']
        wind = data['weatherStations'][0]['sensorValues'][11]['sensorValue']
        wind = 0 if math.isnan(wind) else wind
        wind = 10 if wind > 10 else wind # Lets make 10m/s max wind value.
        wind *= 10 # Multiply wind by 10 to get it into range of 0-100

        wind_direction = data['weatherStations'][0]['sensorValues'][13]['sensorValue'] / 2

        humidity = data['weatherStations'][0]['sensorValues'][15]['sensorValue']
        humidity = 100 if humidity > 100 else humidity
        humidity = 0 if math.isnan(humidity) else humidity

        precipitation = data['weatherStations'][0]['sensorValues'][17]['sensorValue']
        precipitation = 0 if math.isnan(precipitation) or precipitation is -1 else precipitation # this can be nan or -1 so that would give as error later so let make it 0 in this situation
        precipitation = 10 if precipitation > 10 else precipitation # max precipitation value is 10
        precipitation *= 10 # max precipitation is 10mm multiply by it 10 to get in range of 0-100
           
        snow = data['weatherStations'][0]['sensorValues'][49]['sensorValue']
        snow = 100 if snow > 100 else snow # lets set max number of snow to 1meter
        snow = 0 if math.isnan(snow) else snow

        weather_values = [temp, humidity, precipitation, 
            snow, wind, wind_direction, 
            clock, day, month]

        weather.set_weather_manually(weather_values)
        self.hud.update_sliders(weather.weather)
        self.world.set_weather(weather)
        self.hud.notification('Weather: Muonio Realtime')

    def export_json(self):
        '''Export current weather parameters to json file'''
        data = dict()
        sliders = self.hud.sliders
        for slider in sliders:
            data.update({slider.name: slider.val})

        script_path = os.path.dirname(os.path.realpath(__file__))
        timestamp = str(int(time.time()))
        file_name = script_path + "/weather_" + timestamp + ".json"
        print("Exported weather data to json file. Path: " + str(file_name))
        with open(file_name, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)

    def import_json(self):
        '''Import weather json file'''
        root = Tk()
        file = askopenfilename(initialdir=os.getcwd(), title="Select file", filetypes=[("Json Files", "*.json")])
        root.destroy()
        
        if not os.path.exists(file):
            return

        f = open(file,)
        data = json.load(f)

        sliders = self.hud.sliders

        for slider in sliders:
            for d in data:
                if slider.name == d:
                    slider.val = data[d]

        print("Imported weather data: " + str(file))
        self.hud.force_tick_next_frame()

    def update_friction(self, iciness):
        '''Update all vehicle tire friction values'''
        actors = self.world.get_actors()
        friction = 1 - iciness / 5

        # When friction level is 0 (1.0) change it to 2.0 
        # which is default Carla friction value
        if friction == 1.0:
            friction = 2.0

        for actor in actors:
            if 'vehicle' in actor.type_id:
                vehicle = actor
                physics_control = vehicle.get_physics_control()

                # loop through all vehicle wheels and set new tire_friction value
                wheel_count = len(physics_control.wheels)
                wheels = []
                for i in range(wheel_count):
                    wheel = physics_control.wheels[i]
                    wheel.tire_friction = friction
                    wheels.append(wheel)

                physics_control.wheels = wheels
                vehicle.apply_physics_control(physics_control)

    def tick(self, clock, hud):
        self.hud.tick(self, clock, hud)

    def render(self, world, display, weather):
        self.hud.render(world, display, weather)

    def toggle_static_tiretracks(self):
        '''Toggle static tiretracks on snowy roads on/off
        This is wrapped around try - expect block
        just in case someone runs this script elsewhere
        world.set_static_tiretracks() is WinterSim project specific Python API command 
        and does not work on default Carla simulator'''
        self.static_tiretracks_enabled ^= True
        try:
            self.world.set_static_tiretracks(self.static_tiretracks_enabled)
            text = "Static tiretracks enabled" if self.static_tiretracks_enabled else "Static tiretracks disabled"
            self.hud.notification(text)
        except AttributeError:
            print("'set_static_tiretracks()' has not been implemented. This is WinterSim specific Python API command.")

    def on_press(self, key):
        '''pynput on button pressed callback
        pygame inputs are not registered if window is out of focus
        so we use pynput to detect few keys that need to get registered
        even when the window has no focus'''
        try:
            if key == keyboard.Key.f5:
                self.toggle_static_tiretracks()
                for box in self.hud.boxes:
                    box.checked ^= True
            elif key.char == "c":
                self.next_weather(reverse=False)
            elif key.char == "b":
                self.realtime_weather()
        except:
            pass

# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================

class KeyboardControl(object):
    """Class that handles keyboard input."""
    def parse_events(self, world, hud):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                # check if sliders hit
                for slider in hud.sliders:
                    if slider.button_rect.collidepoint(pos):
                        slider.hit = True

                # check if checkboxes hit
                for box in hud.boxes:
                    if box.update_checkbox(pos):
                        world.toggle_static_tiretracks()

            elif event.type == pygame.MOUSEBUTTONUP:
                if hud.ice_slider.hit:                                  # if road iciness slider is moved
                    world.update_friction(hud.ice_slider.val)
                for slider in hud.sliders:
                    slider.hit = False                                  # slider moving stopped
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                if event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_o and pygame.key.get_mods() & KMOD_CTRL:
                    world.import_json()
                elif event.key == K_s and pygame.key.get_mods() & KMOD_CTRL:
                    world.export_json()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

def game_loop(args):
    # position offset for pygame window
    x = 1290
    y = 50
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x,y)
    pygame.init()
    pygame.font.init()
    world = None
    listener = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)
        display.fill((0,0,0))
        pygame.display.flip()

        hud = weather_hud.InfoHud(args.width, args.height, display)
        world = World(client.get_world(), hud, args)                        # instantiate our world object
        controller = KeyboardControl()                                      # controller for changing weather presets
        current_weather = client.get_world().get_weather()
        weather = weather_hud.Weather(current_weather)                      # weather object to update carla weather with sliders
        hud.setup(current_weather, world.filtered_map_name)
        clock = pygame.time.Clock()

        listener = keyboard.Listener(on_press=world.on_press)               # start listening keyboard inputs
        listener.start()               
        
        while True:
            clock.tick_busy_loop(30)
            if controller.parse_events(world, hud):
                return
            world.tick(clock, hud)
            world.render(world, display, weather)
            pygame.display.flip()

    finally:
        if listener is not None:
            listener.stop()
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
        default='620x720',
        help='window resolution (default: 620x720)') # note. UI does not scale properly with resolution!
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