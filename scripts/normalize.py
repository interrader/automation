"""Conservative outline normalization: transparent PNG and #1F1F1F ink.

Only transparent or nearly uniform light backdrops are supported. A complex
background is rejected rather than silently damaging the illustration.
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

INK = (31, 31, 31)
BACKGROUND = (236, 236, 236)


def normalize(source, destination, white_background=False, threshold=225):
    with Image.open(source) as original:
        im = original.convert('RGBA')
    a = np.asarray(im, dtype=np.uint8)
    rgb = a[:, :, :3].astype(np.float32)
    source_alpha = a[:, :, 3].astype(np.float32) / 255.0
    h, w = source_alpha.shape

    if source_alpha.min() < 0.98:
        # Preserve genuine transparency, but do not claim the image is subject-only.
        alpha = source_alpha
        method = 'preserved_existing_alpha'
    else:
        # Sample the full perimeter, not just the four corner pixels.
        border = np.concatenate((rgb[0], rgb[-1], rgb[1:-1, 0], rgb[1:-1, -1]))
        bg = np.median(border, axis=0)
        distances = np.max(np.abs(border - bg), axis=1)
        if np.mean(distances <= 18) < 0.94:
            raise ValueError('Complex/nonuniform border: background removal requires review')
        if float(bg.min()) < 180:
            raise ValueError('Background is not light enough for safe dark-ink extraction')
        # Distance from estimated background; soft edges retain antialiasing.
        difference = np.max(np.abs(rgb - bg), axis=2)
        background_candidate = difference <= 24
        seeds = np.zeros((h, w), dtype=bool)
        seeds[0, :] = background_candidate[0, :]
        seeds[-1, :] = background_candidate[-1, :]
        seeds[:, 0] = background_candidate[:, 0]
        seeds[:, -1] = background_candidate[:, -1]
        exterior = ndimage.binary_propagation(seeds, mask=background_candidate)
        # Connected background only: do not delete enclosed white parts of the subject.
        alpha = np.ones((h, w), dtype=np.float32)
        alpha[exterior] = 0.0
        # Subtle antialiasing immediately inside the background boundary.
        edge = ndimage.binary_dilation(exterior, iterations=1) & ~exterior
        alpha[edge] = np.clip(difference[edge] / 65.0, 0.0, 1.0)
        # Safety: refuse a result where most pixels become opaque or none are visible.
        coverage = float(np.mean(alpha > 0.05))
        if coverage > 0.70 or coverage < 0.002:
            raise ValueError(f'Unsafe foreground coverage ({coverage:.1%}); manual review required')
        method = 'border_connected_light_background'

    out = np.zeros_like(a)
    out[:, :, :3] = INK
    out[:, :, 3] = np.rint(alpha * 255).astype(np.uint8)
    if not np.any(out[:, :, 3] == 0) or not np.any(out[:, :, 3] > 0):
        raise ValueError('Output is not a usable transparent illustration')
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, 'RGBA').save(dest)
    preview = Image.new('RGBA', im.size, (*BACKGROUND, 255))
    preview.alpha_composite(Image.fromarray(out, 'RGBA'))
    preview.convert('RGB').save(dest.with_name(dest.stem + '_preview.png'))
    return {'size': [w, h], 'method': method,
            'visible_pixels': int(np.count_nonzero(out[:, :, 3])),
            'has_transparency': True, 'quality_status': 'needs_visual_review'}


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit('Usage: python scripts/normalize.py input.png output.png')
    print(normalize(sys.argv[1], sys.argv[2]))
