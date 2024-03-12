import time
import os
import requests
from flask import Flask, Response, request, jsonify, abort, render_template, stream_with_context
from channel import channel

app = Flask(__name__)

config = {
    'bindAddr': '192.168.2.1',
    'port': 5004,
    'friendlyName': 'HomeTV',
    'scanDir': '/Volumes/Storage/TV/'
}
global channelMap
channelMap = {
    "id-0": channel("id-0", "Star Trek TV", config, ["Star Trek Deep Space Nine (1993)", "Star Trek Voyager (1995)", "Star Trek Strange New Worlds (2022)", 'Star Trek The Next Generation (1987)', 'Star Trek Prodigy',
        'Star Trek Picard', 'Star Trek Lower Decks (2020)', 'Star Trek Discovery (2017)', 'Star Trek (1966)']),
    "id-1": channel("id-1", "Cartoons", config, ["Hazbin Hotel", "Sonic Underground", 
        "Top Cat", "Super Mario World", "Steven Universe (2013)", "Steven Universe Future (2019)",
        "Adventure Time Fionna and Cake"]),
    "id-2": channel("id-2", "Dramas", config, ["Chicago Med", "Reverie", "Major Crimes"])
}

discoverData = {
    'BaseURL': 'http://%s:%s' % (config['bindAddr'], str(config['port'])),
    'DeviceAuth': 'pytv',
    'DeviceID': 'pytv-1',
    'FirmwareName': 'bin_1.0.0',
    'FirmwareVersion': '1.0.0',
    'FriendlyName': config['friendlyName'],
    'LineupURL': 'http://%s:%s/lineup.json' % (config['bindAddr'], str(config['port'])), 
    'Manufacturer': "Python",
    'ModelNumber': '1.0.0',
    'TunerCount': 100
}

@app.route('/discover.json')
def discover():
    return jsonify(discoverData)

@app.route('/')
@app.route('/device.xml')
@app.route('/capability')
def device():
    return render_template('device.xml',data = discoverData),{'Content-Type': 'application/xml'}

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
    return Response(generate(channel), mimetype='video/MP2T')

@app.route('/lineup_status.json')
def status():
    status = {'ScanInProgress':0,'ScanPossible':0, 'Source': 'Cable', 'SourceList':['Cable']}
    return jsonify(status)

@app.route('/lineup.json')
def lineup():
    lineup = []
    for channel in channelMap.keys():
        cl = channelMap[channel]
        lineup.append({"GuideName": cl.name, "GuideNumber": cl.id, "URL": cl.url})
    return jsonify(lineup)

if __name__ == '__main__':
    app.run(host=config['bindAddr'], port=config['port'], debug=False)
