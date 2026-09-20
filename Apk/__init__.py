import sys

# Python 3.14 compatibility patch for Django Template Context copy bug
if sys.version_info >= (3, 14):
    try:
        from django.template import context

        def _base_context_copy(self):
            duplicate = object.__new__(self.__class__)
            duplicate.__dict__.update(self.__dict__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        context.BaseContext.__copy__ = _base_context_copy
    except Exception:
        pass
