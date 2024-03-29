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
from engine.camerasweep import CameraSweep
import math
import render.image as image
import item
import traceback
import random

def lerp(a, b, s):
    return a + (b - a) * s

def clamp(a, b, c):
    return min(max(a, b), c)

class DummyProjectile(object):
    def __init__(self, delay=None):
        self.delay = delay

    def __nonzero__(self):
        return False

    def update(self, map, dt):
        # hack to force a small delay between missing target and next player get to fire
        if self.delay is not None:
            self.delay -= dt
            if self.delay <= 0:
                game.next_player()
                self.delay = None

    def draw(self):
        pass

event_table = {}
def event(type):
    def wrapper(func):
        event_table[type] = func
        return func
    return wrapper

class Game(object):
    player1_cam = Vector2f(0, -11)
    player2_cam = Vector2f(94, -11)
    proj_spawn = [Vector2f(6, -10), Vector2f(125, -10)]

    def __init__(self):
        self._running = False
        self.camera = Vector2f(0,-11)

        self.camera_targets = [Game.player1_cam, Game.player2_cam]

    def init(self, size, fullscreen=False):
        flags = OPENGL|DOUBLEBUF
        if fullscreen:
            flags |= FULLSCREEN

        pygame.display.set_mode(size.xy, flags)
        pygame.display.set_caption('Ancient Earth')

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

        self.fbo = FBO(self.size, format=GL_RGB8, depth=True)

        self.shader = Shader.load('default')
        self.shader_hud = Shader.load('hud')
        self.post = Shader.load('post')
        self.windmax = 1.0
        self.random_wind()

        self.ambient_light = (1.0, 1.0, 1.0)

        fontsize = 16 + int(self.res_hack() * 14)

        self.map = Map('map.json')
        self.clock = pygame.time.Clock()
        self.hud_msgbox = HUD(Vector2i(500,100), 'msgbox')
        self.hud_ui = HUD(Vector2i(self.size.x, self.size.x * (160./800)), 'ui')
        self.scrollbar = HUD(Vector2i(self.size.x,28), 'scrollbar')
        self.font = self.hud_msgbox.create_font(size=fontsize)
        self.font_ui = self.hud_ui.create_font(size=fontsize, font='Comic Sans MS')
        self.camera_max = self.map.width - 38
        self.catapults = [self.map.get_named_item('Catapult 1'), self.map.get_named_item('Catapult 2')]

        self.reset()

        with self.hud_msgbox:
            self.hud_msgbox.clear((0,1,1,1))

    def res_hack(self):
        """ return [0..1] based on resolution where 800 gives 0 and 1920 gives 1 """
        a = float(self.size.x) - 800.
        b = 1920. - 800.
        return clamp(a/b, 0.0, 1.0)

    def running(self):
        return self._running

    def time(self):
        """ Get current time as float """
        return float(pygame.time.get_ticks()) / 1000.0

    def reset(self):
        self.projectile = DummyProjectile()
        self.angle = [60, 60]
        self.force = [150, 150]
        self.player = 0
        self.firing = False
        self.sweep = None
        self.miss = False
        self.follow_cam = None
        self.is_over = False
        self.textbuf = []
        self.texttime = -10.0
        self.catapults[0].set_loaded(True)
        self.random_wind()

    @event(pygame.QUIT)
    def quit(self, event=None):
        self._running = False

    def over(self):
        self.is_over = True

    def random_wind(self):
        r = float(random.randint(0, 10000)) / 10000 # [0..1]
        r = r * 2.0 - 1.0 # [-1..1]
        self.wind = r * self.windmax

    @event(pygame.KEYDOWN)
    def on_keypress(self, event):
        if event.key == 113 and event.mod & KMOD_CTRL: # ctrl+q
            return self.quit()
        if event.key == 27: # esc
            if not self.is_over:
                return self.quit()
            else:
                self.reset()
                return True
        if event.key == 13: # enter
            if not self.firing and not self.sweep:
                self.projectile_fire()

    @event(pygame.MOUSEBUTTONDOWN)
    def on_button(self, event):
        if not self.firing:
            if event.button == 4: self.camera.x += 5
            if event.button == 5: self.camera.x -= 5

    def next_player(self):
        self.player = 1 - self.player
        self.sweep = CameraSweep(src=self.follow_cam, dst=self.camera_targets[self.player])
        self.follow_cam = None
        self.firing = False
        self.random_wind()

    def projectile_fire(self):
        if not self.firing:
            self.firing = True

            a = math.radians(self.angle[self.player])
            f = self.force[self.player] * 5
            force = Vector2f(math.cos(a), math.sin(a)) * f

            if self.player == 1:
                force.x *= -1

            p = Game.proj_spawn[self.player]
            self.catapults[self.player].set_loaded(False)
            self.projectile = item.create('projectile', name='projectile', x=p.x, y=p.y, flip=self.player==0)
            self.projectile.impulse(force, 0.1)

    def projectile_miss(self, projectile):
        self.miss = True # defer so the projectile is rendered one more frame

    def projectile_hit(self, hit):
        # hack: remove all other message
        self.textbuf = []

        # hack: directly inject message
        if self.player != hit:
            self.text = 'Player %d hit the other player and won!' % (self.player+1)
        else:
            self.text = 'Player %d hit himself and lost...' % (self.player+1)
        self.text += '\n\nPress ESC to restart.'

        if hit == self.player:
            self.catapults[self.player].set_broken()
        else:
            self.catapults[1-self.player].set_broken()

        game.over()

    def poll(self):
        global event_table
        for event in pygame.event.get():
            func = event_table.get(event.type, None)
            if func is None:
                continue
            func(self, event)

    def update(self):
        if self.is_over:
            self.clock.tick(60)
            return

        key = pygame.key.get_pressed()

        if self.miss:
            self.message('Player %d missed the target' % (self.player+1,))
            self.old_projectile = self.projectile
            self.projectile = DummyProjectile(4)
            self.miss = False

        if not self.firing and not self.sweep:
            if key[260]: self.camera.x -= 1
            if key[262]: self.camera.x += 1

            if key[273]: self.angle[self.player] += 0.3
            if key[274]: self.angle[self.player] -= 0.3
            if key[275]: self.force[self.player] += 1
            if key[276]: self.force[self.player] -= 1

            self.camera.x = min(max(self.camera.x, 0), self.camera_max)
            self.angle[self.player] = min(max(self.angle[self.player], 0), 90)
            self.force[self.player] = min(max(self.force[self.player], 0), 3000)

        dt = 1.0 / self.clock.tick(60)
        self.map.update()

        # fixed step for better physics "simulation"
        self.projectile.update(self.map, 0.05)

        if self.sweep:
            self.camera, self.sweep = self.sweep.update(dt)
            if not self.sweep:
                self.catapults[self.player].set_loaded(True)

    def render_hud(self, camera):
        with self.hud_msgbox as hud:
            hud.clear((0,0,0,0))
            hud.cr.identity_matrix()

            t = pygame.time.get_ticks() / 1000.0
            s = (t - self.texttime) / 1.8

            if self.is_over:
                s = 0

            if s > 1.0:
                if len(self.textbuf) > 0:
                    self.texttime = pygame.time.get_ticks() / 1000.0
                    self.text = self.textbuf.pop(0)
            else:
                a = min(1.0-s, 0.2) * 5
                textcolor = (0,0,0,a)
                hud.cr.translate(0,25)
                hud.text(self.text, self.font, color=textcolor, width=hud.width, alignment=ALIGN_CENTER)

        visible = 34. / self.camera_max
        offset = camera.x / float(self.camera_max + 42.0)
        with self.scrollbar as hud:
            w = self.wind / self.windmax * 0.49
            hud.clear((1,0,1,0))
            hud.rectangle(self.size.x * offset, 10, self.size.x * visible, 8, (0,1,1,1))
            hud.rectangle(self.size.x * (0.5+w) - 4, 0, 8, hud.height, (1,0,0,0.8))

        with self.hud_ui as hud:
            hack = self.res_hack() * 20

            hud.clear((1,1,1,0))
            hud.cr.identity_matrix()
            hud.cr.translate(30 + hack, 30 + hack)
            hud.text('Player %d' % (self.player+1,), self.font_ui)

            hud.cr.identity_matrix()
            hud.cr.translate(30 + hack, 70 + hack)
            hud.text('Angle: %3.0f' % self.angle[self.player], self.font_ui)

            hud.cr.identity_matrix()
            hud.cr.translate(30 + hack, 100 + hack)
            hud.text('Force: %3.0f' % self.force[self.player], self.font_ui)

    def render_world(self, camera):
        view = Matrix.lookat(
            camera.x + 19, camera.y, 15,
            camera.x + 19, camera.y, 0,
            0,1,0)

        with self.fbo as frame:
            frame.clear(0,0.03,0.15,1)

            Shader.upload_projection_view(self.projection, view)
            Shader.upload_game(None)
            Shader.upload_light(self.ambient_light, self.cull_lights())

            # parallax background
            pm = Matrix.transform(
                0.75 * camera.x, camera.y * 0.5 - 12, 0,
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
            if not self.is_over:
                self.projectile.draw()

    def render(self):
        glClearColor(1,0,1,1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        camera = self.camera.copy()
        if self.projectile:
            camera.x = min(max(self.projectile.pos.x - 19, 0), self.camera_max)
            self.follow_cam = camera
        elif self.follow_cam:
            camera = self.follow_cam

        self.render_hud(camera)
        self.render_world(camera)

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
        mat = Matrix.translate(0, y-22)
        Shader.upload_model(mat)
        self.scrollbar.draw()

        pygame.display.flip()

    def cull_lights(self):
        return self.map.objects['Lights']

    def run(self):
        self._running = True
        while self.running():
            try:
                self.poll()
                self.update()
                self.render()
            except:
                traceback.print_exc()

    def message(self, text):
        self.textbuf.append(text)

def run():
    pygame.display.init()
    #pygame.mixer.init(channels=3, buffer=1024)
    pygame.mouse.set_visible(True)

    game = Game()

    # superglobals for quick access
    __builtins__['game'] = game

    #game.init(Vector2i(800,600), fullscreen=False)
    game.init(Vector2i(0,0), fullscreen=True)
    #game.init(Vector2i(1280,800), fullscreen=True)
    game.run()

    # force deallocation
    image.cleanup()
    del __builtins__['game']
    del game
