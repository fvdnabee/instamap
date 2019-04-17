"""
This program uses the API of instagram to retrieve location objects for the posts
from the posts collection. The location objects are stored in MongoDB.
"""
import config

import asyncio
import aiohttp
import socket

import pymongo
from pymongo import MongoClient

client = None
db = None
rate_limited = False
n_rate_limited = 0


async def process_unknown_locations(unknown_location_ids, batch_size):
    global rate_limited, n_rate_limited

    n_batches = len(unknown_location_ids)//batch_size
    for i in range(n_batches):
        if rate_limited:
            i -= 1 # Redo the last batch
            rate_limited = False

            seconds = 2**(n_rate_limited - 1) * 10
            print(f"Rate limited -> sleeping for {seconds} seconds")
            await asyncio.sleep(seconds)

        batch_ids = unknown_location_ids[i*batch_size:(i+1)*batch_size]

        asyncio.create_task(retrieve_location_batch(batch_ids))

        await asyncio.sleep(5)

    # If necessary, fetch the last batch:
    if len(unknown_location_ids) % batch_size > 0:
        batch_ids = unknown_location_ids[(n_batches + 1)*batch_size:]
        asyncio.create_task(retrieve_location_batch(batch_ids))

async def retrieve_location_batch(batch_ids):
    global rate_limited, n_rate_limited

    conn = aiohttp.TCPConnector(force_close=True, family=socket.AF_INET) # Force IPv4
    #session = ClientSession(connector=conn)
    async with aiohttp.ClientSession(connector=conn) as session:
        for id in batch_ids:
            url = f"https://www.instagram.com/explore/locations/{id}/"
            params = {'__a': '1'}
            async with session.get(url, params=params) as resp:
                if resp.status == 429:
                    if not rate_limited:
                        n_rate_limited += 1

                    print(f"Retrieved response status {resp.status}, setting rate_limited from {rate_limited} to True")
                    rate_limited = True
                else:
                    rate_limited = False
                    n_rate_limited = 0
                    print(f'Fetched {resp.url}, response status = {resp.status}')
                    loc_json = await resp.json()
                    process_loc_json(loc_json)

def process_loc_json(loc_json):
    loc = loc_json['graphql']['location']
    id = loc['id']

    # remove these two (large) items:
    loc.pop('edge_location_to_media', None)
    loc.pop('edge_location_to_top_posts', None)

    if not db.locations.find_one({'id': id}):
        mongodb_loc_id = db.locations.insert_one(loc).inserted_id
        print("Inserted location\tid = {}\tmongoDB_id = {}".format(id, mongodb_loc_id))
    else:
        print(f"Location {id} allready in database")

if __name__ == '__main__':
    client = MongoClient()
    db = client.instagram
    rate_limited = False

    # find locations that we don't know yet:
    distinct_location_ids = db[config.posts_collection].distinct('location.id') # this takes a while
    cursor_locations = db.locations.find({'id': {'$in': distinct_location_ids}})
    known_location_ids = [loc['id'] for loc in cursor_locations]
    unknown_location_ids = list(set(distinct_location_ids).symmetric_difference(set(known_location_ids)))
    print("{} locations unknown, starting to fetch them".format(len(unknown_location_ids)))

    # for every location.id in the list, send a request to instagram to
    # retrieve its details and store it in MongoDB


    import signal, sys
    def signal_handler(signal, frame):
        loop.stop()
        client.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    batch_size = 5

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(process_unknown_locations(unknown_location_ids, batch_size), loop=loop)
    loop.run_forever()
