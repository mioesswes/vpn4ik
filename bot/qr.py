from io import BytesIO

import qrcode
from aiogram.types import BufferedInputFile


def build_qr_file(text: str, filename: str = "config.png") -> BufferedInputFile:
    image = qrcode.make(text)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return BufferedInputFile(buffer.getvalue(), filename=filename)
