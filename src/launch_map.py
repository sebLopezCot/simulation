#!/usr/bin/env python3

from mapping.map_manager import MapManager
from visualization.map_perspective import MapPerspective


""" This script is used to run the map visualizer. """

if __name__ == '__main__':
    map_manager = MapManager(None)
    MapPerspective(map_manager).run()


