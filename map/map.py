import asyncio
import json
from datetime import datetime

import pymongo
from pymongo import MongoClient

from quart import Quart, request, url_for, jsonify, render_template

app = Quart(__name__)
client = MongoClient()
db = client.instagram

@app.route('/')
async def index():
    start_ts = db.mapentries.find_one(sort=[('ts', pymongo.ASCENDING)])['ts'] - 60*60*24*31
    start_value = datetime.utcfromtimestamp(start_ts).strftime('%Y, %m, %d')

    end_ts = db.mapentries.find_one(sort=[('ts', pymongo.DESCENDING)])['ts'] + 60*60*24*31
    end_value = datetime.utcfromtimestamp(end_ts).strftime('%Y, %m, %d')

    return await render_template('map.html', range_selector_start_value=start_value, range_selector_end_value=end_value, hashtag_filter='bicycletouring')

@app.route('/floriscycles')
async def floriscycles():
    start_value = '2017, 09, 09'
    end_value = '2019, 01, 14'

    return await render_template('map_floriscycles.html', range_selector_start_value=start_value, range_selector_end_value=end_value)

@app.route('/get_map_entries/<path:subpath>')
async def get_map_entries(subpath):
    # Parse request URI
    if subpath[-1] == '/':
        subpath = subpath[:-1] # remove trailing slash

    tokens = subpath.split('/')
    sw_lng, sw_lat = float(tokens[0]), float(tokens[1])
    ne_lng, ne_lat = float(tokens[2]), float(tokens[3])
    ts_begin, ts_end = int(tokens[4]), int(tokens[5])

    username = request.args.get('username') #if key doesn't exist, returns None
    hashtag = request.args.get('hashtag') #if key doesn't exist, returns None

    sort = request.args.get('sort') #if key doesn't exist, returns None

    print(f'{request.path} -> returning JSON for input: {sw_lng} {sw_lat} {ne_lng} {ne_lat} {ts_begin} {ts_end} (u={username} ht={hashtag})')

    # Build the filter dict
    f = {'ts': {'$gte': ts_begin, '$lte': ts_end},
         'loc': {'$within': {'$box': [[sw_lng, sw_lat], [ne_lng, ne_lat]]}}}

    if username:
        f['username'] = username
    if hashtag:
        f['hashtags'] = hashtag

    # Use aggregation instead of find, so we can retrieve random documents:
    aggr_dicts = list()
    aggr_dicts.append({'$match': f})

    N = 100
    if not sort or sort == 0: # Get N most popular documents (by likes)
        aggr_dicts.append({'$sort': {'likes': pymongo.DESCENDING}})
        aggr_dicts.append({'$limit': N})
    elif sort == 1: # Get N most recent documents
        aggr_dicts.append({'$sort': {'ts': pymongo.DESCENDING}})
        aggr_dicts.append({'$limit': N})
    elif sort == 2: # Get N random documents:
        aggr_dicts.append({'$sample': {'size': N}})

    # exclude _id field:
    aggr_dicts.append({'$project': {'_id': False}})
    print(aggr_dicts)

    mapentries = db.mapentries.aggregate(aggr_dicts)
    map_entries = list(mapentries)

    return jsonify(map_entries)

if __name__ == "__main__":

    app.run('localhost', port=5000)
