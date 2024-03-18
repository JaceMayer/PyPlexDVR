class streamChannel:
    def __init__(self, channelDef):
        self.name = channelDef["name"]
        self.id = channelDef["id"]
        self.url = channelDef["url"]
        self.epgData = []