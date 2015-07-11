from OpenGL.GL import *
from OpenGL.GLU import *
import math

class Matrix:
    @staticmethod
    def perspective(fov, size, near, far):
        glLoadIdentity()
        gluPerspective(fov, size.ratio(), near, far)
        return glGetFloatv(GL_MODELVIEW_MATRIX)

    @staticmethod
    def ortho(resolution):
        glLoadIdentity()
        gluOrtho2D(0.0, resolution.x, 0.0, resolution.y)
        return glGetFloatv(GL_MODELVIEW_MATRIX)

    @staticmethod
    def lookat(ex, ey, ez, cx, cy, cz, ux, uy, uz):
        glLoadIdentity()
        gluLookAt(ex, ey, ez, cx, cy, cz, ux, uy, uz)
        return glGetFloatv(GL_MODELVIEW_MATRIX)

    @staticmethod
    def identity():
        glLoadIdentity()
        return glGetFloatv(GL_MODELVIEW_MATRIX)

    @staticmethod
    def translate(x, y, z=0):
        tr = Matrix.identity()
        tr[3,0] = x
        tr[3,1] = y
        tr[3,2] = z
        return tr

    @staticmethod
    def scale(x, y, z=1):
        tr = Matrix.identity()
        tr[0,0] = x
        tr[1,1] = y
        tr[2,2] = z
        return tr

    @staticmethod
    def rotatez(angle):
        tr = Matrix.identity()
        tr[0,0] =  math.cos(angle)
        tr[1,0] = -math.sin(angle)
        tr[0,1] =  math.sin(angle)
        tr[1,1] =  math.cos(angle)
        return tr

    @staticmethod
    def transform(tx, ty, tz, sx, sy, sz):
        tr = Matrix.identity()
        tr[3,0] = tx
        tr[3,1] = ty
        tr[3,2] = tz
        tr[0,0] = sx
        tr[1,1] = sy
        tr[2,2] = sz
        return tr
