"""No network, macros, external relationships, OCR or unbounded archive extraction."""
from io import BytesIO
from zipfile import ZipFile
import re
from .ai_rules import normalize

class Unsupported(ValueError):pass

def extract(filename,raw):
    if not isinstance(raw,bytes) or not raw or len(raw)>10*1024*1024:raise ValueError('Document must be nonempty and at most 10 MB')
    suffix=filename.rsplit('.',1)[-1].lower()
    if suffix in ('doc','ppt'):raise Unsupported('Legacy Office format: convert to PDF, DOCX or PPTX')
    if suffix=='txt':
        return [('text',raw.decode('utf-8-sig',errors='strict'))]
    if suffix not in ('pdf','docx','pptx'):raise Unsupported('Unsupported document type')
    from .material_contract import validate_file
    validate_file(filename,raw)
    if suffix=='pdf':
        from pypdf import PdfReader
        reader=PdfReader(BytesIO(raw),strict=True)
        if reader.is_encrypted or len(reader.pages)>200:raise Unsupported('Encrypted or over-200-page PDF')
        rows=[];total=0
        for n,page in enumerate(reader.pages,1):
            # Bound expanded PDF content before text extraction.
            content=page.get_contents()
            if content and len(content.get_data())>5*1024*1024:raise ValueError('PDF page too complex')
            text=page.extract_text() or '';total+=len(text)
            if total>400000:raise ValueError('Extracted text too large')
            rows.append(('page '+str(n),text))
        return rows
    from defusedxml import ElementTree
    with ZipFile(BytesIO(raw)) as z:
        names=['word/document.xml'] if suffix=='docx' else sorted((n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)),key=lambda n:int(re.search(r'(\d+)\.xml',n).group(1)))
        if len(names)>200:raise ValueError('Too many slides')
        rows=[]
        for n,path in enumerate(names,1):
            xml=ElementTree.fromstring(z.read(path))
            text=' '.join(e.text or '' for e in xml.iter() if e.tag.endswith('}t'))
            rows.append(('document' if suffix=='docx' else 'slide '+str(n),text))
        return rows
