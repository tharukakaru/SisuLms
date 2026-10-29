"""Private S3-compatible media boundary; reservations precede direct uploads."""
import uuid
import frappe
from .saas import managed

TYPES={'video/mp4':'.mp4','video/webm':'.webm'}

def client():
    config=frappe.conf.get('il_private_media_s3') or {}
    if not all(config.get(k) for k in ('bucket','region','access_key','secret')):
        frappe.throw('Private media storage is not configured')
    from urllib.parse import urlsplit
    endpoint=config.get('endpoint_url')
    if endpoint and (urlsplit(endpoint).scheme!='https' or urlsplit(endpoint).username or urlsplit(endpoint).password):
        frappe.throw('Private storage requires a trusted HTTPS endpoint')
    try:import boto3
    except ImportError:frappe.throw('Install the media extra before enabling uploads')
    return boto3.client('s3',region_name=config['region'],endpoint_url=endpoint,
        aws_access_key_id=config['access_key'],aws_secret_access_key=config['secret']),config['bucket']

@frappe.whitelist(methods=['POST'])
def begin(classroom,size,content_type):
    from .api import classroom_for,require_role
    from .teaching import require
    from .pricing_rules import integer
    from .saas import quota
    from .usage import used
    inst,member,room=classroom_for(classroom,write=True);require_role(member,'Teacher');require(room,member,'edit')
    size=integer(size,'Video bytes',int(frappe.conf.get('il_private_video_max_bytes',2147483648)))
    if size<1 or content_type not in TYPES:frappe.throw('Upload an MP4 or WebM within the configured limit')
    provider,bucket=client()
    is_r2 = (frappe.conf.get('il_private_media_s3') or {}).get('provider') == 'r2'
    if not is_r2 and provider.get_bucket_versioning(Bucket=bucket).get('Status')!='Enabled':
        frappe.throw('Enable private bucket versioning before accepting media uploads')
    quota('storage_bytes',lambda:used('storage_bytes'),size)
    key='sisu/'+inst.name+'/'+uuid.uuid4().hex+TYPES[content_type]
    doc=managed(frappe.get_doc({'doctype':'IL Stored Object','institute':inst.name,'classroom':room.name,
        'owner_user':member.user,'bytes':size,'backend':'r2_media' if is_r2 else 's3_media','storage_key':key,'status':'ACTIVE','media_state':'Uploading'}))
    if is_r2:
        # Signed conditional PUT prevents reuse from overwriting accepted media.
        params = {'Bucket':bucket, 'Key':key, 'ContentType':content_type,
                  'ContentLength':size, 'IfNoneMatch':'*'}
        grant = {'method':'PUT', 'url':provider.generate_presigned_url('put_object', Params=params, ExpiresIn=600),
                 'headers':{'Content-Type':content_type, 'If-None-Match':'*'}}
    else:
        grant=provider.generate_presigned_post(bucket,key,Fields={'Content-Type':content_type},
            Conditions=[{'Content-Type':content_type},['content-length-range',size,size]],ExpiresIn=600)
    frappe.db.commit()
    return {'object':doc.name,'upload':grant,'expires_in':600}

@frappe.whitelist(methods=['POST'])
def complete(name):
    from .api import classroom_for
    from .teaching import require
    doc=frappe.get_doc('IL Stored Object',name,for_update=True)
    inst,member,room=classroom_for(doc.classroom,write=True);require(room,member,'edit')
    if doc.institute!=inst.name or doc.owner_user!=member.user or doc.backend not in ('s3_media', 'r2_media') or doc.status!='ACTIVE':
        frappe.throw('Media upload unavailable',frappe.PermissionError)
    if doc.media_state=='Ready':return {'media_key':doc.storage_key,'status':'Ready'}
    provider,bucket=client();result=provider.head_object(Bucket=bucket,Key=doc.storage_key)
    if result.get('ContentLength')!=doc.bytes or result.get('ContentType') not in TYPES:
        frappe.throw('Uploaded media does not match the reservation; operator reconciliation required')
    version=result.get('ETag') if doc.backend=='r2_media' else result.get('VersionId')
    if not version or version=='null':frappe.throw('A durable storage version is required')
    doc.storage_version=version;doc.media_state='Ready';managed(doc)
    return {'media_key':doc.storage_key,'status':'Ready'}

def grant(object_key,user,expires_in=120):
    # Caller has already checked purchase/class authorization. Not whitelisted.
    provider,bucket=client()
    obj=frappe.db.get_value('IL Stored Object',{'storage_key':object_key,'status':'ACTIVE'},['backend','storage_version','media_state'],as_dict=True)
    if not obj:frappe.throw('Private media object unavailable')
    params={'Bucket':bucket,'Key':object_key}
    if obj.backend in ('s3_media','r2_media') and obj.media_state!='Ready':
        frappe.throw('Complete the private upload first')
    if obj.backend=='s3_media':
        if not obj.storage_version:frappe.throw('Durable media version is missing')
        params['VersionId']=obj.storage_version
    return {'url':provider.generate_presigned_url('get_object',Params=params,ExpiresIn=min(120,int(expires_in)))}
