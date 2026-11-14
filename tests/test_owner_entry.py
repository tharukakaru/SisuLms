import unittest
from html import escape
from types import SimpleNamespace as NS
from urllib.parse import urlsplit
from test_upload_provisioning import function


class OwnerEntry(unittest.TestCase):
    def setUp(self):
        self.config = {'il_control_plane': 1, 'host_name': 'http://127.0.0.1:5401',
                       'il_student_campus_url': 'http://127.0.0.1:5400/campus'}
        self.url = function('portal_entry', 'student_campus_url', {'urlsplit': urlsplit})

    def test_explicit_local_navigation(self):
        self.assertEqual(self.url(self.config), 'http://127.0.0.1:5400/campus')

    def test_campus_site_does_not_advertise_owner_navigation(self):
        self.assertEqual(self.url(dict(self.config, il_control_plane=0)), '')

    def test_no_guessed_production_destination(self):
        self.assertEqual(self.url({'il_control_plane': 1}), '')

    def test_https_destination(self):
        self.assertEqual(self.url(dict(self.config, il_student_campus_url='https://school.example/campus')),
                         'https://school.example/campus')

    def test_reject_unsafe_destinations(self):
        for url in ('javascript:alert(1)', '//evil.example', 'http://public.example/campus',
                    'http://localhost:5400/campus', 'https://user:password@example.com',
                    'https://example.com:bad', 'https://example.com/#secret',
                    'https://example.com/ with space', 'https://example.com\\evil'):
            with self.subTest(url=url):
                self.assertEqual(self.url(dict(self.config, il_student_campus_url=url)), '')
        self.assertEqual(self.url(dict(self.config, host_name='https://platform.example')), '')

    def test_owner_guest_redirect_only(self):
        class Redirect(Exception): pass
        flags=NS()
        f=NS(conf=self.config, session=NS(user='Guest'), local=NS(flags=flags), Redirect=Redirect)
        redirect=function('portal_entry', 'redirect_owner_guest', {'frappe':f})
        with self.assertRaises(Redirect) as caught: redirect()
        self.assertEqual(caught.exception.args, (302,))
        self.assertEqual(flags.redirect_location, '/login?redirect-to=/campus')
        for control_plane,user in ((1,'owner@example.invalid'),(0,'Guest'),(0,'student@example.invalid')):
            f.conf={'il_control_plane':control_plane};f.session.user=user
            self.assertIsNone(redirect())

    def test_public_identity_exposes_only_navigation(self):
        f=NS(conf=dict(self.config, api_secret='must-not-leak'))
        public=function('portal_entry', 'public', {'frappe':f,'student_campus_url':self.url})
        self.assertEqual(public(), {'control_plane':True, 'student_campus_url':'http://127.0.0.1:5400/campus'})


    def test_auth_branding_is_server_rendered(self):
        f=NS(conf=self.config, local=NS(request=NS(path='/login/')))
        decorate=function('portal_entry','website_context',{'frappe':f,'student_campus_url':self.url,'escape':escape})
        ctx={'body_class':'existing','head_html':'<meta name="existing">'}
        decorate(ctx)
        self.assertEqual(ctx['body_class'],'existing sisu-login sisu-owner-login')
        self.assertIn('http://127.0.0.1:5400/campus',ctx['head_html'])
        self.assertTrue(ctx['head_html'].startswith('<meta name="existing">'))
        self.assertIn('sisu-icon.png',ctx['logo'])
        self.assertTrue(ctx['sisu_auth_page'])
        self.assertTrue(ctx['sisu_owner_entry'])
        self.assertFalse(ctx['sisu_password_reset'])
        self.assertEqual(ctx['sisu_student_campus'],'http://127.0.0.1:5400/campus')
        f.conf={'il_control_plane':0};f.local.request.path='/update-password'
        ctx={};decorate(ctx)
        self.assertEqual(ctx['body_class'],'sisu-login')
        self.assertTrue(ctx['sisu_password_reset'])
        self.assertFalse(ctx['sisu_owner_entry'])
        self.assertNotIn('sisu-owner-login',ctx['body_class'])
        f.local.request.path='/campus';ctx={};decorate(ctx)
        self.assertEqual(ctx,{})

    def test_auth_metadata_escapes_attribute_content(self):
        f=NS(conf=self.config,local=NS(request=NS(path='/login')))
        decorate=function('portal_entry','website_context',{'frappe':f,'student_campus_url':lambda _: 'https://example.com/?q="test"&next=campus','escape':escape})
        ctx={};decorate(ctx)
        self.assertIn('&quot;test&quot;&amp;next=campus',ctx['head_html'])
