
import random
import numpy as np
import matplotlib.pyplot as plt

from spline import calc_2d_spline_interpolation 

class Graph(object):

    def __init__(self):
        self.forward_edges = {}
        self.backward_edges = {}
        self.paths = {}
        self.latest_path_key = None
    
    def init_path(self, start_cell):
        assert start_cell not in self.paths, "Start cell is already the first node in another path"
        self.paths[start_cell] = []
        self.latest_path_key = start_cell

    def insert(self, start_node, end_node):
        if start_node not in self.forward_edges:
            self.forward_edges[start_node] = set()
        self.forward_edges[start_node].add(end_node)

        if end_node not in self.backward_edges:
            self.backward_edges[end_node] = set()
        self.backward_edges[end_node].add(start_node)

        assert self.latest_path_key is not None, "No path has been initialized yet!"
        self.paths[self.latest_path_key].append(end_node)

    def delete_path(self, start_cell):
        assert start_cell in self.paths, "No path with that start cell"
        
        if self.latest_path_key == start_cell:
            self.latest_path_key = None

        parent = start_cell
        for cell in self.paths[start_cell]:
            self.forward_edges[parent].remove(cell)
            self.backward_edges[cell].remove(parent)
            parent = cell
        del self.paths[start_cell]


class MapGenerator(object):

    def __init__(self, x_min, x_max, y_min, y_max, num_x_cells, num_y_cells, num_connectors, connector_radius):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.num_x_cells = num_x_cells
        self.num_y_cells = num_y_cells

        assert num_connectors % 2 == 0, "Connector number must be even"
        self.num_connectors = num_connectors
        self.connector_radius = connector_radius

    @property
    def grid_ticks(self):
        grid_x_ticks = np.linspace(self.x_min, self.x_max, self.num_x_cells + 1)
        grid_y_ticks = np.linspace(self.y_min, self.y_max, self.num_y_cells + 1)
        return grid_x_ticks, grid_y_ticks

    @property
    def grid_anchors(self):
        grid_xs, grid_ys = self.grid_ticks
        grid_xs, grid_ys = zip(*[(x,y) for x in grid_xs for y in grid_ys])
        
        return grid_xs, grid_ys

    @property
    def connection_points(self):
        anchor_xs, anchor_ys = self.grid_anchors
        theta_incr = np.linspace(0, 2*np.pi, self.num_connectors + 1)[:-1]
        # N x 2
        anchor_r = np.vstack([np.array(anchor_xs), np.array(anchor_ys)]).T
        # T x N X 2
        anchor_rs = np.tile(anchor_r, (self.num_connectors, 1, 1))
        # T X 2
        delta_rs = self.connector_radius * np.vstack([np.cos(theta_incr), np.sin(theta_incr)]).T
        # N x T x 2
        delta_rs = np.tile(delta_rs, (len(anchor_xs), 1, 1))
        # T x N x 2
        delta_rs = np.transpose(delta_rs, (1, 0, 2))
        connection_rs = anchor_rs + delta_rs
        # T*N x 2
        connection_rs = np.reshape(connection_rs, (-1, 2))

        return connection_rs[:,0], connection_rs[:,1]

    def get_random_paths(self):
        non_visited_cells = set((x, y) for x in range(self.num_x_cells) for y in range(self.num_y_cells))
        visit_order = list(non_visited_cells)
        random.shuffle(visit_order)

        edges = Graph()

        for start_cell in visit_order:
            # skip cells which have already been visited
            if not start_cell in non_visited_cells:
                continue

            edges.init_path(start_cell)

            self.random_edge_walk_(edges, non_visited_cells, start_cell)
            
        assert len(non_visited_cells) == 0, "Not all cells were visited!"

        # Remove short paths
        self.remove_short_paths_(edges)

        return edges

    def _acceptable_curvature(self, edges, start_cell, next_cell):
        # Case 1: start node is a start node (i.e., no parent)
        if start_cell not in edges.backward_edges:
            return True

        # Case 2: start node is a continuation node (i.e., has parent)
        parent_cells = edges.backward_edges[start_cell]
        assert len(parent_cells) == 1, "Parent cell list has more than 1 element"
        parent_cell = list(parent_cells)[0]
        subpath1 = np.array(start_cell) - np.array(parent_cell)
        subpath1 = subpath1 / np.linalg.norm(subpath1)

        subpath2 = np.array(next_cell) - np.array(start_cell)
        subpath2 = subpath2 / np.linalg.norm(subpath2)

        cos_theta = np.dot(subpath1, subpath2)
        # cos theta will be positive when some alignment and same direction
        # cos theta will be zero when orthogonal
        # cos theta will be negative when some anti-alignment in opposite directions
        EPS = 1e-3 
        MAX_COS_THETA = 1.0 + EPS
        MIN_COS_THETA = 0.1 - EPS

        return MIN_COS_THETA <= cos_theta <= MAX_COS_THETA

    def random_edge_walk_(self, edges, non_visited_cells, start_cell):
        # Remove from non visited set
        if start_cell in non_visited_cells:
            non_visited_cells.remove(start_cell)

        cur_x, cur_y = start_cell

        x_offsets = [-1, 0, 1]
        y_offsets = [-1, 0, 1]
        nbors = [(cur_x + dx, cur_y + dy) for dx in x_offsets for dy in y_offsets \
                if 0 <= cur_x + dx < self.num_x_cells \
                and 0 <= cur_y + dy < self.num_y_cells\
                and not (dx == 0 and dy == 0)\
                and (cur_x + dx, cur_y + dy) in non_visited_cells\
                and self._acceptable_curvature(edges, start_cell, (cur_x + dx, cur_y + dy))]

        # Base case
        if not nbors:
            return

        # Random neighbor choice
        neighbor_cell_idx = int(np.random.randint(len(nbors))) 
        neighbor_cell = nbors[neighbor_cell_idx]

        # Insert edge into graph
        edges.insert(start_cell, neighbor_cell)

        # Recurse
        self.random_edge_walk_(edges, non_visited_cells, neighbor_cell)

    def remove_short_paths_(self, edges, min_path_length=15):
        paths_to_remove = [k for k, path in edges.paths.items() if len(path) < min_path_length]
        for path_key in paths_to_remove:
            edges.delete_path(path_key)

    def connect_leafs_to_shortest_path_start_nodes_(self, edges):
        # Use bfs to find shortest path end nodes of path i to closest
        # start nodes of path j for all j != i
        raise NotImplementedError()

    def plot(self):
        anchor_xs, anchor_ys = self.grid_anchors
        connection_xs, connection_ys = self.connection_points

        # Plot grid
        #plt.scatter(anchor_xs, anchor_ys, marker='.', c='b')
        #plt.scatter(connection_xs, connection_ys, marker='.', c='r')

        random_paths = self.get_random_paths()
        grid_x_ticks, grid_y_ticks = self.grid_ticks
        
        # Plot edge graph 
        #for src_cell, dst_cells in random_paths.forward_edges.items():
        #    src_x_idx, src_y_idx = src_cell
        #    src_x, src_y = grid_x_ticks[src_x_idx], grid_y_ticks[src_y_idx]
        #    
        #    for dst_cell in dst_cells:
        #        # Plot
        #        dst_x_idx, dst_y_idx = dst_cell
        #        dst_x, dst_y = grid_x_ticks[dst_x_idx], grid_y_ticks[dst_y_idx]
        #        
        #        print("(", src_x, ",", src_y, ") -> (", dst_x, ",", dst_y, ")")

        #        dx = dst_x - src_x
        #        dy = dst_y - src_y
        #        plt.arrow(src_x, src_y, dx, dy)

        # Plot path splines
        for start_cell, path in random_paths.paths.items():
            nd_arr = np.zeros((len(path) + 1, 2))
            nd_arr[0, :] = np.array(start_cell)
            nd_arr[1:, :] = np.array(path)
            nd_xs = nd_arr[:, 0]
            nd_ys = nd_arr[:, 1]

            nd_xs = [grid_x_ticks[int(x_i)] for x_i in nd_xs]
            nd_ys = [grid_y_ticks[int(y_i)] for y_i in nd_ys]

            x, y, yaw, k, travel = calc_2d_spline_interpolation(nd_xs, nd_ys, num=200)
            plt.plot(x, y)


        plt.show()

if __name__ == "__main__":
    MAX_EXTENT = 100.0
    N_CELLS = 20
    N_CONNECTORS = 8
    CONNECTOR_RADIUS = 1.0
    MapGenerator(-MAX_EXTENT, MAX_EXTENT, -MAX_EXTENT, MAX_EXTENT, N_CELLS, N_CELLS, N_CONNECTORS, CONNECTOR_RADIUS).plot()

