from channel.FFMPEG import FFMPEG
from config import dvrConfig


print("Creating EPG Cache")

channelMap = {
}

channelID = 0

# Defines and sets up FFMPEG channels
for channelDef in dvrConfig.get("Channels", []):
    channelDef["id"] = "ffmpeg-" + str(channelID)
    channelMap[channelDef["id"]] = FFMPEG(channelDef)
    channelID += 1


from epg.cache import cacheMap

for cache in cacheMap.values():
    cache.saveCacheToDisk()

print("EPG Cache Created")
