"""Create two named bank-slip practice fixtures; never change existing payments."""
import os
from unittest.mock import patch
os.chdir('/home/sisu/frappe-bench/sites')
import frappe
frappe.init(site='sisuacademylk.com');frappe.connect()
try:
    from institute_lms import programme_courses,teaching
    from institute_lms.campus_context import SESSION_KEY
    inst=frappe.db.get_value('IL Institute',{'code':'SISUDEMO'},'name')
    admin='sisu.student.test+institute.admin@gmail.com'
    teacher='sisu.student.test+institute.teacher@gmail.com'
    student='sisu.student.test@gmail.com'
    assert inst
    for user in (admin,teacher,student):assert frappe.db.get_value('User',user,'enabled')
    t=frappe.db.get_value('IL Member',{'user':teacher,'institute':inst,'active':1,'role':'Teacher'},'name')
    assert t and frappe.db.exists('IL Member',{'user':student,'institute':inst,'active':1,'role':'Student'})
    frappe.set_user(admin);frappe.session.data[SESSION_KEY]=inst
    title='[TEST] Bank-slip practice class'
    room=frappe.db.get_value('IL Classroom',{'institute':inst,'title':title},'name')
    if not room:
        source=frappe.get_doc('IL Classroom','fp20kd7lgd')
        assert source.institute==inst and source.teacher==t
        copy=frappe.copy_doc(source)
        copy.update({'title':title,'subject':'Science','description':'Payment workflow testing only. Do not transfer real money.','programme':None,'billing_type':'One-time','fee_mode':'Paid','fee':100,'published':1,'active':1,'access_duration_days':30,'grade':'O/L','teaching_medium':'Sinhala','cover_image':'/assets/institute_lms/demo/physics.png'})
        copy.insert(ignore_permissions=True);room=copy.name
    title='[TEST] Bank-slip practice programme'
    course=frappe.db.get_value('IL Programme',{'institute':inst,'title':title},'name')
    with patch('institute_lms.notification_service.emit',return_value=None):
        if not course:
            course=programme_courses.create({'title':title,'description':'Payment workflow testing only. Do not transfer real money.','fee':100,'access_duration_days':30,'modules':[{'module_code':programme_courses.module_code(),'title':'Practice module','teacher':t,'duration_weeks':2,'assessment_weight':90}]})
    # Create only the named test student's unpaid enrollment through normal billing.
    from institute_lms.api import enroll,access
    learner=frappe.db.get_value('IL Member',{'user':student,'institute':inst,'active':1,'role':'Student'},'name')
    existing=frappe.db.get_value('IL Enrollment',{'classroom':room,'student':learner},'name')
    if not existing:
        with patch('institute_lms.notification_service.emit',return_value=None):
            enrollment=enroll({'classroom':room,'student':learner,'installments':[{'amount':100,'due_date':frappe.utils.today()}]})
        assert frappe.db.exists('IL Invoice',{'enrollment':enrollment,'status':'Unpaid'})
        assert not access(frappe.get_doc('IL Classroom',room),frappe.get_doc('IL Member',learner))['allowed']
    frappe.db.commit()
    print('READY: locked LKR 100 practice class '+room+' and programme '+course+' in SISUDEMO.')
    print('Named student practice enrollment is prepared; existing enrollments/invoices are unchanged. No payment approved or message sent. Select SISUDEMO or its provider to find the fixtures; use a clearly labelled test slip, not a real transfer.')
except Exception:
    frappe.db.rollback();raise
finally:frappe.destroy()
