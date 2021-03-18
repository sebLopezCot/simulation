
import logging
from threading import Thread
from queue import Queue

import numpy as np

import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math

WINDOW_TITLE = "Map Perspective Visualizer"
WINDOW_WIDTH = 1920 
WINDOW_HEIGHT = 1080

PATH_COLORS = [
    "#FFF0F5",
    "#FFD700",
    "#EE82EE",
    "#1E90FF",
    "#EEE8AA",
    "#FFA500",
    "#BDB76B",
    "#FF00FF",
    "#FF0000",
    "#DA70D6",
    "#0000FF",
    "#9966CC",
    "#F4A460",
    "#FF69B4",
    "#9ACD32",
    "#7FFF00",
]

def random_color():
    color = np.random.choice(PATH_COLORS)
    color_hex = color[1:]
    r, g, b = color_hex[0:2], color_hex[2:4], color_hex[4:6]
    r, g, b = int(r, 16), int(g, 16), int(b, 16)
    r, g, b = float(r) / 255.0, float(g) / 255.0, float(b) / 255.0
    return r, g, b

class PathObjectManager(object):

    def __init__(self):
        pass

    def insert(self, path_splines):
        pass

class MapPerspective(object):

    def __init__(self, map_manager):
        self.map_manager = map_manager
        self.load_requests = Queue()
        self.path_objects = PathObjectManager()

        load_splines_thread = Thread(target=self.load_splines)
        load_splines_thread.start()

    def load_splines(self):
        request = self.load_requests.get()
        logging.info("Handling new request")



        logging.info("Request finished.")

    def maybe_load_next_splines(self):
        load_required = False
        if load_required:
            request = None
            self.load_requests.put(request)

    def init(self):
        logging.info("Starting map perspective visualizer...")

        pygame.init()
        display = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])
        
        self.sphere = gluNewQuadric() 
        
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
        
        glMatrixMode(GL_MODELVIEW)
        gluLookAt(0, -8, 0, 0, 0, 0, 0, 0, 1)
        self.viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        glLoadIdentity()
        
        # init mouse movement and center mouse on screen
        self.displayCenter = [self.screen.get_size()[i] // 2 for i in range(2)]
        self.mouseMove = [0, 0]
        pygame.mouse.set_pos(self.displayCenter)
        
        # Get path splines
        self.nearby_splines = self.map_manager.get_nearby_splines(location=None)
        self.spline_colors = [random_color() for _ in self.nearby_splines]

        # init mouse movement and center mouse on screen
        self.up_down_angle = 0.0
        self.paused = False
        
        self.running = True

    def update(self):
        # apply the look up and down
        self.up_down_angle += self.mouseMove[1]*0.1

        # apply movement of camera
        self.movement_vec = (0.0, 0.0, 0.0)

        vel = 1.0
        if self.keypress[pygame.K_w]:
            self.movement_vec = (0.0, 0.0, vel)
        if self.keypress[pygame.K_s]:
            self.movement_vec = (0.0, 0.0, -vel)
        if self.keypress[pygame.K_d]:
            self.movement_vec = (-vel, 0.0, 0.0)
        if self.keypress[pygame.K_a]:
            self.movement_vec = (vel, 0.0, 0.0)

    def render(self):
        # init model view matrix
        glLoadIdentity()
        
        # apply the look up and down
        glRotatef(self.up_down_angle, 1.0, 0.0, 0.0)
        
        # init the view matrix
        glPushMatrix()
        glLoadIdentity()
        
        # apply the movment
        dx, dy, dz = self.movement_vec
        glTranslatef(dx, dy, dz)

        # apply the left and right rotation
        glRotatef(self.mouseMove[0]*0.1, 0.0, 1.0, 0.0)
        
        # multiply the current matrix by the get the new view matrix and store the final vie matrix 
        glMultMatrixf(self.viewMatrix)
        self.viewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        
        # apply view matrix
        glPopMatrix()
        glMultMatrixf(self.viewMatrix)
        
        glLightfv(GL_LIGHT0, GL_POSITION, [1, -1, 1, 0])
        
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        glPushMatrix()
        
        # Render the floor
        glColor4f(0.5, 0.5, 0.5, 1)
        glBegin(GL_QUADS)
        glVertex3f(-100, -100, -2)
        glVertex3f(100, -100, -2)
        glVertex3f(100, 100, -2)
        glVertex3f(-100, 100, -2)
        glEnd()
        
        glPopMatrix()
        
        glPushMatrix()

        # Rander path splines
        glTranslatef(0, 0, -1.75)
        for spline_idx, spline in enumerate(self.nearby_splines):
            r, g, b = self.spline_colors[spline_idx] 
            glColor4f(r, g, b, 1)
            for p_idx in range(len(spline.x)):
                x = spline.x[p_idx] * 0.125
                y = spline.y[p_idx] * 0.125

                glPushMatrix()

                # Render spheres
                glTranslatef(x, y, 0)
                gluSphere(self.sphere, 0.1, 32, 16) 

                glPopMatrix()

        ## Render spheres
        #glTranslatef(-1.5, 0, 0)
        #glColor4f(0.5, 0.2, 0.2, 1)
        #gluSphere(self.sphere, 0.1, 32, 16) 
        #
        #glTranslatef(3, 0, 0)
        #glColor4f(0.2, 0.2, 0.5, 1)
        #gluSphere(self.sphere, 0.1, 32, 16) 
        
        glPopMatrix()
        
        pygame.display.flip()

    def handle_input_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                self.running = False
            if event.key == pygame.K_PAUSE or event.key == pygame.K_p:
                self.paused = not self.paused
                pygame.mouse.set_pos(self.displayCenter) 
        if not self.paused: 
            if event.type == pygame.MOUSEMOTION:
                self.mouseMove = [event.pos[i] - self.displayCenter[i] for i in range(2)]
            pygame.mouse.set_pos(self.displayCenter)    

    def handle_input_events(self):
        # Handle incoming mouse and keyboard events
        for event in pygame.event.get():
            self.handle_input_event(event)

        # get keys
        self.keypress = pygame.key.get_pressed()

    def run(self):
        self.init()
        
        while self.running:
            # Handle input events
            self.handle_input_events()
        
            if not self.paused:
                self.update()
                self.render()
                pygame.time.wait(10)

        pygame.quit()


