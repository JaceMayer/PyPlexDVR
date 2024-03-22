from config import dvrConfig
import subprocess
import threading
from epg.item import item
from channel.buffer import buffer
import logging


class stream:
    def __init__(self, channelDef):
        self.name = channelDef["name"]
        self.logger = logging.getLogger("Stream-%s"%self.name)
        self.id = channelDef["id"]
        self.stream = channelDef["url"]
        self.url = '%s/stream/%s' % (dvrConfig["Server"]['url'], self.id)
        self.epgData = {
            "stream": item("Stream", None)
        }
        self.epgData["stream"].title = self.name
        self.epgData["stream"].desc = self.name
        self.epgData["stream"].startTime = "20240101000001"
        self.epgData["stream"].endTime = "20440101000001"
        self.buffer = []
        self.__subprocess = None
        self.__channelOnAir = False
        self.__thread = None

    def createBuffer(self):
        if not self.__channelOnAir:
            self.logger.debug("Channel is currently off air - starting FFMPEG process")
            self.__thread = threading.Thread(target=self.runChannel, args=())
            self.__thread.start()
        clBuffer = buffer()
        self.buffer.append(clBuffer)
        return clBuffer

    def removeBuffer(self, buffer):
        buffer.destroy()
        self.buffer.remove(buffer)
        if len(self.buffer) == 0:
            self.logger.debug("Channel has 0 watchers, terminating FFMPEG")
            self.__subprocess.kill()
            self.__subprocess = None
            self.__channelOnAir = False

    def runChannel(self):
        print('Starting Stream channel %s' % self.name)
        self.__channelOnAir = True
        while True:
            cmd = ["ffmpeg", "-v", "error", "-reconnect_at_eof", "1", "-reconnect_streamed","1", "-reconnect_delay_max", str(dvrConfig["FFMPEG"]['streamReconnectDelay']), "-re", "-i", self.stream, "-q:v", str(dvrConfig["FFMPEG"]['videoQuality']), "-acodec", "mp3","-vcodec", "copy", "-f", "mpegts", "-"]
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
