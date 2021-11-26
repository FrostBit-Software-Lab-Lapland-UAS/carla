#!/usr/bin/env python

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>

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

import pygame
import math
import carla
import re

# Slider constants
SLIDER_RIGHT_OFFSET = 120
SLIDER_SIZE = 120
SLIDER_Y = 15

# Color constants
BLACK = (0, 0, 0)
ORANGE = (255, 183, 0)
WHITE = (255, 255, 255)
GREY = (75, 75, 75)
BLUE = (0, 0, 255)

DIR_ARR = ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
DIR_ARR2 = ["North","Nort-East", "East", "South-East", "South","South-West", "West","North-West"]

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

# RH = Relative Humidity
# T  = Temperature
# TD = Dew point

# https://stackoverflow.com/questions/27288021/formula-to-calculate-dew-point-from-temperature-and-humidity
def get_approx_dew_point(T, RH):
    td =  (T-(14.55 + 0.114 * T)*(1-(0.01*RH))-pow(((2.5+0.007*T)*(1-(0.01*RH))),3)-(15.9+0.117*T)*pow((1-(0.01*RH)), 14))
    return td

# https://earthscience.stackexchange.com/questions/20577/relative-humidity-approximation-from-dew-point-and-temperature
def get_approx_relative_humidity(T, TD):
    rh = int(100*(math.exp((17.625*TD)/(243.04+TD))/math.exp((17.625*T)/(243.04+T))))
    return rh

# https://bmcnoldy.rsmas.miami.edu/Humidity.html
def get_approx_temp(TD, RH):
    t = 243.04*(((17.625*TD)/(243.04+TD))-math.log(RH/100))/(17.625+math.log(RH/100)-((17.625*TD)/(243.04+TD)))
    return t

def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]

def degrees_to_compass_names(num):
    val=int((num/22.5)+.5)
    return DIR_ARR[(val % 16)]

def degrees_to_compass_names_simple(angle):
    index = round((angle + 360 if angle % 360 else angle) / 45) % 8
    return DIR_ARR2[index]

# ==============================================================================
# -- INFO_HUD -------------------------------------------------------------
# ==============================================================================

