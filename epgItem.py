import tvdb_v4_official
import moviepy.editor as mp
from config import dvrConfig


class epgItem:
    def __init__(self, path, channelBaseDir):
        self.t = tvdb_v4_official.TVDB(dvrConfig["EPG"]["TMDBAPIKey"])
        self.path = path
        self.baseDir = channelBaseDir
        self.title = ""
        self.desc = ""
        self.length = 0
        self.startTime = None
        self.endTime = None
        if channelBaseDir != None:
            self.getEPGData()

    def getEPGData(self):
        title = self.path.split(self.baseDir)[1].split('/')[0]
        if title == "":
            title = self.path.split(self.baseDir)[1][1:-3]
        self.title = title.encode('utf-8').strip().decode()
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

    def getLength(self):
        try:
            duration = mp.VideoFileClip(self.path).duration / 60
            return duration
        except:
            print("Unable to get Duration for %s" % self.path)
            return 30
