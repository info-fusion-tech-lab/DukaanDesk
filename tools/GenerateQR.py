import os
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from tools.encrypted_json import save_bytes
from tools.paths import get_storage_path

def generate_labeled_qrcode(product_code, save_filename=None):
    """
    Generates a clean QR code with the raw product code underneath
    as a physical backup for manual entry when scanning fails.
    """
    product_qr_dir = os.path.join(get_storage_path(), "ProductQRs")
    os.makedirs(product_qr_dir, exist_ok=True)

    # 1. Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,  # Minimal quiet zone around the QR matrix
    )
    qr.add_data(product_code)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_width, qr_height = qr_img.size

    # 2. Dimensions Layout
    padding = 10
    text_section_height = 40
    
    total_width = qr_width + (padding * 2)
    total_height = qr_height + text_section_height + padding

    # 3. Canvas Creation (Clean white background)
    canvas = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(canvas)
    
    # Paste QR Code centered
    canvas.paste(qr_img, (padding, padding))

    # 4. Render Product Code Label (No borders or lines drawn)
    try:
        font = ImageFont.truetype("arial.ttf", size=16)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text position to center it right under the QR code
    bbox = draw.textbbox((0, 0), product_code, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    text_x = (total_width - text_width) // 2
    text_y = padding + qr_height + ((text_section_height - text_height) // 2) - 8

    draw.text((text_x, text_y), product_code, fill="black", font=font)

    # 5. Save image to storage/ProductQRs/
    if not save_filename:
        save_filename = f"{product_code}.png"
    elif not save_filename.endswith(".png"):
        save_filename += ".png"

    file_path = os.path.join(product_qr_dir, save_filename)
    image_buffer = BytesIO()
    canvas.save(image_buffer, format="PNG")
    save_bytes(file_path, image_buffer.getvalue())
    return file_path

