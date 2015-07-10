import engine.map

class Map(engine.map.Map):
    def __init__(self, filename):
        engine.map.Map.__init__(self, filename)
        self.pickups = []

    def update(self):
        self.pickups = [x for x in self.pickups if not x.killed]
