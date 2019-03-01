"""
This program uses the explore API of instagram to discover posts tagged with a
specific hash tag and stores the posts in a MonogDB running locally.
"""
import config
import json
import re

import pymongo
from pymongo import MongoClient


import argparse

client = None
db = None
posts_collection = None


def get_hashtags_from_post(post):
    " Get hashtags from caption and first comment and return as list "
    hashtags = []
    re_hashtag = re.compile("(?:^|\s)[＃#]{1}(\w+)", re.UNICODE)

    has_caption = len(post['edge_media_to_caption']['edges']) > 0
    if has_caption:
        caption = post['edge_media_to_caption']['edges'][0]['node']['text']
        r = re_hashtag.findall(caption)
        hashtags.extend(r)

    has_comments = post['edge_media_to_comment']['count'] > 0 and len(post['edge_media_to_comment']['edges']) > 0
    # Note: sometimes count will be greather than zero, but edges might still be empty
    if has_comments:
        first_comment = post['edge_media_to_comment']['edges'][0]['node']['text']
        r = re_hashtag.findall(first_comment)
        hashtags.extend(r)

    return hashtags

if __name__ == '__main__':
    client = MongoClient()
    db = client.instagram

    # create index over id and short code:
    _ = db[config.posts_collection].create_index([('id', pymongo.ASCENDING)], unique=True)
    _ = db[config.posts_collection].create_index([('shortcode', pymongo.ASCENDING)], unique=True)

    n_inserted = 0
    with open('user.json') as f:
        data = json.load(f)

        for item in data:
            post = item['node']
            id = post['id']
            shortcode = post['shortcode']

            if not posts_collection.find_one({'id': id}):
                hashtags = get_hashtags_from_post(post)
                post['hashtags'] = hashtags

                mongodb_post_id = posts_collection.insert_one(post).inserted_id
                print("Inserted post\tid = {}\tshortcode = {}\tmongoDB_id = {}".format(id, shortcode, mongodb_post_id))
                n_inserted += 1
            else:
                print(f"Post {id} allready in database")

    print(f'Inserted {n_inserted} posts into MonogDB')

