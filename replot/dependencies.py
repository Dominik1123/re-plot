from functools import wraps
import os
from pathlib import Path
import sys
from typing import Callable, Union

from git import Repo

from .utils import DynamicSet, LazySetUnion


REPO = Repo(
    getattr(sys.modules['__main__'], '__file__', os.getcwd()),
    search_parent_directories=True,
)
REPO_DIR = Path(REPO.working_tree_dir)


class CustomModuleDependencies(DynamicSet):
    ignore_packages = {'replot'}

    @property
    def data(self):
        files = (
            mod.__file__
            for name, mod in sys.modules.items()
            if name != '__main__'
                and getattr(mod, '__file__', None) is not None  # __file__ might be None, so we can't use `hasattr`
        )
        return {
            Path(f)
            for f in files
            if os.path.join('lib', 'python') not in f
                and all(f'{os.path.sep}{x}{os.path.sep}' not in f for x in self.ignore_packages)
        }


file_dependencies = set()
if hasattr(sys.modules['__main__'], '__file__'):
    file_dependencies.add(Path(sys.modules['__main__'].__file__).resolve())
dependencies = LazySetUnion(file_dependencies, CustomModuleDependencies())


def add_file_dependency(file: Path):
    file_dependencies.add(file)


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
    def wrapper(filename: Union[str, Path], *args, **kwargs):
        add_file_dependency(Path(filename).resolve())
        return func(filename, *args, **kwargs)

    return wrapper


def compute_missing_dependencies():
    def _join_paths_with_repo_dir(paths):
        return set(REPO_DIR.joinpath(p) for p in paths)

    ignored = _join_paths_with_repo_dir(REPO.ignored())
    untracked = _join_paths_with_repo_dir(REPO.untracked_files)
    changed = _join_paths_with_repo_dir(p for x in REPO.index.diff(None) for p in (x.a_path, x.b_path)) - {None}
    new = _join_paths_with_repo_dir(x.a_path for x in REPO.index.diff(REPO.head.commit))

    not_inside_repo = {p for p in dependencies if REPO_DIR not in p.parents}
    
    return not_inside_repo | ((ignored | untracked | changed | new) & dependencies)
