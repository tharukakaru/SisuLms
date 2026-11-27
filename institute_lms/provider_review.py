"""Campus-side provider profile review requested by the platform owner panel.

Not whitelisted: it only runs as a background job that the platform enqueues
for an explicitly configured reporting campus on the same bench
(see owner_people.review). Every check happens here, on the campus, against
the campus's own records.
"""
import hashlib
import re
import frappe
from frappe.model.naming import make_autoname


def _code(profile):
    words = re.findall(r'[A-Za-z]+', profile.display_name or '')
    prefix = ''.join(w[0] for w in words[:2]).upper().ljust(2, 'X') if words else 'ED'
    return make_autoname(prefix + '.#######')


def _institute_workspace(profile):
    """Give an approved institute its own workspace on a shared campus."""
    from .campus_provisioning import institute_insert
    from .membership_write import authorized_insert
    phone = frappe.db.get_value('IL Verified Phone', {'user': profile.user}, 'phone')
    if not phone:
        frappe.throw('Mobile verification is required before approval.')
    if profile.workspace:
        member = frappe.db.get_value('IL Member', {'institute': profile.workspace, 'user': profile.user},
                                     ['role', 'active'], as_dict=True)
        if member and member.role == 'Admin' and member.active:
            return profile.workspace
        frappe.throw('This institute already has a workspace that needs a manual review.')
    if frappe.db.exists('IL Member', {'user': profile.user, 'active': 1, 'role': ['in', ['Admin', 'Teacher']]}):
        frappe.throw('This account already has workspace access. Review its memberships first.')
    code = 'I' + hashlib.sha256(profile.user.encode()).hexdigest()[:11].upper()
    if frappe.db.exists('IL Institute', {'code': code}):
        frappe.throw('A workspace for this account already exists. Review it manually.')
    institute = frappe.get_doc({'doctype': 'IL Institute', 'code': code, 'title': profile.display_name,
                                'language': 'en', 'billing_day': 1})
    with institute_insert(institute):
        institute.insert(ignore_permissions=True)
    user = frappe.get_doc('User', profile.user)
    user.append_roles('Institute Admin')
    if frappe.db.exists('Role', 'Moderator'):
        user.append_roles('Moderator')
    user.save(ignore_permissions=True)
    member = frappe.get_doc({'doctype': 'IL Member', 'institute': institute.name, 'user': profile.user,
                             'role': 'Admin', 'full_name': profile.display_name, 'phone': phone, 'active': 1,
                             'language': 'en', 'email_opt_in': 0, 'whatsapp_opt_in': 0})
    with authorized_insert(member):
        member.insert(ignore_permissions=True)  # member_created hook opens the institute account
    return institute.name


def approve_new_institute(profile):
    """Internal first-submission path; never called by a bulk migration or GET."""
    user = frappe.session.user
    if user == 'Guest' or profile.user != user or profile.kind != 'Institute' or profile.status != 'Pending':
        frappe.throw('Verified institute onboarding required.', frappe.PermissionError)
    if not frappe.db.exists('IL Registration Request', {
        'email': user, 'account_type': 'Institute', 'status': 'Approved', 'email_verified': 1
    }):
        frappe.throw('Verify your institute registration email first.', frappe.PermissionError)
    phone = frappe.db.get_value('IL Verified Phone', {'user': user}, ['phone', 'verified_at'], as_dict=True)
    if not phone or not phone.phone or not phone.verified_at:
        frappe.throw('Verify your mobile number first.', frappe.PermissionError)
    result = apply(profile.name, 'Verified',
                   'Automatically approved after verified institute onboarding.', 'Automatic institute onboarding')
    if not result.get('ok'):
        frappe.throw(result.get('message') or 'Institute setup could not be completed.')
    profile.reload()
    # Preserve existing settlement/trial dates. Onboarding approval cannot grant paid access.
    if profile.workspace:
        from .account_billing import account, save
        inst = frappe.get_doc('IL Institute', profile.workspace)
        member = frappe.get_doc('IL Member', frappe.db.get_value('IL Member',
            {'institute': inst.name, 'user': user, 'role': 'Admin', 'active': 1}, 'name'))
        subscription = account(inst, member, create=True, lock=True)
        subscription.onboarding_payment_required = 1
        save(subscription)
    return result


