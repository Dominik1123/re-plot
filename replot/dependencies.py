from fnmatch import fnmatch
from functools import wraps
import os
from pathlib import Path
import sys
from typing import Callable, Set, Union

from git import Repo

from .utils import DynamicSet, LazySetUnion


REPO = Repo(
    getattr(sys.modules['__main__'], '__file__', os.getcwd()),
    search_parent_directories=True,
)
REPO_DIR = Path(REPO.working_tree_dir)


class CustomModuleDependencies(DynamicSet):
    """Set of all custom modules that have been imported by the program.

    This excludes modules from standard library or third party (site) packages.
    If a distribution is installed in editable mode (`pip install -e ...`), then
    it will be identified as a custom module. To prevent this, the corresponding
    package name can be added to `CustomModuleDependencies.ignore_packages`.
    """

    ignore_packages = {'replot'}  # replot could be installed in editable mode

    @property
    def data(self):
        files = (
            mod.__file__
            for name, mod in sys.modules.items()
            if name not in ('__main__', '__mp_main__')
                and getattr(mod, '__file__', None) is not None  # __file__ might be None, so we can't use `hasattr`
        )
        return {
            Path(f)
            for f in files
            if os.path.join('lib', 'python') not in f
                and all(f'{os.path.sep}{x}{os.path.sep}' not in f for x in self.ignore_packages)
        }


class PathPattern:
    def __init__(self, pattern: str):
        self.pattern = pattern

    def __str__(self):
        return self.pattern


file_dependencies = set()
if hasattr(sys.modules['__main__'], '__file__'):
    file_dependencies.add(Path(sys.modules['__main__'].__file__).resolve())
dependencies = LazySetUnion(file_dependencies, CustomModuleDependencies())

IGNORE_PATHS: Set[Path] = {Path(os.devnull), Path('/proc/stat')}
IGNORE_RESOURCES: Set[Path] = {
    Path('site-packages') / 'matplotlib' / 'mpl-data' / 'fonts',
    PathPattern('*.dist-info/namespace_packages.txt'),
    PathPattern('*.egg-info/namespace_packages.txt'),
    PathPattern('*.egg-info/PKG-INFO'),
}


def _path_match(path: Path, other: Union[Path, PathPattern]):
    if isinstance(other, Path):
        return _path_contains(path, other)
    elif isinstance(other, PathPattern):
        return fnmatch(path, str(other))
    else:
        raise TypeError(other)


def _path_contains(path: Path, subpath: Path):
    p_parts = path.resolve().parts
    s_parts = subpath.parts
    for i in range(len(p_parts)-len(s_parts)):
        if p_parts[i:i+len(s_parts)] == s_parts:
            return True
    return False


def add_file_dependency(file: Path):
    if not isinstance(file, Path):
        raise TypeError('File path must be given as Path instance')
    if file in IGNORE_PATHS or any(_path_match(file, p) for p in IGNORE_RESOURCES):
        return
    file_dependencies.add(file)


def monitor(func: Callable) -> Callable:
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
    def wrapper(filename: Union[str, Path], *args, **kwargs):
        add_file_dependency(Path(filename).resolve())
        return func(filename, *args, **kwargs)

    return wrapper


def compute_missing_dependencies() -> Set[Path]:
    """Compute which file dependencies are not saved in the repository.

    This considers those files which are located outside of the repository,
    as well as any untracked, modified, new or ignored file.
    """

    def _join_paths_with_repo_dir(paths):
        return set(REPO_DIR.joinpath(p) for p in paths)

    ignored = _join_paths_with_repo_dir(REPO.ignored())
    untracked = _join_paths_with_repo_dir(REPO.untracked_files)
    changed = _join_paths_with_repo_dir(p for x in REPO.index.diff(None) for p in (x.a_path, x.b_path)) - {None}
    new = _join_paths_with_repo_dir(x.a_path for x in REPO.index.diff(REPO.head.commit))

    not_inside_repo = {p for p in dependencies if REPO_DIR not in p.parents}
    
    return not_inside_repo | ((ignored | untracked | changed | new) & dependencies)
