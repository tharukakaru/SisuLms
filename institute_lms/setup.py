import frappe


def after_install():
    for role in ("Institute Admin", "Institute Teacher", "Institute Student"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 0}).insert(ignore_permissions=True)
    add_indexes()
    from .patches.run1 import execute
    execute()
    from .patches.run2 import execute as run2
    run2()
    from .patches.final_build import execute as final_build
    final_build()
    from .patches.release_v2 import execute as release_v2
    release_v2()


def add_indexes():
    for doctype, columns in {
        "IL Wallet": ["owner_user", "currency"],
        "IL Price Assignment": ["customer", "product", "active"],
        "IL Product Entitlement": ["customer", "product", "expires_at"],
        "IL Checkout Quote": ["customer", "expires_at"],
        "IL Paper": ["institute", "classroom", "status"],
        "IL Paper Attempt": ["paper", "student", "status"],
        "IL Attendance": ["institute", "classroom", "session"],
        "IL Support Ticket": ["institute", "requester", "status"],
        "IL Support Reply": ["ticket", "creation"],
        "IL Wallet Transaction": ["wallet", "creation"],
        "IL Payout Request": ["region", "status", "creation"],
        "IL Public Profile": ["status", "kind"],
        "IL Profile Relationship": ["profile", "status", "kind"],
        "IL Member": ["institute", "user", "active"],
        "IL Classroom": ["institute", "teacher"],
        "IL Session": ["classroom", "starts_at"],
        "IL Enrollment": ["classroom", "student"],
        "IL Invoice": ["student", "status", "due_date"],
        "IL Notification": ["channel", "status", "next_attempt"],
        "IL Calendar Job": ["status", "next_attempt"],
    }.items():
        frappe.db.add_index(doctype, columns)
    frappe.db.add_index('IL Price Assignment',['tenant_id','product','active'])
    frappe.db.sql("UPDATE `tabIL Notification` SET channel='WhatsApp' WHERE channel IS NULL OR channel=''")
    frappe.db.add_unique("IL Programme Enrollment", ["programme", "student"])
    frappe.db.sql("UPDATE `tabIL Classroom` SET owner_type='Institute' WHERE owner_type IS NULL OR owner_type=''")
    frappe.db.sql("UPDATE `tabIL Classroom` SET teacher_assignment_active=1 WHERE teacher_assignment_active IS NULL")
    frappe.db.add_unique("IL Enrollment", ["classroom", "student"])
    frappe.db.add_unique("IL Member", ["institute", "user"])
    frappe.db.add_unique("IL Institute Bill", ["institute", "period"])
    frappe.db.add_unique("IL YouTube Connection", ["member"])
    frappe.db.add_index("IL Classroom", ["institute", "active", "published", "public_provider"])


def configure(code, title, admin_email, base_fee=0):
    """Bench-only first-site setup; deliberately not whitelisted."""
    from .domain import institute_code, money
    code = institute_code(code)
    if frappe.db.count("IL Institute"):
        frappe.throw("This site already has an institute")
    if not frappe.db.exists("User", admin_email):
        frappe.throw("Create the institute administrator User first")
    doc = frappe.get_doc({"doctype": "IL Institute", "code": code, "title": title,
        "base_fee": money(base_fee), "billing_day": 1, "language": "en", "accent": "#6C6AEE"}).insert(ignore_permissions=True)
    user = frappe.get_doc("User", admin_email)
    user.append_roles("Institute Admin", "Moderator")
    user.save(ignore_permissions=True)
    member = frappe.get_doc({"doctype": "IL Member", "institute": doc.name, "user": admin_email,
        "full_name": user.full_name, "role": "Admin", "active": 1, "language": "en"})
    member.insert(ignore_permissions=True, set_name=f"AD-{code}-0001")
    frappe.db.set_single_value("System Settings", "time_zone", "Asia/Colombo")
    frappe.db.commit()
    return {"institute": doc.name, "code": code}
