from pymongo import MongoClient
import csv

def main():
    client = MongoClient()
    db = client.instagram

    n_lines = 0
    with open('text.csv', 'w', newline='') as csvfile:
        post_writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        all_posts_with_location = db.posts.find({'location': {'$ne': None}})
        for post in all_posts_with_location:
            post_id = post['id']

            address_json = None
            if 'address_json' in post['location']:
                address_json = post['location']['address_json']
            else:
                loc_id = post['location']['id']
                post_loc = db.locations.find_one({'id': loc_id})
                if post_loc and 'address_json' in post_loc:
                    address_json = post_loc['address_json']

            if address_json is None:
                # print("Skipping post with empty address_json")
                continue

            post_cc = address_json['country_code']
            if not post_cc: # note that there there are quite a few posts with an empty country_code
                # print("Skipping post with empty country_code")
                continue

            if not post['edge_media_to_caption']['edges']:
                print("Skipping post with missing text")
                continue
            post_text = post['edge_media_to_caption']['edges'][0]['node']['text']

            output_line = [post_id, post_cc, post_text]
            post_writer.writerow(output_line)
            n_lines += 1

    print("Written %d lines to text.csv" % n_lines)

if __name__ == '__main__':
    main()
