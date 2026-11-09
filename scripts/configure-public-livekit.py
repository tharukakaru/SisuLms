"""Connect Public campus to the tested LiveKit project without creating rooms."""
import asyncio,json,logging,os,stat,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
BENCH=Path('/home/sisu/frappe-bench')
TARGET='sisuacademylk.com'
KEYS=('il_livekit_url','il_livekit_api_key','il_livekit_api_secret')
stage='startup'

async def verify(values):
    from livekit import api
    from aiohttp import ClientTimeout
    parsed=urlsplit(values['il_livekit_url'])
    if parsed.scheme!='wss' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Secure URL required')
    client=api.LiveKitAPI(parsed._replace(scheme='https').geturl(),values['il_livekit_api_key'],values['il_livekit_api_secret'],timeout=ClientTimeout(total=20))
    try:await client.room.list_rooms(api.ListRoomsRequest())
    finally:await client.aclose()

def main():
    global stage
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    os.umask(0o077);logging.disable(logging.CRITICAL)
    import frappe
    os.chdir(BENCH/'sites')
    try:
        stage='read staging credentials'
        frappe.init(site='staging.sisuacademylk.com',sites_path=str(BENCH/'sites'));frappe.connect()
        values={k:frappe.conf.get(k) for k in KEYS}
        if not all(values.values()):raise ValueError('Source fields missing')
    finally:frappe.destroy()
    stage='read-only API authentication'
    asyncio.run(verify(values));print('PASS: LiveKit API authentication; no rooms changed.')
    stage='target configuration preflight'
    path=BENCH/'sites'/TARGET/'site_config.json'
    info=path.lstat()
    if path.is_symlink() or info.st_uid!=os.getuid():raise ValueError('Unexpected config ownership')
    original=path.read_text();cfg=json.loads(original)
    if cfg.get('il_control_plane'):raise ValueError('Target must be an institute site')
    if any(cfg.get(k) not in (None,'',values[k]) for k in KEYS):raise ValueError('Existing LiveKit values differ; not overwritten')
    if all(cfg.get(k)==values[k] for k in KEYS):
        print('ALREADY CONFIGURED: Public campus. No changes made.');return
    stage='private configuration backup'
    root=Path.home()/'.sisu-secrets';folder=root/'livekit-rollout'
    for p in (root,folder):
        p.mkdir(exist_ok=True,mode=0o700);s=p.lstat()
        if p.is_symlink() or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)&0o077:raise ValueError('Private directory required')
    backup=folder/(TARGET+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with backup.open('x') as out:out.write(original);out.flush();os.fsync(out.fileno())
    stage='save target LiveKit configuration'
    cfg.update(values)
    fd,temporary=tempfile.mkstemp(dir=path.parent,prefix='.livekit-config-')
    try:
        with os.fdopen(fd,'w') as out:json.dump(cfg,out,indent=2);out.flush();os.fsync(out.fileno())
        os.chmod(temporary,0o600)
        if path.read_text()!=original:raise ValueError('Concurrent config change')
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)
    stage='verify saved configuration'
    try:
        frappe.init(site=TARGET,sites_path=str(BENCH/'sites'));frappe.connect()
        if any(frappe.conf.get(k)!=values[k] for k in KEYS):raise ValueError('Saved values differ')
    finally:frappe.destroy()
    print('CONFIGURED: Public campus LiveKit; configuration file owner-only; previous configuration backed up privately.')
    print('No rooms, messages, recordings or restarts. Staging and platform unchanged. Browser teaching and recording storage still require tests.')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('STOPPED at '+stage+' ['+type(exc).__name__+']. No credentials printed.');raise SystemExit(1) from None
