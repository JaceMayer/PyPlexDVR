from flask import Flask, Response, request, jsonify, abort, render_template, stream_with_context
from channel import channel
from streamChannel import streamChannel
from config import dvrConfig

app = Flask(__name__)

channelMap = {
}

for channelDef in dvrConfig["Channels"]:
    channelMap[channelDef["id"]] = channel(channelDef)

for channelDef in dvrConfig["Streams"]:
    channelMap[channelDef["id"]] = streamChannel(channelDef)

discoverData = {
    'BaseURL': 'http://%s:%s' % (dvrConfig["Server"]['bindAddr'], str(dvrConfig["Server"]['bindPort'])),
    'DeviceAuth': 'pytv',
    'DeviceID': 'pytv-1',
    'FirmwareName': 'bin_1.0.0',
    'FirmwareVersion': '1.0.0',
    'FriendlyName': dvrConfig['DVR']['friendlyName'],
    'LineupURL': 'http://%s:%s/lineup.json' % (dvrConfig["Server"]['bindAddr'], str(dvrConfig["Server"]['bindPort'])),
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
    return render_template('device.xml',data=discoverData),{'Content-Type': 'application/xml'}


@app.route('/epg.xml')
def epg():
    return render_template('xmltv.xml', channels=list(channelMap.values())),{'Content-Type': 'application/xml'}


@app.route('/stream/<channel>')
def stream(channel):
    def generate(channel):
        buffer = channelMap[channel].createBuffer()
        try:
            while True:
                if buffer.length() != 0:
                    yield buffer.pop(0)
        except GeneratorExit:
            channelMap[channel].removeBuffer(buffer)
    return Response(generate(int(channel)), mimetype='video/MP2T')


@app.route('/lineup_status.json')
def status():
    status = {'ScanInProgress': 0,'ScanPossible': 0, 'Source': 'Cable', 'SourceList':['Cable']}
    return jsonify(status)


@app.route('/lineup.json')
def lineup():
    lineup = []
    for channel in channelMap.keys():
        cl = channelMap[channel]
        lineup.append({"GuideName": cl.name, "GuideNumber": cl.id, "URL": cl.url})
    return jsonify(lineup)


if __name__ == '__main__':
    app.run(host=dvrConfig["Server"]['bindAddr'], port=dvrConfig["Server"]['bindPort'], debug=False)
