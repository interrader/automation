"""Download a known-host PNG and conservatively normalize its outline."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
from PIL import Image
from normalize import normalize

MAX_BYTES = 20_000_000


def validate_url(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'f002.backblazeb2.com':
        raise ValueError('Only known Creatomate HTTPS output host is allowed')
    if not p.path.startswith('/file/creatomate-') or not p.path.endswith('.png'):
        raise ValueError('Expected a Creatomate-hosted PNG URL')
    if p.username or p.password or p.port or p.query or p.fragment:
        raise ValueError('Unexpected URL components')
    return url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    validate_url(args.url)
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', args.name):
        raise ValueError('Name must contain only letters, digits, _ or -')
    dest = Path('assets')
    dest.mkdir(exist_ok=True)
    original = dest / (args.name + '_source.png')
    with requests.get(args.url, stream=True, timeout=45, allow_redirects=False) as response:
        response.raise_for_status()
        size = 0
        with original.open('wb') as target:
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('Image too large')
                target.write(chunk)
    with Image.open(original) as im:
        im.verify()
    output = dest / (args.name + '.png')
    info = normalize(original, output)
    metadata = {'name': args.name, 'source_url': args.url,
                'output': str(output), 'quality_status': 'needs_visual_review',
                'technical_checks': info}
    (dest / (args.name + '.json')).write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata))


if __name__ == '__main__':
    main()
