"""Internal, request-local scope for an already-authorized membership insert.

Not an API or document flag: only the exact in-memory document is authorized.
Callers must finish their identity, verification and target checks first.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_authorized = ContextVar('sisu_membership_insert', default=None)


@contextmanager
def authorized_insert(doc):
    token = _authorized.set((doc, doc.institute, doc.user, doc.role))
    try:
        yield
    finally:
        _authorized.reset(token)


def target_for(doc):
    value = _authorized.get()
    if value and value[0] is doc and (doc.institute, doc.user, doc.role) == value[1:]:
        return value[1]
    return None
