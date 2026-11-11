"""Deploy desktop web presentation; retain old assets for open tabs."""
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

BENCH = Path('/home/sisu/frappe-bench')
APP = BENCH / 'apps/institute_lms'
ALLOWED = {'institute_lms/public/login-sisu-logo.png', 'institute_lms/public/login-community.png', 'frontend/src/native/ProviderFirstLogin.vue', 'frontend/src/native/teacherEntryPath.js', 'frontend/src/study/appearance.js', 'institute_lms/public_signup.py', 'institute_lms/programme_courses.py', 'institute_lms/signup_rules.py', 'frontend/src/native/LearnerSignIn.vue', 'frontend/src/native/PortalRoot.vue', 'frontend/src/assets/figma/provider-story-footer.svg', 'frontend/src/native/RegistrationFlow.vue', 'frontend/src/native/Programmes.vue', 'institute_lms/public/login-footer.svg', 'frontend/src/native/ProviderAccessGate.vue', 'frontend/src/native/VerifiedSignup.vue', 'frontend/src/native/GeneralCampus.vue', 'frontend/src/native/InstituteJoinPicker.vue', 'frontend/src/native/MobileVerification.vue', 'institute_lms/portal_session.py', 'frontend/src/native/CampusSwitcher.vue', 'frontend/src/commerce/LmsIdentityCard.vue', 'institute_lms/hooks.py', 'frontend/src/learning/guideContent.js', 'frontend/src/learning/WebWelcomeStory.vue', 'frontend/src/native/verification.css', 'frontend/src/native/StudentClassrooms.vue', 'institute_lms/profiles.py', 'frontend/src/native/ProviderAccountChoice.vue', 'institute_lms/learning_spaces.py', 'frontend/src/App.vue', 'frontend/src/native/TeacherSignupLayout.vue', 'frontend/src/assets/figma/provider-community.png', 'frontend/src/native/AccountReceipts.vue', 'frontend/src/native/VerificationLayout.vue', 'frontend/src/commerce/ProfileEditor.vue', 'frontend/src/assets/figma/verification-story-footer.svg', 'institute_lms/public/login-presentation.js', 'frontend/src/StudentAppearance.vue', 'frontend/src/native/BankPayments.vue', 'frontend/src/assets/figma/verification-journey.png', 'institute_lms/public/login-presentation.css', 'frontend/src/native/PaymentRequired.vue', 'frontend/src/PageLoading.vue', 'institute_lms/onboarding_navigation.py'}


def digest(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.umask(0o022)
    if not (APP / 'institute_lms/provision_verification.py').is_file():
        raise RuntimeError('Existing hosting verification module is missing; preserve and restore it before deployment.')
    with tarfile.open('/tmp/sisu-completed-fixes.tgz') as archive:
        manifest = json.load(archive.extractfile('manifest.json'))
        if set(manifest) != ALLOWED or len(archive.getmembers()) != len(ALLOWED)+1:
            raise RuntimeError('Unexpected UI payload')
        payload = {}
        for name in ALLOWED:
            entry = archive.getmember(name)
            if not entry.isfile():
                raise RuntimeError('Unexpected archive member')
            payload[name] = archive.extractfile(entry).read()
            path = APP / name
            if path.is_symlink() or digest(payload[name]) != manifest[name]['after']:
                raise RuntimeError('UI payload mismatch')
            actual = digest(path.read_bytes()) if path.exists() else None
            if actual not in (manifest[name]['before'], manifest[name]['after'], *manifest[name].get('accepted_before',[])):
                raise RuntimeError('Source conflict: ' + name)
    root = Path.home() / '.sisu-secrets'
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o077:
        raise RuntimeError('Private backup directory required')
    backup = root / ('completed-fixes-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(mode=0o700)
    paths = [*ALLOWED, 'institute_lms/www/campus.html', 'institute_lms/public/portal']
    absent = []
    for name in paths:
        src, dst = APP / name, backup / name
        if not src.exists():
            absent.append(name)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    try:
        for name, data in payload.items():
            (APP / name).parent.mkdir(parents=True, exist_ok=True)
            (APP / name).write_bytes(data)
            (APP / name).chmod(0o644)
        for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
            subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-cache'], cwd=BENCH, check=True)
        env = os.environ.copy()
        env['PATH'] = '/opt/node-v24.15.0-linux-x64/bin:' + env.get('PATH', '')
        with (backup / 'build.log').open('w') as log:
            subprocess.run(['npm', 'run', 'build'], cwd=APP / 'frontend', env=env, stdout=log, stderr=log, check=True)
        portal = APP / 'institute_lms/public/portal'
        old = backup / 'institute_lms/public/portal'
        for file in old.rglob('*'):
            target = portal / file.relative_to(old)
            if file.is_file() and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, target)
        for path in [portal, *portal.rglob('*')]:
            path.chmod(0o755 if path.is_dir() else 0o644)
        (APP / 'institute_lms/www/campus.html').chmod(0o644)
    except Exception:
        for name in paths:
            src, dst = backup / name, APP / name
            if name in absent:
                if dst.is_file():
                    dst.unlink()
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
        print('Previous sources/UI restored. Private build log:', backup / 'build.log')
        raise
    for site in ('sisuacademylk.com', 'teen.sisuacademylk.com', 'platform.sisuacademylk.com', 'staging.sisuacademylk.com'):
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-cache'], cwd=BENCH, check=True)
        subprocess.run(['/usr/local/bin/bench', '--site', site, 'clear-website-cache'], cwd=BENCH, check=True)
    print('DEPLOYED: completed student presentation, login styling, onboarding and returning-teacher routing fixes. Restart web, run checks and hard-refresh. Card-required trials and new personal-workspace activation are not implemented by this package.')
    print('No schema or bank-account data changes by deployment. Existing enrollments/payments unchanged. Gateway configuration unchanged. No demo records changed by this installer.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('STOPPED [' + type(exc).__name__ + ']. ' + (str(exc) if isinstance(exc, RuntimeError) else 'Check private build log; browser result not confirmed.'))
        raise SystemExit(1) from None
