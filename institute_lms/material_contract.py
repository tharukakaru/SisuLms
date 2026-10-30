"""Bounded file validation and material access policy; no file execution."""
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile, BadZipFile

MAX_BYTES = 10 * 1024 * 1024
TYPES = {'txt':'text/plain', 'pdf':'application/pdf', 'ppt':'application/vnd.ms-powerpoint',
         'pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
         'doc':'application/msword', 'docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
PAPER_TYPES = {**TYPES, 'xls':'application/vnd.ms-excel',
    'xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'png':'image/png', 'jpg':'image/jpeg', 'jpeg':'image/jpeg', 'webp':'image/webp'}
PAPER_INLINE = {'pdf', 'txt', 'png', 'jpg', 'jpeg', 'webp'}


def validate_file(filename, content, preview=False, paper=False):
    if not isinstance(filename,str) or not filename or len(filename)>180 or any(c in filename for c in '/\\\r\n\x00'):
        raise ValueError('Use a simple filename of at most 180 characters')
    suffix=filename.rsplit('.',1)[-1].lower()
    types = PAPER_TYPES if paper else TYPES
    if suffix not in types or (preview and suffix!='pdf'):raise ValueError('Unsupported document format; PDF previews must be PDF')
    if not isinstance(content,bytes) or not content or len(content)>MAX_BYTES:raise ValueError('Choose a nonempty document of at most 10 MB')
    if suffix=='txt':
        if b'\x00' in content:raise ValueError('Plain text must not contain binary data')
        try:content.decode('utf-8-sig')
        except UnicodeDecodeError:raise ValueError('Plain text must use UTF-8') from None
    if suffix=='pdf' and not content.startswith(b'%PDF-'):raise ValueError('File is not a PDF')
    if suffix in ('ppt','doc','xls') and not content.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):raise ValueError('Invalid legacy Office file')
    if suffix in ('pptx','docx','xlsx'):
        try:
            with ZipFile(BytesIO(content)) as archive:
                entries=archive.infolist();names={e.filename for e in entries}
                required={'pptx':'ppt/presentation.xml','docx':'word/document.xml','xlsx':'xl/workbook.xml'}[suffix]
                if len(entries)>2000 or sum(e.file_size for e in entries)>50*1024*1024:raise ValueError('Office document is too complex; use a smaller file')
                if required not in names or '[Content_Types].xml' not in names:raise ValueError('Invalid Office document type')
                for e in entries:
                    path=PurePosixPath(e.filename)
                    if path.is_absolute() or '..' in path.parts or '\\' in e.filename or e.flag_bits&1 or 'vbaproject' in e.filename.lower():raise ValueError('Encrypted or macro-bearing Office files are not supported')
        except BadZipFile:raise ValueError('Invalid Office archive') from None
    if suffix in ('png','jpg','jpeg','webp'):
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(BytesIO(content)) as image:
                expected={'png':'PNG','jpg':'JPEG','jpeg':'JPEG','webp':'WEBP'}[suffix]
                if image.format != expected or image.width*image.height>20_000_000:
                    raise ValueError('Use a valid image of at most 20 megapixels')
                image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError('Invalid or oversized image') from exc
    return suffix,types[suffix]


def require_download(policy, role):
    if role=='Student' and policy!='Downloadable':raise PermissionError('Your teacher has made this material view only')


def require_preview(suffix, preview_file, policy):
    if policy not in ('View only','Downloadable'):raise ValueError('Choose View only or Downloadable')
    if suffix!='pdf' and policy=='View only' and not preview_file:raise ValueError('Add a matching PDF preview for view-only PowerPoint or Word materials')
