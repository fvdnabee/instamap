from pymongo import MongoClient

if __name__ == '__main__':
    client = MongoClient()
    db = client.instagram

    known_location_ids = db.locations.distinct('id') # this takes a while
    posts_with_known_loc = db.posts.find({"location.id": {"$in": known_location_ids}})

    db.mapentries.remove({})

    for post in posts_with_known_loc:
        # print(post)
        loc = db.locations.find_one({'id': post['location']['id']})

        mapentry = {}
        mapentry['shortcode'] = post['shortcode']
        mapentry['lat'] = loc['lat']
        mapentry['lng'] = loc['lng']
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
        mapentry['full_name'] = post['owner']['full_name']
        mapentry['likes'] = post['edge_media_preview_like']['count']

        print(mapentry)
        db.mapentries.insert_one(mapentry)
