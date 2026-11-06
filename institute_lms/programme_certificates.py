"""Private course templates and completion-authorized personalized PDF downloads."""
from io import BytesIO
import secrets
import frappe


@frappe.whitelist(methods=['POST'])
def upload(kind, classroom=None):
    from .api import identity, require_role
    from .material_contract import MAX_BYTES, validate_file
    from .registration import limit
    from frappe.utils.file_manager import save_file
    inst, member = identity()
    if classroom and kind in ('cover_image', 'profile_image'):
        from .api import classroom_for
        inst, member, room = classroom_for(classroom, write=True)
        if not room.get('programme'): frappe.throw('Programme module required')
    else:
        require_role(member, 'Admin')
    if kind not in ('cover_image', 'profile_image', 'certificate_template', 'certificate_preview'):
        frappe.throw('Invalid programme upload')
    limit('programme-upload:' + member.user)
    item = frappe.request.files.get('file')
    if not item: frappe.throw('Choose a file')
    raw = item.stream.read(MAX_BYTES + 1)
    try:
        suffix, _ = validate_file(item.filename, raw, preview=kind == 'certificate_preview')
        if kind in ('cover_image', 'profile_image') and suffix not in ('png', 'jpg', 'jpeg'):
            raise ValueError('Choose a PNG or JPEG image')
    except ValueError as error:
        frappe.throw(str(error))
    if suffix == 'pdf':
        from pypdf import PdfReader
        try:
            pdf = PdfReader(BytesIO(raw))
            if pdf.is_encrypted or not 1 <= len(pdf.pages) <= 5: raise ValueError()
        except Exception:
            frappe.throw('Choose a valid, unencrypted certificate PDF with 1–5 pages')
    public = kind in ('cover_image', 'profile_image')
    if public:
        from PIL import Image, ImageOps
        with Image.open(BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            image.thumbnail((1600, 1000))
            output = BytesIO()
            image.save(output, 'JPEG', quality=90)
            raw, suffix = output.getvalue(), 'jpg'
    file = save_file('programme-' + secrets.token_hex(12) + '.' + suffix, raw,
                     'IL Institute', inst.name, is_private=0 if public else 1)
    return {'file_id': file.name, 'url': file.file_url if public else None, 'type': suffix}


def template_file(name, institute):
    file = frappe.get_doc('File', name)
    if (file.owner != frappe.session.user or not file.is_private or
            file.attached_to_doctype != 'IL Institute' or file.attached_to_name != institute):
        frappe.throw('Upload your own institute certificate template', frappe.PermissionError)
    return file


def configure(programme, data):
    from pathlib import PurePosixPath
    source = data.get('certificate_template')
    if not source: return
    original = template_file(source, programme.institute)
    render = template_file(data['certificate_preview'], programme.institute) if data.get('certificate_preview') else original
    if PurePosixPath(render.file_name).suffix.lower() not in ('.pdf', '.png', '.jpg', '.jpeg'):
        frappe.throw('Add a matching PDF preview for an Office or text certificate template')
    programme.certificate_template = original.name
    programme.certificate_preview = render.name
    for field in ('certificate_name_x', 'certificate_name_y'):
        try:
            value = float(data.get(field, 50))
            if not 0 <= value <= 100: raise ValueError()
        except (ValueError, TypeError):
            frappe.throw('Certificate name position must be between 0 and 100 percent')
        programme.set(field, value)


def render_certificate(raw, suffix, student, x=50, y=50):
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    if suffix == '.pdf':
        reader = PdfReader(BytesIO(raw))
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 5:
            raise ValueError('Use an unencrypted certificate PDF with 1–5 pages')
        page = reader.pages[0]
        width, height = float(page.mediabox.width), float(page.mediabox.height)
    else:
        with Image.open(BytesIO(raw)) as image:
            width, height = image.size
            scale = min(1, 1000 / max(width, height))
            width, height = width * scale, height * scale
        base = BytesIO()
        c = canvas.Canvas(base, pagesize=(width, height))
        c.drawImage(ImageReader(BytesIO(raw)), 0, 0, width=width, height=height)
        c.save()
        reader = PdfReader(BytesIO(base.getvalue()))
        page = reader.pages[0]
    writer = PdfWriter()
    for source_page in reader.pages:
        for key in ('/Annots', '/AA'):
            if key in source_page: del source_page[key]
        writer.add_page(source_page)
    page = writer.pages[0]
    overlay = BytesIO()
    c = canvas.Canvas(overlay, pagesize=(width, height))
    # Frappe's installed fonts support Unicode names when available.
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pathlib import Path
    fonts = [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('C:/Windows/Fonts/arial.ttf')]
    font = 'Helvetica'
    for path in fonts:
        if path.exists():
            if 'ProgrammeName' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('ProgrammeName', str(path)))
            font = 'ProgrammeName'
            break
    size = min(28, max(10, width / 25))
    while size > 8 and pdfmetrics.stringWidth(student, font, size) > width * .85:
        size -= 1
    c.setFont(font, size)
    c.drawCentredString(width * x / 100, height * (1 - y / 100), student)
    c.save()
    page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@frappe.whitelist()
def download(programme):
    from pathlib import PurePosixPath
    from .api import identity, require_role, scoped
    from .programme_learning import purchase_for, completed_rooms
    inst, member = identity()
    require_role(member, 'Student')
    p = scoped('IL Programme', programme, inst)
    purchase = purchase_for(p.name, member.name)
    done = completed_rooms(purchase)
    if not purchase or not p.modules or not all(m.classroom in done for m in p.modules):
        frappe.throw('Complete every module before earning your certificate', frappe.PermissionError)
    if not p.get('certificate_preview'):
        frappe.throw('Your institute has not added a certificate template yet')
    file = frappe.get_doc('File', p.certificate_preview)
    if file.attached_to_doctype != 'IL Institute' or file.attached_to_name != inst.name or not file.is_private:
        frappe.throw('Certificate template unavailable', frappe.PermissionError)
    try:
        content = render_certificate(file.get_content(), PurePosixPath(file.file_name).suffix.lower(),
            member.full_name or member.user, p.certificate_name_x, p.certificate_name_y)
    except ValueError as error:
        frappe.throw(str(error))
    frappe.local.response.update({'type': 'download', 'filename': 'course-certificate.pdf',
        'filecontent': content, 'content_type': 'application/pdf', 'display_content_as': 'inline'})
