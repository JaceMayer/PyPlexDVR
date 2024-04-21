import math
import os
import random
from datetime import datetime, timedelta

from channel.channel import channel
from channel.WatchDog import WatchDogObserver
from epg.item import item
from epg.cache import cacheMap
from config import dvrConfig
from plex import refreshEPG


class FFMPEG(channel):

    def __init__(self, channelDef):
        super().__init__(channelDef)
        self.scanDir = channelDef["baseDir"]
        self.scanPaths = channelDef.get("showDirs", [""])
        self.randomType = channelDef.get("random", "episode").lower()
        if self.randomType not in ("episode", "show"):
            raise AttributeError("Channel random type must be either episode or show.")
        if dvrConfig["Server"]['useWatchdog']:
            self.watchDog = WatchDogObserver(self.scanDir, self.scanPaths, self)
        self.pendingReboot = True
        self.showPaths = []
        self.epgOrder = []
        self.epgData = {}
        self.scanShows()
        self.createEPGItems()

    def pendReboot(self):
        self.pendingReboot = True
        if len(self.buffer) != 0:
            self.logger.debug("Queueing channel reboot - will take place when clients have disconnected")
        else:
            self.rebootChannel()

    def rebootChannel(self):
        self.logger.debug("Rebooting channel...")
        self.showPaths = []
        self.epgOrder = []
        self.epgData = {}
        self.scanShows()
        self.createEPGItems()
        for cache in cacheMap.values():
            cache.saveCacheToDisk()
        refreshEPG()

    def createBuffer(self):
        if self.pendingReboot:
            return None
        return super().createBuffer()

    def removeBuffer(self, buffer):
        super().removeBuffer(buffer)
        if not self._channelOnAir and self.pendingReboot:
            self.rebootChannel()

    def ensureEPGWontEmpty(self):
        availShows = sorted(
            [item for name, item in self.epgData.items() if item.endTime > datetime.now() + timedelta(minutes=2)],
            key=lambda epgItem: epgItem.startTime)
        if len(availShows) == 0:
            self.logger.warning("Available show list Empty")
            self.shuffleShows()
            self.createEPGItems()
            return
        else:
            self.shuffleShows()
            for show in availShows:
                if show.path in self.epgOrder:
                    self.logger.debug("Removing show %s from EPGOrder as it exists" % show.path)
                    self.epgOrder.remove(show.path)
            time = availShows[-1].endTime
            for show in self.epgOrder:
                self.epgData[show] = item(show, self.scanDir)
                self.epgData[show].startTime = datetime.fromtimestamp(time.timestamp())
                time += timedelta(minutes=math.ceil(self.epgData[show].length))
                self.epgData[show].endTime = datetime.fromtimestamp(time.timestamp())

    def createEPGItems(self):
        time = datetime.now()
        for show in self.epgOrder:
            self.epgData[show] = item(show, self.scanDir)
            self.epgData[show].startTime = datetime.fromtimestamp(time.timestamp())
            time += timedelta(minutes=math.ceil(self.epgData[show].length))
            self.epgData[show].endTime = datetime.fromtimestamp(time.timestamp())
        self.pendingReboot = False

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
                show = random.randint(0, len(showPaths) - 1)
                episode = random.choice(showPaths[show])
                showPaths[show].remove(episode)
                if len(showPaths[show]) == 0:
                    del showPaths[show]
                shows.append(episode)
                self.epgOrder = shows

    def scanShows(self):
        for path in self.scanPaths:
            scanValues = []
            path = os.path.join(self.scanDir, str(path))
            for file in os.listdir(path):
                if file.startswith('.') or file.endswith(".part"):
                    continue
                f = os.path.join(path, file)
                if os.path.isfile(f):
                    if self.isScannedFileVideo(file):
                        if not os.access(f, os.R_OK):
                            self.logger.warning("Do not have read permissions on file %s" % f)
                            continue
                        scanValues.append(f)
                    else:
                        self.logger.warning("Unknown File Extension encountered %s/%s" % (path, file))
                else:
                    for seasonFile in os.listdir(f):
                        if self.isScannedFileVideo(seasonFile):
                            seasonf = os.path.join(f, seasonFile)
                            if not os.access(seasonf, os.R_OK):
                                self.logger.warning("Do not have read permissions on file %s" % seasonf)
                                continue
                            scanValues.append(seasonf)
            if len(scanValues) != 0:
                self.showPaths.append(scanValues)
        self.logger.debug(
            "Scanning shows for channel %s complete - %s shows found" % (
                self.name, str(sum(len(s) for s in self.showPaths))))
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
        if not os.access(show.path, os.R_OK):
            self.logger.error("Lost read permissions on file %s" % show.path)
            return "assets/channelUnavailable.ts", datetime.now()
        self.logger.debug('Running show %s' % show.path)
        return show.path, show.startTime

    def getFFMPEGCmd(self):
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
        return ["ffmpeg", "-v", "error", "-async", "1", "-ss", time, "-re", "-i", showData[0], "-q:v",
                str(self.videoQuality), "-acodec", "mp3", "-vf",
                "scale=%s:%s:force_original_aspect_ratio=decrease,pad=%s:%s:(ow-iw)/2:(oh-ih)/2,setsar=1"
                % (self.resolution[0], self.resolution[1], self.resolution[0], self.resolution[1]),
                "-f", "mpegts", "-"]
