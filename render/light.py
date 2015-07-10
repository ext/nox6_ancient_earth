import numpy as np

class Light(object):
    def __init__(self, pos, color, radius, falloff, phase_offset, phase_freq):
        self.pos = pos
        self.color = color
        self.radius = radius
        self.falloff = falloff
        self.phase_offset = phase_offset
        self.phase_freq = phase_freq

    def shader_data(self):
        data = []
        data += list((self.pos).xyz) + [0]
        data += list(self.color) + [0]
        data += [self.radius]
        data += [self.falloff]
        data += [self.phase_offset, self.phase_freq]
        return np.array(data, np.float32)
