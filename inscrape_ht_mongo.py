"""
This program uses the explore API of instagram to discover posts tagged with a
specific hash tag and stores the posts in a MonogDB running locally.
"""
import asyncio
import aiohttp
import re

import pymongo
from pymongo import MongoClient


import argparse

client = None
db = None

async def explore_hashtag(hashtag, end_cursor, num_pages, skip_pages, sleep_time=1):
    if num_pages == 0:
        await asyncio.sleep(10) # wait 10 seconds for all remaining tasks to finish

        # Assume all tasks have had a chance to finish.
        print("num_pages reached 0. Exiting")
        loop.stop()
        client.close()

        return # stop crawling when N reaches 0

    print(f"explore_hashtag({hashtag}, {end_cursor}, {num_pages}, {skip_pages})")

    url = f"https://www.instagram.com/explore/tags/{hashtag}/"
    params = {'__a': '1'}
    if end_cursor is not None:
        params['max_id'] = end_cursor

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            print(f'Fetched {resp.url}, response status = {resp.status}')
            data = await resp.json()

    skip_page = True if skip_pages > 0 else False
    print(skip_page)

    if not skip_page:
        media_edges = data['graphql']['hashtag']['edge_hashtag_to_media']['edges']
        asyncio.create_task(parse_edges(media_edges, hashtag))

        top_posts_edges = data['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges']
        asyncio.create_task(parse_edges(top_posts_edges, hashtag))
    else:
        print(f'Skipping this page ({skip_pages})')

    has_next_page = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['has_next_page']
    if has_next_page:
        end_cursor = data['graphql']['hashtag']['edge_hashtag_to_media']['page_info']['end_cursor'] if has_next_page else None

        if skip_page:
            asyncio.create_task(explore_hashtag(hashtag, end_cursor, num_pages - 1, skip_pages - 1, sleep_time))
        else:
            await asyncio.sleep(sleep_time)
            asyncio.create_task(explore_hashtag(hashtag, end_cursor, num_pages - 1, skip_pages, sleep_time))

async def parse_edges(edges_json, hashtag):
    #i = 0
    for edge in edges_json:
        # if i == 3:
        #      break
        # i+=1

        node_json = edge['node']
        shortcode = node_json['shortcode']

        if not db.posts.find_one({'id': node_json['id']}):
            task = asyncio.create_task(get_post(shortcode, node_json, hashtag))
        else:
            print(f"Post {node_json['id']} allready in database")

async def get_post(shortcode, node_json, hashtag):
    url = f"https://www.instagram.com/p/{shortcode}/"
    params = {'__a': '1'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            print(f'Fetched {resp.url}, response status = {resp.status}')
            post_json = await resp.json()

    post = post_json['graphql']['shortcode_media']
    id = post['id']
    shortcode = post['shortcode']

    if not db.posts.find_one({'id': id}):
        post['explore_hashtag'] = hashtag # add the hashtag by which we found this post

        hashtags = get_hashtags_from_post(post)
        post['hashtags'] = hashtags

        mongodb_post_id = db.posts.insert_one(post).inserted_id
        print("Inserted post\tid = {}\tshortcode = {}\tmongoDB_id = {}".format(id, shortcode, mongodb_post_id))
    else:
        print(f"Post {id} allready in database")

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
    parser = argparse.ArgumentParser(description='Crawl an instagram hashtag and store in MongoDB.')
    parser.add_argument('-np', '--num_pages', type=int, help='Number of pages to crawl', default = 10)
    parser.add_argument('-ns', '--num_skip_pages', type=int, help='Number of pages to skip before starting to crawl', default = 0)
    parser.add_argument('-ht', '--hashtag', help='Hashtag to crawl, without # sign.', default='bicycletouring')
    parser.add_argument('-sc', '--start_cursor', help='cursor of where to start crawling.', default=None)
    parser.add_argument('-s', '--sleep_time', type=int, help='Time to wait between subsequent requests to explore/tags (in s).', default=1)
    args = parser.parse_args()

    num_pages = args.num_pages
    skip_pages = args.num_skip_pages
    instagram_hashtag = args.hashtag
    start_cursor = args.start_cursor
    sleep_time = args.sleep_time

    client = MongoClient()
    db = client.instagram

    # create index over id and short code:
    _ = db.posts.create_index([('id', pymongo.ASCENDING)], unique=True)
    _ = db.posts.create_index([('shortcode', pymongo.ASCENDING)], unique=True)

    import signal, sys
    def signal_handler(signal, frame):
        loop.stop()
        client.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(explore_hashtag(instagram_hashtag, start_cursor, num_pages, skip_pages, sleep_time), loop=loop)
    loop.run_forever()
