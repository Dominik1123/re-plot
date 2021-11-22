import os
from subprocess import run
import sys

import matplotlib


metadata_providers = []


def register_metadata_provider(obj):
    metadata_providers.append(obj)
    return obj


def compute_metadata():
    return {p.__name__: p() for p in metadata_providers}


# === Providers ===

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
