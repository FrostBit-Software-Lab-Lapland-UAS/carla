#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#

# Copyright (c) 2021 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys
import glob
import os
import sys
from datetime import datetime
import numpy as np
from matplotlib import cm
import open3d as o3d
import math

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

VIRIDIS = np.array(cm.get_cmap('plasma').colors)
VID_RANGE = np.linspace(0.0, 1.0, VIRIDIS.shape[0])
LABEL_COLORS = np.array([
    (255, 255, 255), # None
    #(145, 170, 100), # None
    (70, 70, 70),    # Building
    (100, 40, 40),   # Fences
    (55, 90, 80),    # Other
    (220, 20, 60),   # Pedestrian
    (153, 153, 153), # Pole
    (157, 234, 50),  # RoadLines
    (128, 64, 128),  # Road
    (244, 35, 232),  # Sidewalk
    (107, 142, 35),  # Vegetation
    (0, 0, 142),     # Vehicle
    (102, 102, 156), # Wall
    (220, 220, 0),   # TrafficSign
    (70, 130, 180),  # Sky
    (81, 0, 81),     # Ground
    (150, 100, 100), # Bridge
    (230, 150, 140), # RailTrack
    (180, 165, 180), # GuardRail
    (250, 170, 30),  # TrafficLight
    (110, 190, 160), # Static
    (170, 120, 50),  # Dynamic
    (45, 60, 150),   # Water
    (145, 170, 100), # Terrain
    (145, 170, 100), # Terrain
]) / 255.0 # normalize each channel [0-1] since is what Open3D uses

class Open3DRadarWindow():
    ''' Class for handling Open3DLidar in separate window. 
    This is similiar to CARLA examples/open3d_lidar.py but 
    instead of spawning NPC and lidar, 
    this spawns lidar to ego vehicle and separate window from the simulation view 
    '''

    def radar_callback(self, radar_data):
        """Prepares a point cloud with semantic segmentation
        colors ready to be consumed by Open3D"""
        points = []
        try:
            data = np.frombuffer(radar_data.raw_data, dtype=np.dtype([
            ('x', np.float32), ('y', np.float32), ('z', np.float32)]))
            points = np.array([data['x'], -data['y'], data['z']]).T
            points.append(data)
        except:
            pass

        self.point_list.points = o3d.utility.Vector3dVector(points)

    def add_open3d_axis(self):
        """Add a small 3D axis on Open3D Visualizer"""
        axis = o3d.geometry.LineSet()
        axis.points = o3d.utility.Vector3dVector(np.array([
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]]))
        axis.lines = o3d.utility.Vector2iVector(np.array([
                [0, 1],
                [0, 2],
                [0, 3]]))
        axis.colors = o3d.utility.Vector3dVector(np.array([
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]]))
        self.vis.add_geometry(axis)

    def load_default_open3d_position(self):
        '''load default open3d position and rotation from json file and set zoom'''
        ctrl = self.vis.get_view_control()
        ctrl.set_zoom(0.3)
        parameters = o3d.io.read_pinhole_camera_parameters("./sensors/open3d_start_pos.json")
        ctrl.convert_from_pinhole_camera_parameters(parameters)

    def render_open3d_lidar(self):
        """Render radar to open3d window"""
        if self.frame == 2:
            self.vis.add_geometry(self.point_list)

            if not self.startup_done:
                self.startup_done = True
                #self.load_default_open3d_position()

        self.vis.update_geometry(self.point_list)
        self.vis.poll_events()
        self.vis.update_renderer()
        self.frame += 1

    def destroy(self):
        """Destroy radar sensor and open3d window"""
        self.sensor.destroy()
        self.vis.destroy_window()

    def setup(self, world, vehicle, show_axis, semantic):
        bp = world.get_blueprint_library().find('sensor.other.radar')
        bp.set_attribute('horizontal_fov', str(35))
        bp.set_attribute('vertical_fov', str(20))
        self.sensor = world.spawn_actor(bp, 
            carla.Transform(carla.Location(x=-0.5, y=0.0, z=0.23899), 
            carla.Rotation(pitch=5)),attach_to=vehicle)

        self.sensor.listen(lambda data: self.radar_callback(data))
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(
            window_name='Carla Radar',
            width=860, height=540,
            left=480, top=270)
        self.vis.get_render_option().background_color = [0.05, 0.05, 0.05]
        self.vis.get_render_option().point_size = 1
        self.vis.get_render_option().show_coordinate_frame = True

        if show_axis:
            self.add_open3d_axis()

    def __init__(self):
        super(Open3DRadarWindow, self).__init__()

        self.original_settings = None
        self.traffic_manager = None
        self.startup_done = False
        self.point_list = o3d.geometry.PointCloud()
        self.vis = None
        self.frame = 0

        self.sensor = None
        self.velocity_range = 7.5