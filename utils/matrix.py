from OpenGL.GL import *
from OpenGL.GLU import *

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
