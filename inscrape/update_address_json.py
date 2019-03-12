import json
from pymongo import MongoClient

def main():
    client = MongoClient()
    db = client.instagram

    # Ensure that all address_json of location documents are dicts
    all_locations = db.locations.find({})
    n_locs = db.locations.count_documents({})
    n_loc_updated = 0
    for loc in all_locations:
        if isinstance(loc['address_json'], str):
            address_json = json.loads(loc['address_json'])
            loc['address_json'] = address_json
            db.locations.replace_one({'_id': loc['_id']}, loc)
            n_loc_updated += 1

    print("Updated %d out of %d location documents" % (n_loc_updated, n_locs))

    # Ensure that all location.address_json members of posts documents are dicts
    all_posts_with_location = db.posts.find({'location': {'$ne': None}})
    n_posts = db.posts.count_documents({'location': {'$ne': None}})
    n_post_updated = 0
    for post in all_posts_with_location:
        if 'address_json' in post['location']:
            if isinstance(post['location']['address_json'], str):
                address_json = json.loads(post['location']['address_json'])
                post['location']['address_json'] = address_json
                db.posts.replace_one({'_id': post['_id']}, post)
                n_post_updated += 1

    print("Updated %d out of %d posts documents that have a location object" % (n_post_updated, n_posts))

if __name__ == '__main__':
    main()
