from gevent import monkey, sleep

monkey.patch_all()
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from flask import Flask, Response, jsonify, render_template, stream_with_context
from channel.FFMPEG import FFMPEG
from channel.stream import stream
from config import dvrConfig

app = Flask(__name__)

channelMap = {
}

channelID = 0

# Defines and sets up FFMPEG channels
for channelDef in dvrConfig.get("Channels", []):
    channelDef["id"] = "ffmpeg-" + str(channelID)
    channelMap[channelDef["id"]] = FFMPEG(channelDef)
    channelID += 1

channelID = 0
# Defines and sets up streaming channels
for channelDef in dvrConfig.get("Streams", []):
    channelDef["id"] = "stream-" + str(channelID)
    channelMap[channelDef["id"]] = stream(channelDef)
    channelID += 1

discoverData = {
    'BaseURL': dvrConfig["Server"]['url'],
    'DeviceAuth': 'pytv',
    'DeviceID': 'pytv-1',
    'FirmwareName': 'bin_1.0.0',
    'FirmwareVersion': '1.0.0',
    'FriendlyName': dvrConfig['DVR']['friendlyName'],
    'LineupURL': '%s/lineup.json' % (dvrConfig["Server"]['url']),
    'Manufacturer': "Python",
    'ModelNumber': '1.0.0',
    'TunerCount': dvrConfig['DVR']['tunerCount']
}


@app.route('/discover.json')
def discover():
    return jsonify(discoverData)


@app.route('/')
@app.route('/device.xml')
@app.route('/capability')
def device():
    return render_template('device.xml', data=discoverData), {'Content-Type': 'application/xml'}


@app.route('/epg.xml')
def epg():
    return render_template('xmltv.xml', channels=list(channelMap.values())), {'Content-Type': 'application/xml'}


@app.route('/stream/<channel>')
def stream(channel):
    def generate(channel):
        buffer = channelMap[channel].createBuffer()
        try:
            while True:
                if buffer.length() != 0:
                    yield buffer.pop(0)
                sleep(0.001)
        except GeneratorExit:
            channelMap[channel].removeBuffer(buffer)

    return Response(stream_with_context(generate(channel)), mimetype='video/MP2T')


@app.route('/lineup_status.json')
def status():
    return jsonify({'ScanInProgress': 0, 'ScanPossible': 0, 'Source': 'Cable', 'SourceList': ['Cable']})


@app.route('/lineup.json')
def lineup():
    return jsonify([{"GuideName": cl.name, "GuideNumber": cl.id, "URL": cl.url} for cl in channelMap.values()])
