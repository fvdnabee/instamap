import asyncio
import json
from datetime import datetime

import pymongo
from pymongo import MongoClient

from quart import Quart, request, url_for, jsonify, render_template

app = Quart(__name__)
db = None

@app.route('/')
async def index():
    start_ts = db.mapentries.find_one(sort=[('ts', pymongo.ASCENDING)])['ts'] - 60*60*24*31
    start_value = datetime.utcfromtimestamp(start_ts).strftime('%Y, %m, %d')

    end_ts = db.mapentries.find_one(sort=[('ts', pymongo.DESCENDING)])['ts'] + 60*60*24*31
    end_value = datetime.utcfromtimestamp(end_ts).strftime('%Y, %m, %d')

    return await render_template('map.html', range_selector_start_value=start_value, range_selector_end_value=end_value)

@app.route('/get_map_entries/<path:subpath>')
async def get_map_entries(subpath):
    if subpath[-1] == '/':
        subpath = subpath[:-1] # remove trailing slash

    tokens = subpath.split('/')
    sw_lng, sw_lat = float(tokens[0]), float(tokens[1])
    ne_lng, ne_lat = float(tokens[2]), float(tokens[3])
    ts_begin, ts_end = int(tokens[4]), int(tokens[5])

    print(f'{request.path} -> returning JSON for input: {sw_lng} {sw_lat} {ne_lng} {ne_lat} {ts_begin} {ts_end}')

    f = {'ts': {'$gte': ts_begin, '$lte': ts_end},
         'loc': {'$within': {'$box': [[sw_lng, sw_lat], [ne_lng, ne_lat]]}}}

    mapentries = db.mapentries.find(filter=f, projection={'_id': False}, sort=[('likes', pymongo.DESCENDING)], limit=100)
    map_entries = list(mapentries)

    return jsonify(map_entries)

if __name__ == "__main__":
    client = MongoClient()
    db = client.instagram

    app.run('localhost', port=5000)
