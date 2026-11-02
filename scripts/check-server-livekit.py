"""Read-only LiveKit API authentication check; no room or recording mutations."""
import asyncio,logging,os
from pathlib import Path
from urllib.parse import urlsplit
stage='startup'

def api_url(value):
    parsed=urlsplit(value)
    if parsed.scheme!='wss' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Secure LiveKit URL required')
    return parsed._replace(scheme='https').geturl()

async def probe(api,url,key,secret):
    from aiohttp import ClientTimeout
    client=api.LiveKitAPI(url,key,secret,timeout=ClientTimeout(total=20))
    try:
        await client.room.list_rooms(api.ListRoomsRequest())
    finally:await client.aclose()

def main():
    global stage
    if os.name!='posix' or Path.home()!=Path('/home/sisu'):raise ValueError('Run as sisu')
    logging.disable(logging.CRITICAL)
    import frappe
    os.chdir('/home/sisu/frappe-bench/sites')
    try:
        stage='load staging configuration'
        frappe.init(site='staging.sisuacademylk.com',sites_path='/home/sisu/frappe-bench/sites');frappe.connect()
        names=('il_livekit_url','il_livekit_api_key','il_livekit_api_secret')
        missing=[key for key in names if not frappe.conf.get(key)]
        if missing:
            print('BLOCKED: missing LiveKit configuration fields: '+', '.join(missing));return
        url=api_url(frappe.conf['il_livekit_url'])
        stage='import installed LiveKit SDK'
        from livekit import api
        print('PASS: LiveKit SDK and secure URL configuration present.')
        stage='read-only LiveKit ListRooms request'
        asyncio.run(probe(api,url,frappe.conf['il_livekit_api_key'],frappe.conf['il_livekit_api_secret']))
        print('PASS: LiveKit authenticated API request completed. Room names and credentials not displayed.')
        print('No rooms created or modified; no recordings started. Browser audio/video, screen sharing and recording delivery remain untested.')
    finally:
        try:frappe.db.rollback()
        except Exception:pass
        frappe.destroy()

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('CHECK FAILED at '+stage+' ['+type(exc).__name__+']. No keys, tokens, endpoint or exception contents printed.');raise SystemExit(1) from None
