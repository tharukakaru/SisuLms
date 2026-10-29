"""Schema sync precedes this non-destructive, repeatable index patch."""
import frappe

def execute():
    for dt,columns in {
        'IL Commerce Event':['delivery_status','next_attempt'],
        'IL Subscription Notice':['tenant_id','acknowledged'],
        'IL Lecture Refund':['status'],
        'IL Paper Generation Job':['user','status'],
        'IL Stored Object':['institute','media_state','status'],
    }.items():frappe.db.add_index(dt,columns)
