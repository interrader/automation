"""Download a Creatomate image, normalize, and write an asset plus metadata.
Dependencies: requests, pillow, numpy. Public HTTPS URL input only.
"""
import argparse, json, os, re, socket, ipaddress
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image
from normalize import normalize

MAX_BYTES = 20_000_000

def validate_url(url):
    p=urlparse(url)
    if p.scheme != 'https' or p.hostname not in {'f002.backblazeb2.com'}:
        raise ValueError('Only known Creatomate HTTPS output host is allowed')
    if not p.path.startswith('/file/creatomate-') or not p.path.endswith('.png'):
        raise ValueError('Expected a Creatomate-hosted PNG URL')
    return url

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--url',required=True)
    ap.add_argument('--name',required=True)
    args=ap.parse_args()
    validate_url(args.url)
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',args.name):
        raise ValueError('Name must contain only letters, digits, _ or -')
    dest=Path('assets')
    dest.mkdir(exist_ok=True)
    original=dest/(args.name+'_source.png')
    # No redirects: prevent untrusted host redirects.
    with requests.get(args.url,stream=True,timeout=45,allow_redirects=False) as r:
        r.raise_for_status()
        if r.status_code in (301,302,303,307,308):
            raise ValueError('Redirects are not allowed')
        size=0
        with original.open('wb') as f:
            for chunk in r.iter_content(65536):
                size+=len(chunk)
                if size>MAX_BYTES:
                    raise ValueError('Image too large')
                f.write(chunk)
    with Image.open(original) as im:
        im.verify()
    # Fail closed if background is not close to white or already transparent.
    with Image.open(original) as im:
        rgba=im.convert('RGBA')
        corners=[rgba.getpixel((x,y)) for x,y in [(0,0),(rgba.width-1,0),(0,rgba.height-1),(rgba.width-1,rgba.height-1)]]
        transparent=any(p[3]<250 for p in corners)
        white=all(min(p[:3])>=245 and max(p[:3])-min(p[:3])<=5 for p in corners)
        if not transparent and not white:
            raise ValueError('Background not white/transparent at all corners; refusing automatic cutout')
    output=dest/(args.name+'.png')
    info=normalize(original,output,white_background=not transparent,threshold=235)
    if not info['has_transparency']:
        raise ValueError('No transparent pixels; output is not suitable')
    metadata={'name':args.name,'source_url':args.url,'output':str(output),'quality_status':'needs_visual_review','technical_checks':info}
    (dest/(args.name+'.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print(json.dumps(metadata,ensure_ascii=False))

if __name__=='__main__': main()
