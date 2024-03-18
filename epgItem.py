import tvdb_v4_official
import moviepy.editor as mp
import os

class epgItem:
    t = tvdb_v4_official.TVDB("feb18639-a308-40c4-a988-9c822574e5ba")
    def __init__(self, path):
        self.path = path
        self.title = ""
        self.desc = ""
        self.length = 0
        self.startTime = None
        self.endTime = None
        print("finding EPG Data for item %s" % path)
        self.getEPGData()

    def getEPGData(self):
        if '/Volumes/Storage/TV' in self.path:
            print("TV Show")
            self.title = self.path.split('/Volumes/Storage/TV/')[1].split('/')[0]
            print(self.title)
            self.title = self.title.encode('utf-8').strip().decode()
            print(self.title)
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
        else:
            self.path = self.path.replace('/Volumes/Storage/Movies/','')
            firstbracket = self.path.find("(")
            res = self.t.search(self.path[:firstbracket].replace('.', ' '))
            if len(res) == 0:
                dateLoc = self.path.find("20")
                res =  self.t.search(self.path[:dateLoc].replace('.', ' '))
                if len(res) == 0:
                    print("Giving up on matching %s" % self.path)
                    self.title = "A movie"
                    self.desc = "Movie"
                    self.length = self.getLength()
            print("%s matched to %s" % (self.path, res[0]["extended_title"]))
            tvdbData = res[0]
            self.title = tvdbData["extended_title"]
            self.desc = tvdbData["overview"]
            extData = self.t.get_movie(tvdbData["tvdb_id"])
            self.length = extData["runtime"]

    def getLength(self):
        print("Getting length for path %s" % self.path)
        try:
            duration =  mp.VideoFileClip(self.path).duration / 60
            print("%s duration = %s" % (self.path, str(duration)))
            return duration
        except:
            print("Unable to get Duration for %s" % self.path)
            return 30
