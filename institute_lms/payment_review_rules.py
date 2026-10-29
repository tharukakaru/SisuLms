REJECTION_REASONS=('Slip is unclear or unreadable','Incorrect payment amount','Payment not received','Incorrect bank account','Duplicate or previously used slip','Wrong class or invoice','Other')

def review_note(decision,note,reason=''):
    note=str(note or '').strip()
    if len(note)>800:raise ValueError('Keep the review note within 800 characters')
    if decision=='Rejected':
        if reason not in REJECTION_REASONS:raise ValueError('Select a rejection reason')
        if reason=='Other' and not note:raise ValueError('Explain the rejection reason')
        return reason+(': '+note if note else '')
    if not note:raise ValueError('Record how you verified the bank payment')
    return note
