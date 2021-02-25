
import random
import numpy as np
import matplotlib.pyplot as plt

class Graph(object):

    def __init__(self):
        self.forward_edges = {}
        self.backward_edges = {}

    def insert(self, start_node, end_node):
        if start_node not in self.forward_edges:
            self.forward_edges[start_node] = []
        self.forward_edges[start_node].append(end_node)

        if end_node not in self.backward_edges:
            self.backward_edges[end_node] = []
        self.backward_edges[end_node].append(start_node)


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

            self.random_edge_walk_(edges, non_visited_cells, start_cell)
            
        assert len(non_visited_cells) == 0, "Not all cells were visited!"

        return edges

    def _acceptable_curvature(self, edges, start_cell, next_cell):
        # Case 1: start node is a start node (i.e., no parent)
        if start_cell not in edges.backward_edges:
            return True

        # Case 2: start node is a continuation node (i.e., has parent)
        parent_cells = edges.backward_edges[start_cell]
        assert len(parent_cells) == 1, "Parent cell list has more than 1 element"
        parent_cell = parent_cells[0]
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

    def plot(self):
        anchor_xs, anchor_ys = self.grid_anchors
        connection_xs, connection_ys = self.connection_points
        plt.scatter(anchor_xs, anchor_ys, marker='.', c='b')
        plt.scatter(connection_xs, connection_ys, marker='.', c='r')

        random_paths = self.get_random_paths()
        grid_x_ticks, grid_y_ticks = self.grid_ticks
        print(random_paths.forward_edges)
        for src_cell, dst_cells in random_paths.forward_edges.items():
            src_x_idx, src_y_idx = src_cell
            src_x, src_y = grid_x_ticks[src_x_idx], grid_y_ticks[src_y_idx]
            
            for dst_cell in dst_cells:
                # Plot
                dst_x_idx, dst_y_idx = dst_cell
                dst_x, dst_y = grid_x_ticks[dst_x_idx], grid_y_ticks[dst_y_idx]
                
                print("(", src_x, ",", src_y, ") -> (", dst_x, ",", dst_y, ")")

                dx = dst_x - src_x
                dy = dst_y - src_y
                plt.arrow(src_x, src_y, dx, dy)

        plt.show()

if __name__ == "__main__":
    MAX_EXTENT = 100.0
    N_CELLS = 20
    N_CONNECTORS = 8
    CONNECTOR_RADIUS = 1.0
    MapGenerator(-MAX_EXTENT, MAX_EXTENT, -MAX_EXTENT, MAX_EXTENT, N_CELLS, N_CELLS, N_CONNECTORS, CONNECTOR_RADIUS).plot()

