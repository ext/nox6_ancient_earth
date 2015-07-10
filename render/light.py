import numpy as np

class Light(object):
    def __init__(self, pos, color, radius, falloff):
        self.pos = pos
        self.color = color
        self.radius = radius
        self.falloff = falloff

    def shader_data(self):
        data = []
        data += list((self.pos).xyz) + [0]
        data += list(self.color) + [0]
        data += [self.radius]
        data += [self.falloff]
        data += [0,0] # fill struct padding
        return np.array(data, np.float32)
