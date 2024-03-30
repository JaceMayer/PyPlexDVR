from channel.FFMPEG import FFMPEG
from config import dvrConfig

if not dvrConfig["EPG"]["generate"]:
    import sys

    sys.exit()

print("Creating EPG Cache")

channelMap = {
}

# Defines and sets up FFMPEG channels
if "Channels" in dvrConfig:
    for channelDef in dvrConfig["Channels"]:
        channelDef["id"] = "ffmpeg-" + str(channelDef["id"])
        channelMap[channelDef["id"]] = FFMPEG(channelDef)

print("EPG Cache Created")
