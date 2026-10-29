"""Optional local Tesseract OCR; no bank slip is sent to an external service."""
from io import BytesIO
from pathlib import Path
import subprocess
def image_text(raw,executable):
    from PIL import Image
    if not executable:return '', 'Image: configure local OCR or review manually'
    path=Path(executable)
    if not path.is_absolute() or not path.is_file():raise ValueError('The server OCR executable is not configured correctly')
    with Image.open(BytesIO(raw)) as im:
        if im.format not in ('PNG','JPEG') or im.width*im.height>20000000:raise ValueError('OCR accepts PNG/JPEG images up to 20 megapixels')
        im=im.convert('RGB');im.thumbnail((3000,3000));image=BytesIO();im.save(image,format='PNG')
    try:
        result=subprocess.run([str(path),'stdin','stdout','-l','eng','--psm','6'],input=image.getvalue(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,check=False,shell=False)
    except (subprocess.TimeoutExpired,OSError):raise ValueError('Local OCR is unavailable or timed out. Review the original slip.')
    if result.returncode:raise ValueError('Local OCR could not read this slip. Review the original file.')
    return result.stdout.decode('utf-8',errors='replace')[:50000],'Local image OCR checks'
