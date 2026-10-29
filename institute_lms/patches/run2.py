"""Non-destructive AI schema initialization. No provider calls or automatic indexing."""
import frappe

def execute():
    for dt,fields in {'IL AI Conversation':['user','institute','status'], 'IL AI Message':['conversation','creation'],
        'IL AI Usage':['institute','period','feature'],'IL Knowledge Document':['classroom','enabled','status'],
        'IL Knowledge Chunk':['document','ordinal'],'IL Knowledge Index':['classroom','status']}.items():
        frappe.db.add_index(dt,fields)
    frappe.db.add_unique('IL AI Message',['conversation','request_key','role'])
    frappe.db.add_unique('IL Knowledge Chunk',['document','ordinal'])
