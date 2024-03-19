import os
import subprocess
import random
import threading
import math
from channelBuffer import channelBuffer
from epgItem import epgItem
from datetime import datetime, timedelta
from config import dvrConfig


class channel:

    def __init__(self, channelDef):
        self.id = channelDef["id"]
        self.name = channelDef["name"]
        self.url = 'http://%s:%s/stream/%s' % (
        dvrConfig["Server"]['bindAddr'], dvrConfig["Server"]['bindPort'], self.id)
        self.scanDir = channelDef["baseDir"]
        if "showDirs" in channelDef:
            self.scanPaths = channelDef["showDirs"]
        else:
            self.scanPaths = [""]
        self.showPaths = []
        self.ranShows = []
        self.epgData = {}
        self.scanShows()
        self.buffer = []
        self.__subprocess = None
        self.__channelOnAir = False
        self.__thread = None
        if dvrConfig["EPG"]["generate"]:
            self.createEPGItems()

    def createEPGItems(self):
        time = datetime.now()
        for item in self.showPaths:
            self.epgData[item] = epgItem(item, self.scanDir)
            self.epgData[item].startTime = time.strftime("%Y%m%d%H%M%S")
            time += timedelta(minutes=math.ceil(self.epgData[item].length))
            self.epgData[item].endTime = time.strftime("%Y%m%d%H%M%S")

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
                    self.showPaths.append('%s/%s' % (path, file))
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
        if not self.__channelOnAir:
            print("Channel is off air - starting FFMPEG")
            self.__thread = threading.Thread(target=self.runChannel, args=())
            self.__thread.start()
        buffer = channelBuffer()
        self.buffer.append(buffer)
        return buffer

    def removeBuffer(self, buffer):
        buffer.destroy()
        self.buffer.remove(buffer)
        if len(self.buffer) == 0:
            print("Nobody buffering this channel - killing FFMPEG")
            self.__subprocess.kill()
            self.__subprocess = None
            self.__channelOnAir = False

    def runChannel(self):
        print('Starting FFMPEG channel %s' % self.name)
        self.__channelOnAir = True
        while True:
            cmd = ["ffmpeg", "-v", "error", "-re", "-i", self.getShow(), "-q:v", "15", "-acodec", "mp3", "-vf",
                   "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
                   "-f", "mpegts", "-"]
            try:
                self.__subprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
            except Exception as e:
                print("Error during FFMPEG execution:", e)
                return
            line = self.__subprocess.stdout.read(1024)
            while True:
                if not self.__channelOnAir:
                    self.__thread = None
                    return
                if line == b'':
                    self.__subprocess.poll()
                    if isinstance(self.__subprocess.returncode, int):
                        break
                for buffer in self.buffer: buffer.append(line)
                line = self.__subprocess.stdout.read(1024)
