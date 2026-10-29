"""Explicit, audited cleanup of expired unused upload reservations only."""
import frappe
from frappe.utils import now_datetime,get_datetime
from .saas import managed,audit

def references(doc):
    return any(frappe.db.exists(dt,filters) for dt,filters in (
        ('IL Lecture Product',{'media_key':doc.storage_key}),
        ('IL Lecture Access',{'media_key':doc.storage_key}),
        ('IL Live Room',{'stored_object':doc.name})))

@frappe.whitelist()
def listing():
    from .api import identity,require_role
    inst,m=identity();require_role(m,'Admin')
    return frappe.get_all('IL Stored Object',filters={'institute':inst.name,'backend':['in',['s3_media','r2_media']],'status':['!=','PURGED'],'media_state':['!=','Ready']},
        fields=['name','classroom','bytes','media_state','status','creation'],order_by='creation asc',limit_page_length=100)

@frappe.whitelist(methods=['POST'])
def cleanup(name,reason):
    from .api import identity,require_role
    from .saas import state
    inst,m=identity();require_role(m,'Admin');state(lock=True)
    d=frappe.get_doc('IL Stored Object',name,for_update=True)
    if d.institute!=inst.name or d.backend not in ('s3_media','r2_media'):frappe.throw('Upload unavailable',frappe.PermissionError)
    if d.status=='PURGED':return {'status':'PURGED'}
    if len(str(reason).strip())<10:frappe.throw('An audit reason is required')
    if d.get('legal_hold') or d.media_state=='Ready' or references(d):frappe.throw('Held, referenced or confirmed media cannot be cleaned up')
    if (now_datetime()-get_datetime(d.creation)).total_seconds()<86400:frappe.throw('Wait 24 hours after the upload grant expires')
    from .private_media import client
    provider,bucket=client()
    remove_exact(provider,bucket,d.storage_key,versioned=d.backend!='r2_media')
    d.status='PURGED';d.media_state='Removed';managed(d);audit('Expired upload cleanup',d.name,reason)
    return {'status':'PURGED','released_bytes':d.bytes}

def remove_exact(provider,bucket,key,versioned=True):
    if not versioned:
        provider.delete_object(Bucket=bucket,Key=key)
        try:
            provider.head_object(Bucket=bucket,Key=key)
        except Exception as exc:
            if getattr(exc,'response',{}).get('ResponseMetadata',{}).get('HTTPStatusCode') != 404:
                raise
        else:
            frappe.throw('Remote object remains; quota is retained')
        return
    # Delete all versions of this exact random object key, never a prefix/bucket purge.
    result=provider.list_object_versions(Bucket=bucket,Prefix=key,MaxKeys=1000)
    if result.get('IsTruncated'):frappe.throw('Too many versions; operator reconciliation required')
    versions=[{'Key':v['Key'],'VersionId':v['VersionId']} for kind in ('Versions','DeleteMarkers')
        for v in result.get(kind,[]) if v['Key']==key]
    if versions:
        outcome=provider.delete_objects(Bucket=bucket,Delete={'Objects':versions,'Quiet':True})
        if outcome.get('Errors'):frappe.throw('Remote cleanup incomplete; quota remains reserved')
    remaining=provider.list_object_versions(Bucket=bucket,Prefix=key,MaxKeys=1000)
    if remaining.get('IsTruncated') or any(v['Key']==key for kind in ('Versions','DeleteMarkers') for v in remaining.get(kind,[])):
        frappe.throw('Remote objects remain; quota is retained')
