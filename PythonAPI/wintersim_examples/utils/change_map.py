#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#

# Copyright (c) 2022 FrostBit Software Lab

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

from __future__ import print_function

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

import argparse
import carla

def map_is_available(client, map_to_load):
    maps = [m.replace('/Game/Carla/Maps/', '') for m in client.get_available_maps()]
    for map in maps:
        if map == map_to_load:
            return True
    return False


def change_map(args):
    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        if args.map is not None:
            client.set_timeout(30.0)
            if map_is_available(client, args.map):
                print("Loading map: " + str(args.map))
                client.load_world(args.map)
                print("Loaded map: " + str(args.map))
            else:
                print("Invalid map name.")
        else:
            print("Provide map name with argument '-m, --m, -map, --map [map_name]]' ")

        return

    except Exception as e:
        print(e)

# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================

# Usage:
# python change_map -m [map_name]
# python change_map --m Muonio
# python change_map -map Muonio
# python change_map --map Muonio

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
        '-m', '--map', '--m', '-map',
        help='load map by name')
    args = argparser.parse_args()

    try:
        change_map(args)
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')

if __name__ == '__main__':
    main()