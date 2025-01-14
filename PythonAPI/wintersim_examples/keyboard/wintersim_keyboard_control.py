#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import carla
import math

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_F1
    from pygame.locals import K_F4
    from pygame.locals import K_F5
    from pygame.locals import K_F6
    from pygame.locals import K_F8
    from pygame.locals import K_F9
    from pygame.locals import K_F11
    from pygame.locals import K_F12
    from pygame.locals import K_LEFT
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_g
    from pygame.locals import K_h
    from pygame.locals import K_l
    from pygame.locals import K_n
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame.locals import K_x
    from pygame.locals import K_z
    from pygame.locals import K_t
    from pygame.locals import K_r

except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

class KeyboardControl(object):
    """Class that handles keyboard input."""
    def __init__(self, world, start_in_autopilot):
        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            self._lights = carla.VehicleLightState.NONE
            world.player.set_light_state(self._lights)
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        world.hud_wintersim.notification("Press 'H' for help.", seconds=4.0)

    def parse_events(self, world, clock):
        if isinstance(self._control, carla.VehicleControl):
            current_lights = self._lights
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                elif event.key == K_F1:
                    world.hud_wintersim.toggle_info()
                elif event.key == K_F4:
                    world.toggle_multi_sensor_view(sensor_option_index=0)
                elif event.key == K_F5:
                    world.toggle_static_tiretracks()
                elif event.key == K_F6:
                    world.clear_dynamic_tiretracks()
                elif event.key == K_F8:
                    world.toggle_camera_windows()
                elif event.key == K_F9:
                    world.toggle_open3d_lidar()
                elif event.key == K_F11:
                    world.take_fullscreen_screenshot()
                elif event.key == K_F12:
                    world.toggle_server_rendering()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    world.hud_wintersim.help_text.toggle()
                elif event.key == K_TAB:
                    if not world.multi_sensor_view_enabled:
                        world.camera_manager.toggle_camera()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_c:
                    world.next_weather()
                elif event.key == K_g:
                    world.toggle_radar()
                elif event.key == K_n:
                    world.camera_manager.next_sensor()
                elif event.key == K_r:
                    world.teleport_vehicle()
                    continue
                elif event.key == K_BACKSPACE:
                    world.change_vehicle()
                elif event.key == K_t:
                    try:
                        world.show_vehicle_telemetry ^= True
                        world.player.show_debug_telemetry(world.show_vehicle_telemetry)
                    except AttributeError:
                        print("'show_debug_telemetry)' has not been implemented. This only works in CARLA version 0.9.12 and above")
                elif event.key > K_0 and event.key <= K_9:
                    if not world.multi_sensor_view_enabled:
                        world.camera_manager.set_sensor(event.key - 1 - K_0)
                    else:
                        index = event.key - 1 - K_0
                        if index <= 3:
                            world.toggle_multi_sensor_view(sensor_option_index=event.key - 1 - K_0, reload = True)

                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_p and not pygame.key.get_mods() & KMOD_CTRL:
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud_wintersim.notification(
                            'Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
                    elif event.key == K_l and pygame.key.get_mods() & KMOD_CTRL:
                        current_lights ^= carla.VehicleLightState.Special1
                    elif event.key == K_l and pygame.key.get_mods() & KMOD_SHIFT:
                        current_lights ^= carla.VehicleLightState.HighBeam
                    elif event.key == K_l:                                      # Use 'L' key to switch between lights:
                        if not self._lights & carla.VehicleLightState.Position: # closed -> position -> low beam -> fog
                            world.hud_wintersim.notification("Position lights") 
                            current_lights |= carla.VehicleLightState.Position
                        else:
                            world.hud_wintersim.notification("Low beam lights")
                            current_lights |= carla.VehicleLightState.LowBeam
                        if self._lights & carla.VehicleLightState.LowBeam:
                            world.hud_wintersim.notification("Fog lights")
                            current_lights |= carla.VehicleLightState.Fog
                        if self._lights & carla.VehicleLightState.Fog:
                            world.hud_wintersim.notification("Lights off")
                            current_lights ^= carla.VehicleLightState.Position
                            current_lights ^= carla.VehicleLightState.LowBeam
                            current_lights ^= carla.VehicleLightState.Fog
                    elif event.key == K_z:
                        current_lights ^= carla.VehicleLightState.LeftBlinker
                    elif event.key == K_x:
                        current_lights ^= carla.VehicleLightState.RightBlinker

        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time(), world)
                self._control.reverse = self._control.gear < 0
                # Set automatic control-related vehicle lights
                if self._control.brake:
                    current_lights |= carla.VehicleLightState.Brake
                else: # Remove the Brake flag
                    current_lights &= ~carla.VehicleLightState.Brake
                if self._control.reverse:
                    current_lights |= carla.VehicleLightState.Reverse
                else: # Remove the Reverse flag
                    current_lights &= ~carla.VehicleLightState.Reverse
                if current_lights != self._lights: # Change the light state only if necessary
                    self._lights = current_lights
                    world.player.set_light_state(carla.VehicleLightState(self._lights))
            world.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds, world):
        v = world.player.get_velocity()
        speed = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
        if keys[K_UP] or keys[K_w]:
            if(self._control.gear == -1):
                self._control.gear = 1
            if(self._control.reverse):
                self._control.reverse = False
            self._control.throttle = min(self._control.throttle + 0.04, 1)
        elif not self._control.reverse:
            self._control.throttle = 0.0

        if keys[K_DOWN] or keys[K_s]:
            if(int(round(speed)) <= 0 or self._control.reverse):
                self._control.brake = 0
                if self._control.gear != -1:
                    self._control.gear = -1
                self._control.throttle = min(self._control.throttle + 0.01, 1)
                self._control.reverse = True
            elif not self._control.reverse:
                self._control.brake = min(self._control.brake + 0.2, 1)
        else:
            self._control.gear = 1
            self._control.brake = 0

        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            if self._steer_cache > 0:
                self._steer_cache = 0
            else:
                self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            if self._steer_cache < 0:
                self._steer_cache = 0
            else:
                self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.hand_brake = keys[K_SPACE]

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)