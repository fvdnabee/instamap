import asyncio
import json
from pymongo import MongoClient
from quart import Quart, request, url_for, jsonify, render_template

app = Quart(__name__)
db = None

@app.route('/')
async def index():
    return await render_template('map.html')

@app.route('/get_map_entries')
async def get_map_entries():
    map_entries = list(db.mapentries.find({}, {'_id': False}))
    return jsonify(map_entries)

if __name__ == "__main__":
    client = MongoClient()
    db = client.instagram

    app.run('localhost', port=5000, debug=True)
