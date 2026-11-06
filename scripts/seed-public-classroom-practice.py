"""Add labelled practice content only to the existing public demo classroom.

Run as sisu. No account activation, financial records, messages or configuration
changes. The sample animation uses the real protected recording playback path;
it is explicitly not represented as a captured live lesson.
"""
import hashlib
import json
import logging
import os
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

BENCH = Path('/home/sisu/frappe-bench')
TITLE = '[DEMO] Institute teacher mathematics - free practice'
TEACHER = 'sisu-public-demo-teacher@example.invalid'
VIDEO = Path('/tmp/sisu-demo-playback.mp4')
VIDEO_SHA = '49711d9e487676d58a843ebed1569a4ed69c1eaf5b10cb616243695b4582d0de'
STAGE = 'preflight'


def deny(*args, **kwargs):
    raise RuntimeError('Unexpected external notification')


def deferred(*args, **kwargs):
    if kwargs.get('enqueue_after_commit') is True and not kwargs.get('now'):
        return
    deny()


def refresh(event=None, *args, **kwargs):
    # File attachment comments publish an internal realtime update, sometimes
    # without after_commit. Suppress all realtime delivery in this CLI seed.
    # Email, job and SMTP boundaries remain separate; no event is dispatched.
    return None


def main():
    global STAGE
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    video = VIDEO.read_bytes()
    if hashlib.sha256(video).hexdigest() != VIDEO_SHA:
        raise RuntimeError('Unexpected sample video')
    logging.disable(logging.CRITICAL)
    import frappe
    from frappe.utils import now_datetime
    from frappe.utils.file_manager import save_file
    from institute_lms import papers, classroom_quizzes
    from institute_lms.paper_rules import validate_questions
    from institute_lms.classroom_quiz_rules import normalize
    from institute_lms.saas import managed
    from institute_lms.private_media import client
    os.chdir(BENCH / 'sites')
    STAGE = 'public site initialization'
    frappe.init(site='sisuacademylk.com', sites_path=str(BENCH / 'sites'))
    frappe.connect()
    frappe.set_user('Administrator')
    try:
        STAGE = 'demo classroom and schema checks'
        if not frappe.conf.get('il_shared_campus_enabled') or not frappe.conf.get('il_payments_paused'):
            raise RuntimeError('Expected public shared campus with gateway payments paused')
        inst = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO'}, 'name')
        name = frappe.db.get_value('IL Classroom', {'institute': inst, 'title': TITLE}, 'name')
        if not name:
            raise RuntimeError('Existing demo classroom required')
        room = frappe.get_doc('IL Classroom', name)
        institute_doc = frappe.get_doc('IL Institute', inst)
        frappe.db.sql('SELECT name FROM `tabIL Classroom` WHERE name=%s FOR UPDATE', (name,))
        if room.owner_user != TEACHER or frappe.db.get_value('User', TEACHER, 'enabled') or room.fee_mode != 'Free':
            raise RuntimeError('Demo identity or classroom changed; no changes made')
        for dt in ('IL Paper', 'IL Paper Attempt', 'IL Classroom Quiz', 'IL Classroom Quiz Submission', 'IL Live Room', 'IL Stored Object'):
            if not frappe.db.table_exists(dt):
                raise RuntimeError('Required classroom schema missing: ' + dt)
        for dt, fields in {'IL Classroom Quiz': {'questions', 'question_count', 'published_at'},
                'IL Live Room': {'recording_published', 'stored_object'},
                'IL Stored Object': {'media_state', 'storage_version'}}.items():
            if not fields.issubset(set(frappe.db.get_table_columns(dt))):
                raise RuntimeError('Required classroom columns missing: ' + dt)
        from institute_lms.account_storage import configured
        if not configured() and not frappe.conf.get('il_tenant_id'):
            raise RuntimeError('Public upload storage allocation is not configured. Run inspect-public-learning-storage.py before retrying.')
        STAGE = 'protected video configuration'
        provider, bucket = None, None
        media_config = frappe.conf.get('il_private_media_s3') or {}
        missing = [key for key in ('bucket', 'region', 'access_key', 'secret') if not media_config.get(key)]
        adapter_ok = frappe.conf.get('il_private_video_adapter') == 'institute_lms.private_media.grant'
        print(json.dumps({'public_private_video': {'missing_setting_names': missing,
            'expected_adapter': adapter_ok, 'allowed_hosts_present': bool(frappe.conf.get('il_private_video_hosts'))}}))
        if not missing and adapter_ok and frappe.conf.get('il_private_video_hosts'):
            try:
                provider, bucket = client()
            except frappe.ValidationError:
                print('BLOCKED: protected video client validation; sample recording not created.')
        else:
            print('BLOCKED: public protected-video configuration incomplete; sample recording not created.')
        with ExitStack() as stack:
            # Bench-only fixture scope: Administrator has no shared-campus
            # membership. Keep the real quota/storage hooks enabled and assign
            # the validated demo institute as owner of this fixture upload.
            from institute_lms import api
            stack.enter_context(patch.object(api, 'institute', lambda: institute_doc))
            for obj, attr, fn in ((frappe, 'sendmail', deny), (frappe, 'enqueue', deferred), (frappe, 'publish_realtime', refresh)):
                stack.enter_context(patch.object(obj, attr, fn))

            def existing(dt, title):
                return frappe.db.get_value(dt, {'classroom': room.name, 'title': title}, 'name')

            STAGE = 'practice handout'
            handout_title = '[DEMO] Algebra practice handout'
            if not existing('IL Material', handout_title):
                body = b'SISU DEMO - Algebra practice\n\nSolve 2x + 3 = 11.\nSubtract 3: 2x = 8. Divide by 2: x = 4.\n\nTry 3x + 6 = 21. Show each step.\nAnswer: x = 5.\n\nPractice content only; no certification or payment.\n'
                file = save_file('sisu-demo-algebra.txt', body, 'IL Classroom', room.name, is_private=1)
                frappe.get_doc(dict(doctype='IL Material', institute=inst, classroom=room.name,
                    title=handout_title, kind='Document', description='Download this labelled practice handout.',
                    file_id=file.name, filename='sisu-demo-algebra.txt', file_type='txt', file_size=len(body),
                    download_policy='Downloadable')).insert(ignore_permissions=True)
            STAGE = 'practice assignment'
            title = '[DEMO] Show your algebra steps'
            if not existing('IL Paper', title):
                questions = validate_questions([dict(kind='Written', prompt='Solve 3x + 6 = 21. Explain both steps.', marks=5)])
                papers.save(frappe.get_doc(dict(doctype='IL Paper', institute=inst, classroom=room.name,
                    title=title, description='Practice assignment. Submit your explanation; teacher grading is separate.',
                    source='Manual', status='Published', questions=json.dumps(questions), duration_minutes=30,
                    max_marks=5, allow_upload=1, published_by='Administrator', published_at=now_datetime())))
            STAGE = 'practice quiz'
            title = '[DEMO] Algebra quick check'
            if not existing('IL Classroom Quiz', title):
                clean = normalize(dict(title=title, instructions='Practice quiz: choose one answer for each question.', questions=[
                    dict(prompt='If 2x + 3 = 11, what is x?', options=['2', '3', '4', '5'], answer=2),
                    dict(prompt='If 3x + 6 = 21, what is x?', options=['3', '4', '5', '6'], answer=2)]), complete=True)
                classroom_quizzes.write(frappe.get_doc(dict(doctype='IL Classroom Quiz', institute=inst,
                    classroom=room.name, title=title, instructions=clean['instructions'], status='Published',
                    questions=json.dumps(clean['questions']), question_count=2,
                    published_by='Administrator', published_at=now_datetime())))
            STAGE = 'protected sample video'
            title = '[DEMO] SISU sample animation - playback test'
            if provider is not None and not existing('IL Live Room', title):
                from institute_lms.saas import quota
                from institute_lms.usage import used
                quota('storage_bytes', lambda: used('storage_bytes'), len(video))
                key = 'sisu/public-demo/' + VIDEO_SHA + '.mp4'
                from botocore.exceptions import ClientError
                try:
                    head = provider.head_object(Bucket=bucket, Key=key)
                except ClientError as exc:
                    if str(exc.response.get('Error', {}).get('Code')) not in ('404', 'NoSuchKey', 'NotFound'):
                        raise
                    provider.put_object(Bucket=bucket, Key=key, Body=video, ContentType='video/mp4',
                        Metadata={'sha256': VIDEO_SHA}, IfNoneMatch='*')
                    head = provider.head_object(Bucket=bucket, Key=key)
                if head.get('ContentLength') != len(video) or head.get('Metadata', {}).get('sha256') != VIDEO_SHA:
                    raise RuntimeError('Existing sample object differs; not overwritten')
                r2 = media_config.get('provider') == 'r2'
                version = head.get('ETag') if r2 else head.get('VersionId')
                if not version or version == 'null':
                    raise RuntimeError('Protected storage needs a durable object version')
                obj = managed(frappe.get_doc(dict(doctype='IL Stored Object', institute=inst, classroom=room.name,
                    owner_user=TEACHER, bytes=len(video), backend='r2_media' if r2 else 's3_media', storage_key=key,
                    status='ACTIVE', media_state='Ready', storage_version=version)))
                now = now_datetime()
                session = frappe.get_doc(dict(doctype='IL Session', institute=inst, classroom=room.name, title=title,
                    description='SISU sample animation for playback testing, not a captured live lesson.',
                    starts_at=now-timedelta(minutes=2), ends_at=now-timedelta(minutes=1), mode='Online',
                    status='Completed')).insert(ignore_permissions=True)
                managed(frappe.get_doc(dict(doctype='IL Live Room', institute=inst, classroom=room.name,
                    session=session.name, title=title, starts_at=session.starts_at, status='Ended',
                    provider_room='public-demo-playback-'+room.name, recording_status='Ready',
                    stored_object=obj.name, recording_published=1)))
            frappe.db.commit()
        print('SAVED: labelled handout, assignment and quiz in ' + room.name)
        print('SAVED: protected sample playback.' if provider is not None else 'PENDING: recording setup and playback; not passed.')
        print('No account activation, payments, enrollments, messages or settings changed. Reruns reuse content.')
        print('Browser download, playback and assessment submissions still require acceptance checks.')
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        import traceback
        print(json.dumps({'failure_frames': [{'file': Path(f.filename).name, 'function': f.name, 'line': f.lineno}
            for f in traceback.extract_tb(exc.__traceback__)[-6:]]}))
        print('STOPPED at '+STAGE+': '+type(exc).__name__+'. '+(str(exc) if isinstance(exc, RuntimeError) else 'No credentials or raw provider response displayed.'))
        raise SystemExit(1) from None
