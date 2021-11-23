from functools import partial
import json
import os
from pathlib import Path
from subprocess import check_output
import sys
from typing import Any, Callable, Dict

import matplotlib

from .dependencies import REPO, REPO_DIR


check_output = partial(check_output, text=True)

metadata_providers = []


def register_metadata_provider(obj: Callable) -> Callable:
    """Decorator for registering a function as a metadata provider.

    The function must assume no arguments and return a single JSON
    serializable object.
    """
    metadata_providers.append(obj)
    return obj


def compute_metadata() -> Dict[str, Any]:
    """Compute all metadata from the registered providers."""
    return {p.__name__: p() for p in metadata_providers}


# === Providers ===

@register_metadata_provider
def current_working_directory():
    return str(Path.cwd().resolve())


@register_metadata_provider
def script_path():
    return str(Path(sys.modules['__main__'].__file__).resolve().relative_to(REPO_DIR))


@register_metadata_provider
def command_line_arguments():
    return sys.argv


@register_metadata_provider
def environment_variables():
    return {
        k: v for k, v in os.environ.items()
        if k.startswith('PYTHON')
            or k.startswith('CONDA_')
            or k in ('LD_LIBRARY_PATH', 'MPLBACKEND', 'MPLCONFIGDIR', 'MPLSETUPCFG')
    }


@register_metadata_provider
def package_versions():
    if os.environ.get('CONDA_PREFIX') is not None:
        return dict(
            style='conda',
            packages=json.loads(check_output(['conda', 'list', '--json'])),
        )
    else:
        return dict(
            style='pip',
            packages=check_output([sys.executable, '-m', 'pip', 'freeze']).split('\n'),
        )


@register_metadata_provider
def matplotlib_rcparams():
    d = dict(matplotlib.rcParams)
    del d['axes.prop_cycle']  # instance of `cycler.Cycler`; not JSON serializable
    return d


@register_metadata_provider
def commit_hash():
    return REPO.commit().hexsha
