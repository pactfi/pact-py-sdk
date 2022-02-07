from typing import Union, get_args, get_origin


class _AnyMatcher:
    def __call__(self, type):
        return _TypeMatcher(type)

    def __eq__(self, other: object):
        return True


class _TypeMatcher:
    def __init__(self, type):
        self.type = type

    def __eq__(self, other: object):
        if get_origin(self.type) == Union:
            return any(isinstance(other, t) for t in get_args(self.type))
        return isinstance(other, self.type)


Any = _AnyMatcher()
