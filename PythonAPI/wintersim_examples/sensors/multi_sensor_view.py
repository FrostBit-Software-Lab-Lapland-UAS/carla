#!/usr/bin/env python
# Copyright (c) 2020 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
Script that render multiple sensors in the same pygame window

By default, it renders four cameras, one LiDAR and one Semantic LiDAR.
It can easily be configure for any different number of sensors.
"""

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
import numpy as np

try:
    import pygame
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

class DisplayManager:
    def __init__(self, display, grid_size, window_size):
        self.display = display
        self.grid_size = grid_size
        self.window_size = window_size
        self.sensor_list = []

    def get_window_size(self):
        return [int(self.window_size[0]), int(self.window_size[1])]

    def get_display_size(self):
        return [int(self.window_size[0] / self.grid_size[1]), int(self.window_size[1] / self.grid_size[0])]

    def get_display_offset(self, gridPos):
        dis_size = self.get_display_size()
        return [int(gridPos[1] * dis_size[0]), int(gridPos[0] * dis_size[1])]

    def add_sensor(self, sensor):
        self.sensor_list.append(sensor)

    def get_sensor_list(self):
        return self.sensor_list

    def render(self):
        if not self.render_enabled():
            return

        for s in self.sensor_list:
            s.render()

    def destroy(self):
        for s in self.sensor_list:
            s.destroy()

    def render_enabled(self):
        return self.display != None

class SensorManager:
    def __init__(self, world, display_manager, sensor_type, transform, attached, sensor_options, display_pos):
        self.surface = None
        self.world = world
        self.display_manager = display_manager
        self.display_pos = display_pos
        self.sensor = self.init_sensor(sensor_type, transform, attached, sensor_options)
        self.sensor_options = sensor_options
        self.display_manager.add_sensor(self)

    def init_sensor(self, sensor_type, transform, attached, sensor_options):
        if sensor_type == 'RGBCamera':
            camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
            disp_size = self.display_manager.get_display_size()
            camera_bp.set_attribute('image_size_x', str(disp_size[0]))
            camera_bp.set_attribute('image_size_y', str(disp_size[1]))
            camera_bp.set_attribute('fov', '70')
            for key in sensor_options:
                camera_bp.set_attribute(key, sensor_options[key])
            camera = self.world.spawn_actor(camera_bp, transform, attach_to=attached)
            camera.listen(self.save_rgb_image)
            return camera

        elif sensor_type == 'LiDAR':
            lidar_bp = self.world.get_blueprint_library().find('sensor.lidar.custom_ray_cast')
            lidar_bp.set_attribute('range', '100')
            lidar_bp.set_attribute('dropoff_general_rate', lidar_bp.get_attribute('dropoff_general_rate').recommended_values[0])
            lidar_bp.set_attribute('dropoff_intensity_limit', lidar_bp.get_attribute('dropoff_intensity_limit').recommended_values[0])
            lidar_bp.set_attribute('dropoff_zero_intensity', lidar_bp.get_attribute('dropoff_zero_intensity').recommended_values[0])
            for key in sensor_options:
                lidar_bp.set_attribute(key, sensor_options[key])
            lidar = self.world.spawn_actor(lidar_bp, transform, attach_to=attached)
            lidar.listen(self.save_lidar_image)
            return lidar
        
        elif sensor_type == 'SemanticLiDAR':
            lidar_bp = self.world.get_blueprint_library().find('sensor.lidar.custom_ray_cast_semantic')
            lidar_bp.set_attribute('range', '100')
            for key in sensor_options:
                lidar_bp.set_attribute(key, sensor_options[key])
            lidar = self.world.spawn_actor(lidar_bp, transform, attach_to=attached)
            lidar.listen(self.save_semanticlidar_image)
            return lidar
        
        elif sensor_type == "Radar":
            print("spawning radar")
            radar_bp = self.world.get_blueprint_library().find('sensor.other.radar')
            for key in sensor_options:
                radar_bp.set_attribute(key, sensor_options[key])
            radar = self.world.spawn_actor(radar_bp, transform, attach_to=attached)
            radar.listen(self.save_radar_image)
            return radar
        else:
            return None

    def get_sensor(self):
        return self.sensor

    def save_rgb_image(self, image):
        image.convert(carla.ColorConverter.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype(np.uint8))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        if self.display_manager.render_enabled():
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    def save_lidar_image(self, image):
        disp_size = self.display_manager.get_display_size()
        lidar_range = 2.0*float(self.sensor_options['range'])
        points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0] / 4), 4))
        lidar_data = np.array(points[:, :2])
        lidar_data *= min(disp_size) / lidar_range
        lidar_data += (0.5 * disp_size[0], 0.5 * disp_size[1])
        lidar_data = np.fabs(lidar_data)
        lidar_data = lidar_data.astype(np.int32)
        lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (disp_size[0], disp_size[1], 3)
        lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)
        lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
        if self.display_manager.render_enabled():
            self.surface = pygame.surfarray.make_surface(lidar_img)

    def save_semanticlidar_image(self, image):
        disp_size = self.display_manager.get_display_size()
        lidar_range = 2.0*float(self.sensor_options['range'])
        points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (int(points.shape[0] / 6), 6))
        lidar_data = np.array(points[:, :2])
        lidar_data *= min(disp_size) / lidar_range
        lidar_data += (0.5 * disp_size[0], 0.5 * disp_size[1])
        lidar_data = np.fabs(lidar_data)
        lidar_data = lidar_data.astype(np.int32)
        lidar_data = np.reshape(lidar_data, (-1, 2))
        lidar_img_size = (disp_size[0], disp_size[1], 3)
        lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)
        lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
        if self.display_manager.render_enabled():
            self.surface = pygame.surfarray.make_surface(lidar_img)

    def save_radar_image(self, radar_data):
        points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
        points = np.reshape(points, (len(radar_data), 4))

    def render(self):
        if self.surface is not None:
            offset = self.display_manager.get_display_offset(self.display_pos)
            self.display_manager.display.blit(self.surface, offset)

    def destroy(self):
        self.sensor.stop()
        self.sensor.destroy()

class MultiSensorView():
    def __init__(self):
        self.display_manager = None

    def setup(self, world, vehicle, display, width, height, vehicle_name = "none"):
        '''Setup multi sensor view'''

        # Display Manager organize all the sensors an its display in a window
        # If can easily configure the grid and the total window size
        # Then, SensorManager can be used to spawn RGBCamera, LiDARs and SemanticLiDARs as needed and assign each of them to a grid position
        #self.display_manager = DisplayManager(display, grid_size=[2, 3], window_size=[width, height])
        self.display_manager = DisplayManager(display, grid_size=[2, 2], window_size=[width, height])

        # WinterSim Camera attributes
        right_camera_attributes = {'camera_sleet_effect' : 'True', 'camera_sleet_effect_rotation' : 'left', 'camera_sleet_effect_strength' : '1.2'}
        front_camera_attributes = {'camera_sleet_effect' : 'True', 'camera_sleet_effect_rotation' : 'up',   'camera_sleet_effect_strength' : '1.2', 'camera_ice_effect' : 'True',}
        left_camera_attributes =  {'camera_sleet_effect' : 'True', 'camera_sleet_effect_rotation' : 'left', 'camera_sleet_effect_strength' : '1.0'}
        back_camera_attributes =  {'camera_sleet_effect' : 'True', 'camera_sleet_effect_rotation' : 'down', 'camera_sleet_effect_strength' : '1.5'}

        lidar_location = carla.Location(0.0, 0.0, 2.4)
        right_cam_loc = carla.Location(0.0, 0.0, 2.4)
        front_cam_loc = carla.Location(0.0, 0.0, 2.4)
        left_cam_loc = carla.Location(0.0, 0.0, 2.4)
        back_cam_loc = carla.Location(0.0, 0.0, 2.4)

        # adjust sensor locations depending on the vehicle (WinterSim vehicles only)
        if vehicle_name == "pickup":
            lidar_location = carla.Location(0.0, 0.0, 2.4)
            right_cam_loc = carla.Location(0.0, 0.0, 2.4)
            front_cam_loc = carla.Location(0.0, 0.0, 2.4)
            left_cam_loc = carla.Location(0.0, 0.0, 2.4)
            back_cam_loc = carla.Location(-2.0, 0.0, 1.8)
        elif vehicle_name == "van":
            lidar_location = carla.Location(0.5, 0.0, 2.4)
            right_cam_loc = carla.Location(-1.0, 0.0, 2.5)
            front_cam_loc = carla.Location(0.5, 0.0, 2.4)
            left_cam_loc = carla.Location(-1.0, 0.0, 2.5)
            back_cam_loc = carla.Location(-2.2, 0.0, 1.8)
        elif vehicle_name == "wagon":
            lidar_location = carla.Location(0.0, 0.0, 2.4)
            right_cam_loc = carla.Location(-1.0, 0.0, 2.4)
            front_cam_loc = carla.Location(2.5, 0.0, 0.8)
            left_cam_loc = carla.Location(-1.0, 0.0, 2.4)
            back_cam_loc = carla.Location(-1.0, 0.0, 2.4)
        elif vehicle_name == "bus":
            lidar_location = carla.Location(0.0, 0.0, 4.2)
            right_cam_loc = carla.Location(-1.0, -1.5, 3.4)
            front_cam_loc = carla.Location(9.5, 0.0, 0.8)
            left_cam_loc = carla.Location(-1.0, 1.5, 3.4)
            back_cam_loc = carla.Location(-7.0, 0.0, 2.4)
        else:
            lidar_location = carla.Location(0.0, 0.0, 2.4)
            right_cam_loc = carla.Location(0.0, 0.0, 2.4)
            front_cam_loc = carla.Location(0.0, 0.0, 2.4)
            left_cam_loc = carla.Location(0.0, 0.0, 2.4)
            back_cam_loc = carla.Location(0.0, 0.0, 2.4)
        
        # # spawn camera sensors
        # SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(right_cam_loc,  carla.Rotation(yaw=-90)), vehicle, right_camera_attributes, display_pos=[0, 0])
        # SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(front_cam_loc,  carla.Rotation(yaw=+00)), vehicle, front_camera_attributes, display_pos=[0, 1])
        # SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(left_cam_loc,  carla.Rotation(yaw=+90)), vehicle, left_camera_attributes, display_pos=[0, 2])
        # SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(back_cam_loc,  carla.Rotation(yaw=180)), vehicle, back_camera_attributes, display_pos=[1, 1])
            
        # # spawn lidar sensors
        # SensorManager(world, self.display_manager, 'LiDAR', carla.Transform(lidar_location), vehicle, {'channels' : '64', 'range' : '100',  'points_per_second': '250000', 'rotation_frequency': '20'}, display_pos=[1, 0])
        # SensorManager(world, self.display_manager, 'SemanticLiDAR', carla.Transform(lidar_location), vehicle, {'channels' : '64', 'range' : '100', 'points_per_second': '100000', 'rotation_frequency': '20'}, display_pos=[1, 2])


        # spawn camera sensors
        SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(right_cam_loc,  carla.Rotation(yaw=-90)), vehicle, right_camera_attributes, display_pos=[0, 0])
        SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(front_cam_loc,  carla.Rotation(yaw=+00)), vehicle, front_camera_attributes, display_pos=[0, 1])
        SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(left_cam_loc,  carla.Rotation(yaw=+90)), vehicle, left_camera_attributes, display_pos=[1, 1])
        SensorManager(world, self.display_manager, 'RGBCamera', carla.Transform(back_cam_loc,  carla.Rotation(yaw=180)), vehicle, back_camera_attributes, display_pos=[1, 0])
            
    def destroy(self):
        '''Destroy multi sensor view'''
        self.display_manager.destroy()

    def render(self):
        '''Render multi sensor view to pygame window'''
        self.display_manager.render()