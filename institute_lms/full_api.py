"""Versioned shared web/mobile capabilities; presentation is not authorization."""
import frappe

@frappe.whitelist()
def capabilities():
    from .api import identity
    from .api import identity
    from .account_billing import policy
    inst,member=identity()
    p=policy()
    return dict(api_version=4,role=member.role,organization=inst.title,plan=p['plan'],state=p['state'],premium_ai=False,ai_tools=[],organization_available=p['available'],locked_reason=p['locked_reason'],revision=1,entitlements=p['features'],features=[k for k,v in p['features'].items() if v])
