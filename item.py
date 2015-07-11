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
        self.mat = self.model_matrix()
        self.killed = False

        if 'texture' in properties:
            self.diffuse = properties['texture']

        if 'shader' in properties:
            self.shader_name = properties['shader']

        self.load_sprite(self.diffuse, self.normal)
        self.shader = Shader.load(self.shader_name)

        if self.shader is None:
            raise AttributeError, 'Failed to load shader %s' % self.shader_name

    def model_matrix(self):
        return Matrix.translate(self.pos.x, self.pos.y)

    def load_sprite(self, *args, **kwargs):
        self.sprite = image.Sprite(*args, **kwargs)

    def draw(self):
        Shader.upload_model(self.mat)
        self.shader.bind()
        self.sprite.draw()

    def update(self, map, dt):
        pass

    def kill(self):
        self.killed = True

class PhysicsItem(Item):
    weight = 1

    def __init__(self, properties={}, *args, **kwargs):
        Item.__init__(self, *args, **kwargs)
        self.velocity = Vector2f(0,0)
        self.acceleration = Vector2f(0,0)
        self.weight = properties.get('weight', self.__class__.weight)
        self.impulses = []

    def update(self, map, dt):
        Item.update(self, map, dt)

        # update position
        self.velocity += self.acceleration * dt
        self.pos += self.velocity * dt

        # check for collisions (hack: or if it fell below map)
        tile = map.tile_at(self.pos)
        if map.tile_collidable(tile) or self.pos.y < -25:
            self.tilemap_collision()

        # reset acceleration and impulses
        self.acceleration = sum([Vector2f(0, -9.82)] + [a for a,_ in self.impulses], Vector2f(0,0))
        self.impulses = [(a, t-dt) for a,t in self.impulses if t-dt > 0]

        # update model matrix
        self.mat = self.model_matrix()

    def impulse(self, force, t=0):
        """ Applies an impulse to the object, if t > 0 it is applied over time (constant force) """
        self.impulses.append((force / self.weight, t))

    def tilemap_collision(self):
        """ Called when this item collides with the tilemap """
        pass

@register_type('catapult')
class Catapult(Item):
    diffuse = 'texture/catapult_loaded.png'
    other = 'texture/catapult_unloaded.png'

    def __init__(self, height, properties, **kwargs):
        Item.__init__(self, height=height, properties=properties, **kwargs)

        flip = 1
        offset = 0
        if 'Flip' in properties:
            flip = -1
            offset = 5

        self.mat = Matrix.transform(self.pos.x + offset, self.pos.y - height * (1.0/8) + 1, 0, 5 * flip, 5, 1)

        self.loaded = self.sprite
        self.unloaded = image.Sprite(diffuse=Catapult.other)

    def set_loaded(self, state):
        if state:
            self.sprite = self.loaded
        else:
            self.sprite = self.unloaded

@register_type('projectile')
class Projectile(PhysicsItem):
    weight = 6
    diffuse = 'texture/projectile.png'

    def __init__(self, x, y, **kwargs):
        PhysicsItem.__init__(self, x=x, y=y, **kwargs)
        self.pos = Vector2f(x,y)
        self.old = self.pos
        self.traveled = 0
        self.mat = self.model_matrix() # hack (position set manually)

    def model_matrix(self):
        return Matrix.transform(self.pos.x, self.pos.y, 0, 2.2, 2.2, 1)

    def tilemap_collision(self):
        game.projectile_miss(self)

    def update(self, map, dt):
        PhysicsItem.update(self, map, dt)
        self.traveled += (self.old - self.pos).length()

        if self.traveled > 100:
            for i in range(2):
                d = (game.catapults[i].pos - self.pos).length()
                if d < 2.5:
                    game.projectile_hit(i)

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
