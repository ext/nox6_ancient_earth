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

@register_type('food')
class Food(Item):
    diffuse = 'texture/examplehead_diffuse.png'
    normal = 'texture/examplehead_normal.png'

    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.hp = 35

    def kill(self):
        Item.kill(self)
        game.eat.play()

@register_type('kebab')
class Schebab(Item):
    diffuse = 'texture/kebab.png'

    def __init__(self, **kwargs):
        Item.__init__(self, **kwargs)
        self.hp = 50

    def kill(self):
        Item.kill(self)
        game.eat.play()

@register_type('key')
class QuestItem(Item):
    def __init__(self, properties, **kwargs):
        Item.__init__(self, **kwargs)
        self.hp = 25

    def kill(self):
        Item.kill(self)
        game.ding.play()

        qn = len([x for x in [game.player.have_ham, game.player.have_bread, game.player.have_cheese] if x])

        if self.name == 'key':
            game.message('Picked up chainsaw key, hurry back home')
            game.set_stage(2)
        elif self.name == 'chainsaw':
            game.message('Picked up monster-ultra-food chainsaw 2000')
            game.message('Quest finished: "Find the chainsaw".')
            game.set_stage(3)
            Player.max_hp *= 2.0
            game.player.hp = Player.max_hp
        elif self.name == 'ham':
            game.message('Acquired questitem [%d/3]: Ham' % (qn+1))
            Player.max_hp *= 1.5
            game.player.hp = Player.max_hp
            game.player.have_ham = True
        elif self.name == 'bread':
            game.message('Acquired questitem [%d/3]: Bread' % (qn+1))
            Player.max_hp *= 1.5
            game.player.hp = Player.max_hp
            game.player.have_bread = True
        elif self.name == 'cheese':
            game.message('Acquired questitem [%d/3]: Cheese' % (qn+1))
            Player.max_hp *= 1.5
            game.player.hp = Player.max_hp
            game.player.have_cheese = True
        elif self.name == 'something':
            game.message('Something has been frobnicated')
            game.message('Quest finished: "Frobnicate something".')
        else:
            raise ValueError, 'unknown questitem %s' % self.name

@register_type('light')
class LightStub(Light):
    def __init__(self, name, x, y, properties={}, **kwargs):
        color = LightStub.parse_color(properties.get('Color', ''), (1,1,1))
        radius = LightStub.parse_float(properties.get('Radius', ''), 50)
        falloff = LightStub.parse_float(properties.get('Falloff', ''), 10)
        pos = Vector3f(x, -y) * (1.0 / 8)
        pos.z = 1

        Light.__init__(self, pos, color, radius, falloff)
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
