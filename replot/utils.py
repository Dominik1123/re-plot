from collections.abc import Set
import operator


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
