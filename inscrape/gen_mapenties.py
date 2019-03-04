import config
import time
from pymongo import MongoClient, GEO2D
import pymongo

if __name__ == '__main__':
    client = MongoClient()
    db = client.instagram

    # db.mapentries.delete_many({})

    known_location_ids = db.locations.distinct('id') # this takes a while
    posts_with_known_loc = db[config.posts_collection].find({"location.id": {"$in": known_location_ids}})

    db.mapentries.create_index([("loc", GEO2D)])

    t0 = time.time()
    n_mapenties = 0
    for post in posts_with_known_loc:
        # print(post)
        loc = db.locations.find_one({'id': post['location']['id']})
        if not loc: continue
        if loc['lng'] == None or loc['lat'] == None:
            continue

        mapentry = {}
        mapentry['shortcode'] = post['shortcode']
        mapentry['lng'] = loc['lng']
        mapentry['lat'] = loc['lat']
        mapentry['loc'] = [loc['lng'], loc['lat']]
        mapentry['loc_name'] = loc['name']
        mapentry['ts'] = post['taken_at_timestamp']
        mapentry['url'] = 'https://www.instagram.com/p/{}/'.format(post['shortcode'])
        mapentry['display_url'] = post['display_url']
        mapentry['dimensions'] = post['dimensions']
        mapentry['is_video'] = post['is_video']
        if mapentry['is_video'] == True:
            mapentry['video_url'] = post['video_url']
        mapentry['caption'] = ''
        if len(post['edge_media_to_caption']['edges']) > 0:
            mapentry['caption'] = post['edge_media_to_caption']['edges'][0]['node']['text']
        mapentry['username'] = post['owner']['username']
        # mapentry['full_name'] = post['owner']['full_name']
        mapentry['likes'] = post['edge_media_preview_like']['count']
        mapentry['hashtags'] = post['hashtags']

        try:
            db.mapentries.insert_one(mapentry)
        except pymongo.errors.WriteError as e:
            print("Error caught: {}".format(e))
            print("post object: {}".format(post))
            print("loc object: {}\n".format(loc))


        n_mapenties += 1
    t1 = time.time()

    print("Inserted {} mapentries in {:.3f} ms".format(n_mapenties, 1000*(t1-t0)))
