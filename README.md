# PyPlexDVR
This was created to constantly serve TV/Movies as a Live TV Stream to Plex Media Server.

Features:
- HDHomeRun DVR Emulation (using gunicorn + Flask)
- Media streaming from files (FFMPEG)
- Media streaming from HTTP (FFMPEG)

# Usage
Download and modify the DVR Configuration file
https://github.com/JaceMayer/PyPlexDVR/blob/main/config.yaml
Pull the latest docker image
```
docker pull ghcr.io/jacemayer/pyplexdvr:latest
```
Run the docker container passing in your media directiory, and your configuration file. 
```
docker run -v /PATH/TO/MEDIA:/CONFIGURED/PATH -v /PATH/TO/config.yaml:/home/appuser/config.yaml -p 5006:5006 -i -t ghcr.io/jacemayer/pyplexdvr:latest
```
