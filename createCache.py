from config import dvrConfig
from channel.FFMPEG import FFMPEG

if not dvrConfig["EPG"]["generate"]:
    import sys
    sys.exit()

print("Creating EPG Cache")

channelMap = {
}

# Defines and sets up FFMPEG channels
if "Channels" in dvrConfig:
    for channelDef in dvrConfig["Channels"]:
        channelDef["id"] = "ffmpeg-"+str(channelDef["id"])
        channelMap[channelDef["id"]] = FFMPEG(channelDef)

print("EPG Cache Created")