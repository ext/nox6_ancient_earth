from render.shader import Shader
from utils.matrix import Matrix
from utils.vector import Vector2f
from OpenGL.GL import *
import render.image as image
from render.light import Light
from player import Player
from utils.vector import Vector3f
import types
import re

type_register = {}

def register_type(cls_or_name):
    name = None
    def inner(cls, *args, **kwargs):
        global type_register
        type_register[name.lower()] = cls
        return cls

    if isinstance(cls_or_name, (type, types.ClassType)):
        name = cls_or_name.__name__
        return inner(cls_or_name)
    else:
        name = cls_or_name
        return inner

def create(typename, *args, **kwargs):
    typename = typename.lower()
    if typename in type_register:
        return type_register[typename](*args, **kwargs)
    raise KeyError, 'no item type named %s' % typename

class Item(object):
    diffuse = None # use sprite default
    normal = None  # use sprite default
    shader_name = 'default'

    def __init__(self, name, x, y, properties={}, **kwargs):
        self.name = name
        self.pos = Vector2f(x,-y) * (1.0 / 8)
        self.mat = Matrix.translate(self.pos.x, self.pos.y)
        self.killed = False

        if 'texture' in properties:
            self.diffuse = properties['texture']

        if 'shader' in properties:
            self.shader_name = properties['shader']

        self.load_sprite(self.diffuse, self.normal)
        self.shader = Shader.load(self.shader_name)

        if self.shader is None:
            raise AttributeError, 'Failed to load shader %s' % self.shader_name

    def load_sprite(self, *args, **kwargs):
        self.sprite = image.Sprite(*args, **kwargs)

    def draw(self):
        Shader.upload_model(self.mat)
        self.shader.bind()
        self.sprite.draw()

    def kill(self):
        self.killed = True

@register_type('catapult')
class Catapult(Item):
    diffuse = 'texture/catapult_loaded.png'

    def __init__(self, height, **kwargs):
        Item.__init__(self, height=height, **kwargs)
        self.mat = Matrix.transform(self.pos.x, self.pos.y - height * (1.0/8) + 1, 0, 5, 5, 1)

@register_type('light')
class LightStub(Light):
    def __init__(self, name, x, y, properties={}, **kwargs):
        color = LightStub.parse_color(properties.get('Color', ''), (1,1,1))
        radius = LightStub.parse_float(properties.get('Radius', ''), 50)
        falloff = LightStub.parse_float(properties.get('Falloff', ''), 10)
        phase_offset = LightStub.parse_float(properties.get('Phase Offset', ''), 10)
        phase_freq = LightStub.parse_float(properties.get('Phase Frequency', ''), 10)
        pos = Vector3f(x, -y) * (1.0 / 8)
        pos.z = 1

        Light.__init__(self, pos, color, radius, falloff, phase_offset, phase_freq)
        self.name = name

    def draw(self):
        pass

    @staticmethod
    def parse_color(string, default):
        m = re.match('\((\d),(\d),(\d)\)', string.strip())
        return default

    @staticmethod
    def parse_float(string, default):
        string = string.strip()
        if len(string) > 0:
            return float(string)
        else:
            return default
