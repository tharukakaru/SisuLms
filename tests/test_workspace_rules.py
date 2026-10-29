import unittest
from io import BytesIO
from datetime import date,timedelta
from institute_lms.workspace_rules import expense,settings,review,vimeo_embed
from institute_lms.slip_analysis import compare_text
from institute_lms.commercial_rules import plan_features,PLANS
class WorkspaceRules(unittest.TestCase):
    def test_all_plans_keep_study_and_news_remains_premium(self):
        for name in PLANS:
            self.assertTrue(plan_features(name)['study'])
            self.assertEqual(plan_features(name)['news'],name in ('Gold','Platinum'))
    def test_expense_money_and_dates(self):
        data=dict(amount='1200.25',date=date.today().isoformat(),category='Teaching',note='Tutor expenses',token='submission-123')
        self.assertEqual(expense(data)['amount_minor'],120025)
        for bad in ('NaN','Infinity','-1','0','1.001','100000001'):
            with self.assertRaises(ValueError):expense(dict(data,amount=bad))
        with self.assertRaises(ValueError):expense(dict(data,date=(date.today()+timedelta(days=1)).isoformat()))
        with self.assertRaises(ValueError):expense(dict(data,category='invalid'))
    def test_limits_and_platinum_boundary(self):
        data=dict(document_views=3,video_views=4,concurrent_sessions=2,pdf_watermark=True,accent='#aabbcc',display_name='Academy')
        self.assertFalse(settings(data)['pdf_watermark']);self.assertEqual(settings(data)['display_name'],'')
        self.assertTrue(settings(data,True)['pdf_watermark'])
        for bad in (-1,1.5,1001,True):
            with self.assertRaises(ValueError):settings(dict(data,document_views=bad))
        with self.assertRaises(ValueError):settings(dict(data,accent='url(evil)'))
    def test_vimeo_allowlist_preserves_unlisted_privacy_hash(self):
        self.assertEqual(vimeo_embed('https://vimeo.com/123456/abc123'),'https://player.vimeo.com/video/123456?h=abc123')
        self.assertEqual(vimeo_embed('https://player.vimeo.com/video/123456?h=abc123'),'https://player.vimeo.com/video/123456?h=abc123')
        for url in ('javascript:alert(1)','https://vimeo.com.evil.test/123','https://attacker@vimeo.com/123','http://vimeo.com/123'):
            with self.assertRaises(ValueError):vimeo_embed(url)
    def test_review_ratings(self):
        self.assertEqual(review(dict(rating=5,body='A useful practical lesson'))['rating'],5)
        for n in (0,6,1.5,True):
            with self.assertRaises(ValueError):review(dict(rating=n,body='A useful practical lesson'))
    def test_slip_checks_are_evidence_not_approval(self):
        result=compare_text('LKR 8,000.00 Ref: ABC-42 17/10/2026',800000,'ABC42','2026-10-17')
        self.assertTrue(all(result.values()));self.assertNotIn('approved',result)
        self.assertFalse(compare_text('',800000,'ABC42','2026-10-17')['amount_match'])
    def test_pdf_watermark_keeps_original_and_adds_student_label(self):
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader
        from institute_lms.pdf_watermark import watermark
        source=BytesIO();c=canvas.Canvas(source);c.drawString(50,700,'Class notes');c.showPage();c.save()
        raw=source.getvalue();marked=watermark(raw,'SISU | ST-001 | 2026-10-17')
        self.assertNotEqual(raw,marked)
        self.assertNotIn('ST-001',PdfReader(BytesIO(raw)).pages[0].extract_text())
        self.assertIn('ST-001',PdfReader(BytesIO(marked)).pages[0].extract_text())
        self.assertIn('Class notes',PdfReader(BytesIO(marked)).pages[0].extract_text())
