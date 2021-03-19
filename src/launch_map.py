#!/usr/bin/env python3

from mapping.map_generator import MapGenerator 
from mapping.map_manager import MapManager
from visualization.map_perspective import MapPerspective


""" This script is used to run the map visualizer. """

if __name__ == '__main__':
    MAX_EXTENT = 100.0
    N_CELLS = 20
    N_CONNECTORS = 8
    CONNECTOR_RADIUS = 1.0
    SPLINE_DENSITY = 200
    map_gen = MapGenerator(-MAX_EXTENT, 
                            MAX_EXTENT, 
                            -MAX_EXTENT, 
                            MAX_EXTENT, 
                            N_CELLS, 
                            N_CELLS, 
                            N_CONNECTORS, 
                            CONNECTOR_RADIUS,
                            SPLINE_DENSITY)

    path_splines = map_gen.get_random_path_splines()
    map_manager = MapManager(path_splines)
    MapPerspective(map_manager).run()


