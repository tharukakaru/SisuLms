"""Navigation hints from approved registration data; never access grants."""
import json


def teaching_path(rows, user):
    for row in rows:
        try:
            details = json.loads(row.get('details') or '{}')
        except (ValueError, TypeError):
            continue
        if not isinstance(details, dict):
            continue
        if (details.get('flow') == 'public-account-v1'
                and details.get('email') == user
                and details.get('kind') == 'Individual Teacher'
                and details.get('teaching_path') in ('individual', 'institute')):
            return details['teaching_path']
    return ''


def profile_pending(rows):
    for row in rows:
        try: details=json.loads(row.get('details') or '{}')
        except (ValueError,TypeError): continue
        if isinstance(details,dict) and details.get('flow')=='public-account-v1' and details.get('onboarding_version')==2:
            return details.get('onboarding_profile_completed') is not True
    return False
