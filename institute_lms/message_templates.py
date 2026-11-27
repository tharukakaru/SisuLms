"""SISU transactional presentation. No delivery, authentication or billing decisions."""
from html import escape
from pathlib import Path
import re

LOGO_NAME = 'sisu-email-logo.png'
LOGO_PATH = Path(__file__).parent / 'public' / 'admin-invite-logo.png'


def paragraph(text):
    return '<p>' + escape(str(text)).replace('\n', '<br>') + '</p>'


def details(rows):
    cells = ''.join(
        '<tr><td style="padding:12px 0;border-bottom:1px solid #e7dff0;color:#655871;width:42%;vertical-align:top">'
        + escape(str(label)) + '</td><td style="padding:12px 0;border-bottom:1px solid #e7dff0;color:#30223f;font-weight:600;text-align:right;overflow-wrap:anywhere">'
        + escape(str(value)) + '</td></tr>' for label, value in rows)
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;font-size:15px">' + cells + '</table>'


def action(label, url):
    # URLs come from the application's existing validated origins/token generators.
    from urllib.parse import urlsplit
    parsed = urlsplit(str(url))
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('Email actions require an HTTP(S) URL')
    return '<p><a href="' + escape(str(url), quote=True) + '">' + escape(str(label)) + '</a></p>'


def verification_body(code, minutes=10):
    if not re.fullmatch(r'[0-9]{6}', str(code)):
        raise ValueError('Expected a six-digit verification code')
    return (paragraph('Enter this code in the SISU window where you requested it.')
            + '<div style="background:#f3edf9;border:1px solid #e0d2ef;border-radius:12px;padding:24px 12px;text-align:center;margin:24px 0">'
            + '<div style="font-size:12px;font-weight:700;color:#655871;letter-spacing:1px;margin-bottom:10px">YOUR VERIFICATION CODE</div>'
            + '<div style="font-family:Consolas,monospace;font-size:36px;font-weight:700;letter-spacing:7px;color:#572b91">' + str(code) + '</div></div>'
            + paragraph(f'This code expires in {minutes} minutes. Never share it with anyone, including someone claiming to be SISU support.')
            + paragraph('If you did not request this code, you can ignore this email.'))


def render_email(title, body, *, preheader='', label='YOUR SISU UPDATE', logo=None):
    """body is trusted application HTML; escape all user data before supplying it."""
    body = re.sub(r'<p>', '<p style="margin:0 0 18px;font-size:16px;line-height:1.7">', body)
    body = re.sub(r'<a href=', '<a style="display:inline-block;background:#572b91;color:#ffffff;text-decoration:none;font-size:15px;font-weight:700;line-height:1.5;padding:14px 22px;border-radius:8px;overflow-wrap:anywhere" href=', body)
    logo_attr = 'src="' + escape(logo, quote=True) + '"' if logo else 'embed="' + LOGO_NAME + '"'
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>''' + escape(title) + '''</title></head>
<body style="margin:0;padding:0;background:#f6f3fa;color:#30223f;font-family:Arial,Helvetica,sans-serif">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all">''' + escape(preheader or title) + '''</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f3fa"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;background:#ffffff;border:1px solid #e6deee;border-radius:18px;overflow:hidden">
<tr><td style="background:#572b91;padding:28px 28px 24px;border-radius:18px 18px 0 0"><img ''' + logo_attr + ''' width="126" height="39" alt="SISU Academy" style="display:block;width:126px;height:39px;color:#ffffff;font-size:22px"><p style="margin:16px 0 0;color:#ffffff;font-size:13px;line-height:1.5">Learn. Connect. Grow.</p></td></tr>
<tr><td style="padding:32px 28px 22px;overflow-wrap:anywhere">
<p style="margin:0 0 12px;font-size:11px;letter-spacing:1.5px;font-weight:700;color:#704b91">''' + escape(label) + '''</p>
<h1 style="margin:0 0 22px;font-size:28px;line-height:1.25;letter-spacing:-0.5px;color:#30223f">''' + escape(title) + '''</h1>
''' + body + '''
</td></tr><tr><td style="padding:22px 28px;background:#faf8fc;border-top:1px solid #e6deee;border-radius:0 0 18px 18px">
<p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#572b91">Here for your next chapter.</p>
<p style="margin:0;font-size:12px;line-height:1.7;color:#655871">SISU Academy<br>This is an automatic account or learning update. Never share your password or verification codes.</p>
<!--unsubscribe link here-->
</td></tr></table><p style="font-size:12px;line-height:1.6;color:#655871;margin:20px 0 0">More than lessons. A place to belong.</p>
</td></tr></table></body></html>'''


def add_email_design(message, body=None, **options):
    """Keep plain text and add HTML plus a related PNG to a Python EmailMessage."""
    if body is None:
        body = paragraph(message.get_body(preferencelist=('plain',)).get_content().strip())
    title = options.pop('title', str(message['Subject']))
    message.add_alternative(render_email(title, body, logo='cid:sisu-logo', **options), subtype='html')
    message.get_payload()[-1].add_related(LOGO_PATH.read_bytes(), maintype='image', subtype='png', cid='<sisu-logo>', filename=LOGO_NAME, disposition='inline')


def sendmail(framework, *, subject, message, title=None, preheader='', label='YOUR SISU UPDATE', **kwargs):
    """Preserve Frappe queue timing, references, PDF attachments and redaction."""
    images = list(kwargs.pop('inline_images', None) or [])
    images.append({'filename': LOGO_NAME, 'filecontent': LOGO_PATH.read_bytes()})
    # An explicit wrapper avoids nested Frappe cards. Unsubscribe behaviour stays
    # with each original caller; subscriptions and learning notices keep theirs.
    return framework.sendmail(subject=subject, message=render_email(title or subject, message, preheader=preheader, label=label),
                           inline_images=images, raw_html=True, add_css=False, **kwargs)


def verification_sms(code, *, purpose='verification', minutes=10):
    if not re.fullmatch(r'[0-9]{6}', str(code)):
        raise ValueError('Expected a six-digit verification code')
    return f'{str(purpose).capitalize()} code: {code}\nValid for {minutes} minutes. Never share this code.\nIf you did not request it, ignore this SMS.'


def format_sms(body):
    """Consistent single brand prefix; never shorten codes, links or identities."""
    text = str(body).strip()
    text = re.sub(r'^(?:SISU(?:\s*:\s*|[ \t]*\r?\n))+', '', text, flags=re.I)
    # ASCII punctuation avoids needlessly switching English SMS to Unicode.
    text = text.translate(str.maketrans({'’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-', '\u00a0': ' '}))
    return 'SISU\n' + text
