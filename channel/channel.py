import logging
import subprocess
import threading

from channel.buffer import buffer
from config import dvrConfig


class channel:
    def __init__(self, channelDef):
        self.name = channelDef["name"]
        self.logger = logging.getLogger(self.name)
        self.id = channelDef["id"]
        self.url = '%s/stream/%s' % (dvrConfig["Server"]['url'], self.id)
        self.buffer = []
        self._subprocess = None
        self._channelOnAir = False
        self._thread = None
        self.videoQuality = channelDef.get("videoQuality", dvrConfig["FFMPEG"]['videoQuality'])
        self.resolution = channelDef.get("resolution", [1280, 720])
        with open("assets/channelUnavailable.ts", "rb") as blankTS:
            self.blankVideo = blankTS.read()

    def createBuffer(self):
        if not self._channelOnAir:
            self.logger.debug("Channel is currently off air - starting FFMPEG process")
            self._thread = threading.Thread(target=self.runChannel, args=())
            self._thread.start()
        clBuffer = buffer()
        self.buffer.append(clBuffer)
        return clBuffer

    def removeBuffer(self, buffer):
        buffer.destroy()
        self.buffer.remove(buffer)
        if len(self.buffer) == 0:
            self.logger.debug("Channel has 0 watchers, terminating FFMPEG")
            self._channelOnAir = False

    # Stub function to be overridden by subclasses
    def getFFMPEGCmd(self):
        raise NotImplementedError()

    def runChannel(self):
        if self._channelOnAir:
            self.logger.warning("Received duplicate request to start the channel")
            return
        self._channelOnAir = True
        while True:
            try:
                self._subprocess = subprocess.Popen(self.getFFMPEGCmd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
            except Exception as e:
                self.logger.error("Error during FFMPEG execution:", e)
                return
            while (line := self._subprocess.stdout.read(1024)) and self._channelOnAir:
                for buffer in self.buffer: buffer.append(line)
            if not self._channelOnAir:
                self._subprocess.communicate(b'q')
                self._subprocess.terminate()
                self._subprocess.poll()
                if self._subprocess.returncode is None:
                    self.logger.error("Subprocess failed to Terminate")
                    self._subprocess.kill()
                self._subprocess = None
                return

