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

class Open3DLidarWindow():
    ''' Class for handling Open3DLidar in separate window. 
    This is similiar to CARLA examples/open3d_lidar.py but 
    instead of spawning NPC and lidar, 
    this spawns lidar to ego vehicle and separate window from the simulation view 
    '''

    def generate_lidar_bp(self, semantic, world, blueprint_library, delta):
        """Generates a CARLA blueprint based on the script parameters"""
        if semantic:
            lidar_bp = world.get_blueprint_library().find('sensor.lidar.ray_cast_semantic')
        else:
            lidar_bp = blueprint_library.find('sensor.lidar.ray_cast')
            lidar_bp.set_attribute('dropoff_general_rate', '0.0')
            lidar_bp.set_attribute('dropoff_intensity_limit', '1.0')
            lidar_bp.set_attribute('dropoff_zero_intensity', '0.0')

        lidar_bp.set_attribute('upper_fov', str(self.upper_fov))
        lidar_bp.set_attribute('lower_fov', str(self.lower_fov))
        lidar_bp.set_attribute('channels', str(self.channels))
        lidar_bp.set_attribute('range', str(self.range))
        lidar_bp.set_attribute('rotation_frequency', str(1.0 / delta))
        lidar_bp.set_attribute('points_per_second', str(self.points_per_second))

        return lidar_bp

    def lidar_callback(self, point_cloud):
        """Prepares a point cloud with intensity
        colors ready to be consumed by Open3D"""
        data = np.copy(np.frombuffer(point_cloud.raw_data, dtype=np.dtype('f4')))
        data = np.reshape(data, (int(data.shape[0] / 4), 4))
        # Isolate the intensity and compute a color for it
        intensity = data[:, -1]
        intensity_col = 1.0 - np.log(intensity) / np.log(np.exp(-0.004 * 100))
        int_color = np.c_[
            np.interp(intensity_col, VID_RANGE, VIRIDIS[:, 0]),
            np.interp(intensity_col, VID_RANGE, VIRIDIS[:, 1]),
            np.interp(intensity_col, VID_RANGE, VIRIDIS[:, 2])]

        # Isolate the 3D data
        points = data[:, :-1]

        # We're negating the y to correclty visualize a world that matches
        # what we see in Unreal since Open3D uses a right-handed coordinate system
        points[:, :1] = -points[:, :1]

        # # An example of converting points from sensor to vehicle space if we had
        # # a carla.Transform variable named "tran":
        # points = np.append(points, np.ones((points.shape[0], 1)), axis=1)
        # points = np.dot(tran.get_matrix(), points.T).T
        # points = points[:, :-1]
        self.point_list.points = o3d.utility.Vector3dVector(points)
        self.point_list.colors = o3d.utility.Vector3dVector(int_color)

    def semantic_lidar_callback(self, point_cloud):
        """Prepares a point cloud with semantic segmentation
        colors ready to be consumed by Open3D"""
        data = np.frombuffer(point_cloud.raw_data, dtype=np.dtype([
            ('x', np.float32), ('y', np.float32), ('z', np.float32),
            ('CosAngle', np.float32), ('ObjIdx', np.uint32), ('ObjTag', np.uint32)]))

        # We're negating the y to correclty visualize a world that matches
        # what we see in Unreal since Open3D uses a right-handed coordinate system
        points = np.array([data['x'], -data['y'], data['z']]).T

        # # An example of adding some noise to our data if needed:
        # points += np.random.uniform(-0.05, 0.05, size=points.shape)

        # Colorize the pointcloud based on the CityScapes color palette
        labels = np.array(data['ObjTag'])

        int_color = LABEL_COLORS[labels]

        # # In case you want to make the color intensity depending
        # # of the incident ray angle, you can use:
        # int_color *= np.array(data['CosAngle'])[:, None]
        self.point_list.points = o3d.utility.Vector3dVector(points)
        self.point_list.colors = o3d.utility.Vector3dVector(int_color)

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

    def render_open3d_lidar(self):
        """Render lidar to open3d window"""
        if self.frame == 2: # every second frame add new geometry
            self.vis.add_geometry(self.point_list)
            
        self.vis.update_geometry(self.point_list)
        self.vis.poll_events()
        self.vis.update_renderer()
        self.frame += 1

    def destroy(self):
        """Destroy lidar and open3d window"""
        self.lidar.destroy()
        self.vis.destroy_window()

    def setup(self, world, vehicle, show_axis, semantic):
        delta = 0.05
        blueprint_library = world.get_blueprint_library()
        lidar_bp = self.generate_lidar_bp(semantic, world, blueprint_library, delta)

        lidar_transform = carla.Transform(carla.Location(x=-0.5, y=0.0, z=0.23899))
        self.lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)

        self.point_list = o3d.geometry.PointCloud()
        if semantic:
            self.lidar.listen(lambda data: self.semantic_lidar_callback(data))
        else:
            self.lidar.listen(lambda data: self.lidar_callback(data))

        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window(
            window_name='Carla Lidar',
            width=860, height=540,
            left=480, top=270)
        self.vis.get_render_option().background_color = [0.05, 0.05, 0.05]
        self.vis.get_render_option().point_size = 1
        self.vis.get_render_option().show_coordinate_frame = True

        if show_axis:
            self.add_open3d_axis()

    def __init__(self):
        super(Open3DLidarWindow, self).__init__()

        self.original_settings = None
        self.traffic_manager = None
        self.point_list = o3d.geometry.PointCloud()
        self.lidar = None
        self.vis = None
        self.frame = 0
        self.points_per_second = 700000
        self.upper_fov = 2.0
        self.lower_fov = 24.9
        self.channels = 32.0
        self.range = 50.0