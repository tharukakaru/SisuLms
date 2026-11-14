"""Public signup fields: never accept privileges, verification flags or passwords here."""
import re
from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

COMMON = ('first_name','last_name','email','phone','username','country','timezone')
EXTRA = {'Student':('birth_date',),'Individual Teacher':('subject',),
         'Institute':('organization','job','backup_name','backup_email')}
OPTIONAL = ('website','qualifications','bio')


def details(data):
    if not isinstance(data,dict) or data.get('kind') not in EXTRA:
        raise ValueError('Choose Student, Individual Teacher or Institute.')
    kind=data['kind']; result={'kind':kind}
    if kind == 'Individual Teacher':
        path = data.get('teaching_path', 'individual')
        if path not in ('individual', 'institute'):
            raise ValueError('Choose independent teaching or institute teaching.')
        # An onboarding preference, never a membership or permission grant.
        result['teaching_path'] = path
    for field in (*COMMON,*EXTRA[kind],*OPTIONAL):
        value=data.get(field,'')
        if not isinstance(value,str) or len(value)>500 or any(c in value for c in '\r\n\x00'):
            raise ValueError('Invalid '+field.replace('_',' ')+'.')
        result[field]=value.strip()
    for field in (*COMMON,*EXTRA[kind]):
        if not result[field]:raise ValueError('Required: '+field.replace('_',' ')+'.')
    for field in ('email', 'backup_email'):
        if field in result:
            result[field]=result[field].lower()
            if len(result[field])>254 or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',result[field]):
                raise ValueError('Enter a valid '+field.replace('_',' ')+'.')
    if result.get('backup_email')==result['email']:raise ValueError('Use a separate recovery contact.')
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}',result['phone']):raise ValueError('Phone number must include the country code.')
    result['username']=result['username'].lower()
    if not re.fullmatch(r'[a-z][a-z0-9_]{2,29}',result['username']) or result['username'] in ('admin','administrator','owner','support','sisu','api'):
        raise ValueError('Choose another username: 3–30 lowercase letters, digits or underscores.')
    if len(result['first_name'])>60 or len(result['last_name'])>60:raise ValueError('Names must be at most 60 characters each.')
    try:ZoneInfo(result['timezone'])
    except (ZoneInfoNotFoundError,ValueError):raise ValueError('Choose a valid time zone.') from None
    if result['website'] and not result['website'].startswith('https://'):raise ValueError('Website must use https://.')
    if data.get('privacy_accepted') is not True:raise ValueError('Accept the privacy policy.')
    if kind=='Student':result['birth_date']=birth_date(result['birth_date'])
    result['privacy_accepted']=True
    return result


def birth_date(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',value):
        raise ValueError('Enter a valid date of birth.')
    try: birthday=date.fromisoformat(value)
    except ValueError:raise ValueError('Enter a valid date of birth.') from None
    if birthday>date.today():raise ValueError('Date of birth cannot be in the future.')
    return birthday.isoformat()


def password(value,confirmation,minimum=12):
    if not isinstance(value,str) or len(value)<minimum or len(value)>128:
        raise ValueError(f'Use a password between {minimum} and 128 characters.')
    if value!=confirmation:raise ValueError('Passwords do not match.')


def verified(state,now):
    return bool(state and now<state.get('expires',0) and state.get('email_verified') is True
                and state.get('phone_verified') is True and not state.get('consumed'))


def account_creation_ready(state, now):
    """Providers verify the phone on first login; students retain both checks."""
    if not state or state.get('consumed') or now >= state.get('expires', 0):
        return False
    kind = (state.get('details') or {}).get('kind')
    if kind not in EXTRA or state.get('email_verified') is not True:
        return False
    return kind != 'Student' or state.get('phone_verified') is True
