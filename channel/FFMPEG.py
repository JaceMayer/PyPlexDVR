import logging
import math
import os
import random
import subprocess
import threading
from datetime import datetime, timedelta

from channel.channel import channel
from channel.buffer import buffer
from config import dvrConfig
from epg.item import item


class FFMPEG(channel):

    def __init__(self, channelDef):
        super().__init__(channelDef)
        self.scanDir = channelDef["baseDir"]
        self.scanPaths = channelDef.get("showDirs", [""])
        self.randomType = channelDef.get("random", "episode").lower()
        if self.randomType not in ("episode", "show"):
            raise AttributeError("Channel random type must be either episode or show.")

        self.showPaths = []
        self.epgOrder = []
        self.epgData = {}
        self.scanShows()
        self.createEPGItems()

    def createEPGItems(self):
        time = datetime.now()
        for show in self.epgOrder:
            self.epgData[show] = item(show, self.scanDir)
            self.epgData[show].startTime = datetime.fromtimestamp(time.timestamp())
            time += timedelta(minutes=math.ceil(self.epgData[show].length))
            self.epgData[show].endTime = datetime.fromtimestamp(time.timestamp())

    def isScannedFileVideo(self, file):
        if file.startswith('.') or file.endswith(".part"):
            return False
        if file.split('.')[-1] not in ('mkv', 'avi', 'mp4'):
            return False
        return True

    def shuffleShows(self):
        if self.randomType == "episode":
            shows = []
            for show in self.showPaths:
                shows += show
            random.shuffle(shows)
            random.shuffle(shows)
            random.shuffle(shows)
            self.epgOrder = shows
        else:
            shows = []
            showPaths = self.showPaths
            for i in range(sum(len(s) for s in self.showPaths)):
                show = random.randint(0, len(showPaths)-1)
                episode = random.choice(showPaths[show])
                showPaths[show].remove(episode)
                if len(showPaths[show]) == 0:
                    del showPaths[show]
                shows.append(episode)
                self.epgOrder = shows


    def scanShows(self):
        for path in self.scanPaths:
            scanValues = []
            path = self.scanDir + str(path)
            for file in os.listdir(path):
                if file.startswith('.') or file.endswith(".part"):
                    continue
                if os.path.isfile('%s/%s' % (path, file)):
                    if self.isScannedFileVideo(file):
                        scanValues.append('%s/%s' % (path, file))
                    else:
                        self.logger.warning("Unknown File Extension encountered %s/%s" % (path, file))
                else:
                    for seasonFile in os.listdir('%s/%s' % (path, file)):
                        if self.isScannedFileVideo(seasonFile):
                            scanValues.append('%s/%s/%s' % (path, file, seasonFile))
            if len(scanValues) != 0:
                self.showPaths.append(scanValues)
        self.logger.debug(
            "Scanning shows for channel %s complete - %s shows found" % (self.name, str(sum(len(s) for s in self.showPaths))))
        if len(self.showPaths) == 0:
            raise Exception("No shows found for channel %s." % self.name)
        self.shuffleShows()

    def getShow(self):
        self.logger.debug("Getting show + StartTime for channel %s" % self.name)
        availShows = sorted(
            [item for name, item in self.epgData.items() if item.endTime > datetime.now() + timedelta(minutes=2)],
            key=lambda epgItem: epgItem.startTime)
        self.logger.debug("Found %s available Shows" % len(availShows))
        if len(availShows) == 0:
            self.logger.warning("Available show list Empty")
            self.shuffleShows()
            self.createEPGItems()
            return self.getShow()
        show = availShows.pop(0)
        self.logger.debug('Running show %s' % show.path)
        return show.path, show.startTime

    def runChannel(self):
        if self._channelOnAir:
            self.logger.warning("Received duplicate request to start the channel")
            return
        self._channelOnAir = True
        while True:
            showData = self.getShow()
            if showData[1] > datetime.now():
                aheadBy = showData[1] - datetime.now()
                self.logger.warning("Show is starting before EPG Start Time - Running ahead by %s seconds" %
                                    str(aheadBy.total_seconds()))
                time = "00:00:01"
            else:
                elapsed = (datetime.now() - showData[1]).total_seconds()
                hours, remainder = divmod(elapsed, 3600)
                minutes, seconds = divmod(remainder, 60)
                time = '%s:%s:%s' % (int(hours), int(minutes), int(math.ceil(seconds)))
                self.logger.debug("Requesting FFMPEG Seek to %s" % time)
            cmd = ["ffmpeg", "-v", "error", "-async", "1", "-ss", time, "-re", "-i", showData[0], "-q:v",
                   str(self.videoQuality), "-acodec", "mp3", "-vf",
                   "scale=%s:%s:force_original_aspect_ratio=decrease,pad=%s:%s:(ow-iw)/2:(oh-ih)/2,setsar=1"
                   % (self.resolution[0], self.resolution[1], self.resolution[0], self.resolution[1]),
                   "-f", "mpegts", "-"]
            try:
                self._subprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
            except Exception as e:
                self.logger.error("Error during FFMPEG execution:", e)
                return
            while line := self._subprocess.stdout.read(1024):
                if not self._channelOnAir:
                    self._thread = None
                    return
                for buffer in self.buffer: buffer.append(line)
