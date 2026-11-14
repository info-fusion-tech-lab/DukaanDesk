import struct
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ICON = ROOT / "store.ico"
OUTPUT_DIRECTORY = ROOT / "desktop" / "assets"
ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
ICNS_CHUNKS = (
    (16, b"icp4"),
    (32, b"icp5"),
    (64, b"icp6"),
    (128, b"ic07"),
    (256, b"ic08"),
    (512, b"ic09"),
    (1024, b"ic10"),
)


def square_icon(source, size):
    resized = ImageOps.contain(source, (size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return canvas


def main():
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with Image.open(SOURCE_ICON) as image:
        source = image.convert("RGBA")

    square_icon(source, 512).save(OUTPUT_DIRECTORY / "store.png")
    square_icon(source, 256).save(
        OUTPUT_DIRECTORY / "store.ico",
        format="ICO",
        sizes=[(size, size) for size in ICON_SIZES],
    )

    chunks = []
    for size, chunk_type in ICNS_CHUNKS:
        buffer = BytesIO()
        square_icon(source, size).save(buffer, format="PNG")
        image_data = buffer.getvalue()
        chunks.append(chunk_type + struct.pack(">I", len(image_data) + 8) + image_data)

    payload = b"".join(chunks)
    icns = b"icns" + struct.pack(">I", len(payload) + 8) + payload
    (OUTPUT_DIRECTORY / "store.icns").write_bytes(icns)


if __name__ == "__main__":
    main()
