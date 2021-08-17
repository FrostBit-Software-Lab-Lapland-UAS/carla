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
        self.temp_slider = Slider
        self.dewpoint_slider = Slider
        self.humidity = 0
        self.snow_amount_slider = Slider
        self.ice_slider = Slider
        self.precipitation_slider = Slider
        self.fog_slider = Slider
        self.wind_slider = Slider
        self.particle_slider = Slider
        self.time_slider = Slider
        self.month_slider = Slider
        self.sliders = []
        self._font_mono = pygame.font.Font(mono, 18 if os.name == 'nt' else 18)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self._info_text = []
        self.months = [
            'January','February','March','April','May','June',
            'July','August','September','October','November','December'
            ]
        self.sun_positions = [
            [12.5, 1.36, -43.6],[12.5, 9.25, -35.11],
            [12.5, 20.13, -24.24],[12.5, 31.99, -12.37],
            [12.5, 41.03, -2.74],[12.5, 45.39, 1.60],
            [12.5, 43.51, 0.05],[12.5, 35.97, -8.07],
            [12.5, 24.94, -19.04],[12.5, 13.44, -30.56],
            [12.5, 3.66, -40.75],[12.5, -0.56, -45.32]
            ]

        # create checkboxe(s)
        self.boxes = []
        self.button = Checkbox(self.screen, 20, 610, 0, caption='Static Tiretracks (F5)')
        self.boxes.append(self.button)

    # Make sliders and add them in to list
    def make_sliders(self):
        self.temp_slider = Slider("Temp", 0, 40, -40, 10)
        self.dewpoint_slider = Slider("Dewpoint", 0, 40, -40, 77)
        self.ice_slider = Slider("Road Ice", 0, 5, 0, 144)
        self.precipitation_slider = Slider("Precipitation", 0, 100, 0, 211)
        self.snow_amount_slider = Slider("Snow amount", 0, 100, 0, 278)
        self.fog_slider = Slider("Fog", 0, 100, 0, 345)
        self.wind_slider = Slider("Wind", 0, 100, 0, 412)
        self.particle_slider = Slider("Snow particle size", 0.5, 7, 0.5, 479)
        self.time_slider = Slider("Time", 10, 24, 0, 546)
        self.month_slider = Slider("Month", 0, 11, 0, 613)
        self.sliders = [
            self.temp_slider, self.dewpoint_slider,
            self.ice_slider, self.precipitation_slider, self.snow_amount_slider,self.fog_slider, 
            self.wind_slider, self.particle_slider, 
            self.time_slider, self.month_slider
            ]

    # Update slider positions if weather is changed without moving sliders
    def update_sliders(self, preset, month=None, clock=None):
        self.snow_amount_slider.val = preset.snow_amount
        self.ice_slider.val = preset.ice_amount
        self.temp_slider.val = preset.temperature
        self.precipitation_slider.val = preset.precipitation
        self.fog_slider.val = preset.fog_density
        self.wind_slider.val = preset.wind_intensity * 100.0
        self.particle_slider.val = preset.particle_size
        self.humidity = preset.relative_humidity
        self.dewpoint_slider.val = preset.dewpoint
        if month and clock:
            self.month_slider.val = month
            self.time_slider.val = clock

    def get_month(self, val): 
        return self.months[val], self.sun_positions[val]

    # Update hud text values
    def tick(self, world, clock, hud): 
        self._notifications.tick(world, clock)
        month, sundata = self.get_month(int(hud.month_slider.val))
        self._info_text = [
            'Weather Control',
            '----------------------------',
            '',
            'Temperature:  {}°C'.format(round(hud.temp_slider.val,1)),
            '',
            'Humidity: {}%'.format(round((hud.humidity), 1)),
            '',
            'Dewpoint: {}°'.format(round((hud.dewpoint_slider.val), 1)),
            '',
            'Amount of Snow:  {} cm'.format(round(hud.snow_amount_slider.val)),
            '',
            'Iciness:  {}.00%'.format(int(hud.ice_slider.val)),
            '',
            'Precipitation:  {} mm'.format(round((hud.precipitation_slider.val/10), 1)),
            '',
            'Fog:  {}%'.format(int(hud.fog_slider.val)),
            '',
            'Wind Intensity: {}m/s'.format(round((hud.wind_slider.val/10), 1)),
            '',
            'Snow particle size: {}mm'.format(round((hud.particle_slider.val), 1)),
            '',
            'Time: {}:00'.format(int(hud.time_slider.val)),
            '',
            'Month: {}'.format(month),
            '',
            '----------------------------',
            '',
            'Press C to change',
            'weather preset',
            '',
            'Press R to get real time',
            'weather from Muonio']

    # Notification about changing weather preset.
    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    # Render hud texts into pygame window.
    def render(self, display): 
        info_surface = pygame.Surface((345, self.dim[1]))
        info_surface.set_alpha(100)
        info_surface.fill((75, 75, 75))
        display.blit(info_surface, (0, 0))
        v_offset = 4           
        for item in self._info_text:
            surface = self._font_mono.render(item, True, (255, 255, 255))
            display.blit(surface, (18, v_offset + 10))
            v_offset += 18
        self._notifications.render(display)

        # render checkboxes to PyGame
        for box in self.boxes:
            box.render_checkbox()

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
    def __init__(self, name, val, maxi, mini, pos):
        BLACK = (0, 0, 0)
        ORANGE = (255, 183, 0)
        WHITE = (255, 255, 255)
        self.font = pygame.font.SysFont("ubuntumono", 16)
        self.name = name
        self.val = val      # start value
        self.maxi = maxi    # maximum at slider position right
        self.mini = mini    # minimum at slider position left
        self.xpos = 358     # x-location on screen
        self.ypos = pos
        self.surf = pygame.surface.Surface((200, 100))
        # The hit attribute indicates slider movement due to mouse interaction.
        self.hit = False    

        self.txt_surf = self.font.render(name, 1, BLACK)
        self.txt_rect = self.txt_surf.get_rect(center=(90, 17))

        # Static graphics - slider background #
        pygame.draw.rect(self.surf, WHITE, [10, 7, 160, 20], 3)
        pygame.draw.rect(self.surf, WHITE, [10, 7, 160, 20], 0)
        pygame.draw.rect(self.surf, ORANGE, [10, 40, 160, 1], 0)

        #borders
        line_width = 1
        width = 180
        height = 53

        # top line #first = starting point on width, second = starting point on height,
        # third = width, fourth = height
        pygame.draw.rect(self.surf, WHITE, [0,0,width,line_width])
        # bottom line
        pygame.draw.rect(self.surf, WHITE, [0,height-line_width,width,line_width])
        # left line
        pygame.draw.rect(self.surf, WHITE, [0,0,line_width, height])
        # right line
        pygame.draw.rect(self.surf, WHITE, [width-line_width,0,line_width, height+line_width])

        # this surface never changes
        self.surf.blit(self.txt_surf, self.txt_rect)  
        self.surf.set_alpha(200)

        # dynamic graphics - button surface #
        self.button_surf = pygame.surface.Surface((20, 40))
        self.button_surf.fill((1, 1, 1))
        self.button_surf.set_colorkey((1, 1, 1))
        pygame.draw.rect(self.button_surf, WHITE, [6,23,6,15], 0)

    def draw(self, screen, slider):
        """ Combination of static and dynamic graphics in a copy ofthe basic slide surface"""
        # static
        surf = self.surf.copy()
        # dynamic
        pos = (10+int((self.val-self.mini)/(self.maxi-self.mini)*160), 29)
        self.button_rect = self.button_surf.get_rect(center=pos)
        surf.blit(self.button_surf, self.button_rect)
        # Move of button box to correct screen position.
        self.button_rect.move_ip(self.xpos, self.ypos)  
        # screen
        screen.blit(surf, (self.xpos, self.ypos))

    def move(self):
        """The dynamic part; reacts to movement of the slider button."""
        self.val = (pygame.mouse.get_pos()[0] - self.xpos - 10) / 160 * (self.maxi - self.mini) + self.mini
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

    # Overal handler for sun altitude and azimuth.
    def SetSun(self, highest_time, sun_highest, sun_lowest, clock): 
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
        self.sun = Sun(weather.sun_azimuth_angle, weather.sun_altitude_angle) #instantiate sun object and pass angles 

    # This is called always when slider is being moved.
    def tick(self, hud, preset, slider): 
        preset = preset[0]
        month, sundata = hud.get_month(int(hud.month_slider.val))
        clock = hud.time_slider.val
        self.sun.SetSun(sundata[0],sundata[1],sundata[2], clock)
        self.weather.cloudiness = hud.precipitation_slider.val
        self.weather.precipitation = hud.precipitation_slider.val
        self.weather.precipitation_deposits = hud.precipitation_slider.val
        self.weather.wind_intensity = hud.wind_slider.val /100.0
        self.weather.fog_density = hud.fog_slider.val
        self.weather.wetness = preset.wetness
        self.weather.sun_azimuth_angle = self.sun.azimuth
        self.weather.sun_altitude_angle = self.sun.altitude
        self.weather.snow_amount = hud.snow_amount_slider.val
        self.weather.temperature = hud.temp_slider.val
        self.weather.ice_amount = hud.ice_slider.val
        self.weather.particle_size = hud.particle_slider.val
        self.weather.humidity = hud.humidity
        self.weather.dewpoint = hud.dewpoint_slider.val
        if slider.name == 'Temp' or slider.name == 'Dewpoint':
            val = get_approx_relative_humidity(self.weather.temperature, self.weather.dewpoint)
            if val > 100.0:
                val = 100
            self.weather.humidity = val
            hud.humidity = val


    def set_weather_manually(self, hud, temp, precipitation, wind, particle_size, visibility, snow, humidity, clock, m):
        month, sundata = hud.get_month(m)
        self.sun.SetSun(sundata[0],sundata[1],sundata[2], clock)
        #self.weather.cloudiness = cloudiness
        self.weather.precipitation = precipitation
        self.weather.precipitation_deposits = precipitation
        self.weather.wind_intensity = wind / 100.0
        self.weather.fog_density = visibility
        self.weather.particle_size = particle_size
        self.weather.wetness = 0
        self.weather.sun_azimuth_angle = self.sun.azimuth
        self.weather.sun_altitude_angle = self.sun.altitude
        self.weather.snow_amount = snow
        self.weather.temperature = temp
        self.weather.ice_amount = 0
        self.weather.humidity = humidity
       
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