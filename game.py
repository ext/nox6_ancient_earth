import pygame
import os, sys
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from render.fbo import FBO
from render.hud import HUD, ALIGN_CENTER
from render.image import Image, Sprite
from render.shader import Shader
from render.vbo import VBO
from render.light import Light
from utils.matrix import Matrix
from utils.vector import Vector2i, Vector2f, Vector3f
from map import Map
import math
import render.image as image
import item

class DummyProjectile(object):
    def __nonzero__(self):
        return false

    def update(self, dt):
        pass

    def draw(self):
        pass

event_table = {}
def event(type):
    def wrapper(func):
        event_table[type] = func
        return func
    return wrapper

class Game(object):
    def __init__(self):
        self._running = False
        self.camera = Vector2f(0,-11)

    def init(self, size, fullscreen=False):
        flags = OPENGL|DOUBLEBUF
        if fullscreen:
            flags |= FULLSCREEN

        pygame.display.set_mode(size.xy, flags)
        pygame.display.set_caption('Super Ancient Precision Adventure^WGame')

        i = pygame.display.Info()
        self.size = Vector2i(i.current_w, i.current_h)

        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

        image.setup()

        self.stage = 1
        self.projection = Matrix.perspective(75, self.size, 0.1, 100)
        self.ortho = Matrix.ortho(self.size)

        v = np.array([
                0,0,0, 0,0,
                1,0,0, 1,0,
                1,1,0, 1,1,
                0,1,0, 0,1,
                ], np.float32)
        i = np.array([0,1,2,3], np.uint32)
        self.quad = VBO(GL_QUADS, v, i)

        # parallax
        self.parallax_rep = 10
        v = np.array([
                0,0,0, 0,1,
                1,0,0, self.parallax_rep, 1,
                1,1,0, self.parallax_rep, 0,
                0,1,0, 0,0,
                ], np.float32)
        i = np.array([0,1,2,3], np.uint32)
        self.repquad = VBO(GL_QUADS, v, i)
        self.parallax = Image('texture/sky.png', wrap=GL_REPEAT)
        self.hudbg = Image('texture/hud_bottom.png')
        self.projectile = DummyProjectile()

        self.fbo = FBO(self.size, format=GL_RGB8, depth=True)

        self.shader = Shader.load('default')
        self.shader_hud = Shader.load('hud')
        self.post = Shader.load('post')

        self.ambient_light = (1.0, 1.0, 1.0)
        self.angle = [60, 60]
        self.force = [50, 50]
        self.player = 0
        self.firing = False

        self.map = Map('map.json')
        self.clock = pygame.time.Clock()
        self.hud_msgbox = HUD(Vector2i(500,100), 'msgbox')
        self.hud_ui = HUD(Vector2i(self.size.x, self.size.x * (160./800)), 'ui')
        self.scrollbar = HUD(Vector2i(self.size.x,8), 'scrollbar')
        self.font = self.hud_msgbox.create_font(size=16)
        self.font_ui = self.hud_ui.create_font(size=16)
        self.camera_max = self.map.width - 36

        self.land = pygame.mixer.Sound('data/sound/land.wav')
        self.ding = pygame.mixer.Sound('data/sound/ding.wav')
        self.eat = pygame.mixer.Sound('data/sound/eat.wav')
        self.wind = pygame.mixer.Sound('data/sound/wind.wav')

        self.wind.play(loops=-1)

        self.textbuf = []
        self.texttime = -10.0
        self.message('<b>derp</b>\na herp.')

        with self.hud_msgbox:
            self.hud_msgbox.clear((0,1,1,1))

    def running(self):
        return self._running

    @event(pygame.QUIT)
    def quit(self, event=None):
        self._running = False

    @event(pygame.KEYDOWN)
    def on_keypress(self, event):
        if event.key == 113 and event.mod & KMOD_CTRL: # ctrl+q
            return self.quit()
        if event.key == 27: # esc
            return self.quit()
        if event.key == 13: # enter
            self.fire()

    @event(pygame.MOUSEBUTTONDOWN)
    def on_button(self, event):
        if not self.firing:
            if event.button == 4: self.camera.x += 5
            if event.button == 5: self.camera.x -= 5

    def fire(self):
        if not self.firing:
            self.firing = True
            self.projectile = item.create('projectile', name='projectile', x=6, y=-10)
            self.projectile.impulse(Vector2f(500, 500), 0.1)

    def poll(self):
        global event_table
        for event in pygame.event.get():
            func = event_table.get(event.type, None)
            if func is None:
                continue
            func(self, event)

    def update(self):
        key = pygame.key.get_pressed()

        if not self.firing:
            if key[260]: self.camera.x -= 1
            if key[262]: self.camera.x += 1

            if key[273]: self.angle[self.player] += 1
            if key[274]: self.angle[self.player] -= 1
            if key[275]: self.force[self.player] += 1
            if key[276]: self.force[self.player] -= 1

            self.camera.x = min(max(self.camera.x, 0), self.camera_max)
            self.angle[self.player] = min(max(self.angle[self.player], 0), 90)
            self.force[self.player] = min(max(self.force[self.player], 0), 200)

        dt = 1.0 / self.clock.tick(60)
        self.map.update()
        self.projectile.update(dt)

    def render_hud(self):
        with self.hud_msgbox as hud:
            hud.clear((0,0,0,0))
            hud.cr.identity_matrix()

            t = pygame.time.get_ticks() / 1000.0
            s = (t - self.texttime) / 4.0

            if s > 1.0:
                if len(self.textbuf) > 0:
                    self.texttime = pygame.time.get_ticks() / 1000.0
                    self.text = self.textbuf.pop(0)
            else:
                a = min(1.0-s, 0.2) * 5
                hud.cr.translate(0,25)
                hud.text(self.text, self.font, color=(1,0.8,0,a), width=hud.width, alignment=ALIGN_CENTER)

        visible = 34. / self.camera_max
        offset = self.camera.x / float(self.camera_max + 42.0)
        with self.scrollbar as hud:
            hud.clear((1,0,1,0))
            hud.rectangle(self.size.x * offset, 0, self.size.x * visible, hud.height, (0,1,1,1))

        with self.hud_ui as hud:
            hud.clear((1,1,1,0))
            hud.cr.identity_matrix()
            hud.cr.translate(20, 25)
            hud.text('Player %d' % (self.player+1,), self.font_ui)

            hud.cr.identity_matrix()
            hud.cr.translate(20, 70)
            hud.text('Angle: %3.0f' % self.angle[self.player], self.font_ui)

            hud.cr.identity_matrix()
            hud.cr.translate(20, 100)
            hud.text('Force: %3.0f' % self.force[self.player], self.font_ui)

    def render_world(self):
        view = Matrix.lookat(
            self.camera.x + 19, self.camera.y, 15,
            self.camera.x + 19, self.camera.y, 0,
            0,1,0)

        with self.fbo as frame:
            frame.clear(0,0.03,0.15,1)

            Shader.upload_projection_view(self.projection, view)
            Shader.upload_game(None)
            Shader.upload_light(self.ambient_light, self.cull_lights())

            # parallax background
            pm = Matrix.transform(
                0.75 * self.camera.x, self.camera.y * 0.5 - 12, 0,
                (19*4) * self.parallax_rep, 19, 0
            )
            self.shader_hud.bind()
            self.parallax.texture_bind()
            Shader.upload_model(pm)
            self.repquad.draw()

            Shader.upload_projection_view(self.projection, view)

            self.shader.bind()
            self.map.draw()

            # entities
            for obj in self.map.obj:
                obj.draw()
            self.projectile.draw()

    def render(self):
        glClearColor(1,0,1,1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        self.render_hud()
        self.render_world()

        mat = Matrix.scale(self.size.x, self.size.y)
        Shader.upload_projection_view(self.ortho, Matrix.identity())
        Shader.upload_model(mat)

        self.fbo.bind_texture()
        self.post.bind()
        self.quad.draw()

        y = self.size.x * (160./800)

        # hud background
        pm = Matrix.transform(
            0, y, 0,
            self.size.x, -y, 1
        )
        self.shader_hud.bind()
        self.hudbg.texture_bind()
        Shader.upload_model(pm)
        self.quad.draw()

        # ui
        pm = Matrix.transform(
            0, self.hud_ui.height, 0,
            self.hud_ui.width, -self.hud_ui.height, 1
        )
        self.hud_ui.draw()
        self.shader_hud.bind()
        Shader.upload_model(pm)
        self.quad.draw()

        # messagebox
        mat = Matrix.translate(self.size.x / 2 - self.hud_msgbox.width / 2, self.size.y - self.hud_msgbox.height)
        Shader.upload_model(mat)
        self.hud_msgbox.draw()

        # scrollbar
        mat = Matrix.translate(0, y-8-2)
        Shader.upload_model(mat)
        self.scrollbar.draw()

        pygame.display.flip()

    def cull_lights(self):
        return self.map.objects['Lights']

    def run(self):
        self._running = True
        while self.running():
            self.poll()
            self.update()
            self.render()

    def message(self, text):
        self.textbuf.append(text)

def run():
    pygame.display.init()
    pygame.mixer.init(channels=3, buffer=1024)
    pygame.mouse.set_visible(True)

    game = Game()

    # superglobals for quick access
    __builtins__['game'] = game

    game.init(Vector2i(800,600), fullscreen=False)
    #game.init(Vector2i(0,0), fullscreen=True)
    game.run()

    # force deallocation
    image.cleanup()
    del __builtins__['game']
    del game
