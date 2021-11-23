import builtins
import json
from pathlib import Path
from typing import Union
import warnings

from matplotlib.figure import Figure
from PIL import Image, ExifTags

from .dependencies import compute_missing_dependencies, monitor
from .metadata import compute_metadata


EXIF_TAGS_BY_NAME = {name: number for number, name in ExifTags.TAGS.items()}

WARN = True

builtins.open = monitor(builtins.open)
try:
    import pandas
except ImportError:
    pass
else:
    pandas.read_csv = monitor(pandas.read_csv)
try:
    import numpy
except ImportError:
    pass
else:
    numpy.load = monitor(numpy.load)
    numpy.loadtxt = monitor(numpy.loadtxt)


_original_savefig = Figure.savefig


def savefig(self, filename: Union[str, Path], *args, **kwargs):
    """Re-plot's wrapper around the original Figure.savefig."""
    missing = compute_missing_dependencies()
    if missing:
        if WARN:
            sep = '\n* '
            list_of_files = sep.join(sorted(f'{p!s}' for p in missing))
            warnings.warn(f'The following files must be added to the respository:\n{sep}{list_of_files}\n')
        return None
    result = _original_savefig(self, filename, *args, **kwargs)
    img = Image.open(filename)
    exif = img.getexif()
    exif[EXIF_TAGS_BY_NAME['UserComment']] = json.dumps(compute_metadata())
    img.save(filename, exif=exif)
    return result


Figure.savefig = savefig
