from channel.FFMPEG import FFMPEG
from config import dvrConfig


print("Creating EPG Cache")

channelMap = {
}

# Defines and sets up FFMPEG channels
if "Channels" in dvrConfig:
    for channelDef in dvrConfig["Channels"]:
        channelDef["id"] = "ffmpeg-" + str(channelDef["id"])
        channelMap[channelDef["id"]] = FFMPEG(channelDef)


from epg.cache import cacheMap

for cache in cacheMap.values():
    cache.saveCacheToDisk()

print("EPG Cache Created")
