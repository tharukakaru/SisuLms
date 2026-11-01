"""Public signup fields: never accept privileges, verification flags or passwords here."""
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

COMMON = ('first_name','last_name','email','phone','username','country','timezone')
EXTRA = {'Student':('grade',),'Individual Teacher':('subject',),
         'Institute':('organization','job','backup_name','backup_email')}
OPTIONAL = ('website','qualifications','bio')


def details(data):
    if not isinstance(data,dict) or data.get('kind') not in EXTRA:
        raise ValueError('Choose Student, Individual Teacher or Institute.')
    kind=data['kind']; result={'kind':kind}
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
    result['privacy_accepted']=True
    return result


def password(value,confirmation):
    if not isinstance(value,str) or len(value)<12 or len(value)>128:
        raise ValueError('Use a password between 12 and 128 characters.')
    if value!=confirmation:raise ValueError('Passwords do not match.')


def verified(state,now):
    return bool(state and now<state.get('expires',0) and state.get('email_verified') is True
                and state.get('phone_verified') is True and not state.get('consumed'))
