import os
import subprocess
import random
import threading
import time
from channelBuffer import channelBuffer


class channel:
    
    def __init__(self, id, name, config, scanPaths):
        self.id = id
        self.name = name
        self.url = 'http://%s:%s/stream/%s' % (config["bindAddr"], config["port"], id)
        self.scanDir = config['scanDir']
        self.scanPaths = scanPaths
        self.showPaths = []
        self.ranShows = []
        self.scanShows()
        self.buffer = []
        t = threading.Thread(target=self.runChannel, args = ())
        t.start()

    def isScannedFileVideo(self, file):
        if file.startswith('.') or file.endswith(".part"):
            return False
        if file.split('.')[-1] not in ('mkv', 'avi', 'mp4'):
            return False
        return True

    def shuffleShows(self):
        random.shuffle(self.showPaths)
        random.shuffle(self.showPaths)
        random.shuffle(self.showPaths)

    def scanShows(self):
        for path in self.scanPaths:
            path = self.scanDir + path
            for file in os.listdir(path):
                if file.startswith('.') or file.endswith(".part"): continue
                if os.path.isfile('%s/%s' % (path, file)) and self.isScannedFileVideo(file):
                    self.showPaths.append('%s/%s' %(path, file))
                else:
                    for seasonFile in os.listdir('%s/%s' % (path, file)):
                        if self.isScannedFileVideo(seasonFile):
                            self.showPaths.append('%s/%s/%s' % (path, file, seasonFile))
        print("Scanning shows for channel %s complete - %s shows found" % (self.name, str(len(self.showPaths))))
        self.shuffleShows()

    def getShow(self):
        if len(self.showPaths) == 0:
            print("Available show list Empty")
            self.showPaths = self.ranShows
            self.shuffleShows()
            self.ranShows = []
        show = self.showPaths.pop(0)
        self.ranShows.append(show)
        print('Running show %s' % show)
        return show

    def createBuffer(self):
        buffer = channelBuffer()
        self.buffer.append(buffer)
        return buffer

    def removeBuffer(self, buffer):
        buffer.destroy()
        self.buffer.remove(buffer)

    def runChannel(self):
        print('Starting FFMPEG channel %s' % self.name)
        while True:
            cmd = ["ffmpeg", "-re", "-i", self.getShow(), "-q:v", "1", "-movflags", "frag_keyframe+empty_moov", "-f", "mpegts", "-"]
            try:
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize =0)
            except Exception as e:
                print("Error during FFMPEG execution:", e)
            line = process.stdout.read(1024)
            while True:
                if line == b'':
                     process.poll()
                     if isinstance(process.returncode, int):
                         break
                for buffer in self.buffer: buffer.append(line)
                line = process.stdout.read(1024)
                
            
