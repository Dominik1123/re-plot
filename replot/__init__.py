from .dependencies import monitor
from . import patch


__all__ = []


def __getattr__(name: str):
    if name == 'nowarn':
        patch.WARN = False
        return None
    else:
        return globals()[name]
