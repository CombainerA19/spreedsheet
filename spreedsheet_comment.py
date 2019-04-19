"""
This script check the spreedsheet for new post entry
which will be process as comment
"""

import datetime
import json
import time
import html

import gspread
import requests
import bs4
import redis
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
creds = ServiceAccountCredentials.from_json_keyfile_name('Document Editing 2-5e9a63406610.json', scope)
client = gspread.authorize(creds)

try:
    sheet = client.open("Reddit operating sheet request").sheet1
    row_length = sheet.row_count
    from_to = row_length - 4
    for i in range(from_to, row_length + 1):
        values_list = sheet.row_values(i)
        try:
            if len(values_list[13]) != 0:
                try:
                    if len(values_list[14]) > 1:
                        pass
                except:
                    url = values_list[13]
                    if "?" in values_list[13]:
                        link_split = values_list[13].split("?")
                        url = link_split[0]
                    post = requests.get(f"{url}.json", headers=agent_headers())
                    to_json = json.loads(post.text)

                    title = to_json[0]["data"]["children"][0]["data"]["title"]
                    comment = to_json[1]["data"]["children"][0]["data"]["body"]
                    upvotes = to_json[1]["data"]["children"][0]["data"]["score"]
                    publish_time = datetime.datetime.fromtimestamp(to_json[1]["data"]["children"][0]["data"]["created_utc"]).strftime('%d.%m.%Y')
                    user_name = to_json[1]["data"]["children"][0]["data"]["author"]
                    post_type = to_json[1]["data"]["children"][0]["data"]["body_html"]
                    short_html = html.unescape(f"{post_type}")
                    soup = bs4.BeautifulSoup(short_html, features="html.parser")
                    try:
                        link = soup.select("a")[0].get("href")
                        if "http" in link:
                            link = soup.select("a")[0].get("href")
                        else:
                            link = "Text"
                    except:
                        link = "Text"
                    is_hidden = "Hidden"
                    if to_json[1]["data"]["children"][0]["data"]["banned_by"] == None and to_json[1]["data"]["children"][0]["data"]["removal_reason"] == None:
                        is_hidden = "Okay"
                    else:
                        is_hidden = "Deleted"
                    # Update the new row with data from reddit
                    sheet.update_cell(i, 15, f'=HYPERLINK("{values_list[13]}";"{title}")')
                    sheet.update_cell(i, 16, f"{comment}")
                    sheet.update_cell(i, 17, f"{upvotes}")
                    sheet.update_cell(i, 18, f"{publish_time}")
                    sheet.update_cell(i, 19, f"{user_name}")
                    sheet.update_cell(i, 20, f"{link}")
                    sheet.update_cell(i, 21, f"{is_hidden}")
                    sheet.update_cell(i, 22, f"{is_hidden}")
        except Exception as e:
            print(e)
            pass
except:
    pass