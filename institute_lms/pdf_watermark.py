"""Watermark a delivered PDF without changing its stored original."""
from io import BytesIO
def watermark(raw,label):
    from pypdf import PdfReader,PdfWriter
    from reportlab.pdfgen import canvas
    reader=PdfReader(BytesIO(raw));writer=PdfWriter()
    if reader.is_encrypted:raise ValueError('Watermarked delivery requires an unencrypted PDF')
    if len(reader.pages)>500:raise ValueError('Watermarked PDFs must contain at most 500 pages')
    for original in reader.pages:
        page=writer.add_page(original)
        width,height=float(page.mediabox.width),float(page.mediabox.height)
        overlay=BytesIO();c=canvas.Canvas(overlay,pagesize=(width,height))
        c.setFillColorRGB(.36,.22,.55);c.setFillAlpha(.18);c.setFont('Helvetica',max(8,min(16,width/35)))
        c.translate(width/2,height/2);c.rotate(32);c.drawCentredString(0,0,label[:150]);c.save()
        page.merge_page(PdfReader(overlay).pages[0])
    out=BytesIO();writer.write(out);return out.getvalue()
