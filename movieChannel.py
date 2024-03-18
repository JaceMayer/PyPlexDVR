from channel import channel

class movieChannel(channel):

    def __init__(self, id, name, config, scanPaths):
        self.movieDir = config["movieDir"]
        channel.__init__(self, id, name, config, scanPaths)

    def scanShows(self):
        self.scanDir = self.movieDir
        channel.scanShows(self)
