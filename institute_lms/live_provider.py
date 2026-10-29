"""LiveKit server adapter. Client grants never include room recording/admin powers."""
import asyncio
from datetime import timedelta
import frappe

def settings():
    from urllib.parse import urlsplit
    url=frappe.conf.get('il_livekit_url','');key=frappe.conf.get('il_livekit_api_key');secret=frappe.conf.get('il_livekit_api_secret')
    if urlsplit(url).scheme!='wss' or not key or not secret:frappe.throw('Live video provider is not configured')
    try:
        from livekit import api
    except ImportError:frappe.throw('Install the documented LiveKit server extra before enabling live classes')
    return api,url,key,secret

def participant(room,user,name,teacher,publish=False):
    api,url,key,secret=settings()
    grant=api.VideoGrants(room_join=True,room=room,can_subscribe=True,can_publish=bool(teacher or publish),
                          can_publish_data=False,room_record=False,room_admin=False,
                          can_publish_sources=['camera','microphone','screen_share','screen_share_audio'] if teacher else ['camera','microphone'])
    token=api.AccessToken(key,secret).with_identity(user).with_name(name).with_ttl(timedelta(minutes=2)).with_grants(grant).to_jwt()
    return {'url':url,'token':token,'expires_in':120,'can_publish':bool(teacher or publish)}

def operation(action,room,egress=None,object_key=None):
    api,url,key,secret=settings()
    async def run():
        from aiohttp import ClientTimeout
        client=api.LiveKitAPI(url.replace('wss://','https://'),key,secret,timeout=ClientTimeout(total=30))
        try:
            if action=='start':return await client.room.create_room(api.CreateRoomRequest(name=room,empty_timeout=300,max_participants=int(frappe.conf.get('il_live_max_participants',100))))
            if action=='end':return await client.room.delete_room(api.DeleteRoomRequest(room=room))
            if action=='record':
                config=frappe.conf.get('il_live_recording_s3') or {}
                if not all(config.get(k) for k in ('bucket','access_key','secret','region')):frappe.throw('Private recording storage is not configured')
                output=api.EncodedFileOutput(file_type=api.EncodedFileType.MP4,filepath=object_key,
                    s3=api.S3Upload(**config))
                return await client.egress.start_room_composite_egress(api.RoomCompositeEgressRequest(room_name=room,layout='grid',file_outputs=[output]))
            if action=='stop_recording':return await client.egress.stop_egress(api.StopEgressRequest(egress_id=egress))
            if action=='reconcile':return await client.egress.list_egress(api.ListEgressRequest(room_name=room))
            raise ValueError('Unsupported live operation')
        finally:await client.aclose()
    return asyncio.run(run())

def webhook(raw,authorization):
    api,_,key,secret=settings()
    return api.WebhookReceiver(api.TokenVerifier(key,secret)).receive(raw,authorization)
