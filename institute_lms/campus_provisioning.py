"""Internal scope for reviewed institute provisioning; not a public endpoint.

Callers must authorize the operator and validate the requested workspace first.
The scope never grants access to the resulting institute.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_institute = ContextVar('sisu_institute_provisioning', default=None)


@contextmanager
def institute_insert(doc):
    token = _institute.set((doc, doc.code))
    try:
        yield
    finally:
        _institute.reset(token)


def allows(doc):
    value = _institute.get()
    return bool(value and value[0] is doc and value[1] == doc.code and doc.is_new())
