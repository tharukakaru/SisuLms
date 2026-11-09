"""Read the one configured catalogue on this Bench, without changing request identity.

Only the source site's owner API can publish. Consumer connections execute one
fixed SELECT in a read-only transaction; no request-controlled database or path.
"""
import json
import re
from pathlib import Path
import frappe
from .plan_catalog_rules import validate, defaults

def source_site():
    return getattr(frappe, 'conf', {}).get('il_plan_catalog_source_site')

def require_source_writer():
    source=source_site()
    if source and source!=frappe.local.site:
        frappe.throw('Publish shared plans from the Platform owner website.', frappe.PermissionError)

def read_source():
    source=source_site()
    if not source or source==frappe.local.site:return None
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9.-]+',source) or '..' in source:
        raise RuntimeError('Invalid catalogue source configuration')
    cached=getattr(frappe.local,'sisu_shared_plan_catalog',None)
    if cached is not None:return cached
    import pymysql
    sites=Path(frappe.get_site_path()).resolve().parent
    config=json.loads((sites/'common_site_config.json').read_text())
    config.update(json.loads((sites/source/'site_config.json').read_text()))
    if config.get('db_type','mariadb')!='mariadb':raise RuntimeError('Catalogue source requires MariaDB')
    connection=pymysql.connect(host=config.get('db_host') or '127.0.0.1',port=int(config.get('db_port') or 3306),
        user=config.get('db_user') or config['db_name'],password=config['db_password'],database=config['db_name'],
        unix_socket=config.get('db_socket'),charset='utf8mb4',connect_timeout=5,read_timeout=5,write_timeout=5)
    try:
        with connection.cursor() as cursor:
            cursor.execute('START TRANSACTION READ ONLY')
            cursor.execute('SELECT payload, revision FROM `tabIL Plan Catalog` WHERE name=%s',('current',))
            row=cursor.fetchone()
        value=dict(plans=validate(json.loads(row[0])) if row else defaults(),revision=int(row[1]) if row else 0)
    finally:
        connection.close()
    frappe.local.sisu_shared_plan_catalog=value
    return value
