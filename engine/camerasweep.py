from utils.vector import lerp2

def clamp(x, a, b):
    """ Clamp value x to min a and max b """
    return min(max(x,a),b)

def linear(x):
    return x

def smoothstep(x):
    edge0 = 0
    edge1 = 1
    x = clamp((x - edge0)/(edge1 - edge0), 0.0, 1.0)
    return x*x*(3 - 2*x)

def smootherstep(x):
    edge0 = 0
    edge1 = 1
    x = clamp((x - edge0)/(edge1 - edge0), 0.0, 1.0)
    return x*x*x*(x*(x*6 - 15) + 10)

table = {
    'linear': linear,
    'smoothstep': smoothstep,
    'smootherstep': smootherstep,
}

class CameraSweep(object):
    def __init__(self, src, dst, duration=1.0, transition='smoothstep'):
        self.src = src
        self.dst = dst
        self.d = duration
        self.t = game.time()
        self.transition = table[transition]

    def update(self, dt):
        t = game.time() - self.t
        s = t / self.d

        if s <= 1.0:
            return lerp2(self.src, self.dst, self.transition(s)), self
        else:
            return self.dst, None