class InfoHud(object):
    
    def __init__(self, width, height, display):
        self.dim = (width, height)
        self.screen = display
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self.preset_slider = Slider
        self.temp_slider = Slider
        self.dewpoint_slider = Slider
        self.humidity = 0
        self.snow_amount_slider = Slider
        self.ice_slider = Slider
        self.precipitation_slider = Slider
        self.fog_slider = Slider
        self.fog_falloff = Slider
        self.wind_slider = Slider
        self.wind_dir_slider = Slider
        self.particle_slider = Slider
        self.time_slider = Slider
        self.month_slider = Slider
        self.sliders = []
        self._font_mono = pygame.font.Font(mono, 18 if os.name == 'nt' else 18)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.logo = pygame.image.load('images/WinterSim_White_Color.png')
        self.logo = pygame.transform.scale(self.logo, (262,61))
        self.logo_rect = self.logo.get_rect()
        self._info_text = []
        self._weather_presets = []
        self.preset_names = []
        self.muonio = False
        self.current_direction = "N"
        self.force_tick = False
        self.gap = 90
        
        self._weather_presets_all = find_weather_presets()
        for preset in self._weather_presets_all:
            if preset[0].temperature <= 0: # only get winter presets
                self._weather_presets.append(preset)
                self.preset_names.append(str(preset[1]))
        self.preset_names.append("Custom") # add 'Custom' prest for the last list index, 
                                           # this is shown if sliders are changed manually

        self.preset_count = len(self._weather_presets)
        self.months = [
            'January','February','March','April','May','June',
            'July','August','September','October','November','December']

        self.muonio_sun_positions = [
            [12.5, 1.36, -43.6],  [12.5, 9.25, -35.11],
            [12.5, 20.13, -24.24],[12.5, 31.99, -12.37],
            [12.5, 41.03, -2.74], [12.5, 45.39, 1.60],
            [12.5, 43.51, 0.05],  [12.5, 35.97, -8.07],
            [12.5, 24.94, -19.04],[12.5, 13.44, -30.56],
            [12.5, 3.66, -40.75], [12.5, -0.56, -45.32]]

        self.rovaniemi_sun_positions = [
            [12.5, 2.37, -44.6],   [12.5, 9.38, -37.29],
            [12.5, 19.60, -27.48], [12.5, 33.05, -14.16],
            [12.5, 41.31, -3.84],  [12.5, 46.84, 1.46],
            [12.5, 45.01, -1.06],  [12.5, 36.14, -9.35],
            [12.5, 26.32, -19.63], [12.5, 15.62, -30.60],
            [12.5, 4.56, -42.72],  [12.5, 0.65, -46.77]]

        # create checkb
        self.boxes = []
        self.button = Checkbox(self.screen, 20, 650, 0, caption='Static Tiretracks (F5)')
        self.boxes.append(self.button)
        self.make_sliders()

    def setup(self, preset, map_name):
        self.update_sliders(preset)
        self.filtered_map_name = map_name
        self.muonio = self.filtered_map_name == "Muonio"

    def get_slider_offset(self, offset=40):
        '''Return offset between each slider'''
        self.gap += offset
        return self.gap

    def make_sliders(self):
        '''Make sliders and add them in to list'''
        self.preset_slider = Slider(self, "Preset", 0, self.preset_count, 0, self.gap)
        self.temp_slider = Slider(self, "Temperature", 0, 40, -40, self.get_slider_offset())
        self.dewpoint_slider = Slider(self, "Dewpoint", 0, 40, -40, self.get_slider_offset())
        self.ice_slider = Slider(self, "Friction", 0, 4, 0, self.get_slider_offset())
        self.precipitation_slider = Slider(self, "Precipitation", 0, 100, 0, self.get_slider_offset())
        self.snow_amount_slider = Slider(self, "Snow amount", 0, 100, 0, self.get_slider_offset())
        self.particle_slider = Slider(self, "Snow p. size", 0.5, 7, 0.5, self.get_slider_offset())
        self.fog_slider = Slider(self, "Fog", 0, 100, 0, self.get_slider_offset())
        self.fog_falloff = Slider(self, "Fog falloff", 0.0, 2.0, 0.0, self.get_slider_offset())
        self.wind_slider = Slider(self, "Wind intensity", 0, 70, 0, self.get_slider_offset())
        self.wind_dir_slider = Slider(self, "Wind direction", 0, 360, 0, self.get_slider_offset())
        self.time_slider = Slider(self, "Time", 10, 24, 0, self.get_slider_offset())
        self.month_slider = Slider(self, "Month", 0, 11, 0, self.get_slider_offset())

    def update_sliders(self, preset, month=None, clock=None):
        '''Update slider positions if weather preset is changed
        wrapped in try-expect block just in-case preset doesn't have certain weather parameter'''
        try:
            self.snow_amount_slider.val = preset.snow_amount
            self.ice_slider.val = preset.ice_amount
            self.temp_slider.val = preset.temperature
            self.precipitation_slider.val = preset.precipitation
            self.fog_slider.val = preset.fog_density
            self.fog_falloff.val = preset.fog_falloff

            self.wind_slider.val = preset.wind_intensity * 100.0
            if self.wind_slider.val >= 70.0:
                self.wind_slider.val = 70.0
            
            self.particle_slider.val = preset.particle_size
            self.humidity = preset.relative_humidity
            self.dewpoint_slider.val = preset.dewpoint
            self.wind_dir_slider.val = preset.wind_direction

            self.current_direction = degrees_to_compass_names_simple(self.wind_dir_slider.val)

            if month and clock:
                self.month_slider.val = month
                self.time_slider.val = clock

        except AttributeError as e:
            print(e, "not implemented")

    def get_month_sundata(self, val):
        if self.muonio:
            return self.months[val], self.muonio_sun_positions[val]
        else:
            return self.months[val], self.rovaniemi_sun_positions[val]

    # Update hud text values
    def tick(self, world, clock, hud):
        self._notifications.tick(world, clock)
        month, sundata = self.get_month_sundata(int(hud.month_slider.val))
        preset = hud.preset_names[int(hud.preset_slider.val)]
        self._info_text = [
            '      Weather Control',
            '----------------------------',
            '',
            'Preset: {}'.format(preset),
            '',
            'Temperature: {}°C'.format(round(hud.temp_slider.val,1)),
            '',
            'Humidity: {}%'.format(round((hud.humidity), 1)),
            '',
            'Dewpoint: {}°'.format(round((hud.dewpoint_slider.val), 1)),
            '',
            'Friction level: {}'.format(int(hud.ice_slider.val)),
            '',
            'Precipitation: {}%'.format(round((hud.precipitation_slider.val), 1)),
            '',
            'Amount of Snow: {} cm'.format(round(hud.snow_amount_slider.val)),
            'Snow particle size: {} mm'.format(round((hud.particle_slider.val), 1)),
            '',
            'Fog: {}%'.format(int(hud.fog_slider.val)),
            'Fog Falloff: {}'.format(round((hud.fog_falloff.val), 1)),
            '',
            'Wind Intensity: {} m/s'.format(round((hud.wind_slider.val/10), 1)),
            #'Wind Direction: {}°'.format(round((hud.wind_dir_slider.val), 1)),
            'Wind Direction: {}'.format(self.current_direction),
            '',
            'Time: {}:00'.format(int(hud.time_slider.val)),
            'Month: {}'.format(month),
            '',
            '----------------------------',
            '',
            'Press C to change',
            'weather preset',
            '',
            'Press B to get real time',
            'weather']

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def force_tick_next_frame(self):
        self.force_tick = True

    def render(self, world, display, weather):
        """Render hud texts into pygame window"""

        display_rect = display.get_rect()
        self.logo_rect.topright = tuple(map(lambda i, j: i - j, display_rect.topright, (5,-2))) 
        display.blit(self.logo, self.logo_rect)

        info_surface = pygame.Surface((345, self.dim[1]))
        info_surface.set_alpha(100)
        info_surface.fill(GREY)
        display.blit(info_surface, (0, 0))
        v_offset = 4           
        for item in self._info_text:
            surface = self._font_mono.render(item, True, WHITE)
            display.blit(surface, (18, v_offset + 10))
            v_offset += 18
        self._notifications.render(display)

        # render checkboxes to pygame window
        for box in self.boxes:
            box.render_checkbox()

        # render sliders to pygame window
        if self.force_tick:
            for slider in self.sliders:
                weather.tick(self, world, world._weather_presets[0], slider)
                self.force_tick = False
            world.world.set_weather(weather.weather)

        # render sliders to pygame window
        for slider in self.sliders:
            if slider.hit:
                slider.move()
                weather.tick(self, world, world._weather_presets[0], slider)
                world.world.set_weather(weather.weather)
            slider.render(display, slider)

