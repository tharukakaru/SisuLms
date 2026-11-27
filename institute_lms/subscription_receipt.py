"""Branded paid subscription invoices; local assets only, no remote PDF requests."""
from io import BytesIO
from pathlib import Path
from html import escape
from datetime import datetime


def date_label(value, include_time=False):
    if not value:
        return '-'
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return parsed.strftime('%d %b %Y, %I:%M %p' if include_time else '%d %b %Y')


def render(bill):
    if bill.status != 'Paid' or not bill.receipt_number:
        raise ValueError('A paid invoice requires verified payment and an issued number')
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Flowable, KeepTogether
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font, bold = 'Helvetica', 'Helvetica-Bold'
    for regular, heavy in (
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/arialbd.ttf')):
        if Path(regular).exists() and Path(heavy).exists():
            if 'SisuReceipt' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('SisuReceipt',regular))
                pdfmetrics.registerFont(TTFont('SisuReceiptBold',heavy))
            font,bold='SisuReceipt','SisuReceiptBold'
            break
    purple=colors.HexColor('#572B91'); ink=colors.HexColor('#272234')
    muted=colors.HexColor('#746B80'); line=colors.HexColor('#E5DFED')
    style=ParagraphStyle('body',fontName=font,fontSize=9.5,leading=15,textColor=ink)
    small=ParagraphStyle('small',parent=style,fontSize=8,leading=12,textColor=muted)
    label=ParagraphStyle('label',parent=small,fontName=bold,fontSize=7.5,spaceAfter=6)
    strong=ParagraphStyle('strong',parent=style,fontName=bold)
    title=ParagraphStyle('title',parent=style,fontName=bold,fontSize=24,leading=30,alignment=TA_RIGHT)
    right=ParagraphStyle('right',parent=style,alignment=TA_RIGHT)
    total=ParagraphStyle('total',parent=right,fontName=bold,fontSize=21,leading=28,textColor=purple)
    p=lambda value,s=style: Paragraph(escape(str(value if value is not None else '')),s)
    money=f'{bill.currency} {int(bill.amount_minor)/100:,.2f}'
    width=A4[0]-88
    output=BytesIO()
    doc=SimpleDocTemplate(output,pagesize=A4,leftMargin=44,rightMargin=44,topMargin=42,bottomMargin=64,
                         title='Paid invoice '+bill.receipt_number,author='SISU Academy')
    class BrandLogo(Flowable):
        def __init__(self):
            super().__init__()
            self.width = 122
            self.height = 122 * 448 / 1444
        def draw(self):
            # Clip the original logo's transparent margins without resampling it.
            scale = self.width / 1444
            c = self.canv
            c.saveState()
            boundary = c.beginPath(); boundary.rect(0, 0, self.width, self.height)
            c.clipPath(boundary, stroke=0)
            c.drawImage(str(Path(__file__).parent/'public'/'login-sisu-logo.png'),
                        -283*scale, -749*scale, width=2000*scale, height=2000*scale, mask='auto')
            c.restoreState()
    logo=BrandLogo()
    logo.hAlign='LEFT'
    header=Table([[logo,[p('INVOICE',title),Spacer(1,5),p(bill.receipt_number,right)]],
                  [[p('SISU Academy',strong),p('www.sisuacademylk.com',small)],
                   p('PAID  /  Payment confirmed',ParagraphStyle('paid',parent=right,fontName=bold,textColor=colors.HexColor('#21784D')))]],
                 colWidths=[width*.48,width*.52])
    header.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,0),18),
        ('BOTTOMPADDING',(0,-1),(-1,-1),22),('LINEBELOW',(0,-1),(-1,-1),1.5,purple)]))
    meta=Table([[p('Invoice date',small),p(date_label(bill.paid_at),right)],
                [p('Payment date',small),p(date_label(bill.paid_at,True),right)],
                [p('Time zone',small),p('Sri Lanka',right)],
                [p('Payment method',small),p(bill.payment_channel,right)]],colWidths=[90,width*.55-90])
    meta.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                             ('RIGHTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    recipient=[p('BILL TO',label),p(bill.billed_to,strong),p(bill.billing_email,small)]
    billing=Table([[recipient,meta]],colWidths=[width*.45,width*.55])
    billing.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
    service=f'{date_label(bill.period_start)} to {date_label(bill.period_end)}'
    description=[p(bill.plan+' subscription',strong),Spacer(1,5),p('Monthly access to your SISU workspace',small),p(service,small)]
    items=Table([[p('DESCRIPTION',label),p('QTY',label),p('UNIT PRICE',label),p('AMOUNT',label)],
                 [description,p('1 month'),p(money,right),p(money,right)]],colWidths=[width*.48,width*.14,width*.19,width*.19],repeatRows=1)
    items.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#F4EFFA')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),16),
        ('LINEBELOW',(0,-1),(-1,-1),.6,line)]))
    amounts=Table([[p('Subtotal',small),p(money,right)],[p('Total paid',strong),p(money,total)],
                   [p('Balance due',small),p(bill.currency+' 0.00',right)]],colWidths=[width*.62,width*.38])
    amounts.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),10),
        ('BOTTOMPADDING',(0,0),(-1,-1),10),('BACKGROUND',(0,1),(-1,1),colors.HexColor('#F4EFFA'))]))
    closing=[Spacer(1,30),p('Thank you for learning and growing with SISU.',strong),Spacer(1,7),
        p('Your subscription is active for the service period shown above. Keep this paid invoice for your records.',small),
        Spacer(1,10),p('No automatic renewal charges. Class tuition is billed separately. This is a subscription payment invoice, not a tax invoice.',small)]
    def footer(canvas, document):
        canvas.saveState();canvas.setStrokeColor(line);canvas.line(44,47,A4[0]-44,47)
        canvas.setFillColor(muted);canvas.setFont(font,7.5)
        canvas.drawString(44,32,'SISU Academy  |  '+bill.receipt_number)
        canvas.drawRightString(A4[0]-44,32,'Page '+str(document.page));canvas.restoreState()
    doc.build([header,Spacer(1,25),billing,Spacer(1,25),items,Spacer(1,18),amounts,KeepTogether(closing)],onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()
