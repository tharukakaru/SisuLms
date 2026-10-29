"""Server-configured provider interfaces; never report success for absent adapters."""
import requests
import frappe

def sms(phone, body, idempotency_key=None):
    hooks=frappe.get_hooks('il_send_verification_sms')
    path=frappe.conf.get('il_sms_adapter')
    if path:
        result=frappe.get_attr(path)(phone=phone,message=body,idempotency_key=idempotency_key)
        if not isinstance(result,dict) or not (result.get('provider_id') or result.get('accepted') is True):frappe.throw('SMS provider did not confirm acceptance')
        return result
    if hooks and idempotency_key is None:
        frappe.get_attr(hooks[0])(phone=phone,message=body)
        return {'accepted':True}  # legacy trusted OTP hook must throw on failure
    frappe.throw('SMS provider adapter is not configured')

def whatsapp_code(phone,code):
    template=frappe.conf.get('il_whatsapp_auth_template') or {}
    token=frappe.conf.get('il_whatsapp_token');phone_id=frappe.conf.get('il_whatsapp_phone_id');version=frappe.conf.get('il_whatsapp_graph_version')
    if not all((token,phone_id,version,template.get('name'),template.get('language'))):frappe.throw('WhatsApp authentication provider is not configured')
    try:
        r=requests.post(f'https://graph.facebook.com/{version}/{phone_id}/messages',headers={'Authorization':'Bearer '+token},timeout=(5,15),allow_redirects=False,
            json={'messaging_product':'whatsapp','to':phone.lstrip('+'),'type':'template','template':{'name':template['name'],'language':{'code':template['language']},
                  'components':[{'type':'body','parameters':[{'type':'text','text':code}]},{'type':'button','sub_type':'url','index':'0','parameters':[{'type':'text','text':code}]}]}})
        if not r.ok or not r.json().get('messages'):frappe.throw('WhatsApp did not confirm acceptance')
    except (requests.RequestException,ValueError):frappe.throw('WhatsApp delivery uncertain; wait before retrying')

def push(token, platform, body, idempotency_key):
    adapter=frappe.conf.get('il_push_adapter')
    if not adapter:frappe.throw('Push provider adapter is not configured')
    result=frappe.get_attr(adapter)(token=token,platform=platform,body=body,idempotency_key=idempotency_key)
    if not isinstance(result,dict) or not result.get('provider_id'):frappe.throw('Push provider did not confirm acceptance')
    return result
