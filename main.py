import builtins
from collections.abc import Hashable, MutableSet, Set
from functools import partial, reduce, wraps
import json
import operator
import os
from pathlib import Path
from subprocess import run
import sys
from typing import Callable, Union
import warnings

from git import Repo
import matplotlib
from matplotlib.figure import Figure
from Pillow import Image


__all__ = []


class UserSet(Set):
    def __init__(self, iterable=()):
        self.data = set(iterable)

    def __contains__(self, value):
        return value in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)


class CustomModuleDependencies(UserSet):
    @property
    def data(self):
        return {Path(x) for x in sys.modules if os.path.join('lib', 'python') not in x}
    
    @data.setter
    def data(self, value):
        pass


class LazySetUnion(UserSet):
    def __init__(self, *sets):
        super().__init__()
        self._sets = args

    @property
    def data(self):
        return reduce(operator.or_, self._sets)
    
    @data.setter
    def data(self, value):
        pass


def __getattr__(name: str):
    global WARN

    if name == 'nowarn':
        WARN = False
        return None
    else:
        return globals()[name]


WARN = True

REPO = Repo(
    getattr(sys.modules['__main__'], '__file__', os.getcwd()),
    search_parent_directories=True,
)
REPO_DIR = Path(REPO.working_tree_dir)

FILE_DEPENDENCIES = set()
DEPENDENCIES = LazySetUnion(FILE_DEPENDENCIES, CustomModuleDependencies())


def add_file_dependency(file: Path):
    FILE_DEPENDENCIES.add(file)


def monitor(func: Callable):
    """Monitor the given function for file dependencies.

    The given function `func` is expected to receive a file path
    as its first argument, either as a `str` of `pathlib.Path` object.

    Args:
        func : callable
            The function to be monitored.
            Expected signature: `func(filename, *args, **kwargs)`

    Returns:
        A wrapper around `func`.
    """
    @wraps(func)
    def wrapper(filename: Union[str, Path], /, *args, **kwargs):
        add_file_dependency(Path(filename))
        return func(filename, *args, **kwargs)

    return wrapper


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


METADATA_PROVIDERS = []


def register_metadata_provider(obj):
    METADATA_PROVIDERS.append(obj)
    return obj


def compute_metadata():
    return {p.__name__: p() for p in METADATA_PROVIDERS}


ORIGINAL_SAVEFIG = Figure.savefig


def compute_missing_dependencies():
    def _join_paths_with_repo_dir(paths):
        return set(REPO_DIR.joinpath(p) for p in paths)

    ignored = _join_paths_with_repo_dir(REPO.ignored)
    untracked = _join_paths_with_repo_dir(REPO.untracked_files)
    changed = _join_paths_with_repo_dir(p for x in REPO.index.diff(None) for p in (x.a_path, x.b_path)) - {None}
    new = _join_paths_with_repo_dir(x.a_path for x in REPO.index.diff(REPO.head.commit))

    not_inside_repo = {p for p in DEPENDENCIES if REPO_DIR not in p.parents}

    return not_inside_repo | ((ignored | untracked | changed | new) & DEPENDENCIES)


def savefig(self, filename: Union[str, Path], *args, **kwargs):
    missing = compute_missing_dependencies()
    if missing:
        if WARN:
            list_of_files = '\n* '.join(sorted(str(p.relative_to(REPO_DIR)) for p in missing))
            warnings.warn(f'The following files must be added to the respository:\n\n{missing}')
        return None
    result = ORIGINAL_SAVEFIG(filename, *args, **kwargs)
    img = Image(filename)
    img.Exif['UserComment'] = json.dumps(compute_metadata())
    img.save(filename)
    return result


Figure.savefig = savefig


# === Metadata providers ===

@register_metadata_provider
def current_working_directory():
    return os.getcwd()


@register_metadata_provider
def script_path():
    return sys.modules['__main__'].__file__


@register_metadata_provider
def command_line_arguments():
    return sys.argv


@register_metadata_provider
def environment_variables():
    return dict(os.environ)


@register_metadata_provider
def package_versions():
    if os.environ.get('CONDA_PREFIX') is not None:
        return dict(
            style='conda',
            packages=run(['conda', 'list'], check=True, text=True),
        )
    else:
        return dict(
            style='pip',
            packages=run([sys.executable, '-m', 'pip', 'freeze'], check=True, text=True),
        )


@register_metadata_provider
def matplotlib_rcparams():
    return dict(matplotlib.rcParams)


@register_metadata_provider
def commit_hash():
    return REPO.commit().hexsha
