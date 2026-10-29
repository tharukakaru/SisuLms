import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch,MagicMock
from PIL import Image
from institute_lms.slip_ocr import image_text
class SlipOCR(unittest.TestCase):
    def test_unconfigured_is_explicit_and_does_not_spawn(self):
        with patch('subprocess.run') as run:
            text,mode=image_text(b'not read',None);self.assertEqual(text,'');self.assertIn('configure',mode);run.assert_not_called()
    def test_only_configured_local_executable_is_used_without_shell(self):
        with TemporaryDirectory() as folder:
            exe=Path(folder)/'tesseract';exe.write_text('test stub')
            data=BytesIO();Image.new('RGB',(50,50),'white').save(data,format='PNG')
            with patch('subprocess.run',return_value=MagicMock(returncode=0,stdout=b'LKR 1,200.00')) as run:
                text,mode=image_text(data.getvalue(),str(exe));self.assertIn('1,200.00',text);self.assertFalse(run.call_args.kwargs['shell']);self.assertEqual(run.call_args.kwargs['timeout'],20)
    def test_relative_executable_rejected(self):
        with self.assertRaises(ValueError):image_text(b'data','tesseract')
