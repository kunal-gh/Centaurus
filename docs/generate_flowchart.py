"""
Generate the Centaurus identity resolution flowchart.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def draw_arrow(draw, start, end, color, width=3):
    draw.line([start, end], fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    arrow_len = 12
    left = (x2 - ux * arrow_len + uy * 6, y2 - uy * arrow_len - ux * 6)
    right = (x2 - ux * arrow_len - uy * 6, y2 - uy * arrow_len + ux * 6)
    draw.polygon([(x2, y2), left, right], fill=color)


def generate_chart():
    width, height = 1200, 900
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
        label_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arial.ttf", 15)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        title_font = subtitle_font = label_font = bold_font = small_font = ImageFont.load_default()

    border = (51, 65, 85)
    card = (30, 41, 59)
    text = (241, 245, 249)
    muted = (148, 163, 184)
    purple = (129, 140, 248)
    green = (52, 211, 153)
    amber = (251, 191, 36)
    red = (248, 113, 113)

    draw.text((width // 2, 40), "CENTAURUS IDENTITY RESOLUTION PIPELINE", fill=purple, font=title_font, anchor="mm")
    draw.text(
        (width // 2, 70),
        "Three-tier multi-signal matching with reviewer fallback and borderline model arbitration",
        fill=muted,
        font=subtitle_font,
        anchor="mm",
    )

    draw.rounded_rectangle([450, 110, 750, 190], radius=8, fill=card, outline=border, width=2)
    draw.text((600, 130), "Incoming Profile Signals", fill=purple, font=bold_font, anchor="mm")
    draw.text((600, 160), "Signals: Email | Phone | Name | Instagram", fill=text, font=label_font, anchor="mm")
    draw_arrow(draw, (600, 190), (600, 240), purple)

    draw.rounded_rectangle([380, 240, 820, 340], radius=8, fill=card, outline=border, width=2)
    draw.text((600, 260), "Multi-Signal Weighted Match Scorer", fill=purple, font=bold_font, anchor="mm")
    draw.text((600, 290), "Email exact (35 pts)  -  Phone normalized exact (30 pts)", fill=text, font=label_font, anchor="mm")
    draw.text((600, 315), "Name fuzzy (25 pts)  -  Instagram exact (10 pts)", fill=text, font=label_font, anchor="mm")
    draw_arrow(draw, (600, 340), (600, 390), purple)

    draw.rounded_rectangle([420, 390, 780, 450], radius=20, fill=card, outline=purple, width=2)
    draw.text((600, 420), "Evaluate Weighted Score (0 - 100)", fill=text, font=bold_font, anchor="mm")

    draw_arrow(draw, (420, 420), (220, 420), purple)
    draw_arrow(draw, (220, 420), (220, 720), purple)
    draw_arrow(draw, (780, 420), (980, 420), purple)
    draw_arrow(draw, (980, 420), (980, 720), purple)
    draw_arrow(draw, (600, 450), (600, 490), purple)

    draw.text((310, 400), "Score >= 80%\n[Tier 1: Auto Match]", fill=green, font=small_font, anchor="mm")
    draw.text((890, 400), "Score < 40%\n[Tier 3: Create New]", fill=red, font=small_font, anchor="mm")
    draw.text((680, 470), "Score 40 - 79%\n[Tier 2: Borderline]", fill=purple, font=small_font, anchor="mm")

    draw.rounded_rectangle([400, 490, 800, 570], radius=8, fill=card, outline=border, width=2)
    draw.text((600, 510), "Borderline Model Verification", fill=purple, font=bold_font, anchor="mm")
    draw.text((600, 540), "Compare profiles, estimate same-person probability", fill=text, font=label_font, anchor="mm")
    draw_arrow(draw, (600, 570), (600, 610), purple)

    draw.rounded_rectangle([430, 610, 770, 670], radius=20, fill=card, outline=purple, width=2)
    draw.text((600, 640), "Probability Gate", fill=text, font=bold_font, anchor="mm")

    draw.line([(430, 640), (320, 640)], fill=purple, width=3)
    draw_arrow(draw, (320, 640), (280, 720), purple)
    draw.text((350, 620), "Prob >= 0.85\n(auto_link)", fill=green, font=small_font, anchor="mm")

    draw_arrow(draw, (600, 670), (600, 720), purple)
    draw.text((670, 695), "Prob 0.60 - 0.84\n(verify_manually)", fill=amber, font=small_font, anchor="mm")

    draw.line([(770, 640), (880, 640)], fill=purple, width=3)
    draw_arrow(draw, (880, 640), (920, 720), purple)
    draw.text((850, 620), "Prob < 0.60\n(create_new)", fill=red, font=small_font, anchor="mm")

    draw.rounded_rectangle([100, 720, 340, 810], radius=8, fill=(6, 78, 59), outline=green, width=2)
    draw.text((220, 745), "AUTO LINK", fill=green, font=bold_font, anchor="mm")
    draw.text((220, 780), "Link the profile automatically\nand continue the workflow", fill=text, font=small_font, anchor="mm")

    draw.rounded_rectangle([480, 720, 720, 810], radius=8, fill=(120, 83, 4), outline=amber, width=2)
    draw.text((600, 745), "VERIFY MANUALLY", fill=amber, font=bold_font, anchor="mm")
    draw.text((600, 780), "Queue the case for reviewer approval\nwith all signal evidence attached", fill=text, font=small_font, anchor="mm")

    draw.rounded_rectangle([860, 720, 1100, 810], radius=8, fill=(153, 27, 27), outline=red, width=2)
    draw.text((980, 745), "CREATE NEW", fill=red, font=bold_font, anchor="mm")
    draw.text((980, 780), "Treat the request as a new profile\nand avoid a risky merge", fill=text, font=small_font, anchor="mm")

    draw.text((width // 2, 860), "© 2026 Centaurus identity resolution diagram.", fill=muted, font=small_font, anchor="mm")

    out = Path("docs/identity_flowchart.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"Flowchart generated at {out}")


if __name__ == "__main__":
    generate_chart()
