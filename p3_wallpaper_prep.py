"""Pre-compensate a photo for iOS wallpaper desaturation.

Boosts saturation by the inverse of the "P3 values read as sRGB" shift
and tags the result as Display P3, so it looks oversaturated in normal
viewers but lands close to the original once set as the wallpaper.

  - sRGB / untagged input: equivalent to "assign Display P3" (no clipping)
  - Display P3 input: P3 -> sRGB matrix applied in P3 coordinates, kept as P3

Usage:
  python3 p3_wallpaper_prep.py input.jpg [--p3-icc PATH]

Output is written next to the input as <name>_ipw.jpg.
By default the Display P3 profile is read from DisplayP3.icc in the same
directory as this script; --p3-icc overrides it.

Author: Shuhao Dong
"""

import argparse
import io
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms

# Linear Display P3 -> linear sRGB (D65)
M_P3_TO_SRGB = np.array([[ 1.2249401, -0.2249404, 0.0000000],
                         [-0.0420569,  1.0420571, 0.0000000],
                         [-0.0196376, -0.0786361, 1.0982735]])
M_SRGB_TO_P3 = np.linalg.inv(M_P3_TO_SRGB)


def decode(v):  # sRGB / Display P3 share this transfer curve
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def encode(v):
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055)


def is_display_p3(icc_bytes):
    if not icc_bytes:
        return False
    desc = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc_bytes)))
    return "P3" in desc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--p3-icc", default=str(Path(__file__).resolve().parent / "DisplayP3.icc"))
    args = ap.parse_args()
    src = Path(args.input)
    args.output = str(src.with_name(f"{src.stem}_ipw.jpg"))

    im = Image.open(args.input)
    src_icc = im.info.get("icc_profile")
    src_is_p3 = is_display_p3(src_icc)

    # Display P3 profile to embed in the output
    p3_icc = src_icc if src_is_p3 else open(args.p3_icc, "rb").read()

    rgb = np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0
    lin = decode(rgb)
    if not src_is_p3:                       # sRGB/untagged -> P3 coordinates
        lin = lin @ M_SRGB_TO_P3.T
    lin = lin @ M_P3_TO_SRGB.T              # the pre-compensation boost

    clipped = np.mean(np.any((lin < 0) | (lin > 1), axis=-1)) * 100
    out = encode(np.clip(lin, 0.0, 1.0))
    Image.fromarray(np.round(out * 255).astype(np.uint8), "RGB").save(
        args.output, "JPEG", quality=97, subsampling=0, icc_profile=p3_icc)
    print(f"source: {'Display P3' if src_is_p3 else 'sRGB/untagged'}; "
          f"{clipped:.2f}% pixels clipped -> {args.output}")


if __name__ == "__main__":
    main()