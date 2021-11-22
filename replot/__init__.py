from .dependencies import monitor


__all__ = []


def __getattr__(name: str):
    global WARN

    if name == 'nowarn':
        WARN = False
        return None
    else:
        return globals()[name]


WARN = True
