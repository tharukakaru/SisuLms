"""Programme grading policy, independent of transport and database permissions."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def weight(value=90):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('Assessment weight must be between 0 and 100') from None
    if not result.is_finite() or not 0 <= result <= 100:
        raise ValueError('Assessment weight must be between 0 and 100')
    return result


def percentage(score, maximum):
    try:
        score, maximum = Decimal(str(score)), Decimal(str(maximum))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not score.is_finite() or not maximum.is_finite() or maximum <= 0 or not 0 <= score <= maximum:
        return None
    return score * 100 / maximum


def module_grade(assessments, attendance, assessment_weight=90):
    """Each assessment is equally weighted after normalization.

    An unmarked submission counts for completion but leaves the grade provisional.
    Attendance contains one status per scheduled non-cancelled session: future or
    unrecorded sessions use None. Excused sessions are removed from the denominator.
    Neither attendance nor passing a test is a prerequisite for completion.
    """
    aw = weight(assessment_weight)
    missing = sum(not a.get('submitted') for a in assessments)
    scores = [percentage(a.get('score'), a.get('maximum')) if a.get('graded') else None for a in assessments]
    pending_marks = sum(v is None for v in scores)
    assessment_score = sum((v or Decimal(0) for v in scores), Decimal(0)) / len(scores) if scores else None
    counted = [s for s in attendance if s != 'Excused']
    pending_attendance = sum(s not in ('Present', 'Absent') for s in counted)
    attendance_score = Decimal(100) * counted.count('Present') / len(counted) if counted else None
    if attendance_score is None:
        aw = Decimal(100)
    if assessment_score is None:
        aw = Decimal(0)
    provisional = bool(missing or (pending_marks and aw > 0) or (pending_attendance and aw < 100))
    score = None
    if assessment_score is not None or attendance_score is not None:
        score = ((assessment_score or Decimal(0)) * aw + (attendance_score or Decimal(0)) * (100 - aw)) / 100
        score = float(score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    return {'can_complete': missing == 0, 'missing_submissions': missing,
            'score': score, 'provisional': provisional, 'pending_marks': pending_marks,
            'pending_attendance': pending_attendance,
            'assessment_percentage': float(assessment_score) if assessment_score is not None else None,
            'attendance_percentage': float(attendance_score) if attendance_score is not None else None,
            'assessment_weight': float(aw), 'attendance_weight': float(100 - aw)}
