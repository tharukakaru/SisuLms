"""Explicit loopback exception for local signup; public hosts still require HTTPS."""
from urllib.parse import urlsplit

def local_signup_allowed(config, request_url):
    if config.get('il_local_student_signup_enabled') != 1 or config.get('il_control_plane'):
        return False
    try:
        configured = urlsplit(config.get('host_name') or '')
        requested = urlsplit(request_url)
        return (configured.scheme == requested.scheme == 'http'
            and configured.hostname in ('127.0.0.1', 'localhost', '::1')
            and requested.hostname == configured.hostname
            and requested.port == configured.port
            and not configured.username and not requested.username)
    except (ValueError, TypeError):
        return False

def student_kind_allowed(config, kind):
    return not config.get('il_student_signup_only') or kind == 'Student'