# ==============================================================================
# -- Checkbox ----------------------------------------------------------------
# ==============================================================================

class Checkbox:

    def __init__(self, surface, x, y, idnum, color=(230, 230, 230),
        caption="", outline_color=(255, 255, 255), check_color=(0, 0, 0),
        font_size=16, font_color=(255, 255, 255), text_offset=(20, 1), checkbox_size=12):
        self.surface = surface
        self.x = x
        self.y = y
        self.color = color
        self.caption = caption
        self.oc = outline_color
        self.cc = check_color
        self.fs = font_size
        self.fc = font_color
        self.to = text_offset
        default_font = 'courier'
        self.ft = default_font
        self.checkbox_size = checkbox_size
        self.idnum = idnum
        self.checkbox_obj = pygame.Rect(self.x, self.y, checkbox_size, checkbox_size)
        self.checkbox_outline = self.checkbox_obj.copy()
        self.checked = True 

    def _draw_button_text(self):
        self.font = pygame.font.SysFont(self.ft, self.fs)
        self.font_surf = self.font.render(self.caption, True, self.fc)
        w, h = self.font.size(self.caption)
        self.font_pos = (self.x + self.to[0], self.y + 12 / 2 - h / 2 +  self.to[1])
        self.surface.blit(self.font_surf, self.font_pos)

    def render_checkbox(self):
        if self.checked:
            pygame.draw.rect(self.surface, self.color, self.checkbox_obj)
            pygame.draw.rect(self.surface, self.oc, self.checkbox_outline, 1)
            pygame.draw.circle(self.surface, self.cc, (self.x + 6, self.y + 6), 4)
        else:
            pygame.draw.rect(self.surface, self.color, self.checkbox_obj)
            pygame.draw.rect(self.surface, self.oc, self.checkbox_outline, 1)

        self._draw_button_text()

    def update_checkbox(self, pos):
        x, y = pos
        px, py, w, h = self.checkbox_obj
        if px < x < px + w and py < y < py + w:
            self.checked ^= True
            return True
        else:
            return False

