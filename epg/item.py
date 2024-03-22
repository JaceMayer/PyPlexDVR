import tvdb_v4_official
import moviepy.editor as mp
from config import dvrConfig
from .cache import cache


class item:
    def __init__(self, path, channelBaseDir):
        self.path = path
        self.baseDir = channelBaseDir
        self.title = ""
        self.desc = ""
        self.length = 0
        self.startTime = None
        self.endTime = None
        if channelBaseDir is not None:
            self.getEPGData()

    def getStartTime(self):
        if isinstance(self.startTime, str):
            return self.startTime
        else:
            return self.startTime.strftime("%Y%m%d%H%M%S")

    def getEndTime(self):
        if isinstance(self.endTime, str):
            return self.endTime
        else:
            return self.endTime.strftime("%Y%m%d%H%M%S")

    def getEPGData(self):
        title = self.path.split(self.baseDir)[1].split('/')[0]
        if title == "":
            title = self.path.split(self.baseDir)[1][1:-3]
        self.title = title.encode('utf-8').strip().decode()
        EPGcache = cache(self.title)
        EPGcache.loadCacheIfExists()
        if not EPGcache.cacheLoaded or EPGcache.getItemFromCache(self.path) is None:
            self.t = tvdb_v4_official.TVDB(dvrConfig["EPG"]["TMDBAPIKey"])
            try:
                show = self.t.search(self.title)
                self.desc = show[0]['overview']
            except Exception as e:
                try:
                    self.title = self.title.split('(')[0][:-1]
                    show = self.t.search(self.title)
                    self.desc = show[0]['overview']
                except Exception as e:
                    print("Unable to find match for %s" % self.title)
                    self.desc = self.title
            self.length = self.getLength()
            if not EPGcache.cacheLoaded:
                EPGcache.cache["title"] = self.title
                EPGcache.cache["desc"] = self.desc
            EPGcache.addItemToCache(self.path, self.length)
            EPGcache.saveCacheToDisk()
        else:
            self.length = EPGcache.getItemFromCache(self.path)
            self.desc = EPGcache.cache["desc"]
            self.title = EPGcache.cache["title"]

    def getLength(self):
        try:
            duration = mp.VideoFileClip(self.path).duration / 60
            return duration
        except:
            print("Unable to get Duration for %s" % self.path)
            return 30