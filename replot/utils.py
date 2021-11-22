from collections.abc import Set
from functools import reduce
import operator


class DynamicSet(Set):
    @property
    def data(self):
        raise NotImplementedError

    def __contains__(self, value):
        return value in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    @classmethod
    def _from_iterable(cls, iterable):
        return set(iterable)


class LazySetUnion(DynamicSet):
    def __init__(self, *sets):
        super().__init__()
        self._sets = sets

    @property
    def data(self):
        return reduce(operator.or_, self._sets)