# ==============================================================================
# -- SliderObject -------------------------------------------------------------
# ==============================================================================

class Slider():

    def __init__(self, InfoHud, name, val, maxi, mini, pos):
        self.hud = InfoHud
        self.font = pygame.font.SysFont("ubuntumono", 20)
        self.name = name
        self.val = val      # start value
        self.maxi = maxi    # maximum at slider position right
        self.mini = mini    # minimum at slider position left
        self.xpos = 358     # x-location on screen
        self.ypos = pos
        self.surf = pygame.surface.Surface((250, 100))
        # The hit attribute indicates slider movement due to mouse interaction.
        self.hit = False    

        self.txt_surf = self.font.render(name, 1, WHITE)
        self.txt_rect = self.txt_surf.get_rect()
        self.txt_rect.left = 6
        self.txt_rect.top = 8

        # Static graphics - slider background #
        pygame.draw.rect(self.surf, ORANGE, [SLIDER_RIGHT_OFFSET, SLIDER_Y, SLIDER_SIZE, 1], 0)

        #borders
        line_width = 1
        width = 250
        height = 27

        # top line #first = starting point on width, second = starting point on height,
        # third = width, fourth = height
        pygame.draw.rect(self.surf, WHITE, [0,0, width,line_width])                             # top line
        pygame.draw.rect(self.surf, WHITE, [0, height-line_width,width,line_width])             # bottom line
        pygame.draw.rect(self.surf, WHITE, [0,0, line_width, height])                           # left line
        pygame.draw.rect(self.surf, WHITE, [width-line_width,0,line_width, height+line_width])  # right line

        # this surface never changes
        self.surf.blit(self.txt_surf, self.txt_rect)  

        # dynamic graphics - button surface #
        self.button_surf = pygame.surface.Surface((40, 40))
        self.button_surf.fill((1, 1, 1))
        self.button_surf.set_colorkey((1, 1, 1))
        pygame.draw.rect(self.button_surf, WHITE, [18, 0, 6, 15], 0)

        self.hud.sliders.append(self)

    def render(self, screen, slider):
        """Draw sliders"""
        surf = self.surf.copy()
        pos = (SLIDER_RIGHT_OFFSET+int((self.val-self.mini) / (self.maxi-self.mini) * SLIDER_SIZE), 29)
        self.button_rect = self.button_surf.get_rect(center=pos)
        surf.blit(self.button_surf, self.button_rect)
        self.button_rect.move_ip(self.xpos, self.ypos)
        screen.blit(surf, (self.xpos, self.ypos))

    def move(self):
        """The dynamic part; reacts to movement of the slider button."""
        self.val = (pygame.mouse.get_pos()[0] - self.xpos - SLIDER_RIGHT_OFFSET) / SLIDER_SIZE * (self.maxi - self.mini) + self.mini
        if self.val < self.mini:
            self.val = self.mini
        if self.val > self.maxi:
            self.val = self.maxi
 
# ==============================================================================
# -- SunObject -------------------------------------------------------------
# ==============================================================================

