import select
import subprocess
import time

from channel.channel import channel
from config import dvrConfig
from epg.item import item


class stream(channel):
    def __init__(self, channelDef):
        super().__init__(channelDef)
        self.stream = channelDef["url"]
        self.epgData = {
            "stream": item("Stream", None)
        }
        self.epgData["stream"].title = self.name
        self.epgData["stream"].desc = self.name
        self.epgData["stream"].startTime = "20240101000001"
        self.epgData["stream"].endTime = "20440101000001"

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
        if self._channelOnAir:
            self.logger.warning("Received duplicate request to start the channel")
            return
        self._channelOnAir = True
        lastFrameT = time.time()
        while True:
            cmd = ["ffmpeg", "-v", "error", "-reconnect_at_eof", "1", "-reconnect_streamed", "1",
                   "-reconnect_delay_max", str(dvrConfig["FFMPEG"]['streamReconnectDelay']), "-async", "1", "-re", "-i",
                   self.stream,
                   "-q:v", str(dvrConfig["FFMPEG"]['videoQuality']), "-acodec", "mp3", "-vcodec", "copy", "-f",
                   "mpegts",
                   "-"]
            try:
                self._subprocess = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
                subprocessPoll = select.poll()
                subprocessPoll.register(self._subprocess.stdout, select.POLLIN)
            except Exception as e:
                self.logger.error("Error during FFMPEG execution:", e)
                if time.time() - lastFrameT > 1:
                    lastFrameT = time.time()
                    frame = self.getBlankVideo()
                    for buffer in self.buffer: buffer.append(frame)
                continue
            line = b''
            while True:
                if not self._channelOnAir:
                    self._thread = None
                    return
                if line == b'':
                    self._subprocess.poll()
                    if isinstance(self._subprocess.returncode, int):
                        frame = self.getBlankVideo()
                        for buffer in self.buffer: buffer.append(frame)
                        break
                if subprocessPoll.poll(0.001):
                    lastFrameT = time.time()
                    line = self._subprocess.stdout.read(1024)
                    for buffer in self.buffer: buffer.append(line)
                elif time.time() - lastFrameT > 1:
                    lastFrameT = time.time()
                    self.logger.warning("No FFMPEG data received in 1 seconds")
                    frame = self.getBlankVideo()
                    for buffer in self.buffer: buffer.append(frame)
