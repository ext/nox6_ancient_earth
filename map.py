import json
import os.path
from OpenGL.GL import *
from render.vbo import VBO
from render.image import Image
from render.shader import Shader
import item
import numpy as np
from utils.matrix import Matrix

class Map(object):
    def __init__(self, filename):
        self.filename = os.path.join('data', filename)

        with open(self.filename) as fp:
            data = json.load(fp)

        self.vbo = None
        self.grid = None
        self.width  = data['width']
        self.height = data['height']
        self.tile_width  = data['tilewidth']
        self.tile_height = data['tileheight']

        # load tilemap
        self.load_tileset(data['tilesets'])

        for layer in data['layers']:
            if layer['type'] == 'tilelayer':
                self.load_tiles(layer)

        # load objects
        self.obj1 = list(self.load_objects(data['layers'][1]['objects']))
        self.obj2 = list(self.load_objects(data['layers'][2]['objects']))
        self.obj3 = list(self.load_objects(data['layers'][3]['objects']))

        self.pickups = []

    def load_tileset(self, data):
        self.texture = []
        self.normal = []
        for tileset in data:
            props = tileset.get('properties', {})
            self.texture.append(Image(tileset['image'], filter=GL_NEAREST))
            self.normal.append(Image(props.get('normalmap', 'texture/default_normal.png'), filter=GL_NEAREST))

    def load_tiles(self, layer):
        if self.grid is not None:
            raise ValueError, 'Currently only one tile layer is supported'

        # hardcoded
        dx = self.tile_width  / 128.0
        dy = self.tile_height / 128.0
        tile_div = 128 / self.tile_width

        n = len(layer['data'])
        ver = np.zeros((n*4, 5), np.float32)
        for i, tile in enumerate(layer['data']):
            x = i % self.width
            y = -(i / self.width)

            tile -= 1 # start with 0 index
            tx = tile % tile_div
            ty = tile / tile_div

            ver[i*4+0] = (x  , y  , 0, tx*dx,    ty*dy+dy)
            ver[i*4+1] = (x+1, y  , 0, tx*dx+dx, ty*dy+dy)
            ver[i*4+2] = (x+1, y+1, 0, tx*dx+dx, ty*dy)
            ver[i*4+3] = (x  , y+1, 0, tx*dx,    ty*dy)

        ver = ver.flatten()
        ind = np.array(range(n*4), np.uint32)
        self.vbo = VBO(GL_QUADS, ver, ind)
        self.grid = np.array(layer['data'], np.uint32)

    @staticmethod
    def load_objects(src):
        for obj in src:
            yield item.create(obj['type'], **obj)

    def draw(self, *args, **kwargs):
        Shader.upload_model(Matrix.identity())
        glActiveTexture(GL_TEXTURE1)
        self.normal[0].texture_bind()
        glActiveTexture(GL_TEXTURE0)
        self.texture[0].texture_bind()
        self.vbo.draw(*args, **kwargs)

    def tile_at(self, pos):
        x = int(pos.x)
        y = -int(pos.y)
        if x < 0 or y < 0: return -1
        i = y * self.width + x
        try:
            return self.grid[i]
        except IndexError:
            return -1

    def update(self):
        self.pickups = [x for x in self.pickups if not x.killed]
