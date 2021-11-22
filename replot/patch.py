import builtins
import json
import warnings

from matplotlib.figure import Figure
from Pillow import Image

from .dependencies import monitor


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
    missing = compute_missing_dependencies()
    if missing:
        if WARN:
            list_of_files = '\n* '.join(sorted(str(p.relative_to(REPO_DIR)) for p in missing))
            warnings.warn(f'The following files must be added to the respository:\n\n{missing}')
        return None
    result = _original_savefig(filename, *args, **kwargs)
    img = Image(filename)
    img.Exif['UserComment'] = json.dumps(compute_metadata())
    img.save(filename)
    return result


Figure.savefig = savefig
