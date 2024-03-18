from config import dvrConfig
import os
import subprocess
import random
import threading
import math
from epgItem import epgItem
from channelBuffer import channelBuffer

class streamChannel:
    def __init__(self, channelDef):
        self.name = channelDef["name"]
        self.id = channelDef["id"]
        self.stream = channelDef["url"]
        self.url = 'http://%s:%s/stream/%s' % (dvrConfig["Server"]['bindAddr'], dvrConfig["Server"]['bindPort'], self.id)
        self.epgData = {
            "stream": epgItem("Stream", None)
        }
        self.epgData["stream"].title = self.name
        self.epgData["stream"].desc = self.name
        self.epgData["stream"].startTime = "20240101000001"
        self.epgData["stream"].startTime = "20440101000001"
        self.buffer = []
        t = threading.Thread(target=self.runChannel, args=())
        t.start()

    def createBuffer(self):
        buffer = channelBuffer()
        self.buffer.append(buffer)
        return buffer

    def removeBuffer(self, buffer):
        buffer.destroy()
        self.buffer.remove(buffer)

    def runChannel(self):
        print('Starting Stream channel %s' % self.name)
        while True:
            cmd = ["ffmpeg", "-v", "error", "-re", "-i", self.stream, "-q:v", "15", "-acodec", "mp3", "-vf",
                   "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1",
                   "-f", "mpegts", "-"]
            try:
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
            except Exception as e:
                print("Error during FFMPEG execution:", e)
                return
            line = process.stdout.read(1024)
            while True:
                if line == b'':
                    process.poll()
                    if isinstance(process.returncode, int):
                        break
                for buffer in self.buffer: buffer.append(line)
                line = process.stdout.read(1024)
