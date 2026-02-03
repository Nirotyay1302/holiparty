import qrcode
import io
from PIL import Image

def generate_qr(ticket_id):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(ticket_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf