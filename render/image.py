#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import traceback
import os
from OpenGL.GL import *
from OpenGL.GLU import *
from render.vbo import VBO
import numpy as np

lut = {}
def load(filename, *args, **kwargs):
    global lut
    if filename not in lut:
        lut[filename] = Image(filename, *args, **kwargs)
    return lut[filename]

class Image(object):
    def __init__(self, filename, filter=GL_LINEAR, wrap=GL_CLAMP_TO_EDGE):
        self.id = glGenTextures(1)

        try:
            with open(os.path.join('data', filename), 'rb') as fp:
                surface = pygame.image.load(fp).convert_alpha()
        except:
            traceback.print_exc()
            with open('data/texture/default.jpg', 'rb') as fp:
                surface = pygame.image.load(fp).convert_alpha()

        try:
            data = pygame.image.tostring(surface, "RGBA", 0)

            self.texture_bind()
            glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data);
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filter)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filter)
        except Exception, e:
            traceback.print_exc()

        self.size = surface.get_size()

    def texture_bind(self):
        glBindTexture(GL_TEXTURE_2D, self.id)

sprite_quad = None
def setup():
    global sprite_quad
    v = np.array([
        0,0,0, 0,1,
        1,0,0, 1,1,
        1,1,0, 1,0,
        0,1,0, 0,0,
    ], np.float32)
    i = np.array([0,1,2,3], np.uint32)
    sprite_quad = VBO(GL_QUADS, v, i)

def cleanup():
    global sprite_quad
    sprite_quad.destroy()
    del sprite_quad

class Sprite(Image):
    def __init__(self, diffuse=None, normal=None):
        # other classes sometimes explicitly passes None as argument so cannot
        # use default arguments here
        if diffuse is None: diffuse='texture/default_diffuse.png'
        if normal is None: normal='texture/default_normal.png'

        self.diffuse = load(diffuse)
        self.normal = load(normal)

    def texture_bind(self):
        glActiveTexture(GL_TEXTURE1)
        self.normal.texture_bind()
        glActiveTexture(GL_TEXTURE0)
        self.diffuse.texture_bind()

    def draw(self):
        self.texture_bind()
        sprite_quad.draw()