def apply(profile, decision, reason, reviewer):
    """Return {'ok', 'status', 'message'}; refusals roll back and never raise."""
    try:
        if frappe.conf.get('il_control_plane'):
            frappe.throw('Provider reviews run on campus sites only.')
        reason = str(reason or '').strip()
        if decision not in ('Verified', 'Rejected') or not reason:
            frappe.throw('Choose approve or reject and give a reason.')
        frappe.db.sql('SELECT name FROM `tabIL Public Profile` WHERE name=%s FOR UPDATE', (profile,))
        if not frappe.db.exists('IL Public Profile', profile):
            frappe.throw('Profile not found on this campus.')
        p = frappe.get_doc('IL Public Profile', profile)
        if p.kind not in ('Teacher', 'Institute') or p.status != 'Pending':
            frappe.throw('This profile is no longer waiting for review. Refresh to see its status.')
        if decision == 'Verified':
            if not p.code:
                p.code = _code(p)
            if p.kind == 'Institute':
                if frappe.conf.get('il_shared_campus_enabled'):
                    p.workspace = _institute_workspace(p)
                else:
                    from .api import institute
                    from .onboarding import activate
                    workspace = institute().name
                    activate(p, workspace)
                    p.workspace = workspace
            else:
                from .onboarding import activate
                from .teacher_workspace import enabled as unified_teacher_enabled
                # With unified signup the teacher opens a personal workspace themselves.
                if not unified_teacher_enabled():
                    activate(p)
        p.status = decision
        # The applicant may see review_reason, so the reviewer goes in an audit comment instead.
        p.review_reason = reason[:1000]
        p.reviewed_by = 'Administrator'
        from .profiles import write
        write(p)
        p.add_comment('Info', f'{decision} from the platform owner panel by {reviewer}')
        decision_made(p)
        return {'ok': True, 'status': p.status, 'code': p.code, 'workspace': p.workspace}
    except (frappe.ValidationError, frappe.PermissionError) as e:
        frappe.db.rollback()
        frappe.clear_messages()
        return {'ok': False, 'message': str(e) or 'The campus refused this review.'}


# ---------------------------------------------------------------------------
# Notifications. Email goes through the site's Frappe mail account and SMS
# through the site's configured adapter. A failed channel is logged and never
# blocks the signup or the review decision.

def _bench_sites():
    import json
    from pathlib import Path
    root = Path(frappe.get_site_path()).resolve().parent
    for path in root.iterdir():
        config = path / 'site_config.json'
        if path.is_dir() and config.is_file():
            try:
                yield path.name, json.loads(config.read_text())
            except (ValueError, OSError):
                continue


def _platforms_for(campus):
    """Control-plane sites on this bench that report on (and review) this campus."""
    return [name for name, conf in _bench_sites()
            if conf.get('il_control_plane') and campus in (conf.get('il_owner_reporting_sites') or [])]


def _enqueue_on(site, method, **kwargs):
    from frappe.utils.background_jobs import get_queue
    get_queue('default').enqueue_call('frappe.utils.background_jobs.execute_job', timeout=300,
        kwargs={'site': site, 'user': 'Administrator', 'method': method, 'event': None,
                'job_name': method, 'is_async': True, 'kwargs': kwargs})


def _sms(phone, text):
    from .providers import sms
    from .message_templates import format_sms
    sms(phone, format_sms(text))


def _try(channel, fn):
    try:
        fn()
        return True
    except Exception:
        frappe.log_error(title='Provider review ' + channel + ' notification failed')
        return False


def institute_submitted(profile):
    """Campus: tell the platform reviewers an institute profile awaits review."""
    if profile.kind != 'Institute' or profile.status != 'Pending':
        return
    campus = frappe.local.site
    payload = dict(campus=campus, user=profile.user, display_name=profile.display_name,
                   username=profile.username, country=profile.country or '')
    platforms = _platforms_for(campus)
    if not platforms:
        frappe.log_error(title='Provider review: no platform reviews this campus', message=campus)
        return
    frappe.db.after_commit.add(lambda: [
        _enqueue_on(site, 'institute_lms.provider_review.notify_reviewers', **payload) for site in platforms])


