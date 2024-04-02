import os

import yaml

cacheMap = {}

class cache:
    def __init__(self, showName):
        self.showName = showName
        cacheMap[self.showName] = self
        if not os.path.isdir("cache"):
            print("Creating base cache dir")
            os.mkdir("cache")
        self.cache = {"items": {}}
        self.cacheLoaded = False

    def hasEPGDesc(self):
        return self.cacheLoaded or "title" in self.cache

    def getItemFromCache(self, itemName):
        return self.cache["items"].get(itemName, None)

    def addItemToCache(self, itemName, length):
        self.cache["items"][itemName] = length

    def loadCacheIfExists(self):
        if not os.path.isfile("cache/%s.yaml" % self.showName):
            print("No cache for item %s" % self.showName)
            return
        with open("cache/%s.yaml" % self.showName, 'r') as stream:
            self.cache = yaml.safe_load(stream)
        self.cacheLoaded = True

    def saveCacheToDisk(self):
        with open("cache/%s.yaml" % self.showName, "w") as stream:
            yaml.dump(self.cache, stream)


def getCache(showName):
    if showName in cacheMap:
        return cacheMap[showName]
    c = cache(showName)
    c.loadCacheIfExists()
    return c
