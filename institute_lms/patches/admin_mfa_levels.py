"""Keep SMS MFA on delegated Admins, remove it from full Administrators."""
def execute():
    from institute_lms.admin_mfa import sync_all
    sync_all()
