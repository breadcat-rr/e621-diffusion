""" Resize and pad all images in raw, generate all prompts from data.json in txt"""

import multiprocessing
import os
from multiprocessing import Pool
import ujson
import re
from PIL import Image
import argparse
from functools import partial

year_match = re.compile("2[0-9]{3}")
bg = Image.new("RGB", size=(512,512), color="#ffffff")

size = (0,0)

with open("data.json", "r") as f:
    x = "".join(f.readlines())
    data = ujson.loads(x)

# def process_image(path: str):
#     try:
#         img = Image.open("raw/"+path)
#     except Image.DecompressionBombError:
#         print("Max size, fuck off aadi:", path)
#         return
#     img = img.resize((512, int((img.height / img.width) * 512))) if img.width > img.height else img.resize((int((img.width / img.height) * 512), 512))
#     img.save("processed/" + path, quality=90)

def load_resize_pad_image(path: str, size: tuple,):
    try:
        img = Image.open("raw/"+path)
    except Image.DecompressionBombError:
        return
    
    img = img.resize((size[0], int((img.height / img.width) * size[0]))) if img.width > img.height else img.resize((int((img.width / img.height) * size[1]), size[1])) 

    bg_copy = bg.copy()
    bg_copy.paste(img, box=(int((size[0]/2) - (img.width//2)), int(size[1]/2 - (img.height//2))))
    bg_copy.save("img/" + path.split(".")[0] + ".jpg", format="jpeg", quality=90)

    return img    

def extract_tags(json_data: str):
    tags: dict = json_data["tags"]
    flat_tags = ", ".join([tag.replace("_", " ") for tag_type in tags.values() for tag in tag_type if not year_match.match(tag)]) 
    with open("txt/"+json_data["filename"].split(".")[0] + ".txt", "w+", encoding="utf-8") as f:
        f.write(flat_tags)

# def main():
    # p = Pool(32)
    # for i, _ in enumerate(p.imap_unordered(extract_tags, data["images"]), 1):
    #     print('\rdone {0:%}'.format(i/len(data["images"])))
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Fetch all images from e621 according to --search')
    parser.add_argument('--size', help="Save location", required=False)
    args = parser.parse_args()

    if args.size != None:
        size = (int(args.size.split("x")[0]), int(args.size.split("x")[1]))
        print(f"Using explicit size {size[0]}x{size[1]}")
    else:
        size = (512, 512)
        print("No --size specified, using default 512x512")

    
    with open("data.json", "r") as f:
        x = "".join(f.readlines())
        data = ujson.loads(x)

    downloaded = os.listdir("raw")
    print("Initializing process pool")
    p = Pool(multiprocessing.cpu_count())

    Image.MAX_IMAGE_PIXELS = 10**100

    load_resize_pad_image_partial = partial(load_resize_pad_image, size=size)
    for i, _ in enumerate(p.imap_unordered(load_resize_pad_image_partial, downloaded), 1):
        print(f'Loading, resizing and padding images ({size[0]}x{size[1]}): {i/len(downloaded):.1%}', end="        \r")
    print()
    print(f"Finished loading and resizing. Total count: {len(downloaded)}. File loss: {len(os.listdir('raw')) - len(downloaded)}")
    print()
    
    for i, _ in enumerate(p.imap_unordered(extract_tags, data["images"]), 1):
        print(f'Generating prompts: {i/len(downloaded):.1%}', end="                   \r")
    print()
    print("Finished generating prompts.")
    p.close()
    exit()