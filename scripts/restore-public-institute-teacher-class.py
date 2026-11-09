"""Restore only the operator-requested test assignment, without changing credentials."""
import os
from pathlib import Path


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com'); frappe.connect()
    try:
        frappe.set_user('Administrator')
        inst = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO'}, 'name')
        member = frappe.db.get_value('IL Member', {'institute': inst,
            'user': 'sisu.student.test+institute.teacher@gmail.com', 'role': 'Teacher', 'active': 1}, 'name')
        room = frappe.get_doc('IL Classroom', 'fp20kd7lgd', for_update=True)
        if not member or room.institute != inst or room.teacher != member or room.owner_type != 'Institute' or room.title != '[TEST] Institute teacher assigned practice':
            raise RuntimeError('Named test assignment conflict; no change made')
        from institute_lms.teaching import approved_teacher
        approved_teacher(frappe.get_doc('IL Institute', inst), member, room.public_provider)
        if room.teacher_assignment_active:
            print('READY: named test assignment already active.')
        else:
            room.teacher_assignment_active = 1
            room.save(ignore_permissions=True)
            room.add_comment('Info', 'Restored named public institute-teacher test assignment at operator request.')
            frappe.db.commit()
            print('RESTORED: fp20kd7lgd to the existing institute test teacher.')
        print('No password, role, membership, payment or other classroom changed.')
    finally:
        frappe.db.rollback(); frappe.destroy()


if __name__ == '__main__': main()
