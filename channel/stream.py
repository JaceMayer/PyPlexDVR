from config import dvrConfig
import subprocess
import threading
from epg.item import item
from channel.buffer import buffer
import logging
import select
import time


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

    def getBlankVideo(self):
        cmd = ["ffmpeg", "-v", "error", "-i", "assets/channelUnavailable.mp4", "-f", "mpegts", "-"]
        __subprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
        buffer = b''
        line = __subprocess.stdout.read(1024)
        while line != b'':
            buffer += line
            line = __subprocess.stdout.read(1024)
        return buffer

    def runChannel(self):
        self.__channelOnAir = True
        lastFrameT = time.time()
        while True:
            cmd = ["ffmpeg", "-v", "error", "-reconnect_at_eof", "1", "-reconnect_streamed","1",
                   "-reconnect_delay_max", str(dvrConfig["FFMPEG"]['streamReconnectDelay']), "-async", "1", "-re", "-i", self.stream,
                   "-q:v", str(dvrConfig["FFMPEG"]['videoQuality']), "-acodec", "mp3","-vcodec", "copy", "-f", "mpegts",
                   "-"]
            try:
                self.__subprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
                subprocessPoll = select.poll()
                subprocessPoll.register(self.__subprocess.stdout, select.POLLIN)
            except Exception as e:
                self.logger.error("Error during FFMPEG execution:", e)
                if time.time() - lastFrameT > 1:
                    lastFrameT = time.time()
                    frame = self.getBlankVideo()
                    for buffer in self.buffer: buffer.append(frame)
                continue
            line = b''
            while True:
                if not self.__channelOnAir:
                    self.__thread = None
                    return
                if line == b'':
                    self.__subprocess.poll()
                    if isinstance(self.__subprocess.returncode, int):
                        frame = self.getBlankVideo()
                        for buffer in self.buffer: buffer.append(frame)
                        break
                if subprocessPoll.poll(0):
                    lastFrameT = time.time()
                    line = self.__subprocess.stdout.read(1024)
                    for buffer in self.buffer: buffer.append(line)
                elif time.time() - lastFrameT > 1:
                    lastFrameT = time.time()
                    self.logger.warning("No FFMPEG data received in 1 seconds")
                    frame = self.getBlankVideo()
                    for buffer in self.buffer: buffer.append(frame)
                time.sleep(0.001)
