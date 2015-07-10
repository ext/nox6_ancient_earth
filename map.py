import engine.map

class Map(engine.map.Map):
    def __init__(self, filename):
        engine.map.Map.__init__(self, filename)
        self.obj = self.objects['Player 1']

    def update(self):
        self.obj = [x for x in self.obj if not x.killed]
