"""
This script check the google sheet for new post entry
"""

import datetime
import json
import time
import html

import gspread
import requests
import redis
import praw
from oauth2client.service_account import ServiceAccountCredentials

def agent_headers():
    agent_name = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
    return {'User-Agent': agent_name,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8','Accept-Language':'en-US,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch, br'}

redis_host = "localhost"
redis_port = 6379
redis_password = ""

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('Document Editing-2a48c498b2fe.json', scope)
client = gspread.authorize(creds)

sheet = client.open("Reddit operating sheet request").sheet1
row_length = sheet.row_count
from_to = row_length - 6
for i in range(from_to, row_length + 1):
    values_list = sheet.row_values(i)
    try:
        if len(values_list[6]) == 0:
            pass
        else:
            if len(values_list[1]) > 1:
                pass
            else:
                post = requests.get(f"{values_list[6]}.json", headers=agent_headers())
                to_json = json.loads(post.text)

                subreddit_name = to_json[0]["data"]["children"][0]["data"]["subreddit"]
                subreddit_subscribers = to_json[0]["data"]["children"][0]["data"]["subreddit_subscribers"]
                upvotes = to_json[0]["data"]["children"][0]["data"]["score"]
                title = html.unescape(to_json[0]["data"]["children"][0]["data"]["title"])
                publish_time = datetime.datetime.fromtimestamp(to_json[0]["data"]["children"][0]["data"]["created_utc"]).strftime('%d.%m.%Y')
                try:
                    post_type = to_json[0]["data"]["children"][0]["data"]["post_hint"]
                    if post_type == "link":
                        post_type = "Link"
                        link_url = to_json[0]["data"]["children"][0]["data"]["url"]

                except:
                    url = to_json[0]["data"]["children"][0]["data"]["url"]
                    if "https://www.reddit.com" in url or "https://i.redd.it" in url:
                        post_type = "Text"
                    else:
                        post_type = "Link"
                        link_url = url
                    
                user_name = str(to_json[0]["data"]["children"][0]["data"]["author"])
                is_hidden = "Okay"
                if to_json[0]["data"]["children"][0]["data"]["selftext"] == "[deleted]":
                    is_hidden = "Deleted"
                # Update the new row with data from reddit
                domain = f"https://www.reddit.com/r/{subreddit_name}"
                sheet.update_cell(i, 2, f'=HYPERLINK("{domain}";"{subreddit_name}")')
                sheet.update_cell(i, 3, f"{subreddit_subscribers}")
                sheet.update_cell(i, 4, "-------")
                sheet.update_cell(i, 5, "-------")
                sheet.update_cell(i, 6, f"{title}")
                sheet.update_cell(i, 8, f"{publish_time}")
                sheet.update_cell(i, 9, f"{post_type}")
                if post_type == "Link":
                    sheet.update_cell(i, 10, f"{link_url}")
                sheet.update_cell(i, 11, f"{user_name}")
                sheet.update_cell(i, 12, "-------")
                sheet.update_cell(i, 13, "-------")
                # save the new row redis
                key = "Post"f"{i}"
                now = time.time()
                post_time = to_json[0]["data"]["children"][0]["data"]["created_utc"]
                data = {"key": [i, now, f"{values_list[6]}", post_time]}
                js = json.dumps(data)
                r.set(key, js)
    except:
        pass
