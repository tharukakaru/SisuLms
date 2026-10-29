"""Deterministic academic evidence. No private AI messages or personal profiling."""
import json
import frappe

def weakness_evidence(questions,answers,paper,attempt):
    evidence=[]
    for n,(q,a) in enumerate(zip(questions,answers)):
        if q.get('kind') in ('MCQ','True/False') and type(a) is int and a!=q.get('answer'):
            evidence.append({'topic':q.get('prompt','')[:180],'paper':paper,'attempt':attempt,'question':n+1,'reason':'Incorrect objectively scored answer','recommendation':'Practise this question and review its related lesson.'})
    return evidence

def recommendations_for(inst,member,room):
    rows=frappe.db.sql('''SELECT a.name,a.paper,a.answers,p.questions,p.title FROM `tabIL Paper Attempt` a
        JOIN `tabIL Paper` p ON p.name=a.paper WHERE a.student=%s AND a.status='Graded' AND p.institute=%s AND p.classroom=%s
        ORDER BY a.modified DESC LIMIT 30''',(member.name,inst.name,room.name),as_dict=True)
    evidence=[]
    for row in rows:
        evidence+=weakness_evidence(json.loads(row.questions),json.loads(row.answers or '[]'),row.paper,row.name)
    materials=frappe.get_all('IL Material',filters={'institute':inst.name,'classroom':room.name},fields=['name','title'],limit_page_length=50)
    for item in evidence[:20]:
        words={w.lower().strip('.,?') for w in item['topic'].split() if len(w)>4}
        item['suggested_materials']=[r for r in materials if words & {w.lower() for w in r.title.split()}][:3]
        item['matching_basis']='Shared title terms; no relevance claim when no material matches'
    return {'sufficient_evidence':bool(rows),'evidence':evidence[:20], 'message':'Review the questions with documented incorrect answers.' if evidence else 'Insufficient evidence to identify a review priority; no weakness is inferred.', 'basis':'Up to 30 graded attempts; no personality or intelligence inference'}

def aggregates(room):
    row=frappe.db.sql('''SELECT COUNT(*) attempts,COUNT(DISTINCT a.student) students,
        SUM(a.score) score,SUM(p.max_marks) maximum FROM `tabIL Paper Attempt` a
        JOIN `tabIL Paper` p ON p.name=a.paper WHERE p.institute=%s AND p.classroom=%s AND a.status='Graded' ''',(room.institute,room.name),as_dict=True)[0]
    if row.students<5:return {'sufficient_data':False,'reason':'At least five assessed students are required for class-level AI insights'}
    attendance=frappe.db.sql('SELECT status,COUNT(*) count FROM `tabIL Attendance` WHERE institute=%s AND classroom=%s GROUP BY status',(room.institute,room.name),as_dict=True)
    usage=frappe.db.sql('SELECT feature,COUNT(*) requests,SUM(total_tokens) tokens,SUM(charged_units) credits FROM `tabIL AI Usage` WHERE institute=%s AND classroom=%s GROUP BY feature',(room.institute,room.name),as_dict=True)
    attempts=frappe.db.sql('''SELECT a.student,a.answers,p.questions FROM `tabIL Paper Attempt` a
        JOIN `tabIL Paper` p ON p.name=a.paper WHERE p.institute=%s AND p.classroom=%s AND a.status='Graded'
        ORDER BY a.modified DESC LIMIT 200''',(room.institute,room.name),as_dict=True)
    difficulties={}
    for a in attempts:
        for evidence in weakness_evidence(json.loads(a.questions),json.loads(a.answers or '[]'),'',''):
            difficulties.setdefault(evidence['topic'],set()).add(a.student)
    topics=[{'question_topic':topic,'students_with_incorrect_answer':len(students)} for topic,students in difficulties.items() if len(students)>=5]
    topics.sort(key=lambda r:r['students_with_incorrect_answer'],reverse=True)
    return {'sufficient_data':True,'graded_attempts':row.attempts,'assessed_students':row.students,'weighted_score_percent':round(float(row.score or 0)*100/float(row.maximum),2) if row.maximum else None,'attendance':attendance,'ai_usage':usage,'practice_priorities':topics[:10],'topic_sample':'Most recent 200 graded attempts; labels are question prompts, not inferred topic classifications','scope':'Verified stored records only; no conversation content'}
