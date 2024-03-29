import re
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.ARB.uniform_buffer_object import *
from os.path import exists, join
import numpy as np
import pygame

file_counter = 1
file_lut = {}
re_inc = re.compile(r'#\s*include\s+[<"](.*)[<"]')
re_log = re.compile("([0-9]+)[(]([0-9]+)[)] \\: ([a-zA-Z]+) ([a-zA-Z0-9]+)\\: (.+)")

def file_id(filename):
    global file_lut, file_counter
    if filename not in file_lut:
        file_lut[filename] = file_counter
        file_counter += 1
    return file_lut[filename]

def file_reverse(id):
    # hack
    global file_lut
    id = int(id)
    for k,v in file_lut.iteritems():
        if v == id: return k
    raise KeyError, 'No file with id %d' % id

def preprocess(source, parent_id):
    global re_inc, file_lut

    for i, line in enumerate(source.splitlines()):
        line = line.strip()

        # hack to put a #line marker after #version so errors is marked correctly
        if i == 0 and line[:8] == '#version':
            yield line
            yield '#line %d %s' % (2, parent_id)
            continue

        match = re_inc.match(line)
        if match:
            filename = join('data/shader', match.group(1))
            id = file_id(filename)
            with open(filename) as fp:
                yield '#line %d %s' % (1, id)
                for x in preprocess(fp.read(), id):
                    yield x
                yield '#line %d %d' % (i+2, parent_id)
        else:
            yield line

class UniformBlock(object):
    counter = 0

    def __init__(self, name, size, usage=GL_DYNAMIC_DRAW):
        self.id = glGenBuffers(1)
        self.name = name
        self.size = size
        self.usage = usage
        self.binding = UniformBlock.counter
        UniformBlock.counter += 1

        with self:
            glBufferData(GL_UNIFORM_BUFFER, self.size, None, usage)
            glBindBufferRange(GL_UNIFORM_BUFFER, self.binding, self.id, 0, self.size)

    def __enter__(self):
        glBindBuffer(GL_UNIFORM_BUFFER, self.id)

    def __exit__(self, type, value, traceback):
        glBindBuffer(GL_UNIFORM_BUFFER, self.id)

    def upload(self, *args):
        with self:
            for offset, size, value in args:
                glBufferSubData(GL_UNIFORM_BUFFER, offset, size, value);

class Shader(object):
    max_lights = 12 # hardcoded in common.glsl
    light_size = 12 # defined in common.glsl

    uproj = None
    umodel = None
    ugame = None
    ulight = None
    lut = {}

    @classmethod
    def load(cls, filename):
        if filename not in cls.lut:
            cls.lut[filename] = Shader(filename)
        return cls.lut[filename]

    def __init__(self, name):
        self.initialize()

        self.sp = glCreateProgram()
        self.add_shader(name, '.vs', GL_VERTEX_SHADER)
        self.add_shader(name, '.fs', GL_FRAGMENT_SHADER)
        glLinkProgram(self.sp)
        self.print_log(self.sp)

        self.bind()

        for k,v in Shader.__dict__.iteritems():
            if v.__class__.__name__ != 'UniformBlock': continue

            id = glGetUniformBlockIndex(self.sp, v.name)
            if id != -1:
                glUniformBlockBinding(self.sp, id, v.binding)

        self.unbind()

    def add_shader(self, filename, ext, type):
        shader = glCreateShader(type)

        fullpath = join('data/shader', filename) + ext
        if not exists(fullpath):
            assert filename != 'default'
            return self.add_shader('default', ext, type)

        with open(fullpath) as fp:
            id = file_id(fullpath)
            source = '\n'.join(preprocess(fp.read(), id))

        glShaderSource(shader, source)
        glCompileShader(shader)
        glAttachShader(self.sp, shader)

        self.print_log(shader)

    def print_log(self, obj):
        global re_log
        if glIsShader(obj):
            raw = glGetShaderInfoLog(obj)
        else:
            raw = glGetProgramInfoLog(obj)
        for line in raw.splitlines():
            match = re_log.match(line)
            if match:
                file_id, line_num, severity, reference, message = match.groups()
                try:
                    filename = file_reverse(file_id)
                except KeyError:
                    filename = '<unknown>'
                print '%s:%s: %s: %s [%s]' % (filename, line_num, severity, message, reference)
            else:
                print line

    def bind(self):
        glUseProgram(self.sp)

    @staticmethod
    def unbind():
        glUseProgram(0)

    @staticmethod
    def upload_projection_view(proj, view):
        pv = np.matrix(view) * np.matrix(proj)

        s = 4*16
        Shader.uproj.upload(
            (0*s, s, pv),
            (1*s, s, proj),
            (2*s, s, view))

    @staticmethod
    def upload_model(mat):
        s = 4*16
        Shader.umodel.upload((0*s, s, mat))

    @staticmethod
    def upload_game(player):
        Shader.ugame.upload((0,   4*2, np.array([0,0], np.float32)))
        Shader.ugame.upload((4*2, 4*1, np.array(pygame.time.get_ticks() / 1000.0, np.float32)))
        Shader.ugame.upload((4*3, 4*1, np.array(0, np.float32)))
        Shader.ugame.upload((4*4, 4*1, np.array(0, np.float32)))

    @staticmethod
    def upload_light(ambient, lights):
        if len(lights) > Shader.max_lights:
            raise ValueError, 'Too many lights uploaded (max: %d, got: %d)' % (Shader.max_ligths, len(lights))

        Shader.ulight.upload((4*0, 4*1, np.array(len(lights), np.uint32)))
        Shader.ulight.upload((4*4, 4*3, np.array(ambient, np.float32)))

        offset = 4*8
        for light in lights:
            Shader.ulight.upload((offset, 4*Shader.light_size, light.shader_data()))
            offset += 4*Shader.light_size

    @staticmethod
    def lightbuffer_size(num_lights):
        return 4*4 + 4*Shader.light_size*num_lights

    @staticmethod
    def initialize():
        if Shader.uproj is not None: return

        Shader.uproj = UniformBlock('projectionViewMatrices', 4*16*3)
        Shader.umodel = UniformBlock('modelMatrices', 4*16*1)
        Shader.ugame = UniformBlock('game', 4*5)
        Shader.ulight = UniformBlock('light', Shader.lightbuffer_size(Shader.max_lights))

        for i in range(2):
            glEnableVertexAttribArray(i)
