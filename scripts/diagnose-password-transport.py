"""Probe HTTPS reset transport with a verified nonexistent random key. No real password is used."""
import os,json,secrets,hashlib,time
from urllib.request import Request,build_opener,HTTPCookieProcessor,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from urllib.parse import urlsplit
ORIGIN='https://platform.sisuacademylk.com'
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
class Meta(HTMLParser):
 def __init__(self):super().__init__();self.token=''
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta' and a.get('name')=='csrf-token':self.token=a.get('content','')
def report(response,stage):
 data=response.read(1048576);out={'stage':stage,'http_status':response.code,'content_type':response.headers.get('Content-Type','')}
 loc=response.headers.get('Location')
 if loc:
  u=urlsplit(loc);out['redirect']={'scheme':u.scheme,'host':u.hostname,'path':u.path}
 try:
  value=json.loads(data);out['exception_type']=value.get('exc_type');out['has_exception']=bool(value.get('exc'))
 except (ValueError,UnicodeDecodeError):pass
 print(json.dumps(out))
 return data

def main():
 os.chdir('/home/sisu/frappe-bench/sites')
 import frappe
 frappe.init(site='platform.sisuacademylk.com');frappe.connect()
 try:
  key=secrets.token_hex(32)
  assert not frappe.db.exists('User',{'reset_password_key':hashlib.sha256(key.encode()).hexdigest()})
  assert not frappe.db.exists('User',{'reset_password_key':key})
 finally:frappe.db.rollback();frappe.destroy()
 opener=build_opener(HTTPCookieProcessor(CookieJar()),NoRedirect())
 try:
  with opener.open(Request(ORIGIN+'/sisu_password',headers={'User-Agent':'SISU-transport-diagnostic'}),timeout=25) as r:html=report(r,'GET password form')
  meta=Meta();meta.feed(html.decode('utf-8','replace'))
  print(json.dumps({'csrf_meta_present':bool(meta.token and meta.token not in ('None','undefined'))}))
  body=json.dumps({'new_password':secrets.token_urlsafe(32)+'aA!9','key':key,'logout_all_sessions':0}).encode()
  headers={'Content-Type':'application/json','X-Frappe-CSRF-Token':meta.token,'Origin':ORIGIN,'Referer':ORIGIN+'/sisu_password','User-Agent':'SISU-transport-diagnostic'}
  started=time.monotonic()
  try:
   with opener.open(Request(ORIGIN+'/api/method/frappe.core.doctype.user.user.update_password',data=body,headers=headers,method='POST'),timeout=35) as r:report(r,'POST nonexistent reset key')
  except HTTPError as e:report(e,'POST nonexistent reset key')
  print(json.dumps({'post_elapsed_seconds':round(time.monotonic()-started,2)}))
 except HTTPError as e:report(e,'GET password form')
 except Exception as exc:print(json.dumps({'transport_error':type(exc).__name__,'reason_type':type(getattr(exc,'reason',None)).__name__}))
 print('No real reset key or password used or printed. A nonexistent random key cannot select a user. No mail sent or configuration changed; the rejected probe may appear in request/rate-limit logs.')
if __name__=='__main__':main()
