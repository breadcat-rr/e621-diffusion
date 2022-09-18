import asyncio
import datetime as dt
import os
import re
import time
from multiprocessing import Pool
import argparse
import aiohttp
import requests
import ujson
from PIL import Image
import shutil
import logging

logging.basicConfig()
log = logging.getLogger(__name__)

headers = {
    'User-Agent': 'FurryDiffusionTest/0.1 (by TheRealCreamers)',
}

year_match = re.compile("2[0-9]{3}")

class ImageE621:
    downloaded = []
    session = None
    def __init__(self, post_id: int, url: str, tags: list) -> None:
        self.id = post_id
        self.url = url

        self.raw_tags = tags
        self.tags = " ".join([tag.replace("_", " ") for tag_type in tags.values() for tag in tag_type if year_match.match(tag) == None])

    def __repr__(self):
        return f"<ImageE621 (Id: {self.id}, Tags: {self.tags[:10]})>"

    async def save_image(self, location: str = ""):
        """ Saves image, also updates the data.json file"""
        if self.url == None:
            print("Blocked post. Failed to download")
            return False
        
        filename = f"{self.id}.{self.url.split('.')[-1]}"

        if filename in ImageE621.downloaded:
            print("Image already exists, skipping.",end="                \r")
            return False
        
        async with ImageE621.session.get(self.url) as resp:
            data = await resp.read()

        with open(f"raw/{filename}","wb") as f:
            f.write(data)

        ImageE621.downloaded.append(filename)

        with open("data.json", "a+") as f:
            f.seek(0)
            raw = "".join(f.readlines())
            if raw == "": 
                raw = "{}"

            json = ujson.loads(raw)
            if "images" not in json:
                json["images"] = []
            
            image_data = {}
            image_data["filename"] = filename
            image_data["url"] = self.url
            image_data["tags"] = self.raw_tags
        
            json["images"].append(image_data)
            f.seek(0)
            f.truncate()
            f.write(ujson.dumps(json))






async def main():
   
    s = aiohttp.ClientSession()
    downloaded = os.listdir("raw")

    with open("index", "a+") as f:
        f.seek(0)
        index = int("".join(f.readlines()))
    
    ImageE621.session = s
    ImageE621.downloaded = downloaded

    # params = {
    #     'tags': search
    # }
        
    # print("Fetching page count...")
    # r = requests.get('https://e621.net/posts', headers=headers)
    # page_count = re.search(r"""[0-9]+(?=<\/a><\/li><li class=\'arrow\'>)""", r.text)
    # if page_count == None:
    #     print("Error occured fetching page count.")
    #     return
    
    # page_count = int(page_count[0])

    # download_time_s = (page_count * 1.5) + (page_count * 75)
    # download_time_m = int((download_time_s // 60) % 60)
    # download_time_h = int((download_time_s // 3600))
    # print(f"Estimated {page_count * 75} posts found.\n")
    # print(f"Time to download all posts: {download_time_h}:{download_time_m:<02}:{download_time_s % 60:<02}")
    
    while True:
        params = {
            'tags': search,
            'page': index // 75,
        }

        if index // 75 == 750:
            print("Max limit reached. Exiting.")
            return
        
        await asyncio.sleep(0.4)

        r = requests.get('https://e621.net/posts.json', params=params, headers=headers)
        
        if r.ok:
            r = r.json()
            posts = r['posts']

            if len(posts) == 0:
                current_time = dt.datetime.now().strftime("%c")
                print(f"Fetched {len(ImageE621.downloaded)} images at {current_time}")
                exit()

            posts = [ImageE621(int(p['id']), p['file']['url'], tags=p['tags']) for p in posts]
            
            for i, p in enumerate(posts):
                call_time = time.time()

                print(f"Fetching image {index + i} on page {params['page']}",end="         \r")
                success = await p.save_image()
                print(f"Fetched image {index + i} on page {params['page']}",end="         \r")

                if success == False:
                    await asyncio.sleep(1/75)
                else:
                    await asyncio.sleep(max(1 - (time.time() - call_time), 0))

            
            with open("index", "r+") as f:
                index += len(posts)
                f.seek(0)
                f.truncate()
                f.write(str(index))
            
        elif r.status_code == 503:
            print("Rate limited; sleeping for 30 seconds...")
            await asyncio.sleep(30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fetch all images from e621 according to --search')
    parser.add_argument('--dest', help="Save location", required=False)
    parser.add_argument('--search', required=False)
    parser.add_argument('--start',type=int, required=False)

    parser.add_argument('--reset',action='store_true', required=False)
    args = parser.parse_args()
    
    if args.search != None:
        search = args.search
    else:
        search = "-animated -not_furry_focus -meme order:score rating:s score:>50"
        print(f'Search not provided, using default: "{search}"')
    
    if args.reset:
        with open("index", "w+") as f:
            f.write("0")
        with open("data.json", "w+") as f:
            f.write("{}")

        try: shutil.rmtree("txt")
        except: pass
        try: shutil.rmtree("raw")
        except: pass
        try: shutil.rmtree("img")
        except: pass
       
    if args.start:
        print(f"Setting start position to {args.start}")
        with open("index", "w+") as f:
            f.write(str(args.start))
    
    # Create necessary folders if they don't exist
    cur_folder = os.listdir()
    if "txt" not in cur_folder or "img" not in cur_folder or "raw" not in cur_folder:
        print(f"Creating img, txt and raw")
        try: os.mkdir("txt")
        except: pass

        try: os.mkdir("img")
        except: pass

        try: os.mkdir("raw")
        except: pass
    
    print()
    asyncio.run(main())
