"""Local-only registration integration check; all database changes roll back."""
import logging
import os
import uuid
import sys
import re
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch

stage = 'preflight'
suppressed_updates = 0
suppressed_jobs = 0


class SetupBlocked(Exception):
    """Only fixed, non-sensitive operator messages belong in this exception."""


def deny(operation):
    def blocked(*args, **kwargs):
        raise SetupBlocked(operation+' attempted during rollback-only test')
    return blocked


def discard_document_refresh(event=None, *args, **kwargs):
    global suppressed_updates
    # Frappe emits these for every saved document. They are browser refresh
    # signals scheduled after commit, not membership/delivery success evidence.
    if event in ('doc_update','list_update') and kwargs.get('after_commit') is True:
        suppressed_updates += 1
        return
    raise SetupBlocked('Unexpected realtime event attempted during rollback-only test')


def discard_deferred_job(*args, **kwargs):
    global suppressed_jobs
    # A job deferred until commit can never run in this rollback-only test.
    # Discard its scheduling without retaining or printing its payload.
    if kwargs.get('enqueue_after_commit') is True and not kwargs.get('now'):
        suppressed_jobs += 1
        return None
    raise SetupBlocked('Immediate background job attempted; only after-commit jobs may be discarded')


def run_request_guards(frappe, method, verb='GET'):
    """Real installed hooks with a synthetic request, not an HTTP/login test."""
    from werkzeug.wrappers import Request
    hooks=frappe.get_hooks('auth_hooks')
    required={'institute_lms.mobile_auth.authenticate',
              'institute_lms.account_billing.guard_request',
              'institute_lms.saas.guard_request','institute_lms.native_access.guard'}
    if not required.issubset(set(hooks)):
        raise SetupBlocked('Expected SISU request guards are not all installed')
    # Upstream LMS endpoint restriction hook: execute the installed function in
    # its configured order. Do not disable block_endpoints or widen its allowlist.
    reviewed=required|{'lms.auth.authenticate'}
    unknown=[hook for hook in hooks if hook not in reviewed]
    if unknown:
        for hook in unknown:
            # Only Python import identifiers, never hook arguments or settings.
            if isinstance(hook,str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+',hook):
                print('REVIEW AUTH HOOK: '+hook)
            else:
                print('REVIEW AUTH HOOK: unexpected non-module value (not displayed)')
        raise SetupBlocked('Additional authentication hook requires test review')
    request=Request.from_values(path='/api/method/'+method,method=verb)
    with patch.object(frappe.local,'request',request,create=True), patch.object(frappe.local,'form_dict',frappe._dict(cmd=method),create=True):
        for hook in hooks:
            if hook not in reviewed:
                raise SetupBlocked('Additional authentication hook requires test review')
            frappe.get_attr(hook)()


def main():
    global stage
    bench = (Path.home()/'sisu-hnb-sandbox-bench').resolve()
    if os.name!='posix' or Path.cwd().resolve()!=bench:raise SetupBlocked('Run from ~/sisu-hnb-sandbox-bench in local Ubuntu.')
    logging.disable(logging.CRITICAL)
    import frappe
    stage='initializing local sandbox'
    os.chdir(bench/'sites')
    frappe.init(site='hnb-checkout.localhost',sites_path=str(bench/'sites'))
    try:
        stage='connecting database'
        frappe.connect()
        stage='checking fixture prerequisites'
        issues=[]
        if frappe.conf.get('il_shared_campus_enabled') or frappe.conf.get('il_control_plane'):
            issues.append('Expected shared mode and control-plane mode both OFF.')
        institutes=frappe.get_all('IL Institute',pluck='name')
        students=frappe.get_all('IL Public Profile',filters={'kind':'Student','status':'Verified'},fields=['user'])
        print(f'CHECK: institute count={len(institutes)}; verified student count={len(students)}')
        if len(institutes)!=1 or len(students)!=1:
            issues.append('Exactly one institute and one verified student are required for this fixture.')
            raise SetupBlocked(' '.join(issues))
        institute=institutes[0]; original_institute=institute; user=students[0].user
        two_institutes='--two-institutes' in sys.argv[1:]
        admins=frappe.get_all('IL Member',filters={'institute':institute,'role':'Admin','active':1},fields=['user'])
        print(f'CHECK: active institute admin count={len(admins)}')
        temporary_admin = two_institutes or not admins
        # Administrator already exists in Frappe. Use it only as the owner of
        # transaction-local fixtures; never alter its User or role records.
        admin='Administrator' if temporary_admin else admins[0].user
        if temporary_admin:
            print('FIXTURE: will create a rollback-only admin membership; no login or User roles changed.')
        if admin and frappe.db.exists('IL Public Profile',{'user':admin}):
            issues.append('The institute admin already has a public profile; the test must preserve it.')
        phone=frappe.db.get_value('IL Verified Phone',{'user':user},['phone','verified_at'],as_dict=True)
        print(f'CHECK: student phone record={bool(phone)}; number present={bool(phone and phone.phone)}; verification timestamp={bool(phone and phone.verified_at)}')
        if not phone or not phone.phone or not phone.verified_at:
            issues.append('The verified student needs an existing phone verification record with a number and timestamp.')
        if not frappe.db.get_value('User',user,'enabled'):
            issues.append('The verified student login is disabled.')
        if issues:raise SetupBlocked(' '.join(issues))
        original=frappe.get_all('IL Member',filters={'institute':institute,'user':user},pluck='name')
        frappe.db.rollback()
        # These are in-memory settings only, never saved to site configuration.
        frappe.conf.il_shared_campus_enabled=1
        with ExitStack() as stack:
            for owner,name in ((frappe.db,'commit'),(frappe,'sendmail')):
                stack.enter_context(patch.object(owner,name,deny(name)))
            stack.enter_context(patch.object(frappe,'enqueue',discard_deferred_job))
            stack.enter_context(patch.object(frappe,'publish_realtime',discard_document_refresh))
            import requests, smtplib
            stack.enter_context(patch.object(requests.sessions.Session,'request',deny('HTTP request')))
            stack.enter_context(patch.object(smtplib.SMTP,'sendmail',deny('SMTP delivery')))
            temporary_admin_name=None
            second_institute=None
            classroom_fixtures=[]
            teacher_fixture=None
            try:
                frappe.set_user('Administrator')
                if two_institutes:
                    stage='provisioning temporary second institute'
                    from institute_lms.campus_provisioning import institute_insert
                    second=frappe.get_doc({'doctype':'IL Institute','code':'T'+uuid.uuid4().hex[:5].upper(),
                        'title':'[TEST] Rollback second institute','language':'en','billing_day':1})
                    with institute_insert(second):second.insert(ignore_permissions=True)
                    second_institute=institute=second.name
                if temporary_admin:
                    stage='creating rollback-only admin membership'
                    temporary_admin_name='TEST-ADMIN-'+uuid.uuid4().hex[:16]
                    fixture=frappe.get_doc({'doctype':'IL Member','institute':institute,
                        'user':admin,'role':'Admin','full_name':'[TEST] Rollback administrator',
                        'active':1,'language':'en','email_opt_in':0,'whatsapp_opt_in':0})
                    fixture.insert(ignore_permissions=True,set_name=temporary_admin_name)
                stage='creating temporary institute profile'
                profile=frappe.get_doc({'doctype':'IL Public Profile','user':admin,
                    'username':'test_'+uuid.uuid4().hex[:16], 'display_name':'[TEST] Rollback institute',
                    'kind':'Institute','country':'Sri Lanka','status':'Verified','workspace':institute})
                profile.flags.community_service=True
                profile.insert(ignore_permissions=True)
                stage='preparing temporary membership state'
                # Transaction-local removal permits a fresh insert for the existing
                # verified test identity. No existing profile/account is changed.
                frappe.db.sql('DELETE FROM `tabIL Member` WHERE institute=%s AND user=%s',(institute,user))
                frappe.set_user(user)
                from institute_lms.campus_join import register_student, directory
                from institute_lms.campus_context import current_institute, SESSION_KEY
                frappe.session.data.pop(SESSION_KEY,None)
                stage='discovering institute without a selected workspace'
                run_request_guards(frappe,'institute_lms.campus_join.directory')
                assert any(row.name==profile.name for row in directory('[TEST] Rollback')['institutes'])
                run_request_guards(frappe,'institute_lms.campus_join.details')
                run_request_guards(frappe,'institute_lms.campus_context.choices')
                run_request_guards(frappe,'institute_lms.campus_join.register_student','POST')
                print('PASS: installed request guards permit discovery, details, choices and registration without a selected institute.')
                stage='registering through real document validation and insert hooks'
                first=register_student(profile.name)
                assert first['created'] and frappe.db.exists('IL Member',first['student_number'])
                print('PASS: registration inserted a student membership through real Frappe hooks.')
                stage='checking duplicate registration'
                again=register_student(profile.name)
                assert not again['created'] and again['student_number']==first['student_number']
                print('PASS: repeat registration returned the same student number.')
                if two_institutes:
                    stage='checking isolation between institute memberships'
                    frappe.session.data[SESSION_KEY]=institute
                    assert current_institute().name==institute
                    stage='checking actual API membership role and native resource guard'
                    from institute_lms.api import identity
                    _, resolved_member=identity()
                    assert resolved_member.role=='Student' and resolved_member.name==first['student_number']
                    from institute_lms.native_access import guard, file_permission
                    from werkzeug.wrappers import Request
                    with patch.object(frappe.local,'request',Request.from_values(path='/api/resource/IL%20Member'),create=True), patch.object(frappe.local,'form_dict',frappe._dict(),create=True):
                        try:guard()
                        except frappe.PermissionError:pass
                        else:raise AssertionError('Generic member API allowed')
                    # Reject a foreign-user permission evaluation before a File
                    # lookup; this does not simulate downloading a physical file.
                    try:file_permission(frappe._dict(),user='Administrator')
                    except frappe.PermissionError:pass
                    else:raise AssertionError('Foreign-user file check allowed')
                    print('PASS: API identity retained Student role; generic member API and foreign-user file check denied.')
                    stage='creating rollback-only classroom fixtures'
                    # Disabled test identity: never usable for login, never mailed.
                    teacher_fixture='rollback-'+uuid.uuid4().hex+'@example.invalid'
                    teacher_user=frappe.get_doc({'doctype':'User','email':teacher_fixture,
                        'first_name':'Rollback teacher','enabled':0,'send_welcome_email':0,
                        'user_type':'Website User'})
                    teacher_user.insert(ignore_permissions=True)
                    from institute_lms.membership_write import authorized_insert
                    for target in (original_institute,institute):
                        teacher=frappe.get_doc({'doctype':'IL Member','institute':target,
                            'user':teacher_fixture,'role':'Teacher','full_name':'[TEST] Rollback teacher',
                            'active':1,'language':'en','email_opt_in':0,'whatsapp_opt_in':0})
                        with authorized_insert(teacher):
                            teacher.insert(ignore_permissions=True,set_name='TEST-TC-'+uuid.uuid4().hex[:16])
                        room=frappe.get_doc({'doctype':'IL Classroom','institute':target,
                            'title':'[TEST] Rollback free classroom','subject':'Test',
                            'teacher':teacher.name,'font':'sans','active':1,'fee_mode':'Free',
                            'fee':0,'owner_type':'Institute'})
                        room.insert(ignore_permissions=True)
                        classroom_fixtures.append(room.name)
                    from institute_lms.api import classroom_for
                    own_room=classroom_fixtures[1]
                    stage='checking unenrolled student classroom denial'
                    try:classroom_for(own_room)
                    except frappe.PermissionError:pass
                    else:raise AssertionError('Unenrolled student accepted')
                    stage='creating rollback-only enrollment'
                    enrollment=frappe.get_doc({'doctype':'IL Enrollment','institute':institute,
                        'classroom':own_room,'student':first['student_number'],
                        'active':1,'fee':0,'access_override':'Automatic'})
                    enrollment.insert(ignore_permissions=True)
                    stage='checking classroom membership isolation'
                    assert classroom_for(own_room)[2].name==own_room
                    try:classroom_for(classroom_fixtures[0])
                    except frappe.PermissionError:pass
                    else:raise AssertionError('Foreign free classroom accepted')
                    # Evaluate the file hook against a foreign classroom reference.
                    # No physical file is created or downloaded by this test.
                    try:file_permission(frappe._dict(name='test-file',attached_to_doctype='IL Classroom',attached_to_name=classroom_fixtures[0]))
                    except frappe.PermissionError:pass
                    else:raise AssertionError('Foreign classroom file reference accepted')
                    print('PASS: unenrolled class denied; enrolled own class accepted; foreign free class and its file reference denied.')
                    stage='checking institute teacher coverage against real subscription records'
                    from datetime import timedelta
                    from frappe.utils import now_datetime
                    from institute_lms.institute_coverage import sponsor, request_allowed
                    # Synthetic entitlement state is transaction-local, not a
                    # payment or a client trial grant. No payment record is made.
                    subscription=frappe.db.get_value('IL Account Subscription',{'account_key':'Institute:'+institute},'name')
                    if not subscription:raise SetupBlocked('Temporary institute subscription was not created by its member hook')
                    until=now_datetime()+timedelta(days=1)
                    frappe.db.set_value('IL Account Subscription',subscription,{'enabled':1,'trial_until':until,'paid_until':None})
                    stage='checking free and unpaid classroom access'
                    from institute_lms.api import access
                    from institute_lms.commercial import account_for, save as save_commercial
                    from institute_lms.commercial_rules import beneficiary
                    _,student_member,free_room=classroom_for(own_room)
                    provider=account_for(free_room,False)
                    if not provider:
                        provider=frappe.get_doc({'doctype':'IL Provider Account',
                            'provider_key':beneficiary(free_room),'institute':institute,
                            'owner_type':'Institute','plan':'Gold','enabled':1,
                            'billing_email':'rollback@example.invalid',
                            'cycle_start':now_datetime(),'cycle_end':until})
                        save_commercial(provider)
                    else:
                        frappe.db.set_value('IL Provider Account',provider.name,{'plan':'Gold','enabled':1})
                    assert access(free_room,student_member)['allowed'] is True
                    # Evaluate a paid variant without changing the stored class or
                    # granting access. This fixture must have no paid entitlement.
                    assert not frappe.db.exists('IL Paid Access',{'classroom':own_room})
                    paid_room=frappe._dict(free_room.as_dict())
                    paid_room.fee_mode='Paid'; paid_room.fee=1000
                    assert access(paid_room,student_member)['allowed'] is False
                    print('PASS: enrolled free class needs no paid grant; unpaid paid-class variant remains locked.')
                    relation=frappe.get_doc({'doctype':'IL Profile Relationship',
                        'relationship_key':'rollback-'+uuid.uuid4().hex,'profile':profile.name,
                        'user':teacher_fixture,'kind':'Teacher membership','status':'Pending'})
                    relation.flags.community_service=True
                    relation.insert(ignore_permissions=True)
                    frappe.conf.il_institute_teacher_coverage=1
                    frappe.conf.il_institute_trial_grants={institute:{'subscription':subscription,'expires_at':str(until)}}
                    assert sponsor(institute,teacher_fixture) is None
                    stage='checking real teacher approval endpoint'
                    teacher_profile=frappe.get_doc({'doctype':'IL Public Profile','user':teacher_fixture,
                        'username':'teacher_'+uuid.uuid4().hex[:14],'display_name':'[TEST] Rollback teacher',
                        'kind':'Teacher','country':'Sri Lanka','status':'Verified'})
                    teacher_profile.flags.community_service=True
                    teacher_profile.insert(ignore_permissions=True)
                    teacher_member=frappe.db.get_value('IL Member',{'institute':institute,'user':teacher_fixture},'name')
                    frappe.db.set_value('IL Member',teacher_member,'active',0)
                    frappe.db.set_value('IL Classroom',own_room,{'public_provider':profile.name,'teacher_assignment_active':1})
                    from institute_lms.teaching import membership as decide_membership
                    try:decide_membership(relation.name,'Active')
                    except frappe.PermissionError:pass
                    else:raise AssertionError('Student approved a teacher')
                    assert frappe.db.get_value('IL Profile Relationship',relation.name,'status')=='Pending'
                    # Only the newly-created, rollback-only membership is changed
                    # into the admin actor fixture. No original member/User roles change.
                    frappe.db.set_value('IL Member',first['student_number'],'role','Admin')
                    try:
                        assert decide_membership(relation.name,'Active')['status']=='Active'
                        assert frappe.db.get_value('IL Member',teacher_member,'active')==1
                    finally:
                        frappe.db.set_value('IL Member',first['student_number'],'role','Student')
                    print('PASS: student approval denied; institute admin endpoint activated teacher membership.')
                    assert sponsor(institute,teacher_fixture) is not None
                    assert sponsor(original_institute,teacher_fixture) is None
                    assert not request_allowed('institute_lms.api.create_classroom',institute,teacher_fixture)
                    assert not request_allowed('frappe.client.get_list',institute,teacher_fixture)
                    assert request_allowed('institute_lms.api.classrooms',institute,teacher_fixture)
                    stage='checking sponsored teacher subscription response and request guards'
                    independent=frappe.copy_doc(frappe.get_doc('IL Classroom',own_room))
                    independent.title='[TEST] Rollback independent classroom'
                    independent.owner_type='Teacher'
                    independent.owner_user=teacher_fixture
                    independent.public_provider=teacher_profile.name
                    independent.insert(ignore_permissions=True)
                    classroom_fixtures.append(independent.name)
                    personal_subscription=frappe.db.get_value('IL Account Subscription',{'account_key':'Teacher:'+teacher_fixture},'name')
                    if not personal_subscription:raise SetupBlocked('Temporary teacher subscription missing')
                    frappe.db.set_value('IL Account Subscription',personal_subscription,
                        {'trial_until':now_datetime()-timedelta(days=1),'paid_until':None})
                    # Enable only the uncommitted fixture User to exercise identity.
                    # It has no test password or externally issued session.
                    frappe.db.set_value('User',teacher_fixture,'enabled',1)
                    try:
                        frappe.set_user(teacher_fixture)
                        frappe.session.data[SESSION_KEY]=institute
                        from institute_lms.account_billing import account, public_account, policy
                        response=public_account(account())
                        assert not response['available'] and response['workspace_available']
                        assert response['institute_covered'] and response['institute_only']
                        assert policy()['available']
                        run_request_guards(frappe,'institute_lms.api.classrooms')
                        from institute_lms.api import classrooms
                        visible={row.name for row in classrooms()}
                        assert own_room in visible
                        assert independent.name not in visible and classroom_fixtures[0] not in visible
                        assert classroom_for(own_room)[2].name==own_room
                        try:classroom_for(independent.name)
                        except frappe.PermissionError:pass
                        else:raise AssertionError('Institute grant opened independent class')
                        print('PASS: sponsored teacher sees assigned institute class; independent and foreign classes excluded, direct independent access denied.')
                        try:run_request_guards(frappe,'institute_lms.api.create_classroom','POST')
                        except frappe.PermissionError:pass
                        else:raise AssertionError('Institute coverage unlocked independent creation')
                        print('PASS: expired personal plan reports institute-only workspace access; request guards allow classroom listing but deny independent creation.')
                    finally:
                        frappe.set_user(user)
                        frappe.session.data[SESSION_KEY]=institute
                        frappe.db.set_value('User',teacher_fixture,'enabled',0)
                    frappe.conf.il_institute_trial_grants[institute]['expires_at']=str(now_datetime()-timedelta(seconds=1))
                    assert sponsor(institute,teacher_fixture) is None
                    frappe.conf.il_institute_trial_grants[institute]['expires_at']=str(until)
                    stage='checking real teacher removal endpoint'
                    frappe.db.set_value('IL Member',first['student_number'],'role','Admin')
                    try:
                        assert decide_membership(relation.name,'Removed')['status']=='Removed'
                    finally:
                        frappe.db.set_value('IL Member',first['student_number'],'role','Student')
                    assert frappe.db.get_value('IL Member',teacher_member,'active')==0
                    assert frappe.db.get_value('IL Classroom',own_room,'teacher_assignment_active')==0
                    assert frappe.db.get_value('IL Member',{'institute':original_institute,'user':teacher_fixture},'active')==1
                    assert sponsor(institute,teacher_fixture) is None
                    print('PASS: removal endpoint revoked target membership and assignment; other institute membership remained active.')
                    print('PASS: institute coverage requires active affiliation and unexpired grant; foreign institute and independent/generic APIs denied.')
                    stage='checking isolation between institute memberships'
                    # Revoke only the original institute in this transaction.
                    frappe.db.sql('UPDATE `tabIL Member` SET active=0 WHERE institute=%s AND user=%s',(original_institute,user))
                    assert current_institute().name==institute
                    frappe.session.data[SESSION_KEY]=original_institute
                    try:current_institute()
                    except frappe.PermissionError:pass
                    else:raise AssertionError('Original revoked institute still accessible')
                    print('PASS: revoking institute A leaves institute B accessible; A is denied.')
                stage='checking revoked membership'
                frappe.db.set_value('IL Member',first['student_number'],'active',0)
                frappe.session.data[SESSION_KEY]=institute
                try:current_institute()
                except frappe.PermissionError:pass
                else:raise AssertionError('Revoked membership accepted')
                print('PASS: revoked membership cannot open the institute.')
            finally:
                frappe.db.rollback()
                frappe.conf.il_shared_campus_enabled=0
        stage='verifying rollback'
        restored=frappe.get_all('IL Member',filters={'institute':original_institute,'user':user},pluck='name')
        assert sorted(restored)==sorted(original)
        assert not frappe.db.exists('IL Public Profile',profile.name)
        if temporary_admin_name:
            assert not frappe.db.exists('IL Member',temporary_admin_name)
        if second_institute:
            assert not frappe.db.exists('IL Institute',second_institute)
            assert not frappe.db.exists('IL Member',{'institute':second_institute})
            print('PASS: temporary second institute and its memberships were rolled back.')
        for room in classroom_fixtures:assert not frappe.db.exists('IL Classroom',room)
        if teacher_fixture:
            assert not frappe.db.exists('User',teacher_fixture)
            assert not frappe.db.exists('IL Member',{'user':teacher_fixture})
            print('PASS: classroom fixtures and disabled test teacher identity were rolled back.')
        print('PASS: rollback restored original membership IDs and removed the temporary profile.')
        if temporary_admin_name:print('PASS: temporary admin membership was rolled back.')
        print(f'TEST ONLY: suppressed {suppressed_updates} after-commit document refresh signals; none published.')
        print(f'TEST ONLY: discarded {suppressed_jobs} after-commit jobs; asynchronous job behavior is not tested.')
        print('Shared mode remains OFF. No messages, configuration changes or restarts.')
        print('Still untested: HTTP/browser requests, physical file downloads, paid access, teacher login/approval UI and asynchronous jobs.')
    finally:
        if getattr(frappe.local,'db',None):frappe.db.rollback()
        frappe.destroy()


if __name__=='__main__':
    try:main()
    except SetupBlocked as error:
        print(f'BLOCKED at {stage}: {error}')
        print('No credentials displayed. No test changes committed.')
        raise SystemExit(1)
    except Exception as error:
        print(f'BLOCKED at {stage} [{type(error).__name__}]. No credentials printed; transaction rollback requested.')
        raise SystemExit(1)