def _reviewers():
    """Platform managers (only they can approve), each with a mobile when one is known."""
    from .owner_access import primary_email
    people = {}
    primary = primary_email()
    if primary and frappe.db.get_value('User', primary, 'enabled'):
        people[primary] = (frappe.db.get_value('IL Owner Access', {'user': primary}, 'phone')
                           or frappe.db.get_value('IL Verified Phone', {'user': primary}, 'phone')
                           or frappe.db.get_value('User', primary, 'mobile_no'))
    for row in frappe.get_all('IL Owner Access', filters={'enabled': 1, 'access_level': 'Administrator'},
                              fields=['user', 'phone']):
        if frappe.db.get_value('User', row.user, 'enabled'):
            people.setdefault(row.user, row.phone)
    return people


def notify_reviewers(campus, user, display_name, username, country):
    """Platform job: email and SMS every reviewer about a new institute application."""
    from frappe.utils import get_url
    from .message_templates import sendmail, paragraph, details, action
    if not frappe.conf.get('il_control_plane'):
        return
    link = get_url('/campus#People%20%26%20connections')
    body = (paragraph('A new institute has finished signup and is waiting for your review.')
            + details([('Institute', display_name), ('Username', '@' + username), ('Account', user),
                       ('Country', country or 'Not given'), ('Campus', campus)])
            + paragraph('Open People & connections, choose this campus and select Review.')
            + action('Review institute', link))
    text = f'New institute awaiting review: {display_name} (@{username}). Review it in the owner panel: {link}'
    for email, phone in _reviewers().items():
        _try('email', lambda email=email: sendmail(frappe, recipients=[email], now=True,
             subject=f'Institute awaiting review: {display_name}', title='Institute awaiting review',
             preheader=f'{display_name} (@{username}) needs your approval', label='OWNER REVIEW', message=body))
        if phone:
            _try('sms', lambda phone=phone: _sms(phone, text))


def decision_made(profile):
    """Campus: once the review commits, tell the applicant."""
    name, site = profile.name, frappe.local.site
    frappe.db.after_commit.add(lambda: _enqueue_on(site, 'institute_lms.provider_review.notify_applicant',
                                                   profile=name))


def notify_applicant(profile):
    """Campus job: email and SMS the applicant about an approval or rejection."""
    from frappe.utils import get_url
    from .message_templates import sendmail, paragraph, action
    p = frappe.db.get_value('IL Public Profile', profile,
                            ['user', 'kind', 'status', 'display_name', 'review_reason'], as_dict=True)
    if not p or p.status not in ('Verified', 'Rejected'):
        return
    link = get_url('/campus')
    institute = p.kind == 'Institute'
    if p.status == 'Verified':
        subject = 'Your SISU institute is approved' if institute else 'Your SISU teacher profile is verified'
        step = ('Sign in to choose your plan and open your institute workspace.' if institute
                else 'Sign in to open your teaching workspace.')
        body = (paragraph(f'Good news, {p.display_name}. ' + ('Your institute has been approved.' if institute
                          else 'Your teacher profile has been verified.'))
                + paragraph(step) + action('Sign in to SISU', link))
        text = f'Your SISU {"institute" if institute else "teacher profile"} is approved. {step} {link}'
    else:
        reason = p.review_reason or 'Please review your details.'
        subject = 'Your SISU profile needs an update'
        body = (paragraph(f'Hello {p.display_name}, we could not approve your profile yet.')
                + paragraph('Reason: ' + reason) + paragraph('Sign in to update your details and send them again.')
                + action('Update my profile', link))
        text = f'Your SISU profile needs an update. Reason: {reason[:120]}. Sign in to update it: {link}'
    _try('email', lambda: sendmail(frappe, recipients=[p.user], now=True, subject=subject, title=subject,
                                   label='YOUR SISU ACCOUNT', message=body))
    phone = frappe.db.get_value('IL Verified Phone', {'user': p.user}, 'phone')
    if phone:
        _try('sms', lambda: _sms(phone, text))
