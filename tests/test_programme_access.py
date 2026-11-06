from io import BytesIO
from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock
from test_upload_provisioning import function


class Doc(dict):
    __getattr__ = dict.get


class ProgrammeAccessTests(TestCase):
    def gate(self, completed=(), purchase='purchase', active=1, institute='inst'):
        programme = Doc(name='course', institute=institute, active=active, sequential_modules=1,
            modules=[Doc(classroom='first'), Doc(classroom='second')])
        frappe = NS(get_doc=lambda *args: programme)
        return function('programme_learning', 'access_reason', {
            'frappe': frappe, 'purchase_for': lambda *args: purchase,
            'completed_rooms': lambda *args: set(completed)})

    def test_direct_second_module_is_blocked(self):
        gate = self.gate()
        self.assertIn('preceding', gate(Doc(name='second', programme='course'), Doc(role='Student', name='s', institute='inst')))

    def test_first_and_completed_modules_remain_open(self):
        member = Doc(role='Student', name='s', institute='inst')
        self.assertIsNone(self.gate()(Doc(name='first', programme='course'), member))
        self.assertIsNone(self.gate(['first'])(Doc(name='second', programme='course'), member))
        self.assertIsNone(self.gate(['second'])(Doc(name='second', programme='course'), member))

    def test_no_purchase_or_foreign_institute_is_blocked(self):
        room, member = Doc(name='first', programme='course'), Doc(role='Student', name='s', institute='inst')
        self.assertIsNotNone(self.gate(purchase=None)(room, member))
        self.assertIsNotNone(self.gate(institute='foreign')(room, member))
        self.assertIsNotNone(self.gate(active=0)(room, member))

    def test_teachers_use_existing_teaching_permissions(self):
        self.assertIsNone(self.gate()(Doc(name='second', programme='course'), Doc(role='Teacher')))

    def test_initial_institute_payment_does_not_claim_trial_access(self):
        state = function('account_billing', 'state', {})
        self.assertEqual(state(NS(onboarding_payment_required=1, paid_until=None)),
                         {'state': 'Choose a plan', 'available': False})

    def test_certificate_personalizes_image_and_pdf(self):
        from PIL import Image
        from pypdf import PdfReader
        from reportlab.pdfgen.canvas import Canvas
        render = function('programme_certificates', 'render_certificate', {'BytesIO': BytesIO})
        image = BytesIO(); Image.new('RGB', (800, 500), 'white').save(image, 'PNG')
        pdf = BytesIO(); canvas = Canvas(pdf, pagesize=(800, 500)); canvas.drawString(20, 450, 'Course award'); canvas.save()
        for raw, suffix in ((image.getvalue(), '.png'), (pdf.getvalue(), '.pdf')):
            result = render(raw, suffix, 'Test Student')
            reader = PdfReader(BytesIO(result))
            self.assertEqual(len(reader.pages), 1)
            self.assertIn('Test Student', reader.pages[0].extract_text())
