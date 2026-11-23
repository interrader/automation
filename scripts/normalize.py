"""Generic outline image normalization. Usage: python scripts/normalize.py input.png output.png
Produces transparent PNG, uniform #1F1F1F visible ink, plus _preview.png on #ECECEC.
Note: this normalizes colors and background; it does not guarantee subject-only composition.
"""
from PIL import Image, ImageOps
from pathlib import Path
import sys
import numpy as np

INK=(31,31,31)
BACKGROUND=(236,236,236)

def normalize(source, destination, white_background=False, threshold=225):
    im=Image.open(source).convert('RGBA')
    a=np.array(im).astype(np.uint8)
    rgb=a[:,:,:3].astype(np.float32)
    old_alpha=a[:,:,3].astype(np.float32)/255
    # For opaque white-background inputs, map grayscale darkness to transparency.
    # For already transparent images, preserve existing alpha and do not interpret RGB.
    has_alpha=(a[:,:,3].min()<250)
    if has_alpha:
        alpha=old_alpha
    elif white_background:
        luma=(.2126*rgb[:,:,0]+.7152*rgb[:,:,1]+.0722*rgb[:,:,2])
        alpha=np.clip((255-luma)/(255-threshold),0,1)
    else:
        raise ValueError('Opaque input: specify --white-background only for a truly plain white backdrop')
    out=np.zeros_like(a)
    out[:,:,:3]=INK
    out[:,:,3]=np.rint(alpha*255).astype(np.uint8)
    Image.fromarray(out,'RGBA').save(destination)
    preview=Image.new('RGBA',im.size,(*BACKGROUND,255))
    preview.alpha_composite(Image.fromarray(out,'RGBA'))
    preview.convert('RGB').save(str(Path(destination).with_name(Path(destination).stem+'_preview.png')))
    return {'size':im.size,'alpha_min':int(out[:,:,3].min()),'alpha_max':int(out[:,:,3].max()),'visible_pixels':int((out[:,:,3]>0).sum()),'has_transparency':bool((out[:,:,3]<255).any())}

if __name__=='__main__':
    args=sys.argv[1:]
    if len(args)<2:
        raise SystemExit('Usage: python scripts/normalize.py input.png output.png [--white-background]')
    print(normalize(args[0],args[1], '--white-background' in args))
