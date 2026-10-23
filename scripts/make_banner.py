"""Generate the repository preview image from the bundled character art."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "preview.png"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / name), size)


def main() -> None:
    width, height = 1280, 640
    canvas = Image.new("RGBA", (width, height), "#101b18")
    pixels = canvas.load()

    for y in range(height):
        for x in range(width):
            glow = max(0, 1 - ((x - 930) ** 2 + (y - 310) ** 2) ** 0.5 / 570)
            red = int(16 + 18 * glow)
            green = int(27 + 31 * glow)
            blue = int(24 + 20 * glow)
            pixels[x, y] = (red, green, blue, 255)

    draw = ImageDraw.Draw(canvas)
    draw.ellipse((663, 22, 1262, 621), outline="#344b42", width=2)
    draw.ellipse((705, 64, 1220, 579), outline="#263a33", width=1)
    draw.line((78, 492, 606, 492), fill="#8d7248", width=1)

    character = Image.open(ROOT / "assets" / "images" / "idle.png").convert("RGBA")
    character.thumbnail((570, 570), Image.Resampling.LANCZOS)
    shadow = Image.new("RGBA", character.size, (0, 0, 0, 0))
    alpha = character.getchannel("A")
    shadow.putalpha(alpha.point(lambda value: int(value * 0.28)))
    canvas.alpha_composite(shadow, (957 - character.width // 2 + 10, 43 + 15))
    canvas.alpha_composite(character, (957 - character.width // 2, 43))

    draw.text((78, 98), "虾 仁 桌 宠", fill="#f3ecde", font=font(68, bold=True))
    draw.text(
        (82, 186),
        "让一只会陪你说话的桌宠，留在工作台一角。",
        fill="#b7c4bb",
        font=font(25),
    )
    draw.text((82, 272), "29", fill="#d4a85e", font=font(64, bold=True))
    draw.text((162, 289), "种姿态", fill="#e7decd", font=font(25))
    draw.text((294, 272), "36", fill="#d4a85e", font=font(64, bold=True))
    draw.text((374, 289), "句台词", fill="#e7decd", font=font(25))
    draw.text((82, 386), "拖动 · 双击 · 托盘常驻 · 久坐与待办提醒", fill="#82968b", font=font(20))
    draw.text((82, 516), "PYQT5  ·  WINDOWS  ·  PORTABLE", fill="#6f8177", font=font(17))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(OUTPUT, "PNG", optimize=True)
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    main()
