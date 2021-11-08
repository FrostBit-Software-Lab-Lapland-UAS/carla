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
import threading
import weakref
import carla

from wintersim_object_detection import WinterSimObjectDetection

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

try:
    import cv2
except ImportError:
    raise RuntimeError('cannot import cv2, make sure cv2 package is installed')

# Camera cv2 window width, height and camera fov
VIEW_WIDTH = 608
VIEW_HEIGHT = 384
VIEW_FOV = 70

class CameraWindows(threading.Thread):
    """This class handles Wintersim separate camera views.
    This works by spawning separate camera-actors and listening camera callback 
    which are then displayed into separate cv2 windows.
    """

    def camera_blueprint(self, camera_effect, rotation, effect_strength):
        """Returns RGB camera blueprint."""
        camera_bp = self.world.get_blueprint_library().find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', str(VIEW_WIDTH))
        camera_bp.set_attribute('image_size_y', str(VIEW_HEIGHT))
        camera_bp.set_attribute('fov', str(VIEW_FOV))

        # WinterSim added camera attributes, all attributes must be converted to string!
        if camera_effect:
            camera_bp.set_attribute('camera_sleet_effect', str(camera_effect))              # Value: boolean, (Default False)
            camera_bp.set_attribute('camera_sleet_effect_rotation', str(rotation))          # Value: string,  (Default: "up" - values: "up", "right", "left", "down")
            camera_bp.set_attribute('camera_sleet_effect_strength', str(effect_strength))   # Value: float,   (Default 1.2)
        
        return camera_bp

    def depth_camera_blueprint(self):
        """Returns depth camera blueprint."""
        depth_camera_bp = self.world.get_blueprint_library().find('sensor.camera.depth')
        depth_camera_bp.set_attribute('image_size_x', str(VIEW_WIDTH))
        depth_camera_bp.set_attribute('image_size_y', str(VIEW_HEIGHT))
        depth_camera_bp.set_attribute('fov', str(VIEW_FOV))
        
        return depth_camera_bp

    def setup_front_rgb_camera(self):
        """Spawn Camera-actor (front RGB camera) to given position and
        setup camera image callback and cv2 window."""
        camera_transform = carla.Transform(carla.Location(x=2.0, z=2.0), carla.Rotation(pitch=0))
        if self.actor_name == "bus":
            camera_transform = carla.Transform(carla.Location(x=6.0, y=0.4, z=3.0), carla.Rotation(pitch=0))

        self.front_rgb_camera = self.world.spawn_actor(self.camera_blueprint(True, "up", 1.2), camera_transform, attach_to=self.car)
        weak_rgb_self = weakref.ref(self)
        self.front_rgb_camera.listen(lambda front_rgb_image: weak_rgb_self().set_front_rgb_image(weak_rgb_self, front_rgb_image))
        self.front_rgb_camera_display = cv2.namedWindow('front RGB camera')
        cv2.moveWindow('front RGB camera', 5, 740)

    def setup_back_rgb_camera(self):
        """Spawn Camera-actor (back RGB camera) to given position and
        setup camera image callback and cv2 window."""
        camera_transform = carla.Transform(carla.Location(x=-3.5, z=2.0), carla.Rotation(pitch=-10, yaw=180))
        if self.actor_name == "bus":
            camera_transform = carla.Transform(carla.Location(x=-6.7, y=0.4, z=3.0), carla.Rotation(pitch=-10, yaw=180))

        self.back_rgb_camera = self.world.spawn_actor(self.camera_blueprint(False, None, None), camera_transform, attach_to=self.car)
        weak_back_rgb_self = weakref.ref(self)
        self.back_rgb_camera.listen(lambda back_rgb_image: weak_back_rgb_self().set_back_rgb_image(weak_back_rgb_self, back_rgb_image))
        self.back_rgb_camera_display = cv2.namedWindow('back RGB camera')
        cv2.moveWindow('back RGB camera', 610, 740)

    def setup_front_depth_camera(self):
        """Spawn Camera-actor (front depth camera) to given position and
        setup camera image callback and cv2 window."""
        depth_camera_transform = carla.Transform(carla.Location(x=0, z=2.8), carla.Rotation(pitch=0))
        self.depth_camera = self.world.spawn_actor(self.depth_camera_blueprint(), depth_camera_transform, attach_to=self.car)
        weak_depth_self = weakref.ref(self)
        self.depth_camera.listen(lambda front_depth_image: weak_depth_self().set_front_depth_image(weak_depth_self, front_depth_image))
        self.front_depth_display = cv2.namedWindow('front_depth_image')
       
    @staticmethod
    def set_front_rgb_image(weak_self, img):
        """Sets image coming from front RGB camera sensor."""
        self = weak_self()
        self.front_rgb_image = img

    @staticmethod
    def set_back_rgb_image(weak_self, img):
        """Sets image coming from back RGB camera sensor."""
        self = weak_self()
        self.back_rgb_image = img

    @staticmethod
    def set_front_depth_image(weak_depth_self, depth_img):
        """Sets image coming from depth camera sensor."""
        self = weak_depth_self()
        self.front_depth_image = depth_img

    def render_front_depth(self):
        """Render front depth camera."""
        if self.front_depth_image is not None:
            image = np.asarray(self.front_depth_image.raw_data)
            image = image.reshape((VIEW_HEIGHT, VIEW_WIDTH, 4))
            image = image[:, :, :3]
            cv2.imshow("front_depth_image", image)
            self.front_depth_image = None

    def render_front_rgb_camera(self):
        """Render front RGB camera."""
        if self.front_rgb_image is not None:
            image = np.asarray(self.front_rgb_image.raw_data)
            image = image.reshape((VIEW_HEIGHT, VIEW_WIDTH, 4))
            image = image[:, :, :3]
            image = self.object_detection.Detect(image)
            cv2.imshow("front RGB camera", image)
            self.front_rgb_image = None

    def render_back_rgb_camera(self):
        """Render back RGB camera."""
        if self.back_rgb_image is not None:
            image = np.asarray(self.back_rgb_image.raw_data)
            image = image.reshape((VIEW_HEIGHT, VIEW_WIDTH, 4))
            image = image[:, :, :3]
            cv2.imshow("back RGB camera", image)
            self.back_rgb_image = None

    def render_all_windows(self):
        """Render all separate cameras to CV2 windows"""
        self.render_front_rgb_camera()
        self.render_back_rgb_camera()
        #self.render_front_depth()
       
    def destroy(self):
        """Destroy all spawned camera-actors and cv2 windows."""
        self.stop()

        if self.front_rgb_camera is not None:
            self.front_rgb_camera.stop()
            self.front_rgb_camera.destroy()

        if self.back_rgb_camera is not None:
            self.back_rgb_camera.stop()
            self.back_rgb_camera.destroy()

        if self.front_depth_camera is not None:
            self.front_depth_camera.stop()
            self.front_depth_camera.destroy()

        cv2.destroyAllWindows()

    def __init__(self, ego_vehicle, camera, world, actor_name):
        super(CameraWindows, self).__init__()
        self.__flag = threading.Event()             # The flag used to pause the thread
        self.__flag.set()                           # Set to True
        self.__running = threading.Event()          # Used to stop the thread identification
        self.__running.set()                        # Set running to True
        
        self.camera = camera
        self.world = world
        self.car = ego_vehicle
        self.actor_name = actor_name

        self.front_rgb_camera_display = None
        self.front_rgb_camera = None
        self.front_rgb_image = None

        self.back_rgb_camera_display = None
        self.back_rgb_camera = None
        self.back_rgb_image = None

        self.front_depth_display = None
        self.front_depth_camera = None
        self.front_depth_image = None

        self.setup_back_rgb_camera()
        self.setup_front_rgb_camera()
        #self.setup_front_depth_camera()

        # self.object_detection = None
        self.object_detection = WinterSimObjectDetection()

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()                      # return immediately when it is True, block until the internal flag is True when it is False
            self.render_all_windows()               # render all cv2 windows when flag is True

    def pause(self):
        self.__flag.clear()                         # Set to False to block the thread

    def resume(self):
        self.__flag.set()                           # Set to True, let the thread stop blocking

    def stop(self):
        self.__flag.set()                           # Resume the thread from the suspended state, if it is already suspended
        self.__running.clear()                      # Set to False