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

    def getFFMPEGCmd(self):
        return ["ffmpeg", "-v", "error", "-reconnect_at_eof", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", str(dvrConfig["FFMPEG"]['streamReconnectDelay']), "-async", "1", "-re", "-i",
                self.stream,
                "-q:v", str(self.videoQuality), "-acodec", "mp3", "-vcodec", "copy", "-f",
                "mpegts",
                "-"]
