# iPhone Wallpaper P3 Pre-compensation

A small Python tool that prepares photos for use as iPhone wallpapers, so they
don't lose saturation when iOS sets them on the Home Screen.

## The problem

Many users notice that a photo looks less saturated as a wallpaper than it does
in the Photos app. Brightness and contrast are unchanged, but colours look
washed out. The shift only appears after the wallpaper is set,
never in the preview.

A widely shared community explanation is that iOS reads the wallpaper's pixel
values as sRGB and then converts them into the display's Display P3 space.
For a photo that is already Display P3, this extra conversion shrinks its
colours towards the smaller sRGB gamut. Because iOS does this whatever profile
the file carries, simply exporting the photo as sRGB does not help.

> **Note:** this explanation is not documented by Apple. The tool is built on
> it, and results may vary between iOS versions.

## What the tool does

It applies the inverse of that desaturation in advance, so the two cancel out:

| Input photo | Processing | Output |
|---|---|---|
| sRGB or no profile | Keeps the pixel values and labels them Display P3 (the "Assign Profile → Display P3" step in Photoshop) | Display P3 JPEG |
| Display P3 | Applies the P3 → sRGB matrix to the values in P3 coordinates, a saturation boost of about 18% | Display P3 JPEG |

The output **looks oversaturated** in Photos, Preview and on other screens.
That is expected. Once it is set as a wallpaper, iOS desaturates it back to
the original look.

## Requirements

- Python 3.8+
- [NumPy](https://numpy.org/) and [Pillow](https://python-pillow.org/)

```bash
pip install numpy pillow
```

## Usage

```bash
python3 p3_wallpaper_prep.py photo.jpg
```

This writes `photo_ipw.jpg` next to the input.

By default the script uses `DisplayP3.icc` in its own folder. To use a
different Display P3 profile:

```bash
python3 p3_wallpaper_prep.py photo.jpg --p3-icc /path/to/DisplayP3.icc
```

Always keep the original. The prepared file is only for wallpaper use.

## Files

| File | Purpose |
|---|---|
| `p3_wallpaper_prep.py` | The tool |
| `DisplayP3.icc` | Display P3 ICC v4 profile, embedded into outputs |

`DisplayP3.icc` is generated from the standard Display P3 definition (DCI-P3
primaries, D65 white point, sRGB transfer curve, Bradford adaptation to D50).
It is not Apple's profile, but it has identical colourant values and produces
pixel-identical conversions. 

## License

[MIT](LICENSE)
