from pymongo import MongoClient
import csv

def main():
    client = MongoClient()
    db = client.instagram

    # Get some stats from the DB:
    n_missing = 0
    country_codes = {}
    fil = {'location': {'$ne': None}}
    n_posts = db.posts.count_documents(fil)
    all_posts_with_location = db.posts.find(fil)

    for post in all_posts_with_location:
        address_json = None # Get from either the post or the location document

        if 'address_json' in post['location']:
            address_json = post['location']['address_json']
        else:
            loc_id = post['location']['id']
            post_loc = db.locations.find_one({'id': loc_id})
            if post_loc and 'address_json' in post_loc:
                address_json = post_loc['address_json']

        if address_json is None:
            n_missing += 1
            continue

        post_cc = address_json['country_code']
        country_codes[post_cc] = country_codes.get(post_cc, 0) + 1

    print("%d/%d" % (n_missing, n_posts))
    print(country_codes)

if __name__ == '__main__':
    main()