class Sun(object):

    def __init__(self, azimuth, altitude):
        self.azimuth = azimuth
        self.altitude = altitude

    def SetSun(self, highest_time, sun_highest, sun_lowest, clock):
        '''handler for sun altitude and azimuth.'''
        if clock is highest_time:
            self.altitude = sun_highest
        elif clock < highest_time:
            D = highest_time - (highest_time - clock)
            X = float(D/highest_time)
            Y = math.sin(X * 87 * math.pi / 180)
            A = sun_highest
            B = sun_lowest
            self.altitude = (Y * A) + ((1-Y) * B)
        else:
            D = highest_time - (clock - highest_time)
            X = float(D / highest_time)
            Y = math.sin(X * 87 * math.pi / 180)
            A = sun_highest
            B = sun_lowest
            self.altitude = (Y * A) + ((1 - Y) * B)
        self.azimuth = 348.98 + clock * 15
        if self.azimuth > 360: 
            self.azimuth -= 360    
    def __str__(self):
        return 'Sun(alt: %.2f, azm: %.2f)' % (self.altitude, self.azimuth)

# ==============================================================================
# -- WeatherObject -------------------------------------------------------------
# ==============================================================================

class Weather(object):

    def __init__(self, weather):
        self.weather = weather
        self.sun = Sun(weather.sun_azimuth_angle, weather.sun_altitude_angle)

    def tick(self, hud, world, preset, slider):
        '''This is called always when slider is being moved'''

        # if preset slider is the one being moved, change other sliders as well
        # else set preset_slider to Custom
        if slider.name == 'Preset':
            world.set_weather(int(hud.preset_slider.val))
        else:
            hud.preset_slider.val = hud.preset_count

        # only update time / month when either of those sliders touched
        if slider.name == "Time" or slider.name == "Month":
            month, sundata = hud.get_month_sundata(int(hud.month_slider.val))
            clock = hud.time_slider.val
            self.sun.SetSun(sundata[0],sundata[1],sundata[2], clock)

        preset = preset[0]
        self.weather.cloudiness = hud.precipitation_slider.val
        self.weather.precipitation = hud.precipitation_slider.val
        self.weather.precipitation_deposits = hud.precipitation_slider.val
        self.weather.wind_intensity = hud.wind_slider.val / 100.0
        self.weather.fog_density = hud.fog_slider.val
        self.weather.fog_falloff= hud.fog_falloff.val
        self.weather.wetness = preset.wetness
        self.weather.sun_azimuth_angle = self.sun.azimuth
        self.weather.sun_altitude_angle = self.sun.altitude
        self.weather.snow_amount = hud.snow_amount_slider.val
        self.weather.temperature = hud.temp_slider.val
        self.weather.ice_amount = hud.ice_slider.val
        self.weather.particle_size = hud.particle_slider.val
        self.weather.humidity = hud.humidity
        self.weather.dewpoint = hud.dewpoint_slider.val

        hud.current_direction = degrees_to_compass_names_simple(hud.wind_dir_slider.val)
        self.weather.wind_direction = hud.wind_dir_slider.val

        # Adjust humidity correctly when either 
        # temperature or dewpoint slider changed
        if slider.name == 'Temp' or slider.name == 'Dewpoint':
            val = get_approx_relative_humidity(self.weather.temperature, self.weather.dewpoint)
            if val > 100.0:
                val = 100
            self.weather.humidity = val
            hud.humidity = val

    def set_weather_manually(self, hud, weather_values):
        # weather_values must be in correct order!
        self.weather.temperature = weather_values[0]
        self.weather.precipitation = weather_values[1]
        self.weather.precipitation_deposits = weather_values[1]
        self.weather.wind_intensity = weather_values[2] / 100.0
        self.weather.particle_size = weather_values[3]
        self.weather.fog_density = weather_values[4]
        self.weather.snow_amount = weather_values[5]
        self.weather.humidity = weather_values[6]
        self.weather.wind_direction = weather_values[7]
        month, sundata = hud.get_month_sundata(weather_values[9])
        self.sun.SetSun(sundata[0],sundata[1],sundata[2], weather_values[8])
        self.weather.wetness = 0
        self.weather.sun_azimuth_angle = self.sun.azimuth
        self.weather.sun_altitude_angle = self.sun.altitude
        self.weather.ice_amount = 0
       
    def __str__(self):
        return '%s %s' % (self._sun, self._storm)

# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================

class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)